#!/usr/bin/env python3
"""
CineVault OS — High-Speed IMDb Bulk Ingestion Pipeline
Downloads IMDb public datasets (title.basics.tsv.gz, title.ratings.tsv.gz),
filters for high-quality titles (movies & series with >= 500 votes), and
performs high-speed binary bulk ingestion into PostgreSQL using asyncpg.
"""

import argparse
import asyncio
import csv
import gzip
import logging
import os
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
logger = logging.getLogger("cinevault.ingestion.bulk_imdb")

# Public IMDb Dataset Endpoints
IMDB_BASICS_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"
IMDB_RATINGS_URL = "https://datasets.imdbws.com/title.ratings.tsv.gz"

# Allowed IMDb titleType mapping -> canonical content_type_id
TITLE_TYPE_MAP = {
    "movie": "movie",
    "tvSeries": "tv_series",
    "tvMiniSeries": "tv_series",
}

DEFAULT_MIN_VOTES = 500
DEFAULT_BATCH_SIZE = 10000


async def download_file(
    url: str,
    dest_path: Path,
    client: httpx.AsyncClient,
    chunk_size: int = 1024 * 1024,
) -> Path:
    """Streams a file from HTTP/HTTPS to a local destination path."""
    logger.info("Starting download: %s -> %s", url, dest_path)
    start_time = time.time()
    downloaded_bytes = 0

    async with client.stream("GET", url, follow_redirects=True) as response:
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to download {url}: HTTP status {response.status_code}"
            )

        total_bytes = int(response.headers.get("content-length", 0))
        total_mb = f"{total_bytes / (1024 * 1024):.1f} MB" if total_bytes else "unknown size"
        logger.info("Content length for %s: %s", dest_path.name, total_mb)

        with open(dest_path, "wb") as f:
            async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                f.write(chunk)
                downloaded_bytes += len(chunk)
                if total_bytes and downloaded_bytes % (chunk_size * 20) == 0:
                    pct = (downloaded_bytes / total_bytes) * 100
                    logger.info(
                        "Downloading %s: %.1f%% (%d / %d MB)",
                        dest_path.name,
                        pct,
                        downloaded_bytes // (1024 * 1024),
                        total_bytes // (1024 * 1024),
                    )

    elapsed = time.time() - start_time
    mb = downloaded_bytes / (1024 * 1024)
    logger.info(
        "Downloaded %s: %.2f MB in %.1fs (%.2f MB/s)",
        dest_path.name,
        mb,
        elapsed,
        mb / elapsed if elapsed > 0 else 0,
    )
    return dest_path


