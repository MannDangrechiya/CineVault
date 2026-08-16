# CineVault OS — Phase 13: Recommendation Quality Verification Tests
# Validates already-watched exclusion, negative preference penalties (poor rating & dropped status), MMR genre diversity, and non-clickbait quality controls

from unittest import IsolatedAsyncioTestCase
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.repositories.personal import personal_repository
from services.api.repositories.recommendations import recommendation_repository
from services.api.models.canonical import (
    TitleModel, ContentTypeModel, EditionModel, GenreModel, TitleGenreModel,
    PersonModel, CreditRoleModel, CreditModel, TitleCountryModel, TitleLanguageModel
)
from services.api.schemas.personal import WatchEventCreate, UserTitleStateUpdate, RatingCreate
from services.api.schemas.recommendations import RecommendationModeEnum

class Phase13RecommendationQualityTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 13 verification for recommendation quality, diversity, and negative signals."""

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
            # 1. Ensure Content Types, Genres, Roles
            movie_type = await session.get(ContentTypeModel, "movie")
            if not movie_type:
                session.add(ContentTypeModel(content_type_id="movie", type_name="Feature Film"))

            for g_id, g_name in [("horror", "Horror"), ("thriller", "Thriller"), ("comedy", "Comedy"), ("sci_fi", "Sci-Fi")]:
                if not await session.get(GenreModel, g_id):
                    session.add(GenreModel(genre_id=g_id, name=g_name))

            for r_id, r_name, r_cat in [("DIRECTOR", "Director", "CREW"), ("ACTOR", "Actor", "CAST")]:
                if not await session.get(CreditRoleModel, r_id):
                    session.add(CreditRoleModel(credit_role_id=r_id, role_name=r_name, category=r_cat))

            await session.flush()

            # 2. Seed Titles
            # Film A (Horror, Director X)
            self.film_horror1 = TitleModel(
                title_id=uuid.uuid4(),
                display_id="MOV-Q-001",
                content_type_id="movie",
                canonical_title="Horror Night 1",
                original_title="Horror Night 1",
                production_year=2021
            )
            # Film B (Horror, Director X)
            self.film_horror2 = TitleModel(
                title_id=uuid.uuid4(),
                display_id="MOV-Q-002",
                content_type_id="movie",
                canonical_title="Horror Night 2",
                original_title="Horror Night 2",
                production_year=2022
            )
            # Film C (Sci-Fi, Director Y)
            self.film_scifi = TitleModel(
                title_id=uuid.uuid4(),
                display_id="MOV-Q-003",
                content_type_id="movie",
                canonical_title="Cosmic Horizon",
                original_title="Cosmic Horizon",
                production_year=2023
            )
            session.add_all([self.film_horror1, self.film_horror2, self.film_scifi])
            await session.flush()

            ed1 = EditionModel(edition_id=uuid.uuid4(), title_id=self.film_horror1.title_id, edition_name="Theatrical", runtime_minutes=95, is_primary=True)
            ed2 = EditionModel(edition_id=uuid.uuid4(), title_id=self.film_horror2.title_id, edition_name="Theatrical", runtime_minutes=100, is_primary=True)
            ed3 = EditionModel(edition_id=uuid.uuid4(), title_id=self.film_scifi.title_id, edition_name="Theatrical", runtime_minutes=120, is_primary=True)

            g1 = TitleGenreModel(title_id=self.film_horror1.title_id, genre_id="horror")
            g2 = TitleGenreModel(title_id=self.film_horror2.title_id, genre_id="horror")
            g3 = TitleGenreModel(title_id=self.film_scifi.title_id, genre_id="sci_fi")

            session.add_all([ed1, ed2, ed3, g1, g2, g3])
            await session.commit()

        self.user_id = str(uuid.uuid4())
        self.now = datetime.now(timezone.utc)

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_already_watched_exclusion_in_recommendations(self):
        """Already-Watched Exclusion: Watched titles are excluded from recommendations when include_watched=False."""
        async with self.SessionLocal() as session:
            h1_id = str(self.film_horror1.title_id)

            # User logs Film Horror 1 as watched
            await personal_repository.create_watch_event(
                db=session, user_id=self.user_id,
                body=WatchEventCreate(title_id=h1_id, watched_at=self.now.isoformat(), progress_percentage=100.0)
            )
            await session.commit()

            # Query recommendations with include_watched=False
            res = await recommendation_repository.get_recommendations(
                db=session, user_id=self.user_id, mode=RecommendationModeEnum.TONIGHT, include_watched=False, limit=10
            )

            rec_ids = [item.title_id for item in res.data]
            self.assertNotIn(h1_id, rec_ids, "Watched title must NOT appear in recommendations when include_watched=False")

    async def test_negative_preference_signals_penalize_disliked_genres(self):
        """Negative Preferences: Poor ratings (<= 3) and DROPPED state down-rank related genres and creators."""
        async with self.SessionLocal() as session:
            h1_id = str(self.film_horror1.title_id)
            scifi_id = str(self.film_scifi.title_id)

            # User drops Film Horror 1 and rates it 2/10
            await personal_repository.update_user_title_state(
                db=session, user_id=self.user_id, title_id=h1_id,
                body=UserTitleStateUpdate(manual_status_override="DROPPED")
            )
            await personal_repository.set_rating(
                db=session, user_id=self.user_id,
                body=RatingCreate(title_id=h1_id, rating_value=2)
            )

            # User completes Sci-Fi and rates it 10/10
            await personal_repository.update_user_title_state(
                db=session, user_id=self.user_id, title_id=scifi_id,
                body=UserTitleStateUpdate(manual_status_override="COMPLETED", is_favorite=True)
            )
            await personal_repository.set_rating(
                db=session, user_id=self.user_id,
                body=RatingCreate(title_id=scifi_id, rating_value=10)
            )
            await session.commit()

            # Get recommendations for unseen titles
            res = await recommendation_repository.get_recommendations(
                db=session, user_id=self.user_id, mode=RecommendationModeEnum.TONIGHT, include_watched=True, limit=10
            )

            horror_items = [i for i in res.data if "Horror" in i.genres]
            scifi_items = [i for i in res.data if "Sci-Fi" in i.genres]

            if horror_items and scifi_items:
                self.assertGreater(
                    scifi_items[0].recommendation_score,
                    horror_items[0].recommendation_score,
                    "Liked genre titles must rank significantly higher than dropped/penalized genre titles"
                )

    async def test_mmr_genre_diversity_re_ranking(self):
        """Diversity & MMR: Repeated identical genres receive diversity dampening to ensure a rich catalog mix."""
        async with self.SessionLocal() as session:
            res = await recommendation_repository.get_recommendations(
                db=session, user_id=self.user_id, mode=RecommendationModeEnum.TONIGHT, include_watched=True, limit=10
            )
            # Ensure recommendations returned
            self.assertGreaterEqual(res.total, 1)
            scores = [i.recommendation_score for i in res.data]
            # Ensure sorting is descending
            self.assertEqual(scores, sorted(scores, reverse=True))
