# CineVault OS — Unit Tests for TMDB Metadata & Poster Sync Worker

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi.testclient import TestClient

from services.api.ingestion.tmdb_worker import (
    AsyncRateLimiter,
    TMDBClient,
    sync_missing_posters,
)
from services.api.main import app


class TestTMDBWorker(unittest.IsolatedAsyncioTestCase):
    async def test_rate_limiter_interval(self):
        limiter = AsyncRateLimiter(rate_limit_per_second=50.0)
        start = asyncio.get_event_loop().time()
        for _ in range(5):
            await limiter.acquire()
        elapsed = asyncio.get_event_loop().time() - start
        # 5 acquisitions at 50 req/s should take at least ~0.08s
        self.assertGreaterEqual(elapsed, 0.05)

    def test_extract_imdb_id(self):
        client = TMDBClient()
        self.assertEqual(client._extract_imdb_id("IMDB-tt0111161"), "tt0111161")
        self.assertEqual(client._extract_imdb_id("tt0111161"), "tt0111161")
        self.assertEqual(client._extract_imdb_id("  IMDB-tt1375666  "), "tt1375666")
        self.assertIsNone(client._extract_imdb_id("INVALID-123"))
        self.assertIsNone(client._extract_imdb_id(""))

    async def test_find_by_imdb_id_success(self):
        mock_response_data = {
            "movie_results": [
                {
                    "id": 550,
                    "title": "Fight Club",
                    "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
                    "backdrop_path": "/hZkgoQYus5vegHoetLkCJzb17zJ.jpg",
                    "overview": "An insomniac office worker and a devil-may-care soap maker form an underground fight club.",
                }
            ],
            "tv_results": [],
        }

        mock_httpx = AsyncMock()
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = mock_response_data
        mock_httpx.get.return_value = mock_res

        client = TMDBClient(api_key="test_api_key", client=mock_httpx)
        result = await client.find_by_imdb_id("tt0137523")

        self.assertIsNotNone(result)
        self.assertEqual(result["tmdb_id"], 550)
        self.assertEqual(
            result["poster_url"],
            "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        )
        self.assertEqual(
            result["backdrop_url"],
            "https://image.tmdb.org/t/p/w1280/hZkgoQYus5vegHoetLkCJzb17zJ.jpg",
        )
        self.assertIn("underground fight club", result["overview"])

    async def test_find_by_imdb_id_not_found(self):
        mock_httpx = AsyncMock()
        mock_res = MagicMock()
        mock_res.status_code = 404
        mock_httpx.get.return_value = mock_res

        client = TMDBClient(api_key="test_api_key", client=mock_httpx)
        result = await client.find_by_imdb_id("tt9999999")
        self.assertIsNone(result)

    async def test_sync_missing_posters_pipeline(self):
        # Mock database connection and fetch results
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        mock_conn.fetch.return_value = [
            {
                "title_id": "018f2e4a-7b31-7000-8000-123456789abc",
                "display_id": "IMDB-tt6751668",
                "synopsis": "IMDb movie entry (tt6751668).",
            },
            {
                "title_id": "018f2e4a-7b31-7000-8000-123456789abd",
                "display_id": "IMDB-tt0000000",
                "synopsis": "IMDb movie entry (tt0000000).",
            },
        ]

        mock_httpx = AsyncMock()

        def side_effect(url, **kwargs):
            res = MagicMock()
            if "tt6751668" in url:
                res.status_code = 200
                res.json.return_value = {
                    "movie_results": [
                        {
                            "id": 496243,
                            "title": "Parasite",
                            "poster_path": "/7IiTTgloJzvGI1TAYGlC2z2zOZB.jpg",
                            "backdrop_path": "/hiKmpZMGZOSXAAtWwhZIz6wXxpy.jpg",
                            "overview": "Greed and class discrimination threaten...",
                        }
                    ]
                }
            else:
                res.status_code = 200
                res.json.return_value = {"movie_results": [], "tv_results": []}
            return res

        mock_httpx.get.side_effect = side_effect

        stats = await sync_missing_posters(
            db_pool=mock_pool,
            tmdb_api_key="test_key",
            batch_size=10,
            max_batches=1,
            client=mock_httpx,
        )

        self.assertEqual(stats["processed"], 2)
        self.assertEqual(stats["synced"], 1)
        self.assertEqual(stats["not_found"], 1)
        self.assertEqual(mock_conn.execute.call_count, 2)


class TestAdminSyncMetadataEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("services.api.routers.admin.sync_missing_posters", new_callable=AsyncMock)
    def test_post_admin_sync_metadata(self, mock_sync):
        mock_sync.return_value = {"processed": 0, "synced": 0, "not_found": 0, "errors": 0}
        response = self.client.post("/admin/sync-metadata", json={"batch_size": 100})
        self.assertEqual(response.status_code, 202)
        data = response.json()
        self.assertEqual(data["status"], "ACCEPTED")
        self.assertTrue(data["job_id"].startswith("sync-meta-"))
        self.assertEqual(data["batch_size"], 100)

    @patch("services.api.ingestion.tmdb_worker.sync_missing_posters", new_callable=AsyncMock)
    def test_post_automations_sync_metadata(self, mock_sync):
        mock_sync.return_value = {"processed": 0, "synced": 0, "not_found": 0, "errors": 0}
        response = self.client.post("/automations/sync-metadata?batch_size=50")
        self.assertEqual(response.status_code, 202)
        data = response.json()
        self.assertEqual(data["status"], "ACCEPTED")
        self.assertTrue(data["job_id"].startswith("sync-meta-"))


if __name__ == "__main__":
    unittest.main()
