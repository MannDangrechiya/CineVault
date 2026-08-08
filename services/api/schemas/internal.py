# CineVault OS — Internal Operational & Curation API Schemas
# Administrative endpoints for ingestion monitoring, reconciliation curation, and AI proposals

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class IngestionRunSummary(BaseModel):
    run_id: str
    provider_id: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    records_fetched: int
    records_quarantined: int

class RawPayloadDetail(BaseModel):
    raw_payload_id: str
    provider_id: str
    payload_hash: str
    payload_data: Dict[str, Any]
    captured_at: str

class ReconciliationCandidateSummary(BaseModel):
    candidate_id: str
    source_provider: str
    suggested_action: str  # MATCH_EXACT, MERGE_CANDIDATE, SPLIT_CANDIDATE, REQUIRES_REVIEW
    match_confidence: float
    status: str  # PENDING_REVIEW, PROMOTED, REJECTED

class PromotionDecisionRequest(BaseModel):
    rationale: str
    override_fields: Optional[Dict[str, Any]] = None

class AIProposalSummary(BaseModel):
    proposal_id: str
    target_title_id: str
    proposal_type: str
    confidence_score: float
    provenance_type: str = "AI_GENERATED"
    model_id: str
    suggested_attributes: Dict[str, Any]
