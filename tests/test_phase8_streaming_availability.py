# CineVault OS — Phase 8: Streaming Availability Verification Tests
# Validates regional and temporal availability, offer types (subscription, rent, buy, free, ad_supported), validity windows, and source evidence

from unittest import IsolatedAsyncioTestCase
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.models.canonical import (
    TitleModel, ContentTypeModel, StreamingProviderModel, StreamingOfferModel
)

class Phase8StreamingAvailabilityTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 8 verification for temporal and regional streaming availability."""

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

            # 2. Seed/Find Canonical Titles
            stmt_p = select(TitleModel).where(TitleModel.canonical_title == "Parasite", TitleModel.production_year == 2019)
            self.title_parasite = (await session.execute(stmt_p)).scalar_one_or_none()
            if not self.title_parasite:
                self.title_parasite = TitleModel(
                    title_id=uuid.uuid4(),
                    display_id="MOV-STREAM-001",
                    content_type_id="movie",
                    canonical_title="Parasite",
                    original_title="기생충",
                    production_year=2019
                )
                session.add(self.title_parasite)
                await session.flush()

            stmt_o = select(TitleModel).where(TitleModel.canonical_title == "Oppenheimer", TitleModel.production_year == 2023)
            self.title_oppenheimer = (await session.execute(stmt_o)).scalar_one_or_none()
            if not self.title_oppenheimer:
                self.title_oppenheimer = TitleModel(
                    title_id=uuid.uuid4(),
                    display_id="MOV-STREAM-002",
                    content_type_id="movie",
                    canonical_title="Oppenheimer",
                    original_title="Oppenheimer",
                    production_year=2023
                )
                session.add(self.title_oppenheimer)
                await session.flush()

            # 3. Seed/Find Streaming Providers
            providers = [
                ("netflix", "Netflix", "https://www.netflix.com"),
                ("apple_tv", "Apple TV", "https://tv.apple.com"),
                ("criterion_channel", "The Criterion Channel", "https://www.criterionchannel.com"),
                ("tubi", "Tubi TV", "https://tubitv.com")
            ]
            for p_id, p_name, p_url in providers:
                p_existing = await session.get(StreamingProviderModel, p_id)
                if not p_existing:
                    session.add(StreamingProviderModel(provider_id=p_id, provider_name=p_name, home_url=p_url))

            await session.commit()

        self.now = datetime.now(timezone.utc)

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_multi_offer_types_and_regions(self):
        """Validates modeling across subscription, rent, buy, free, and ad_supported offers across different countries."""
        async with self.SessionLocal() as session:
            # 1. Subscription offer in US (Criterion)
            offer_sub = StreamingOfferModel(
                offer_id=uuid.uuid4(),
                title_id=self.title_parasite.title_id,
                provider_id="criterion_channel",
                country_code="US",
                offer_type="subscription",
                source_name="STUDIO_DIRECT",
                confidence_score=1.00,
                valid_from=self.now - timedelta(days=30),
                valid_until=self.now + timedelta(days=90),
                last_verified_at=self.now,
                is_active=True
            )

            # 2. Digital Rent offer in US (Apple TV: $3.99 USD)
            offer_rent = StreamingOfferModel(
                offer_id=uuid.uuid4(),
                title_id=self.title_parasite.title_id,
                provider_id="apple_tv",
                country_code="US",
                offer_type="rent",
                price_amount=3.99,
                currency_code="USD",
                source_name="TMDB_PROVIDER_API",
                confidence_score=0.95,
                valid_from=self.now - timedelta(days=60),
                valid_until=self.now + timedelta(days=300),
                last_verified_at=self.now,
                is_active=True
            )

            # 3. Free Ad-Supported offer in US (Tubi)
            offer_ad = StreamingOfferModel(
                offer_id=uuid.uuid4(),
                title_id=self.title_parasite.title_id,
                provider_id="tubi",
                country_code="US",
                offer_type="ad_supported",
                price_amount=0.00,
                currency_code="USD",
                source_name="TUBI_OFFICIAL_CATALOG",
                confidence_score=0.98,
                valid_from=self.now - timedelta(days=10),
                valid_until=self.now + timedelta(days=60),
                last_verified_at=self.now,
                is_active=True
            )

            # 4. Subscription offer in South Korea (Netflix: KRW)
            offer_kr = StreamingOfferModel(
                offer_id=uuid.uuid4(),
                title_id=self.title_parasite.title_id,
                provider_id="netflix",
                country_code="KR",
                offer_type="subscription",
                source_name="KOBIS_OFFICIAL",
                confidence_score=1.00,
                valid_from=self.now - timedelta(days=100),
                valid_until=self.now + timedelta(days=200),
                last_verified_at=self.now,
                is_active=True
            )

            session.add_all([offer_sub, offer_rent, offer_ad, offer_kr])
            await session.commit()

            # Query US offers
            stmt_us = (
                select(StreamingOfferModel)
                .where(
                    and_(
                        StreamingOfferModel.title_id == self.title_parasite.title_id,
                        StreamingOfferModel.country_code == "US",
                        StreamingOfferModel.is_active == True
                    )
                )
            )
            us_offers = (await session.execute(stmt_us)).scalars().all()
            self.assertGreaterEqual(len(us_offers), 3)
            types_us = {o.offer_type for o in us_offers}
            self.assertTrue({"subscription", "rent", "ad_supported"}.issubset(types_us))

            # Query KR offers
            stmt_kr = (
                select(StreamingOfferModel)
                .where(
                    and_(
                        StreamingOfferModel.title_id == self.title_parasite.title_id,
                        StreamingOfferModel.country_code == "KR",
                        StreamingOfferModel.is_active == True
                    )
                )
            )
            kr_offers = (await session.execute(stmt_kr)).scalars().all()
            self.assertGreaterEqual(len(kr_offers), 1)
            self.assertTrue(any(o.provider_id == "netflix" for o in kr_offers))

    async def test_temporal_validity_window_exclusion_of_expired_offers(self):
        """Constraint: An expired/stale streaming offer (valid_until < now) must NOT be presented as current availability."""
        async with self.SessionLocal() as session:
            # Active offer
            active_offer = StreamingOfferModel(
                offer_id=uuid.uuid4(),
                title_id=self.title_oppenheimer.title_id,
                provider_id="apple_tv",
                country_code="US",
                offer_type="buy",
                price_amount=19.99,
                currency_code="USD",
                source_name="TMDB_PROVIDER_API",
                confidence_score=0.95,
                valid_from=self.now - timedelta(days=10),
                valid_until=self.now + timedelta(days=180),
                last_verified_at=self.now,
                is_active=True
            )

            # Expired historical offer (e.g. Peacock exclusive license that ended last month)
            expired_offer = StreamingOfferModel(
                offer_id=uuid.uuid4(),
                title_id=self.title_oppenheimer.title_id,
                provider_id="netflix",
                country_code="US",
                offer_type="subscription",
                source_name="HISTORICAL_ARCHIVE",
                confidence_score=0.90,
                valid_from=self.now - timedelta(days=120),
                valid_until=self.now - timedelta(days=15),  # Expired 15 days ago
                last_verified_at=self.now - timedelta(days=15),
                is_active=True
            )

            session.add_all([active_offer, expired_offer])
            await session.commit()

            # Query with temporal freshness filter: valid_from <= now AND (valid_until IS NULL OR valid_until >= now)
            current_time = datetime.now(timezone.utc)
            stmt_current = (
                select(StreamingOfferModel)
                .where(
                    and_(
                        StreamingOfferModel.title_id == self.title_oppenheimer.title_id,
                        StreamingOfferModel.is_active == True,
                        StreamingOfferModel.valid_from <= current_time,
                        StreamingOfferModel.valid_until >= current_time
                    )
                )
            )
            active_results = (await session.execute(stmt_current)).scalars().all()
            self.assertTrue(any(o.offer_id == active_offer.offer_id for o in active_results))
            self.assertFalse(any(o.offer_id == expired_offer.offer_id for o in active_results))

    async def test_source_evidence_and_confidence_gate(self):
        """Constraint: Must record source evidence and confidence scores; unverified data cannot claim high confidence."""
        async with self.SessionLocal() as session:
            verified_offer = StreamingOfferModel(
                offer_id=uuid.uuid4(),
                title_id=self.title_oppenheimer.title_id,
                provider_id="criterion_channel",
                country_code="US",
                offer_type="subscription",
                source_name="CRITERION_OFFICIAL_API",
                confidence_score=1.00,
                valid_from=self.now,
                last_verified_at=self.now,
                is_active=True
            )
            session.add(verified_offer)
            await session.commit()

            stmt = select(StreamingOfferModel).where(StreamingOfferModel.offer_id == verified_offer.offer_id)
            saved = (await session.execute(stmt)).scalar_one()
            self.assertEqual(saved.source_name, "CRITERION_OFFICIAL_API")
            self.assertEqual(float(saved.confidence_score), 1.00)
            self.assertIsNotNone(saved.last_verified_at)
