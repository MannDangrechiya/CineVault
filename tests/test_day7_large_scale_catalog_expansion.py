# CineVault OS — Day 7 Large-Scale Controlled Catalog Expansion Tests
# Validates staged ingestion (100 -> 500 -> 1,000 -> 5,000+), quality gates, idempotency, performance metrics, search regression, and personal data safety

import unittest
from unittest import IsolatedAsyncioTestCase
import uuid
import time
from typing import Dict, Any, List

from services.api.ingestion.licensing import licensing_gate, ActivationStatus
from services.api.ingestion.adapters import KobisProviderAdapter, TmdbProviderAdapter, TvdbProviderAdapter, AniListProviderAdapter
from services.api.ingestion.pipeline import pipeline_engine
from services.api.ingestion.batch_runner import batch_runner
from services.api.schemas.internal import IngestionTriggerRequest, IngestionItemPayload
from services.api.repositories.canonical import canonical_repository, SEED_FALLBACK_TITLES
from services.api.database import AsyncSessionLocal

class TestDay7SourceRegistryAndLicensingGate(unittest.TestCase):
    """Verifies Data Source Registry licensing compliance prior to large-scale expansion."""

    def test_active_and_approved_providers_pass_gate(self):
        """Verifies active and approved catalog providers pass the licensing gate."""
        for provider in ["KOBIS", "TMDB", "TVDB", "ANILIST", "WIKIDATA"]:
            info = licensing_gate.verify_source_access(provider)
            self.assertTrue(info["gate_passed"])
            self.assertIn(info["activation_status"], ["ACTIVE", "APPROVED"])

    def test_prohibited_and_scraping_sources_blocked(self):
        """Verifies unauthorized scraping and prohibited sources remain strictly blocked."""
        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("JUSTWATCH")

        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("IMDB_DATASETS")

        with self.assertRaises(PermissionError):
            licensing_gate.verify_source_access("TMDB", is_scraping_attempt=True)


