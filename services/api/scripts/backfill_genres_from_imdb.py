#!/usr/bin/env python3
"""
CineVault OS — IMDb Genre Backfill
Downloads the public IMDb title.basics.tsv.gz dataset and populates
canonical.genre / canonical.title_genre for titles that were bulk-imported
via seed_bulk_imdb.py without genre data (that importer never read the
genres column). Matches purely on IMDb tconst (display_id = "IMDB-{tconst}").
"""

import argparse
import asyncio
import csv
import gzip
import logging
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import asyncpg
import httpx

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api.config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("cinevault.ingestion.backfill_genres")

IMDB_BASICS_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"
DEFAULT_BATCH_SIZE = 10000


def slugify_genre(name: str) -> str:
    """Normalize a genre display name into the existing genre_id convention
    (lowercase, non-alphanumeric collapsed to underscore) so IMDb's "Sci-Fi"
    lands on the same row as the already-seeded "sci_fi" genre."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return slug[:64]


async def download_basics(dest_path: Path, client: httpx.AsyncClient) -> Path:
    """Streams title.basics.tsv.gz from IMDb to a local destination path."""
    logger.info("Downloading %s -> %s", IMDB_BASICS_URL, dest_path)
    start_time = time.time()
    downloaded_bytes = 0

    async with client.stream("GET", IMDB_BASICS_URL, follow_redirects=True) as response:
        if response.status_code != 200:
            raise RuntimeError(f"Failed to download {IMDB_BASICS_URL}: HTTP {response.status_code}")

        total_bytes = int(response.headers.get("content-length", 0))
        total_mb = f"{total_bytes / (1024 * 1024):.1f} MB" if total_bytes else "unknown size"
        logger.info("Content length: %s", total_mb)

        with open(dest_path, "wb") as f:
            async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                f.write(chunk)
                downloaded_bytes += len(chunk)
                if total_bytes and downloaded_bytes % (1024 * 1024 * 20) == 0:
                    pct = (downloaded_bytes / total_bytes) * 100
                    logger.info("Downloading: %.1f%% (%d / %d MB)", pct,
                                downloaded_bytes // (1024 * 1024), total_bytes // (1024 * 1024))

    elapsed = time.time() - start_time
    mb = downloaded_bytes / (1024 * 1024)
    logger.info("Downloaded %.2f MB in %.1fs (%.2f MB/s)", mb, elapsed, mb / elapsed if elapsed > 0 else 0)
    return dest_path


async def create_db_pool() -> asyncpg.Pool:
    host = os.getenv("POSTGRES_HOST") or config.pgbouncer_host
    port = int(os.getenv("POSTGRES_PORT") or config.pgbouncer_port)
    return await asyncpg.create_pool(
        host=host,
        port=port,
        user=config.postgres_user,
        password=config.postgres_password,
        database=config.postgres_db,
        min_size=1,
        max_size=5,
        statement_cache_size=0,
        ssl=False,
        timeout=10.0,
    )


async def load_known_tconsts(pool: asyncpg.Pool) -> Dict[str, str]:
    """Returns {tconst: title_id} for every IMDb-sourced title already in the catalog."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT title_id, display_id FROM canonical.title WHERE display_id LIKE 'IMDB-%';"
        )
    mapping = {row["display_id"][len("IMDB-"):]: str(row["title_id"]) for row in rows}
    logger.info("Loaded %d known IMDb titles from catalog.", len(mapping))
    return mapping


async def load_known_genres(pool: asyncpg.Pool) -> Dict[str, str]:
    """Returns {genre_id: name} for existing canonical.genre rows."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT genre_id, name FROM canonical.genre;")
    return {row["genre_id"]: row["name"] for row in rows}


async def backfill_genres(
    basics_path: Path,
    pool: asyncpg.Pool,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Dict[str, int]:
    stats = {"basics_scanned": 0, "titles_matched": 0, "genre_links_inserted": 0, "genres_created": 0}

    tconst_to_title_id = await load_known_tconsts(pool)
    known_genre_ids = await load_known_genres(pool)

    pending_genre_rows: List[Tuple[str, str]] = []  # (genre_id, name)
    pending_links: List[Tuple[str, str]] = []  # (title_id, genre_id)
    seen_genre_ids: Set[str] = set(known_genre_ids.keys())

    async def flush_batches(conn: asyncpg.Connection) -> None:
        nonlocal pending_genre_rows, pending_links
        if pending_genre_rows:
            await conn.executemany(
                """
                INSERT INTO canonical.genre (genre_id, name)
                VALUES ($1, $2)
                ON CONFLICT (genre_id) DO NOTHING;
                """,
                pending_genre_rows,
            )
            stats["genres_created"] += len(pending_genre_rows)
            pending_genre_rows = []
        if pending_links:
            await conn.executemany(
                """
                INSERT INTO canonical.title_genre (title_id, genre_id)
                VALUES ($1, $2)
                ON CONFLICT (title_id, genre_id) DO NOTHING;
                """,
                pending_links,
            )
            stats["genre_links_inserted"] += len(pending_links)
            pending_links = []

    async with pool.acquire() as conn:
        with gzip.open(basics_path, "rt", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader, None)  # header

            for row in reader:
                stats["basics_scanned"] += 1
                if len(row) < 9:
                    continue

                tconst = row[0]
                title_id = tconst_to_title_id.get(tconst)
                if not title_id:
                    continue

                genres_raw = row[8]
                if not genres_raw or genres_raw == r"\N":
                    continue

                stats["titles_matched"] += 1
                for genre_name in genres_raw.split(","):
                    genre_name = genre_name.strip()
                    if not genre_name:
                        continue
                    genre_id = slugify_genre(genre_name)
                    if not genre_id:
                        continue
                    if genre_id not in seen_genre_ids:
                        pending_genre_rows.append((genre_id, genre_name))
                        seen_genre_ids.add(genre_id)
                    pending_links.append((title_id, genre_id))

                if len(pending_links) >= batch_size:
                    await flush_batches(conn)
                    logger.info(
                        "Progress: %d basics rows scanned, %d titles matched, %d genre links inserted so far.",
                        stats["basics_scanned"], stats["titles_matched"], stats["genre_links_inserted"],
                    )

            await flush_batches(conn)

    logger.info("Backfill complete: %s", stats)
    return stats


async def main() -> None:
    parser = argparse.ArgumentParser(description="CineVault OS IMDb Genre Backfill")
    parser.add_argument("--basics-file", type=str, default=None,
                         help="Path to an existing title.basics.tsv.gz (skips download if present)")
    parser.add_argument("--data-dir", type=str, default=None,
                         help="Directory to store/read the dataset file (defaults to system temp dir)")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    args = parser.parse_args()

    data_dir = Path(args.data_dir) if args.data_dir else Path(tempfile.gettempdir()) / "cinevault_imdb_datasets"
    data_dir.mkdir(parents=True, exist_ok=True)
    basics_path = Path(args.basics_file) if args.basics_file else data_dir / "title.basics.tsv.gz"

    if not basics_path.exists() or basics_path.stat().st_size == 0:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=30.0, read=600.0, write=30.0, pool=30.0)) as client:
            await download_basics(basics_path, client)
    else:
        logger.info("Using cached dataset file: %s", basics_path)

    pool = await create_db_pool()
    try:
        start_time = time.time()
        stats = await backfill_genres(basics_path, pool, batch_size=args.batch_size)
        elapsed = time.time() - start_time
        logger.info("=== Genre backfill finished in %.2fs: %s ===", elapsed, stats)
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
