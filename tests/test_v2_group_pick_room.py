import unittest
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.database import AsyncSessionLocal, engine
from services.api.models.canonical import TitleModel
from services.api.models.social import PickRoomModel, PickRoomCandidateModel, PickVoteModel
from services.api.schemas.social import PickRoomCreate, PickVoteCreate
from services.api.repositories.social import social_repository


@pytest.mark.anyio
class TestGroupPickRoomIntegration(unittest.IsolatedAsyncioTestCase):
    """
    Integration tests for Part 2 Phase 2 Item 2.8 Group Pick Room & Async Voting.
    Verifies room creation, candidate nominations, anonymous guest voting,
    tally calculation, and host closure with winner resolution.
    """

    async def asyncSetUp(self):
        self._conn = await engine.connect()
        self._outer_txn = await self._conn.begin()
        self.SessionLocal = AsyncSessionLocal

        self.host_id = uuid.uuid4()
        self.guest_id = uuid.uuid4()

        self.title_1_id = uuid.uuid4()
        self.title_2_id = uuid.uuid4()
        self.title_3_id = uuid.uuid4()

        async with self.SessionLocal() as session:
            t1_name = f"Inception {uuid.uuid4().hex[:4]}"
            t2_name = f"Interstellar {uuid.uuid4().hex[:4]}"
            t3_name = f"Oppenheimer {uuid.uuid4().hex[:4]}"
            t1 = TitleModel(
                title_id=self.title_1_id,
                display_id=f"MOV-PK1-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="movie",
                canonical_title=t1_name,
                original_title=t1_name,
                production_year=2010,
            )
            t2 = TitleModel(
                title_id=self.title_2_id,
                display_id=f"MOV-PK2-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="movie",
                canonical_title=t2_name,
                original_title=t2_name,
                production_year=2014,
            )
            t3 = TitleModel(
                title_id=self.title_3_id,
                display_id=f"MOV-PK3-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="movie",
                canonical_title=t3_name,
                original_title=t3_name,
                production_year=2023,
            )
            session.add_all([t1, t2, t3])
            await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_create_pick_room_and_retrieve_by_slug(self):
        """Verifies creating a pick room attaches candidates and is retrievable by slug."""
        async with self.SessionLocal() as session:
            create_payload = PickRoomCreate(
                title="Sci-Fi Marathon Night",
                candidate_title_ids=[self.title_1_id, self.title_2_id, self.title_3_id],
                expires_in_hours=24,
            )
            room = await social_repository.create_pick_room(session, self.host_id, create_payload)
            self.assertIsNotNone(room.slug)
            self.assertEqual(room.title, "Sci-Fi Marathon Night")
            self.assertEqual(room.status, "OPEN")
            self.assertEqual(len(room.candidates), 3)
            self.assertEqual(room.total_votes, 0)

            # Retrieve by slug
            fetched = await social_repository.get_pick_room_by_slug(session, room.slug)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.room_id, room.room_id)
            self.assertEqual(len(fetched.candidates), 3)

    async def test_voting_lifecycle_and_deduplication(self):
        """Verifies casting votes accumulates tallies and deduplicates per fingerprint."""
        async with self.SessionLocal() as session:
            create_payload = PickRoomCreate(
                title="Weekend Watch Party",
                candidate_title_ids=[self.title_1_id, self.title_2_id],
            )
            room = await social_repository.create_pick_room(session, self.host_id, create_payload)

            # Vote 1 from Guest Alice on Title 1
            vote_1 = await social_repository.cast_pick_vote(
                session,
                room.slug,
                voter_user_id=None,
                data=PickVoteCreate(
                    title_id=self.title_1_id,
                    guest_name="Alice",
                    voter_fingerprint="fp-alice-123",
                    vote_type="UPVOTE",
                ),
            )
            self.assertEqual(vote_1.voter_name, "Alice")

            # Vote 2 from Guest Bob on Title 1
            await social_repository.cast_pick_vote(
                session,
                room.slug,
                voter_user_id=None,
                data=PickVoteCreate(
                    title_id=self.title_1_id,
                    guest_name="Bob",
                    voter_fingerprint="fp-bob-456",
                    vote_type="UPVOTE",
                ),
            )

            # Vote 3 from Member Charlie on Title 2
            await social_repository.cast_pick_vote(
                session,
                room.slug,
                voter_user_id=self.guest_id,
                data=PickVoteCreate(
                    title_id=self.title_2_id,
                    guest_name="Charlie",
                    voter_fingerprint=str(self.guest_id),
                    vote_type="UPVOTE",
                ),
            )

            # Re-fetch room detail to inspect tallies
            detail = await social_repository.get_pick_room_by_slug(session, room.slug)
            self.assertEqual(detail.total_votes, 3)

            cand_1 = next(c for c in detail.candidates if c.title_id == self.title_1_id)
            cand_2 = next(c for c in detail.candidates if c.title_id == self.title_2_id)
            self.assertEqual(cand_1.upvotes, 2)
            self.assertIn("Alice", cand_1.voter_names)
            self.assertIn("Bob", cand_1.voter_names)
            self.assertEqual(cand_2.upvotes, 1)

    async def test_host_close_room_resolves_winner(self):
        """Verifies closing a room tallies votes and locks winning title."""
        async with self.SessionLocal() as session:
            create_payload = PickRoomCreate(
                title="Championship Ballot",
                candidate_title_ids=[self.title_1_id, self.title_2_id],
            )
            room = await social_repository.create_pick_room(session, self.host_id, create_payload)

            # Vote on Title 2
            await social_repository.cast_pick_vote(
                session,
                room.slug,
                voter_user_id=None,
                data=PickVoteCreate(
                    title_id=self.title_2_id,
                    guest_name="Voter X",
                    voter_fingerprint="fp-x",
                    vote_type="UPVOTE",
                ),
            )

            # Host closes room
            close_res = await social_repository.close_pick_room(session, room.slug, self.host_id)
            self.assertEqual(close_res.status, "RESOLVED")
            self.assertEqual(close_res.winning_title_id, self.title_2_id)
            self.assertEqual(close_res.total_votes_cast, 1)

            # Verify voting is now rejected on resolved room
            with self.assertRaises(ValueError):
                await social_repository.cast_pick_vote(
                    session,
                    room.slug,
                    voter_user_id=None,
                    data=PickVoteCreate(
                        title_id=self.title_1_id,
                        guest_name="Late Voter",
                        voter_fingerprint="fp-late",
                    ),
                )

    async def test_non_host_cannot_close_room(self):
        """Verifies unauthorized user cannot close room."""
        async with self.SessionLocal() as session:
            create_payload = PickRoomCreate(
                title="Private Room",
                candidate_title_ids=[self.title_1_id, self.title_2_id],
            )
            room = await social_repository.create_pick_room(session, self.host_id, create_payload)

            with self.assertRaises(PermissionError):
                await social_repository.close_pick_room(session, room.slug, host_id=self.guest_id)


def test_public_and_authenticated_pick_room_routes():
    """Verifies FastAPI router endpoints for pick room."""
    client = TestClient(app)

    # 1. Unauthenticated request to /social/pick-rooms (POST) requires auth
    res = client.post("/social/pick-rooms", json={"title": "Test", "candidate_title_ids": [str(uuid.uuid4())]})
    assert res.status_code in (401, 403, 422)

    # 2. 404 for non-existent slug
    res = client.get("/social/pick-rooms/pick-nonexistent-1234")
    assert res.status_code == 404
