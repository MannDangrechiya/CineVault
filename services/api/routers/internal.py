# CineVault OS — Internal Operational & Curation Router
# Control Room administrative endpoints for ingestion monitoring, reconciliation curation, and AI proposals

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas.internal import (
    IngestionRunSummary, RawPayloadDetail,
    ReconciliationCandidateSummary, PromotionDecisionRequest,
    AIProposalSummary
)
from ..auth.dependencies import require_curator, require_system_admin, verify_service_identity
from ..auth.jwt_validator import SecurityTokenClaims
from ..auth.rbac import RBACPolicyEngine, HighRiskAuthError
from ..auth.audit import audit_logger
from ..rate_limiter import enforce_rate_limit

router = APIRouter(prefix="/internal/v1", tags=["Internal Operational & Curation"])

@router.get("/ingestion/runs", response_model=List[IngestionRunSummary], dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_ingestion_runs(claims: SecurityTokenClaims = Depends(require_curator)):
    """Inspects historical and active ingestion pipeline executions."""
    return [
        IngestionRunSummary(
            run_id="run_20260808_001",
            provider_id="KOBIS",
            status="COMPLETED",
            started_at="2026-08-08T10:00:00Z",
            completed_at="2026-08-08T10:05:00Z",
            records_fetched=150,
            records_quarantined=2
        )
    ]

@router.get("/ingestion/raw-payloads/{raw_payload_id}", response_model=RawPayloadDetail, dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def get_raw_payload(raw_payload_id: str, claims: SecurityTokenClaims = Depends(require_curator)):
    """Retrieves immutable raw provider payload (CAT-5)."""
    return RawPayloadDetail(
        raw_payload_id=raw_payload_id,
        provider_id="TMDB",
        payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        payload_data={"id": 496243, "title": "Parasite", "vote_average": 8.5},
        captured_at="2026-08-08T10:01:00Z"
    )

@router.get("/reconciliation/candidates", response_model=List[ReconciliationCandidateSummary], dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_reconciliation_candidates(claims: SecurityTokenClaims = Depends(require_curator)):
    """Fetches reconciliation candidates flagged for human review or merge/split curation."""
    return [
        ReconciliationCandidateSummary(
            candidate_id="cand_001",
            source_provider="TMDB",
            suggested_action="MERGE_CANDIDATE",
            match_confidence=0.92,
            status="PENDING_REVIEW"
        )
    ]

@router.post("/reconciliation/candidates/{candidate_id}/promote", status_code=status.HTTP_200_OK, dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def promote_candidate(
    candidate_id: str,
    body: PromotionDecisionRequest,
    claims: SecurityTokenClaims = Depends(require_curator)
):
    """Approves human curation decision and promotes record to CAT-1 Canonical Platform Data."""
    audit_record = audit_logger.log_event(
        event_type="AUDIT_CANONICAL_PROMOTION",
        actor_id=claims.sub,
        target_id=candidate_id,
        details={"rationale": body.rationale, "override_fields": body.override_fields}
    )
    return {
        "status": "PROMOTED",
        "candidate_id": candidate_id,
        "promoted_by": claims.sub,
        "rationale": body.rationale,
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "integrity_hash": audit_record["integrity_hash"]
    }

@router.post("/reconciliation/candidates/{candidate_id}/reject", status_code=status.HTTP_200_OK, dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def reject_candidate(
    candidate_id: str,
    body: PromotionDecisionRequest,
    claims: SecurityTokenClaims = Depends(require_curator)
):
    """Rejects reconciliation candidate with logged audit rationale."""
    audit_record = audit_logger.log_event(
        event_type="AUDIT_AI_PROPOSAL_DECISION",
        actor_id=claims.sub,
        target_id=candidate_id,
        details={"action": "REJECT", "rationale": body.rationale}
    )
    return {
        "status": "REJECTED",
        "candidate_id": candidate_id,
        "rejected_by": claims.sub,
        "rationale": body.rationale,
        "rejected_at": datetime.now(timezone.utc).isoformat(),
        "integrity_hash": audit_record["integrity_hash"]
    }

@router.get("/ai/proposals", response_model=List[AIProposalSummary], dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_ai_proposals(claims: SecurityTokenClaims = Depends(require_curator)):
    """Inspects CAT-6 AI proposal candidates. AI endpoints cannot directly write to CAT-1."""
    return [
        AIProposalSummary(
            proposal_id="prop_ai_991",
            target_title_id="018f2e4a-7b31-7000-8000-123456789abc",
            proposal_type="SYNOPSIS_ENHANCEMENT",
            confidence_score=0.88,
            provenance_type="AI_GENERATED",
            model_id="cinevault-synopsis-v1",
            suggested_attributes={"enhanced_synopsis": "An AI proposed localized synopsis summary."}
        )
    ]
