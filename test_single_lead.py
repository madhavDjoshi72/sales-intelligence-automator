"""
Step 2 proof of concept: run ONE lead through the full pipeline
(scrape -> clean -> LLM -> validated JSON) before building anything else.

Usage:
  export GEMINI_API_KEY=your_key_here
  python test_single_lead.py
"""

from dotenv import load_dotenv

load_dotenv()

from scraper import scrape_lead
from analyzer import analyze_lead

TEST_URL = "https://www.bostonplumbing.com"


def main():
    print(f"Scraping {TEST_URL} ...")
    content = scrape_lead(TEST_URL)

    if content:
        print(f"Got {len(content)} characters of cleaned content.\n")
    else:
        print("Scrape failed — will let the LLM work from the name alone.\n")

    print("Sending to Gemini for analysis...")
    result = analyze_lead(lead_label=TEST_URL, scraped_text=content, source_url=TEST_URL)

    if result:
        print("\n--- SALES BRIEF ---")
        print(result.model_dump_json(indent=2))
    else:
        print("Failed to get a valid structured result after retry.")


if __name__ == "__main__":
    main()
