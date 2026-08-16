# CineVault OS — Phase 10: Dashboard & Personal Analytics Verification Tests
# Validates dynamic derivation of watch metrics, hours, streaks, countries, ratings, and cross-user isolation

from unittest import IsolatedAsyncioTestCase
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.repositories.personal import personal_repository
from services.api.models.canonical import (
    TitleModel, ContentTypeModel, EditionModel, TitleCountryModel, TitleLanguageModel
)
from services.api.schemas.personal import (
    WatchEventCreate, UserTitleStateUpdate, RatingCreate
)

class Phase10DashboardAnalyticsTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 10 verification for dynamic dashboard analytics derived from personal media logs."""

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
            # 1. Ensure Content Types
            types = [("movie", "Feature Film"), ("tv_series", "Television Series"), ("anime", "Anime Series/Film")]
            for t_id, t_name in types:
                existing = await session.get(ContentTypeModel, t_id)
                if not existing:
                    session.add(ContentTypeModel(content_type_id=t_id, type_name=t_name))
            await session.flush()

            # 2. Seed Movie (Parasite, KR, kor, 132 mins)
            self.movie_title = TitleModel(
                title_id=uuid.uuid4(),
                display_id="MOV-DASH-001",
                content_type_id="movie",
                canonical_title="Parasite Dash",
                original_title="기생충",
                production_year=2019
            )
            self.movie_ed = EditionModel(
                edition_id=uuid.uuid4(),
                title_id=self.movie_title.title_id,
                edition_name="Theatrical Cut",
                runtime_minutes=132,
                is_primary=True
            )
            self.movie_country = TitleCountryModel(title_id=self.movie_title.title_id, country_code="KR")
            self.movie_lang = TitleLanguageModel(title_id=self.movie_title.title_id, language_code="kor")

            # 3. Seed Anime (Your Name, JP, jpn, 106 mins)
            self.anime_title = TitleModel(
                title_id=uuid.uuid4(),
                display_id="ANI-DASH-001",
                content_type_id="anime",
                canonical_title="Your Name Dash",
                original_title="君の名は。",
                production_year=2016
            )
            self.anime_ed = EditionModel(
                edition_id=uuid.uuid4(),
                title_id=self.anime_title.title_id,
                edition_name="Theatrical Cut",
                runtime_minutes=106,
                is_primary=True
            )
            self.anime_country = TitleCountryModel(title_id=self.anime_title.title_id, country_code="JP")
            self.anime_lang = TitleLanguageModel(title_id=self.anime_title.title_id, language_code="jpn")

            # 4. Seed TV Series (Severance, US, eng, 60 mins per ep)
            self.tv_title = TitleModel(
                title_id=uuid.uuid4(),
                display_id="TV-DASH-001",
                content_type_id="tv_series",
                canonical_title="Severance Dash",
                original_title="Severance",
                production_year=2022
            )
            self.tv_ed = EditionModel(
                edition_id=uuid.uuid4(),
                title_id=self.tv_title.title_id,
                edition_name="Broadcast Cut",
                runtime_minutes=60,
                is_primary=True
            )
            self.tv_country = TitleCountryModel(title_id=self.tv_title.title_id, country_code="US")
            self.tv_lang = TitleLanguageModel(title_id=self.tv_title.title_id, language_code="eng")

            session.add_all([
                self.movie_title, self.movie_ed, self.movie_country, self.movie_lang,
                self.anime_title, self.anime_ed, self.anime_country, self.anime_lang,
                self.tv_title, self.tv_ed, self.tv_country, self.tv_lang
            ])
            await session.commit()

        self.user_a_id = str(uuid.uuid4())
        self.user_b_id = str(uuid.uuid4())
        self.now = datetime.now(timezone.utc)

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_dynamic_dashboard_metrics_aggregation(self):
        """Validates calculation of all personal media dashboard metrics for User A."""
        async with self.SessionLocal() as session:
            # User A logs 3 titles with states
            t_movie = str(self.movie_title.title_id)
            t_anime = str(self.anime_title.title_id)
            t_tv = str(self.tv_title.title_id)

            # 1. Title states
            await personal_repository.update_user_title_state(
                db=session, user_id=self.user_a_id, title_id=t_movie,
                body=UserTitleStateUpdate(manual_status_override="COMPLETED", is_favorite=True)
            )
            await personal_repository.update_user_title_state(
                db=session, user_id=self.user_a_id, title_id=t_anime,
                body=UserTitleStateUpdate(manual_status_override="COMPLETED", is_favorite=False)
            )
            await personal_repository.update_user_title_state(
                db=session, user_id=self.user_a_id, title_id=t_tv,
                body=UserTitleStateUpdate(manual_status_override="WATCHING", is_favorite=True)
            )

            # 2. Watch Events creating a 2-day watch streak
            # Today: watched Movie
            await personal_repository.create_watch_event(
                db=session, user_id=self.user_a_id,
                body=WatchEventCreate(
                    title_id=t_movie,
                    edition_id=str(self.movie_ed.edition_id),
                    watched_at=self.now.isoformat(),
                    progress_percentage=100.0
                )
            )
            # Yesterday: watched Anime
            yesterday = (self.now - timedelta(days=1)).isoformat()
            await personal_repository.create_watch_event(
                db=session, user_id=self.user_a_id,
                body=WatchEventCreate(
                    title_id=t_anime,
                    edition_id=str(self.anime_ed.edition_id),
                    watched_at=yesterday,
                    progress_percentage=100.0
                )
            )

            # 3. Ratings (Movie rated 10, Anime rated 8 -> Average = 9.0)
            await personal_repository.set_rating(
                db=session, user_id=self.user_a_id,
                body=RatingCreate(title_id=t_movie, rating_value=10)
            )
            await personal_repository.set_rating(
                db=session, user_id=self.user_a_id,
                body=RatingCreate(title_id=t_anime, rating_value=8)
            )
            await session.commit()

            # Retrieve dynamic dashboard metrics
            dash = await personal_repository.get_user_dashboard_metrics(db=session, user_id=self.user_a_id)

            # Assert all derived metrics
            self.assertEqual(dash.total_titles, 3)
            self.assertEqual(dash.completed_count, 2)
            self.assertEqual(dash.watching_count, 1)
            self.assertEqual(dash.favorites_count, 2)
            self.assertEqual(dash.watched_count, 2)
            self.assertEqual(dash.movies_watched, 1)
            self.assertEqual(dash.anime_completed, 1)
            self.assertEqual(dash.series_completed, 0)

            # Total watch hours: (132 + 106) / 60 = 238 / 60 = 3.966 -> 4.0 hours
            self.assertAlmostEqual(dash.total_watch_hours, 4.0, places=1)

            # Countries & Languages explored
            self.assertEqual(set(dash.countries_explored), {"KR", "JP"})
            self.assertEqual(set(dash.languages_explored), {"kor", "jpn"})

            # Watch streak: 2 consecutive days
            self.assertEqual(dash.watch_streak_days, 2)

            # Monthly and annual watch counts
            self.assertEqual(dash.monthly_watch_count, 2)
            self.assertEqual(dash.annual_watch_count, 2)

            # Average personal rating: (10 + 8) / 2 = 9.0
            self.assertEqual(dash.average_personal_rating, 9.0)

    async def test_cross_user_isolation_on_dashboard_metrics(self):
        """Privacy: User B dashboard metrics are zero and unaffected by User A's watch events and ratings."""
        async with self.SessionLocal() as session:
            # User A logs data
            t_movie = str(self.movie_title.title_id)
            await personal_repository.create_watch_event(
                db=session, user_id=self.user_a_id,
                body=WatchEventCreate(title_id=t_movie, watched_at=self.now.isoformat(), progress_percentage=100.0)
            )
            await personal_repository.set_rating(
                db=session, user_id=self.user_a_id,
                body=RatingCreate(title_id=t_movie, rating_value=10)
            )
            await session.commit()

            # User B inspects dashboard
            b_dash = await personal_repository.get_user_dashboard_metrics(db=session, user_id=self.user_b_id)
            self.assertEqual(b_dash.total_titles, 0)
            self.assertEqual(b_dash.watched_count, 0)
            self.assertEqual(b_dash.total_watch_hours, 0.0)
            self.assertEqual(b_dash.watch_streak_days, 0)
            self.assertIsNone(b_dash.average_personal_rating)
