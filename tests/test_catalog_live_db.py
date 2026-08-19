import unittest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.database import get_db

class TestCatalogEndpoints(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides.pop(get_db, None)
        self.client = TestClient(app)

    def test_catalog_endpoint_pagination(self):
        response = self.client.get("/v1/catalog?limit=24&offset=0")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("total", data)
        self.assertIn("limit", data)
        self.assertEqual(data["limit"], 24)
        self.assertEqual(len(data["items"]), 24)
        self.assertGreaterEqual(data["total"], 88979)
        self.assertEqual(data["next_offset"], 24)

        # Check structure of item
        item = data["items"][0]
        self.assertIn("id", item)
        self.assertIn("display_id", item)
        self.assertIn("canonical_title", item)
        self.assertIn("content_type", item)
        self.assertIn("production_year", item)

    def test_catalog_endpoint_search_query(self):
        response = self.client.get("/v1/catalog?q=Dark%20Knight&limit=10&offset=0")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["total"], 0)
        self.assertTrue(any("dark knight" in item["canonical_title"].lower() for item in data["items"]))

    def test_catalog_endpoint_year_filter(self):
        response = self.client.get("/v1/catalog?production_year=2019&limit=10&offset=0")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["total"], 0)
        self.assertTrue(all(item["production_year"] == 2019 for item in data["items"]))

    def test_genres_endpoint(self):
        response = self.client.get("/v1/genres")
        self.assertEqual(response.status_code, 200)
        genres = response.json()
        self.assertIsInstance(genres, list)
        self.assertGreaterEqual(len(genres), 7)
        genre_ids = [g["genre_id"] for g in genres]
        self.assertIn("action", genre_ids)
        self.assertIn("drama", genre_ids)

    def test_titles_root_endpoint_query_params(self):
        response = self.client.get("/titles?limit=24&offset=0&query=Dark&genre=Action&year=2008&content_type=MOVIE")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("total", data)
        self.assertIn("limit", data)
        self.assertEqual(data["limit"], 24)
        if len(data["items"]) > 0:
            item = data["items"][0]
            self.assertEqual(item["content_type"], "MOVIE")
            self.assertEqual(item["production_year"], 2008)

    def test_titles_endpoint(self):
        response = self.client.get("/v1/titles?limit=25")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("data", data)
        self.assertEqual(len(data["data"]), 25)

if __name__ == "__main__":
    unittest.main()

