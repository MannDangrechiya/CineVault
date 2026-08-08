# CineVault OS — Control Room / Curation Foundation Router (Build Unit 8.10)
# Privileged administrative endpoints for human curation, quarantine inspection, evidence breakdown, and audit tracking

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.control_room import (
    ControlRoomSummaryStats,
    QuarantineRecordResponse,
    QuarantineResolveRequest,
    CandidateDetailResponse,
    ControlRoomAuditLogResponse
)
from ..schemas.internal import (
    ReconciliationCandidateSummary,
    PromotionDecisionRequest
)
from ..auth.dependencies import require_curator
from ..auth.jwt_validator import SecurityTokenClaims
from ..rate_limiter import enforce_rate_limit
from ..database import get_db
from ..repositories.control_room import control_room_repository
from ..repositories.quality import quality_repository

router = APIRouter(prefix="/internal/v1/control-room", tags=["Control Room Curation (8.10)"])

@router.get("/stats", response_model=ControlRoomSummaryStats, dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def get_summary_stats(
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves operational summary counts for Control Room administration dashboard."""
    return await control_room_repository.get_summary_stats(db=db)

@router.get("/quarantine", response_model=List[QuarantineRecordResponse], dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_quarantine_records(
    status_filter: Optional[str] = Query("PENDING", description="Status filter (PENDING, RESOLVED, DISCARDED)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Lists ingestion quarantine records for curator inspection."""
    return await control_room_repository.list_quarantine_records(
        db=db,
        status_filter=status_filter,
        limit=limit,
        offset=offset
    )

@router.post("/quarantine/{quarantine_id}/resolve", dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def resolve_quarantine_record(
    quarantine_id: str,
    body: QuarantineResolveRequest,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Resolves an ingestion quarantine record with logged curator audit rationale."""
    return await control_room_repository.resolve_quarantine_record(
        db=db,
        quarantine_id=quarantine_id,
        actor_id=claims.sub,
        body=body
    )

@router.get("/candidates", response_model=List[ReconciliationCandidateSummary], dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_reconciliation_candidates(
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Lists reconciliation candidates flagged for human review or curation."""
    return await quality_repository.list_reconciliation_candidates(db=db)

@router.get("/candidates/{candidate_id}", response_model=CandidateDetailResponse, dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def get_candidate_detail(
    candidate_id: str,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves detailed evidence & provenance breakdown for a reconciliation candidate."""
    return await control_room_repository.get_candidate_detail(
        db=db,
        candidate_id=candidate_id
    )

@router.post("/candidates/{candidate_id}/promote", dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
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

@router.post("/candidates/{candidate_id}/reject", dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def reject_candidate(
    candidate_id: str,
    body: PromotionDecisionRequest,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Rejects reconciliation candidate with logged curator audit rationale."""
    return await quality_repository.reject_candidate(
        db=db,
        candidate_id=candidate_id,
        actor_id=claims.sub,
        rationale=body.rationale
    )

@router.get("/audit-log", response_model=List[ControlRoomAuditLogResponse], dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_audit_log_entries(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Inspects immutable system audit logs signed with SHA-256 HMAC integrity."""
    return await control_room_repository.list_audit_log_entries(
        db=db,
        limit=limit,
        offset=offset
    )
