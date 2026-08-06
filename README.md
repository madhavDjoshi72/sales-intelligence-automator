# sales-intelligence-automator

A simple Flask frontend for the sales intelligence automator. Enter site URLs or company names, then review generated sales briefs in the browser.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Gemini API key:

```bash
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

3. Run the web app with Gemini mode:

```bash
python app.py
```

4. Visit `http://localhost:5000` or `http://127.0.0.1:5000` and paste one lead per line.

## Troubleshooting

- If `localhost refused to connect`, make sure the Flask server is running:

```bash
python app.py
```

- If you are in a remote container or Codespace, open the forwarded port `5000` in your host browser or use the VS Code Ports panel.

- If Google returns a rate limit or quota error, set up billing on your Google Cloud project and consider using a lower-volume model list.
  - Example:

```bash
export GEMINI_MODEL_CANDIDATES="gemini-3-flash-preview,gemini-3.1-flash-lite,gemini-flash-lite-latest"
python app.py
```

- If port `5000` is already in use, run the app on a different port:

```bash
export PORT=5001
python app.py
```

### Free local-only mode

If you want to run without Gemini/API usage at all, start the app in free local mode:

```bash
export FREE_MODE=true
python app.py
```

This uses a simple built-in heuristic analyzer and does not call Google Gemini. The output is less accurate than Gemini, but it works without billing.

## Design Notes

- Architecture overview: lead input → URL resolution → scraping → LLM analysis → Pydantic validation → SQLite/JSON storage → Flask UI.
- Gemini was chosen because it offers a free tier and generally produces reliable JSON output for structured briefs; Flask was chosen because it is simple and fast to prototype with.
- Strict JSON output is enforced with a system prompt schema, Pydantic validation, and one retry where the prior error is fed back to the model.
- Known edge cases handled: JS-redirect pages, parked/expired domains, Cloudflare-style bot walls, and name-only leads with no URL.
- Name-only lead resolution now attempts a DuckDuckGo-based lookup with a browser-style user agent and preserves the guessed source URL even when scraping later fails.
- What I'd improve with more time: Playwright for more JS-heavy sites, richer search fallback strategies, and more robust retry handling for rate limits.
- The results UI now shows a numbered company list and an explicit B2B Qualification Decision (Yes/No) for each lead.

## Static output report

If you cannot access the web UI, you can use generate_sample_report.py as an optional offline report generator to create a standalone HTML report instead:

```bash
python generate_sample_report.py
```

Then open `output_report.html` in your editor or browser.

## Saved data persistence

Generated briefs are stored in `saved_briefs.json` in the project directory so they remain available between app restarts. Clear results in the app also updates this file.

## Model override

The app now retries with a fallback list of supported Gemini models if the first one is unavailable or quota-limited.

If you hit Gemini quota or availability errors, set a safer model list before running:

```bash
export GEMINI_MODEL_CANDIDATES="gemini-3-flash-preview,gemini-3.1-flash-lite,gemini-flash-lite-latest"
python app.py
```

If the live app still cannot call Gemini, it will show a friendly error message on the results page instead of a raw server failure.
