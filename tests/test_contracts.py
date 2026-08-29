# CineVault OS — API Contract Validation Test Suite
# Verifies request/response schemas, status codes, cursor pagination, and standard RFC 7807 error structure

import unittest
from fastapi.testclient import TestClient
from services.api.main import app

class TestAPIContracts(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_title_detail_contract(self):
        # Real Parasite (2019) row -- the previous ID (018f2e4a-7b31-...) was
        # a fake seed UUID that only worked against the db=None mock
        # fallback and doesn't exist in the real catalog.
        real_parasite_id = "10000000-0000-7000-8000-000000000001"
        response = self.client.get(f"/v1/titles/{real_parasite_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], real_parasite_id)
        self.assertEqual(data["display_id"], "MOV-000001")
        self.assertEqual(data["canonical_title"], "Parasite")
        self.assertIn("has_licensed_artwork", data)

    def test_cursor_pagination_contract(self):
        response = self.client.get("/v1/titles?limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("data", data)
        self.assertIn("pagination", data)
        self.assertIn("next_cursor", data["pagination"])
        self.assertIn("has_more", data["pagination"])
        self.assertEqual(data["pagination"]["limit"], 10)

    def test_validation_error_contract(self):
        response = self.client.get("/v1/search?q=")  # Invalid query string (too short)
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("details", data["error"])

    def test_list_titles_filter_contract(self):
        """Asserts that production_year and origin_country query params actually narrow results."""
        # 1. Fetch titles for production_year=2019 & origin_country=KR (Parasite is 2019 KR)
        response = self.client.get("/v1/titles?production_year=2019&origin_country=KR")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("data", data)
        items = data["data"]
        self.assertTrue(len(items) > 0)
        for item in items:
            self.assertEqual(item["production_year"], 2019)
            self.assertEqual(item["origin_country"], "KR")

        # 2. Fetch titles for a non-matching production_year=1900
        empty_response = self.client.get("/v1/titles?production_year=1900")
        self.assertEqual(empty_response.status_code, 200)
        empty_data = empty_response.json()
        self.assertEqual(len(empty_data["data"]), 0)

if __name__ == "__main__":
    unittest.main()
