# CineVault OS — Test Suite for Social Circle Leaderboard (Part 2 Item 2.4)
# Validates dynamic ranking by viewing volume, time-window filtering (weekly/monthly/all_time),
# isolation of strangers, and API contract integration.

import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest import IsolatedAsyncioTestCase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.main import app
from services.api.database import engine
from services.api.models.social import FriendshipModel
from services.api.models.personal import WatchEventModel
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


class TestSocialLeaderboardIntegration(IsolatedAsyncioTestCase):
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
        self.friend_1 = uuid.uuid4()
        self.friend_2 = uuid.uuid4()
        self.friend_old = uuid.uuid4()
        self.stranger = uuid.uuid4()

        async with self.SessionLocal() as session:
            # 1. Establish friendships
            session.add_all([
                FriendshipModel(
                    friendship_id=uuid.uuid4(),
                    requester_id=self.user_id,
                    addressee_id=self.friend_1,
                    status=FriendshipStatusEnum.ACCEPTED.value,
                    trust_score=80.0,
                ),
                FriendshipModel(
                    friendship_id=uuid.uuid4(),
                    requester_id=self.friend_2,
                    addressee_id=self.user_id,
                    status=FriendshipStatusEnum.ACCEPTED.value,
                    trust_score=60.0,
                ),
                FriendshipModel(
                    friendship_id=uuid.uuid4(),
                    requester_id=self.user_id,
                    addressee_id=self.friend_old,
                    status=FriendshipStatusEnum.ACCEPTED.value,
                    trust_score=50.0,
                ),
                # Stranger is PENDING, not accepted
                FriendshipModel(
                    friendship_id=uuid.uuid4(),
                    requester_id=self.stranger,
                    addressee_id=self.user_id,
                    status=FriendshipStatusEnum.PENDING.value,
                    trust_score=50.0,
                ),
            ])

            # 2. Canonical title & edition for runtime
            title_id = uuid.uuid4()
            title = TitleModel(
                title_id=title_id,
                display_id=f"MOV-LB-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="movie",
                canonical_title="Leaderboard Feature Film",
                original_title="Leaderboard Feature Film",
                production_year=2024,
            )
            edition = EditionModel(
                edition_id=uuid.uuid4(),
                title_id=title_id,
                edition_name="Theatrical",
                runtime_minutes=120,
                is_primary=True,
            )
            session.add(title)
            await session.flush()
            session.add(edition)
            await session.flush()

            now = datetime.now(timezone.utc)

            # 3. Create watch events
            # Caller: 2 watches 2 days ago
            for _ in range(2):
                session.add(WatchEventModel(
                    watch_event_id=uuid.uuid4(),
                    user_id=self.user_id,
                    title_id=title_id,
                    edition_id=edition.edition_id,
                    watched_at=now - timedelta(days=2),
                    is_tombstoned=False,
                ))

            # Friend 1: 5 watches 1 day ago
            for _ in range(5):
                session.add(WatchEventModel(
                    watch_event_id=uuid.uuid4(),
                    user_id=self.friend_1,
                    title_id=title_id,
                    edition_id=edition.edition_id,
                    watched_at=now - timedelta(days=1),
                    is_tombstoned=False,
                ))

            # Friend 2: 1 watch 3 days ago
            session.add(WatchEventModel(
                watch_event_id=uuid.uuid4(),
                user_id=self.friend_2,
                title_id=title_id,
                edition_id=edition.edition_id,
                watched_at=now - timedelta(days=3),
                is_tombstoned=False,
            ))

            # Friend Old: 10 watches 15 days ago (older than weekly, inside monthly)
            for _ in range(10):
                session.add(WatchEventModel(
                    watch_event_id=uuid.uuid4(),
                    user_id=self.friend_old,
                    title_id=title_id,
                    edition_id=edition.edition_id,
                    watched_at=now - timedelta(days=15),
                    is_tombstoned=False,
                ))

            # Stranger: 20 watches 1 day ago (should be excluded!)
            for _ in range(20):
                session.add(WatchEventModel(
                    watch_event_id=uuid.uuid4(),
                    user_id=self.stranger,
                    title_id=title_id,
                    edition_id=edition.edition_id,
                    watched_at=now - timedelta(days=1),
                    is_tombstoned=False,
                ))

            await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_leaderboard_weekly_ranking_and_isolation(self):
        """Verifies weekly leaderboard ranks only accepted circle and filters events older than 7d."""
        async with self.SessionLocal() as session:
            lb = await social_repository.get_friend_leaderboard(
                db=session,
                user_id=self.user_id,
                period="weekly",
            )

            self.assertEqual(lb.period, "weekly")
            self.assertEqual(len(lb.entries), 4)  # user_id + 3 accepted friends

            # Stranger must NOT be present
            entry_user_ids = [e.user_id for e in lb.entries]
            self.assertNotIn(self.stranger, entry_user_ids)

            # Rank 1: friend_1 (5 watches, 10.0 hours)
            self.assertEqual(lb.entries[0].user_id, self.friend_1)
            self.assertEqual(lb.entries[0].watch_count, 5)
            self.assertEqual(lb.entries[0].watch_hours, 10.0)
            self.assertEqual(lb.entries[0].rank, 1)
            self.assertFalse(lb.entries[0].is_current_user)

            # Rank 2: user_id (2 watches, 4.0 hours, current user)
            self.assertEqual(lb.entries[1].user_id, self.user_id)
            self.assertEqual(lb.entries[1].watch_count, 2)
            self.assertEqual(lb.entries[1].watch_hours, 4.0)
            self.assertEqual(lb.entries[1].rank, 2)
            self.assertTrue(lb.entries[1].is_current_user)

            # Rank 3: friend_2 (1 watch, 2.0 hours)
            self.assertEqual(lb.entries[2].user_id, self.friend_2)
            self.assertEqual(lb.entries[2].watch_count, 1)
            self.assertEqual(lb.entries[2].rank, 3)

            # Rank 4: friend_old (0 watches in past 7 days)
            self.assertEqual(lb.entries[3].user_id, self.friend_old)
            self.assertEqual(lb.entries[3].watch_count, 0)
            self.assertEqual(lb.entries[3].rank, 4)

    async def test_leaderboard_monthly_period(self):
        """Verifies monthly leaderboard includes activity from up to 30 days ago."""
        async with self.SessionLocal() as session:
            lb = await social_repository.get_friend_leaderboard(
                db=session,
                user_id=self.user_id,
                period="monthly",
            )

            # In monthly window, friend_old has 10 watches -> Rank 1
            self.assertEqual(lb.entries[0].user_id, self.friend_old)
            self.assertEqual(lb.entries[0].watch_count, 10)
            self.assertEqual(lb.entries[0].watch_hours, 20.0)
            self.assertEqual(lb.entries[0].rank, 1)


def test_leaderboard_endpoint_authenticated():
    """Verifies GET /social/leaderboard endpoint returns 200 with enriched display names."""
    user_id = str(uuid.uuid4())
    token = get_test_token(user_id)

    resp = client.get("/social/leaderboard?period=weekly", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["period"] == "weekly"
    assert "entries" in data
    assert "calculated_at" in data
    assert len(data["entries"]) >= 1
    assert data["entries"][0]["is_current_user"] is True
