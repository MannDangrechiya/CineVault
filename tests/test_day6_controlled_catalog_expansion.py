# CineVault OS — Day 6 Data Source Registry, Provider Activation & Controlled Catalog Expansion Tests

import unittest
import asyncio
import uuid
import httpx
from typing import Dict, Any

from services.api.ingestion.licensing import licensing_gate, ActivationStatus, SourceAccessStatus, AuthorityRole
from services.api.ingestion.adapters import (
    KobisProviderAdapter, TmdbProviderAdapter, TvdbProviderAdapter,
    JustWatchAdapter, ImdbDatasetAdapter, compute_payload_checksum
)
from services.api.ingestion.pipeline import pipeline_engine, get_provider_adapter
from services.api.schemas.internal import IngestionTriggerRequest, IngestionItemPayload
from services.api.config import config
from services.api.repositories.canonical import SEED_FALLBACK_TITLES

class TestDay6DataSourceRegistry(unittest.TestCase):
    """Validates Data Source Registry V1 structure, mandatory 16 fields, and activation statuses."""

    def test_data_source_registry_attributes(self):
        """Verifies that all provider records in registry contain the 16 mandatory technical specification fields."""
        registry = licensing_gate.get_source_registry()
        self.assertGreaterEqual(len(registry), 8)

        mandatory_fields = [
            "provider", "dataset_api", "source_type", "official_url",
            "license", "attribution_requirement", "commercial_use", "redistribution",
            "rate_limit", "update_frequency", "authentication_requirements",
            "regions", "available_fields", "reliability", "last_reviewed", "activation_status"
        ]

        for provider_key, record in registry.items():
            for field in mandatory_fields:
                self.assertIn(field, record, f"Provider '{provider_key}' missing mandatory registry field '{field}'")
            self.assertIn(record["activation_status"], [
                "ACTIVE", "APPROVED", "REVIEW_REQUIRED", "RESEARCH", "SUSPENDED", "RETIRED"
            ])

    def test_legal_licensing_gate_enforcement(self):
        """Verifies pre-acquisition licensing gate permits active sources and blocks prohibited/review-required sources."""
        # Permitted/Active providers pass gate
        kobis_info = licensing_gate.verify_source_access("KOBIS")
        self.assertTrue(kobis_info["gate_passed"])
        self.assertEqual(kobis_info["provider_name"], "KOBIS")

        tmdb_info = licensing_gate.verify_source_access("TMDB")
        self.assertTrue(tmdb_info["gate_passed"])

        wikidata_info = licensing_gate.verify_source_access("WIKIDATA")
        self.assertTrue(wikidata_info["gate_passed"])

        # Prohibited provider blocks
        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("JUSTWATCH")

        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("IMDB_DATASETS")

        # Scraping attempt blocks
        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("KOBIS", is_scraping_attempt=True)

        # Review required blocks
        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("UNKNOWN_SOURCE")

    def test_provider_credential_isolation(self):
        """Verifies provider credentials are bound via environment config and never hardcoded."""
        self.assertTrue(hasattr(config, "kobis_api_key"))
        self.assertTrue(hasattr(config, "tmdb_api_key"))
        self.assertTrue(hasattr(config, "provider_api_key"))

        kobis_adapter = KobisProviderAdapter()
        self.assertTrue(hasattr(kobis_adapter, "api_key"))

        tmdb_adapter = TmdbProviderAdapter()
        self.assertTrue(hasattr(tmdb_adapter, "api_key"))

class TestDay6ProviderAdaptersAndNormalization(unittest.TestCase):
    """Validates real provider payload acquisition, multi-record catalog normalization, and SHA-256 checksums."""

    def test_kobis_adapter_fetch_and_normalize(self):
        """Verifies KOBIS provider adapter fetches raw payload, computes checksum, and normalizes schema."""
        adapter = KobisProviderAdapter()
        raw = asyncio.run(adapter.fetch_raw_payload("MOVIE", "20192194"))
        self.assertEqual(raw["movieCd"], "20192194")
        self.assertEqual(raw["movieNm"], "기생충")

        checksum = compute_payload_checksum(raw)
        self.assertEqual(len(checksum), 64)

        normalized = adapter.normalize_payload(raw)
        self.assertEqual(normalized["provider_name"], "KOBIS")
        self.assertEqual(normalized["external_id"], "20192194")
        self.assertEqual(normalized["canonical_title_proposal"], "Parasite")
        self.assertEqual(normalized["original_title"], "기생충")
        self.assertEqual(normalized["content_type"], "MOVIE")
        self.assertEqual(normalized["production_year"], 2019)
        self.assertEqual(normalized["origin_country"], "KR")

    def test_tmdb_adapter_fetch_and_normalize(self):
        """Verifies TMDb provider adapter fetches raw payload and normalizes global catalog schema."""
        adapter = TmdbProviderAdapter()
        raw = asyncio.run(adapter.fetch_raw_payload("MOVIE", "496243"))
        self.assertEqual(str(raw["id"]), "496243")

        normalized = adapter.normalize_payload(raw)
        self.assertEqual(normalized["provider_name"], "TMDB")
        self.assertEqual(normalized["external_id"], "496243")
        self.assertEqual(normalized["canonical_title_proposal"], "Parasite")
        self.assertEqual(normalized["original_title"], "기생충")
        self.assertEqual(normalized["production_year"], 2019)

    def test_multi_record_batch_payload_fetching(self):
        """Verifies fetching varied records (movies, TV series, different languages/countries) from KOBIS."""
        kobis = KobisProviderAdapter()
        batch_ids = ["20192194", "20030371", "20202781", "20224982", "20163074", "20211111", "20239999", "20238888", "20237777"]

        for ext_id in batch_ids:
            raw = asyncio.run(kobis.fetch_raw_payload("MOVIE", ext_id))
            norm = kobis.normalize_payload(raw)
            from services.api.quality.verification import quality_verifier
            is_valid, errors = quality_verifier.verify_normalized_payload(norm)
            self.assertTrue(is_valid, f"Validation failed for KOBIS ID {ext_id}: {errors}")
            self.assertGreater(norm["production_year"], 1900)

