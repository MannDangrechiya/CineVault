# CineVault OS — Phase 5: Personal User Foundation Verification Tests
# Validates complete personal media layer, status lifecycle, ratings, notes, reviews, watch history, and cross-user privacy isolation

from unittest import IsolatedAsyncioTestCase
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.repositories.personal import personal_repository
from services.api.models.canonical import TitleModel, EditionModel, ContentTypeModel
from services.api.schemas.personal import (
    WatchEventCreate, UserTitleStateUpdate, RatingCreate, NoteCreate, ReviewCreate
)

class Phase5PersonalUserFoundationTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 5 verification for user personal data and privacy isolation."""

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
            # Ensure content types exist
            movie_type = await session.get(ContentTypeModel, "movie")
            if not movie_type:
                session.add(ContentTypeModel(content_type_id="movie", type_name="Feature Film"))
                await session.flush()

            # Seed test Canonical Titles
            self.title_1_id = uuid.uuid4()
            self.title_1 = TitleModel(
                title_id=self.title_1_id,
                display_id="MOV-PERS-001",
                content_type_id="movie",
                canonical_title="Personal Test Feature 1",
                original_title="Personal Test Feature 1",
                production_year=2022
            )
            self.edition_1 = EditionModel(
                edition_id=uuid.uuid4(),
                title_id=self.title_1_id,
                edition_name="Theatrical Cut",
                runtime_minutes=115,
                is_primary=True
            )

            self.title_2_id = uuid.uuid4()
            self.title_2 = TitleModel(
                title_id=self.title_2_id,
                display_id="MOV-PERS-002",
                content_type_id="movie",
                canonical_title="Personal Test Feature 2",
                original_title="Personal Test Feature 2",
                production_year=2023
            )

            session.add_all([self.title_1, self.edition_1, self.title_2])
            await session.commit()

        # Define two distinct test users
        self.user_a_id = str(uuid.uuid4())
        self.user_b_id = str(uuid.uuid4())

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_media_status_lifecycle_and_favorites(self):
        """Validates transitions across watchlist (PLAN_TO_WATCH), WATCHING, COMPLETED, DROPPED, PAUSED, and favorites."""
        async with self.SessionLocal() as session:
            t1_str = str(self.title_1_id)

            # 1. Add to Watchlist (PLAN_TO_WATCH)
            st1 = await personal_repository.update_user_title_state(
                db=session,
                user_id=self.user_a_id,
                title_id=t1_str,
                body=UserTitleStateUpdate(manual_status_override="PLAN_TO_WATCH", is_favorite=False)
            )
            self.assertEqual(st1.manual_status_override, "PLAN_TO_WATCH")
            self.assertFalse(st1.is_favorite)

            # 2. Transition to WATCHING
            st2 = await personal_repository.update_user_title_state(
                db=session,
                user_id=self.user_a_id,
                title_id=t1_str,
                body=UserTitleStateUpdate(manual_status_override="WATCHING")
            )
            self.assertEqual(st2.manual_status_override, "WATCHING")

            # 3. Transition to COMPLETED and favorite
            st3 = await personal_repository.update_user_title_state(
                db=session,
                user_id=self.user_a_id,
                title_id=t1_str,
                body=UserTitleStateUpdate(manual_status_override="COMPLETED", is_favorite=True)
            )
            self.assertEqual(st3.manual_status_override, "COMPLETED")
            self.assertTrue(st3.is_favorite)

            # 4. Fetch state back from DB
            fetched = await personal_repository.get_user_title_state(
                db=session,
                user_id=self.user_a_id,
                title_id=t1_str
            )
            self.assertEqual(fetched.manual_status_override, "COMPLETED")
            self.assertTrue(fetched.is_favorite)

    async def test_ratings_and_notes(self):
        """Validates setting ratings (1-10 scale) and creating private user notes."""
        async with self.SessionLocal() as session:
            t1_str = str(self.title_1_id)

            # 1. Record rating 9
            r_res = await personal_repository.set_rating(
                db=session,
                user_id=self.user_a_id,
                body=RatingCreate(title_id=t1_str, rating_value=9)
            )
            self.assertEqual(r_res.rating_value, 9)

            ratings = await personal_repository.list_ratings(db=session, user_id=self.user_a_id)
            self.assertEqual(len(ratings), 1)
            self.assertEqual(ratings[0].rating_value, 9)

            # 2. Update rating to 10
            r_update = await personal_repository.set_rating(
                db=session,
                user_id=self.user_a_id,
                body=RatingCreate(title_id=t1_str, rating_value=10)
            )
            self.assertEqual(r_update.rating_value, 10)

            # 3. Create private personal note
            note_res = await personal_repository.create_note(
                db=session,
                user_id=self.user_a_id,
                body=NoteCreate(title_id=t1_str, note_text="Rewatched in Dolby Cinema with incredible sound.")
            )
            self.assertEqual(note_res.note_text, "Rewatched in Dolby Cinema with incredible sound.")

            notes = await personal_repository.list_notes(db=session, user_id=self.user_a_id)
            self.assertEqual(len(notes), 1)
            self.assertEqual(notes[0].note_text, "Rewatched in Dolby Cinema with incredible sound.")

    async def test_reviews_creation_and_retrieval(self):
        """Validates creating and listing user title reviews."""
        async with self.SessionLocal() as session:
            t1_str = str(self.title_1_id)

            rev_res = await personal_repository.create_review(
                db=session,
                user_id=self.user_a_id,
                body=ReviewCreate(
                    title_id=t1_str,
                    review_title="Spectacular Visuals",
                    review_text="The cinematography in this piece sets a new benchmark for modern filmmaking.",
                    is_public=True
                )
            )
            self.assertEqual(rev_res.review_title, "Spectacular Visuals")
            self.assertTrue(rev_res.is_public)

            reviews = await personal_repository.list_reviews(db=session, user_id=self.user_a_id)
            self.assertEqual(len(reviews), 1)
            self.assertEqual(reviews[0].review_title, "Spectacular Visuals")

    async def test_watch_history_and_rewatches(self):
        """Validates append-only watch event logging, progress tracking, and multiple rewatches."""
        async with self.SessionLocal() as session:
            t1_str = str(self.title_1_id)
            ed1_str = str(self.edition_1.edition_id)

            # 1. First watch (100% completed)
            ev1 = await personal_repository.create_watch_event(
                db=session,
                user_id=self.user_a_id,
                body=WatchEventCreate(
                    title_id=t1_str,
                    edition_id=ed1_str,
                    watched_at="2023-01-15T20:00:00Z",
                    progress_percentage=100.0
                )
            )
            self.assertEqual(ev1.progress_percentage, 100.0)

            # 2. Rewatch (Second watch session)
            ev2 = await personal_repository.create_watch_event(
                db=session,
                user_id=self.user_a_id,
                body=WatchEventCreate(
                    title_id=t1_str,
                    edition_id=ed1_str,
                    watched_at="2024-02-10T21:30:00Z",
                    progress_percentage=100.0
                )
            )

            # 3. Verify append-only history contains both entries
            events = await personal_repository.list_watch_events(db=session, user_id=self.user_a_id)
            self.assertEqual(len(events), 2)

    async def test_strict_cross_user_isolation(self):
        """NON-NEGOTIABLE CONSTRAINT: User A must never see, leak, or mutate User B's personal data."""
        async with self.SessionLocal() as session:
            t1_str = str(self.title_1_id)
            t2_str = str(self.title_2_id)

            # User A sets state, rating, note, review, and watch event on Title 1
            await personal_repository.update_user_title_state(
                db=session, user_id=self.user_a_id, title_id=t1_str,
                body=UserTitleStateUpdate(manual_status_override="COMPLETED", is_favorite=True)
            )
            await personal_repository.set_rating(
                db=session, user_id=self.user_a_id,
                body=RatingCreate(title_id=t1_str, rating_value=10)
            )
            await personal_repository.create_note(
                db=session, user_id=self.user_a_id,
                body=NoteCreate(title_id=t1_str, note_text="User A secret private note.")
            )
            await personal_repository.create_review(
                db=session, user_id=self.user_a_id,
                body=ReviewCreate(title_id=t1_str, review_title="User A Review", review_text="Great film.", is_public=False)
            )
            await personal_repository.create_watch_event(
                db=session, user_id=self.user_a_id,
                body=WatchEventCreate(title_id=t1_str, watched_at="2024-01-01T00:00:00Z", progress_percentage=100.0)
            )
            await session.commit()

            # User B inspects their personal space
            b_state = await personal_repository.get_user_title_state(db=session, user_id=self.user_b_id, title_id=t1_str)
            self.assertEqual(b_state.derived_status, "UNWATCHED")
            self.assertIsNone(b_state.manual_status_override)
            self.assertFalse(b_state.is_favorite)

            b_ratings = await personal_repository.list_ratings(db=session, user_id=self.user_b_id)
            self.assertEqual(len(b_ratings), 0)

            b_notes = await personal_repository.list_notes(db=session, user_id=self.user_b_id)
            self.assertEqual(len(b_notes), 0)

            b_reviews = await personal_repository.list_reviews(db=session, user_id=self.user_b_id)
            self.assertEqual(len(b_reviews), 0)

            b_events = await personal_repository.list_watch_events(db=session, user_id=self.user_b_id)
            self.assertEqual(len(b_events), 0)

            # User B records their own data on Title 2 with zero effect on User A
            await personal_repository.set_rating(
                db=session, user_id=self.user_b_id,
                body=RatingCreate(title_id=t2_str, rating_value=6)
            )
            await session.commit()

            a_ratings = await personal_repository.list_ratings(db=session, user_id=self.user_a_id)
            self.assertEqual(len(a_ratings), 1)
            self.assertEqual(a_ratings[0].title_id, t1_str)
            self.assertEqual(a_ratings[0].rating_value, 10)
