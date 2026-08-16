# CineVault OS — Integration Tests for Conflict Reconciliation & Merge Safety (Batch 6, ADR-003, ADR-004)
# Verifies real cross-provider field conflict detection, authority weighting, merge safety gates, and identity redirects

from unittest import IsolatedAsyncioTestCase
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.ingestion.pipeline import pipeline_engine
from services.api.quality.reconciliation import reconciliation_engine
from services.api.schemas.internal import IngestionTriggerRequest, IngestionItemPayload
from services.api.models.canonical import TitleModel, EditionModel, TitleExternalIdModel, IdentityRedirectModel
from services.api.models.quality import MetadataConflictModel


class RollbackIsolatedAsyncTestCase(IsolatedAsyncioTestCase):
    """Encapsulates each test method inside an outer connection transaction with savepoints."""

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


class TestConflictReconciliationIntegration(RollbackIsolatedAsyncTestCase):
    """Integration test suite for conflict reconciliation and merge safety."""

    async def test_real_field_conflict_detected_and_recorded_in_db(self):
        """When an incoming payload matches an existing title but has differing runtime/year, a real MetadataConflict is stored."""
        async with self.SessionLocal() as session:
            # 1. Create a baseline title: "Parasite 2019" with runtime 132
            base_id = uuid.uuid4()
            title_orm = TitleModel(
                title_id=base_id,
                display_id=f"MOV-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="movie",
                canonical_title="Unique Conflict Feature",
                original_title="Unique Conflict Original Title",
                production_year=2019,
                status_flag="ACTIVE"
            )
            ed_orm = EditionModel(
                edition_id=uuid.uuid4(),
                title_id=base_id,
                edition_name="Theatrical Cut",
                is_primary=True,
                runtime_minutes=132
            )
            ext_orm = TitleExternalIdModel(
                mapping_id=uuid.uuid4(),
                title_id=base_id,
                provider_name="KOBIS",
                external_id="KOBIS-CONF-001"
            )
            title_orm.editions.append(ed_orm)
            title_orm.external_ids.append(ext_orm)
            session.add(title_orm)
            await session.flush()

            # 2. Ingest TMDb payload with runtime=145 (differs by 13 mins) matching the same title/year
            incoming_payload = {
                "id": 88001,
                "title": "Unique Conflict Feature",
                "original_title": "Unique Conflict Original Title",
                "release_date": "2019-05-30",
                "runtime": 145,
                "origin_country": ["KR"],
                "genres": [{"id": 18, "name": "Drama"}],
                "overview": "A drama with conflicting runtime from TMDB."
            }

            req = IngestionTriggerRequest(
                provider_name="TMDB",
                dry_run=False,
                items=[IngestionItemPayload(
                    external_entity_id="TMDB-88001",
                    external_entity_type="MOVIE",
                    raw_payload=incoming_payload
                )]
            )

            result = await pipeline_engine.execute_run(db=session, trigger_req=req)

            self.assertEqual(result["status"], "COMPLETED")
            self.assertGreaterEqual(result["records_conflicted"], 1)

            # Query quality.metadata_conflict to verify real conflict was persisted
            stmt = select(MetadataConflictModel).where(
                MetadataConflictModel.entity_id == base_id,
                MetadataConflictModel.field_name == "runtime_minutes"
            )
            res = await session.execute(stmt)
            conflicts = res.scalars().all()

            self.assertGreaterEqual(len(conflicts), 1)
            conf = conflicts[0]
            self.assertEqual(conf.candidate_value, "145")
            self.assertEqual(conf.existing_value, "132")
            self.assertEqual(conf.status, "OPEN")
            self.assertEqual(conf.source_provider, "TMDB")

    async def test_domain_authority_conflict_resolution(self):
        """ReconciliationEngine applies domain authority weights (KOBIS > TMDB for Korean film)."""
        observations = [
            {"provider_name": "TMDB", "value": "Parasite (English Title)"},
            {"provider_name": "KOBIS", "value": "기생충"}
        ]
        decision = reconciliation_engine.resolve_attribute_conflict(
            attribute_name="original_title",
            observations=observations,
            domain_type="KOREAN_FILM"
        )
        self.assertEqual(decision["winning_provider"], "KOBIS")
        self.assertEqual(decision["winning_value"], "기생충")
        self.assertEqual(decision["confidence_score"], 1.0)

    async def test_merge_safety_gate_blocks_invalid_merges(self):
        """ADR-003: Merge safety blocks merges with content-type mismatches, year discrepancies (>1y), or attached user data."""
        # 1. Content type mismatch
        source = {"content_type": "movie", "production_year": 2020}
        target = {"content_type": "tv_series", "production_year": 2020}
        is_safe, reasons = reconciliation_engine.verify_merge_safety(source, target)
        self.assertFalse(is_safe)
        self.assertTrue(any("Content type mismatch" in r for r in reasons))

        # 2. Year discrepancy > 1 year
        source = {"content_type": "movie", "production_year": 1982}
        target = {"content_type": "movie", "production_year": 2011}
        is_safe, reasons = reconciliation_engine.verify_merge_safety(source, target)
        self.assertFalse(is_safe)
        self.assertTrue(any("Production year discrepancy" in r for r in reasons))

        # 3. User personal data attached
        source = {"content_type": "movie", "production_year": 2020}
        target = {"content_type": "movie", "production_year": 2020}
        is_safe, reasons = reconciliation_engine.verify_merge_safety(source, target, user_personal_data_attached=True)
        self.assertFalse(is_safe)
        self.assertTrue(any("User personal data" in r for r in reasons))

    async def test_execute_title_merge_creates_identity_redirect_and_tombstone(self):
        """execute_title_merge soft-deletes source title (status_flag='RETIRED') and creates canonical.identity_redirect."""
        async with self.SessionLocal() as session:
            # Create duplicate source and target titles
            source_id = uuid.uuid4()
            target_id = uuid.uuid4()

            s_title = TitleModel(
                title_id=source_id,
                display_id=f"MOV-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="movie",
                canonical_title="Duplicate Source Variant Title",
                original_title="Duplicate Source Variant Title",
                production_year=2022,
                status_flag="ACTIVE"
            )
            t_title = TitleModel(
                title_id=target_id,
                display_id=f"MOV-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="movie",
                canonical_title="Duplicate Canonical Target Title",
                original_title="Duplicate Canonical Target Title",
                production_year=2022,
                status_flag="ACTIVE"
            )
            s_ext = TitleExternalIdModel(
                mapping_id=uuid.uuid4(),
                title_id=source_id,
                provider_name="ANILIST",
                external_id="MERGE-ANI-101"
            )
            s_title.external_ids.append(s_ext)
            session.add_all([s_title, t_title])
            await session.flush()

            # Execute merge
            merge_res = await reconciliation_engine.execute_title_merge(
                db=session,
                source_title_id=source_id,
                target_title_id=target_id,
                merge_reason="TEST_MERGE_DEDUPLICATION"
            )

            self.assertEqual(merge_res["status"], "MERGED")
            self.assertEqual(merge_res["from_id"], str(source_id))
            self.assertEqual(merge_res["to_id"], str(target_id))

            # Verify source title is RETIRED (Tombstone pattern)
            await session.refresh(s_title)
            self.assertEqual(s_title.status_flag, "RETIRED")

            # Verify canonical.identity_redirect row was written
            stmt = select(IdentityRedirectModel).where(
                IdentityRedirectModel.from_id == source_id,
                IdentityRedirectModel.to_id == target_id
            )
            res = await session.execute(stmt)
            redirect = res.scalars().first()
            self.assertIsNotNone(redirect)
            self.assertEqual(redirect.entity_type, "TITLE")
            self.assertEqual(redirect.merge_reason, "TEST_MERGE_DEDUPLICATION")
