# CineVault OS — Test Suite for Viral Invites & Referrals (Part 2 Items 2.6 & 2.7)
# Validates taste preview snapshots, unauthenticated public previews, auto-friendship conversion,
# referral milestone records, and self-accept prevention.

import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest import IsolatedAsyncioTestCase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.main import app
from services.api.database import engine
from services.api.models.social import InviteTokenModel, ReferralModel, FriendshipModel
from services.api.models.personal import WatchEventModel
from services.api.models.canonical import TitleModel, EditionModel, GenreModel, TitleGenreModel
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


class TestSocialInvitesReferralsIntegration(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._conn = await engine.connect()
        self._outer_txn = await self._conn.begin()
        self.SessionLocal = async_sessionmaker(
            bind=self._conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        self.inviter_id = uuid.uuid4()
        self.invitee_id = uuid.uuid4()
        self.title_id = uuid.uuid4()
        self.title_name = f"Invite Movie {uuid.uuid4().hex[:6]}"

        async with self.SessionLocal() as session:
            title = TitleModel(
                title_id=self.title_id,
                display_id=f"MOV-INV-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="movie",
                canonical_title=self.title_name,
                original_title=self.title_name,
                production_year=2024,
            )
            genre = GenreModel(
                genre_id=f"sci-fi-{uuid.uuid4().hex[:6]}",
                name="Sci-Fi",
            )
            session.add(title)
            session.add(genre)
            await session.flush()

            title_genre = TitleGenreModel(
                title_id=self.title_id,
                genre_id=genre.genre_id,
            )
            session.add(title_genre)
            await session.flush()

            # Add watch event for inviter
            session.add(WatchEventModel(
                watch_event_id=uuid.uuid4(),
                user_id=self.inviter_id,
                title_id=self.title_id,
                watched_at=datetime.now(timezone.utc),
                is_tombstoned=False,
            ))
            await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_create_invite_token_and_preview_snapshot(self):
        """Verifies generating an invite creates baked taste snapshot."""
        async with self.SessionLocal() as session:
            res = await social_repository.create_invite_token(session, self.inviter_id)
            self.assertIsNotNone(res.token)
            self.assertEqual(res.inviter_id, self.inviter_id)
            self.assertIn(self.title_name, res.preview_data.get("recent_watched_titles", []))
            self.assertIn("Sci-Fi", res.preview_data.get("top_genres", []))
            self.assertEqual(res.preview_data.get("total_watched_count"), 1)

            # Public preview
            preview = await social_repository.get_invite_preview(session, res.token)
            self.assertIsNotNone(preview)
            self.assertFalse(preview.is_expired)
            self.assertFalse(preview.is_converted)
            self.assertIn(self.title_name, preview.recent_watched_titles)

    async def test_accept_invite_and_referral_creation(self):
        """Verifies accepting token connects friendship and logs referral milestone."""
        async with self.SessionLocal() as session:
            invite = await social_repository.create_invite_token(session, self.inviter_id)

            token_orm, friendship = await social_repository.accept_invite_token(
                session, invite.token, self.invitee_id
            )

            self.assertEqual(token_orm.converted_user_id, self.invitee_id)
            self.assertEqual(friendship.status, FriendshipStatusEnum.ACCEPTED.value)
            self.assertEqual(friendship.trust_score, 75.0)

            # Check referral stats
            stats = await social_repository.get_referral_stats(session, self.inviter_id)
            self.assertEqual(stats.total_invites_sent, 1)
            self.assertEqual(stats.total_conversions, 1)
            self.assertEqual(len(stats.referrals), 1)
            self.assertEqual(stats.referrals[0].invitee_id, self.invitee_id)

    async def test_cannot_accept_own_invite(self):
        """Verifies self-invites are rejected with ValueError."""
        async with self.SessionLocal() as session:
            invite = await social_repository.create_invite_token(session, self.inviter_id)
            with self.assertRaises(ValueError):
                await social_repository.accept_invite_token(session, invite.token, self.inviter_id)


def test_public_preview_and_authenticated_routes():
    """Verifies REST endpoints for invite generation, public preview, accept, and referrals."""
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    token_a = get_test_token(user_a)
    token_b = get_test_token(user_b)

    # 1. User A generates invite
    resp = client.post("/social/invites", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    invite_data = resp.json()
    token = invite_data["token"]
    assert "invite_url" in invite_data

    # 2. Public preview (NO auth header)
    preview_resp = client.get(f"/social/invites/{token}/preview")
    assert preview_resp.status_code == 200
    prev_data = preview_resp.json()
    assert prev_data["token"] == token
    assert prev_data["is_expired"] is False

    # 3. User B accepts invite
    accept_resp = client.post(f"/social/invites/{token}/accept", headers={"Authorization": f"Bearer {token_b}"})
    assert accept_resp.status_code == 200
    f_data = accept_resp.json()
    assert f_data["status"] == "ACCEPTED"

    # 4. User A checks referrals
    ref_resp = client.get("/social/referrals", headers={"Authorization": f"Bearer {token_a}"})
    assert ref_resp.status_code == 200
    refs_data = ref_resp.json()
    assert refs_data["total_conversions"] >= 1
