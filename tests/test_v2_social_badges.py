# CineVault OS — Test Suite for Core Badge System (Part 2 Item 2.5)
# Validates BadgeDefinitionModel, UserBadgeModel, criteria evaluation engine
# (watch volume, streaks, friendship networks, reviews), and API endpoints.

import uuid
from datetime import datetime, date, timezone, timedelta
from fastapi.testclient import TestClient
from unittest import IsolatedAsyncioTestCase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.main import app
from services.api.database import engine
from services.api.models.social import BadgeDefinitionModel, UserBadgeModel, FriendshipModel
from services.api.models.personal import WatchEventModel, UserStreakModel, ReviewModel, UserListModel
from services.api.models.canonical import TitleModel, EditionModel
from services.api.schemas.social import FriendshipStatusEnum
from services.api.repositories.social import social_repository
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


class TestSocialBadgesIntegration(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._conn = await engine.connect()
        self._outer_txn = await self._conn.begin()
        self.SessionLocal = async_sessionmaker(
            bind=self._conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        self.user_id = uuid.uuid4()
        self.title_id = uuid.uuid4()

        async with self.SessionLocal() as session:
            title = TitleModel(
                title_id=self.title_id,
                display_id=f"MOV-BDG-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="movie",
                canonical_title="Badge Test Movie",
                original_title="Badge Test Movie",
                production_year=2024,
            )
            edition = EditionModel(
                edition_id=uuid.uuid4(),
                title_id=self.title_id,
                edition_name="Theatrical",
                runtime_minutes=120,
                is_primary=True,
            )
            session.add(title)
            await session.flush()
            session.add(edition)
            await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_seeded_badges_exist_and_initially_unearned(self):
        """Verifies system seed badges exist and are not earned by a new user."""
        async with self.SessionLocal() as session:
            res = await social_repository.list_user_badges(session, self.user_id)
            self.assertGreaterEqual(len(res.badges), 6)
            self.assertEqual(res.total_earned, 0)
            slugs = {b.slug for b in res.badges}
            self.assertIn("first-watch", slugs)
            self.assertIn("century-club", slugs)
            self.assertIn("seven-day-streak", slugs)
            self.assertIn("inner-circle", slugs)

    async def test_evaluate_first_watch_and_century_badges(self):
        """Verifies logging watch events unlocks watch_count badges upon evaluation."""
        async with self.SessionLocal() as session:
            # 1. Log 1 watch event
            session.add(WatchEventModel(
                watch_event_id=uuid.uuid4(),
                user_id=self.user_id,
                title_id=self.title_id,
                watched_at=datetime.now(timezone.utc),
                is_tombstoned=False,
            ))
            await session.flush()

            # Evaluate
            res = await social_repository.evaluate_user_badges(session, self.user_id)
            badge_map = {b.slug: b for b in res.badges}

            # 'first-watch' must be earned!
            self.assertTrue(badge_map["first-watch"].is_earned)
            self.assertIsNotNone(badge_map["first-watch"].earned_at)
            # 'century-club' must NOT be earned yet
            self.assertFalse(badge_map["century-club"].is_earned)

    async def test_evaluate_streak_and_inner_circle_badges(self):
        """Verifies maintaining a 7-day streak and having 5 friends unlocks respective badges."""
        async with self.SessionLocal() as session:
            # 1. Add 7-day streak
            session.add(UserStreakModel(
                user_id=self.user_id,
                current_streak=7,
                longest_streak=7,
                last_watch_date=date.today(),
            ))

            # 2. Add 5 accepted friends
            for _ in range(5):
                session.add(FriendshipModel(
                    friendship_id=uuid.uuid4(),
                    requester_id=self.user_id,
                    addressee_id=uuid.uuid4(),
                    status=FriendshipStatusEnum.ACCEPTED.value,
                    trust_score=75.0,
                ))

            await session.flush()

            res = await social_repository.evaluate_user_badges(session, self.user_id)
            badge_map = {b.slug: b for b in res.badges}

            self.assertTrue(badge_map["seven-day-streak"].is_earned)
            self.assertTrue(badge_map["inner-circle"].is_earned)


def test_badges_endpoints_authenticated():
    """Verifies GET /social/badges, POST /social/badges/evaluate, and target inspection."""
    user_id = str(uuid.uuid4())
    token = get_test_token(user_id)

    # 1. GET /social/badges
    resp = client.get("/social/badges", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "badges" in data
    assert "total_earned" in data
    assert len(data["badges"]) >= 6

    # 2. POST /social/badges/evaluate
    eval_resp = client.post("/social/badges/evaluate", headers={"Authorization": f"Bearer {token}"})
    assert eval_resp.status_code == 200

    # 3. GET /social/badges/{user_id}
    target_resp = client.get(f"/social/badges/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert target_resp.status_code == 200
