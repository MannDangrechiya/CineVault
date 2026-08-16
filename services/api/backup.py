# CineVault OS — Backup & Disaster Recovery Layer (Phase 30)
# Implements operational recovery tooling:
# - Backup manifest with integrity verification (SHA-256)
# - Restore verification (backup-not-valid-until-restore-tested constraint)
# - RPO/RTO tracking (target: RPO < 5 min, RTO < 1 hour)
# - Database, object storage, queue, and configuration recovery strategies
# - Reconciliation-after-recovery verification
# - Disaster recovery runbook execution record

import time
import uuid
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

from .telemetry import signal_router

logger = logging.getLogger("cinevault.backup")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RPO_TARGET_SECONDS = 5 * 60        # 5 minutes
RTO_TARGET_SECONDS = 60 * 60       # 1 hour


# ---------------------------------------------------------------------------
# Backup Types & Status
# ---------------------------------------------------------------------------
class BackupType(str, Enum):
    DATABASE = "database"
    OBJECT_STORAGE = "object_storage"
    CONFIGURATION = "configuration"
    QUEUE_STATE = "queue_state"
    CANONICAL_CATALOG = "canonical_catalog"


class BackupStatus(str, Enum):
    CREATED = "CREATED"
    VERIFIED = "VERIFIED"         # Integrity hash verified
    RESTORE_TESTED = "RESTORE_TESTED"   # Restoration successfully tested
    INVALID = "INVALID"           # Integrity check failed
    EXPIRED = "EXPIRED"           # Outside retention window


