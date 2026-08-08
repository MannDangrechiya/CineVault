# CineVault OS — Availability & Release Discovery Integration Test Suite
# Tests Build Unit 8.6: Title Releases, Regional Platform Offers, and Temporal Availability Windows

import unittest
import asyncio
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.repositories.canonical import canonical_repository
from services.api.schemas.titles import AvailabilityDiscoveryResponse, ReleaseSummary

class TestAvailabilityAndReleaseDiscovery(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_title_id = "018f2e4a-7b31-7000-8000-123456789abc"

    def test_repository_get_title_releases(self):
        releases = asyncio.run(canonical_repository.get_title_releases(db=None, title_id=self.test_title_id))
        self.assertIsInstance(releases, list)
        self.assertGreater(len(releases), 0)
        self.assertEqual(releases[0].release_type, "THEATRICAL")

    def test_repository_get_title_availability(self):
        avail = asyncio.run(canonical_repository.get_title_availability(db=None, title_id=self.test_title_id, country_code="KR"))
        self.assertIsInstance(avail, AvailabilityDiscoveryResponse)
        self.assertEqual(avail.country_code, "KR")
        self.assertGreater(avail.total_offers, 0)
        self.assertIn(avail.offers[0].offer_type, ["FLATRATE", "RENT", "BUY", "FREE", "ADS"])

    def test_router_releases_endpoint(self):
        response = self.client.get(f"/v1/titles/{self.test_title_id}/releases")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_router_availability_endpoint(self):
        response = self.client.get(f"/v1/titles/{self.test_title_id}/availability?country_code=KR")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["country_code"], "KR")
        self.assertIn("offers", data)
        self.assertIn("releases", data)

    def test_router_nonexistent_title_404(self):
        response = self.client.get("/v1/titles/00000000-0000-0000-0000-000000000000/availability")
        self.assertEqual(response.status_code, 404)

if __name__ == "__main__":
    unittest.main()
