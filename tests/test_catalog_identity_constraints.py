# CineVault OS — Catalog Identity Constraint Verification (W2 duplicate audit)
#
# Session 5/6 (2026-08-29) investigated a reported "duplicate catalog rows"
# concern (a "Parasite (2019) appears more than once" example) against the
# real catalog. Finding: there is exactly ONE real "Parasite" (2019) row
# (title_id 10000000-0000-7000-8000-000000000001) -- the earlier "duplicate"
# was an artifact of a broken test helper (querying /v1/titles?q=... with a
# search param that endpoint silently ignores, returning an arbitrary
# same-year title, not a second "Parasite"), not a real data problem.
#
# A broader sweep found 158 (canonical_title, production_year) groups with
# more than one row (e.g. "Beauty and the Beast" 1987 has both a movie and
# an unrelated TV special). Every single one differs by content_type_id
# (movie vs tv_series) and/or has a distinct external_id (a different real
# IMDb tconst) -- these are legitimately distinct real-world works that
# happen to share a title and year, not accidental duplicates. Zero
# external_id values map to more than one title_id anywhere in the catalog.
#
# The database already enforces this via two constraints added in
# V2.2__add_catalog_uniqueness_constraints.sql:
#   - uq_canonical_title_year_type: UNIQUE (canonical_title, production_year,
#     content_type_id) -- a movie and a TV series can share a title+year
#     (different content_type = different real production per ADR-001), but
#     two rows can never collide on all three.
#   - unique_provider_title_mapping: UNIQUE (provider_name, external_id) --
#     the same external ID (e.g. an IMDb tconst) can never be mapped to two
#     different canonical titles.
#
# These tests verify both constraints are live and enforced (not just
# "happens to be true today"), so future ingestion cannot silently
# reintroduce a genuine duplicate. No catalog cleanup/merge was needed --
# see WEB_FEATURE_AUDIT.md "Known gaps" for the full write-up.

import asyncio
import uuid

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from services.api.database import AsyncSessionLocal
from services.api.models.canonical import TitleModel, TitleExternalIdModel


def test_title_year_content_type_uniqueness_is_enforced_by_the_database():
    """Inserting a second row with the same (canonical_title, production_year,
    content_type_id) as an existing row must be rejected by the DB, not just
    application code. Uses a shared, well-known real row (Parasite, 2019,
    movie) as the collision target; the attempted duplicate is never
    committed (flush() alone triggers Postgres's immediate constraint check)."""

    async def _run():
        async with AsyncSessionLocal() as session:
            colliding_row = TitleModel(
                title_id=uuid.uuid4(),
                display_id=f"TEST-DUPE-{uuid.uuid4().hex[:12]}",
                content_type_id="movie",
                canonical_title="Parasite",
                original_title="Gisaengchung",
                production_year=2019,
            )
            session.add(colliding_row)
            raised = None
            try:
                await session.flush()
            except IntegrityError as exc:
                raised = exc
            await session.rollback()
            return raised

    raised = asyncio.run(_run())
    assert raised is not None, "expected an IntegrityError, no duplicate was rejected"
    assert "uq_canonical_title_year_type" in str(raised)


def test_external_id_uniqueness_is_enforced_by_the_database():
    """The same (provider_name, external_id) pair can never be mapped to two
    different title_ids -- verified against a real existing mapping so the
    FK on title_id is satisfiable, without needing to insert a throwaway
    title too."""

    async def _run():
        async with AsyncSessionLocal() as session:
            existing = await session.execute(select(TitleExternalIdModel).limit(1))
            row = existing.scalars().first()
            assert row is not None, "no existing title_external_id rows to test against"

            colliding_mapping = TitleExternalIdModel(
                mapping_id=uuid.uuid4(),
                title_id=row.title_id,
                provider_name=row.provider_name,
                external_id=row.external_id,
            )
            session.add(colliding_mapping)
            raised = None
            try:
                await session.flush()
            except IntegrityError as exc:
                raised = exc
            await session.rollback()
            return raised

    raised = asyncio.run(_run())
    assert raised is not None, "expected an IntegrityError, no duplicate mapping was rejected"
    assert "unique_provider_title_mapping" in str(raised)


def test_no_external_id_currently_maps_to_more_than_one_title():
    """Live data-integrity check (not just a schema check): confirms the
    catalog has zero external IDs mapped to more than one title_id right
    now. Catches a future accidental duplicate even if it somehow bypassed
    the DB constraint (e.g. a schema change that drops it)."""

    async def _run():
        async with AsyncSessionLocal() as session:
            stmt = (
                select(
                    TitleExternalIdModel.provider_name,
                    TitleExternalIdModel.external_id,
                    func.count(func.distinct(TitleExternalIdModel.title_id)).label("title_count"),
                )
                .group_by(TitleExternalIdModel.provider_name, TitleExternalIdModel.external_id)
                .having(func.count(func.distinct(TitleExternalIdModel.title_id)) > 1)
            )
            res = await session.execute(stmt)
            return res.all()

    offenders = asyncio.run(_run())
    assert offenders == [], f"external IDs mapped to more than one title: {offenders}"