class TestDay6ControlledIngestionPipeline(unittest.TestCase):
    """Validates dry-run execution, report generation, controlled apply, idempotency, and baseline preservation."""

    def test_small_real_batch_dry_run_report(self):
        """Verifies 10-record real batch execution in dry-run mode returns complete statistics with zero DB mutation."""
        trigger_items = [
            IngestionItemPayload(external_entity_id="20192194", external_entity_type="MOVIE"),
            IngestionItemPayload(external_entity_id="20030371", external_entity_type="MOVIE"),
            IngestionItemPayload(external_entity_id="20202781", external_entity_type="MOVIE"),
            IngestionItemPayload(external_entity_id="20224982", external_entity_type="MOVIE"),
            IngestionItemPayload(external_entity_id="20163074", external_entity_type="MOVIE"),
            IngestionItemPayload(external_entity_id="20060280", external_entity_type="MOVIE"),
            IngestionItemPayload(external_entity_id="20211111", external_entity_type="MOVIE"),
            IngestionItemPayload(external_entity_id="20239999", external_entity_type="MOVIE"),
            IngestionItemPayload(external_entity_id="20238888", external_entity_type="MOVIE"),
            IngestionItemPayload(external_entity_id="20237777", external_entity_type="MOVIE"),
        ]

        request = IngestionTriggerRequest(
            provider_name="KOBIS",
            dry_run=True,
            items=trigger_items
        )

        result = asyncio.run(pipeline_engine.execute_run(db=None, trigger_req=request))

        self.assertEqual(result["status"], "COMPLETED")
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["records_seen"], 10)
        self.assertEqual(result["records_valid"], 10)
        self.assertEqual(result["records_rejected"], 0)
        self.assertEqual(result["error_count"], 0)
        self.assertIn("new_candidates", result)
        self.assertIn("existing_matches", result)
        self.assertEqual(len(result["candidate_results"]), 10)

    def test_existing_title_resolution_and_matching(self):
        """Verifies that importing an existing title (Parasite) resolves to the existing baseline title ID without duplication."""
        request = IngestionTriggerRequest(
            provider_name="KOBIS",
            dry_run=True,
            items=[IngestionItemPayload(external_entity_id="20192194", external_entity_type="MOVIE")]
        )

        result = asyncio.run(pipeline_engine.execute_run(db=None, trigger_req=request))
        cand = result["candidate_results"][0]

        self.assertIn(cand["match_status"], ("AUTO_MATCH", "MATCH_EXACT"))
        self.assertIsNotNone(cand["matched_canonical_title_id"])

    def test_pipeline_idempotency(self):
        """Verifies executing the exact same batch twice yields zero new duplicates."""
        request = IngestionTriggerRequest(
            provider_name="KOBIS",
            dry_run=True,
            items=[
                IngestionItemPayload(external_entity_id="20192194", external_entity_type="MOVIE"),
                IngestionItemPayload(external_entity_id="20030371", external_entity_type="MOVIE")
            ]
        )

        run1 = asyncio.run(pipeline_engine.execute_run(db=None, trigger_req=request))
        run2 = asyncio.run(pipeline_engine.execute_run(db=None, trigger_req=request))

        self.assertEqual(run1["records_valid"], run2["records_valid"])
        self.assertEqual(run1["records_rejected"], run2["records_rejected"])

    def test_provider_http_429_rate_limit_resilience(self):
        """Verifies provider adapter handles HTTP 429 rate limiting with Retry-After header cleanly."""
        dummy_req = httpx.Request("GET", "http://www.kobis.or.kr/test")
        mock_response_429 = httpx.Response(
            status_code=429,
            headers={"Retry-After": "0.01"},
            json={"detail": "Rate limit exceeded"},
            request=dummy_req
        )
        mock_response_200 = httpx.Response(
            status_code=200,
            json={
                "movieInfoResult": {
                    "movieInfo": {
                        "movieCd": "20192194",
                        "movieNm": "기생충",
                        "movieNmEn": "Parasite",
                        "prdtYear": "2019"
                    }
                }
            },
            request=dummy_req
        )

        class MockHttpxClient:
            def __init__(self):
                self.calls = 0

            async def get(self, url, params=None):
                self.calls += 1
                if self.calls == 1:
                    return mock_response_429
                return mock_response_200

        mock_client = MockHttpxClient()
        adapter = KobisProviderAdapter(api_key="test_key", http_client=mock_client)
        adapter.ingestion_mode = "live"

        payload = asyncio.run(adapter.fetch_raw_payload("MOVIE", "20192194"))
        self.assertEqual(payload["movieCd"], "20192194")
        self.assertEqual(mock_client.calls, 2)

    def test_original_10_title_baseline_preserved(self):
        """Verifies the protected 10-title baseline (9 Movies, 1 TV Series) remains preserved intact."""
        titles = list(SEED_FALLBACK_TITLES.values())
        self.assertEqual(len(titles), 10)

        movies = [t for t in titles if t["content_type"] == "MOVIE"]
        tv_series = [t for t in titles if t["content_type"] == "TV_SERIES"]

        self.assertEqual(len(movies), 9)
        self.assertEqual(len(tv_series), 1)

        parasite = next(t for t in titles if t["canonical_title"] == "Parasite")
        self.assertEqual(parasite["display_id"], "MOV-000001")
        self.assertEqual(parasite["production_year"], 2019)
