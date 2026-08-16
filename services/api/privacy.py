# CineVault OS — Privacy & Data Lifecycle Layer (Phase 29)
# Implements data subject rights (GDPR-aligned):
# - Right to Erasure (account & personal data deletion)
# - Right to Portability (personal data export)
# - Data Retention policies (auto-expiry of stale personal data)
# - Sensitive data minimization (field-level suppression)
# - Audit record scrubbing policy (remove sensitive content, preserve anonymized event facts)
#
# Constraint: When a user deletes personal data it must actually disappear.
# Audit events are scrubbed — sensitive fields removed, anonymized event
# summary retained for legal/security compliance.

import time
import uuid
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

from .telemetry import signal_router

logger = logging.getLogger("cinevault.privacy")

# ---------------------------------------------------------------------------
# Data Categories
# ---------------------------------------------------------------------------
class DataCategory(str, Enum):
    CAT1 = "CAT_1"    # Canonical catalog data — not personal
    CAT2 = "CAT_2"    # Personal user data — subject to deletion/export
    AUDIT = "AUDIT"   # Audit trail — scrubbed on deletion, anonymized fact retained


# CAT-2 personal data fields that must be deleted or minimized
CAT2_PERSONAL_FIELDS = {
    "email", "display_name", "preferred_username", "watch_event_notes",
    "user_address", "phone", "date_of_birth", "profile_image_url",
    "ip_address", "device_id", "auth_token", "refresh_token",
}

# Fields that must be suppressed (set to None) rather than deleted on export
MINIMIZED_FIELDS_ON_EXPORT = {"ip_address", "device_id", "auth_token", "refresh_token"}

# Retention periods (seconds)
RETENTION_POLICY: Dict[str, int] = {
    "watch_history": 3 * 365 * 24 * 3600,       # 3 years
    "user_sessions": 30 * 24 * 3600,             # 30 days
    "recommendation_logs": 90 * 24 * 3600,       # 90 days
    "export_jobs": 7 * 24 * 3600,                # 7 days
    "audit_events": 7 * 365 * 24 * 3600,         # 7 years (legal requirement)
}


# ---------------------------------------------------------------------------
# Deletion Record — Tamper-Evident Proof of Deletion
# ---------------------------------------------------------------------------
@dataclass
class DeletionRecord:
    """Immutable record proving user data was deleted."""
    deletion_id: str
    user_id_hash: str          # SHA-256 of user_id — anonymized reference
    requested_at: float
    completed_at: Optional[float]
    data_categories_deleted: List[str]
    records_deleted: int
    audit_records_scrubbed: int
    status: str                 # PENDING | COMPLETED | FAILED
    reason: str                 # "user_request" | "retention_policy" | "admin"
    integrity_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deletion_id": self.deletion_id,
            "user_id_hash": self.user_id_hash,
            "requested_at": self.requested_at,
            "completed_at": self.completed_at,
            "data_categories_deleted": self.data_categories_deleted,
            "records_deleted": self.records_deleted,
            "audit_records_scrubbed": self.audit_records_scrubbed,
            "status": self.status,
            "reason": self.reason,
            "integrity_hash": self.integrity_hash,
        }


# ---------------------------------------------------------------------------
# Personal Data Export Record
# ---------------------------------------------------------------------------
@dataclass
class PersonalDataExport:
    """Structured personal data export package (GDPR portability)."""
    export_id: str
    user_id_hash: str
    exported_at: float
    data_categories: List[str]
    records: Dict[str, Any]         # Minimized personal data fields
    minimized_fields: List[str]     # Fields suppressed during export


