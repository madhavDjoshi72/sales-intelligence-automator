import unittest
from unittest.mock import patch

import app
from scraper import scrape_lead


class LeadResolutionTests(unittest.TestCase):
    def test_name_only_lead_uses_search_result_when_available(self):
        html = """
        <html><body>
        <div><a href="https://www.acmecorp.com">Acme Corp</a></div>
        </body></html>
        """
        with patch("app.requests.post") as mock_post:
            mock_post.return_value.text = html
            mock_post.return_value.raise_for_status.return_value = None

            resolved = app._guess_url_from_name("Acme Corp")

            self.assertEqual(resolved, "https://www.acmecorp.com")
            self.assertEqual(mock_post.call_args.args[0], "https://html.duckduckgo.com/html/")
            self.assertEqual(mock_post.call_args.kwargs["data"], {"q": "Acme Corp", "kl": "us-en"})
            self.assertIn("Mozilla/5.0 (Windows NT 10.0; Win64; x64)", mock_post.call_args.kwargs["headers"]["User-Agent"])

    def test_parked_domain_is_treated_as_no_content(self):
        html = """
        <html><body>
        <title>Domain may be for sale</title>
        <h1>Access denied</h1>
        <p>This domain is temporarily unavailable.</p>
        </body></html>
        """
        with patch("scraper.requests.get") as mock_get:
            mock_get.return_value.text = html
            mock_get.return_value.raise_for_status.return_value = None

            self.assertIsNone(scrape_lead("https://example-for-sale.com"))


if __name__ == "__main__":
    unittest.main()
