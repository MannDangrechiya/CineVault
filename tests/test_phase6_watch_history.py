# CineVault OS — Phase 6: Watch History Engine Verification Tests
# Validates TV/Movie watch hierarchies, episode progress, rewatch history, idempotency, and canonical resilience

from unittest import IsolatedAsyncioTestCase
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.repositories.personal import personal_repository
from services.api.models.canonical import (
    TitleModel, EditionModel, SeasonModel, EpisodeModel, ContentTypeModel
)
from services.api.models.personal import WatchEventModel, UserTitleStateModel
from services.api.schemas.personal import WatchEventCreate, UserTitleStateUpdate

class Phase6WatchHistoryEngineTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 6 verification for the watch history engine."""

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
            # Seed Content Types
            types = [("movie", "Feature Film"), ("tv_series", "Television Series")]
            for t_id, t_name in types:
                existing = await session.get(ContentTypeModel, t_id)
                if not existing:
                    session.add(ContentTypeModel(content_type_id=t_id, type_name=t_name))
            await session.flush()

            # 1. Seed Movie Hierarchy (Title -> Edition)
            self.movie_id = uuid.uuid4()
            self.movie = TitleModel(
                title_id=self.movie_id,
                display_id="MOV-WATCH-001",
                content_type_id="movie",
                canonical_title="Dune: Part Two",
                original_title="Dune: Part Two",
                production_year=2024
            )
            self.movie_edition = EditionModel(
                edition_id=uuid.uuid4(),
                title_id=self.movie_id,
                edition_name="IMAX Theatrical Cut",
                runtime_minutes=166,
                is_primary=True
            )

            # 2. Seed TV Hierarchy (Series -> Season -> Episode)
            self.tv_id = uuid.uuid4()
            self.tv_series = TitleModel(
                title_id=self.tv_id,
                display_id="TV-WATCH-001",
                content_type_id="tv_series",
                canonical_title="Severance",
                original_title="Severance",
                production_year=2022
            )
            session.add_all([self.movie, self.movie_edition, self.tv_series])
            await session.flush()

            self.season_1 = SeasonModel(
                season_id=uuid.uuid4(),
                title_id=self.tv_id,
                season_number=1,
                season_name="Season 1"
            )
            session.add(self.season_1)
            await session.flush()

            self.ep_1 = EpisodeModel(
                episode_id=uuid.uuid4(),
                season_id=self.season_1.season_id,
                episode_number=1,
                episode_name="Good News About Hell",
                runtime_minutes=57
            )
            self.ep_2 = EpisodeModel(
                episode_id=uuid.uuid4(),
                season_id=self.season_1.season_id,
                episode_number=2,
                episode_name="Half Loop",
                runtime_minutes=53
            )
            session.add_all([self.ep_1, self.ep_2])
            await session.commit()

        self.user_id = str(uuid.uuid4())

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_movie_watch_hierarchy_and_rewatches(self):
        """Movie Hierarchy: title -> (edition) -> watch events (with multiple rewatches, progress, and device metadata)."""
        async with self.SessionLocal() as session:
            movie_id_str = str(self.movie_id)
            ed_id_str = str(self.movie_edition.edition_id)

            # First watch: theatrical screening
            ev1 = await personal_repository.create_watch_event(
                db=session,
                user_id=self.user_id,
                body=WatchEventCreate(
                    title_id=movie_id_str,
                    edition_id=ed_id_str,
                    watched_at="2024-03-01T19:00:00Z",
                    progress_percentage=100.0,
                    device_type="IMAX Theater",
                    notes="Opening night IMAX 70mm screening."
                )
            )
            self.assertEqual(ev1.device_type, "IMAX Theater")
            self.assertEqual(ev1.progress_percentage, 100.0)

            # Second watch: home theater rewatch
            ev2 = await personal_repository.create_watch_event(
                db=session,
                user_id=self.user_id,
                body=WatchEventCreate(
                    title_id=movie_id_str,
                    edition_id=ed_id_str,
                    watched_at="2024-06-15T21:00:00Z",
                    progress_percentage=100.0,
                    device_type="Apple TV 4K",
                    notes="Rewatch in 4K HDR."
                )
            )
            self.assertEqual(ev2.device_type, "Apple TV 4K")

            # Verify 2 events logged in reverse chronological order
            events = await personal_repository.list_watch_events(db=session, user_id=self.user_id)
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0].device_type, "Apple TV 4K")
            self.assertEqual(events[1].device_type, "IMAX Theater")

    async def test_tv_watch_hierarchy_episode_progress(self):
        """TV Hierarchy: series -> season -> episode -> watch events."""
        async with self.SessionLocal() as session:
            tv_id_str = str(self.tv_id)
            s1_id_str = str(self.season_1.season_id)
            ep1_id_str = str(self.ep_1.episode_id)
            ep2_id_str = str(self.ep_2.episode_id)

            # Watch Season 1 Episode 1
            ev_ep1 = await personal_repository.create_watch_event(
                db=session,
                user_id=self.user_id,
                body=WatchEventCreate(
                    title_id=tv_id_str,
                    season_id=s1_id_str,
                    episode_id=ep1_id_str,
                    watched_at="2024-04-01T20:00:00Z",
                    progress_percentage=100.0,
                    device_type="iPad Pro",
                    notes="Pilot episode completed."
                )
            )
            self.assertEqual(ev_ep1.season_id, s1_id_str)
            self.assertEqual(ev_ep1.episode_id, ep1_id_str)

            # Watch Season 1 Episode 2 partially (in progress / paused at 65%)
            ev_ep2 = await personal_repository.create_watch_event(
                db=session,
                user_id=self.user_id,
                body=WatchEventCreate(
                    title_id=tv_id_str,
                    season_id=s1_id_str,
                    episode_id=ep2_id_str,
                    watched_at="2024-04-02T20:30:00Z",
                    progress_percentage=65.0,
                    device_type="iPad Pro",
                    notes="Paused mid-episode."
                )
            )
            self.assertEqual(ev_ep2.progress_percentage, 65.0)

            # Query all user watch events for this series
            events = await personal_repository.list_watch_events(db=session, user_id=self.user_id)
            self.assertEqual(len(events), 2)
            self.assertTrue(any(e.episode_id == ep1_id_str for e in events))
            self.assertTrue(any(e.episode_id == ep2_id_str for e in events))

    async def test_watch_event_idempotency(self):
        """Idempotency Constraint: Submitting identical watch events with the same key produces NO duplicate rows."""
        async with self.SessionLocal() as session:
            movie_id_str = str(self.movie_id)
            idempotency_key = str(uuid.uuid4())

            create_payload = WatchEventCreate(
                title_id=movie_id_str,
                watched_at="2024-05-01T12:00:00Z",
                progress_percentage=100.0,
                device_type="Sony Bravia TV"
            )

            # First submission
            ev1 = await personal_repository.create_watch_event(
                db=session,
                user_id=self.user_id,
                body=create_payload,
                idempotency_key=idempotency_key
            )
            await session.commit()

            # Second duplicate submission with exact same key
            ev2 = await personal_repository.create_watch_event(
                db=session,
                user_id=self.user_id,
                body=create_payload,
                idempotency_key=idempotency_key
            )
            await session.commit()

            self.assertEqual(ev1.id, ev2.id)

            # Query database directly to guarantee count == 1
            stmt = select(WatchEventModel).where(WatchEventModel.user_id == uuid.UUID(self.user_id))
            records = (await session.execute(stmt)).scalars().all()
            self.assertEqual(len(records), 1)

    async def test_history_preservation_across_canonical_updates(self):
        """Constraint: Preserve user watch history when canonical metadata undergoes updates or corrections."""
        async with self.SessionLocal() as session:
            movie_id_str = str(self.movie_id)

            # Log watch event
            await personal_repository.create_watch_event(
                db=session,
                user_id=self.user_id,
                body=WatchEventCreate(
                    title_id=movie_id_str,
                    watched_at="2024-03-05T18:00:00Z",
                    progress_percentage=100.0,
                    device_type="Cinema"
                )
            )
            await session.commit()

            # Mutate canonical title and edition
            self.movie.canonical_title = "Dune: Part Two (Remastered Edition)"
            self.movie.synopsis = "Updated synopsis with new official plot details."
            self.movie_edition.runtime_minutes = 168
            await session.commit()

            # Verify watch event persists unaltered and accurately points to the updated entity
            events = await personal_repository.list_watch_events(db=session, user_id=self.user_id)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].title_id, movie_id_str)
