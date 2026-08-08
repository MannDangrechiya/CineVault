# CineVault OS — Search Repository Integration Test Suite
# Tests Build Unit 8.3: Catalog Search, Trigram FTS Engine & Script Normalization

import unittest
import asyncio
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.repositories.search import search_repository, normalize_search_query
from services.api.schemas.search import SearchResponse

class TestSearchRepository(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_query_normalization(self):
        self.assertEqual(normalize_search_query("  PARASITE  "), "parasite")
        self.assertEqual(normalize_search_query("기생충"), "기생충")

    def test_repository_search_title(self):
        res = asyncio.run(search_repository.search_catalog(db=None, q="parasite"))
        self.assertIsInstance(res, SearchResponse)
        self.assertGreater(res.total_hits, 0)
        self.assertEqual(res.results[0].canonical_title, "Parasite")
        self.assertEqual(res.results[0].entity_type, "TITLE")

    def test_repository_search_original_script(self):
        res = asyncio.run(search_repository.search_catalog(db=None, q="기생충"))
        self.assertGreater(res.total_hits, 0)
        self.assertEqual(res.results[0].canonical_title, "Parasite")

    def test_repository_search_person(self):
        res = asyncio.run(search_repository.search_catalog(db=None, q="bong", entity_type="PERSON"))
        self.assertGreater(res.total_hits, 0)
        self.assertEqual(res.results[0].entity_type, "PERSON")
        self.assertEqual(res.results[0].canonical_title, "Bong Joon-ho")

    def test_router_search_endpoint(self):
        response = self.client.get("/v1/search?q=parasite&type=TITLE")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("query", data)
        self.assertIn("total_hits", data)
        self.assertIn("results", data)
        self.assertGreater(data["total_hits"], 0)
        self.assertEqual(data["results"][0]["canonical_title"], "Parasite")

if __name__ == "__main__":
    unittest.main()
