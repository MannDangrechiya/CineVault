# CineVault OS — Phase 1: Canonical Data Foundation Verification Tests
# Verifies complete structural catalog foundation, relational hierarchies, and representative entities

from unittest import IsolatedAsyncioTestCase
import uuid
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.models.canonical import (
    ContentTypeModel, GenreModel, ThemeModel, KeywordModel, CreditRoleModel,
    CertificationModel, ProductionCompanyModel, TitleModel, TitleAliasModel,
    TitleGenreModel, TitleThemeModel, TitleKeywordModel, TitleCountryModel, TitleLanguageModel,
    TitleCertificationModel, TitleCompanyModel, EditionModel, ReleaseModel,
    SeasonModel, EpisodeModel, PersonModel,
    CreditModel, TitleExternalIdModel,
    AwardModel, AwardCategoryModel, AwardEventModel, AwardResultModel,
    FestivalModel, FestivalEditionModel, FestivalParticipationModel
)
from services.api.repositories.canonical import canonical_repository

class Phase1CanonicalFoundationTestCase(IsolatedAsyncioTestCase):
    """Test suite executing complete verification for Phase 1 Canonical Data Foundation."""

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
            # Seed foundational taxonomy if missing in current transaction
            types = ["MOVIE", "TV_SERIES", "ANIME", "DOCUMENTARY"]
            for t_id in types:
                existing = await session.get(ContentTypeModel, t_id)
                if not existing:
                    session.add(ContentTypeModel(content_type_id=t_id, type_name=t_id.capitalize()))

            roles = [
                ("DIRECTOR", "Director", "DIRECTING"),
                ("ACTOR", "Actor", "CAST"),
                ("PRODUCER", "Producer", "PRODUCTION"),
                ("SHOWRUNNER", "Showrunner", "WRITING"),
            ]
            for r_id, r_name, r_cat in roles:
                existing = await session.get(CreditRoleModel, r_id)
                if not existing:
                    session.add(CreditRoleModel(credit_role_id=r_id, role_name=r_name, category=r_cat))

            genres = [
                ("SCI_FI", "Science Fiction"),
                ("DRAMA", "Drama"),
                ("ACTION", "Action"),
                ("DOCUMENTARY_GENRE", "Documentary"),
                ("ANIMATION", "Animation"),
            ]
            for g_id, g_name in genres:
                existing = await session.get(GenreModel, g_id)
                if not existing:
                    session.add(GenreModel(genre_id=g_id, name=g_name))

            themes = [
                ("DYSTOPIA", "Dystopian Society"),
                ("NATURE", "Nature & Wildlife"),
            ]
            for th_id, th_name in themes:
                existing = await session.get(ThemeModel, th_id)
                if not existing:
                    session.add(ThemeModel(theme_id=th_id, name=th_name))

            keywords = [
                ("ARTIFICIAL_INTELLIGENCE", "artificial intelligence"),
                ("SURVIVAL", "survival"),
            ]
            for kw_id, kw_name in keywords:
                existing = await session.get(KeywordModel, kw_id)
                if not existing:
                    session.add(KeywordModel(keyword_id=kw_id, name=kw_name))

            await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_representative_movie_hierarchy_and_editions(self):
        """Verifies Representative Movie with Title → Edition → Release, Credits, Studio, MPAA Certification, and Awards."""
        async with self.SessionLocal() as session:
            movie_id = uuid.uuid4()
            person_dir_id = uuid.uuid4()
            person_act_id = uuid.uuid4()
            company_wb_id = uuid.uuid4()
            cert_id = uuid.uuid4()
            award_id = uuid.uuid4()
            award_cat_id = uuid.uuid4()
            award_evt_id = uuid.uuid4()

            # 1. Base entities
            movie = TitleModel(
                title_id=movie_id,
                display_id=f"MOV-P1-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="MOVIE",
                canonical_title="Blade Runner 2049 (Phase 1 Test)",
                original_title="Blade Runner 2049 (Phase 1 Test)",
                production_year=2017,
                tagline="The key to the future is finally unearthed.",
                synopsis="Young Blade Runner K's discovery of a long-buried secret leads him to track down former Blade Runner Rick Deckard."
            )
            dir_person = PersonModel(person_id=person_dir_id, canonical_name="Denis Villeneuve")
            act_person = PersonModel(person_id=person_act_id, canonical_name="Ryan Gosling")
            wb_company = ProductionCompanyModel(company_id=company_wb_id, company_name="Warner Bros. Pictures", country_code="US")
            cert = CertificationModel(
                certification_id=cert_id,
                country_code="US",
                certification_code="R",
                rating_body="MPAA",
                meaning="Restricted: Under 17 requires accompanying parent",
                min_age=17
            )
            award = AwardModel(award_id=award_id, award_name="Academy Awards", organization="AMPAS")

            session.add_all([movie, dir_person, act_person, wb_company, cert, award])
            await session.flush()

            # 2. Award hierarchy
            award_cat = AwardCategoryModel(category_id=award_cat_id, award_id=award_id, category_name="Best Cinematography")
            award_evt = AwardEventModel(event_id=award_evt_id, award_id=award_id, year=2018, edition_number=90)
            session.add_all([award_cat, award_evt])
            await session.flush()

            award_res = AwardResultModel(
                result_id=uuid.uuid4(),
                event_id=award_evt_id,
                category_id=award_cat_id,
                title_id=movie_id,
                is_winner=True
            )

            # 3. Editions & Releases (Title → Edition → Release)
            ed_theatrical = EditionModel(
                edition_id=uuid.uuid4(),
                title_id=movie_id,
                edition_name="Theatrical Cut",
                is_primary=True,
                runtime_minutes=164,
                aspect_ratio="2.39:1",
                color_format="Color",
                sound_mix="Dolby Atmos"
            )
            session.add(ed_theatrical)
            await session.flush()

            rel_theatrical_us = ReleaseModel(
                release_id=uuid.uuid4(),
                edition_id=ed_theatrical.edition_id,
                release_name="US Theatrical Premiere",
                release_type="THEATRICAL",
                release_date=date(2017, 10, 6),
                country_code="US"
            )
            rel_digital = ReleaseModel(
                release_id=uuid.uuid4(),
                edition_id=ed_theatrical.edition_id,
                release_name="Global 4K Digital Release",
                release_type="DIGITAL",
                release_date=date(2017, 12, 26),
                country_code="US"
            )

            # 4. Credits, Company & Cert associations
            credit_dir = CreditModel(
                credit_id=uuid.uuid4(),
                title_id=movie_id,
                person_id=person_dir_id,
                credit_role_id="DIRECTOR",
                billing_order=1
            )
            credit_act = CreditModel(
                credit_id=uuid.uuid4(),
                title_id=movie_id,
                person_id=person_act_id,
                credit_role_id="ACTOR",
                character_name="Officer K",
                billing_order=2
            )
            title_company = TitleCompanyModel(
                title_company_id=uuid.uuid4(),
                title_id=movie_id,
                company_id=company_wb_id,
                role="STUDIO"
            )
            title_cert = TitleCertificationModel(
                title_id=movie_id,
                certification_id=cert_id,
                note="Violence, some sexuality, nudity and language"
            )
            ext_imdb = TitleExternalIdModel(
                mapping_id=uuid.uuid4(),
                title_id=movie_id,
                provider_name="IMDB",
                external_id=f"tt1856101-{uuid.uuid4().hex[:6]}"
            )
            title_genre = TitleGenreModel(title_id=movie_id, genre_id="SCI_FI")
            title_theme = TitleThemeModel(title_id=movie_id, theme_id="DYSTOPIA")
            title_country = TitleCountryModel(title_id=movie_id, country_code="US")

            session.add_all([
                rel_theatrical_us, rel_digital, credit_dir, credit_act,
                title_company, title_cert, award_res,
                ext_imdb, title_genre, title_theme, title_country
            ])
            await session.commit()

            # Query via repository and verify full schema hydration
            detail = await canonical_repository.get_title_by_id(session, str(movie_id))
            self.assertIsNotNone(detail)
            self.assertEqual(detail.canonical_title, "Blade Runner 2049 (Phase 1 Test)")
            self.assertEqual(detail.content_type, "MOVIE")
            self.assertEqual(len(detail.editions), 1)
            self.assertEqual(detail.editions[0].edition_name, "Theatrical Cut")
            self.assertEqual(len(detail.editions[0].releases), 2)
            self.assertEqual(detail.editions[0].releases[0].release_type, "THEATRICAL")
            self.assertEqual(len(detail.credits), 2)
            self.assertEqual(detail.credits[1].character_name, "Officer K")
            self.assertEqual(len(detail.companies), 1)
            self.assertEqual(detail.companies[0].company_name, "Warner Bros. Pictures")
            self.assertEqual(detail.companies[0].role, "STUDIO")
            self.assertEqual(len(detail.certifications), 1)
            self.assertEqual(detail.certifications[0].certification_code, "R")
            self.assertEqual(len(detail.awards), 1)
            self.assertTrue(detail.awards[0].is_winner)
            self.assertEqual(detail.awards[0].category_name, "Best Cinematography")
            self.assertEqual(len(detail.seasons), 0)

    async def test_representative_tv_series_hierarchy_and_seasons(self):
        """Verifies Representative TV Series with Title → Season → Episode, Network Company, and TV-MA Certification."""
        async with self.SessionLocal() as session:
            tv_id = uuid.uuid4()
            s1_id = uuid.uuid4()
            s2_id = uuid.uuid4()
            company_hbo_id = uuid.uuid4()
            cert_id = uuid.uuid4()

            # 1. Base TV Series Title & Network
            tv_series = TitleModel(
                title_id=tv_id,
                display_id=f"TV-P1-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="TV_SERIES",
                canonical_title="Succession (Phase 1 Test)",
                original_title="Succession (Phase 1 Test)",
                production_year=2018,
                synopsis="The Roy family is known for controlling the biggest media and entertainment company in the world."
            )
            hbo_company = ProductionCompanyModel(company_id=company_hbo_id, company_name="HBO", country_code="US")
            cert = CertificationModel(
                certification_id=cert_id,
                country_code="US",
                certification_code="TV-MA",
                rating_body="FCC/TV Parental Guidelines",
                meaning="Mature Audience Only"
            )

            session.add_all([tv_series, hbo_company, cert])
            await session.flush()

            # 2. Seasons & Episodes Hierarchy (Title → Season → Episode)
            season_1 = SeasonModel(
                season_id=s1_id,
                title_id=tv_id,
                season_number=1,
                season_name="Season 1",
                overview="Logan Roy's 80th birthday sets off a succession battle."
            )
            season_2 = SeasonModel(
                season_id=s2_id,
                title_id=tv_id,
                season_number=2,
                season_name="Season 2",
                overview="Kendall deals with the fallout from his hostile takeover attempt."
            )
            session.add_all([season_1, season_2])
            await session.flush()

            ep1_1 = EpisodeModel(
                episode_id=uuid.uuid4(),
                season_id=s1_id,
                episode_number=1,
                episode_name="Celebration",
                air_date=date(2018, 6, 3),
                runtime_minutes=60
            )
            ep1_2 = EpisodeModel(
                episode_id=uuid.uuid4(),
                season_id=s1_id,
                episode_number=2,
                episode_name="Shit Show at the Tit Factory",
                air_date=date(2018, 6, 10),
                runtime_minutes=58
            )
            ep2_1 = EpisodeModel(
                episode_id=uuid.uuid4(),
                season_id=s2_id,
                episode_number=1,
                episode_name="The Summer Palace",
                air_date=date(2019, 8, 11),
                runtime_minutes=62
            )

            title_network = TitleCompanyModel(
                title_company_id=uuid.uuid4(),
                title_id=tv_id,
                company_id=company_hbo_id,
                role="NETWORK"
            )
            title_cert = TitleCertificationModel(
                title_id=tv_id,
                certification_id=cert_id,
                note="Strong language, sexual content"
            )

            session.add_all([ep1_1, ep1_2, ep2_1, title_network, title_cert])
            await session.commit()

            detail = await canonical_repository.get_title_by_id(session, str(tv_id))
            self.assertIsNotNone(detail)
            self.assertEqual(detail.canonical_title, "Succession (Phase 1 Test)")
            self.assertEqual(detail.content_type, "TV_SERIES")
            self.assertEqual(len(detail.seasons), 2)
            self.assertEqual(detail.seasons[0].season_number, 1)
            self.assertEqual(len(detail.seasons[0].episodes), 2)
            self.assertEqual(detail.seasons[0].episodes[0].episode_name, "Celebration")
            self.assertEqual(detail.seasons[1].season_number, 2)
            self.assertEqual(len(detail.seasons[1].episodes), 1)
            self.assertEqual(detail.companies[0].role, "NETWORK")
            self.assertEqual(detail.companies[0].company_name, "HBO")
            self.assertEqual(detail.certifications[0].certification_code, "TV-MA")

    async def test_representative_anime_multilingual_and_aliases(self):
        """Verifies Representative Anime with original Japanese title, transliterated aliases, studio, and external IDs."""
        async with self.SessionLocal() as session:
            anime_id = uuid.uuid4()
            s1_id = uuid.uuid4()
            studio_id = uuid.uuid4()

            anime = TitleModel(
                title_id=anime_id,
                display_id=f"ANM-P1-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="ANIME",
                canonical_title="Attack on Titan (Phase 1 Test)",
                original_title="進撃の巨人 (Phase 1 Test)",
                production_year=2013,
                synopsis="After his hometown is destroyed and his mother is killed, young Eren Jaeger vows to cleanse the earth of the giant humanoid Titans."
            )
            studio = ProductionCompanyModel(company_id=studio_id, company_name="WIT Studio", country_code="JP")
            session.add_all([anime, studio])
            await session.flush()

            alias_romaji = TitleAliasModel(
                alias_id=uuid.uuid4(),
                title_id=anime_id,
                alias_name="Shingeki no Kyojin",
                alias_type="TRANSLITERATED",
                language_code="jpn"
            )
            alias_alt = TitleAliasModel(
                alias_id=uuid.uuid4(),
                title_id=anime_id,
                alias_name="AoT",
                alias_type="WORKING"
            )
            season_1 = SeasonModel(
                season_id=s1_id,
                title_id=anime_id,
                season_number=1,
                season_name="Season 1"
            )
            session.add_all([alias_romaji, alias_alt, season_1])
            await session.flush()

            ep1 = EpisodeModel(
                episode_id=uuid.uuid4(),
                season_id=s1_id,
                episode_number=1,
                episode_name="To You, in 2000 Years: The Fall of Shiganshina, Part 1",
                air_date=date(2013, 4, 7),
                runtime_minutes=24
            )
            title_studio = TitleCompanyModel(
                title_company_id=uuid.uuid4(),
                title_id=anime_id,
                company_id=studio_id,
                role="STUDIO"
            )
            ext_anilist = TitleExternalIdModel(
                mapping_id=uuid.uuid4(),
                title_id=anime_id,
                provider_name="ANILIST",
                external_id=f"16498-{uuid.uuid4().hex[:6]}",
                external_url="https://anilist.co/anime/16498"
            )
            ext_mal = TitleExternalIdModel(
                mapping_id=uuid.uuid4(),
                title_id=anime_id,
                provider_name="MAL",
                external_id=f"16498-{uuid.uuid4().hex[:6]}"
            )

            session.add_all([ep1, title_studio, ext_anilist, ext_mal])
            await session.commit()

            detail = await canonical_repository.get_title_by_id(session, str(anime_id))
            self.assertIsNotNone(detail)
            self.assertEqual(detail.canonical_title, "Attack on Titan (Phase 1 Test)")
            self.assertEqual(detail.original_title, "進撃の巨人 (Phase 1 Test)")
            self.assertEqual(len(detail.aliases), 2)
            self.assertTrue(any(a.alias_name == "Shingeki no Kyojin" and a.alias_type == "TRANSLITERATED" for a in detail.aliases))
            self.assertEqual(len(detail.external_ids), 2)
            self.assertTrue(any(e.provider_name == "ANILIST" and "16498" in e.external_id for e in detail.external_ids))
            self.assertEqual(detail.companies[0].company_name, "WIT Studio")

    async def test_representative_documentary_and_festivals(self):
        """Verifies Representative Documentary with Themes, Keywords, Festival Selection, and Distributor."""
        async with self.SessionLocal() as session:
            doc_id = uuid.uuid4()
            fest_id = uuid.uuid4()
            fest_ed_id = uuid.uuid4()
            distributor_id = uuid.uuid4()

            doc = TitleModel(
                title_id=doc_id,
                display_id=f"DOC-P1-{uuid.uuid4().hex[:6].upper()}",
                content_type_id="DOCUMENTARY",
                canonical_title="Planet Earth II (Phase 1 Test)",
                original_title="Planet Earth II (Phase 1 Test)",
                production_year=2016,
                synopsis="David Attenborough presents a documentary series exploring the world's most iconic habitats and fascinating animal behavior."
            )
            fest = FestivalModel(festival_id=fest_id, festival_name="Sundance Film Festival", country_code="US")
            bbc_dist = ProductionCompanyModel(company_id=distributor_id, company_name="BBC Studios Distribution", country_code="GB")
            session.add_all([doc, fest, bbc_dist])
            await session.flush()

            fest_ed = FestivalEditionModel(festival_edition_id=fest_ed_id, festival_id=fest_id, year=2017, edition_number=33)
            session.add(fest_ed)
            await session.flush()

            theme_nature = TitleThemeModel(title_id=doc_id, theme_id="NATURE")
            kw_survival = TitleKeywordModel(title_id=doc_id, keyword_id="SURVIVAL")
            fest_part = FestivalParticipationModel(
                participation_id=uuid.uuid4(),
                festival_edition_id=fest_ed_id,
                title_id=doc_id,
                section_name="Special Screenings"
            )
            title_dist = TitleCompanyModel(
                title_company_id=uuid.uuid4(),
                title_id=doc_id,
                company_id=distributor_id,
                role="DISTRIBUTOR"
            )

            session.add_all([theme_nature, kw_survival, fest_part, title_dist])
            await session.commit()

            detail = await canonical_repository.get_title_by_id(session, str(doc_id))
            self.assertIsNotNone(detail)
            self.assertEqual(detail.canonical_title, "Planet Earth II (Phase 1 Test)")
            self.assertEqual(detail.content_type, "DOCUMENTARY")
            self.assertEqual(len(detail.themes), 1)
            self.assertEqual(detail.themes[0].name, "Nature & Wildlife")
            self.assertEqual(len(detail.keywords), 1)
            self.assertEqual(detail.keywords[0].name, "survival")
            self.assertEqual(len(detail.festival_participations), 1)
            self.assertEqual(detail.festival_participations[0].festival_name, "Sundance Film Festival")
            self.assertEqual(detail.festival_participations[0].section_name, "Special Screenings")
            self.assertEqual(detail.companies[0].role, "DISTRIBUTOR")

    async def test_structural_separation_edition_vs_season(self):
        """Enforces Non-Negotiable rule: Edition is physical/theatrical cut, Season is episodic grouping."""
        async with self.SessionLocal() as session:
            dual_id = uuid.uuid4()
            
            title = TitleModel(
                title_id=dual_id,
                display_id="SER-P1-002",
                content_type_id="TV_SERIES",
                canonical_title="Hybrid Anthology",
                original_title="Hybrid Anthology",
                production_year=2021
            )
            session.add(title)
            await session.flush()
            
            # Season hierarchy
            season = SeasonModel(season_id=uuid.uuid4(), title_id=dual_id, season_number=1, season_name="Anthology S1")
            edition = EditionModel(edition_id=uuid.uuid4(), title_id=dual_id, edition_name="Unrated Extended Cut", runtime_minutes=75)
            session.add_all([season, edition])
            await session.flush()

            ep = EpisodeModel(episode_id=uuid.uuid4(), season_id=season.season_id, episode_number=1, episode_name="Pilot")
            release = ReleaseModel(release_id=uuid.uuid4(), edition_id=edition.edition_id, release_name="Blu-ray Release", release_type="PHYSICAL_BLURAY")
            session.add_all([ep, release])
            await session.commit()
            
            detail = await canonical_repository.get_title_by_id(session, str(dual_id))
            self.assertIsNotNone(detail)
            
            # Both hierarchies coexist cleanly without conflation
            self.assertEqual(len(detail.seasons), 1)
            self.assertEqual(detail.seasons[0].season_number, 1)
            self.assertEqual(len(detail.seasons[0].episodes), 1)
            
            self.assertEqual(len(detail.editions), 1)
            self.assertEqual(detail.editions[0].edition_name, "Unrated Extended Cut")
            self.assertEqual(len(detail.editions[0].releases), 1)
            self.assertEqual(detail.editions[0].releases[0].release_type, "PHYSICAL_BLURAY")
