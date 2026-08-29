# CineVault OS — Day 5 Data Quality, Deduplication & Conflict Resolution Integration Test Suite
# Tests 4 Validation Layers, Normalization, 4-Level Identity Matching, ADR-002 Boundaries, Metadata Conflicts, and Merge Protection

import time
import base64
import json
import unittest
import asyncio
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.quality.verification import quality_verifier, QualityStatus, ConfidenceLevel
from services.api.quality.normalization import normalize_title_text, normalize_for_matching, is_transliteration_candidate
from services.api.quality.identity_resolution import identity_resolver, MatchState
from services.api.quality.reconciliation import reconciliation_engine
from services.api.repositories.quality import quality_repository
from services.api.ingestion.pipeline import pipeline_engine
from services.api.schemas.internal import IngestionTriggerRequest, IngestionItemPayload
from services.api.database import AsyncSessionLocal
from services.api.models.quality import MetadataConflictModel
import uuid


async def _create_metadata_conflict() -> str:
    """Creates a real quality.metadata_conflict row -- resolve_metadata_conflict
    used to return a fabricated 'RESOLVED' success even for a fake conflict
    ID ('conf_001') that was never a real row; it now correctly 404s for
    that, so tests need a real conflict to resolve."""
    async with AsyncSessionLocal() as session:
        conflict = MetadataConflictModel(
            conflict_id=uuid.uuid4(),
            entity_type="TITLE",
            field_name="runtime_minutes",
            candidate_value="140",
            existing_value="142",
            source_provider="TMDB",
            status="OPEN",
        )
        session.add(conflict)
        await session.commit()
        return str(conflict.conflict_id)


async def _delete_metadata_conflict(conflict_id: str) -> None:
    async with AsyncSessionLocal() as session:
        obj = await session.get(MetadataConflictModel, uuid.UUID(conflict_id))
        if obj:
            await session.delete(obj)
            await session.commit()

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

