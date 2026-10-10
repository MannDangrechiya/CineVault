# CineVault OS — Automated Catalog Refresh & Metadata Sync Scheduler
# Runs the same pipelines exposed by /admin/catalog/sync-bulk and
# /admin/sync-metadata on a recurring interval, in-process, so new/updated
# titles and artwork keep appearing without a human triggering them
# manually. See REMAINING_WORK_PLAN.md's "Infrastructure & External
# Services" section — this is the "auto updated content" piece that was
# previously just an admin-triggered endpoint with no timer behind it.

import logging
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import config
from .ingestion.tmdb_worker import sync_missing_posters
from .scripts.backfill_country_from_imdb import backfill_countries, download_akas
from .scripts.backfill_genres_from_imdb import backfill_genres
from .scripts.seed_bulk_imdb import (
    DEFAULT_BATCH_SIZE as BULK_DEFAULT_BATCH_SIZE,
    DEFAULT_MIN_VOTES as BULK_DEFAULT_MIN_VOTES,
    create_db_pool as create_bulk_db_pool,
    download_imdb_datasets,
    process_and_import,
)

logger = logging.getLogger("cinevault.scheduler")

_SCHEDULER_DATA_DIR = Path(tempfile.gettempdir()) / "cinevault_scheduler_data"

# Postgres advisory lock keys. Production runs 4 uvicorn workers (see
# services/api/Dockerfile) and each one would otherwise start its own
# in-process scheduler, quadrupling every download and racing the same DB
# writes. A session-level advisory lock held on a dedicated connection for
# the job's full duration makes "only one worker actually runs this" true
# without adding a new infra dependency — Postgres is already load-bearing
# for everything else here. Arbitrary but stable bigints, one per job.
_CATALOG_REFRESH_LOCK_KEY = 72100583001
_POSTER_SYNC_LOCK_KEY = 72100583002

# Per-process status snapshot, surfaced via GET /admin/scheduler/status.
# Deliberately in-memory/per-worker (matches every other single-process
# assumption in this codebase, e.g. the rate limiter's in-process fallback)
# — good enough for the "owner + a handful of friends" deployment profile
# this stack targets; a real multi-worker aggregate view isn't worth the
# complexity it would add.
_job_status: Dict[str, Dict[str, Any]] = {
    "catalog_refresh": {"last_run_at": None, "last_result": None, "last_error": None},
    "poster_sync": {"last_run_at": None, "last_result": None, "last_error": None},
}

_scheduler: Optional[AsyncIOScheduler] = None


def _record(job_name: str, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
    _job_status[job_name] = {
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "last_result": result,
        "last_error": error,
    }


async def run_catalog_refresh_job() -> None:
    """
    Full catalog freshness pass: re-downloads IMDb's daily-refreshed public
    datasets, upserts any new/newly-qualified titles (process_and_import
    uses ON CONFLICT DO NOTHING -- never touches existing rows), then
    re-runs the genre and country-of-origin backfills so newly added titles
    get enriched the same way the original 89k-title catalog was built (see
    WEB_FEATURE_AUDIT.md). Always re-downloads rather than reusing a cached
    file, since IMDb refreshes these daily and a long-lived scheduler would
    otherwise serve the same snapshot forever.
    """
    pool = await create_bulk_db_pool()
    try:
        async with pool.acquire() as lock_conn:
            acquired = await lock_conn.fetchval("SELECT pg_try_advisory_lock($1)", _CATALOG_REFRESH_LOCK_KEY)
            if not acquired:
                logger.info("Catalog refresh skipped: another worker already holds the scheduler lock.")
                return

            try:
                logger.info("Scheduled catalog refresh starting...")
                _SCHEDULER_DATA_DIR.mkdir(parents=True, exist_ok=True)
                basics_path = _SCHEDULER_DATA_DIR / "title.basics.tsv.gz"
                ratings_path = _SCHEDULER_DATA_DIR / "title.ratings.tsv.gz"
                akas_path = _SCHEDULER_DATA_DIR / "title.akas.tsv.gz"
                for stale in (basics_path, ratings_path, akas_path):
                    stale.unlink(missing_ok=True)

                basics_path, ratings_path = await download_imdb_datasets(_SCHEDULER_DATA_DIR)
                title_stats = await process_and_import(
                    db_pool=pool,
                    basics_path=basics_path,
                    ratings_path=ratings_path,
                    min_votes=BULK_DEFAULT_MIN_VOTES,
                    batch_size=BULK_DEFAULT_BATCH_SIZE,
                )

                genre_stats = await backfill_genres(basics_path, pool)

                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(connect=30.0, read=600.0, write=30.0, pool=30.0)
                ) as client:
                    await download_akas(akas_path, client)
                country_stats = await backfill_countries(akas_path, pool)

                result = {"titles": title_stats, "genres": genre_stats, "countries": country_stats}
                logger.info("Scheduled catalog refresh complete: %s", result)
                _record("catalog_refresh", result=result)
            except Exception as exc:
                logger.error("Scheduled catalog refresh failed: %s", exc, exc_info=True)
                _record("catalog_refresh", error=str(exc))
            finally:
                await lock_conn.execute("SELECT pg_advisory_unlock($1)", _CATALOG_REFRESH_LOCK_KEY)
    finally:
        await pool.close()


