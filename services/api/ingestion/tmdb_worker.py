# CineVault OS — TMDB Background Metadata & Poster Sync Worker
# Fetches poster artwork, backdrop artwork, and synopses from TMDB API with robust rate limiting and database persistence

import argparse
import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
import httpx

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api.config import config

logger = logging.getLogger("cinevault.ingestion.tmdb_worker")

TMDB_FIND_URL_TEMPLATE = "https://api.themoviedb.org/3/find/{imdb_id}?external_source=imdb_id"
TMDB_POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
TMDB_BACKDROP_BASE_URL = "https://image.tmdb.org/t/p/w1280"

# Target safe throttle: 20 requests per second (50ms interval)
DEFAULT_RATE_LIMIT_PER_SEC = 20.0
DEFAULT_BATCH_SIZE = 500


class AsyncRateLimiter:
    """Async leaky token limiter ensuring requests never exceed the specified rate per second."""

    def __init__(self, rate_limit_per_second: float = DEFAULT_RATE_LIMIT_PER_SEC):
        self.rate = max(1.0, float(rate_limit_per_second))
        self.interval = 1.0 / self.rate
        self.lock = asyncio.Lock()
        self.last_request_time = 0.0

    async def acquire(self) -> None:
        async with self.lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_request_time
            if elapsed < self.interval:
                await asyncio.sleep(self.interval - elapsed)
            self.last_request_time = asyncio.get_event_loop().time()


