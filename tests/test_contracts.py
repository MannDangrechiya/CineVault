# CineVault OS — API Contract Validation Test Suite
# Verifies request/response schemas, status codes, cursor pagination, and standard RFC 7807 error structure

import unittest
from fastapi.testclient import TestClient
from services.api.main import app

class TestAPIContracts(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_title_detail_contract(self):
        response = self.client.get("/v1/titles/018f2e4a-7b31-7000-8000-123456789abc")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], "018f2e4a-7b31-7000-8000-123456789abc")
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

if __name__ == "__main__":
    unittest.main()
