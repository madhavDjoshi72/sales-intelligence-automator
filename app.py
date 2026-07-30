import os
import re
import json

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for

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


def _guess_url_from_name(text: str) -> str | None:
    text = text.strip()
    if not text:
        return None

    if URL_LIKE_PATTERN.match(text):
        return text if text.startswith("http") else f"https://{text}"

    if "." in text and " " not in text:
        return f"https://{text}"

    cleaned = re.sub(r"[^\w\s-]", "", text.lower())
    cleaned = re.sub(r"[\s_]+", "-", cleaned).strip("-")
    if not cleaned:
        return None
    return f"https://{cleaned}.com"


def _prepare_leads(raw: str) -> list[str]:
    return [line.strip() for line in raw.splitlines() if line.strip()]


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
                scraped_text = scrape_lead(guessed)
                if scraped_text:
                    source_url = guessed

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

        brief_data = result.model_dump()
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
