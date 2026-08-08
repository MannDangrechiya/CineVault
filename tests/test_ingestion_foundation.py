# CineVault OS — Ingestion Foundation Integration Test Suite
# Tests Build Unit 8.4: Source Licensing Gate, Immutable Raw Capture, Provider Adapters & Quarantine Staging

import time
import base64
import json
import unittest
import asyncio
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.ingestion.licensing import licensing_gate, SourceAccessStatus, AuthorityRole
from services.api.ingestion.adapters import KobisProviderAdapter, TvdbProviderAdapter, compute_payload_checksum
from services.api.repositories.ingestion import ingestion_repository

def generate_curator_jwt(sub: str = "curator-999") -> str:
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

class TestIngestionFoundation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.curator_headers = {"Authorization": f"Bearer {generate_curator_jwt()}"}

    def test_licensing_gate_permits_authorized_sources(self):
        kobis_gate = licensing_gate.verify_source_access("KOBIS")
        self.assertTrue(kobis_gate["gate_passed"])
        self.assertEqual(kobis_gate["authority_role"], AuthorityRole.PRIMARY_KOREAN.value)

        tvdb_gate = licensing_gate.verify_source_access("TVDB")
        self.assertTrue(tvdb_gate["gate_passed"])
        self.assertEqual(tvdb_gate["authority_role"], AuthorityRole.SECONDARY_TV.value)

    def test_licensing_gate_blocks_prohibited_sources_and_scraping(self):
        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("JUSTWATCH")

        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("IMDB_DATASETS")

        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("KOBIS", is_scraping_attempt=True)

    def test_payload_sha256_checksum(self):
        payload = {"movieCd": "20192194", "movieNm": "Parasite"}
        checksum = compute_payload_checksum(payload)
        self.assertEqual(len(checksum), 64)
        self.assertIsInstance(checksum, str)

    def test_kobis_adapter_fetch_and_normalize(self):
        adapter = KobisProviderAdapter()
        raw = asyncio.run(adapter.fetch_raw_payload("MOVIE", "20192194"))
        self.assertEqual(raw["movieNm"], "기생충")

        normalized = adapter.normalize_payload(raw)
        self.assertEqual(normalized["provider_name"], "KOBIS")
        self.assertEqual(normalized["original_title"], "기생충")
        self.assertEqual(normalized["content_type"], "MOVIE")

    def test_tvdb_adapter_fetch_and_normalize(self):
        adapter = TvdbProviderAdapter()
        raw = asyncio.run(adapter.fetch_raw_payload("TV_SERIES", "364014"))
        self.assertEqual(raw["name"], "Squid Game")

        normalized = adapter.normalize_payload(raw)
        self.assertEqual(normalized["provider_name"], "TVDB")
        self.assertEqual(normalized["content_type"], "TV_SERIES")

    def test_ingestion_repository_raw_capture_and_quarantine(self):
        payload = {"test_key": "test_value"}
        capture = asyncio.run(
            ingestion_repository.capture_raw_payload(
                db=None,
                provider_name="KOBIS",
                external_entity_type="MOVIE",
                external_entity_id="20192194",
                raw_payload=payload
            )
        )
        self.assertIsNotNone(capture["raw_payload_id"])
        self.assertEqual(capture["provider_name"], "KOBIS")
        self.assertEqual(len(capture["payload_checksum"]), 64)

        quarantine = asyncio.run(
            ingestion_repository.stage_quarantine_record(
                db=None,
                provider_name="KOBIS",
                failure_category="SCHEMA_VALIDATION_ERROR",
                diagnostic_details={"error": "Missing mandatory title field"}
            )
        )
        self.assertEqual(quarantine["review_status"], "PENDING")

    def test_internal_ingestion_runs_endpoint(self):
        res = self.client.get("/internal/v1/ingestion/runs", headers=self.curator_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_internal_raw_payload_endpoint(self):
        res = self.client.get("/internal/v1/ingestion/raw-payloads/raw-12345", headers=self.curator_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("payload_hash", data)
        self.assertIn("payload_data", data)

if __name__ == "__main__":
    unittest.main()
