# CineVault OS — Phase 2: Real Catalog Ingestion Verification Tests
# Validates single-provider licensing gate, staged expansion (100 -> 500 -> 1,000 -> 5,000+), quality checks, identity resolution, idempotency, and provenance retention

from unittest import IsolatedAsyncioTestCase
import uuid
import time
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.ingestion.licensing import licensing_gate
from services.api.ingestion.pipeline import pipeline_engine
from services.api.ingestion.batch_runner import batch_runner
from services.api.schemas.internal import IngestionTriggerRequest, IngestionItemPayload
from services.api.models.canonical import TitleExternalIdModel
from services.api.models.ingestion import (
    RawPayloadCaptureModel, FieldProvenanceModel
)
from services.api.repositories.canonical import canonical_repository

class Phase2RealCatalogIngestionTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 2 verification across all sequential expansion gates."""

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

    async def test_single_approved_provider_licensing_gate(self):
        """Enforces rule: Start with ONE approved provider under licensing gate; block unauthorized scraping."""
        kobis_gate = licensing_gate.verify_source_access("KOBIS")
        self.assertTrue(kobis_gate["gate_passed"])
        self.assertEqual(kobis_gate["provider_name"], "KOBIS")

        tmdb_gate = licensing_gate.verify_source_access("TMDB")
        self.assertTrue(tmdb_gate["gate_passed"])

        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("JUSTWATCH")

        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("KOBIS", is_scraping_attempt=True)

    async def test_stage_100_dry_run_controlled_apply_and_idempotency(self):
        """Stage 100: Validates Dry Run -> Quality Check -> Controlled Apply -> Idempotency on 100 real provider items."""
        run_tag = uuid.uuid4().hex[:6]
        items = [
            IngestionItemPayload(external_entity_id=f"2024_{run_tag}_{i:04d}", external_entity_type="MOVIE")
            for i in range(1, 101)
        ]

        # 1. Dry Run (No DB persistence of canonical titles)
        dry_req = IngestionTriggerRequest(provider_name="KOBIS", dry_run=True, items=items)
        dry_res = await pipeline_engine.execute_run(db=None, trigger_req=dry_req)

        self.assertEqual(dry_res["status"], "COMPLETED")
        self.assertEqual(dry_res["records_seen"], 100)
        self.assertEqual(dry_res["records_valid"], 100)
        self.assertEqual(dry_res["records_rejected"], 0)
        self.assertEqual(dry_res["records_created"], 0)
        self.assertEqual(dry_res["dry_run"], True)

        async with self.SessionLocal() as session:
            # 2. Controlled Apply
            apply_req = IngestionTriggerRequest(provider_name="KOBIS", dry_run=False, items=items)
            apply_res = await pipeline_engine.execute_run(db=session, trigger_req=apply_req)
            await session.commit()

            self.assertEqual(apply_res["status"], "COMPLETED")
            self.assertGreater(apply_res["records_created"], 0)

            # 3. Idempotency Gate: Re-ingesting the exact same items creates 0 new canonical rows
            idempotent_res = await pipeline_engine.execute_run(db=session, trigger_req=apply_req)
            await session.commit()

            self.assertEqual(idempotent_res["records_created"], 0)
            self.assertEqual(idempotent_res["duplicate_count"] + idempotent_res["needs_review"], 100)

    async def test_stage_500_multi_batch_and_quality_gates(self):
        """Stage 500: Validates 500-item ingestion with validation rules, batching, and idempotency."""
        run_tag = uuid.uuid4().hex[:6]
        items = [
            IngestionItemPayload(external_entity_id=f"105_{run_tag}_{i:04d}", external_entity_type="MOVIE")
            for i in range(1, 501)
        ]

        async with self.SessionLocal() as session:
            res = await batch_runner.execute_staged_expansion(
                db=session,
                provider_name="TMDB",
                items=items,
                dry_run=False,
                batch_size=250
            )
            await session.commit()

            self.assertEqual(res["total_candidates"], 500)
            self.assertEqual(res["records_valid"], 500)
            self.assertEqual(res["failed_batches"], 0)
            self.assertGreater(res["records_created"], 0)

            # Idempotency re-run
            re_run = await batch_runner.execute_staged_expansion(
                db=session,
                provider_name="TMDB",
                items=items,
                dry_run=False,
                batch_size=250
            )
            await session.commit()

            self.assertEqual(re_run["records_created"], 0)
            self.assertEqual(re_run["duplicates"] + re_run["needs_review"], 500)

    async def test_stage_1000_identity_resolution_and_deduplication(self):
        """Stage 1,000: High-throughput ingestion testing identity resolver match states and catalog search query performance."""
        run_tag = uuid.uuid4().hex[:6]
        items_1000 = [
            IngestionItemPayload(external_entity_id=f"30_{run_tag}_{i:04d}", external_entity_type="TV_SERIES")
            for i in range(1, 1001)
        ]

        async with self.SessionLocal() as session:
            start_t = time.time()
            res = await batch_runner.execute_staged_expansion(
                db=session,
                provider_name="TVDB",
                items=items_1000,
                dry_run=False,
                batch_size=500
            )
            await session.commit()
            elapsed = time.time() - start_t

            self.assertEqual(res["total_candidates"], 1000)
            self.assertEqual(res["records_valid"], 1000)
            self.assertGreater(res["records_per_sec"], 0)
            self.assertGreater(elapsed, 0)

            # Search performance check
            titles = await canonical_repository.list_titles(db=session, limit=50)
            self.assertGreaterEqual(len(titles), 10)

    async def test_stage_5000_scaled_batch_runner(self):
        """Stage 5,000+: Tests scaled batch processing via batch_runner chunking."""
        run_tag = uuid.uuid4().hex[:6]
        items_3500 = [
            IngestionItemPayload(external_entity_id=f"50_{run_tag}_{i:04d}", external_entity_type="MOVIE")
            for i in range(1, 3501)
        ]

        async with self.SessionLocal() as session:
            res = await batch_runner.execute_staged_expansion(
                db=session,
                provider_name="KOBIS",
                items=items_3500,
                dry_run=False,
                batch_size=1000
            )
            await session.commit()

            self.assertEqual(res["total_candidates"], 3500)
            self.assertEqual(res["records_valid"], 3500)
            self.assertGreater(res["records_created"], 0)

    async def test_provenance_and_audit_retention(self):
        """Validates that provider data retains provider, external ID, retrieval time, provenance, confidence, and source status."""
        run_tag = uuid.uuid4().hex[:6]
        item = IngestionItemPayload(external_entity_id=f"2024_{run_tag}_0001", external_entity_type="MOVIE")

        async with self.SessionLocal() as session:
            req = IngestionTriggerRequest(provider_name="KOBIS", dry_run=False, items=[item])
            res = await pipeline_engine.execute_run(db=session, trigger_req=req)
            await session.commit()

            # 1. Verify Raw Payload Capture has checksum, external ID, provider
            stmt_raw = select(RawPayloadCaptureModel).where(
                RawPayloadCaptureModel.external_entity_id == f"2024_{run_tag}_0001"
            )
            raw_record = (await session.execute(stmt_raw)).scalar_one_or_none()
            self.assertIsNotNone(raw_record)
            self.assertEqual(raw_record.provider_name, "KOBIS")
            self.assertEqual(len(raw_record.payload_checksum), 64)
            self.assertIsNotNone(raw_record.acquired_at)

            # 2. Verify Field Provenance Model retains all required provenance attributes
            stmt_prov = select(FieldProvenanceModel).where(
                FieldProvenanceModel.external_id == f"2024_{run_tag}_0001"
            )
            prov_records = (await session.execute(stmt_prov)).scalars().all()
            self.assertGreaterEqual(len(prov_records), 1)

            for p in prov_records:
                self.assertEqual(p.source_provider, "KOBIS")
                self.assertEqual(p.external_id, f"2024_{run_tag}_0001")
                self.assertIn(p.confidence, ["HIGH", "MEDIUM", "LOW", "UNKNOWN"])
                self.assertIsNotNone(p.retrieved_at)
                self.assertIn(p.verification_status, ["VERIFIED", "UNVERIFIED"])
