# CineVault OS — Phase 11: Taste Profile Verification Tests
# Validates learned cinematic taste model (genres, themes, directors, actors, decades, runtime, completion behavior) and non-invasive privacy constraints

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
    ThemeModel, TitleThemeModel, PersonModel, CreditRoleModel, CreditModel,
    TitleCountryModel, TitleLanguageModel
)
from services.api.schemas.personal import WatchEventCreate, UserTitleStateUpdate, RatingCreate

class Phase11TasteProfileTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 11 verification for user taste profile modeling and privacy boundaries."""

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
            # 1. Ensure Content Types, Genres, Themes, Roles
            movie_type = await session.get(ContentTypeModel, "movie")
            if not movie_type:
                session.add(ContentTypeModel(content_type_id="movie", type_name="Feature Film"))

            for g_id, g_name in [("thriller", "Thriller"), ("drama", "Drama"), ("sci_fi", "Sci-Fi")]:
                if not await session.get(GenreModel, g_id):
                    session.add(GenreModel(genre_id=g_id, name=g_name))

            for th_id, th_name in [("class_struggle", "Class Struggle"), ("dystopia", "Dystopian Society")]:
                if not await session.get(ThemeModel, th_id):
                    session.add(ThemeModel(theme_id=th_id, name=th_name))

            for r_id, r_name, r_cat in [("DIRECTOR", "Director", "CREW"), ("ACTOR", "Actor", "CAST")]:
                if not await session.get(CreditRoleModel, r_id):
                    session.add(CreditRoleModel(credit_role_id=r_id, role_name=r_name, category=r_cat))

            await session.flush()

            # 2. Seed Directors and Actors
            self.director_bong = PersonModel(person_id=uuid.uuid4(), canonical_name="Bong Joon-ho")
            self.actor_song = PersonModel(person_id=uuid.uuid4(), canonical_name="Song Kang-ho")
            session.add_all([self.director_bong, self.actor_song])
            await session.flush()

            # 3. Seed Film 1: Parasite (2019, 132 mins, KR, kor, Drama/Thriller, Bong Joon-ho/Song Kang-ho)
            self.film_parasite = TitleModel(
                title_id=uuid.uuid4(),
                display_id="MOV-TASTE-001",
                content_type_id="movie",
                canonical_title="Parasite Taste",
                original_title="기생충",
                production_year=2019
            )
            session.add(self.film_parasite)
            await session.flush()

            ed1 = EditionModel(edition_id=uuid.uuid4(), title_id=self.film_parasite.title_id, edition_name="Theatrical", runtime_minutes=132, is_primary=True)
            g1 = TitleGenreModel(title_id=self.film_parasite.title_id, genre_id="thriller")
            g2 = TitleGenreModel(title_id=self.film_parasite.title_id, genre_id="drama")
            th1 = TitleThemeModel(title_id=self.film_parasite.title_id, theme_id="class_struggle")
            c1 = TitleCountryModel(title_id=self.film_parasite.title_id, country_code="KR")
            l1 = TitleLanguageModel(title_id=self.film_parasite.title_id, language_code="kor")
            cr1 = CreditModel(credit_id=uuid.uuid4(), title_id=self.film_parasite.title_id, person_id=self.director_bong.person_id, credit_role_id="DIRECTOR")
            cr2 = CreditModel(credit_id=uuid.uuid4(), title_id=self.film_parasite.title_id, person_id=self.actor_song.person_id, credit_role_id="ACTOR", character_name="Kim Ki-taek")

            # 4. Seed Film 2: Snowpiercer (2013, 126 mins, KR, eng, Sci-Fi/Drama, Bong Joon-ho/Song Kang-ho)
            self.film_snowpiercer = TitleModel(
                title_id=uuid.uuid4(),
                display_id="MOV-TASTE-002",
                content_type_id="movie",
                canonical_title="Snowpiercer Taste",
                original_title="설국열차",
                production_year=2013
            )
            session.add(self.film_snowpiercer)
            await session.flush()

            ed2 = EditionModel(edition_id=uuid.uuid4(), title_id=self.film_snowpiercer.title_id, edition_name="Theatrical", runtime_minutes=126, is_primary=True)
            g3 = TitleGenreModel(title_id=self.film_snowpiercer.title_id, genre_id="sci_fi")
            g4 = TitleGenreModel(title_id=self.film_snowpiercer.title_id, genre_id="drama")
            th2 = TitleThemeModel(title_id=self.film_snowpiercer.title_id, theme_id="dystopia")
            c2 = TitleCountryModel(title_id=self.film_snowpiercer.title_id, country_code="KR")
            l2 = TitleLanguageModel(title_id=self.film_snowpiercer.title_id, language_code="eng")
            cr3 = CreditModel(credit_id=uuid.uuid4(), title_id=self.film_snowpiercer.title_id, person_id=self.director_bong.person_id, credit_role_id="DIRECTOR")
            cr4 = CreditModel(credit_id=uuid.uuid4(), title_id=self.film_snowpiercer.title_id, person_id=self.actor_song.person_id, credit_role_id="ACTOR", character_name="Namgoong Minsoo")

            session.add_all([
                ed1, g1, g2, th1, c1, l1, cr1, cr2,
                ed2, g3, g4, th2, c2, l2, cr3, cr4
            ])
            await session.commit()

        self.user_a_id = str(uuid.uuid4())
        self.user_b_id = str(uuid.uuid4())
        self.now = datetime.now(timezone.utc)

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_taste_profile_learning_and_affinities(self):
        """Validates that the system learns director, actor, genre, theme, decade, runtime, and completion affinities."""
        async with self.SessionLocal() as session:
            t1_str = str(self.film_parasite.title_id)
            t2_str = str(self.film_snowpiercer.title_id)

            # User A completes Parasite (rated 10) and completes Snowpiercer (rated 9)
            await personal_repository.update_user_title_state(
                db=session, user_id=self.user_a_id, title_id=t1_str,
                body=UserTitleStateUpdate(manual_status_override="COMPLETED", is_favorite=True)
            )
            await personal_repository.update_user_title_state(
                db=session, user_id=self.user_a_id, title_id=t2_str,
                body=UserTitleStateUpdate(manual_status_override="COMPLETED", is_favorite=False)
            )

            await personal_repository.create_watch_event(
                db=session, user_id=self.user_a_id,
                body=WatchEventCreate(title_id=t1_str, watched_at=self.now.isoformat(), progress_percentage=100.0)
            )
            await personal_repository.create_watch_event(
                db=session, user_id=self.user_a_id,
                body=WatchEventCreate(title_id=t2_str, watched_at=self.now.isoformat(), progress_percentage=100.0)
            )

            await personal_repository.set_rating(
                db=session, user_id=self.user_a_id,
                body=RatingCreate(title_id=t1_str, rating_value=10)
            )
            await personal_repository.set_rating(
                db=session, user_id=self.user_a_id,
                body=RatingCreate(title_id=t2_str, rating_value=9)
            )
            await session.commit()

            # Compute taste profile
            profile = await recommendation_repository.get_taste_profile(db=session, user_id=self.user_a_id)

            # 1. Top director: Bong Joon-ho (2 films watched)
            self.assertGreaterEqual(len(profile.top_directors), 1)
            self.assertEqual(profile.top_directors[0].person_name, "Bong Joon-ho")
            self.assertEqual(profile.top_directors[0].titles_watched, 2)

            # 2. Top actor: Song Kang-ho (2 films watched)
            self.assertGreaterEqual(len(profile.top_actors), 1)
            self.assertEqual(profile.top_actors[0].person_name, "Song Kang-ho")
            self.assertEqual(profile.top_actors[0].titles_watched, 2)

            # 3. Top genre: Drama (appears in both films, watched_count=2, avg_rating=9.5)
            drama_affinity = next((g for g in profile.top_genres if g.genre == "Drama"), None)
            self.assertIsNotNone(drama_affinity)
            self.assertEqual(drama_affinity.watched_count, 2)
            self.assertEqual(drama_affinity.avg_rating, 9.5)

            # 4. Favorite Decades & Runtimes: 2010s, average runtime = (132 + 126) / 2 = 129
            self.assertIn("2010s", profile.favorite_decades)
            self.assertEqual(profile.average_preferred_runtime, 129)

            # 5. Completion behavior: 100% completion rate, 0% abandon rate
            self.assertEqual(profile.completion_rate, 1.0)
            self.assertEqual(profile.abandon_rate, 0.0)

            # 6. Total rated count & diversity
            self.assertEqual(profile.total_rated_count, 2)
            self.assertGreater(profile.taste_diversity_score, 0.0)

    async def test_cross_user_isolation_on_taste_profile(self):
        """Constraint: User B receives an empty/independent taste profile with zero leakage of User A's tastes."""
        async with self.SessionLocal() as session:
            # User A logs data
            t1_str = str(self.film_parasite.title_id)
            await personal_repository.create_watch_event(
                db=session, user_id=self.user_a_id,
                body=WatchEventCreate(title_id=t1_str, watched_at=self.now.isoformat(), progress_percentage=100.0)
            )
            await session.commit()

            # User B checks taste profile
            b_profile = await recommendation_repository.get_taste_profile(db=session, user_id=self.user_b_id)
            self.assertEqual(len(b_profile.top_directors), 0)
            self.assertEqual(len(b_profile.top_actors), 0)
            self.assertEqual(len(b_profile.top_genres), 0)
            self.assertEqual(b_profile.total_rated_count, 0)
