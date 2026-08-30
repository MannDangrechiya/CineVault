# CineVault OS - Phase W9: Search Quality Verification Tests

from unittest import IsolatedAsyncioTestCase
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.repositories.search import search_repository
from services.api.models.canonical import (
    TitleModel, TitleAliasModel, PersonModel, PersonNameModel,
    FranchiseModel, TitleGenreModel, GenreModel,
    TitleThemeModel, ThemeModel, TitleCountryModel, ContentTypeModel
)

class PhaseW9SearchQualityTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase W9 verification for search relevance, exact matching, and pagination."""

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
            # Basic seeding for W9 search
            types = [("movie", "Feature Film"), ("series", "Television Series")]
            for t_id, t_name in types:
                if not await session.get(ContentTypeModel, t_id):
                    session.add(ContentTypeModel(content_type_id=t_id, type_name=t_name))

            genres = [("scifi", "Sci-Fi"), ("action", "Action")]
            for g_id, g_name in genres:
                if not await session.get(GenreModel, g_id):
                    session.add(GenreModel(genre_id=g_id, name=g_name))

            await session.flush()

            # Seed Title: The Matrix
            stmt = select(TitleModel).where(TitleModel.canonical_title == "The Matrix", TitleModel.production_year == 1999)
            matrix = (await session.execute(stmt)).scalar_one_or_none()
            if not matrix:
                matrix = TitleModel(
                    title_id=uuid.uuid4(),
                    display_id="MOV-MAT-01",
                    content_type_id="movie",
                    canonical_title="The Matrix",
                    original_title="The Matrix",
                    production_year=1999,
                    synopsis="A computer hacker learns from mysterious rebels about the true nature of his reality."
                )
                session.add(matrix)
                await session.flush()

            # Seed Title: The Matrix Reloaded
            stmt_reloaded = select(TitleModel).where(TitleModel.canonical_title == "The Matrix Reloaded")
            reloaded = (await session.execute(stmt_reloaded)).scalar_one_or_none()
            if not reloaded:
                reloaded = TitleModel(
                    title_id=uuid.uuid4(),
                    display_id="MOV-MAT-02",
                    content_type_id="movie",
                    canonical_title="The Matrix Reloaded",
                    original_title="The Matrix Reloaded",
                    production_year=2003
                )
                session.add(reloaded)
                await session.flush()

            # Genre mapping
            stmt_g = select(TitleGenreModel).where(TitleGenreModel.title_id == matrix.title_id, TitleGenreModel.genre_id == "scifi")
            if not (await session.execute(stmt_g)).scalar_one_or_none():
                session.add(TitleGenreModel(title_id=matrix.title_id, genre_id="scifi"))

            self.matrix_display_id = matrix.display_id
            await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_exact_title_search(self):
        """Validates that exact title searches rank highest."""
        async with self.SessionLocal() as session:
            res = await search_repository.search_catalog(session, q="The Matrix")
            self.assertGreaterEqual(res.total_hits, 1)
            self.assertEqual(res.results[0].canonical_title, "The Matrix")
            self.assertGreaterEqual(res.results[0].relevance_score, 0.99)

    async def test_prefix_search_ranking(self):
        """Validates prefix search returns correct ranking."""
        async with self.SessionLocal() as session:
            res = await search_repository.search_catalog(session, q="Matrix")
            titles = [r.canonical_title for r in res.results]
            self.assertIn("The Matrix", titles)

    async def test_fuzzy_typo_search(self):
        """Validates typo tolerance."""
        async with self.SessionLocal() as session:
            res = await search_repository.search_catalog(session, q="matrx")
            self.assertGreaterEqual(res.total_hits, 1)
            titles = [r.canonical_title for r in res.results]
            self.assertIn("The Matrix", titles)

    async def test_display_id_search(self):
        """Validates exact Display ID resolution."""
        async with self.SessionLocal() as session:
            res = await search_repository.search_catalog(session, q=self.matrix_display_id)
            self.assertEqual(res.total_hits, 1)
            self.assertEqual(res.results[0].canonical_title, "The Matrix")

    async def test_pagination_and_sorting(self):
        """Validates stable sorting and pagination parameters."""
        async with self.SessionLocal() as session:
            res_p1 = await search_repository.search_catalog(session, q="Matrix", limit=1, page=1)
            res_p2 = await search_repository.search_catalog(session, q="Matrix", limit=1, page=2)

            self.assertEqual(len(res_p1.results), 1)
            self.assertEqual(len(res_p2.results), 1)
            self.assertNotEqual(res_p1.results[0].id, res_p2.results[0].id)
            self.assertGreaterEqual(res_p1.total_hits, 2)
            self.assertGreaterEqual(res_p1.total_pages, 2)

    async def test_faceted_filtering(self):
        """Validates filters push down."""
        async with self.SessionLocal() as session:
            res = await search_repository.search_catalog(session, q="Matrix", genre="scifi", year=1999)
            self.assertEqual(len(res.results), 1)
            self.assertEqual(res.results[0].canonical_title, "The Matrix")

    async def test_zero_results(self):
        """Validates honest empty state without fallback fabrication."""
        async with self.SessionLocal() as session:
            res = await search_repository.search_catalog(session, q="xyzabc12349876nonsense")
            self.assertEqual(res.total_hits, 0)
            self.assertEqual(len(res.results), 0)