# ---------------------------------------------------------------------------
# Privacy Engine
# ---------------------------------------------------------------------------
class PrivacyEngine:
    """
    Implements data subject rights: erasure, portability, retention, minimization.
    All operations emit AUDIT signals and produce immutable deletion records.
    """

    def __init__(self):
        self._deletion_log: List[DeletionRecord] = []
        self._export_log: List[str] = []         # export_ids

    def _hash_user_id(self, user_id: str) -> str:
        return hashlib.sha256(user_id.encode("utf-8")).hexdigest()

    def _compute_integrity(self, user_id_hash: str, deletion_id: str, ts: float) -> str:
        payload = f"{user_id_hash}:{deletion_id}:{ts}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # 1. Right to Erasure — Account & Personal Data Deletion
    # ------------------------------------------------------------------
    def delete_user_personal_data(
        self,
        user_id: str,
        reason: str = "user_request",
        personal_data_snapshot: Optional[Dict[str, Any]] = None,
    ) -> DeletionRecord:
        """
        Deletes all CAT-2 personal data for a user.
        - Zeroes out all personal fields in the snapshot
        - Scrubs audit events (removes sensitive content, preserves anonymized fact)
        - Produces a tamper-evident DeletionRecord

        In production this would cascade to database tables via a delete mutation.
        Here we simulate the operation on the provided snapshot.
        """
        deletion_id = str(uuid.uuid4())
        requested_at = time.time()
        user_id_hash = self._hash_user_id(user_id)

        # Count records that would be deleted
        records_deleted = 0
        audit_records_scrubbed = 0

        if personal_data_snapshot:
            for field_name in CAT2_PERSONAL_FIELDS:
                if field_name in personal_data_snapshot:
                    personal_data_snapshot[field_name] = None
                    records_deleted += 1
            # Simulate audit scrubbing
            audit_events = personal_data_snapshot.get("audit_events", [])
            for event in audit_events:
                for field_name in CAT2_PERSONAL_FIELDS:
                    if field_name in event:
                        event[field_name] = "[SCRUBBED]"
                audit_records_scrubbed += 1

        integrity_hash = self._compute_integrity(user_id_hash, deletion_id, requested_at)

        record = DeletionRecord(
            deletion_id=deletion_id,
            user_id_hash=user_id_hash,
            requested_at=requested_at,
            completed_at=time.time(),
            data_categories_deleted=[DataCategory.CAT2],
            records_deleted=records_deleted,
            audit_records_scrubbed=audit_records_scrubbed,
            status="COMPLETED",
            reason=reason,
            integrity_hash=integrity_hash,
        )
        self._deletion_log.append(record)

        signal_router.emit(
            "AUDIT",
            "USER_DATA_DELETED",
            source_service="privacy-engine",
            severity="INFO",
            deletion_id=deletion_id,
            user_id_hash=user_id_hash,
            records_deleted=records_deleted,
            audit_records_scrubbed=audit_records_scrubbed,
            reason=reason,
        )
        logger.info(
            f"User data deleted: deletion_id={deletion_id} user_hash={user_id_hash[:8]}... "
            f"records={records_deleted} audit_scrubbed={audit_records_scrubbed}"
        )
        return record

    # ------------------------------------------------------------------
    # 2. Right to Portability — Personal Data Export
    # ------------------------------------------------------------------
    def export_personal_data(
        self,
        user_id: str,
        personal_data_snapshot: Dict[str, Any],
    ) -> PersonalDataExport:
        """
        Exports all CAT-2 personal data for a user in a portable format.
        Suppresses minimized fields (device IDs, tokens) before export.
        """
        export_id = str(uuid.uuid4())
        user_id_hash = self._hash_user_id(user_id)

        # Copy and minimize
        export_data = dict(personal_data_snapshot)
        suppressed = []
        for field_name in MINIMIZED_FIELDS_ON_EXPORT:
            if field_name in export_data:
                export_data[field_name] = None
                suppressed.append(field_name)

        export = PersonalDataExport(
            export_id=export_id,
            user_id_hash=user_id_hash,
            exported_at=time.time(),
            data_categories=[DataCategory.CAT2],
            records=export_data,
            minimized_fields=suppressed,
        )
        self._export_log.append(export_id)

        signal_router.emit(
            "AUDIT",
            "USER_DATA_EXPORTED",
            source_service="privacy-engine",
            severity="INFO",
            export_id=export_id,
            user_id_hash=user_id_hash,
            fields_exported=len(export_data),
            fields_suppressed=len(suppressed),
        )
        return export

    # ------------------------------------------------------------------
    # 3. Retention Policy Evaluation
    # ------------------------------------------------------------------
    def evaluate_retention(
        self,
        data_type: str,
        record_created_at: float,
        now: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates whether a record has exceeded its retention period.
        Returns {"expired": bool, "retention_seconds": int, "age_seconds": float}.
        """
        now = now or time.time()
        retention_seconds = RETENTION_POLICY.get(data_type)
        if retention_seconds is None:
            return {"expired": False, "retention_seconds": None, "age_seconds": now - record_created_at}

        age_seconds = now - record_created_at
        expired = age_seconds > retention_seconds
        return {
            "expired": expired,
            "retention_seconds": retention_seconds,
            "age_seconds": round(age_seconds, 2),
            "data_type": data_type,
        }

    # ------------------------------------------------------------------
    # 4. Sensitive Data Minimization
    # ------------------------------------------------------------------
    def minimize_for_storage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a copy of data with sensitive/high-risk fields suppressed.
        Used before storing personal data in logs, analytics exports, or caches.
        """
        minimized = dict(data)
        for field_name in MINIMIZED_FIELDS_ON_EXPORT:
            if field_name in minimized:
                minimized[field_name] = None
        return minimized

    # ------------------------------------------------------------------
    # 5. Audit Record Scrubbing Policy
    # ------------------------------------------------------------------
    def scrub_audit_record(self, audit_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Removes sensitive personal data from an audit event while retaining
        the anonymized fact (event type, timestamp, anonymized actor ID).
        Constraint: Audit records must NOT retain deleted sensitive content.
        """
        scrubbed = {}
        for key, value in audit_event.items():
            if key in CAT2_PERSONAL_FIELDS:
                scrubbed[key] = "[SCRUBBED_ON_DELETION]"
            elif key == "user_id":
                # Replace with anonymized hash instead of deleting
                scrubbed["user_id_hash"] = self._hash_user_id(str(value))
            else:
                scrubbed[key] = value
        scrubbed["_scrubbed"] = True
        scrubbed["_scrubbed_at"] = time.time()
        return scrubbed

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def get_deletion_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._deletion_log[-limit:]]

    def get_deletion_record(self, deletion_id: str) -> Optional[DeletionRecord]:
        for r in self._deletion_log:
            if r.deletion_id == deletion_id:
                return r
        return None


privacy_engine = PrivacyEngine()
