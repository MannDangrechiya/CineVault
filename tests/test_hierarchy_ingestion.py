# CineVault OS — Integration Tests for Season/Episode Hierarchy Ingestion (ADR-002)
# Verifies that episodic ingestion payloads persist structured SeasonModel and EpisodeModel trees

from unittest import IsolatedAsyncioTestCase
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.ingestion.pipeline import pipeline_engine
from services.api.schemas.internal import IngestionTriggerRequest, IngestionItemPayload
from services.api.models.canonical import TitleModel, SeasonModel, EpisodeModel


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


class TestHierarchyIngestion(RollbackIsolatedAsyncTestCase):
    """Integration test suite for TV Series and Anime Season/Episode hierarchy ingestion."""

    async def test_tv_series_multi_season_ingestion(self):
        """Verify that a TV series payload with explicit seasons & episodes creates the complete hierarchy."""
        async with self.SessionLocal() as session:
            # Staged TVDB-like TV Series with 2 seasons
            custom_payload = {
                "id": 9901,
                "name": "Hierarchy Test Drama",
                "originalName": "계층 테스트 드라마",
                "content_type": "TV_SERIES",
                "year": 2024,
                "runtime_minutes": 55,
                "originalCountry": "kor",
                "genres": [{"name": "Drama"}, {"name": "Mystery"}],
                "overview": "A multi-season drama testing ADR-002 hierarchy persistence.",
                "seasons": [
                    {
                        "season_number": 1,
                        "season_name": "Season 1: The Beginning",
                        "overview": "First season arc.",
                        "episodes": [
                            {"episode_number": 1, "episode_name": "Chapter 1", "air_date": "2024-01-01", "runtime_minutes": 60},
                            {"episode_number": 2, "episode_name": "Chapter 2", "air_date": "2024-01-08", "runtime_minutes": 58}
                        ]
                    },
                    {
                        "season_number": 2,
                        "season_name": "Season 2: The Climax",
                        "overview": "Second season arc.",
                        "episodes": [
                            {"episode_number": 1, "episode_name": "Chapter 3", "air_date": "2024-06-01", "runtime_minutes": 62}
                        ]
                    }
                ]
            }

            req = IngestionTriggerRequest(
                provider_name="TVDB",
                dry_run=False,
                items=[IngestionItemPayload(
                    external_entity_id="TV-SERIES-9901",
                    external_entity_type="TV_SERIES",
                    raw_payload=custom_payload
                )]
            )

            result = await pipeline_engine.execute_run(db=session, trigger_req=req)

            self.assertEqual(result["status"], "COMPLETED")
            self.assertEqual(result["records_created"], 1)

            # Query database to verify Title -> Seasons -> Episodes hierarchy
            stmt = (
                select(TitleModel)
                .options(
                    selectinload(TitleModel.seasons).selectinload(SeasonModel.episodes),
                    selectinload(TitleModel.editions)
                )
                .where(TitleModel.canonical_title == "Hierarchy Test Drama")
            )
            res = await session.execute(stmt)
            title = res.scalars().first()

            self.assertIsNotNone(title)
            self.assertEqual(title.content_type_id, "tv_series")
            self.assertEqual(len(title.seasons), 2)

            # Validate Season 1
            s1 = next(s for s in title.seasons if s.season_number == 1)
            self.assertEqual(s1.season_name, "Season 1: The Beginning")
            self.assertEqual(len(s1.episodes), 2)
            ep1 = next(e for e in s1.episodes if e.episode_number == 1)
            self.assertEqual(ep1.episode_name, "Chapter 1")
            self.assertEqual(ep1.runtime_minutes, 60)

            # Validate Season 2
            s2 = next(s for s in title.seasons if s.season_number == 2)
            self.assertEqual(s2.season_name, "Season 2: The Climax")
            self.assertEqual(len(s2.episodes), 1)
            ep3 = s2.episodes[0]
            self.assertEqual(ep3.episode_name, "Chapter 3")
            self.assertEqual(ep3.runtime_minutes, 62)

    async def test_tv_series_flat_episodes_fallback(self):
        """Verify that a TV series payload with a flat episodes list attaches them to default Season 1."""
        async with self.SessionLocal() as session:
            custom_payload = {
                "id": 9902,
                "name": "Flat Episode Show",
                "originalName": "플랫 에피소드 쇼",
                "content_type": "TV_SERIES",
                "year": 2023,
                "runtime_minutes": 24,
                "originalCountry": "jpn",
                "genres": [{"name": "Animation"}, {"name": "Comedy"}],
                "overview": "An anime series with flat episodes list.",
                "episodes": [
                    {"episode_number": 1, "episode_name": "Pilot Episode", "air_date": "2023-04-01", "runtime_minutes": 24},
                    {"episode_number": 2, "episode_name": "Second Step", "air_date": "2023-04-08", "runtime_minutes": 24}
                ]
            }

            req = IngestionTriggerRequest(
                provider_name="TVDB",
                dry_run=False,
                items=[IngestionItemPayload(
                    external_entity_id="TV-SERIES-9902",
                    external_entity_type="TV_SERIES",
                    raw_payload=custom_payload
                )]
            )

            result = await pipeline_engine.execute_run(db=session, trigger_req=req)

            self.assertEqual(result["status"], "COMPLETED")
            self.assertEqual(result["records_created"], 1)

            stmt = (
                select(TitleModel)
                .options(selectinload(TitleModel.seasons).selectinload(SeasonModel.episodes))
                .where(TitleModel.canonical_title == "Flat Episode Show")
            )
            res = await session.execute(stmt)
            title = res.scalars().first()

            self.assertIsNotNone(title)
            self.assertEqual(len(title.seasons), 1)
            season = title.seasons[0]
            self.assertEqual(season.season_number, 1)
            self.assertEqual(len(season.episodes), 2)
            self.assertEqual(season.episodes[0].episode_name, "Pilot Episode")
            self.assertEqual(season.episodes[1].episode_name, "Second Step")

    async def test_movie_ingestion_has_no_seasons(self):
        """Verify that movie ingestion creates editions without creating seasons/episodes."""
        async with self.SessionLocal() as session:
            custom_payload = {
                "id": 9903,
                "title": "Standalone Feature Film",
                "original_title": "Standalone Feature Film",
                "content_type": "MOVIE",
                "release_date": "2024-05-10",
                "runtime": 115,
                "origin_country": ["US"],
                "genres": [{"id": 28, "name": "Action"}, {"id": 53, "name": "Thriller"}],
                "overview": "A feature length film."
            }

            req = IngestionTriggerRequest(
                provider_name="TMDB",
                dry_run=False,
                items=[IngestionItemPayload(
                    external_entity_id="MOVIE-9903",
                    external_entity_type="MOVIE",
                    raw_payload=custom_payload
                )]
            )

            result = await pipeline_engine.execute_run(db=session, trigger_req=req)

            self.assertEqual(result["status"], "COMPLETED")
            self.assertEqual(result["records_created"], 1)

            stmt = (
                select(TitleModel)
                .options(selectinload(TitleModel.seasons), selectinload(TitleModel.editions))
                .where(TitleModel.canonical_title == "Standalone Feature Film")
            )
            res = await session.execute(stmt)
            title = res.scalars().first()

            self.assertIsNotNone(title)
            self.assertEqual(title.content_type_id, "movie")
            self.assertEqual(len(title.seasons), 0)
            self.assertEqual(len(title.editions), 1)
            self.assertEqual(title.editions[0].edition_name, "Theatrical Cut")