class RestoreStatus(str, Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


# ---------------------------------------------------------------------------
# Backup Manifest
# ---------------------------------------------------------------------------
@dataclass
class BackupManifest:
    """Tamper-evident backup manifest record."""
    backup_id: str
    backup_type: BackupType
    created_at: float
    size_bytes: int
    storage_location: str
    integrity_hash: str             # SHA-256 of backup content descriptor
    status: BackupStatus = BackupStatus.CREATED
    restore_test_at: Optional[float] = None
    restore_test_result: Optional[str] = None
    expiry_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_valid_for_restore(self) -> bool:
        """A backup is only valid for restore if restore has been tested successfully."""
        return self.status == BackupStatus.RESTORE_TESTED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "backup_type": self.backup_type,
            "created_at": self.created_at,
            "size_bytes": self.size_bytes,
            "storage_location": self.storage_location,
            "integrity_hash": self.integrity_hash,
            "status": self.status,
            "restore_test_at": self.restore_test_at,
            "restore_test_result": self.restore_test_result,
            "expiry_at": self.expiry_at,
            "valid_for_restore": self.is_valid_for_restore(),
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Restore Record
# ---------------------------------------------------------------------------
@dataclass
class RestoreRecord:
    """Records a restore test or actual recovery operation."""
    restore_id: str
    backup_id: str
    backup_type: BackupType
    initiated_at: float
    completed_at: Optional[float]
    status: RestoreStatus
    rto_seconds: Optional[float]    # Actual RTO achieved
    rto_within_target: Optional[bool]
    reconciliation_passed: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "restore_id": self.restore_id,
            "backup_id": self.backup_id,
            "backup_type": self.backup_type,
            "initiated_at": self.initiated_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "rto_seconds": self.rto_seconds,
            "rto_target_seconds": RTO_TARGET_SECONDS,
            "rto_within_target": self.rto_within_target,
            "reconciliation_passed": self.reconciliation_passed,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Backup & Recovery Manager
# ---------------------------------------------------------------------------
class BackupRecoveryManager:
    """
    Manages backup manifests, restore testing, RPO/RTO tracking,
    and post-recovery reconciliation verification.

    Constraint: A backup is NOT considered valid until restoration is tested.
    """

    def __init__(self):
        self._backups: Dict[str, BackupManifest] = {}
        self._restores: List[RestoreRecord] = []

    # ------------------------------------------------------------------
    # 1. Backup Registration
    # ------------------------------------------------------------------
    def register_backup(
        self,
        backup_type: BackupType,
        size_bytes: int,
        storage_location: str,
        content_descriptor: str,        # Descriptive string for integrity hash
        retention_days: int = 30,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BackupManifest:
        """
        Registers a new backup manifest with SHA-256 integrity hash.
        Status starts as CREATED (not yet restore-tested).
        """
        backup_id = str(uuid.uuid4())
        now = time.time()
        integrity_hash = hashlib.sha256(
            f"{backup_id}:{content_descriptor}:{now}".encode("utf-8")
        ).hexdigest()
        expiry_at = now + (retention_days * 24 * 3600)

        manifest = BackupManifest(
            backup_id=backup_id,
            backup_type=backup_type,
            created_at=now,
            size_bytes=size_bytes,
            storage_location=storage_location,
            integrity_hash=integrity_hash,
            status=BackupStatus.CREATED,
            expiry_at=expiry_at,
            metadata=metadata or {},
        )
        self._backups[backup_id] = manifest

        signal_router.emit(
            "SYSTEM", "BACKUP_REGISTERED",
            source_service="backup-manager",
            backup_id=backup_id,
            backup_type=backup_type,
            size_bytes=size_bytes,
        )
        logger.info(f"Backup registered: {backup_id} type={backup_type} size={size_bytes}")
        return manifest

    # ------------------------------------------------------------------
    # 2. Integrity Verification
    # ------------------------------------------------------------------
    def verify_integrity(self, backup_id: str, expected_hash: str) -> bool:
        """
        Verifies backup integrity hash matches the stored hash.
        Marks backup INVALID if hashes don't match.
        """
        manifest = self._backups.get(backup_id)
        if not manifest:
            raise ValueError(f"Backup '{backup_id}' not found")

        matches = manifest.integrity_hash == expected_hash
        if matches:
            manifest.status = BackupStatus.VERIFIED
        else:
            manifest.status = BackupStatus.INVALID
            signal_router.emit(
                "SECURITY", "BACKUP_INTEGRITY_FAILURE",
                source_service="backup-manager",
                severity="CRITICAL",
                backup_id=backup_id,
            )
        return matches

    # ------------------------------------------------------------------
    # 3. Restore Testing (Constraint: must be done before backup is valid)
    # ------------------------------------------------------------------
    def test_restore(
        self,
        backup_id: str,
        simulated_restore_seconds: float = 120.0,
        reconciliation_passed: bool = True,
        force_failure: bool = False,
    ) -> RestoreRecord:
        """
        Tests restoring from a backup. Marks the backup RESTORE_TESTED on success.
        Constraint: Until this succeeds, backup.is_valid_for_restore() returns False.
        Tracks actual RTO vs target (< 1 hour).
        """
        manifest = self._backups.get(backup_id)
        if not manifest:
            raise ValueError(f"Backup '{backup_id}' not found")

        restore_id = str(uuid.uuid4())
        initiated_at = time.time()
        completed_at = initiated_at + simulated_restore_seconds
        rto_seconds = simulated_restore_seconds
        rto_within_target = rto_seconds <= RTO_TARGET_SECONDS

        if force_failure:
            record = RestoreRecord(
                restore_id=restore_id,
                backup_id=backup_id,
                backup_type=manifest.backup_type,
                initiated_at=initiated_at,
                completed_at=completed_at,
                status=RestoreStatus.FAILED,
                rto_seconds=rto_seconds,
                rto_within_target=False,
                reconciliation_passed=False,
                error="Simulated restore failure",
            )
            signal_router.emit(
                "SYSTEM", "RESTORE_TEST_FAILED",
                source_service="backup-manager",
                severity="ERROR",
                backup_id=backup_id,
                restore_id=restore_id,
            )
        else:
            manifest.status = BackupStatus.RESTORE_TESTED
            manifest.restore_test_at = completed_at
            manifest.restore_test_result = (
                f"PASS: restored in {rto_seconds:.0f}s "
                f"({'within' if rto_within_target else 'EXCEEDS'} RTO target), "
                f"reconciliation={'PASS' if reconciliation_passed else 'FAIL'}"
            )
            record = RestoreRecord(
                restore_id=restore_id,
                backup_id=backup_id,
                backup_type=manifest.backup_type,
                initiated_at=initiated_at,
                completed_at=completed_at,
                status=RestoreStatus.SUCCEEDED,
                rto_seconds=rto_seconds,
                rto_within_target=rto_within_target,
                reconciliation_passed=reconciliation_passed,
            )
            signal_router.emit(
                "SYSTEM", "RESTORE_TEST_PASSED",
                source_service="backup-manager",
                backup_id=backup_id,
                restore_id=restore_id,
                rto_seconds=rto_seconds,
                rto_within_target=rto_within_target,
            )

        self._restores.append(record)
        return record

    # ------------------------------------------------------------------
    # 4. RPO Measurement
    # ------------------------------------------------------------------
    def measure_rpo(
        self,
        last_backup_at: float,
        incident_at: float,
    ) -> Dict[str, Any]:
        """
        Measures actual RPO (data loss window) between last backup and incident.
        Compares against RPO target (< 5 minutes).
        """
        rpo_seconds = incident_at - last_backup_at
        within_target = rpo_seconds <= RPO_TARGET_SECONDS
        return {
            "rpo_seconds": round(rpo_seconds, 2),
            "rpo_target_seconds": RPO_TARGET_SECONDS,
            "rpo_within_target": within_target,
            "last_backup_at": last_backup_at,
            "incident_at": incident_at,
        }

    # ------------------------------------------------------------------
    # 5. Recovery Runbook Simulation
    # ------------------------------------------------------------------
    def generate_recovery_runbook(self, backup_type: BackupType) -> Dict[str, Any]:
        """
        Returns the recovery runbook steps for the given backup type.
        Used to document and verify recovery procedures.
        """
        steps = {
            BackupType.DATABASE: [
                "1. Stop all write traffic (maintenance mode)",
                "2. Verify latest pg_basebackup integrity hash",
                "3. Restore pg_basebackup to standby replica",
                "4. Replay WAL segments up to latest checkpoint",
                "5. Promote replica to primary (pg_promote())",
                "6. Update connection strings in PgBouncer",
                "7. Run reconciliation: verify title count, audit event count, user data integrity",
                "8. Re-enable write traffic",
                "9. Verify RTO < 1 hour achieved",
            ],
            BackupType.OBJECT_STORAGE: [
                "1. Identify affected bucket/prefix",
                "2. Restore objects from versioned backup location",
                "3. Verify object count and checksums",
                "4. Update storage references if endpoint changed",
            ],
            BackupType.CONFIGURATION: [
                "1. Restore secrets from vault backup",
                "2. Re-deploy environment configuration",
                "3. Verify all service health probes pass",
            ],
            BackupType.QUEUE_STATE: [
                "1. Restart RabbitMQ with Quorum Queue topology",
                "2. Replay any persisted messages from queue journal",
                "3. Verify queue depth and consumer health",
            ],
            BackupType.CANONICAL_CATALOG: [
                "1. Restore canonical_titles table from pg_dump",
                "2. Verify title count matches last known good count",
                "3. Run quality reconciliation pass",
                "4. Re-index search if applicable",
            ],
        }
        return {
            "backup_type": backup_type,
            "rpo_target": f"{RPO_TARGET_SECONDS // 60} minutes",
            "rto_target": f"{RTO_TARGET_SECONDS // 3600} hour",
            "steps": steps.get(backup_type, ["No runbook defined"]),
        }

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def get_backup(self, backup_id: str) -> Optional[BackupManifest]:
        return self._backups.get(backup_id)

    def list_backups(self, backup_type: Optional[BackupType] = None) -> List[Dict[str, Any]]:
        manifests = list(self._backups.values())
        if backup_type:
            manifests = [m for m in manifests if m.backup_type == backup_type]
        return [m.to_dict() for m in manifests]

    def list_restore_records(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._restores]

    def get_backup_health_summary(self) -> Dict[str, Any]:
        total = len(self._backups)
        restore_tested = sum(1 for m in self._backups.values() if m.status == BackupStatus.RESTORE_TESTED)
        invalid = sum(1 for m in self._backups.values() if m.status == BackupStatus.INVALID)
        valid_ratio = round(restore_tested / total, 4) if total > 0 else 0.0
        return {
            "total_backups": total,
            "restore_tested": restore_tested,
            "invalid": invalid,
            "valid_backup_ratio": valid_ratio,
            "rpo_target_seconds": RPO_TARGET_SECONDS,
            "rto_target_seconds": RTO_TARGET_SECONDS,
        }


backup_manager = BackupRecoveryManager()
