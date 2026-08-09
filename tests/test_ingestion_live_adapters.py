# CineVault OS — Live Ingestion Provider Adapters Unit & Retry Tests (Phase 9.6)

import pytest
import unittest
import httpx
from unittest.mock import AsyncMock, MagicMock
from services.api.ingestion.adapters import KobisProviderAdapter, TvdbProviderAdapter


class TestKobisProviderAdapter(unittest.IsolatedAsyncioTestCase):

    async def test_kobis_mock_mode_default(self):
        adapter = KobisProviderAdapter(api_key=None)
        adapter.ingestion_mode = "mock"

        raw = await adapter.fetch_raw_payload("MOVIE", "20192194")
        self.assertEqual(raw["movieCd"], "20192194")

        normalized = adapter.normalize_payload(raw)
        self.assertEqual(normalized["provider_name"], "KOBIS")
        self.assertEqual(normalized["canonical_title_proposal"], "Parasite")
        self.assertEqual(normalized["production_year"], 2019)

    async def test_kobis_live_mode_http_success(self):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "movieInfoResult": {
                "movieInfo": {
                    "movieCd": "20201234",
                    "movieNm": "한산",
                    "movieNmEn": "Hansan: Rising Dragon",
                    "prdtYear": "2022",
                    "genres": [{"genreNm": "Action"}, {"genreNm": "History"}],
                    "directors": [{"peopleNm": "김한민"}],
                    "actors": [{"peopleNm": "박해일"}]
                }
            }
        }
        mock_client.get.return_value = mock_response

        adapter = KobisProviderAdapter(api_key="mock-kobis-key", http_client=mock_client)
        adapter.ingestion_mode = "live"

        raw = await adapter.fetch_raw_payload("MOVIE", "20201234")
        self.assertEqual(raw["movieCd"], "20201234")

        normalized = adapter.normalize_payload(raw)
        self.assertEqual(normalized["canonical_title_proposal"], "Hansan: Rising Dragon")
        self.assertEqual(normalized["production_year"], 2022)
        self.assertIn("Action", normalized["genres"])

    async def test_kobis_live_mode_retry_resilience(self):
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        fail_response = MagicMock()
        fail_response.raise_for_status.side_effect = httpx.HTTPStatusError("500 Internal Error", request=MagicMock(), response=MagicMock())

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.raise_for_status = MagicMock()
        success_response.json.return_value = {
            "movieInfoResult": {
                "movieInfo": {
                    "movieCd": "20201234",
                    "movieNmEn": "Retried Title"
                }
            }
        }

        mock_client.get.side_effect = [fail_response, success_response]

        adapter = KobisProviderAdapter(api_key="mock-kobis-key", http_client=mock_client)
        adapter.ingestion_mode = "live"

        raw = await adapter.fetch_raw_payload("MOVIE", "20201234")
        self.assertEqual(raw["movieNmEn"], "Retried Title")
        self.assertEqual(mock_client.get.call_count, 2)


class TestTvdbProviderAdapter(unittest.IsolatedAsyncioTestCase):

    async def test_tvdb_mock_mode_default(self):
        adapter = TvdbProviderAdapter(api_key=None)
        adapter.ingestion_mode = "mock"

        raw = await adapter.fetch_raw_payload("TV_SERIES", "364014")
        self.assertEqual(raw["id"], 364014)

        normalized = adapter.normalize_payload(raw)
        self.assertEqual(normalized["provider_name"], "TVDB")
        self.assertEqual(normalized["canonical_title_proposal"], "Squid Game")
        self.assertEqual(normalized["production_year"], 2021)

    async def test_tvdb_live_mode_auth_and_fetch_success(self):
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        login_response = MagicMock()
        login_response.status_code = 200
        login_response.raise_for_status = MagicMock()
        login_response.json.return_value = {"data": {"token": "test-tvdb-bearer-token"}}

        series_response = MagicMock()
        series_response.status_code = 200
        series_response.raise_for_status = MagicMock()
        series_response.json.return_value = {
            "data": {
                "id": 999123,
                "name": "All of Us Are Dead",
                "originalName": "지금 우리 학교는",
                "year": 2022,
                "overview": "Zombie outbreak in high school.",
                "genres": [{"name": "Action"}, {"name": "Horror"}]
            }
        }

        mock_client.post.return_value = login_response
        mock_client.get.return_value = series_response

        adapter = TvdbProviderAdapter(api_key="mock-tvdb-key", http_client=mock_client)
        adapter.ingestion_mode = "live"

        raw = await adapter.fetch_raw_payload("TV_SERIES", "999123")
        self.assertEqual(raw["name"], "All of Us Are Dead")

        normalized = adapter.normalize_payload(raw)
        self.assertEqual(normalized["canonical_title_proposal"], "All of Us Are Dead")
        self.assertEqual(normalized["production_year"], 2022)
        self.assertIn("Horror", normalized["genres"])


if __name__ == "__main__":
    unittest.main()
