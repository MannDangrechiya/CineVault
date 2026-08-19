# CineVault OS — Canonical Repository Integration Test Suite
# Tests Build Unit 8.1: Canonical Data Access Layer, ORM Models, and Rewired Title Routers

import unittest
import asyncio
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.repositories.canonical import canonical_repository
from services.api.schemas.titles import TitleSummary, TitleDetail, TitleLookupResponse

class TestCanonicalRepository(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_repository_list_titles(self):
        titles = asyncio.run(canonical_repository.list_titles(db=None))
        self.assertGreater(len(titles), 0)
        self.assertIsInstance(titles[0], TitleSummary)
        self.assertEqual(titles[0].display_id, "MOV-000001")

    def test_repository_get_title_by_id(self):
        title_id = "018f2e4a-7b31-7000-8000-123456789abc"
        title = asyncio.run(canonical_repository.get_title_by_id(db=None, title_id=title_id))
        self.assertIsNotNone(title)
        self.assertIsInstance(title, TitleDetail)
        self.assertEqual(title.canonical_title, "Parasite")
        self.assertEqual(title.content_type, "MOVIE")

    def test_repository_lookup_title_display_id(self):
        res = asyncio.run(canonical_repository.lookup_title(db=None, display_id="MOV-000001"))
        self.assertIsNotNone(res)
        self.assertIsInstance(res, TitleLookupResponse)
        self.assertEqual(res.display_id, "MOV-000001")
        self.assertEqual(res.lookup_method, "DISPLAY_ID")

    def test_repository_lookup_title_provider_mapping(self):
        res = asyncio.run(canonical_repository.lookup_title(db=None, provider="TMDB", external_id="496243"))
        self.assertIsNotNone(res)
        self.assertEqual(res.lookup_method, "PROVIDER_EXTERNAL_MAPPING")
        self.assertEqual(res.matched_external_id, "496243")

    def test_router_list_titles_endpoint(self):
        response = self.client.get("/v1/titles")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("data", data)
        self.assertIn("pagination", data)
        self.assertGreater(len(data["data"]), 0)
        self.assertTrue(all("display_id" in t and bool(t["display_id"]) for t in data["data"]))

    def test_router_title_detail_endpoint(self):
        response = self.client.get("/v1/titles/018f2e4a-7b31-7000-8000-123456789abc")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["canonical_title"], "Parasite")
        self.assertEqual(data["display_id"], "MOV-000001")
        self.assertIn("synopsis", data)

    def test_router_title_provenance_endpoint(self):
        response = self.client.get("/v1/titles/018f2e4a-7b31-7000-8000-123456789abc/provenance")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]["field_name"], "canonical_title")
        self.assertEqual(data[0]["source_provider"], "KOBIS")

    def test_router_catalog_endpoint(self):
        response = self.client.get("/v1/catalog?limit=24&offset=0")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("total", data)
        self.assertIn("limit", data)
        self.assertEqual(data["limit"], 24)
        self.assertGreater(len(data["items"]), 0)
        self.assertGreater(data["total"], 0)

    def test_router_genres_endpoint(self):
        response = self.client.get("/v1/genres")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertIn("genre_id", data[0])
        self.assertIn("name", data[0])

if __name__ == "__main__":
    unittest.main()