class TMDBClient:
    """High-speed asynchronous TMDB client equipped with automatic rate limiting and retry handling."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit_per_sec: float = DEFAULT_RATE_LIMIT_PER_SEC,
        client: Optional[httpx.AsyncClient] = None,
    ):
        self.api_key = api_key or config.tmdb_api_key or config.provider_api_key or os.getenv("TMDB_API_KEY")
        self.limiter = AsyncRateLimiter(rate_limit_per_sec)
        self._external_client = client
        self._internal_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._external_client is not None:
            return self._external_client
        if self._internal_client is None or self._internal_client.is_closed:
            self._internal_client = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=10.0, read=20.0, write=10.0, pool=30.0)
            )
        return self._internal_client

    async def close(self) -> None:
        if self._internal_client and not self._internal_client.is_closed:
            await self._internal_client.aclose()

    def _extract_imdb_id(self, display_id: str) -> Optional[str]:
        """Extracts normalized IMDb tconst (e.g., 'tt0111161') from display_id or string."""
        if not display_id:
            return None
        clean = display_id.strip()
        if clean.upper().startswith("IMDB-"):
            clean = clean[5:]
        if clean.startswith("tt") and len(clean) >= 7:
            return clean
        return None

    async def find_by_imdb_id(self, imdb_id: str) -> Optional[Dict[str, Any]]:
        """
        Queries TMDB Find API for given IMDb ID.
        Returns extracted artwork and overview metadata or None if not found.
        """
        await self.limiter.acquire()
        client = await self._get_client()

        url = TMDB_FIND_URL_TEMPLATE.format(imdb_id=imdb_id)
        headers = {
            "Accept": "application/json",
            "User-Agent": "CineVault-OS-Worker/2.0",
        }
        params: Dict[str, str] = {}

        if self.api_key:
            if self.api_key.startswith("eyJ"):
                # JWT / v4 Read Access Token
                headers["Authorization"] = f"Bearer {self.api_key}"
            else:
                # v3 API Key query parameter
                params["api_key"] = self.api_key

        try:
            response = await client.get(url, headers=headers, params=params)
            
            if response.status_code == 404:
                return None
            
            if response.status_code == 429:
                retry_after = float(response.headers.get("Retry-After", "1.0"))
                logger.warning("TMDB 429 Too Many Requests. Backing off for %.2fs...", retry_after)
                await asyncio.sleep(retry_after)
                return await self.find_by_imdb_id(imdb_id)

            if response.status_code != 200:
                logger.warning("TMDB Find API returned status %d for %s", response.status_code, imdb_id)
                return None

            data = response.json()
            
            # TMDB find returns movies, tv, tv_episodes, tv_seasons
            results = (
                data.get("movie_results")
                or data.get("tv_results")
                or data.get("tv_episode_results")
                or data.get("tv_season_results")
                or []
            )

            if not results:
                return None

            primary = results[0]
            poster_path = primary.get("poster_path")
            backdrop_path = primary.get("backdrop_path")
            overview = primary.get("overview")

            poster_url = f"{TMDB_POSTER_BASE_URL}{poster_path}" if poster_path else None
            backdrop_url = f"{TMDB_BACKDROP_BASE_URL}{backdrop_path}" if backdrop_path else None

            return {
                "tmdb_id": primary.get("id"),
                "poster_url": poster_url,
                "backdrop_url": backdrop_url,
                "overview": overview if overview else None,
            }

        except Exception as e:
            logger.error("Exception fetching TMDB metadata for %s: %s", imdb_id, e)
            return None


async def sync_missing_posters(
    db_pool: Optional[asyncpg.Pool] = None,
    tmdb_api_key: Optional[str] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_batches: Optional[int] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """
    Background worker that queries canonical titles missing posters, fetches artwork
    from TMDB with strict rate limiting, and persists results to PostgreSQL.
    """
    stats = {
        "processed": 0,
        "synced": 0,
        "not_found": 0,
        "errors": 0,
        "batches_completed": 0,
    }

    own_pool = False
    if db_pool is None:
        try:
            host = os.getenv("POSTGRES_HOST") or config.postgres_host
            port = int(os.getenv("POSTGRES_PORT") or config.postgres_port)
            db_pool = await asyncpg.create_pool(
                host=host,
                port=port,
                user=config.postgres_user,
                password=config.postgres_password,
                database=config.postgres_db,
                min_size=1,
                max_size=5,
                statement_cache_size=0,
                ssl=False,
                timeout=5.0,
            )
            own_pool = True
        except (OSError, ConnectionRefusedError, asyncpg.PostgresError, Exception) as e:
            logger.warning("Database connection unavailable for TMDB poster sync: %s", e)
            return stats

    tmdb_client = TMDBClient(api_key=tmdb_api_key, client=client)

    try:
        batch_num = 0
        while True:
            if max_batches is not None and batch_num >= max_batches:
                break

            batch_num += 1
            logger.info("Fetching batch #%d of titles missing posters (limit=%d)...", batch_num, batch_size)

            async with db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT title_id, display_id, synopsis
                    FROM canonical.title
                    WHERE (poster_url IS NULL OR poster_sync_status = 'PENDING')
                      AND poster_sync_status NOT IN ('NOT_FOUND', 'INVALID_ID')
                    ORDER BY created_at DESC
                    LIMIT $1;
                    """,
                    batch_size,
                )

                if not rows:
                    logger.info("No more titles requiring poster sync. Worker complete.")
                    break

                logger.info("Processing %d titles in batch #%d...", len(rows), batch_num)

                for row in rows:
                    title_id = row["title_id"]
                    display_id = row["display_id"]
                    existing_synopsis = row["synopsis"]
                    stats["processed"] += 1

                    imdb_id = tmdb_client._extract_imdb_id(display_id)
                    if not imdb_id:
                        await conn.execute(
                            """
                            UPDATE canonical.title
                            SET poster_sync_status = 'INVALID_ID',
                                metadata_synced_at = clock_timestamp(),
                                updated_at = clock_timestamp()
                            WHERE title_id = $1;
                            """,
                            title_id,
                        )
                        stats["errors"] += 1
                        continue

                    try:
                        metadata = await tmdb_client.find_by_imdb_id(imdb_id)
                        if metadata and (metadata.get("poster_url") or metadata.get("backdrop_url")):
                            poster_url = metadata.get("poster_url")
                            backdrop_url = metadata.get("backdrop_url")
                            overview = metadata.get("overview")

                            # Update canonical title record
                            await conn.execute(
                                """
                                UPDATE canonical.title
                                SET poster_url = COALESCE($2, poster_url),
                                    backdrop_url = COALESCE($3, backdrop_url),
                                    synopsis = CASE
                                        WHEN synopsis IS NULL OR synopsis LIKE 'IMDb %'
                                        THEN COALESCE($4, synopsis)
                                        ELSE synopsis
                                    END,
                                    poster_sync_status = 'SYNCED',
                                    metadata_synced_at = clock_timestamp(),
                                    updated_at = clock_timestamp()
                                WHERE title_id = $1;
                                """,
                                title_id,
                                poster_url,
                                backdrop_url,
                                overview,
                            )
                            stats["synced"] += 1
                        else:
                            # Not found in TMDB or no artwork returned
                            await conn.execute(
                                """
                                UPDATE canonical.title
                                SET poster_sync_status = 'NOT_FOUND',
                                    metadata_synced_at = clock_timestamp(),
                                    updated_at = clock_timestamp()
                                WHERE title_id = $1;
                                """,
                                title_id,
                            )
                            stats["not_found"] += 1

                    except Exception as e:
                        logger.error("Failed to sync title %s (%s): %s", title_id, display_id, e)
                        stats["errors"] += 1

                stats["batches_completed"] += 1
                logger.info(
                    "Batch #%d finished. Progress: %d synced, %d not found, %d errors (total processed: %d).",
                    batch_num,
                    stats["synced"],
                    stats["not_found"],
                    stats["errors"],
                    stats["processed"],
                )

                if len(rows) < batch_size:
                    break

    finally:
        await tmdb_client.close()
        if own_pool:
            await db_pool.close()

    logger.info("Poster sync summary: %s", stats)
    return stats


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="CineVault OS TMDB Background Metadata & Poster Sync Worker"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="TMDB API Key (defaults to TMDB_API_KEY environment variable)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Batch size per query (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=None,
        help="Maximum batches to process before exiting (default: run until complete)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=DEFAULT_RATE_LIMIT_PER_SEC,
        help=f"Requests per second throttle (default: {DEFAULT_RATE_LIMIT_PER_SEC})",
    )

    args = parser.parse_args()

    logger.info("=== Starting TMDB Background Poster Sync Worker ===")
    start_time = time.time()
    stats = await sync_missing_posters(
        tmdb_api_key=args.api_key,
        batch_size=args.batch_size,
        max_batches=args.max_batches,
    )
    elapsed = time.time() - start_time
    logger.info("=== Worker Finished in %.2fs. Total Synced: %d ===", elapsed, stats["synced"])


if __name__ == "__main__":
    asyncio.run(main())
