# CineVault OS — Identity Resolver Pipeline Integration Tests (Day 1-7 remediation, Batch 4)
#
# The Day 1-7 audit found that quality/identity_resolution.py's
# resolve_identity() existed and was unit-tested in isolation, but the LIVE
# ingestion pipeline never actually called it — a raw canonical_title.lower()
# dict lookup made every real matching decision instead. These tests prove
# the wiring itself: that a real pipeline_engine.execute_run() call, against
# a real (rollback-isolated) database session, actually invokes
# identity_resolver.resolve_identity, and that the specific bug class this
# caused (duplicate titles across scripts) no longer reproduces end-to-end.

import unittest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.ingestion.pipeline import pipeline_engine
from services.api.quality import identity_resolution
from services.api.schemas.internal import IngestionTriggerRequest, IngestionItemPayload
from services.api.models.canonical import TitleModel


class RollbackIsolatedAsyncTestCase(IsolatedAsyncioTestCase):
    """Same pattern as tests/test_day7_large_scale_catalog_expansion.py —
    see that file for the full rationale. Duplicated here rather than
    imported to keep this file independently runnable/reviewable."""

    async def asyncSetUp(self):
        self._conn = await engine.connect()
        self._outer_txn = await self._conn.begin()
        self.SessionLocal = async_sessionmaker(
            bind=self._conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()


class TestIdentityResolverIsActuallyWiredIntoPipeline(RollbackIsolatedAsyncTestCase):
    async def test_resolve_identity_is_invoked_during_a_real_pipeline_run(self):
        """Proves the wiring, not just the function: spies on
        identity_resolver.resolve_identity (wraps the real implementation)
        and asserts it was actually called while running a real ingestion
        batch through pipeline_engine.execute_run with a live DB session."""
        with patch.object(
            identity_resolution.identity_resolver,
            "resolve_identity",
            wraps=identity_resolution.identity_resolver.resolve_identity,
        ) as spy:
            async with self.SessionLocal() as session:
                run_tag = uuid.uuid4().hex[:6]
                items = [
                    IngestionItemPayload(
                        external_entity_id=f"wiring_{run_tag}_{i:03d}",
                        external_entity_type="MOVIE",
                    )
                    for i in range(1, 6)
                ]
                req = IngestionTriggerRequest(provider_name="TMDB", dry_run=False, items=items)
                result = await pipeline_engine.execute_run(db=session, trigger_req=req)
                await session.commit()

            self.assertEqual(result["status"], "COMPLETED")
            self.assertGreater(
                spy.call_count, 0,
                "identity_resolver.resolve_identity was never called — the pipeline "
                "is still deciding matches without the real identity resolution engine.",
            )

    async def test_cross_script_duplicate_no_longer_reproduces_end_to_end(self):
        """
        Reproduces the exact bug class the audit found live in the DB (two
        "Inception" rows under different UUIDs) — but for a cross-script
        title, through the REAL pipeline entrypoint, not just the pure
        resolve_identity() function. A payload arriving with ONLY the Latin
        romanization ("Gisaengchung" — no Korean text at all) plus the SAME
        production year as an existing "Parasite" / "기생충" (2019) row must
        resolve to that existing title via the phonetic transliteration
        bridge, not create a second one.
        """
        async with self.SessionLocal() as session:
            # Fictitious Korean title (deliberately not a real film, and not
            # the real "Parasite" baseline row already present in the DB —
            # reusing that title/year would create a genuine ambiguous-
            # duplicate scenario and correctly route to MATCH_AMBIGUOUS
            # instead of the single-candidate auto-match this test proves).
            # "테스트영화구조" transliterates via unidecode to exactly
            # "teseuteuyeonghwagujo" (ratio 1.0) — verified before writing
            # this test.
            korean_title = "테스트영화구조"
            romanized_title = "Teseuteuyeonghwagujo"

            baseline_id = uuid.uuid4()
            session.add(TitleModel(
                title_id=baseline_id,
                display_id=f"MOV-WIRING-{uuid.uuid4().hex[:8]}",
                content_type_id="movie",
                canonical_title="CineVault Wiring Test Film",
                original_title=korean_title,
                production_year=2019,
                status_flag="ACTIVE",
            ))
            await session.flush()

            # KOBIS normalize_payload: canonical_title_proposal = movieNmEn or
            # movieNm; original_title = movieNm. Supplying ONLY movieNm = the
            # Latin romanization (no movieNmEn) means BOTH fields end up
            # Latin — no Korean text anywhere in this payload — so a match
            # against the baseline's Korean original_title can only succeed
            # via the phonetic bridge, not a same-script exact/substring
            # match.
            req = IngestionTriggerRequest(
                provider_name="KOBIS",
                dry_run=False,
                items=[IngestionItemPayload(
                    external_entity_id="wiring-phonetic-001",
                    external_entity_type="MOVIE",
                    raw_payload={
                        "movieCd": "wiring-phonetic-001",
                        "movieNm": romanized_title,
                        "prdtYear": "2019",
                    },
                )],
            )
            result = await pipeline_engine.execute_run(db=session, trigger_req=req)
            await session.commit()

            candidate = result["candidate_results"][0]
            self.assertIn(candidate["match_status"], ("AUTO_MATCH", "MATCH_EXACT"),
                          f"Expected the Latin-romanization payload to match the existing "
                          f"Korean-titled row via the phonetic bridge + year corroboration; got {candidate}")
            self.assertEqual(candidate["matched_canonical_title_id"], str(baseline_id))

            # Confirm no second row was created for this fictitious title/year.
            title_count = await session.execute(
                select(TitleModel).where(TitleModel.production_year == 2019, TitleModel.original_title == korean_title)
            )
            self.assertEqual(len(title_count.scalars().all()), 1)


if __name__ == "__main__":
    unittest.main()
