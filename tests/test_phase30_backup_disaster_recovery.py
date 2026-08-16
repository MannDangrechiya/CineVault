# CineVault OS — Phase 30 Backup / Disaster Recovery Tests
# Verifies backup manifest registration, integrity verification,
# restore testing (constraint: backup not valid until tested),
# RPO/RTO tracking, recovery runbooks, and health summary.

import time
import pytest

from services.api.backup import (
    BackupRecoveryManager,
    BackupType,
    BackupStatus,
    RestoreStatus,
    RPO_TARGET_SECONDS,
    RTO_TARGET_SECONDS,
    backup_manager,
)


class TestPhase30BackupDisasterRecovery:
    """Phase 30 — Backup / Disaster Recovery: manifests, integrity, restore testing, RPO/RTO."""

    def fresh_mgr(self) -> BackupRecoveryManager:
        return BackupRecoveryManager()

    # ------------------------------------------------------------------
    # 1. Backup Registration
    # ------------------------------------------------------------------
    def test_register_backup_creates_manifest(self):
        """register_backup creates a BackupManifest with CREATED status."""
        mgr = self.fresh_mgr()
        manifest = mgr.register_backup(
            backup_type=BackupType.DATABASE,
            size_bytes=512 * 1024 * 1024,
            storage_location="s3://cinevault-backups/db/2026-08-16/",
            content_descriptor="pg_basebackup_2026-08-16T00:00:00Z",
        )
        assert manifest.status == BackupStatus.CREATED
        assert manifest.backup_type == BackupType.DATABASE
        assert manifest.backup_id is not None

    def test_register_all_backup_types(self):
        """All 5 backup types can be registered."""
        mgr = self.fresh_mgr()
        for bt in BackupType:
            m = mgr.register_backup(bt, 1000, "s3://test/", f"desc-{bt}")
            assert m.backup_type == bt

    def test_backup_has_sha256_integrity_hash(self):
        """Backup manifest has a 64-char SHA-256 integrity hash."""
        mgr = self.fresh_mgr()
        m = mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/", "desc")
        assert len(m.integrity_hash) == 64

    def test_backup_not_valid_for_restore_before_testing(self):
        """Constraint: backup is NOT valid for restore until restore is tested."""
        mgr = self.fresh_mgr()
        m = mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/", "desc")
        assert m.is_valid_for_restore() is False

    def test_backup_has_expiry(self):
        """Registered backup has an expiry_at timestamp set."""
        mgr = self.fresh_mgr()
        m = mgr.register_backup(BackupType.CONFIGURATION, 100, "s3://test/", "cfg", retention_days=7)
        assert m.expiry_at is not None
        assert m.expiry_at > time.time()

    # ------------------------------------------------------------------
    # 2. Integrity Verification
    # ------------------------------------------------------------------
    def test_integrity_verification_passes_with_correct_hash(self):
        """Integrity check passes when expected_hash matches stored hash."""
        mgr = self.fresh_mgr()
        m = mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/", "desc")
        result = mgr.verify_integrity(m.backup_id, m.integrity_hash)
        assert result is True
        assert mgr.get_backup(m.backup_id).status == BackupStatus.VERIFIED

    def test_integrity_verification_fails_with_wrong_hash(self):
        """Integrity check fails and marks backup INVALID on hash mismatch."""
        mgr = self.fresh_mgr()
        m = mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/", "desc")
        result = mgr.verify_integrity(m.backup_id, "deadbeef" * 8)  # wrong hash
        assert result is False
        assert mgr.get_backup(m.backup_id).status == BackupStatus.INVALID

    def test_integrity_raises_for_unknown_backup(self):
        """verify_integrity raises ValueError for unknown backup_id."""
        mgr = self.fresh_mgr()
        with pytest.raises(ValueError, match="not found"):
            mgr.verify_integrity("non-existent-id", "hash")

    # ------------------------------------------------------------------
    # 3. Restore Testing (Core Constraint)
    # ------------------------------------------------------------------
    def test_restore_test_marks_backup_valid(self):
        """After successful restore test, backup.is_valid_for_restore() returns True."""
        mgr = self.fresh_mgr()
        m = mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/", "desc")
        assert m.is_valid_for_restore() is False  # not yet tested

        record = mgr.test_restore(m.backup_id, simulated_restore_seconds=60.0)
        assert record.status == RestoreStatus.SUCCEEDED
        assert m.is_valid_for_restore() is True  # now valid

    def test_restore_test_records_rto(self):
        """Restore test records actual RTO seconds."""
        mgr = self.fresh_mgr()
        m = mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/", "desc")
        record = mgr.test_restore(m.backup_id, simulated_restore_seconds=300.0)
        assert record.rto_seconds == 300.0

    def test_restore_within_rto_target(self):
        """Restore under 1 hour reports rto_within_target=True."""
        mgr = self.fresh_mgr()
        m = mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/", "desc")
        record = mgr.test_restore(m.backup_id, simulated_restore_seconds=1800.0)  # 30 min
        assert record.rto_within_target is True

    def test_restore_exceeds_rto_target(self):
        """Restore over 1 hour reports rto_within_target=False."""
        mgr = self.fresh_mgr()
        m = mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/", "desc")
        record = mgr.test_restore(m.backup_id, simulated_restore_seconds=7200.0)  # 2 hours
        assert record.rto_within_target is False

    def test_restore_failure_keeps_backup_not_valid(self):
        """Failed restore test does NOT mark backup as valid."""
        mgr = self.fresh_mgr()
        m = mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/", "desc")
        record = mgr.test_restore(m.backup_id, force_failure=True)
        assert record.status == RestoreStatus.FAILED
        assert m.is_valid_for_restore() is False

    def test_restore_test_raises_for_unknown_backup(self):
        """test_restore raises ValueError for unknown backup_id."""
        mgr = self.fresh_mgr()
        with pytest.raises(ValueError, match="not found"):
            mgr.test_restore("non-existent-backup")

    def test_restore_reconciliation_result_recorded(self):
        """Restore test captures reconciliation_passed flag."""
        mgr = self.fresh_mgr()
        m = mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/", "desc")
        record = mgr.test_restore(m.backup_id, reconciliation_passed=True)
        assert record.reconciliation_passed is True

    # ------------------------------------------------------------------
    # 4. RPO Measurement
    # ------------------------------------------------------------------
    def test_rpo_within_target(self):
        """RPO within 5 minutes reports rpo_within_target=True."""
        mgr = self.fresh_mgr()
        now = time.time()
        result = mgr.measure_rpo(
            last_backup_at=now - 120,  # 2 minutes ago
            incident_at=now,
        )
        assert result["rpo_within_target"] is True
        assert result["rpo_seconds"] == pytest.approx(120.0, abs=0.5)

    def test_rpo_exceeds_target(self):
        """RPO over 5 minutes reports rpo_within_target=False."""
        mgr = self.fresh_mgr()
        now = time.time()
        result = mgr.measure_rpo(
            last_backup_at=now - 600,  # 10 minutes ago
            incident_at=now,
        )
        assert result["rpo_within_target"] is False

    def test_rpo_target_is_five_minutes(self):
        """RPO target is 300 seconds (5 minutes)."""
        assert RPO_TARGET_SECONDS == 300

    def test_rto_target_is_one_hour(self):
        """RTO target is 3600 seconds (1 hour)."""
        assert RTO_TARGET_SECONDS == 3600

    # ------------------------------------------------------------------
    # 5. Recovery Runbooks
    # ------------------------------------------------------------------
    def test_database_recovery_runbook_has_steps(self):
        """Database recovery runbook has at least 5 steps."""
        mgr = self.fresh_mgr()
        runbook = mgr.generate_recovery_runbook(BackupType.DATABASE)
        assert "steps" in runbook
        assert len(runbook["steps"]) >= 5

    def test_runbook_includes_reconciliation_step(self):
        """Database runbook explicitly includes reconciliation verification."""
        mgr = self.fresh_mgr()
        runbook = mgr.generate_recovery_runbook(BackupType.DATABASE)
        steps_text = " ".join(runbook["steps"]).lower()
        assert "reconciliation" in steps_text

    def test_runbook_all_backup_types(self):
        """Runbook can be generated for all backup types."""
        mgr = self.fresh_mgr()
        for bt in BackupType:
            runbook = mgr.generate_recovery_runbook(bt)
            assert "steps" in runbook
            assert len(runbook["steps"]) >= 1

    def test_runbook_includes_rpo_rto_targets(self):
        """Runbook documents RPO and RTO targets."""
        mgr = self.fresh_mgr()
        runbook = mgr.generate_recovery_runbook(BackupType.DATABASE)
        assert "rpo_target" in runbook
        assert "rto_target" in runbook

    # ------------------------------------------------------------------
    # 6. Health Summary
    # ------------------------------------------------------------------
    def test_health_summary_structure(self):
        """get_backup_health_summary returns expected keys."""
        mgr = self.fresh_mgr()
        mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/", "desc")
        summary = mgr.get_backup_health_summary()
        assert "total_backups" in summary
        assert "restore_tested" in summary
        assert "invalid" in summary
        assert "valid_backup_ratio" in summary
        assert "rpo_target_seconds" in summary
        assert "rto_target_seconds" in summary

    def test_health_summary_valid_ratio_after_restore_test(self):
        """valid_backup_ratio is 1.0 when all backups have been restore-tested."""
        mgr = self.fresh_mgr()
        m = mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/", "desc")
        mgr.test_restore(m.backup_id)
        summary = mgr.get_backup_health_summary()
        assert summary["valid_backup_ratio"] == 1.0

    def test_health_summary_zero_ratio_before_restore_test(self):
        """valid_backup_ratio is 0.0 when no backups have been restore-tested."""
        mgr = self.fresh_mgr()
        mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/", "desc")
        summary = mgr.get_backup_health_summary()
        assert summary["valid_backup_ratio"] == 0.0

    # ------------------------------------------------------------------
    # 7. List / Query
    # ------------------------------------------------------------------
    def test_list_backups_returns_all(self):
        """list_backups returns all registered backups."""
        mgr = self.fresh_mgr()
        mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/db", "desc-db")
        mgr.register_backup(BackupType.CONFIGURATION, 500, "s3://test/cfg", "desc-cfg")
        backups = mgr.list_backups()
        assert len(backups) == 2

    def test_list_backups_filtered_by_type(self):
        """list_backups with backup_type filter returns only matching type."""
        mgr = self.fresh_mgr()
        mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/db", "desc-db")
        mgr.register_backup(BackupType.OBJECT_STORAGE, 2000, "s3://test/obj", "desc-obj")
        db_only = mgr.list_backups(backup_type=BackupType.DATABASE)
        assert len(db_only) == 1
        assert db_only[0]["backup_type"] == BackupType.DATABASE

    def test_list_restore_records(self):
        """list_restore_records returns all restore test results."""
        mgr = self.fresh_mgr()
        m = mgr.register_backup(BackupType.DATABASE, 1000, "s3://test/", "desc")
        mgr.test_restore(m.backup_id)
        records = mgr.list_restore_records()
        assert len(records) == 1
        assert records[0]["backup_id"] == m.backup_id
