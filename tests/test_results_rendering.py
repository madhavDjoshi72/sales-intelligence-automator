import unittest

import app as app_module


class ResultsRenderingTests(unittest.TestCase):
    def setUp(self):
        app_module.saved_briefs = [
            {
                "company_name": "Example Corp",
                "company_overview": "Example Corp helps teams grow.",
                "core_product_or_service": "Sales automation",
                "target_customer": "B2B sales teams",
                "is_b2b_lead": True,
                "b2b_reasoning": "This looks like a business-focused software vendor.",
                "sales_questions": ["What is your current workflow?"],
                "notes": "Limited evidence.",
                "_lead_label": "Example Corp",
            }
        ]

    def test_results_page_renders_brief_cards(self):
        client = app_module.app.test_client()
        response = client.get("/results")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Lead summary", response.data)
        self.assertIn(b"Example Corp", response.data)


if __name__ == "__main__":
    unittest.main()
