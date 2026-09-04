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

class DataSourceUpdateRequest(BaseModel):
    activation_status: Optional[str] = None
    access_status: Optional[str] = None
    rate_limit_per_min: Optional[int] = None
    reliability_score: Optional[float] = None
    authority_role: Optional[str] = None
    description: Optional[str] = None

@router.get("/ingestion/sources", dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def list_data_sources(
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Returns Data Source Registry metadata, licensing statuses, and rate limits."""
    from ..ingestion.licensing import licensing_gate
    return await licensing_gate.get_source_registry_async(db=db)

@router.get("/ingestion/sources/{source_id}", dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def get_data_source(
    source_id: str,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Retrieves a single data source registry record."""
    from ..ingestion.licensing import licensing_gate
    registry = await licensing_gate.get_source_registry_async(db=db)
    match = next((v for k, v in registry.items() if v.get("source_id") == source_id or k.lower() == source_id.lower()), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Data source '{source_id}' not found")
    return match

@router.patch("/ingestion/sources/{source_id}", dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def update_data_source(
    source_id: str,
    body: DataSourceUpdateRequest,
    claims: SecurityTokenClaims = Depends(require_system_admin),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Updates data source registry governance fields (requires SystemAdmin)."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database connection required for registry updates")

    from ..models.ingestion import DataSourceRegistryModel
    from sqlalchemy import select

    stmt = select(DataSourceRegistryModel).where(
        (DataSourceRegistryModel.source_id == source_id) |
        (DataSourceRegistryModel.provider_name.ilike(source_id))
    )
    res = await db.execute(stmt)
    source = res.scalars().first()
    if not source:
        raise HTTPException(status_code=404, detail=f"Data source '{source_id}' not found")

    if body.activation_status is not None:
        source.activation_status = body.activation_status
    if body.access_status is not None:
        source.access_status = body.access_status
    if body.rate_limit_per_min is not None:
        source.rate_limit_per_min = body.rate_limit_per_min
    if body.reliability_score is not None:
        source.reliability_score = body.reliability_score
    if body.authority_role is not None:
        source.authority_role = body.authority_role
    if body.description is not None:
        source.description = body.description

    source.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return {
        "status": "UPDATED",
        "source_id": source.source_id,
        "provider_name": source.provider_name,
        "activation_status": source.activation_status,
        "access_status": source.access_status,
        "rate_limit_per_min": source.rate_limit_per_min
    }

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
    result = await ingestion_repository.get_raw_payload_by_id(db=db, raw_payload_id=raw_payload_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Raw payload '{raw_payload_id}' not found.")
    return result

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
    result = await quality_repository.resolve_metadata_conflict(
        db=db,
        conflict_id=conflict_id,
        actor_id=claims.sub,
        winning_value=body.winning_value,
        resolution_notes=body.resolution_notes
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Metadata conflict '{conflict_id}' not found.")
    return result

@router.post("/reconciliation/candidates/{candidate_id}/promote", status_code=status.HTTP_200_OK, dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def promote_candidate(
    candidate_id: str,
    body: PromotionDecisionRequest,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Approves human curation decision and promotes record to CAT-1 Canonical Platform Data."""
    result = await quality_repository.promote_candidate(
        db=db,
        candidate_id=candidate_id,
        actor_id=claims.sub,
        rationale=body.rationale,
        override_fields=body.override_fields
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconciliation candidate '{candidate_id}' not found.")
    return result

@router.post("/reconciliation/candidates/{candidate_id}/reject", status_code=status.HTTP_200_OK, dependencies=[Depends(enforce_rate_limit("INTERNAL_ADMIN"))])
async def reject_candidate(
    candidate_id: str,
    body: PromotionDecisionRequest,
    claims: SecurityTokenClaims = Depends(require_curator),
    db: Optional[AsyncSession] = Depends(get_db)
):
    """Rejects reconciliation candidate with logged audit rationale."""
    result = await quality_repository.reject_candidate(
        db=db,
        candidate_id=candidate_id,
        actor_id=claims.sub,
        rationale=body.rationale
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconciliation candidate '{candidate_id}' not found.")
    return result

from ..storage import storage_adapter, StorageError

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
    """Uploads artwork image to local storage and returns its canonical CDN URL."""
    import base64
    try:
        file_bytes = base64.b64decode(body.file_base64)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid base64 artwork content.")

    try:
        cdn_url = storage_adapter.upload_artwork(
            file_bytes=file_bytes,
            filename=body.filename,
            content_type=body.content_type,
            folder=body.folder,
        )
        object_key = storage_adapter.generate_object_key(body.filename, folder=body.folder)
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return ArtworkUploadResponse(
        cdn_url=cdn_url,
        filename=body.filename,
        object_key=object_key,
    )
