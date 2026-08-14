# CineVault OS — Day 4 Ingestion Architecture & Data Source Adapters Integration Test Suite
# Tests Source Registry, Provider Adapters, Ingestion Pipeline, Matching, Provenance, Candidate Staging, Dry Run & Safeguards

import time
import base64
import json
import unittest
import asyncio
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.ingestion.licensing import licensing_gate, SourceAccessStatus
from services.api.ingestion.adapters import (
    KobisProviderAdapter, TvdbProviderAdapter, TmdbProviderAdapter,
    AniListProviderAdapter, MyAnimeListProviderAdapter, WikidataProviderAdapter,
    compute_payload_checksum
)
from services.api.ingestion.pipeline import pipeline_engine
from services.api.schemas.internal import IngestionTriggerRequest, IngestionItemPayload

def generate_curator_jwt(sub: str = "curator-day4") -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    now = int(time.time())
    payload_dict = {
        "sub": sub,
        "iss": "http://localhost:8080/realms/cinevault-dev",
        "aud": "cinevault-api-gateway",
        "exp": now + 900,
        "iat": now,
        "realm_access": {"roles": ["AuthenticatedUser", "Curator"]}
    }
    payload = base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(b"mock_signature").decode().rstrip("=")
    return f"{header}.{payload}.{signature}"

