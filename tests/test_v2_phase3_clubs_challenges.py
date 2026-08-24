"""
CineVault OS — Part 2 Phase 3 Integration Tests
Tests Watch Clubs (2.10), Club Activity Feed (2.12), and Monthly Challenges (2.13).
"""
import unittest
import uuid
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient

from services.api.main import app
from services.api.repositories.social import (
    social_repository,
    SEED_CLUBS,
    SEED_CLUB_MEMBERSHIPS,
    SEED_CLUB_ACTIVITIES,
    SEED_CHALLENGES,
    SEED_CHALLENGE_PARTICIPANTS,
)
from services.api.schemas.social import WatchClubCreate, ChallengeCreate


class TestWatchClubsIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for Watch Clubs (2.10)."""

    def setUp(self):
        SEED_CLUBS.clear()
        SEED_CLUB_MEMBERSHIPS.clear()
        SEED_CLUB_ACTIVITIES.clear()
        self.user_id = uuid.uuid4()
        self.friend_id = uuid.uuid4()

    async def test_create_club_and_retrieve_by_slug(self):
        """Creator becomes OWNER and club is retrievable by slug."""
        payload = WatchClubCreate(name="Sci-Fi Sunday Club", description="Weekly sci-fi viewings")
        club = await social_repository.create_watch_club(None, self.user_id, payload)

        self.assertEqual(club.name, "Sci-Fi Sunday Club")
        self.assertEqual(club.member_count, 1)
        self.assertTrue(club.slug.startswith("sci-fi-sunday-club-"))

        detail = await social_repository.get_watch_club(None, club.slug)
        self.assertEqual(detail.club.club_id, club.club_id)
        self.assertEqual(len(detail.members), 1)
        self.assertEqual(detail.members[0].role, "OWNER")

    async def test_join_club_increments_member_count(self):
        """Joining a club adds MEMBER role and increments member_count."""
        payload = WatchClubCreate(name="Horror Nights")
        club = await social_repository.create_watch_club(None, self.user_id, payload)

        membership = await social_repository.join_watch_club(None, club.slug, self.friend_id)
        self.assertEqual(membership.role, "MEMBER")
        self.assertEqual(membership.user_id, self.friend_id)

        detail = await social_repository.get_watch_club(None, club.slug)
        self.assertEqual(detail.club.member_count, 2)
        self.assertEqual(len(detail.members), 2)

    async def test_list_user_clubs(self):
        """Listing clubs returns all clubs a user belongs to."""
        p1 = WatchClubCreate(name="Club Alpha")
        p2 = WatchClubCreate(name="Club Beta")
        await social_repository.create_watch_club(None, self.user_id, p1)
        await social_repository.create_watch_club(None, self.user_id, p2)
        await social_repository.create_watch_club(None, self.friend_id, WatchClubCreate(name="Club Gamma"))

        my_clubs = await social_repository.list_user_clubs(None, self.user_id)
        self.assertEqual(len(my_clubs), 2)
        names = {c.name for c in my_clubs}
        self.assertIn("Club Alpha", names)
        self.assertIn("Club Beta", names)


class TestClubActivityFeedIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for Club Activity Feed (2.12)."""

    def setUp(self):
        SEED_CLUBS.clear()
        SEED_CLUB_MEMBERSHIPS.clear()
        SEED_CLUB_ACTIVITIES.clear()
        self.user_id = uuid.uuid4()

    async def test_post_and_retrieve_activity_feed(self):
        """Activities posted to a club appear in the feed."""
        payload = WatchClubCreate(name="Drama Circle")
        club = await social_repository.create_watch_club(None, self.user_id, payload)

        await social_repository.post_club_activity(
            None, club.club_id, self.user_id, "WATCH",
            metadata={"title": "The Godfather"},
        )
        await social_repository.post_club_activity(
            None, club.club_id, self.user_id, "RATING",
            metadata={"title": "The Godfather", "rating": 9.5},
        )

        feed = await social_repository.get_club_activity_feed(None, club.slug)
        self.assertEqual(len(feed), 2)
        activity_types = {f.activity_type for f in feed}
        self.assertIn("WATCH", activity_types)
        self.assertIn("RATING", activity_types)


class TestMonthlyChallengesIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for Monthly Challenges (2.13)."""

    def setUp(self):
        SEED_CHALLENGES.clear()
        SEED_CHALLENGE_PARTICIPANTS.clear()
        self.user_id = uuid.uuid4()

    async def test_create_challenge_and_join(self):
        """Creating and joining a challenge tracks participation."""
        now = datetime.now(timezone.utc)
        payload = ChallengeCreate(
            title="Watch 5 Sci-Fi Classics",
            description="Complete 5 sci-fi films this month",
            goal_count=5,
            starts_at=now - timedelta(days=1),
            ends_at=now + timedelta(days=30),
        )
        ch = await social_repository.create_challenge(None, payload)
        self.assertEqual(ch.title, "Watch 5 Sci-Fi Classics")
        self.assertEqual(ch.goal_count, 5)

        participant = await social_repository.join_challenge(None, ch.challenge_id, self.user_id)
        self.assertEqual(participant.progress, 0)
        self.assertFalse(participant.completed)

    async def test_challenge_progress_and_completion(self):
        """Incrementing progress triggers completion at goal."""
        now = datetime.now(timezone.utc)
        payload = ChallengeCreate(
            title="Watch 3 Films", goal_count=3,
            starts_at=now - timedelta(days=1), ends_at=now + timedelta(days=30),
        )
        ch = await social_repository.create_challenge(None, payload)
        await social_repository.join_challenge(None, ch.challenge_id, self.user_id)

        # Progress to 2 — not complete yet
        p = await social_repository.update_challenge_progress(None, ch.challenge_id, self.user_id, increment=2)
        self.assertEqual(p.progress, 2)
        self.assertFalse(p.completed)

        # Progress to 3 — completed!
        p = await social_repository.update_challenge_progress(None, ch.challenge_id, self.user_id, increment=1)
        self.assertEqual(p.progress, 3)
        self.assertTrue(p.completed)
        self.assertIsNotNone(p.completed_at)

    async def test_list_active_challenges(self):
        """Only challenges within their active window are returned."""
        now = datetime.now(timezone.utc)
        active = ChallengeCreate(
            title="Active Challenge", goal_count=1,
            starts_at=now - timedelta(days=1), ends_at=now + timedelta(days=10),
        )
        expired = ChallengeCreate(
            title="Expired Challenge", goal_count=1,
            starts_at=now - timedelta(days=30), ends_at=now - timedelta(days=1),
        )
        await social_repository.create_challenge(None, active)
        await social_repository.create_challenge(None, expired)

        results = await social_repository.list_active_challenges(None)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Active Challenge")

    async def test_get_challenge_detail_with_participants(self):
        """Challenge detail includes all participants."""
        now = datetime.now(timezone.utc)
        payload = ChallengeCreate(
            title="Detail Test", goal_count=1,
            starts_at=now - timedelta(days=1), ends_at=now + timedelta(days=10),
        )
        ch = await social_repository.create_challenge(None, payload)
        user2 = uuid.uuid4()
        await social_repository.join_challenge(None, ch.challenge_id, self.user_id)
        await social_repository.join_challenge(None, ch.challenge_id, user2)

        detail = await social_repository.get_challenge_detail(None, ch.challenge_id)
        self.assertEqual(detail.challenge.title, "Detail Test")
        self.assertEqual(len(detail.participants), 2)
        self.assertEqual(detail.challenge.participant_count, 2)


def test_phase3_endpoints_require_auth():
    """All Phase 3 endpoints require authentication."""
    client = TestClient(app)
    assert client.get("/social/clubs").status_code in (401, 403)
    assert client.post("/social/clubs", json={"name": "Test"}).status_code in (401, 403, 422)
    assert client.get("/social/challenges").status_code in (401, 403)
    assert client.post("/social/challenges", json={"title": "T", "goal_count": 1, "starts_at": "2025-01-01T00:00:00Z", "ends_at": "2025-02-01T00:00:00Z"}).status_code in (401, 403, 422)