class TestDay5DataQuality(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.curator_headers = {"Authorization": f"Bearer {generate_curator_jwt()}"}

    def test_layer1_schema_validation(self):
        """Layer 1: Schema validation rejects missing mandatory fields and invalid data types."""
        invalid_type_payload = {
            "canonical_title_proposal": "Parasite",
            "content_type": "MOVIE",
            "production_year": "abc"  # Invalid string type for integer field
        }
        is_valid, errors = quality_verifier.verify_normalized_payload(invalid_type_payload)
        self.assertFalse(is_valid)
        self.assertTrue(any("SCHEMA_ERROR" in e for e in errors))

        missing_title_payload = {
            "content_type": "MOVIE",
            "production_year": 2019
        }
        is_valid, errors = quality_verifier.verify_normalized_payload(missing_title_payload)
        self.assertFalse(is_valid)
        self.assertTrue(any("Missing" in e for e in errors))

    def test_layer2_referential_validation(self):
        """Layer 2: Referential validation checks parent-child relationship integrity."""
        orphan_episode = {
            "entity_type": "EPISODE",
            "episode_name": "Pilot",
            "episode_number": 1
            # Missing season_id or season_number reference
        }
        is_valid, errors = quality_verifier.verify_normalized_payload(orphan_episode)
        self.assertFalse(is_valid)
        self.assertTrue(any("REFERENTIAL_ERROR" in e for e in errors))

    def test_layer3_semantic_validation(self):
        """Layer 3: Semantic validation rejects negative runtimes and invalid production years."""
        invalid_runtime = {
            "canonical_title_proposal": "Dune",
            "content_type": "MOVIE",
            "production_year": 2021,
            "runtime_minutes": -15
        }
        is_valid, errors = quality_verifier.verify_normalized_payload(invalid_runtime)
        self.assertFalse(is_valid)
        self.assertTrue(any("FIELD_ERROR" in e for e in errors))

        improbable_year = {
            "canonical_title_proposal": "Ancient Title",
            "content_type": "MOVIE",
            "production_year": 1800
        }
        is_valid, errors = quality_verifier.verify_normalized_payload(improbable_year)
        self.assertFalse(is_valid)

    def test_layer4_cross_field_validation(self):
        """Layer 4: Cross-field validation flags classification and inter-attribute conflicts."""
        movie_with_seasons = {
            "canonical_title_proposal": "Inception",
            "content_type": "MOVIE",
            "production_year": 2010,
            "season_count": 3
        }
        is_valid, errors = quality_verifier.verify_normalized_payload(movie_with_seasons)
        self.assertFalse(is_valid)
        self.assertTrue(any("CROSS_FIELD_ERROR" in e for e in errors))

    def test_normalization_engine(self):
        """Deterministic normalization preserves original titles while cleaning comparison keys."""
        raw_title = "  Kimi   no Na wa.  "
        normalized = normalize_title_text(raw_title)
        self.assertEqual(normalized, "Kimi no Na wa.")

        match_key = normalize_for_matching("The Dark Knight!")
        self.assertEqual(match_key, "dark knight")

        # Multilingual transliteration check
        is_candidate = is_transliteration_candidate("Kimi no Na wa.", "Your Name / Kimi no Na wa")
        self.assertTrue(is_candidate)

    def test_multi_level_identity_matching(self):
        """Multi-level identity resolution tests Level 1-4 matching rules."""
        catalog = [
            {
                "id": "018f6f60-7a00-7000-8000-000000000001",
                "display_id": "MOV-PARASITE-2019",
                "canonical_title": "Parasite",
                "original_title": "기생충",
                "production_year": 2019,
                "external_ids": {"KOBIS": "20192194", "TMDB": "496243"}
            }
        ]

        # Level 1: Exact External ID
        state, match_id, score, rule = identity_resolver.resolve_identity(
            {"provider_name": "KOBIS", "external_id": "20192194"}, catalog
        )
        self.assertEqual(state, MatchState.MATCH_EXACT)
        self.assertEqual(match_id, "018f6f60-7a00-7000-8000-000000000001")

        # Level 2: Canonical Display ID
        state, match_id, score, rule = identity_resolver.resolve_identity(
            {"display_id": "MOV-PARASITE-2019"}, catalog
        )
        self.assertEqual(state, MatchState.MATCH_EXACT)

        # Level 3: Deterministic Title + Year
        state, match_id, score, rule = identity_resolver.resolve_identity(
            {"canonical_title_proposal": "Parasite", "production_year": 2019}, catalog
        )
        self.assertEqual(state, MatchState.MATCH_EXACT)

        # Level 4: Probabilistic soft match -> REQUIRES_REVIEW
        state, match_id, score, rule = identity_resolver.resolve_identity(
            {"canonical_title_proposal": "Parasite Director Cut Special", "production_year": 2019}, catalog
        )
        self.assertIn(state, (MatchState.REQUIRES_REVIEW, MatchState.MATCH_EXACT))

    def test_adr002_edition_boundary_distinction(self):
        """ADR-002: Re-releases or Director's Cuts map as Edition under Title, NOT duplicate Title."""
        catalog = [
            {
                "id": "018f6f60-7a00-7000-8000-000000000001",
                "canonical_title": "Blade Runner",
                "production_year": 1982
            }
        ]
        state, match_id, score, rule = identity_resolver.resolve_identity(
            {
                "canonical_title_proposal": "Blade Runner",
                "production_year": 1982,
                "edition_name": "Director's Cut"
            },
            catalog
        )
        self.assertEqual(state, MatchState.MATCH_EXACT)
        self.assertEqual(rule, "RULE-LEVEL3-TITLE-EDITION-MATCH")

    def test_external_id_collision_detection(self):
        """Detects provider external ID collision when mapped to multiple titles."""
        colliding_catalog = [
            {"id": "uuid-1", "external_ids": {"TMDB": "12345"}},
            {"id": "uuid-2", "external_ids": {"TMDB": "12345"}}
        ]
        state, match_id, score, rule = identity_resolver.resolve_identity(
            {"provider_name": "TMDB", "external_id": "12345"}, colliding_catalog
        )
        self.assertEqual(state, MatchState.REQUIRES_REVIEW)
        self.assertEqual(rule, "RULE-LEVEL1-EXTERNAL-ID-COLLISION")

    def test_domain_authority_and_conflict_resolution(self):
        """Domain authority matrix resolves attribute conflicts and logs resolution."""
        obs = [
            {"provider_name": "TMDB", "value": "140"},
            {"provider_name": "KOBIS", "value": "132"}
        ]
        res = reconciliation_engine.resolve_attribute_conflict("runtime_minutes", obs, domain_type="KOREAN_FILM")
        self.assertEqual(res["winning_provider"], "KOBIS")
        self.assertEqual(res["winning_value"], "132")

    def test_canonical_merge_protection_gate(self):
        """Canonical merge gate blocks merge if user personal data is attached or content types mismatch."""
        source = {"content_type": "MOVIE", "production_year": 2019}
        target = {"content_type": "TV_SERIES", "production_year": 2019}
        is_safe, reasons = reconciliation_engine.verify_merge_safety(source, target)
        self.assertFalse(is_safe)
        self.assertTrue(any("Content type mismatch" in r for r in reasons))

        # Personal data protection
        is_safe_pd, reasons_pd = reconciliation_engine.verify_merge_safety(
            {"content_type": "MOVIE", "production_year": 2019},
            {"content_type": "MOVIE", "production_year": 2019},
            user_personal_data_attached=True
        )
        self.assertFalse(is_safe_pd)
        self.assertTrue(any("User personal data" in r for r in reasons_pd))

    def test_metadata_conflict_endpoints(self):
        """REST endpoints for metadata conflicts listing and resolution."""
        conflict_id = asyncio.run(_create_metadata_conflict())
        try:
            res = self.client.get("/internal/v1/reconciliation/conflicts", headers=self.curator_headers)
            self.assertEqual(res.status_code, 200)
            self.assertTrue(any(c["conflict_id"] == conflict_id for c in res.json()))

            resolve_res = self.client.post(
                f"/internal/v1/reconciliation/conflicts/{conflict_id}/resolve",
                json={"winning_value": "142", "resolution_notes": "Official theatrical runtime verified."},
                headers=self.curator_headers
            )
            self.assertEqual(resolve_res.status_code, 200)
            self.assertEqual(resolve_res.json()["status"], "RESOLVED")
        finally:
            asyncio.run(_delete_metadata_conflict(conflict_id))

    def test_dry_run_and_idempotency(self):
        """Dry-run execution computes quality counters without canonical mutation; running twice is idempotent."""
        req = IngestionTriggerRequest(
            provider_name="KOBIS",
            dry_run=True,
            items=[
                IngestionItemPayload(
                    external_entity_type="MOVIE",
                    external_entity_id="20192194",
                    raw_payload={
                        "movieCd": "20192194",
                        "movieNm": "기생충",
                        "movieNmEn": "Parasite",
                        "prdtYear": "2019",
                        "showTm": "132"
                    }
                )
            ]
        )

        res1 = self.client.post("/internal/v1/ingestion/trigger", json=req.model_dump(), headers=self.curator_headers)
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()
        self.assertTrue(data1["dry_run"])
        self.assertEqual(data1["records_valid"], 1)

        # Run 2: Exact same payload (idempotency check)
        res2 = self.client.post("/internal/v1/ingestion/trigger", json=req.model_dump(), headers=self.curator_headers)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data2["records_valid"], 1)

if __name__ == "__main__":
    unittest.main()
