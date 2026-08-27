#!/usr/bin/env python3
"""
CineVault OS — IMDb Country-of-Origin Backfill
Downloads the public IMDb title.akas.tsv.gz dataset and populates
canonical.title_country for titles that were bulk-imported via
seed_bulk_imdb.py without country data (that importer never ingested
country — IMDb's title.basics.tsv.gz doesn't carry it; only title.akas.tsv.gz
does, via each release's `region` field). Matches purely on IMDb tconst
(display_id = "IMDB-{tconst}"), same pattern as backfill_genres_from_imdb.py.

Honesty note: title.akas.tsv.gz's `region` field marks where a given release
title was used, not a verified "country of production" — TMDB's
production_countries field would be more semantically precise but requires
one API call per title (89k titles at TMDB's 20 req/s rate limit). This is
the best-guess free/bulk approximation: for each title we take the akas row
IMDb itself flags as the original title (`isOriginalTitle=1`) if one has a
real region code, else the lowest `ordering` row with a real region code
(IMDb's own primary/default entry). One country per title, not the full set
of regions a title happened to release into — that would overstate what
this data actually supports.
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
from typing import Dict, List, Optional, Tuple

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
logger = logging.getLogger("cinevault.ingestion.backfill_country")

IMDB_AKAS_URL = "https://datasets.imdbws.com/title.akas.tsv.gz"
DEFAULT_BATCH_SIZE = 10000

_VALID_REGION_RE = re.compile(r"^[A-Z]{2}$")


def _is_valid_region(region: str) -> bool:
    """IMDb region codes are ISO 3166-1 alpha-2, with occasional non-country
    values ("\\N" for unset, or rare multi-char aggregates) that don't fit
    the CHAR(2) column — those are skipped rather than truncated/guessed."""
    return bool(region) and region != r"\N" and bool(_VALID_REGION_RE.match(region))


async def download_akas(dest_path: Path, client: httpx.AsyncClient) -> Path:
    """Streams title.akas.tsv.gz from IMDb to a local destination path."""
    logger.info("Downloading %s -> %s", IMDB_AKAS_URL, dest_path)
    start_time = time.time()
    downloaded_bytes = 0

    async with client.stream("GET", IMDB_AKAS_URL, follow_redirects=True) as response:
        if response.status_code != 200:
            raise RuntimeError(f"Failed to download {IMDB_AKAS_URL}: HTTP {response.status_code}")

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


async def load_already_backfilled(pool: asyncpg.Pool) -> set:
    """Returns the set of title_ids that already have a country_code row, so
    a re-run doesn't need to re-decide titles it already resolved."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT DISTINCT title_id FROM canonical.title_country;")
    return {str(row["title_id"]) for row in rows}


def _best_region_for_tconst(rows_for_tconst: List[Tuple[str, str, str]]) -> Optional[str]:
    """
    rows_for_tconst: list of (ordering, region, is_original_title) tuples for
    one tconst, in file order. Prefers the isOriginalTitle=1 row's region if
    valid, else the lowest-ordering row with a valid region.
    """
    best_original: Optional[Tuple[int, str]] = None
    best_any: Optional[Tuple[int, str]] = None

    for ordering_raw, region, is_original in rows_for_tconst:
        if not _is_valid_region(region):
            continue
        try:
            ordering = int(ordering_raw)
        except ValueError:
            ordering = 0

        if best_any is None or ordering < best_any[0]:
            best_any = (ordering, region)
        if is_original == "1" and (best_original is None or ordering < best_original[0]):
            best_original = (ordering, region)

    chosen = best_original or best_any
    return chosen[1] if chosen else None


