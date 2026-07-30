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

3. Run the web app:

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

### Free local-only mode

If you want to run without Gemini/API usage at all, start the app in free local mode:

```bash
export FREE_MODE=true
python app.py
```

This uses a simple built-in heuristic analyzer and does not call Google Gemini. The output is less accurate than Gemini, but it works without billing.

## Static output report

If you cannot access the web UI, you can generate a standalone HTML report instead:

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
