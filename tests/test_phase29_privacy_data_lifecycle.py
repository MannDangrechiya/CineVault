# CineVault OS — Phase 29 Privacy / Data Lifecycle Tests
# Verifies data subject rights: erasure, portability, retention, minimization,
# audit record scrubbing, and tamper-evident deletion records.

import time
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.privacy import (
    PrivacyEngine,
    DataCategory,
    CAT2_PERSONAL_FIELDS,
    MINIMIZED_FIELDS_ON_EXPORT,
    RETENTION_POLICY,
    privacy_engine,
)

client = TestClient(app)


class TestPhase29PrivacyDataLifecycle:
    """Phase 29 — Privacy / Data Lifecycle: erasure, portability, retention, minimization, audit scrubbing."""

    def fresh_engine(self) -> PrivacyEngine:
        return PrivacyEngine()

    # ------------------------------------------------------------------
    # 1. Right to Erasure
    # ------------------------------------------------------------------
    def test_delete_personal_data_clears_cat2_fields(self):
        """Deletion sets all CAT-2 personal fields to None in the snapshot."""
        engine = self.fresh_engine()
        snapshot = {
            "email": "alice@example.com",
            "display_name": "Alice",
            "watch_event_notes": "private notes",
            "preferred_username": "alice_cv",
            "title_count": 42,  # CAT-1 field — should NOT be cleared
        }
        record = engine.delete_user_personal_data("user-001", personal_data_snapshot=snapshot)

        assert snapshot["email"] is None
        assert snapshot["display_name"] is None
        assert snapshot["watch_event_notes"] is None
        assert snapshot["preferred_username"] is None
        assert snapshot["title_count"] == 42  # CAT-1 untouched

    def test_deletion_produces_tamper_evident_record(self):
        """Deletion record has status COMPLETED and non-empty integrity hash."""
        engine = self.fresh_engine()
        record = engine.delete_user_personal_data("user-002")
        assert record.status == "COMPLETED"
        assert len(record.integrity_hash) == 64  # SHA-256 hex

    def test_deletion_record_uses_anonymized_user_id(self):
        """DeletionRecord stores user_id_hash, not raw user_id."""
        engine = self.fresh_engine()
        record = engine.delete_user_personal_data("user-003")
        assert record.user_id_hash != "user-003"
        assert len(record.user_id_hash) == 64  # SHA-256

    def test_deletion_scrubs_audit_events_in_snapshot(self):
        """Audit events in snapshot are scrubbed on deletion."""
        engine = self.fresh_engine()
        snapshot = {
            "email": "bob@example.com",
            "audit_events": [
                {"event": "LOGIN", "email": "bob@example.com", "timestamp": 1000},
                {"event": "WATCHLIST_ADD", "email": "bob@example.com", "title_id": "tt001"},
            ]
        }
        record = engine.delete_user_personal_data("user-004", personal_data_snapshot=snapshot)
        assert snapshot["audit_events"][0]["email"] == "[SCRUBBED]"
        assert snapshot["audit_events"][1]["email"] == "[SCRUBBED]"
        assert record.audit_records_scrubbed == 2

    def test_deletion_log_is_queryable(self):
        """Deletion events are recorded in the deletion log."""
        engine = self.fresh_engine()
        record = engine.delete_user_personal_data("user-005")
        log = engine.get_deletion_log()
        assert any(r["deletion_id"] == record.deletion_id for r in log)

    def test_deletion_reason_recorded(self):
        """Deletion reason is preserved in the record."""
        engine = self.fresh_engine()
        record = engine.delete_user_personal_data("user-006", reason="retention_policy")
        assert record.reason == "retention_policy"

    # ------------------------------------------------------------------
    # 2. Right to Portability
    # ------------------------------------------------------------------
    def test_export_returns_personal_data(self):
        """Export contains user's personal data."""
        engine = self.fresh_engine()
        snapshot = {
            "email": "carol@example.com",
            "display_name": "Carol",
            "watchlist": ["tt001", "tt002"],
            "ip_address": "192.168.1.100",
        }
        export = engine.export_personal_data("user-010", snapshot)
        assert export.records["email"] == "carol@example.com"
        assert export.records["display_name"] == "Carol"

    def test_export_suppresses_minimized_fields(self):
        """Sensitive fields are suppressed (None) in exported data."""
        engine = self.fresh_engine()
        snapshot = {
            "email": "dave@example.com",
            "ip_address": "10.0.0.1",
            "device_id": "device-xyz",
            "auth_token": "tok-secret",
        }
        export = engine.export_personal_data("user-011", snapshot)
        assert export.records.get("ip_address") is None
        assert export.records.get("device_id") is None
        assert export.records.get("auth_token") is None
        assert "ip_address" in export.minimized_fields

    def test_export_preserves_non_sensitive_fields(self):
        """Non-sensitive personal fields are preserved in the export."""
        engine = self.fresh_engine()
        snapshot = {"email": "eve@example.com", "watchlist": ["tt001"]}
        export = engine.export_personal_data("user-012", snapshot)
        assert export.records["watchlist"] == ["tt001"]

    def test_export_data_category_is_cat2(self):
        """Export data_categories correctly indicates CAT-2."""
        engine = self.fresh_engine()
        export = engine.export_personal_data("user-013", {"email": "f@f.com"})
        assert DataCategory.CAT2 in export.data_categories

    def test_export_user_id_anonymized(self):
        """Export stores user_id_hash, not raw user_id."""
        engine = self.fresh_engine()
        export = engine.export_personal_data("user-014", {})
        assert export.user_id_hash != "user-014"

    # ------------------------------------------------------------------
    # 3. Retention Policy Evaluation
    # ------------------------------------------------------------------
    def test_retention_not_expired_recent_record(self):
        """A very recently created record is not expired."""
        engine = self.fresh_engine()
        result = engine.evaluate_retention(
            "watch_history",
            record_created_at=time.time() - 100,
        )
        assert result["expired"] is False

    def test_retention_expired_old_record(self):
        """A record older than its retention period is expired."""
        engine = self.fresh_engine()
        # Export jobs expire after 7 days (604800 seconds)
        old_ts = time.time() - (8 * 24 * 3600)
        result = engine.evaluate_retention("export_jobs", record_created_at=old_ts)
        assert result["expired"] is True

    def test_retention_unknown_data_type_never_expires(self):
        """Unknown data types have no retention limit (not expired)."""
        engine = self.fresh_engine()
        result = engine.evaluate_retention("custom_type", record_created_at=0)
        assert result["expired"] is False
        assert result["retention_seconds"] is None

    def test_retention_policy_keys_defined(self):
        """All expected data types have retention policies defined."""
        for data_type in ["watch_history", "user_sessions", "recommendation_logs", "export_jobs", "audit_events"]:
            assert data_type in RETENTION_POLICY

    # ------------------------------------------------------------------
    # 4. Data Minimization
    # ------------------------------------------------------------------
    def test_minimize_for_storage_suppresses_tokens(self):
        """minimize_for_storage removes auth tokens and device IDs."""
        engine = self.fresh_engine()
        data = {"display_name": "Alice", "auth_token": "tok-secret", "device_id": "d-123"}
        minimized = engine.minimize_for_storage(data)
        assert minimized["auth_token"] is None
        assert minimized["device_id"] is None
        assert minimized["display_name"] == "Alice"  # preserved

    def test_minimize_does_not_mutate_original(self):
        """minimize_for_storage returns a copy, not mutating the original."""
        engine = self.fresh_engine()
        original = {"auth_token": "secret"}
        minimized = engine.minimize_for_storage(original)
        assert original["auth_token"] == "secret"  # original unchanged
        assert minimized["auth_token"] is None

    # ------------------------------------------------------------------
    # 5. Audit Record Scrubbing
    # ------------------------------------------------------------------
    def test_scrub_audit_record_removes_personal_fields(self):
        """scrub_audit_record replaces CAT-2 fields with [SCRUBBED_ON_DELETION]."""
        engine = self.fresh_engine()
        audit_event = {
            "event_type": "METADATA_CHANGE",
            "timestamp": 1000.0,
            "email": "secret@domain.com",
            "display_name": "Private Name",
            "actor_type": "CURATOR",
        }
        scrubbed = engine.scrub_audit_record(audit_event)
        assert scrubbed["email"] == "[SCRUBBED_ON_DELETION]"
        assert scrubbed["display_name"] == "[SCRUBBED_ON_DELETION]"
        assert scrubbed["event_type"] == "METADATA_CHANGE"   # preserved
        assert scrubbed["actor_type"] == "CURATOR"            # preserved

    def test_scrub_audit_record_anonymizes_user_id(self):
        """user_id is replaced with user_id_hash (anonymized), not deleted."""
        engine = self.fresh_engine()
        audit_event = {"event_type": "LOGIN", "user_id": "user-abc", "timestamp": 999.0}
        scrubbed = engine.scrub_audit_record(audit_event)
        assert "user_id" not in scrubbed or scrubbed.get("user_id") is None
        assert "user_id_hash" in scrubbed
        assert len(scrubbed["user_id_hash"]) == 64

    def test_scrub_audit_record_marks_scrubbed_flag(self):
        """Scrubbed audit records carry _scrubbed=True marker."""
        engine = self.fresh_engine()
        scrubbed = engine.scrub_audit_record({"event_type": "x"})
        assert scrubbed["_scrubbed"] is True
        assert "_scrubbed_at" in scrubbed

    def test_scrub_preserves_non_personal_fields(self):
        """Non-personal fields like event_type and title_id are preserved."""
        engine = self.fresh_engine()
        audit_event = {
            "event_type": "WATCHLIST_ADD",
            "title_id": "tt001",
            "email": "secret@x.com",
        }
        scrubbed = engine.scrub_audit_record(audit_event)
        assert scrubbed["title_id"] == "tt001"
        assert scrubbed["event_type"] == "WATCHLIST_ADD"

    # ------------------------------------------------------------------
    # 6. Deletion Record Retrieval
    # ------------------------------------------------------------------
    def test_get_deletion_record_by_id(self):
        """get_deletion_record returns the correct record by deletion_id."""
        engine = self.fresh_engine()
        record = engine.delete_user_personal_data("user-020")
        found = engine.get_deletion_record(record.deletion_id)
        assert found is not None
        assert found.deletion_id == record.deletion_id

    def test_get_deletion_record_not_found_returns_none(self):
        """get_deletion_record returns None for unknown deletion_id."""
        engine = self.fresh_engine()
        assert engine.get_deletion_record("non-existent-id") is None

    # ------------------------------------------------------------------
    # 7. CAT-2 Field Inventory
    # ------------------------------------------------------------------
    def test_cat2_fields_include_core_personal_data(self):
        """CAT-2 personal field set contains all core personal data identifiers."""
        required = {"email", "display_name", "watch_event_notes", "ip_address", "auth_token"}
        assert required.issubset(CAT2_PERSONAL_FIELDS)

    def test_minimized_fields_subset_of_cat2(self):
        """All minimized-on-export fields are a subset of CAT-2 personal fields."""
        assert MINIMIZED_FIELDS_ON_EXPORT.issubset(CAT2_PERSONAL_FIELDS)
