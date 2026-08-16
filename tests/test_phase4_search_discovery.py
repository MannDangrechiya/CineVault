# CineVault OS — Phase 4: Search & Discovery Verification Tests
# Validates PostgreSQL-first search, multilingual cases (Parasite/기생충/Gisaengchung, Your Name/君の名は。/Kimi no Na wa), people, franchises, and faceted filters

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

class Phase4SearchDiscoveryTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 4 verification for multilingual search and discovery."""

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
            # 1. Ensure Content Types exist
            types = [("movie", "Feature Film"), ("anime", "Anime Series/Film"), ("tv_series", "Television Series")]
            for t_id, t_name in types:
                existing = await session.get(ContentTypeModel, t_id)
                if not existing:
                    session.add(ContentTypeModel(content_type_id=t_id, type_name=t_name))

            # 2. Ensure Genres & Themes exist
            genres = [("drama", "Drama"), ("thriller", "Thriller"), ("animation", "Animation"), ("sci_fi", "Sci-Fi")]
            for g_id, g_name in genres:
                existing = await session.get(GenreModel, g_id)
                if not existing:
                    session.add(GenreModel(genre_id=g_id, name=g_name))

            themes = [("cyberpunk", "Cyberpunk"), ("class_struggle", "Class Struggle")]
            for th_id, th_name in themes:
                existing = await session.get(ThemeModel, th_id)
                if not existing:
                    session.add(ThemeModel(theme_id=th_id, name=th_name))

            await session.flush()

            # 3. Seed/Hydrate Required Multilingual Test Case 1: Parasite / 기생충 / Gisaengchung
            stmt_p = select(TitleModel).where(TitleModel.canonical_title == "Parasite", TitleModel.production_year == 2019)
            parasite = (await session.execute(stmt_p)).scalar_one_or_none()
            if not parasite:
                parasite = TitleModel(
                    title_id=uuid.uuid4(),
                    display_id="MOV-PARASITE-01",
                    content_type_id="movie",
                    canonical_title="Parasite",
                    original_title="기생충",
                    production_year=2019,
                    synopsis="Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan."
                )
                session.add(parasite)
                await session.flush()

            # Add Parasite Alias, Country, Genre, Theme
            stmt_pa = select(TitleAliasModel).where(TitleAliasModel.title_id == parasite.title_id, TitleAliasModel.alias_name == "Gisaengchung")
            if not (await session.execute(stmt_pa)).scalar_one_or_none():
                session.add(TitleAliasModel(
                    alias_id=uuid.uuid4(),
                    title_id=parasite.title_id,
                    alias_name="Gisaengchung",
                    alias_type="TRANSLITERATION",
                    language_code="kor"
                ))

            stmt_pc = select(TitleCountryModel).where(TitleCountryModel.title_id == parasite.title_id, TitleCountryModel.country_code == "KR")
            if not (await session.execute(stmt_pc)).scalar_one_or_none():
                session.add(TitleCountryModel(title_id=parasite.title_id, country_code="KR"))

            stmt_pg = select(TitleGenreModel).where(TitleGenreModel.title_id == parasite.title_id, TitleGenreModel.genre_id == "drama")
            if not (await session.execute(stmt_pg)).scalar_one_or_none():
                session.add(TitleGenreModel(title_id=parasite.title_id, genre_id="drama"))

            stmt_pt = select(TitleThemeModel).where(TitleThemeModel.title_id == parasite.title_id, TitleThemeModel.theme_id == "class_struggle")
            if not (await session.execute(stmt_pt)).scalar_one_or_none():
                session.add(TitleThemeModel(title_id=parasite.title_id, theme_id="class_struggle"))

            # 4. Seed/Hydrate Required Multilingual Test Case 2: Your Name / 君の名は。/ Kimi no Na wa
            stmt_y = select(TitleModel).where(TitleModel.canonical_title == "Your Name.", TitleModel.production_year == 2016)
            your_name = (await session.execute(stmt_y)).scalar_one_or_none()
            if not your_name:
                your_name = TitleModel(
                    title_id=uuid.uuid4(),
                    display_id="ANI-YOURNAME-01",
                    content_type_id="anime",
                    canonical_title="Your Name.",
                    original_title="君の名は。",
                    production_year=2016,
                    synopsis="Two teenagers share a profound, magical connection upon discovering they are swapping bodies."
                )
                session.add(your_name)
                await session.flush()

            stmt_ya = select(TitleAliasModel).where(TitleAliasModel.title_id == your_name.title_id, TitleAliasModel.alias_name == "Kimi no Na wa")
            if not (await session.execute(stmt_ya)).scalar_one_or_none():
                session.add(TitleAliasModel(
                    alias_id=uuid.uuid4(),
                    title_id=your_name.title_id,
                    alias_name="Kimi no Na wa",
                    alias_type="ROMAJI",
                    language_code="jpn"
                ))

            stmt_yc = select(TitleCountryModel).where(TitleCountryModel.title_id == your_name.title_id, TitleCountryModel.country_code == "JP")
            if not (await session.execute(stmt_yc)).scalar_one_or_none():
                session.add(TitleCountryModel(title_id=your_name.title_id, country_code="JP"))

            stmt_yg = select(TitleGenreModel).where(TitleGenreModel.title_id == your_name.title_id, TitleGenreModel.genre_id == "animation")
            if not (await session.execute(stmt_yg)).scalar_one_or_none():
                session.add(TitleGenreModel(title_id=your_name.title_id, genre_id="animation"))

            # 5. Seed Person with Alias
            stmt_dir = select(PersonModel).where(PersonModel.canonical_name == "Bong Joon-ho")
            director = (await session.execute(stmt_dir)).scalar_one_or_none()
            if not director:
                director = PersonModel(
                    person_id=uuid.uuid4(),
                    canonical_name="Bong Joon-ho"
                )
                session.add(director)
                await session.flush()

            stmt_da = select(PersonNameModel).where(PersonNameModel.person_id == director.person_id, PersonNameModel.name_value == "Bong Jun-ho")
            if not (await session.execute(stmt_da)).scalar_one_or_none():
                session.add(PersonNameModel(
                    name_id=uuid.uuid4(),
                    person_id=director.person_id,
                    name_value="Bong Jun-ho",
                    name_type="ROMANIZATION"
                ))

            # 6. Seed Franchise
            stmt_fr = select(FranchiseModel).where(FranchiseModel.name == "Marvel Cinematic Universe")
            franchise = (await session.execute(stmt_fr)).scalar_one_or_none()
            if not franchise:
                session.add(FranchiseModel(
                    franchise_id=uuid.uuid4(),
                    name="Marvel Cinematic Universe"
                ))

            await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_multilingual_benchmark_parasite(self):
        """Required Multilingual Case 1: Search Parasite via English, Korean Hangul, and Romanized Transliteration."""
        async with self.SessionLocal() as session:
            # English Title Search
            res_en = await search_repository.search_catalog(session, q="Parasite")
            self.assertGreaterEqual(res_en.total_hits, 1)
            self.assertEqual(res_en.results[0].canonical_title, "Parasite")

            # Korean Original Script Search
            res_kr = await search_repository.search_catalog(session, q="기생충")
            self.assertGreaterEqual(res_kr.total_hits, 1)
            self.assertEqual(res_kr.results[0].canonical_title, "Parasite")

            # Romanized Transliteration Search
            res_trans = await search_repository.search_catalog(session, q="Gisaengchung")
            self.assertGreaterEqual(res_trans.total_hits, 1)
            self.assertEqual(res_trans.results[0].canonical_title, "Parasite")

    async def test_multilingual_benchmark_your_name(self):
        """Required Multilingual Case 2: Search Your Name via English, Japanese Kanji, and Romaji Transliteration."""
        async with self.SessionLocal() as session:
            # English Title Search
            res_en = await search_repository.search_catalog(session, q="Your Name")
            self.assertGreaterEqual(res_en.total_hits, 1)
            self.assertEqual(res_en.results[0].canonical_title, "Your Name.")

            # Japanese Kanji Original Script Search
            res_jp = await search_repository.search_catalog(session, q="君の名は。")
            self.assertGreaterEqual(res_jp.total_hits, 1)
            self.assertEqual(res_jp.results[0].canonical_title, "Your Name.")

            # Romaji Transliteration Search
            res_romaji = await search_repository.search_catalog(session, q="Kimi no Na wa")
            self.assertGreaterEqual(res_romaji.total_hits, 1)
            self.assertEqual(res_romaji.results[0].canonical_title, "Your Name.")

    async def test_person_search_by_canonical_and_alias(self):
        """Validates person discovery across primary name and transliterated name aliases."""
        async with self.SessionLocal() as session:
            # Primary name search
            res_primary = await search_repository.search_catalog(session, q="Bong Joon-ho", entity_type="PERSON")
            self.assertGreaterEqual(res_primary.total_hits, 1)
            self.assertEqual(res_primary.results[0].canonical_title, "Bong Joon-ho")
            self.assertEqual(res_primary.results[0].entity_type, "PERSON")

            # Alias search
            res_alias = await search_repository.search_catalog(session, q="Bong Jun-ho", entity_type="PERSON")
            self.assertGreaterEqual(res_alias.total_hits, 1)
            self.assertEqual(res_alias.results[0].canonical_title, "Bong Joon-ho")

    async def test_franchise_search(self):
        """Validates franchise entity search."""
        async with self.SessionLocal() as session:
            res_fran = await search_repository.search_catalog(session, q="Marvel Cinematic Universe", entity_type="FRANCHISE")
            self.assertGreaterEqual(res_fran.total_hits, 1)
            self.assertEqual(res_fran.results[0].canonical_title, "Marvel Cinematic Universe")
            self.assertEqual(res_fran.results[0].entity_type, "FRANCHISE")

    async def test_faceted_filtering_by_genre_country_year_theme(self):
        """Validates faceted search combinations: genre, country, year, content_type, and theme."""
        async with self.SessionLocal() as session:
            # Filter Korean Drama from 2019
            res_kr_drama = await search_repository.search_catalog(
                session,
                q="Parasite",
                country="KR",
                genre="drama",
                year=2019,
                content_type="movie"
            )
            self.assertEqual(res_kr_drama.total_hits, 1)
            self.assertEqual(res_kr_drama.results[0].canonical_title, "Parasite")

            # Filter Theme (class_struggle)
            res_theme = await search_repository.search_catalog(
                session,
                q="Parasite",
                theme="class_struggle"
            )
            self.assertEqual(res_theme.total_hits, 1)
            self.assertEqual(res_theme.results[0].canonical_title, "Parasite")
