# CineVault OS — Test Suite for User Streak Tracking (Part 2 Item 2.3)
# Validates UserStreakModel, consecutive daily calculation, same-day deduplication,
# broken streak reset with longest_streak preservation, and API endpoint integration.

import uuid
from datetime import datetime, date, timezone, timedelta
from fastapi.testclient import TestClient
from unittest import IsolatedAsyncioTestCase
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.main import app
from services.api.database import engine
from services.api.models.personal import UserStreakModel, WatchEventModel
from services.api.models.canonical import TitleModel, EditionModel
from services.api.schemas.personal import WatchEventCreate
from services.api.repositories.personal import personal_repository
from services.api.routers.auth import generate_dev_jwt

client = TestClient(app)


def get_test_token(user_id: str) -> str:
    """Generates an authenticated JWT for integration testing."""
    return generate_dev_jwt(
        user_id=user_id,
        email=f"{user_id}@cinevault.test",
        username=f"user_{user_id[-6:]}",
        roles=["authenticated_user"],
    )


class TestUserStreakIntegration(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._conn = await engine.connect()
        self._outer_txn = await self._conn.begin()
        self.SessionLocal = async_sessionmaker(
            bind=self._conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        self.user_id = str(uuid.uuid4())
        self.user_uuid = uuid.UUID(self.user_id)
        self.title_id = str(uuid.uuid4())

        async with self.SessionLocal() as session:
            title = TitleModel(
                title_id=uuid.UUID(self.title_id),
                display_id=f"MOV-STRK-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="movie",
                canonical_title="Streak Test Movie",
                original_title="Streak Test Movie",
                production_year=2024,
            )
            edition = EditionModel(
                edition_id=uuid.uuid4(),
                title_id=uuid.UUID(self.title_id),
                edition_name="Theatrical",
                runtime_minutes=110,
                is_primary=True,
            )
            session.add(title)
            await session.flush()
            session.add(edition)
            await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_streak_initial_creation_and_same_day_dedup(self):
        """Verifies logging first watch creates streak 1, second watch on same day keeps streak 1."""
        async with self.SessionLocal() as session:
            day1 = date(2026, 8, 20)
            s1 = await personal_repository.update_user_streak(session, self.user_uuid, day1)
            self.assertEqual(s1.current_streak, 1)
            self.assertEqual(s1.longest_streak, 1)
            self.assertEqual(s1.last_watch_date, day1)

            # Same day watch
            s2 = await personal_repository.update_user_streak(session, self.user_uuid, day1)
            self.assertEqual(s2.current_streak, 1)
            self.assertEqual(s2.longest_streak, 1)

    async def test_streak_consecutive_days_progression(self):
        """Verifies consecutive day viewing increments streak and longest streak."""
        async with self.SessionLocal() as session:
            day1 = date(2026, 8, 20)
            day2 = date(2026, 8, 21)
            day3 = date(2026, 8, 22)

            await personal_repository.update_user_streak(session, self.user_uuid, day1)
            await personal_repository.update_user_streak(session, self.user_uuid, day2)
            s3 = await personal_repository.update_user_streak(session, self.user_uuid, day3)

            self.assertEqual(s3.current_streak, 3)
            self.assertEqual(s3.longest_streak, 3)
            self.assertEqual(s3.last_watch_date, day3)

    async def test_streak_break_resets_current_preserves_longest(self):
        """Verifies skipped day resets current streak to 1 while preserving longest streak."""
        async with self.SessionLocal() as session:
            day1 = date(2026, 8, 20)
            day2 = date(2026, 8, 21)
            day3 = date(2026, 8, 22)
            # Skip day4 (2026-08-23)
            day5 = date(2026, 8, 24)

            await personal_repository.update_user_streak(session, self.user_uuid, day1)
            await personal_repository.update_user_streak(session, self.user_uuid, day2)
            await personal_repository.update_user_streak(session, self.user_uuid, day3)

            # Break streak on day 5
            s5 = await personal_repository.update_user_streak(session, self.user_uuid, day5)

            self.assertEqual(s5.current_streak, 1)
            self.assertEqual(s5.longest_streak, 3)
            self.assertEqual(s5.last_watch_date, day5)

    async def test_create_watch_event_updates_streak_automatically(self):
        """Verifies create_watch_event automatically invokes update_user_streak side effect."""
        async with self.SessionLocal() as session:
            payload = WatchEventCreate(
                title_id=self.title_id,
                watched_at=datetime.now(timezone.utc).isoformat(),
                progress_percentage=100.0,
            )
            res = await personal_repository.create_watch_event(session, self.user_id, payload)
            self.assertIsNotNone(res)

            # Check streak table
            stmt = select(UserStreakModel).where(UserStreakModel.user_id == self.user_uuid)
            streak = (await session.execute(stmt)).scalar_one_or_none()
            self.assertIsNotNone(streak)
            self.assertEqual(streak.current_streak, 1)


def test_streak_endpoint_authenticated():
    """Verifies GET /v1/personal/streak returns current user streak metrics."""
    user_id = str(uuid.uuid4())
    token = get_test_token(user_id)

    # 1. Without watching anything yet, returns 0 streak
    resp = client.get("/v1/personal/streak", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_streak"] == 0
    assert data["longest_streak"] == 0
    assert "updated_at" in data