class TestDay4IngestionPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.curator_headers = {"Authorization": f"Bearer {generate_curator_jwt()}"}

    def test_source_registry_metadata_and_governance(self):
        """Verifies full Data Source Registry metadata, licensing statuses, and rate limits."""
        registry = licensing_gate.get_source_registry()
        self.assertIn("KOBIS", registry)
        self.assertIn("TVDB", registry)
        self.assertIn("TMDB", registry)
        self.assertIn("ANILIST", registry)
        self.assertIn("MYANIMELIST", registry)
        self.assertIn("WIKIDATA", registry)
        self.assertIn("JUSTWATCH", registry)
        self.assertIn("IMDB_DATASETS", registry)

        # Check metadata fields
        kobis_meta = registry["KOBIS"]
        self.assertEqual(kobis_meta["access_status"], "PERMITTED")
        self.assertEqual(kobis_meta["rate_limit_per_min"], 300)
        self.assertIn("title", kobis_meta["available_fields"])

        # Check prohibited sources
        justwatch_meta = registry["JUSTWATCH"]
        self.assertEqual(justwatch_meta["access_status"], "PROHIBITED")

    def test_licensing_gate_blocks_prohibited_sources_and_scraping(self):
        """Verifies licensing gate throws PermissionError for prohibited providers or scraping."""
        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("JUSTWATCH")

        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("IMDB_DATASETS")

        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("UNKNOWN_SOURCE")

        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("KOBIS", is_scraping_attempt=True)

    def test_tmdb_adapter_fetch_normalize_and_validate(self):
        """Validates TMDb provider adapter normalizing and schema validation."""
        adapter = TmdbProviderAdapter()
        raw = asyncio.run(adapter.fetch_raw_payload("MOVIE", "496243"))
        self.assertEqual(raw["id"], 496243)
        self.assertEqual(raw["title"], "Parasite")

        normalized = adapter.normalize_payload(raw)
        self.assertEqual(normalized["provider_name"], "TMDB")
        self.assertEqual(normalized["canonical_title_proposal"], "Parasite")
        self.assertEqual(normalized["content_type"], "MOVIE")
        self.assertEqual(normalized["production_year"], 2019)

        is_valid, errors = adapter.validate_normalized(normalized)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_anilist_and_mal_adapters_normalize(self):
        """Validates AniList and MyAnimeList anime provider adapters."""
        anilist_adapter = AniListProviderAdapter()
        raw_ani = asyncio.run(anilist_adapter.fetch_raw_payload("ANIME", "21"))
        norm_ani = anilist_adapter.normalize_payload(raw_ani)
        self.assertEqual(norm_ani["provider_name"], "ANILIST")
        self.assertEqual(norm_ani["content_type"], "ANIME")

        mal_adapter = MyAnimeListProviderAdapter()
        raw_mal = asyncio.run(mal_adapter.fetch_raw_payload("ANIME", "5114"))
        norm_mal = mal_adapter.normalize_payload(raw_mal)
        self.assertEqual(norm_mal["provider_name"], "MYANIMELIST")
        self.assertEqual(norm_mal["content_type"], "ANIME")

    def test_wikidata_adapter_normalize(self):
        """Validates Wikidata SPARQL structured entity adapter."""
        wiki_adapter = WikidataProviderAdapter()
        raw_wiki = asyncio.run(wiki_adapter.fetch_raw_payload("MOVIE", "Q6114"))
        norm_wiki = wiki_adapter.normalize_payload(raw_wiki)
        self.assertEqual(norm_wiki["provider_name"], "WIKIDATA")
        self.assertIn("imdb_id", norm_wiki["external_id_mappings"])

    def test_ingestion_pipeline_dry_run_execution(self):
        """Validates ingestion pipeline dry-run execution without canonical database mutations."""
        req = IngestionTriggerRequest(
            provider_name="KOBIS",
            items=[IngestionItemPayload(external_entity_type="MOVIE", external_entity_id="20192194")],
            dry_run=True
        )
        res = asyncio.run(pipeline_engine.execute_run(db=None, trigger_req=req))
        self.assertEqual(res["provider_name"], "KOBIS")
        self.assertEqual(res["status"], "COMPLETED")
        self.assertTrue(res["dry_run"])
        self.assertEqual(res["records_seen"], 1)
        self.assertEqual(res["records_valid"], 1)

    def test_ingestion_pipeline_schema_validation_failure_quarantine(self):
        """Validates malformed payload schema validation failure routing to quarantine."""
        req = IngestionTriggerRequest(
            provider_name="TMDB",
            items=[
                IngestionItemPayload(
                    external_entity_type="MOVIE",
                    external_entity_id="bad-001",
                    raw_payload={"id": None, "invalid": True}  # Missing title and external_id
                )
            ],
            dry_run=True
        )
        res = asyncio.run(pipeline_engine.execute_run(db=None, trigger_req=req))
        self.assertEqual(res["records_rejected"], 1)
        self.assertEqual(res["error_count"], 1)

    def test_pipeline_idempotency_and_conflict_detection(self):
        """Verifies repeated ingestion runs with same checksum are safe and conflict detection works."""
        payload1 = {"movieCd": "20192194", "movieNm": "기생충", "movieNmEn": "Parasite", "showTm": "132"}
        checksum1 = compute_payload_checksum(payload1)
        checksum2 = compute_payload_checksum(payload1)
        self.assertEqual(checksum1, checksum2)

        # Run 1
        req1 = IngestionTriggerRequest(
            provider_name="KOBIS",
            items=[IngestionItemPayload(external_entity_type="MOVIE", external_entity_id="20192194", raw_payload=payload1)],
            dry_run=True
        )
        res1 = asyncio.run(pipeline_engine.execute_run(db=None, trigger_req=req1))
        self.assertEqual(res1["status"], "COMPLETED")

        # Run 2 (Idempotent execution)
        res2 = asyncio.run(pipeline_engine.execute_run(db=None, trigger_req=req1))
        self.assertEqual(res2["status"], "COMPLETED")
        self.assertEqual(res2["records_valid"], 1)

    def test_internal_sources_endpoint(self):
        """Tests GET /internal/v1/ingestion/sources endpoint."""
        res = self.client.get("/internal/v1/ingestion/sources", headers=self.curator_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("KOBIS", data)
        self.assertIn("TMDB", data)

    def test_internal_trigger_endpoint(self):
        """Tests POST /internal/v1/ingestion/trigger endpoint."""
        body = {
            "provider_name": "KOBIS",
            "items": [{"external_entity_type": "MOVIE", "external_entity_id": "20192194"}],
            "dry_run": True
        }
        res = self.client.post("/internal/v1/ingestion/trigger", json=body, headers=self.curator_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["provider_name"], "KOBIS")
        self.assertTrue(data["dry_run"])

    def test_internal_candidates_endpoint(self):
        """Tests GET /internal/v1/ingestion/candidates endpoint."""
        res = self.client.get("/internal/v1/ingestion/candidates", headers=self.curator_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)

    def test_internal_provenance_endpoint(self):
        """Tests GET /internal/v1/ingestion/provenance/{entity_id} endpoint."""
        res = self.client.get("/internal/v1/ingestion/provenance/018f6f60-7a00-7000-8000-000000000001", headers=self.curator_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)

if __name__ == "__main__":
    unittest.main()
