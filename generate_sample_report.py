import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

from analyzer import analyze_lead

SAMPLE_LEAD = "https://www.bostonplumbing.com"
OUTPUT_FILE = "output_report.html"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Sales Intelligence Report</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 32px; background: #f8fafc; color: #111827; }}
    .container {{ max-width: 980px; margin: 0 auto; background: white; border-radius: 16px; padding: 28px; box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08); }}
    h1 {{ margin-top: 0; font-size: 2rem; }}
    .field {{ margin-bottom: 1.5rem; }}
    .label {{ font-weight: 700; color: #111827; margin-bottom: 0.35rem; display: block; }}
    .value {{ line-height: 1.7; white-space: pre-line; }}
    .badge {{ display: inline-block; background: #2563eb; color: white; border-radius: 999px; padding: 0.45rem 0.85rem; font-size: 0.9rem; }}
    .notes {{ color: #6b7280; font-size: 0.95rem; margin-top: 0.5rem; }}
  </style>
</head>
<body>
  <div class=\"container\">
    <h1>Sales Intelligence Report</h1>
    <p class=\"notes\">Lead: <strong>{lead}</strong></p>
    <div class=\"field\"><span class=\"label\">Company Name</span><div class=\"value\">{company_name}</div></div>
    <div class=\"field\"><span class=\"label\">Overview</span><div class=\"value\">{company_overview}</div></div>
    <div class=\"field\"><span class=\"label\">Core Product / Service</span><div class=\"value\">{core_product_or_service}</div></div>
    <div class=\"field\"><span class=\"label\">Target Customer</span><div class=\"value\">{target_customer}</div></div>
    <div class=\"field\"><span class=\"label\">B2B?</span><div class=\"value\"><span class=\"badge\">{is_b2b}</span><div class=\"notes\">{b2b_reasoning}</div></div></div>
    <div class=\"field\"><span class=\"label\">Sales Questions</span><div class=\"value\">{sales_questions}</div></div>
    <div class=\"field\"><span class=\"label\">Notes</span><div class=\"value\">{notes}</div></div>
  </div>
</body>
</html>"""


def main():
    print(f"Analyzing sample lead: {SAMPLE_LEAD}")
    result = analyze_lead(lead_label=SAMPLE_LEAD, scraped_text=None, source_url=SAMPLE_LEAD)
    if result is None:
        print("Failed to generate a report.")
        return

    html = HTML_TEMPLATE.format(
        lead=SAMPLE_LEAD,
        company_name=result.company_name,
        company_overview=result.company_overview,
        core_product_or_service=result.core_product_or_service,
        target_customer=result.target_customer,
        is_b2b="Yes" if result.is_b2b_lead else "No",
        b2b_reasoning=result.b2b_reasoning,
        sales_questions="<br>".join(result.sales_questions),
        notes=result.notes or "None",
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
