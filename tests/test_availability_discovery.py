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
        # Real Parasite (2019) row -- the previous ID (018f2e4a-7b31-...) was
        # a fake seed UUID that only worked against the db=None mock
        # fallback and doesn't exist in the real catalog.
        cls.test_title_id = "10000000-0000-7000-8000-000000000001"

    def test_repository_get_title_releases(self):
        # db=None deliberately exercises the seed/local-dev fallback path
        # (legitimate test-only behavior, not a production code path).
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
        # Against the real catalog (the default, see conftest.py), release
        # data doesn't exist yet for any title (0 rows in canonical.release
        # database-wide -- a documented, known data gap, not a bug: no free
        # source carries theatrical/digital release-window data at this
        # catalog's scale). The endpoint must honestly return an empty
        # list, not fabricate one -- see the canonical.py fallback-safety
        # fix this session.
        response = self.client.get(f"/v1/titles/{self.test_title_id}/releases")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    def test_router_availability_endpoint(self):
        # Same real-data caveat as test_router_releases_endpoint: 0 rows in
        # canonical.platform_offer database-wide currently, so offers/releases
        # are honestly empty rather than fabricated ("Watcha"/"Naver Series
        # On" demo offers).
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
