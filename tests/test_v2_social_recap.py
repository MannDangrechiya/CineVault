import unittest
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.database import AsyncSessionLocal, engine
from services.api.models.canonical import TitleModel, GenreModel, TitleGenreModel
from services.api.models.personal import WatchEventModel, UserStreakModel
from services.api.models.social import FriendshipModel
from services.api.schemas.social import FriendshipStatusEnum
from services.api.repositories.social import social_repository


@pytest.mark.anyio
class TestSocialRecapIntegration(unittest.IsolatedAsyncioTestCase):
    """
    Integration tests for Part 2 Phase 2 Item 2.9 Wrapped-Style Recap Card.
    Verifies year/month aggregations, top genres, directors, friend percentile,
    and persona archetype calculations.
    """

    async def asyncSetUp(self):
        self._conn = await engine.connect()
        self._outer_txn = await self._conn.begin()
        self.SessionLocal = AsyncSessionLocal

        self.user_id = uuid.uuid4()
        self.friend_id = uuid.uuid4()

        self.title_1_id = uuid.uuid4()
        self.title_2_id = uuid.uuid4()

        async with self.SessionLocal() as session:
            t1_name = f"Sci-Fi Film {uuid.uuid4().hex[:12]}"
            t2_name = f"Drama Film {uuid.uuid4().hex[:12]}"

            t1 = TitleModel(
                title_id=self.title_1_id,
                display_id=f"MOV-REC1-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="movie",
                canonical_title=t1_name,
                original_title=t1_name,
                production_year=2024,
            )
            t2 = TitleModel(
                title_id=self.title_2_id,
                display_id=f"MOV-REC2-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="movie",
                canonical_title=t2_name,
                original_title=t2_name,
                production_year=2023,
            )
            g_scifi = GenreModel(
                genre_id=f"scifi-{uuid.uuid4().hex[:6]}",
                name="Sci-Fi",
            )
            session.add_all([t1, t2, g_scifi])
            await session.flush()

            session.add(TitleGenreModel(title_id=self.title_1_id, genre_id=g_scifi.genre_id))
            await session.flush()

            # Add watch events for self (2 watches)
            now = datetime.now(timezone.utc)
            session.add(WatchEventModel(
                watch_event_id=uuid.uuid4(),
                user_id=self.user_id,
                title_id=self.title_1_id,
                watched_at=now,
                is_tombstoned=False,
            ))
            session.add(WatchEventModel(
                watch_event_id=uuid.uuid4(),
                user_id=self.user_id,
                title_id=self.title_2_id,
                watched_at=now,
                is_tombstoned=False,
            ))

            # Add watch event for friend (1 watch)
            session.add(WatchEventModel(
                watch_event_id=uuid.uuid4(),
                user_id=self.friend_id,
                title_id=self.title_1_id,
                watched_at=now,
                is_tombstoned=False,
            ))

            # Connect friendship
            session.add(FriendshipModel(
                friendship_id=uuid.uuid4(),
                requester_id=self.user_id,
                addressee_id=self.friend_id,
                status=FriendshipStatusEnum.ACCEPTED.value,
                trust_score=80.0,
                created_at=now,
                updated_at=now,
            ))

            # Add streak
            session.add(UserStreakModel(
                user_id=self.user_id,
                current_streak=5,
                longest_streak=12,
                updated_at=now,
            ))
            await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_get_user_recap_metrics_and_genres(self):
        """Verifies aggregate watch counts, runtime, and top genre calculations."""
        async with self.SessionLocal() as session:
            recap = await social_repository.get_user_recap(
                session, self.user_id, period="all_time"
            )
            self.assertEqual(recap.total_titles_watched, 2)
            self.assertEqual(recap.longest_streak_days, 12)
            self.assertGreater(recap.total_runtime_minutes, 0)
            self.assertEqual(recap.cinema_archetype, "The Sci-Fi Visionary")
            self.assertTrue(len(recap.top_genres) > 0)
            self.assertEqual(recap.top_genres[0].genre, "Sci-Fi")

    async def test_recap_friend_circle_percentile(self):
        """Verifies friend circle percentile gives higher rank when watching more than friends."""
        async with self.SessionLocal() as session:
            recap = await social_repository.get_user_recap(
                session, self.user_id, period="all_time"
            )
            # User watched 2, friend watched 1 -> user is in 100th percentile of circle
            self.assertEqual(recap.circle_percentile, 100.0)


def test_authenticated_recap_endpoint():
    """Verifies /social/recap requires JWT auth."""
    client = TestClient(app)
    res = client.get("/social/recap")
    assert res.status_code in (401, 403)
