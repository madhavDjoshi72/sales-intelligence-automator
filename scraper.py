"""
Fetches a webpage and strips it down to meaningful text —
removing nav, footers, scripts, cookie banners, etc.
Heuristic, not perfect — documented as a known limitation in the README.

Two-tier fetch strategy:
1. Plain requests first (fast, cheap).
2. If the result is suspiciously small or is just a JS-redirect shell
   (e.g. window.location.href = "/lander"), follow the redirect target
   with requests once more.
3. If content is STILL too small (real JS-rendered SPA), fall back to
   Playwright to render the page in a headless browser.
"""

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SalesIntelBot/1.0; +prototype)"
}

STRIP_TAGS = ["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]
NOISE_HINTS = ["cookie", "consent", "popup", "modal", "newsletter", "subscribe"]
MIN_CONTENT_LENGTH = 300

JS_REDIRECT_PATTERN = re.compile(
    r"window\.location(?:\.href)?\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE
)
PARKED_HINTS = [
    "domain may be for sale",
    "domain is for sale",
    "this domain is parked",
    "this site is parked",
    "parked domain",
    "parked page",
    "expired domain",
    "access denied",
    "temporarily unavailable",
    "domain has expired",
    "this domain may be for sale",
    "for sale",
]


def _http_get(url: str, timeout: int = 10) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException:
        return None


def _find_js_redirect(html: str, base_url: str) -> str | None:
    match = JS_REDIRECT_PATTERN.search(html)
    if match:
        return urljoin(base_url, match.group(1))
    return None


def _fetch_with_playwright(url: str, timeout_ms: int = 15000) -> str | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(user_agent=HEADERS["User-Agent"])
            page.goto(url, timeout=timeout_ms, wait_until="networkidle")
            html = page.content()
            browser.close()
            return html
    except Exception:
        return None


def fetch_page(url: str, timeout: int = 10) -> str | None:
    html = _http_get(url, timeout)

    if html and len(html.strip()) < MIN_CONTENT_LENGTH:
        redirect_url = _find_js_redirect(html, url)
        if redirect_url:
            redirected_html = _http_get(redirect_url, timeout)
            if redirected_html and len(redirected_html.strip()) >= MIN_CONTENT_LENGTH:
                return redirected_html
        rendered = _fetch_with_playwright(url)
        if rendered:
            return rendered
        return html

    return html


def clean_text(html: str, max_chars: int = 6000) -> str:
    """Strip boilerplate and return the main readable text, truncated."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    # Drop elements whose class/id suggest cookie banners, popups, etc.
    for tag in soup.find_all(True):
        if not hasattr(tag, "attrs") or tag.attrs is None:
            continue
        attrs = tag.attrs or {}
        class_names = attrs.get("class", []) or []
        if isinstance(class_names, str):
            class_names = [class_names]
        attrs_text = " ".join(class_names + [attrs.get("id", "") or ""]).lower()
        if any(hint in attrs_text for hint in NOISE_HINTS):
            tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    # Collapse excess whitespace
    text = " ".join(text.split())
    return text[:max_chars]


def _looks_like_parked_or_blocked_page(html: str) -> bool:
    if not html:
        return False
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).lower()
    if not text:
        return False
    return any(hint in text for hint in PARKED_HINTS)


def scrape_lead(url: str) -> str | None:
    """Fetch + clean a single URL. Returns cleaned text, or None if fetch failed."""
    html = fetch_page(url)
    if not html:
        return None
    if _looks_like_parked_or_blocked_page(html):
        return None
    return clean_text(html)


if __name__ == "__main__":
    # Quick manual test
    test_url = "https://www.bostonplumbing.com"
    content = scrape_lead(test_url)
    if content:
        print(f"Scraped {len(content)} chars from {test_url}\n")
        print(content[:500])
    else:
        print(f"Failed to fetch {test_url}")
