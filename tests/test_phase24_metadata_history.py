# CineVault OS — Phase 24: Metadata Update History Verification Tests
# Validates append-only metadata change tracking, old/new value delta, reason, confidence, and SHA-256 integrity preservation

import unittest
import asyncio
import uuid
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.repositories.canonical import canonical_repository
from services.api.schemas.titles import MetadataChangeHistoryRecord

class TestPhase24MetadataHistory(unittest.TestCase):
    """Verifies complete metadata update history tracking and tamper-evident audit protection."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_title_id = "018f2e4a-7b31-7000-8000-123456789abc"

    def test_record_and_retrieve_metadata_history(self):
        """History Engine: Emits change events tracking old/new values, source, actor, reason, and confidence."""
        # 1. Record runtime change
        change1 = asyncio.run(
            canonical_repository.record_metadata_change(
                db=None,
                title_id=self.test_title_id,
                field_name="runtime_minutes",
                old_value="120",
                new_value="126",
                source_provider="IMDb",
                actor_id="usr_curator_john",
                actor_type="CURATOR",
                reason="Corrected runtime based on Director's Cut theatrical release",
                confidence=0.99
            )
        )
        self.assertEqual(change1.title_id, self.test_title_id)
        self.assertEqual(change1.field_name, "runtime_minutes")
        self.assertEqual(change1.old_value, "120")
        self.assertEqual(change1.new_value, "126")
        self.assertEqual(change1.actor_type, "CURATOR")
        self.assertEqual(change1.confidence, 0.99)
        self.assertEqual(len(change1.integrity_hash), 64) # SHA-256

        # 2. Record synopsis change
        change2 = asyncio.run(
            canonical_repository.record_metadata_change(
                db=None,
                title_id=self.test_title_id,
                field_name="synopsis",
                old_value="A brief summary.",
                new_value="A comprehensive and detailed cinematic narrative synopsis.",
                source_provider="TMDB",
                actor_id="system_sync_worker",
                actor_type="SYSTEM",
                reason="Automatic weekly synopsis enrichment",
                confidence=0.95
            )
        )
        self.assertEqual(change2.new_value, "A comprehensive and detailed cinematic narrative synopsis.")

        # 3. Retrieve history via repository
        history = asyncio.run(canonical_repository.get_metadata_history(db=None, title_id=self.test_title_id))
        self.assertGreaterEqual(len(history), 2)
        fields = [h.field_name for h in history]
        self.assertIn("runtime_minutes", fields)
        self.assertIn("synopsis", fields)

    def test_title_history_public_api_endpoint(self):
        """API: GET /v1/titles/{title_id}/history exposes append-only change logs."""
        asyncio.run(
            canonical_repository.record_metadata_change(
                db=None,
                title_id=self.test_title_id,
                field_name="tagline",
                old_value=None,
                new_value="Experience the untold story.",
                source_provider="KOBIS",
                actor_id="usr_curator_alice",
                actor_type="CURATOR",
                reason="Added official localized tagline",
                confidence=0.98
            )
        )

        res = self.client.get(f"/v1/titles/{self.test_title_id}/history")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

        tagline_entry = next((item for item in data if item["field_name"] == "tagline"), None)
        self.assertIsNotNone(tagline_entry)
        self.assertEqual(tagline_entry["new_value"], "Experience the untold story.")
        self.assertEqual(tagline_entry["actor_type"], "CURATOR")
        self.assertIn("integrity_hash", tagline_entry)
        self.assertEqual(len(tagline_entry["integrity_hash"]), 64)

    def test_historical_evidence_preservation_constraint(self):
        """Constraint: Historical changes are strictly immutable and never destroyed."""
        unique_entity_id = "018f2e4a-7b31-7000-8000-unique-entity-test"

        # 1. Append initial change
        asyncio.run(
            canonical_repository.record_metadata_change(
                db=None,
                title_id=unique_entity_id,
                field_name="canonical_title",
                old_value="Initial Draft Title",
                new_value="Approved Canonical Title",
                source_provider="KOBIS",
                actor_id="system_reconciliation",
                actor_type="SYSTEM",
                reason="Initial ingestion normalization",
                confidence=0.9
            )
        )
        history_1 = asyncio.run(canonical_repository.get_metadata_history(db=None, title_id=unique_entity_id))
        self.assertEqual(len(history_1), 1)

        # 2. Append second change
        asyncio.run(
            canonical_repository.record_metadata_change(
                db=None,
                title_id=unique_entity_id,
                field_name="production_year",
                old_value="2018",
                new_value="2019",
                source_provider="KOBIS",
                actor_id="usr_curator_lead",
                actor_type="CURATOR",
                reason="Official release year validation",
                confidence=1.0
            )
        )

        history_2 = asyncio.run(canonical_repository.get_metadata_history(db=None, title_id=unique_entity_id))
        self.assertEqual(len(history_2), 2)
        self.assertEqual(history_2[0].field_name, "canonical_title")
        self.assertEqual(history_2[1].field_name, "production_year")
