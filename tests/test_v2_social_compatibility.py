# CineVault OS — Test Suite for Head-to-Head Compatibility (Part 2 Item 2.1 & 2.2)
# Validates CompatibilityResponse, pgvector cosine calculation, shared genres/directors,
# friendship access restrictions, and in-memory/DB execution.

import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest import IsolatedAsyncioTestCase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.main import app
from services.api.database import engine
from services.api.models.social import FriendshipModel, UserTasteProfileModel
from services.api.models.personal import WatchEventModel, UserTitleStateModel
from services.api.models.canonical import TitleModel, TitleGenreModel, GenreModel, CreditModel, CreditRoleModel, PersonModel, EditionModel
from services.api.schemas.social import FriendshipStatusEnum, CompatibilityResponse
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


class TestSocialCompatibilityIntegration(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._conn = await engine.connect()
        self._outer_txn = await self._conn.begin()
        self.SessionLocal = async_sessionmaker(
            bind=self._conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        self.user1_id = uuid.uuid4()
        self.user2_id = uuid.uuid4()
        self.stranger_id = uuid.uuid4()

        async with self.SessionLocal() as session:
            # Seed CreditRoleModel and GenreModel if needed
            for r_id, r_name, r_cat in [("DIRECTOR", "Director", "DIRECTING"), ("ACTOR", "Actor", "ACTING")]:
                existing = await session.get(CreditRoleModel, r_id)
                if not existing:
                    session.add(CreditRoleModel(credit_role_id=r_id, role_name=r_name, category=r_cat))
            for g_id, g_name in [("sci_fi", "Sci-Fi"), ("drama", "Drama")]:
                existing_g = await session.get(GenreModel, g_id)
                if not existing_g:
                    session.add(GenreModel(genre_id=g_id, name=g_name))
            await session.flush()

            # Create friendship between user1 and user2
            friendship = FriendshipModel(
                friendship_id=uuid.uuid4(),
                requester_id=self.user1_id,
                addressee_id=self.user2_id,
                status=FriendshipStatusEnum.ACCEPTED.value,
                trust_score=85.0,
            )
            session.add(friendship)

            # Create test title with genres and director
            self.title_id = uuid.uuid4()
            title = TitleModel(
                title_id=self.title_id,
                display_id=f"MOV-TEST-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="movie",
                canonical_title="Compatibility Test Movie",
                original_title="Compatibility Test Movie",
                production_year=2024,
            )
            person = PersonModel(person_id=uuid.uuid4(), canonical_name="Christopher Nolan Test")
            session.add_all([title, person])
            await session.flush()

            edition = EditionModel(
                edition_id=uuid.uuid4(),
                title_id=self.title_id,
                edition_name="Theatrical",
                runtime_minutes=120,
                is_primary=True,
            )
            genre_m = TitleGenreModel(title_id=self.title_id, genre_id="sci_fi")
            credit = CreditModel(credit_id=uuid.uuid4(), title_id=self.title_id, person_id=person.person_id, credit_role_id="DIRECTOR")
            session.add_all([edition, genre_m, credit])
            await session.flush()

            # Both users watched this title
            w1 = WatchEventModel(
                watch_event_id=uuid.uuid4(),
                user_id=self.user1_id,
                title_id=self.title_id,
                edition_id=edition.edition_id,
                watched_at=datetime.now(timezone.utc),
            )
            w2 = WatchEventModel(
                watch_event_id=uuid.uuid4(),
                user_id=self.user2_id,
                title_id=self.title_id,
                edition_id=edition.edition_id,
                watched_at=datetime.now(timezone.utc),
            )
            fav1 = UserTitleStateModel(
                user_id=self.user1_id,
                title_id=self.title_id,
                is_favorite=True,
            )
            fav2 = UserTitleStateModel(
                user_id=self.user2_id,
                title_id=self.title_id,
                is_favorite=True,
            )
            session.add_all([w1, w2, fav1, fav2])

            # Add taste vectors: aligned vectors -> high compatibility
            vec1 = [0.1] * 384
            vec2 = [0.1] * 384
            p1 = UserTasteProfileModel(
                user_id=self.user1_id,
                taste_vector=vec1,
                last_computed_at=datetime.now(timezone.utc),
            )
            p2 = UserTasteProfileModel(
                user_id=self.user2_id,
                taste_vector=vec2,
                last_computed_at=datetime.now(timezone.utc),
            )
            session.add_all([p1, p2])
            await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_get_head_to_head_compatibility_calculation(self):
        """Verifies repository calculates compatibility score and extracts shared metadata."""
        async with self.SessionLocal() as session:
            res = await social_repository.get_head_to_head_compatibility(
                db=session,
                user_id=self.user1_id,
                friend_id=self.user2_id,
            )

            self.assertEqual(res.user_id, self.user1_id)
            self.assertEqual(res.friend_id, self.user2_id)
            # Same vectors -> ~100% compatibility
            self.assertGreaterEqual(res.compatibility_score, 99.0)
            self.assertEqual(res.taste_tier, "Oracle")
            self.assertTrue(any("Sci" in g for g in res.shared_genres))
            self.assertIn("Christopher Nolan Test", res.shared_directors)
            self.assertIn("Compatibility Test Movie", res.shared_favorite_titles)

    async def test_compatibility_without_vectors(self):
        """Verifies graceful 0.0 compatibility score when users lack taste vectors."""
        async with self.SessionLocal() as session:
            res = await social_repository.get_head_to_head_compatibility(
                db=session,
                user_id=self.user1_id,
                friend_id=self.stranger_id,
            )
            self.assertEqual(res.compatibility_score, 0.0)
            self.assertEqual(res.taste_tier, "Curious")


def test_compatibility_endpoint_authenticated_and_friendship_check():
    """Verifies API router blocks non-friends and succeeds for friends."""
    u1 = str(uuid.uuid4())
    u2 = str(uuid.uuid4())
    stranger = str(uuid.uuid4())

    token1 = get_test_token(u1)

    # 1. Non-friend should be 403
    resp_blocked = client.get(
        f"/social/friendships/{stranger}/compatibility",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert resp_blocked.status_code == 403

    # 2. In-memory / fallback friendship setup
    # Create friendship via API
    token2 = get_test_token(u2)
    resp_req = client.post(
        "/social/friendships",
        headers={"Authorization": f"Bearer {token1}"},
        json={"addressee_id": u2, "trust_score": 75.0},
    )
    assert resp_req.status_code in (200, 201)
    friendship_id = resp_req.json()["friendship_id"]

    # Accept friendship
    resp_accept = client.patch(
        f"/social/friendships/{friendship_id}",
        headers={"Authorization": f"Bearer {token2}"},
        json={"status": "ACCEPTED"},
    )
    assert resp_accept.status_code == 200

    # 3. Request compatibility
    resp_compat = client.get(
        f"/social/friendships/{u2}/compatibility",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert resp_compat.status_code == 200
    data = resp_compat.json()
    assert "compatibility_score" in data
    assert "taste_tier" in data
    assert "shared_genres" in data
    assert "shared_directors" in data
