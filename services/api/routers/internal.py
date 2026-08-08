# CineVault OS — Internal Operational & Curation Router
# Control Room administrative endpoints for ingestion monitoring, reconciliation curation, and AI proposals

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

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
from ..database import get_db
from ..repositories.ingestion import ingestion_repository
from ..repositories.quality import quality_repository

router = APIRouter(prefix="/internal/v1", tags=["Internal Operational & Curation"])

@router.get("/ingestion/runs", response_model=List[IngestionRunSummary], dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_ingestion_runs(
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Inspects historical and active ingestion pipeline executions."""
    return await ingestion_repository.list_ingestion_runs(db=db)

@router.get("/ingestion/raw-payloads/{raw_payload_id}", response_model=RawPayloadDetail, dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def get_raw_payload(
    raw_payload_id: str,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves immutable raw provider payload (CAT-5)."""
    return await ingestion_repository.get_raw_payload_by_id(db=db, raw_payload_id=raw_payload_id)

@router.get("/reconciliation/candidates", response_model=List[ReconciliationCandidateSummary], dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_reconciliation_candidates(
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Fetches reconciliation candidates flagged for human review or merge/split curation."""
    return await quality_repository.list_reconciliation_candidates(db=db)

@router.post("/reconciliation/candidates/{candidate_id}/promote", status_code=status.HTTP_200_OK, dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def promote_candidate(
    candidate_id: str,
    body: PromotionDecisionRequest,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Approves human curation decision and promotes record to CAT-1 Canonical Platform Data."""
    return await quality_repository.promote_candidate(
        db=db,
        candidate_id=candidate_id,
        actor_id=claims.sub,
        rationale=body.rationale,
        override_fields=body.override_fields
    )

@router.post("/reconciliation/candidates/{candidate_id}/reject", status_code=status.HTTP_200_OK, dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def reject_candidate(
    candidate_id: str,
    body: PromotionDecisionRequest,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Rejects reconciliation candidate with logged audit rationale."""
    return await quality_repository.reject_candidate(
        db=db,
        candidate_id=candidate_id,
        actor_id=claims.sub,
        rationale=body.rationale
    )

@router.get("/ai/proposals", response_model=List[AIProposalSummary], dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_ai_proposals(
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Inspects CAT-6 AI proposal candidates. AI endpoints cannot directly write to CAT-1."""
    return await quality_repository.list_ai_proposals(db=db)
