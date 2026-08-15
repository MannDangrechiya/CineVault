#!/usr/bin/env python
"""
CineVault OS — Development Fixture Cleanup (Day 1-7 remediation, Batch 3 / Phase 1)

Removes synthetic fixture-generation contamination from the shared
development database, while strictly preserving:

  1. The 10 protected baseline titles (9 movies + 1 TV series) that the
     project's tests and walkthroughs treat as ground truth.
  2. Every row in personal.* (watch history, ratings, notes, reviews,
     title state) — regardless of what canonical title it references.
  3. One additional fixture title (00013417-6b24-43c1-93cb-032d475e48cb,
     "Catalog Tv Series Entry 50090484") that real personal-data rows
     point at. It is fixture-pattern data, but deleting it would either
     violate the ON DELETE RESTRICT FK from personal.watch_event /
     personal.user_title_state, or (if forced) destroy real user
     history. It is left in place until Batch 4's identity-resolution /
     merge-safety work can properly redirect those personal records to
     a correct canonical title.

Deletion criterion (verified complete against the live DB before this
script was written): every canonical.title row that is NOT one of the
11 protected/preserved IDs above has a canonical.title_external_id
mapping — i.e., 100% of non-baseline rows originated from the ingestion
pipeline. There were zero exceptions found.

This also clears the ingestion/quality pipeline history tables
(ingestion_runs, ingestion_items, raw_payload_capture,
quality.candidate_title, quality.field_provenance,
quality.metadata_conflict, and the currently-empty
reconciliation_candidate / quarantine_record / normalized_title_staging
/ ai_proposal_staging) — every row in that history was produced by
mock-mode ingestion runs; none of it is a real audit trail of real
provider contact.

Usage:
    python scripts/cleanup_fixture_data.py            # dry run (default) — reports counts only
    python scripts/cleanup_fixture_data.py --apply     # actually deletes

Idempotent: running this again after a successful cleanup finds nothing
left to delete and reports zero rows affected.

Take a backup first:
    docker exec <postgres-container> pg_dump -U <user> -d cinevault -F c -f /tmp/backup.dump
    docker cp <postgres-container>:/tmp/backup.dump ./backup.dump
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from services.api.database import AsyncSessionLocal  # noqa: E402

# The 10 baseline titles (SEED_FALLBACK_TITLES in repositories/canonical.py)
# plus the one fixture title that real personal data currently references.
PROTECTED_TITLE_IDS = [
    "10000000-0000-7000-8000-000000000001",  # MOV-000001 Parasite
    "10000000-0000-7000-8000-000000000002",  # MOV-000002 Inception
    "018f2e4a-7b31-7000-8000-123456789abe",  # MOV-000003 3 Idiots
    "018f2e4a-7b31-7000-8000-123456789abf",  # MOV-000004 The Dark Knight
    "018f2e4a-7b31-7000-8000-123456789ac0",  # MOV-000005 Inception (duplicate — Batch 4 dedupes this)
    "018f2e4a-7b31-7000-8000-123456789ac1",  # MOV-000006 Dangal
    "018f2e4a-7b31-7000-8000-123456789ac2",  # MOV-000007 RRR
    "018f2e4a-7b31-7000-8000-123456789ac3",  # MOV-000008 The Godfather
    "018f2e4a-7b31-7000-8000-123456789ac4",  # TV-000001 Sacred Games
    "018f2e4a-7b31-7000-8000-123456789ac5",  # MOV-000009 Interstellar
]
PRESERVED_FOR_PERSONAL_DATA = "00013417-6b24-43c1-93cb-032d475e48cb"  # MOV-007993, referenced by real watch_event/user_title_state rows
ALL_PRESERVED_IDS = PROTECTED_TITLE_IDS + [PRESERVED_FOR_PERSONAL_DATA]

# Tables with ON DELETE RESTRICT from canonical.title that could otherwise
# block the delete. Cleared for non-preserved titles before the title delete.
# (personal.* RESTRICT tables are deliberately NOT included here — every
# such row must keep blocking deletion of whatever it references; the only
# row that currently exists there points at PRESERVED_FOR_PERSONAL_DATA,
# which is excluded from deletion anyway.)
RESTRICT_CHILD_TABLES = [
    "canonical.edition",
    "canonical.credit",
    "canonical.award_result",
    "canonical.festival_participation",
    "canonical.franchise_entry",
    "canonical.platform_offer",
    "canonical.season",
    "canonical.title_company",
    "canonical.viewing_order_item",
]

# Ingestion/quality pipeline history — 100% mock-mode noise, safe to clear
# in full regardless of which titles it references.
PIPELINE_HISTORY_TABLES = [
    "quality.candidate_title",
    "quality.field_provenance",
    "quality.metadata_conflict",
    "quality.reconciliation_candidate",
    "quality.quarantine_record",
    "quality.normalized_title_staging",
    "quality.ai_proposal_staging",
    "ingestion.ingestion_items",
    "ingestion.raw_payload_capture",
    "ingestion.ingestion_runs",
]


async def _count(session, sql, **params):
    result = await session.execute(text(sql), params)
    return result.scalar_one()


async def run(apply: bool):
    async with AsyncSessionLocal() as session:
        # All IDs here are hardcoded UUID literals from ALL_PRESERVED_IDS
        # above (not user input), so building the IN-list directly is safe.
        preserved_list_sql = ", ".join(f"'{tid}'" for tid in ALL_PRESERVED_IDS)

        title_count_sql = f"SELECT COUNT(*) FROM canonical.title WHERE title_id NOT IN ({preserved_list_sql})"
        non_preserved_titles = await _count(session, title_count_sql)

        print(f"{'[DRY RUN] ' if not apply else ''}canonical.title rows to delete: {non_preserved_titles}")

        if apply:
            for table in RESTRICT_CHILD_TABLES:
                result = await session.execute(
                    text(f"DELETE FROM {table} WHERE title_id NOT IN ({preserved_list_sql})")
                )
                if result.rowcount:
                    print(f"  deleted {result.rowcount} from {table}")

            result = await session.execute(
                text(f"DELETE FROM canonical.title WHERE title_id NOT IN ({preserved_list_sql})")
            )
            print(f"  deleted {result.rowcount} from canonical.title")

            for table in PIPELINE_HISTORY_TABLES:
                result = await session.execute(text(f"DELETE FROM {table}"))
                if result.rowcount:
                    print(f"  deleted {result.rowcount} from {table}")

            await session.commit()
        else:
            for table in RESTRICT_CHILD_TABLES:
                c = await _count(session, f"SELECT COUNT(*) FROM {table} WHERE title_id NOT IN ({preserved_list_sql})")
                if c:
                    print(f"  [DRY RUN] would delete {c} from {table}")
            for table in PIPELINE_HISTORY_TABLES:
                c = await _count(session, f"SELECT COUNT(*) FROM {table}")
                if c:
                    print(f"  [DRY RUN] would delete {c} from {table}")

        # Verification, always run (safe under both modes)
        baseline_count = await _count(
            session,
            "SELECT COUNT(*) FROM canonical.title WHERE title_id IN ("
            + ", ".join(f"'{tid}'" for tid in PROTECTED_TITLE_IDS) + ")",
        )
        movie_count = await _count(
            session,
            "SELECT COUNT(*) FROM canonical.title WHERE title_id IN ("
            + ", ".join(f"'{tid}'" for tid in PROTECTED_TITLE_IDS)
            + ") AND content_type_id = 'movie'",
        )
        tv_count = await _count(
            session,
            "SELECT COUNT(*) FROM canonical.title WHERE title_id IN ("
            + ", ".join(f"'{tid}'" for tid in PROTECTED_TITLE_IDS)
            + ") AND content_type_id = 'tv_series'",
        )
        watch_events = await _count(session, "SELECT COUNT(*) FROM personal.watch_event")
        title_states = await _count(session, "SELECT COUNT(*) FROM personal.user_title_state")

        print()
        print(f"Baseline titles present: {baseline_count} (expected 10) — {movie_count} movies, {tv_count} TV series")
        print(f"personal.watch_event rows: {watch_events} (must be unchanged)")
        print(f"personal.user_title_state rows: {title_states} (must be unchanged)")

        if baseline_count != 10:
            print("!! BASELINE DAMAGED — investigate before proceeding further.")
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="Actually perform the deletion (default is dry-run).")
    args = parser.parse_args()
    asyncio.run(run(apply=args.apply))
