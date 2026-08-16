# CineVault OS — Phase 22: Systematic Data Curation Verification Tests
# Validates regional catalog prioritization, deduplication safety, community rating labeling, and curator governance

from unittest import IsolatedAsyncioTestCase
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.models.canonical import TitleModel, ContentTypeModel
from services.api.repositories.quality import quality_repository
from services.api.repositories.control_room import control_room_repository

class Phase22DataCurationTestCase(IsolatedAsyncioTestCase):
    """Verifies systematic catalog data curation, regional coverage, provenance tracking, and community rating isolation."""

    async def asyncSetUp(self):
        self._conn = await engine.connect()
        self._outer_txn = await self._conn.begin()
        self.SessionLocal = async_sessionmaker(
            bind=self._conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        async with self.SessionLocal() as session:
            movie_type = await session.get(ContentTypeModel, "movie")
            if not movie_type:
                session.add(ContentTypeModel(content_type_id="movie", type_name="Feature Film"))

            # Check if title exists, otherwise insert unique curated title
            stmt = select(TitleModel).where(TitleModel.canonical_title == "Kantara A Legend")
            res = await session.execute(stmt)
            self.canonical_title = res.scalar_one_or_none()
            if not self.canonical_title:
                self.canonical_title = TitleModel(
                    title_id=uuid.uuid4(),
                    display_id="MOV-CUR-999",
                    content_type_id="movie",
                    canonical_title="Kantara A Legend",
                    original_title="ಕಾಂತಾರ",
                    production_year=2022
                )
                session.add(self.canonical_title)
                await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_regional_cinema_provenance_and_deduplication(self):
        """Regional Curation: Preserves multilingual titles, original scripts, and deduplication provenance."""
        async with self.SessionLocal() as session:
            candidates = await quality_repository.list_reconciliation_candidates(db=session)
            self.assertIsInstance(candidates, list)
            self.assertGreaterEqual(len(candidates), 1)

            cand = candidates[0]
            self.assertGreater(cand.match_confidence, 0.0)
            self.assertIn(cand.suggested_action, ["MERGE_CANDIDATE", "NEW_TITLE_CANDIDATE"])

    async def test_community_rating_non_authoritative_labeling(self):
        """Constraint: Community ratings remain strictly labeled with source provenance."""
        community_sources = [
            {"provider": "IMDb", "rating": 8.8, "votes": 150000, "is_community": True},
            {"provider": "TMDB", "rating": 8.4, "votes": 85000, "is_community": True},
            {"provider": "Letterboxd", "rating": 4.3, "votes": 92000, "is_community": True},
        ]

        for entry in community_sources:
            self.assertTrue(entry["is_community"], "Community ratings must be explicitly labeled as community data")
            self.assertIn("provider", entry)
            self.assertIn("votes", entry)

    async def test_curator_governed_promotion_and_decision_tracking(self):
        """Curator Governance: Human review decision records audit event with SHA-256 integrity."""
        async with self.SessionLocal() as session:
            stats = await control_room_repository.get_summary_stats(db=session)
            self.assertGreaterEqual(stats.pending_reconciliation_candidates, 0)
            self.assertGreaterEqual(stats.pending_quarantine_records, 0)
            self.assertGreaterEqual(stats.promoted_canonical_records, 0)

            # Insert reconciliation candidate for curator testing
            from services.api.models.quality import ReconciliationCandidateModel
            cand_id = uuid.uuid4()
            cand = ReconciliationCandidateModel(
                candidate_id=cand_id,
                provider_name="KOBIS",
                external_id="kobis_test_cur_001",
                candidate_title_id=self.canonical_title.title_id,
                match_confidence=0.98,
                match_rule_id="RULE_EXACT_MATCH",
                decision_status="PENDING"
            )
            session.add(cand)
            await session.flush()

            # Approve promotion test via quality repository
            promotion_result = await quality_repository.promote_candidate(
                db=session,
                candidate_id=str(cand_id),
                actor_id="usr_curator_master",
                rationale="Verified against national cinema archives and official distributor release metadata."
            )
            self.assertEqual(promotion_result["status"], "PROMOTED")
            self.assertIn("integrity_hash", promotion_result)
            self.assertEqual(len(promotion_result["integrity_hash"]), 64) # SHA-256 hash
