# CineVault OS — Cross-User Personal Data Isolation Integration Test Suite (Batch 7)
# Validates CAT-2 zero-trust boundaries: user data is strictly scoped to token claims.sub (ADR-003, ADR-004)

import json
import time
import uuid
import pytest
from unittest import IsolatedAsyncioTestCase
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient

from services.api.database import engine
from services.api.main import app
from services.api.models.canonical import TitleModel, EditionModel
from services.api.repositories.personal import personal_repository
from services.api.schemas.personal import (
    WatchEventCreate, UserTitleStateUpdate, RatingCreate, NoteCreate, ReviewCreate
)


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


class TestCrossUserIsolation(RollbackIsolatedAsyncTestCase):
    """Integration tests verifying strict cross-user data isolation on all personal data endpoints."""

    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.client = TestClient(app)
        self.user_a_id = "user-isolation-alice-001"
        self.user_b_id = "user-isolation-bob-002"

    async def _create_test_title(self, session: AsyncSession) -> uuid.UUID:
        """Helper to create a canonical title within the active test session."""
        t_id = uuid.uuid4()
        title = TitleModel(
            title_id=t_id,
            display_id=f"MOV-{uuid.uuid4().hex[:6].upper()}",
            content_type_id="movie",
            canonical_title=f"Isolation Test Title {uuid.uuid4().hex[:4]}",
            original_title="Isolation Test Original Title",
            production_year=2024,
            status_flag="ACTIVE"
        )
        ed = EditionModel(
            edition_id=uuid.uuid4(),
            title_id=t_id,
            edition_name="Theatrical Cut",
            is_primary=True,
            runtime_minutes=120
        )
        title.editions.append(ed)
        session.add(title)
        await session.flush()
        return t_id

    async def test_watch_events_isolation_between_users(self):
        """User A's logged watch events must never be visible to User B."""
        async with self.SessionLocal() as session:
            title_id = await self._create_test_title(session)
            now_iso = datetime.now(timezone.utc).isoformat()

            # User A logs a watch event
            event_a = WatchEventCreate(
                title_id=str(title_id),
                watched_at=now_iso,
                progress_percentage=100.0
            )
            created_a = await personal_repository.create_watch_event(
                db=session, user_id=self.user_a_id, body=event_a
            )
            self.assertIsNotNone(created_a.id)

            # User B queries watch events -> must see 0 events
            events_b = await personal_repository.list_watch_events(
                db=session, user_id=self.user_b_id
            )
            self.assertEqual(len(events_b), 0, "User B should see 0 watch events, but saw User A's data!")

            # User A queries watch events -> must see their 1 event
            events_a = await personal_repository.list_watch_events(
                db=session, user_id=self.user_a_id
            )
            self.assertEqual(len(events_a), 1)
            self.assertEqual(events_a[0].id, created_a.id)

    async def test_title_state_isolation_between_users(self):
        """User A marking a title as favorite / watching does not affect User B's state."""
        async with self.SessionLocal() as session:
            title_id = await self._create_test_title(session)

            # User A updates state: favorite=True, status="WATCHING"
            update_a = UserTitleStateUpdate(
                manual_status_override="WATCHING",
                is_favorite=True
            )
            state_a = await personal_repository.update_user_title_state(
                db=session, user_id=self.user_a_id, title_id=str(title_id), body=update_a
            )
            self.assertTrue(state_a.is_favorite)
            self.assertEqual(state_a.manual_status_override, "WATCHING")

            # User B reads title state -> must be uninitialized / default
            state_b = await personal_repository.get_user_title_state(
                db=session, user_id=self.user_b_id, title_id=str(title_id)
            )
            self.assertFalse(state_b.is_favorite, "User B saw User A's favorite flag!")
            self.assertIsNone(state_b.manual_status_override)

            # User B updates their own state: favorite=False, status="COMPLETED"
            update_b = UserTitleStateUpdate(
                manual_status_override="COMPLETED",
                is_favorite=False
            )
            await personal_repository.update_user_title_state(
                db=session, user_id=self.user_b_id, title_id=str(title_id), body=update_b
            )

            # Re-read User A state -> unchanged
            state_a_refreshed = await personal_repository.get_user_title_state(
                db=session, user_id=self.user_a_id, title_id=str(title_id)
            )
            self.assertTrue(state_a_refreshed.is_favorite)
            self.assertEqual(state_a_refreshed.manual_status_override, "WATCHING")

    async def test_ratings_isolation_between_users(self):
        """User A rating a title 10/10 does not leak or overwrite User B's rating."""
        async with self.SessionLocal() as session:
            title_id = await self._create_test_title(session)

            # User A gives rating 10
            rate_a = RatingCreate(title_id=str(title_id), rating_value=10)
            await personal_repository.set_rating(db=session, user_id=self.user_a_id, body=rate_a)

            # User B gives rating 4
            rate_b = RatingCreate(title_id=str(title_id), rating_value=4)
            await personal_repository.set_rating(db=session, user_id=self.user_b_id, body=rate_b)

            # Query ratings for both
            ratings_a = await personal_repository.list_ratings(db=session, user_id=self.user_a_id)
            ratings_b = await personal_repository.list_ratings(db=session, user_id=self.user_b_id)

            self.assertEqual(len(ratings_a), 1)
            self.assertEqual(ratings_a[0].rating_value, 10)

            self.assertEqual(len(ratings_b), 1)
            self.assertEqual(ratings_b[0].rating_value, 4)

    async def test_notes_and_reviews_private_isolation(self):
        """Private personal notes and reviews are strictly scoped to the creator."""
        async with self.SessionLocal() as session:
            title_id = await self._create_test_title(session)

            # User A creates private note
            note_a = NoteCreate(
                title_id=str(title_id),
                note_text="User A Private Confidential Thoughts."
            )
            created_note = await personal_repository.create_note(db=session, user_id=self.user_a_id, body=note_a)
            self.assertIsNotNone(created_note.id)

            # User B lists notes -> must receive 0 notes
            notes_b = await personal_repository.list_notes(db=session, user_id=self.user_b_id)
            self.assertEqual(len(notes_b), 0, "User B leaked User A's private notes!")

            # User A creates review
            review_a = ReviewCreate(
                title_id=str(title_id),
                review_title="User A Review Title",
                review_text="User A Review Summary.",
                is_public=False
            )
            await personal_repository.create_review(db=session, user_id=self.user_a_id, body=review_a)

            # User B lists reviews -> must receive 0 reviews
            reviews_b = await personal_repository.list_reviews(db=session, user_id=self.user_b_id)
            self.assertEqual(len(reviews_b), 0, "User B leaked User A's reviews!")

    async def test_unauthenticated_request_to_me_endpoints_is_rejected(self):
        """Zero-Trust: requests to /v1/me/* without valid JWT credentials must return 401 Unauthorized."""
        dummy_id = str(uuid.uuid4())
        endpoints = [
            "/v1/me/watch-events",
            f"/v1/me/title-states/{dummy_id}",
            "/v1/me/ratings",
            "/v1/me/notes",
            "/v1/me/reviews",
            "/v1/me/conflicts"
        ]
        for ep in endpoints:
            resp = self.client.get(ep)
            self.assertEqual(resp.status_code, 401, f"Endpoint '{ep}' did not enforce 401 for unauthenticated request!")
