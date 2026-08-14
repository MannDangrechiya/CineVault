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

class IngestionItemPayload(BaseModel):
    external_entity_type: str = Field(default="MOVIE")
    external_entity_id: str
    raw_payload: Optional[Dict[str, Any]] = None

class IngestionTriggerRequest(BaseModel):
    provider_name: str
    items: List[IngestionItemPayload]
    dry_run: bool = False

class IngestionRunDetail(BaseModel):
    run_id: str
    provider_name: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    records_seen: int = 0
    records_valid: int = 0
    records_rejected: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_conflicted: int = 0
    error_count: int = 0
    dry_run: bool = False
    summary_notes: Optional[Dict[str, Any]] = None

class CandidateTitleDetail(BaseModel):
    candidate_id: str
    provider_name: str
    external_id: str
    candidate_payload: Dict[str, Any]
    match_status: str
    matched_canonical_title_id: Optional[str] = None
    match_score: float = 0.0
    match_rule_id: Optional[str] = None
    review_status: str = "PENDING"
    created_at: str

class FieldProvenanceDetail(BaseModel):
    provenance_id: str
    entity_type: str = "TITLE"
    entity_id: str
    field_name: str
    field_value: str
    source_provider: str
    external_id: Optional[str] = None
    confidence: str = "UNKNOWN"
    verification_status: str = "UNVERIFIED"
    retrieved_at: str

class SourceRegistryEntry(BaseModel):
    provider_name: str
    source_type: str
    official_url: str
    license: str
    attribution_requirement: str
    commercial_use_status: str
    redistribution_restrictions: str
    rate_limit_per_min: int
    update_frequency: str
    authentication_requirements: str
    regions: List[str]
    available_fields: List[str]
    reliability_score: float
    last_reviewed: str
    access_status: str

