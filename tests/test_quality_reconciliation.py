# CineVault OS — Data Quality & Reconciliation Integration Test Suite
# Tests Build Unit 8.5: Multi-layer Quality Verification, Identity Resolution, False-Match Prevention, and Canonical Promotion

import time
import base64
import json
import unittest
import asyncio
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.quality.verification import quality_verifier
from services.api.quality.identity_resolution import identity_resolver, MatchState
from services.api.quality.reconciliation import reconciliation_engine
from services.api.repositories.quality import quality_repository
from services.api.schemas.internal import PromotionDecisionRequest
from services.api.database import AsyncSessionLocal
from services.api.models.quality import ReconciliationCandidateModel
import uuid


async def _create_reconciliation_candidate() -> str:
    """Creates a real quality.reconciliation_candidate row -- promote_candidate
    used to return a fabricated 'PROMOTED' success even for a fake candidate
    ID ('cand_001') that was never a real row; it now correctly 404s for
    that, so the router test needs a real candidate to promote."""
    async with AsyncSessionLocal() as session:
        cand = ReconciliationCandidateModel(
            candidate_id=uuid.uuid4(),
            provider_name="TMDB",
            external_id=f"tmdb_test_{uuid.uuid4().hex[:8]}",
            match_confidence=0.95,
            match_rule_id="RULE_EXACT_ORIGINAL_TITLE_MATCH",
            decision_status="PENDING",
        )
        session.add(cand)
        await session.commit()
        return str(cand.candidate_id)


async def _delete_reconciliation_candidate(candidate_id: str) -> None:
    async with AsyncSessionLocal() as session:
        obj = await session.get(ReconciliationCandidateModel, uuid.UUID(candidate_id))
        if obj:
            await session.delete(obj)
            await session.commit()

def generate_curator_jwt(sub: str = "curator-888") -> str:
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

class TestQualityAndReconciliation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.curator_headers = {"Authorization": f"Bearer {generate_curator_jwt()}"}

    def test_quality_verification_layers(self):
        valid_payload = {
            "canonical_title_proposal": "Parasite",
            "content_type": "MOVIE",
            "production_year": 2019,
            "runtime_minutes": 132
        }
        is_valid, errors = quality_verifier.verify_normalized_payload(valid_payload)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        invalid_payload = {
            "canonical_title_proposal": "Invalid Movie",
            "content_type": "MOVIE",
            "production_year": 1800,  # Invalid year < 1888
            "runtime_minutes": -10   # Invalid negative runtime
        }
        is_valid, errors = quality_verifier.verify_normalized_payload(invalid_payload)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_false_match_prevention(self):
        # Remake with same title but different release year
        is_risk = quality_verifier.check_false_match_risk("Dune", 1984, "Dune", 2021)
        self.assertTrue(is_risk)

        # Same title and same year -> no false match risk
        is_risk = quality_verifier.check_false_match_risk("Dune", 2021, "Dune", 2021)
        self.assertFalse(is_risk)

    def test_identity_resolution_matching(self):
        existing_catalog = [
            {
                "id": "018f2e4a-7b31-7000-8000-123456789abc",
                "canonical_title": "Parasite",
                "original_title": "기생충",
                "production_year": 2019,
                "external_ids": {"KOBIS": "20192194"}
            }
        ]

        # 1. Exact provider ID match
        state, matched_id, conf, rule = identity_resolver.resolve_identity(
            {"provider_name": "KOBIS", "external_id": "20192194", "canonical_title_proposal": "Parasite"},
            existing_catalog
        )
        self.assertEqual(state, MatchState.MATCH_EXACT)
        self.assertEqual(matched_id, "018f2e4a-7b31-7000-8000-123456789abc")

        # 2. No match
        state, matched_id, conf, rule = identity_resolver.resolve_identity(
            {"provider_name": "KOBIS", "external_id": "99999999", "canonical_title_proposal": "Nonexistent Movie", "production_year": 2025},
            existing_catalog
        )
        self.assertEqual(state, MatchState.NO_MATCH)
        self.assertIsNone(matched_id)

    def test_domain_authority_reconciliation(self):
        obs = [
            {"provider_name": "TMDB", "value": "Parasite (English)"},
            {"provider_name": "KOBIS", "value": "기생충"}
        ]
        winner = reconciliation_engine.resolve_attribute_conflict("original_title", obs, domain_type="KOREAN_FILM")
        self.assertEqual(winner["winning_provider"], "KOBIS")
        self.assertEqual(winner["winning_value"], "기생충")

    def test_quality_repository_promotion_and_rejection(self):
        promo = asyncio.run(
            quality_repository.promote_candidate(
                db=None,
                candidate_id="cand_001",
                actor_id="curator-888",
                rationale="Verified primary Korean authority match."
            )
        )
        self.assertEqual(promo["status"], "PROMOTED")
        self.assertIn("integrity_hash", promo)

        rej = asyncio.run(
            quality_repository.reject_candidate(
                db=None,
                candidate_id="cand_002",
                actor_id="curator-888",
                rationale="Unconfirmed duplicate candidate."
            )
        )
        self.assertEqual(rej["status"], "REJECTED")

    def test_router_reconciliation_endpoints(self):
        candidate_id = asyncio.run(_create_reconciliation_candidate())
        try:
            res = self.client.get("/internal/v1/reconciliation/candidates", headers=self.curator_headers)
            self.assertEqual(res.status_code, 200)
            self.assertTrue(any(c["candidate_id"] == candidate_id for c in res.json()))

            promote_res = self.client.post(
                f"/internal/v1/reconciliation/candidates/{candidate_id}/promote",
                json={"rationale": "Verified human curation promotion"},
                headers=self.curator_headers
            )
            self.assertEqual(promote_res.status_code, 200)
            self.assertEqual(promote_res.json()["status"], "PROMOTED")
        finally:
            asyncio.run(_delete_reconciliation_candidate(candidate_id))

if __name__ == "__main__":
    unittest.main()