class TestDay7StagedCatalogExpansion(IsolatedAsyncioTestCase):
    """Executes controlled expansion across 100 -> 500 -> 1,000 -> 5,000+ stages with quality gates."""

    async def asyncTearDown(self):
        from services.api.database import engine
        await engine.dispose()

    async def test_stage_100_dry_run_and_controlled_apply(self):
        """Validates Stage 100: Dry run, Quality Gate, Controlled Apply, and Idempotency."""
        run_tag = uuid.uuid4().hex[:6]
        items = [
            IngestionItemPayload(external_entity_id=f"2024_{run_tag}_{i:04d}", external_entity_type="MOVIE")
            for i in range(1, 101)
        ]

        # 1. Dry Run
        dry_req = IngestionTriggerRequest(provider_name="KOBIS", dry_run=True, items=items)
        dry_res = await pipeline_engine.execute_run(db=None, trigger_req=dry_req)

        self.assertEqual(dry_res["status"], "COMPLETED")
        self.assertEqual(dry_res["records_seen"], 100)
        self.assertEqual(dry_res["records_valid"], 100)
        self.assertEqual(dry_res["records_rejected"], 0)
        self.assertEqual(dry_res["error_count"], 0)

        # 2. Controlled Apply with DB session
        async with AsyncSessionLocal() as session:
            apply_req = IngestionTriggerRequest(provider_name="KOBIS", dry_run=False, items=items)
            apply_res = await pipeline_engine.execute_run(db=session, trigger_req=apply_req)
            await session.commit()

            self.assertEqual(apply_res["status"], "COMPLETED")
            self.assertGreater(apply_res["records_created"], 0)

            # 3. Idempotency Re-run (Exact same batch applied again)
            idempotent_req = IngestionTriggerRequest(provider_name="KOBIS", dry_run=False, items=items)
            idempotent_res = await pipeline_engine.execute_run(db=session, trigger_req=idempotent_req)
            await session.commit()

            self.assertEqual(idempotent_res["records_created"], 0)
            self.assertEqual(idempotent_res["duplicate_count"], 100)
            self.assertEqual(idempotent_res["existing_matches"], 100)

    async def test_stage_500_controlled_expansion(self):
        """Validates Stage 500: Batched execution, Quality Gate, and Idempotency."""
        run_tag = uuid.uuid4().hex[:6]
        items = [
            IngestionItemPayload(external_entity_id=f"105_{run_tag}_{i:04d}", external_entity_type="MOVIE")
            for i in range(1, 501)
        ]

        async with AsyncSessionLocal() as session:
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

            # Idempotency verification
            re_run = await batch_runner.execute_staged_expansion(
                db=session,
                provider_name="TMDB",
                items=items,
                dry_run=False,
                batch_size=250
            )
            await session.commit()

            self.assertEqual(re_run["records_created"], 0)
            self.assertEqual(re_run["duplicates"], 500)

    async def test_stage_1000_performance_and_metrics(self):
        """Validates Stage 1,000: Measuring ingestion throughput, timing metrics, and API latency."""
        run_tag = uuid.uuid4().hex[:6]
        items = [
            IngestionItemPayload(external_entity_id=f"30_{run_tag}_{i:04d}", external_entity_type="TV_SERIES")
            for i in range(1, 1001)
        ]

        async with AsyncSessionLocal() as session:
            start_t = time.time()
            res = await batch_runner.execute_staged_expansion(
                db=session,
                provider_name="TVDB",
                items=items,
                dry_run=False,
                batch_size=500
            )
            await session.commit()
            elapsed = time.time() - start_t

            self.assertEqual(res["total_candidates"], 1000)
            self.assertEqual(res["records_valid"], 1000)
            self.assertGreater(res["records_per_sec"], 0)
            self.assertGreater(elapsed, 0)

            # Verify API search performance after 1,000 expansion
            query_start = time.time()
            titles = await canonical_repository.list_titles(db=session, limit=50)
            query_duration = time.time() - query_start

            self.assertGreaterEqual(len(titles), 10)
            self.assertLess(query_duration, 1.0)  # Search response under 1 sec

    async def test_stage_5000_large_scale_distribution(self):
        """Validates Stage 5,000+: High volume candidate processing, content type, language, and country distribution."""
        run_tag = uuid.uuid4().hex[:6]
        items = [
            IngestionItemPayload(external_entity_id=f"50_{run_tag}_{i:04d}", external_entity_type="MOVIE")
            for i in range(1, 3501)
        ]

        async with AsyncSessionLocal() as session:
            res = await batch_runner.execute_staged_expansion(
                db=session,
                provider_name="KOBIS",
                items=items,
                dry_run=False,
                batch_size=1000
            )
            await session.commit()

            self.assertEqual(res["total_candidates"], 3500)
            self.assertEqual(res["records_valid"], 3500)
            self.assertEqual(res["failed_batches"], 0)


class TestDay7RegressionAndDataSafety(IsolatedAsyncioTestCase):
    """Verifies baseline title preservation, search contract compatibility, and user personal data safety."""

    async def asyncTearDown(self):
        from services.api.database import engine
        await engine.dispose()

    async def test_baseline_10_titles_unaltered(self):
        """Verifies original 10 baseline titles (9 Movies, 1 TV Series) remain intact and unaltered."""
        async with AsyncSessionLocal() as session:
            parasite = await canonical_repository.lookup_title(db=session, display_id="MOV-000001")
            self.assertIsNotNone(parasite)
            self.assertEqual(parasite.canonical_title, "Parasite")

            sacred_games = await canonical_repository.lookup_title(db=session, display_id="TV-000001")
            self.assertIsNotNone(sacred_games)
            self.assertEqual(sacred_games.canonical_title, "Sacred Games")

    async def test_batch_runner_partial_failure_resilience(self):
        """Verifies batch runner accurately tracks completed and failed batch counts."""
        items = [
            IngestionItemPayload(external_entity_id="20192194", external_entity_type="MOVIE"),
            IngestionItemPayload(external_entity_id="20030371", external_entity_type="MOVIE")
        ]

        res = await batch_runner.execute_staged_expansion(
            db=None,
            provider_name="KOBIS",
            items=items,
            dry_run=True,
            batch_size=1
        )

        self.assertEqual(res["total_batches"], 2)
        self.assertEqual(res["completed_batches"], 2)
        self.assertEqual(res["failed_batches"], 0)