async def run_poster_sync_job() -> None:
    """
    TMDB poster/backdrop/synopsis sync for titles missing artwork. Skipped
    (not an error) when no TMDB_API_KEY is configured -- hammering TMDB with
    guaranteed-401s on a timer would just be log noise, the same honest-
    degradation pattern already used for the AI provider mock fallback
    rather than crashing or spamming errors.
    """
    if not config.tmdb_api_key:
        logger.info("Scheduled poster sync skipped: TMDB_API_KEY not configured.")
        _record("poster_sync", result={"skipped": "no TMDB_API_KEY configured"})
        return

    pool = await create_bulk_db_pool()
    try:
        async with pool.acquire() as lock_conn:
            acquired = await lock_conn.fetchval("SELECT pg_try_advisory_lock($1)", _POSTER_SYNC_LOCK_KEY)
            if not acquired:
                logger.info("Poster sync skipped: another worker already holds the scheduler lock.")
                return

            try:
                logger.info("Scheduled poster sync starting...")
                stats = await sync_missing_posters(
                    tmdb_api_key=config.tmdb_api_key,
                    batch_size=config.poster_sync_batch_size,
                    max_batches=config.poster_sync_max_batches,
                )
                logger.info("Scheduled poster sync complete: %s", stats)
                _record("poster_sync", result=stats)
            except Exception as exc:
                logger.error("Scheduled poster sync failed: %s", exc, exc_info=True)
                _record("poster_sync", error=str(exc))
            finally:
                await lock_conn.execute("SELECT pg_advisory_unlock($1)", _POSTER_SYNC_LOCK_KEY)
    finally:
        await pool.close()


def start_scheduler() -> Optional[AsyncIOScheduler]:
    """
    Starts the background auto-update scheduler from the FastAPI lifespan.
    No-op during pytest (same `"pytest" in sys.modules` gate used by
    database.py's pool selection -- multi-minute network jobs firing mid
    test-run would be its own source of flakiness) and when
    AUTO_INGESTION_ENABLED=false. Deliberately does NOT run a job
    immediately on startup: uvicorn --reload restarts the whole process on
    every file save, which would otherwise re-trigger a ~700MB download
    chain on every local edit during development.
    """
    global _scheduler
    if "pytest" in sys.modules:
        logger.info("Auto-update scheduler not started: running under pytest.")
        return None
    if not config.auto_ingestion_enabled:
        logger.info("Auto-update scheduler not started: AUTO_INGESTION_ENABLED=false.")
        return None
    if _scheduler is not None:
        return _scheduler

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        run_catalog_refresh_job,
        trigger=IntervalTrigger(hours=config.catalog_refresh_interval_hours),
        id="catalog_refresh",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.add_job(
        run_poster_sync_job,
        trigger=IntervalTrigger(hours=config.poster_sync_interval_hours),
        id="poster_sync",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info(
        "Auto-update scheduler started (catalog refresh every %dh, poster sync every %dh).",
        config.catalog_refresh_interval_hours,
        config.poster_sync_interval_hours,
    )
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def get_scheduler_status() -> Dict[str, Any]:
    """Status snapshot backing GET /admin/scheduler/status."""
    jobs = []
    if _scheduler is not None:
        for job in _scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            })
    return {
        "enabled": config.auto_ingestion_enabled,
        "running": _scheduler is not None and _scheduler.running,
        "catalog_refresh_interval_hours": config.catalog_refresh_interval_hours,
        "poster_sync_interval_hours": config.poster_sync_interval_hours,
        "jobs": jobs,
        "job_history": _job_status,
    }
