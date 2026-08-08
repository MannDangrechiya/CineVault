# CineVault OS — Control Room / Curation Foundation Schemas (Build Unit 8.10)
# Privileged curator administration, quarantine inspection, evidence breakdown, and audit history schemas

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ControlRoomSummaryStats(BaseModel):
    pending_reconciliation_candidates: int = Field(..., description="Count of pending identity resolution candidates")
    pending_ai_proposals: int = Field(..., description="Count of pending CAT-6 AI metadata proposals")
    pending_quarantine_records: int = Field(..., description="Count of unresolved ingestion quarantine records")
    promoted_canonical_records: int = Field(..., description="Count of promoted canonical platform data records")

class QuarantineRecordResponse(BaseModel):
    quarantine_id: str = Field(..., description="Quarantine record UUID")
    raw_payload_id: Optional[str] = Field(None, description="Associated raw provider payload UUID")
    provider_name: str = Field(..., description="Originating ingestion provider name")
    failure_category: str = Field(..., description="Ingestion failure classification")
    diagnostic_details: Dict[str, Any] = Field(..., description="Diagnostic failure payload")
    review_status: str = Field(..., description="PENDING, RESOLVED, or DISCARDED")
    detected_at: datetime = Field(..., description="Quarantine detection timestamp")

class QuarantineResolveRequest(BaseModel):
    decision: str = Field(..., description="RESOLVE, REPROCESS, or DISCARD")
    rationale: str = Field(..., min_length=3, description="Curator decision rationale for audit logging")

class CandidateDetailResponse(BaseModel):
    candidate_id: str = Field(..., description="Reconciliation candidate UUID")
    provider_name: str = Field(..., description="Provider name")
    external_id: str = Field(..., description="External provider identifier")
    candidate_title_id: Optional[str] = Field(None, description="Suggested matching canonical title UUID")
    match_confidence: float = Field(..., description="Match confidence score (0.000 - 1.000)")
    match_rule_id: str = Field(..., description="Matching rule identifier executed")
    decision_status: str = Field(..., description="PENDING, PROMOTED, or REJECTED")
    evidence_summary: Dict[str, Any] = Field(default_factory=dict, description="Structured provenance and evidence payload")
    created_at: datetime = Field(..., description="Candidate creation timestamp")

class ControlRoomAuditLogResponse(BaseModel):
    event_id: str = Field(..., description="Audit record UUID")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
    event_type: str = Field(..., description="System audit event type")
    actor_id: str = Field(..., description="Actor identity performing action")
    target_id: Optional[str] = Field(None, description="Target entity ID")
    details: Dict[str, Any] = Field(..., description="Event details and rationale")
    integrity_hash: str = Field(..., description="SHA-256 HMAC cryptographic integrity hash")
