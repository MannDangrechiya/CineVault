# CineVault OS — Admin & Catalog Operations API Router
# Administrative endpoints for triggering background metadata sync, poster fetching, and maintenance tasks

import logging
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..auth.dependencies import require_system_admin
from ..auth.jwt_validator import SecurityTokenClaims
from ..config import config
from ..ingestion.tmdb_worker import sync_missing_posters
from ..rate_limiter import enforce_rate_limit
from ..scripts.seed_bulk_imdb import (
    DEFAULT_BATCH_SIZE as BULK_DEFAULT_BATCH_SIZE,
    DEFAULT_MIN_VOTES as BULK_DEFAULT_MIN_VOTES,
    create_db_pool as create_bulk_db_pool,
    download_imdb_datasets,
    process_and_import,
)

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
    claims: SecurityTokenClaims = Depends(require_system_admin),
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


class BulkCatalogSyncRequest(BaseModel):
    min_votes: int = Field(BULK_DEFAULT_MIN_VOTES, ge=0, description="Minimum IMDb vote threshold for inclusion")
    batch_size: int = Field(BULK_DEFAULT_BATCH_SIZE, ge=1, le=50000, description="Database copy batch size")
    skip_download: bool = Field(False, description="Reuse previously downloaded dataset files instead of re-fetching")


class BulkCatalogSyncResponse(BaseModel):
    status: str
    job_id: str
    message: str
    min_votes: int
    batch_size: int
    triggered_at: str


async def _run_bulk_catalog_sync_task(
    job_id: str,
    min_votes: int,
    batch_size: int,
    skip_download: bool,
) -> None:
    """Background task runner for the automated bulk IMDb catalog ingestion pipeline."""
    logger.info(
        "Starting background bulk IMDb catalog sync job %s (min_votes=%d, batch_size=%d)...",
        job_id,
        min_votes,
        batch_size,
    )
    pool = None
    try:
        pool = await create_bulk_db_pool()
        data_dir = Path(tempfile.gettempdir()) / "cinevault_imdb_data"

        if skip_download:
            basics_path = data_dir / "title.basics.tsv.gz"
            ratings_path = data_dir / "title.ratings.tsv.gz"
            if not basics_path.exists() or not ratings_path.exists():
                logger.error(
                    "Bulk catalog sync job %s: skip_download requested but cached dataset files are missing in %s",
                    job_id,
                    data_dir,
                )
                return
        else:
            basics_path, ratings_path = await download_imdb_datasets(data_dir)

        stats = await process_and_import(
            db_pool=pool,
            basics_path=basics_path,
            ratings_path=ratings_path,
            min_votes=min_votes,
            batch_size=batch_size,
        )
        logger.info("Bulk catalog sync job %s completed successfully: %s", job_id, stats)
    except Exception as e:
        logger.error("Bulk catalog sync job %s failed with exception: %s", job_id, e, exc_info=True)
    finally:
        if pool is not None:
            await pool.close()


@router.post(
    "/catalog/sync-bulk",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=BulkCatalogSyncResponse,
    summary="Trigger automated bulk IMDb ingestion into canonical.title",
)
async def trigger_bulk_catalog_sync(
    background_tasks: BackgroundTasks,
    payload: Optional[BulkCatalogSyncRequest] = None,
    min_votes: int = Query(BULK_DEFAULT_MIN_VOTES, ge=0, description="Minimum IMDb vote threshold for inclusion"),
    batch_size: int = Query(BULK_DEFAULT_BATCH_SIZE, ge=1, le=50000, description="Database copy batch size"),
    skip_download: bool = Query(False, description="Reuse previously downloaded dataset files instead of re-fetching"),
    claims: SecurityTokenClaims = Depends(require_system_admin),
) -> BulkCatalogSyncResponse:
    """
    Kicks off asynchronous background bulk ingestion of the IMDb title.basics/title.ratings
    datasets into canonical.title, wrapping the same download → filter → binary bulk-copy
    pipeline as scripts/seed_bulk_imdb.py so it can be triggered on-demand or scheduled
    (e.g. via cron hitting this endpoint weekly) instead of only run manually from the CLI.
    """
    effective_min_votes = payload.min_votes if payload else min_votes
    effective_batch_size = payload.batch_size if payload else batch_size
    effective_skip_download = payload.skip_download if payload else skip_download

    job_id = f"sync-bulk-{uuid.uuid4().hex[:12]}"
    triggered_at = datetime.now(timezone.utc).isoformat()

    background_tasks.add_task(
        _run_bulk_catalog_sync_task,
        job_id=job_id,
        min_votes=effective_min_votes,
        batch_size=effective_batch_size,
        skip_download=effective_skip_download,
    )

    logger.info(
        "Dispatched bulk catalog sync job %s (min_votes=%d, batch_size=%d, skip_download=%s)",
        job_id,
        effective_min_votes,
        effective_batch_size,
        effective_skip_download,
    )

    return BulkCatalogSyncResponse(
        status="ACCEPTED",
        job_id=job_id,
        message="Background bulk IMDb catalog ingestion dispatched.",
        min_votes=effective_min_votes,
        batch_size=effective_batch_size,
        triggered_at=triggered_at,
    )
