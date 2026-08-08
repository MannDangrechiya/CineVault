# CineVault OS — Protected Security Audit Logger Module
# Implements DEC-SEC-PRP-08 & DEC-SEC-PRP-11: Protected audit events with SHA-256 integrity hashes

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger("cinevault.audit")

class AuditLogger:
    """Centralized protected audit logger emitting tamper-evident security audit events."""

    @staticmethod
    def _compute_integrity_hash(event_id: str, timestamp: str, event_type: str, actor_id: str, target_id: str, details_json: str) -> str:
        """Calculates SHA-256 checksum over canonical audit event attributes for tamper detection."""
        raw_payload = f"{event_id}|{timestamp}|{event_type}|{actor_id}|{target_id}|{details_json}"
        return hashlib.sha256(raw_payload.encode('utf-8')).hexdigest()

    @classmethod
    def log_event(
        cls,
        event_type: str,
        actor_id: str,
        target_id: str = "N/A",
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Emits a structured audit event with SHA-256 integrity hash.
        Supported event types:
        - AUDIT_AUTH_FAILURE
        - AUDIT_PRIVILEGED_ACCESS
        - AUDIT_CANONICAL_PROMOTION
        - AUDIT_ENTITY_MERGE
        - AUDIT_ENTITY_SPLIT
        - AUDIT_PROVIDER_CONFIG_CHANGE
        - AUDIT_AI_PROPOSAL_DECISION
        - AUDIT_SECURITY_POLICY_CHANGE
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        details_dict = details or {}
        details_json = json.dumps(details_dict, sort_keys=True)

        integrity_hash = cls._compute_integrity_hash(
            event_id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            actor_id=actor_id,
            target_id=target_id,
            details_json=details_json
        )

        audit_record = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "actor_id": actor_id,
            "target_id": target_id,
            "details": details_dict,
            "correlation_id": correlation_id or "018f2e4a-7b31-7000-8000-000000000000",
            "integrity_hash": integrity_hash,
            "service": "cinevault-audit-engine"
        }

        # Log formatted audit payload
        logger.info(f"AUDIT_RECORD: {json.dumps(audit_record)}")
        return audit_record

audit_logger = AuditLogger()