async def download_imdb_datasets(
    dest_dir: Path,
    client: Optional[httpx.AsyncClient] = None,
) -> Tuple[Path, Path]:
    """Downloads both IMDb basics and ratings datasets in parallel."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    basics_path = dest_dir / "title.basics.tsv.gz"
    ratings_path = dest_dir / "title.ratings.tsv.gz"

    own_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0))
        own_client = True

    try:
        tasks = []
        if not basics_path.exists() or basics_path.stat().st_size == 0:
            tasks.append(download_file(IMDB_BASICS_URL, basics_path, client))
        else:
            logger.info("Found cached %s, skipping download.", basics_path.name)

        if not ratings_path.exists() or ratings_path.stat().st_size == 0:
            tasks.append(download_file(IMDB_RATINGS_URL, ratings_path, client))
        else:
            logger.info("Found cached %s, skipping download.", ratings_path.name)

        if tasks:
            await asyncio.gather(*tasks)
    finally:
        if own_client:
            await client.aclose()

    return basics_path, ratings_path


def parse_qualified_ratings(
    ratings_gz_path: Path,
    min_votes: int = DEFAULT_MIN_VOTES,
) -> Set[str]:
    """
    Parses title.ratings.tsv.gz line-by-line in a memory-efficient manner.
    Returns a set of tconsts matching numVotes >= min_votes.
    """
    logger.info("Parsing IMDb ratings from %s (min_votes=%d)...", ratings_gz_path, min_votes)
    start_time = time.time()
    qualified_tconsts: Set[str] = set()
    total_ratings = 0

    with gzip.open(ratings_gz_path, "rt", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)
        # Expected: tconst, averageRating, numVotes
        for row in reader:
            if len(row) < 3:
                continue
            total_ratings += 1
            tconst = row[0]
            try:
                num_votes = int(row[2])
                if num_votes >= min_votes:
                    qualified_tconsts.add(tconst)
            except (ValueError, IndexError):
                continue

    elapsed = time.time() - start_time
    logger.info(
        "Parsed %d total ratings in %.2fs -> %d titles qualified with >= %d votes.",
        total_ratings,
        elapsed,
        len(qualified_tconsts),
        min_votes,
    )
    return qualified_tconsts


async def create_db_pool() -> asyncpg.Pool:
    """Constructs an asyncpg Connection Pool from application configuration."""
    host = os.getenv("POSTGRES_HOST") or config.postgres_host
    port = int(os.getenv("POSTGRES_PORT") or config.postgres_port)
    user = config.postgres_user
    password = config.postgres_password
    database = config.postgres_db

    logger.info(
        "Connecting to PostgreSQL database '%s' at %s:%d as user '%s'...",
        database,
        host,
        port,
        user,
    )
    return await asyncpg.create_pool(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        min_size=1,
        max_size=10,
        statement_cache_size=0,
        ssl=False,
        timeout=30.0,
    )


async def ensure_taxonomy_and_schemas(conn: asyncpg.Connection) -> None:
    """Ensures required canonical taxonomy content types exist before title insertion."""
    await conn.execute(
        """
        INSERT INTO canonical.content_type (content_type_id, type_name, description)
        VALUES
            ('movie', 'Feature Film', 'Full-length motion picture released for theatrical, streaming, or physical media.'),
            ('tv_series', 'Television Series', 'Episodic television or web broadcast content.'),
            ('short_film', 'Short Film', 'Motion picture with a runtime under 40 minutes.')
        ON CONFLICT (content_type_id) DO NOTHING;
        """
    )


async def process_and_import(
    db_pool: asyncpg.Pool,
    basics_path: Path,
    ratings_path: Path,
    min_votes: int = DEFAULT_MIN_VOTES,
    batch_size: int = DEFAULT_BATCH_SIZE,
    dry_run: bool = False,
) -> Dict[str, int]:
    """
    Extracts, filters, and bulk inserts IMDb datasets into PostgreSQL.
    
    1. Loads filtered tconsts (numVotes >= min_votes) from ratings dataset.
    2. Streams basics dataset row-by-row, filtering for target title types.
    3. Bulk writes records into a temporary staging table via binary copy.
    4. Executes upsert from staging table into canonical.title and external IDs.
    """
    stats = {
        "qualified_ratings": 0,
        "basics_scanned": 0,
        "records_staged": 0,
        "titles_inserted": 0,
        "external_ids_inserted": 0,
    }

    # Step A: Parse qualified ratings
    qualified_tconsts = parse_qualified_ratings(ratings_path, min_votes=min_votes)
    stats["qualified_ratings"] = len(qualified_tconsts)

    if not qualified_tconsts:
        logger.warning("No titles met the filter criteria (>= %d votes). Exiting.", min_votes)
        return stats

    logger.info("Opening database connection for bulk staging...")
    async with db_pool.acquire() as conn:
        await ensure_taxonomy_and_schemas(conn)

        # Create temporary staging table
        await conn.execute(
            """
            CREATE TEMP TABLE IF NOT EXISTS staging_title (
                imdb_id VARCHAR(32) NOT NULL,
                display_id VARCHAR(32) NOT NULL,
                content_type_id VARCHAR(32) NOT NULL,
                canonical_title VARCHAR(512) NOT NULL,
                original_title VARCHAR(512) NOT NULL,
                production_year SMALLINT,
                tagline VARCHAR(512),
                synopsis TEXT,
                status_flag VARCHAR(32) DEFAULT 'ACTIVE'
            );
            """
        )
        # Clear staging table in case of re-use in same session
        await conn.execute("TRUNCATE TABLE staging_title;")

        logger.info("Streaming and filtering basics from %s...", basics_path)
        start_time = time.time()
        batch_records: List[Tuple[str, str, str, str, str, Optional[int], Optional[str], Optional[str], str]] = []
        
        with gzip.open(basics_path, "rt", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader, None)
            # Expected: tconst, titleType, primaryTitle, originalTitle, isAdult, startYear, endYear, runtimeMinutes, genres

            for row in reader:
                stats["basics_scanned"] += 1
                if len(row) < 4:
                    continue

                tconst = row[0]
                if tconst not in qualified_tconsts:
                    continue

                title_type = row[1]
                content_type_id = TITLE_TYPE_MAP.get(title_type)
                if not content_type_id:
                    continue

                primary_title = row[2].strip() if row[2] != r"\N" else f"Title {tconst}"
                orig_title = row[3].strip() if row[3] != r"\N" else primary_title

                # Year parsing & validation against canonical constraint [1888, 2100]
                prod_year: Optional[int] = None
                if len(row) > 5 and row[5] != r"\N":
                    try:
                        parsed_year = int(row[5])
                        if 1888 <= parsed_year <= 2100:
                            prod_year = parsed_year
                    except ValueError:
                        prod_year = None

                # Construct fields
                # Display ID format: IMDB-tt1234567 (deterministic & unique)
                display_id = f"IMDB-{tconst}"
                canonical_title = primary_title[:512]
                original_title = orig_title[:512]
                tagline = None
                synopsis = f"IMDb {title_type} entry ({tconst})."
                status_flag = "ACTIVE"

                record = (
                    tconst,
                    display_id,
                    content_type_id,
                    canonical_title,
                    original_title,
                    prod_year,
                    tagline,
                    synopsis,
                    status_flag,
                )
                batch_records.append(record)

                if len(batch_records) >= batch_size:
                    if not dry_run:
                        await conn.copy_records_to_table(
                            "staging_title",
                            records=batch_records,
                            columns=[
                                "imdb_id",
                                "display_id",
                                "content_type_id",
                                "canonical_title",
                                "original_title",
                                "production_year",
                                "tagline",
                                "synopsis",
                                "status_flag",
                            ],
                        )
                    stats["records_staged"] += len(batch_records)
                    logger.info(
                        "Staged %d records (scanned %d basics rows)...",
                        stats["records_staged"],
                        stats["basics_scanned"],
                    )
                    batch_records = []

            # Flush remaining records
            if batch_records:
                if not dry_run:
                    await conn.copy_records_to_table(
                        "staging_title",
                        records=batch_records,
                        columns=[
                            "imdb_id",
                            "display_id",
                            "content_type_id",
                            "canonical_title",
                            "original_title",
                            "production_year",
                            "tagline",
                            "synopsis",
                            "status_flag",
                        ],
                    )
                stats["records_staged"] += len(batch_records)
                batch_records = []

        elapsed = time.time() - start_time
        logger.info(
            "Finished staging %d records in %.2fs (%.1f records/s).",
            stats["records_staged"],
            elapsed,
            stats["records_staged"] / elapsed if elapsed > 0 else 0,
        )

        if dry_run:
            logger.info("[DRY RUN] Skipping canonical database insertion.")
            return stats

        # Step B: Bulk Upsert into canonical.title
        logger.info("Executing safe upsert into canonical.title from staging_title...")
        upsert_start = time.time()
        
        insert_titles_query = """
        INSERT INTO canonical.title (
            display_id,
            content_type_id,
            canonical_title,
            original_title,
            production_year,
            tagline,
            synopsis,
            status_flag
        )
        SELECT 
            s.display_id,
            s.content_type_id,
            s.canonical_title,
            s.original_title,
            s.production_year,
            s.tagline,
            s.synopsis,
            COALESCE(s.status_flag, 'ACTIVE')
        FROM staging_title s
        ON CONFLICT DO NOTHING;
        """
        title_res = await conn.execute(insert_titles_query)
        # Parse command tag e.g. "INSERT 0 105234"
        try:
            stats["titles_inserted"] = int(title_res.split()[-1])
        except Exception:
            stats["titles_inserted"] = stats["records_staged"]

        logger.info(
            "Inserted titles result: %s in %.2fs",
            title_res,
            time.time() - upsert_start,
        )

        # Step C: Upsert external IDs into canonical.title_external_id
        logger.info("Populating canonical.title_external_id mapping...")
        ext_start = time.time()
        insert_ext_query = """
        INSERT INTO canonical.title_external_id (
            title_id,
            provider_name,
            external_id,
            external_url
        )
        SELECT 
            t.title_id,
            'IMDB',
            s.imdb_id,
            'https://www.imdb.com/title/' || s.imdb_id || '/'
        FROM staging_title s
        JOIN canonical.title t ON t.display_id = s.display_id
        ON CONFLICT DO NOTHING;
        """
        ext_res = await conn.execute(insert_ext_query)
        try:
            stats["external_ids_inserted"] = int(ext_res.split()[-1])
        except Exception:
            pass

        logger.info(
            "External IDs result: %s in %.2fs",
            ext_res,
            time.time() - ext_start,
        )

    return stats


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="CineVault OS High-Speed Bulk IMDb Ingestion Pipeline"
    )
    parser.add_argument(
        "--min-votes",
        type=int,
        default=DEFAULT_MIN_VOTES,
        help=f"Minimum vote threshold for ratings (default: {DEFAULT_MIN_VOTES})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Database copy batch size (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=os.getenv("IMDB_DATA_DIR"),
        help="Directory to store/read IMDb .tsv.gz files (defaults to system temp dir)",
    )
    parser.add_argument(
        "--basics-file",
        type=str,
        default=None,
        help="Path to an existing title.basics.tsv.gz file",
    )
    parser.add_argument(
        "--ratings-file",
        type=str,
        default=None,
        help="Path to an existing title.ratings.tsv.gz file",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading dataset files and expect them in --data-dir",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and stage records without committing changes to the database",
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir) if args.data_dir else Path(tempfile.gettempdir()) / "cinevault_imdb_data"

    if args.basics_file and args.ratings_file:
        basics_path = Path(args.basics_file)
        ratings_path = Path(args.ratings_file)
    elif args.skip_download:
        basics_path = data_dir / "title.basics.tsv.gz"
        ratings_path = data_dir / "title.ratings.tsv.gz"
        if not basics_path.exists() or not ratings_path.exists():
            logger.error(
                "Specified --skip-download but missing dataset files in %s", data_dir
            )
            sys.exit(1)
    else:
        logger.info("Fetching IMDb public datasets to directory: %s", data_dir)
        basics_path, ratings_path = await download_imdb_datasets(data_dir)

    logger.info("Initializing async database pool...")
    try:
        pool = await create_db_pool()
    except Exception as e:
        logger.error("Failed to connect to database: %s", e)
        logger.info("Please ensure PostgreSQL is running.")
        sys.exit(1)

    try:
        total_start = time.time()
        logger.info(
            "=== CineVault OS Bulk IMDb Ingestion Pipeline Started (min_votes=%d) ===",
            args.min_votes,
        )
        stats = await process_and_import(
            db_pool=pool,
            basics_path=basics_path,
            ratings_path=ratings_path,
            min_votes=args.min_votes,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
        )
        total_elapsed = time.time() - total_start
        logger.info("=== Bulk Ingestion Pipeline Completed in %.2fs ===", total_elapsed)
        logger.info("Summary Statistics:")
        logger.info("  • Qualified titles (>= %d votes): %d", args.min_votes, stats["qualified_ratings"])
        logger.info("  • Basics rows scanned:            %d", stats["basics_scanned"])
        logger.info("  • Records staged:                 %d", stats["records_staged"])
        logger.info("  • Titles inserted:                %d", stats["titles_inserted"])
        logger.info("  • External ID mappings:           %d", stats["external_ids_inserted"])
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
