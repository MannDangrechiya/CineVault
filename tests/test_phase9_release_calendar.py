# CineVault OS — Phase 9: Release Calendar Verification Tests
# Validates release date tracking across theatrical, streaming, regional, TV broadcast, digital, physical, festival releases, and Title vs Edition vs Release separation

from unittest import IsolatedAsyncioTestCase
import uuid
from datetime import date, timedelta
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.models.canonical import (
    TitleModel, EditionModel, ReleaseModel, ContentTypeModel
)

class Phase9ReleaseCalendarTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 9 verification for release calendar tracking and Title-Edition-Release separation."""

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
            movie_type = await session.get(ContentTypeModel, "movie")
            if not movie_type:
                session.add(ContentTypeModel(content_type_id="movie", type_name="Feature Film"))
                await session.flush()

            # 2. Seed/Find Canonical Title (Parasite)
            stmt_p = select(TitleModel).where(TitleModel.canonical_title == "Parasite", TitleModel.production_year == 2019)
            self.parasite = (await session.execute(stmt_p)).scalar_one_or_none()
            if not self.parasite:
                self.parasite = TitleModel(
                    title_id=uuid.uuid4(),
                    display_id="MOV-REL-001",
                    content_type_id="movie",
                    canonical_title="Parasite",
                    original_title="기생충",
                    production_year=2019
                )
                session.add(self.parasite)
                await session.flush()

            # 3. Find or Seed Editions: Theatrical Cut vs Black-and-White Edition
            stmt_ed = select(EditionModel).where(EditionModel.title_id == self.parasite.title_id)
            existing_eds = (await session.execute(stmt_ed)).scalars().all()

            self.theatrical_edition = next((e for e in existing_eds if e.is_primary), None)
            if not self.theatrical_edition:
                self.theatrical_edition = EditionModel(
                    edition_id=uuid.uuid4(),
                    title_id=self.parasite.title_id,
                    edition_name="Original Theatrical Cut",
                    runtime_minutes=132,
                    is_primary=True
                )
                session.add(self.theatrical_edition)
                await session.flush()

            self.bw_edition = next((e for e in existing_eds if not e.is_primary and "Black" in (e.edition_name or "")), None)
            if not self.bw_edition:
                self.bw_edition = EditionModel(
                    edition_id=uuid.uuid4(),
                    title_id=self.parasite.title_id,
                    edition_name="Black-and-White Edition",
                    runtime_minutes=132,
                    is_primary=False
                )
                session.add(self.bw_edition)
                await session.flush()

            # 4. Seed/Find Future Upcoming Film (Avatar: Fire and Ash)
            stmt_f = select(TitleModel).where(TitleModel.canonical_title == "Avatar: Fire and Ash", TitleModel.production_year == 2025)
            self.future_film = (await session.execute(stmt_f)).scalar_one_or_none()
            if not self.future_film:
                self.future_film = TitleModel(
                    title_id=uuid.uuid4(),
                    display_id="MOV-FUT-001",
                    content_type_id="movie",
                    canonical_title="Avatar: Fire and Ash",
                    original_title="Avatar: Fire and Ash",
                    production_year=2025
                )
                session.add(self.future_film)
                await session.flush()

            stmt_fe = select(EditionModel).where(EditionModel.title_id == self.future_film.title_id)
            self.future_edition = (await session.execute(stmt_fe)).scalars().first()
            if not self.future_edition:
                self.future_edition = EditionModel(
                    edition_id=uuid.uuid4(),
                    title_id=self.future_film.title_id,
                    edition_name="Theatrical Cut",
                    runtime_minutes=190,
                    is_primary=True
                )
                session.add(self.future_edition)

            await session.commit()

        self.today = date.today()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_title_edition_release_separation(self):
        """Constraint: Title, Edition, and Release are three distinct architectural entities and must not be conflated."""
        async with self.SessionLocal() as session:
            # Add Releases for Theatrical Edition
            rel_cannes = ReleaseModel(
                release_id=uuid.uuid4(),
                edition_id=self.theatrical_edition.edition_id,
                release_name="Cannes Film Festival Premiere",
                release_type="FESTIVAL",
                release_date=date(2019, 5, 21),
                country_code="FR"
            )
            rel_kr = ReleaseModel(
                release_id=uuid.uuid4(),
                edition_id=self.theatrical_edition.edition_id,
                release_name="South Korea Theatrical Distribution",
                release_type="THEATRICAL",
                release_date=date(2019, 5, 30),
                country_code="KR"
            )
            rel_us = ReleaseModel(
                release_id=uuid.uuid4(),
                edition_id=self.theatrical_edition.edition_id,
                release_name="United States Limited Theatrical",
                release_type="THEATRICAL",
                release_date=date(2019, 10, 11),
                country_code="US"
            )
            rel_bluray = ReleaseModel(
                release_id=uuid.uuid4(),
                edition_id=self.theatrical_edition.edition_id,
                release_name="Criterion Collection 4K UHD",
                release_type="PHYSICAL",
                release_date=date(2020, 10, 27),
                country_code="US"
            )

            # Add Release for Black-and-White Edition
            rel_bw_fest = ReleaseModel(
                release_id=uuid.uuid4(),
                edition_id=self.bw_edition.edition_id,
                release_name="Rotterdam Film Festival B&W Premiere",
                release_type="FESTIVAL",
                release_date=date(2020, 1, 29),
                country_code="NL"
            )

            session.add_all([rel_cannes, rel_kr, rel_us, rel_bluray, rel_bw_fest])
            await session.commit()

            # Query complete Title hierarchy with selectinload
            stmt = (
                select(TitleModel)
                .options(
                    selectinload(TitleModel.editions).selectinload(EditionModel.releases)
                )
                .where(TitleModel.title_id == self.parasite.title_id)
            )
            title = (await session.execute(stmt)).scalar_one()

            # Verify: 1 Title -> >= 2 Editions -> Multiple Releases
            self.assertGreaterEqual(len(title.editions), 2)
            ed_map = {e.edition_id: e for e in title.editions}

            theatrical = ed_map[self.theatrical_edition.edition_id]
            self.assertGreaterEqual(len(theatrical.releases), 4)

            bw = ed_map[self.bw_edition.edition_id]
            self.assertGreaterEqual(len(bw.releases), 1)
            self.assertTrue(any(r.release_type == "FESTIVAL" for r in bw.releases))

    async def test_release_types_coverage(self):
        """Validates all required release types: theatrical, streaming, regional, TV broadcast, digital, physical, festival."""
        async with self.SessionLocal() as session:
            ed_id = self.theatrical_edition.edition_id
            types = [
                ("THEATRICAL", "US Theatrical Release", "US", date(2019, 10, 11)),
                ("STREAMING", "Hulu Exclusive Streaming Launch", "US", date(2020, 4, 8)),
                ("REGIONAL", "UK Regional Cinema Tour", "GB", date(2020, 2, 7)),
                ("TV_BROADCAST", "KBS1 Television Premiere", "KR", date(2020, 9, 30)),
                ("DIGITAL", "Apple TV & Prime Video VOD Release", "US", date(2020, 1, 14)),
                ("PHYSICAL", "Standard Blu-ray Edition", "US", date(2020, 1, 28)),
                ("FESTIVAL", "Sydney Film Festival", "AU", date(2019, 6, 16))
            ]

            for r_type, r_name, c_code, r_date in types:
                session.add(
                    ReleaseModel(
                        release_id=uuid.uuid4(),
                        edition_id=ed_id,
                        release_name=r_name,
                        release_type=r_type,
                        country_code=c_code,
                        release_date=r_date
                    )
                )
            await session.commit()

            stmt = select(ReleaseModel).where(ReleaseModel.edition_id == ed_id)
            releases = (await session.execute(stmt)).scalars().all()
            found_types = {r.release_type for r in releases}
            self.assertTrue({"THEATRICAL", "STREAMING", "REGIONAL", "TV_BROADCAST", "DIGITAL", "PHYSICAL", "FESTIVAL"}.issubset(found_types))

    async def test_temporal_calendar_queries_future_vs_historical(self):
        """Calendar Engine: Query upcoming future releases vs historical releases and regional calendars."""
        async with self.SessionLocal() as session:
            future_date_us = self.today + timedelta(days=120)
            future_date_kr = self.today + timedelta(days=118)

            rel_future_us = ReleaseModel(
                release_id=uuid.uuid4(),
                edition_id=self.future_edition.edition_id,
                release_name="Avatar 3 North America Theatrical Release",
                release_type="THEATRICAL",
                release_date=future_date_us,
                country_code="US"
            )
            rel_future_kr = ReleaseModel(
                release_id=uuid.uuid4(),
                edition_id=self.future_edition.edition_id,
                release_name="Avatar 3 South Korea Theatrical Release",
                release_type="THEATRICAL",
                release_date=future_date_kr,
                country_code="KR"
            )
            session.add_all([rel_future_us, rel_future_kr])
            await session.commit()

            # 1. Query Upcoming Future Release Calendar: release_date >= today
            stmt_future = (
                select(ReleaseModel)
                .where(ReleaseModel.release_date >= self.today)
                .order_by(ReleaseModel.release_date.asc())
            )
            upcoming = (await session.execute(stmt_future)).scalars().all()
            self.assertTrue(any(r.release_id == rel_future_us.release_id for r in upcoming))
            self.assertTrue(any(r.release_id == rel_future_kr.release_id for r in upcoming))

            # 2. Query Regional Calendar for KR
            stmt_kr = (
                select(ReleaseModel)
                .where(
                    and_(
                        ReleaseModel.country_code == "KR",
                        ReleaseModel.release_date >= self.today
                    )
                )
            )
            kr_upcoming = (await session.execute(stmt_kr)).scalars().all()
            self.assertTrue(any(r.release_id == rel_future_kr.release_id for r in kr_upcoming))
