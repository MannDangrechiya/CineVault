# CineVault OS — Persistent Data Source Registry Integration Tests (Batch 8, DS-01, ADR-001)
# Validates DB-backed persistent data source registry, dynamic governance, access levels, and licensing gate enforcement

import pytest
from unittest import IsolatedAsyncioTestCase
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.ingestion.licensing import licensing_gate
from services.api.models.ingestion import DataSourceRegistryModel


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


class TestDataSourceRegistryIntegration(RollbackIsolatedAsyncTestCase):
    """Integration test suite for persistent data source registry and licensing gate."""

    async def test_registry_loads_all_seeded_sources_from_db(self):
        """get_source_registry_async loads all 8 baseline providers from the database."""
        async with self.SessionLocal() as session:
            registry = await licensing_gate.get_source_registry_async(db=session)

            self.assertGreaterEqual(len(registry), 8)
            self.assertIn("KOBIS", registry)
            self.assertIn("TVDB", registry)
            self.assertIn("TMDB", registry)
            self.assertIn("ANILIST", registry)
            self.assertIn("WIKIDATA", registry)
            self.assertIn("OMDB", registry)
            self.assertIn("IMDB_SCRAPING", registry)
            self.assertIn("THEPIRATEBAY", registry)

            kobis = registry["KOBIS"]
            self.assertEqual(kobis["authority_role"], "PRIMARY_KOREAN")
            self.assertEqual(kobis["access_status"], "PERMITTED")
            self.assertEqual(kobis["rate_limit_per_min"], 300)
            self.assertTrue(kobis["requires_api_key"])
            self.assertFalse(kobis["scraping_permitted"])

    async def test_licensing_gate_authorization_evaluation(self):
        """evaluate_source_authorization_async correctly allows permitted and blocks prohibited sources."""
        async with self.SessionLocal() as session:
            # 1. Permitted provider -> passes gate
            auth_kobis = await licensing_gate.evaluate_source_authorization_async(
                provider_name="KOBIS", db=session
            )
            self.assertTrue(auth_kobis["gate_passed"])
            self.assertEqual(auth_kobis["authority_role"], "PRIMARY_KOREAN")

            # 2. Prohibited piracy tracker -> PermissionError
            with self.assertRaises(PermissionError) as ctx_tp:
                await licensing_gate.evaluate_source_authorization_async(
                    provider_name="THEPIRATEBAY", db=session
                )
            self.assertIn("blocked (PROHIBITED)", str(ctx_tp.exception))

            # 3. Scraping attempt on prohibited source -> PermissionError
            with self.assertRaises(PermissionError) as ctx_imdb:
                await licensing_gate.evaluate_source_authorization_async(
                    provider_name="IMDB_SCRAPING", is_scraping_attempt=True, db=session
                )
            self.assertIn("strictly prohibited", str(ctx_imdb.exception))

            # 4. Unknown provider -> PermissionError
            with self.assertRaises(PermissionError):
                await licensing_gate.evaluate_source_authorization_async(
                    provider_name="UNKNOWN_RANDOM_SOURCE", db=session
                )

    async def test_dynamic_governance_suspension_blocks_ingestion_immediately(self):
        """Updating provider activation_status in DB to SUSPENDED immediately blocks ingestion at licensing gate."""
        async with self.SessionLocal() as session:
            # 1. Verify TMDB is initially ACTIVE
            auth_before = await licensing_gate.evaluate_source_authorization_async(
                provider_name="TMDB", db=session
            )
            self.assertTrue(auth_before["gate_passed"])

            # 2. Dynamically suspend TMDB in the database
            stmt = (
                update(DataSourceRegistryModel)
                .where(DataSourceRegistryModel.provider_name == "TMDB")
                .values(activation_status="SUSPENDED")
            )
            await session.execute(stmt)
            await session.flush()

            # 3. Licensing gate must immediately block TMDB
            with self.assertRaises(PermissionError) as ctx:
                await licensing_gate.evaluate_source_authorization_async(
                    provider_name="TMDB", db=session
                )
            self.assertIn("activation status is SUSPENDED", str(ctx.exception))

    async def test_dynamic_governance_rate_limit_and_role_update(self):
        """Updating provider rate limits and authority roles in DB is immediately reflected."""
        async with self.SessionLocal() as session:
            stmt = (
                update(DataSourceRegistryModel)
                .where(DataSourceRegistryModel.provider_name == "TVDB")
                .values(rate_limit_per_min=5000, authority_role="OFFICIAL_DISTRIBUTOR")
            )
            await session.execute(stmt)
            await session.flush()

            reg = await licensing_gate.get_source_registry_async(db=session)
            tvdb = reg["TVDB"]
            self.assertEqual(tvdb["rate_limit_per_min"], 5000)
            self.assertEqual(tvdb["authority_role"], "OFFICIAL_DISTRIBUTOR")
