# CineVault OS — Internal Operational & Curation Router
# Control Room administrative endpoints for ingestion monitoring, reconciliation curation, metadata conflicts, and AI proposals

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.internal import (
    IngestionRunSummary, RawPayloadDetail,
    ReconciliationCandidateSummary, PromotionDecisionRequest,
    AIProposalSummary, IngestionTriggerRequest
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

class ConflictResolutionRequest(BaseModel):
    winning_value: str
    resolution_notes: str

@router.get("/ingestion/sources", dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_data_sources(
    claims: SecurityTokenClaims = Depends(require_curator)
):
    """Returns Data Source Registry metadata, licensing statuses, and rate limits."""
    from ..ingestion.licensing import licensing_gate
    return licensing_gate.get_source_registry()

@router.post("/ingestion/trigger", dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def trigger_ingestion_pipeline(
    body: IngestionTriggerRequest,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Triggers Day 4/5 ingestion pipeline execution for specified provider and payloads."""
    from ..ingestion.pipeline import pipeline_engine
    return await pipeline_engine.execute_run(db=db, trigger_req=body)

@router.get("/ingestion/candidates", dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_candidate_titles(
    provider_name: Optional[str] = None,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Lists staged candidate titles awaiting curation review or controlled apply."""
    return await ingestion_repository.list_candidate_titles(db=db, provider_name=provider_name)

@router.get("/ingestion/provenance/{entity_id}", dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_field_provenance(
    entity_id: str,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Inspects field provenance records for target entity."""
    return await ingestion_repository.list_field_provenance(db=db, entity_id=entity_id)

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

@router.get("/reconciliation/conflicts", dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_metadata_conflicts(
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Fetches active metadata conflicts requiring review or resolution."""
    return await quality_repository.list_metadata_conflicts(db=db)

@router.post("/reconciliation/conflicts/{conflict_id}/resolve", status_code=status.HTTP_200_OK, dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def resolve_metadata_conflict(
    conflict_id: str,
    body: ConflictResolutionRequest,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Resolves active metadata conflict, logging winning choice and resolution audit provenance."""
    return await quality_repository.resolve_metadata_conflict(
        db=db,
        conflict_id=conflict_id,
        actor_id=claims.sub,
        winning_value=body.winning_value,
        resolution_notes=body.resolution_notes
    )

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

from ..storage import storage_adapter

class ArtworkUploadRequest(BaseModel):
    filename: str
    content_type: str = "image/jpeg"
    folder: str = "posters"
    file_base64: str

class ArtworkUploadResponse(BaseModel):
    cdn_url: str
    filename: str
    object_key: str

@router.get("/ai/proposals", response_model=List[AIProposalSummary], dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_ai_proposals(
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Inspects CAT-6 AI proposal candidates. AI endpoints cannot directly write to CAT-1."""
    return await quality_repository.list_ai_proposals(db=db)

@router.post("/artwork/upload", response_model=ArtworkUploadResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def upload_artwork(
    body: ArtworkUploadRequest,
    claims: SecurityTokenClaims = Depends(require_curator),
):
    """Uploads artwork image to S3/MinIO object storage bucket and returns canonical CDN URL."""
    import base64
    try:
        file_bytes = base64.b64decode(body.file_base64)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid base64 artwork content.")

    cdn_url = storage_adapter.upload_artwork(
        file_bytes=file_bytes,
        filename=body.filename,
        content_type=body.content_type,
        folder=body.folder,
    )
    object_key = storage_adapter.generate_object_key(body.filename, folder=body.folder)

    return ArtworkUploadResponse(
        cdn_url=cdn_url,
        filename=body.filename,
        object_key=object_key,
    )
