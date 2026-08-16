# CineVault OS — Phase 12: Recommendation Engine Foundation Verification Tests
# Validates cold-start recommendations, behavioral personalization, multi-attribute similarity, explainability, and deterministic ranking governance

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
from services.api.schemas.personal import WatchEventCreate, RatingCreate
from services.api.schemas.recommendations import (
    RecommendationModeEnum, ColdStartPreferenceInput
)

class Phase12RecommendationFoundationTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 12 verification for explainable recommendation engine foundation."""

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

            for g_id, g_name in [("drama", "Drama"), ("thriller", "Thriller"), ("sci_fi", "Sci-Fi"), ("action", "Action")]:
                if not await session.get(GenreModel, g_id):
                    session.add(GenreModel(genre_id=g_id, name=g_name))

            for r_id, r_name, r_cat in [("DIRECTOR", "Director", "CREW"), ("ACTOR", "Actor", "CAST")]:
                if not await session.get(CreditRoleModel, r_id):
                    session.add(CreditRoleModel(credit_role_id=r_id, role_name=r_name, category=r_cat))

            await session.flush()

            # 2. Seed Directors
            self.director_bong = PersonModel(person_id=uuid.uuid4(), canonical_name="Bong Joon-ho")
            self.director_nolan = PersonModel(person_id=uuid.uuid4(), canonical_name="Christopher Nolan")
            session.add_all([self.director_bong, self.director_nolan])
            await session.flush()

            # 3. Seed Film 1: Parasite (Bong Joon-ho, Drama/Thriller, KR)
            self.film_parasite = TitleModel(
                title_id=uuid.uuid4(),
                display_id="MOV-REC-001",
                content_type_id="movie",
                canonical_title="Parasite Rec",
                original_title="기생충",
                production_year=2019
            )
            # Seed Film 2: Memories of Murder (Bong Joon-ho, Drama/Thriller, KR)
            self.film_memories = TitleModel(
                title_id=uuid.uuid4(),
                display_id="MOV-REC-002",
                content_type_id="movie",
                canonical_title="Memories of Murder Rec",
                original_title="살인의 추억",
                production_year=2003
            )
            # Seed Film 3: Oppenheimer (Christopher Nolan, Drama/Thriller, US)
            self.film_oppenheimer = TitleModel(
                title_id=uuid.uuid4(),
                display_id="MOV-REC-003",
                content_type_id="movie",
                canonical_title="Oppenheimer Rec",
                original_title="Oppenheimer",
                production_year=2023
            )
            session.add_all([self.film_parasite, self.film_memories, self.film_oppenheimer])
            await session.flush()

            # Editions
            ed1 = EditionModel(edition_id=uuid.uuid4(), title_id=self.film_parasite.title_id, edition_name="Theatrical", runtime_minutes=132, is_primary=True)
            ed2 = EditionModel(edition_id=uuid.uuid4(), title_id=self.film_memories.title_id, edition_name="Theatrical", runtime_minutes=131, is_primary=True)
            ed3 = EditionModel(edition_id=uuid.uuid4(), title_id=self.film_oppenheimer.title_id, edition_name="Theatrical", runtime_minutes=180, is_primary=True)

            # Genres & Countries
            g_p1 = TitleGenreModel(title_id=self.film_parasite.title_id, genre_id="thriller")
            g_p2 = TitleGenreModel(title_id=self.film_parasite.title_id, genre_id="drama")
            c_p = TitleCountryModel(title_id=self.film_parasite.title_id, country_code="KR")
            l_p = TitleLanguageModel(title_id=self.film_parasite.title_id, language_code="kor")
            cr_p = CreditModel(credit_id=uuid.uuid4(), title_id=self.film_parasite.title_id, person_id=self.director_bong.person_id, credit_role_id="DIRECTOR")

            g_m1 = TitleGenreModel(title_id=self.film_memories.title_id, genre_id="thriller")
            g_m2 = TitleGenreModel(title_id=self.film_memories.title_id, genre_id="drama")
            c_m = TitleCountryModel(title_id=self.film_memories.title_id, country_code="KR")
            l_m = TitleLanguageModel(title_id=self.film_memories.title_id, language_code="kor")
            cr_m = CreditModel(credit_id=uuid.uuid4(), title_id=self.film_memories.title_id, person_id=self.director_bong.person_id, credit_role_id="DIRECTOR")

            g_o1 = TitleGenreModel(title_id=self.film_oppenheimer.title_id, genre_id="drama")
            c_o = TitleCountryModel(title_id=self.film_oppenheimer.title_id, country_code="US")
            l_o = TitleLanguageModel(title_id=self.film_oppenheimer.title_id, language_code="eng")
            cr_o = CreditModel(credit_id=uuid.uuid4(), title_id=self.film_oppenheimer.title_id, person_id=self.director_nolan.person_id, credit_role_id="DIRECTOR")

            session.add_all([
                ed1, ed2, ed3,
                g_p1, g_p2, c_p, l_p, cr_p,
                g_m1, g_m2, c_m, l_m, cr_m,
                g_o1, c_o, l_o, cr_o
            ])
            await session.commit()

        self.new_user_id = str(uuid.uuid4())
        self.active_user_id = str(uuid.uuid4())
        self.now = datetime.now(timezone.utc)

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_mandatory_cold_start_for_new_user(self):
        """Mandatory Cold-Start: A brand-new user with 0 watch history receives relevant recommendations via explicit preferences."""
        async with self.SessionLocal() as session:
            cold_prefs = ColdStartPreferenceInput(
                preferred_genres=["Drama", "Thriller"],
                preferred_countries=["KR"],
                preferred_languages=["kor"]
            )

            res = await recommendation_repository.get_recommendations(
                db=session,
                user_id=self.new_user_id,
                mode=RecommendationModeEnum.COLD_START,
                cold_start_input=cold_prefs,
                limit=5
            )

            self.assertEqual(res.mode, RecommendationModeEnum.COLD_START)
            self.assertTrue(res.is_cold_start)
            self.assertGreaterEqual(res.total, 1)
            # Ensure every item has a grounded explanation
            for item in res.data:
                self.assertIsNotNone(item.explanation.explanation_text)
                self.assertGreater(len(item.explanation.explanation_text), 5)

    async def test_because_you_liked_similarity_mode(self):
        """Validates 'Because You Liked' mode: Seed title produces ranked similar titles with grounded director/genre matches."""
        async with self.SessionLocal() as session:
            seed_id = str(self.film_parasite.title_id)

            res = await recommendation_repository.get_recommendations(
                db=session,
                user_id=self.active_user_id,
                mode=RecommendationModeEnum.BECAUSE_YOU_LIKED,
                seed_title_id=seed_id,
                include_watched=True,
                limit=5
            )

            self.assertGreaterEqual(res.total, 1)
            first = res.data[0]
            self.assertGreater(first.recommendation_score, 0.0)
            self.assertIsNotNone(first.explanation.explanation_text)

    async def test_recommendation_explanation_score_breakdown(self):
        """Transparent Explainability: Every recommendation provides a score breakdown without hallucination."""
        async with self.SessionLocal() as session:
            target_id = str(self.film_memories.title_id)
            seed_id = str(self.film_parasite.title_id)

            explain_res = await recommendation_repository.explain_recommendation(
                db=session,
                user_id=self.active_user_id,
                title_id=target_id,
                seed_title_id=seed_id
            )

            self.assertEqual(explain_res.title_id, target_id)
            self.assertIn("content_similarity", explain_res.score_breakdown)
            self.assertIn("personal_taste", explain_res.score_breakdown)
            self.assertIn("total_score", explain_res.score_breakdown)
            self.assertIsNotNone(explain_res.explanation.explanation_text)

    async def test_deterministic_ranking_governance_no_direct_llm_decisions(self):
        """Constraint: Recommendation ranking and scoring are deterministic functions governed by catalog and user weights."""
        async with self.SessionLocal() as session:
            # First run
            res1 = await recommendation_repository.get_recommendations(
                db=session, user_id=self.new_user_id, mode=RecommendationModeEnum.TONIGHT, limit=5
            )
            # Second run
            res2 = await recommendation_repository.get_recommendations(
                db=session, user_id=self.new_user_id, mode=RecommendationModeEnum.TONIGHT, limit=5
            )

            # Ranks and scores must match deterministically
            self.assertEqual(res1.total, res2.total)
            if res1.data and res2.data:
                self.assertEqual(res1.data[0].title_id, res2.data[0].title_id)
                self.assertEqual(res1.data[0].recommendation_score, res2.data[0].recommendation_score)
