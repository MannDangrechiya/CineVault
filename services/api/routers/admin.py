# CineVault OS — Admin & Catalog Operations API Router
# Administrative endpoints for triggering background metadata sync, poster fetching, and maintenance tasks

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..auth.dependencies import get_optional_claims
from ..auth.jwt_validator import SecurityTokenClaims
from ..config import config
from ..ingestion.tmdb_worker import sync_missing_posters
from ..rate_limiter import enforce_rate_limit

logger = logging.getLogger("cinevault.routers.admin")

router = APIRouter(prefix="/admin", tags=["Admin & Metadata Operations"])


class SyncMetadataRequest(BaseModel):
    tmdb_api_key: Optional[str] = Field(None, description="Optional TMDB API Key override")
    batch_size: int = Field(500, ge=1, le=5000, description="Number of titles to process per query batch")
    max_batches: Optional[int] = Field(None, ge=1, description="Maximum batches to run before stopping")


class SyncMetadataResponse(BaseModel):
    status: str
    job_id: str
    message: str
    batch_size: int
    max_batches: Optional[int]
    triggered_at: str


async def _run_metadata_sync_task(
    job_id: str,
    api_key: Optional[str],
    batch_size: int,
    max_batches: Optional[int],
) -> None:
    """Background task runner for TMDB metadata and poster synchronization."""
    logger.info("Starting background metadata sync job %s...", job_id)
    try:
        stats = await sync_missing_posters(
            tmdb_api_key=api_key,
            batch_size=batch_size,
            max_batches=max_batches,
        )
        logger.info("Background metadata sync job %s completed successfully: %s", job_id, stats)
    except Exception as e:
        logger.error("Background metadata sync job %s failed with exception: %s", job_id, e)


@router.post(
    "/sync-metadata",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SyncMetadataResponse,
    summary="Trigger TMDB poster, backdrop, and metadata synchronization",
)
async def trigger_metadata_sync(
    background_tasks: BackgroundTasks,
    payload: Optional[SyncMetadataRequest] = None,
    batch_size: int = Query(500, ge=1, le=5000, description="Batch size per query"),
    max_batches: Optional[int] = Query(None, ge=1, description="Optional max batch count"),
    api_key: Optional[str] = Query(None, description="Optional TMDB API key override"),
    claims: Optional[SecurityTokenClaims] = Depends(get_optional_claims),
) -> SyncMetadataResponse:
    """
    Kicks off asynchronous background synchronization of posters, backdrops, and synopses from TMDB.
    Titles missing artwork are queried, throttled to 20 req/s, and updated safely in PostgreSQL.
    """
    effective_batch_size = payload.batch_size if payload else batch_size
    effective_max_batches = payload.max_batches if payload else max_batches
    effective_api_key = (payload.tmdb_api_key if payload and payload.tmdb_api_key else api_key) or config.tmdb_api_key

    job_id = f"sync-meta-{uuid.uuid4().hex[:12]}"
    triggered_at = datetime.now(timezone.utc).isoformat()

    background_tasks.add_task(
        _run_metadata_sync_task,
        job_id=job_id,
        api_key=effective_api_key,
        batch_size=effective_batch_size,
        max_batches=effective_max_batches,
    )

    logger.info(
        "Dispatched background metadata sync job %s (batch_size=%d, max_batches=%s)",
        job_id,
        effective_batch_size,
        effective_max_batches,
    )

    return SyncMetadataResponse(
        status="ACCEPTED",
        job_id=job_id,
        message="Background TMDB artwork & metadata synchronization dispatched.",
        batch_size=effective_batch_size,
        max_batches=effective_max_batches,
        triggered_at=triggered_at,
    )