async def backfill_countries(
    akas_path: Path,
    pool: asyncpg.Pool,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Dict[str, int]:
    stats = {"akas_rows_scanned": 0, "titles_matched": 0, "titles_resolved": 0, "country_rows_inserted": 0}

    tconst_to_title_id = await load_known_tconsts(pool)
    already_done = await load_already_backfilled(pool)

    # title.akas.tsv.gz is grouped by tconst (all rows for one title are
    # contiguous, in ordering sequence) — accumulate per-tconst, flush when
    # the tconst changes so memory stays bounded regardless of file size.
    current_tconst: Optional[str] = None
    current_rows: List[Tuple[str, str, str]] = []
    pending_inserts: List[Tuple[str, str]] = []  # (title_id, country_code)

    async def flush_inserts(conn: asyncpg.Connection) -> None:
        nonlocal pending_inserts
        if pending_inserts:
            await conn.executemany(
                """
                INSERT INTO canonical.title_country (title_id, country_code)
                VALUES ($1, $2)
                ON CONFLICT (title_id, country_code) DO NOTHING;
                """,
                pending_inserts,
            )
            stats["country_rows_inserted"] += len(pending_inserts)
            pending_inserts = []

    def resolve_current(conn_pending: List[Tuple[str, str]]) -> None:
        nonlocal current_tconst, current_rows
        if current_tconst is None:
            return
        title_id = tconst_to_title_id.get(current_tconst)
        if title_id and title_id not in already_done:
            stats["titles_matched"] += 1
            region = _best_region_for_tconst(current_rows)
            if region:
                stats["titles_resolved"] += 1
                conn_pending.append((title_id, region))
        current_tconst = None
        current_rows = []

    async with pool.acquire() as conn:
        with gzip.open(akas_path, "rt", encoding="utf-8", errors="replace") as f:
            # IMDb's TSV exports aren't CSV-quoted — a literal " in a title
            # (common in akas' alternate/foreign titles) makes Python's
            # default QUOTE_MINIMAL csv.reader treat it as an opening quote
            # and swallow everything up to the next matching " (sometimes
            # megabytes later) into one giant "field", which then blows past
            # the default 128KB field_size_limit. QUOTE_NONE treats the tab
            # as the only delimiter, matching how this data is actually
            # structured.
            reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
            next(reader, None)  # header: titleId ordering title region language types attributes isOriginalTitle

            for row in reader:
                stats["akas_rows_scanned"] += 1
                if len(row) < 8:
                    continue

                tconst, ordering, _title, region, _lang, _types, _attrs, is_original = row[:8]

                if tconst != current_tconst:
                    resolve_current(pending_inserts)
                    current_tconst = tconst
                    current_rows = []
                current_rows.append((ordering, region, is_original))

                if len(pending_inserts) >= batch_size:
                    await flush_inserts(conn)
                    logger.info(
                        "Progress: %d akas rows scanned, %d titles matched, %d resolved, %d country rows inserted so far.",
                        stats["akas_rows_scanned"], stats["titles_matched"], stats["titles_resolved"], stats["country_rows_inserted"],
                    )

            resolve_current(pending_inserts)  # flush the final tconst group
            await flush_inserts(conn)

    logger.info("Backfill complete: %s", stats)
    return stats


async def main() -> None:
    parser = argparse.ArgumentParser(description="CineVault OS IMDb Country-of-Origin Backfill")
    parser.add_argument("--akas-file", type=str, default=None,
                         help="Path to an existing title.akas.tsv.gz (skips download if present)")
    parser.add_argument("--data-dir", type=str, default=None,
                         help="Directory to store/read the dataset file (defaults to system temp dir)")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    args = parser.parse_args()

    data_dir = Path(args.data_dir) if args.data_dir else Path(tempfile.gettempdir()) / "cinevault_imdb_datasets"
    data_dir.mkdir(parents=True, exist_ok=True)
    akas_path = Path(args.akas_file) if args.akas_file else data_dir / "title.akas.tsv.gz"

    if not akas_path.exists() or akas_path.stat().st_size == 0:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=30.0, read=600.0, write=30.0, pool=30.0)) as client:
            await download_akas(akas_path, client)
    else:
        logger.info("Using cached dataset file: %s", akas_path)

    pool = await create_db_pool()
    try:
        start_time = time.time()
        stats = await backfill_countries(akas_path, pool, batch_size=args.batch_size)
        elapsed = time.time() - start_time
        logger.info("=== Country backfill finished in %.2fs: %s ===", elapsed, stats)
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
