import os
import re
import json

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from urllib.parse import urljoin, urlparse

load_dotenv(dotenv_path=".env")

from analyzer import analyze_lead
from scraper import scrape_lead

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "saved_briefs.json")
FREE_MODE = os.environ.get("FREE_MODE", "false").strip().lower() in {"1", "true", "yes"}


def _load_saved_briefs() -> list[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[DATA LOAD ERROR] Could not read {DATA_FILE}: {e}")
        return []


def _save_saved_briefs() -> None:
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as handle:
            json.dump(saved_briefs, handle, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"[DATA SAVE ERROR] Could not write {DATA_FILE}: {e}")


saved_briefs: list[dict] = _load_saved_briefs()

URL_LIKE_PATTERN = re.compile(r"^(https?://|www\.)", re.IGNORECASE)
SEARCH_EXCLUDED_DOMAINS = {
    "duckduckgo.com",
    "google.com",
    "bing.com",
    "yahoo.com",
    "yelp.com",
    "bbb.org",
    "yellowpages.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",
    "reddit.com",
    "quora.com",
}


def _is_excluded_domain(url: str) -> bool:
    hostname = urlparse(url).hostname or ""
    hostname = hostname.lower().removeprefix("www.")
    if not hostname:
        return True
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in SEARCH_EXCLUDED_DOMAINS)


def _search_for_lead_url(query: str) -> str | None:
    browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    try:
        response = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query, "kl": "us-en"},
            headers={"User-Agent": browser_user_agent},
            timeout=8,
        )
        response.raise_for_status()
    except requests.RequestException:
        response = None

    if response is not None:
        soup = BeautifulSoup(response.text, "html.parser")
        for anchor in soup.select("a.result__a"):
            href = anchor.get("href")
            if not href:
                continue
            candidate = urljoin("https://html.duckduckgo.com/html/", href)
            if not _is_excluded_domain(candidate):
                return candidate

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href")
            if not href:
                continue
            candidate = urljoin("https://html.duckduckgo.com/html/", href)
            if candidate.startswith("http") and not _is_excluded_domain(candidate):
                return candidate

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
    except Exception:
        return None

    for result in results:
        candidate = str(result.get("href", "")).strip()
        if candidate.startswith("http") and not _is_excluded_domain(candidate):
            return candidate

    return None


def _guess_url_from_name(text: str) -> str | None:
    text = text.strip()
    if not text:
        return None

    if URL_LIKE_PATTERN.match(text):
        return text if text.startswith("http") else f"https://{text}"

    if "." in text and " " not in text:
        return f"https://{text}"

    search_result = _search_for_lead_url(text)
    if search_result:
        return search_result

    cleaned = re.sub(r"[^\w\s-]", "", text.lower())
    cleaned = re.sub(r"[\s_]+", "-", cleaned).strip("-")
    if not cleaned:
        return None
    return f"https://{cleaned}.com"


def _prepare_leads(raw: str) -> list[str]:
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _normalize_brief_data(brief_data: dict) -> dict:
    company_name = str(brief_data.get("company_name") or "Unknown company").strip()
    overview = str(brief_data.get("company_overview") or "No overview available.").strip()
    product = str(brief_data.get("core_product_or_service") or "No product/service summary available.").strip()
    target_customer = str(brief_data.get("target_customer") or "No target customer identified.").strip()
    reasoning = str(brief_data.get("b2b_reasoning") or "No reasoning provided.").strip()
    notes = brief_data.get("notes")
    notes = str(notes).strip() if notes else None

    questions = brief_data.get("sales_questions") or []
    if isinstance(questions, str):
        questions = [questions]
    else:
        questions = [str(q).strip() for q in questions if str(q).strip()]
    if not questions:
        questions = ["No sales questions were generated."]

    return {
        "company_name": company_name,
        "company_overview": overview,
        "core_product_or_service": product,
        "target_customer": target_customer,
        "is_b2b_lead": bool(brief_data.get("is_b2b_lead", False)),
        "b2b_reasoning": reasoning,
        "sales_questions": questions,
        "source_url": brief_data.get("source_url"),
        "notes": notes,
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", free_mode=FREE_MODE)


@app.route("/run", methods=["POST"])
def run_analysis():
    raw_leads = request.form.get("leads", "")
    leads = _prepare_leads(raw_leads)
    processed = 0
    failed = 0

    for lead in leads:
        processed += 1
        source_url = None
        scraped_text = None

        if URL_LIKE_PATTERN.match(lead):
            source_url = lead if lead.startswith("http") else f"https://{lead}"
            scraped_text = scrape_lead(source_url)
        else:
            guessed = _guess_url_from_name(lead)
            if guessed:
                source_url = guessed
                scraped_text = scrape_lead(guessed)

        try:
            result = analyze_lead(lead_label=lead, scraped_text=scraped_text, source_url=source_url)
        except RuntimeError as e:
            print(f"[ANALYSIS ERROR] {e}")
            return render_template(
                "results.html",
                briefs=saved_briefs,
                processed=processed,
                failed=failed,
                error_message=str(e),
                free_mode=FREE_MODE,
            )
        if result is None:
            failed += 1
            continue

        brief_data = _normalize_brief_data(result.model_dump())
        brief_data["_lead_label"] = lead
        saved_briefs.append(brief_data)
        _save_saved_briefs()

    return redirect(url_for("results", processed=processed, failed=failed))


@app.route("/error", methods=["GET"])
def error_page():
    return render_template(
        "results.html",
        briefs=saved_briefs,
        processed=0,
        failed=0,
        error_message="The Gemini model quota is currently exhausted or unavailable. Try again later or set a different GEMINI_MODEL_CANDIDATES value.",
        free_mode=FREE_MODE,
    )


@app.route("/results", methods=["GET"])
def results():
    processed = request.args.get("processed")
    failed = request.args.get("failed")
    return render_template(
        "results.html",
        briefs=saved_briefs,
        processed=processed,
        failed=failed,
        free_mode=FREE_MODE,
    )


@app.route("/clear", methods=["POST"])
def clear_results():
    saved_briefs.clear()
    _save_saved_briefs()
    return redirect(url_for("results"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Sales Intelligence Automator on http://127.0.0.1:{port}")
    print(f"If you are in a remote container, forward port {port} or use the Codespaces forwarded URL.")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
