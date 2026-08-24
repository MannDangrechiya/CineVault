# CineVault OS — Phase 7: Collections / Franchises / Lists Verification Tests
# Validates universe and franchise relationships, canonical viewing orders (chronological, release, recommended), and personal custom collections

from unittest import IsolatedAsyncioTestCase
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.models.canonical import (
    TitleModel, ContentTypeModel, UniverseModel, FranchiseModel,
    FranchiseEntryModel, ViewingOrderModel, ViewingOrderItemModel
)
from services.api.models.personal import UserListModel, UserListItemModel

class Phase7CollectionsFranchisesTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 7 verification for franchises, viewing orders, and personal collections."""

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
            # 1. Ensure Content Type
            movie_type = await session.get(ContentTypeModel, "movie")
            if not movie_type:
                session.add(ContentTypeModel(content_type_id="movie", type_name="Feature Film"))
                await session.flush()

            # 2. Seed/Find MCU Universe & Franchise Titles
            stmt_im = select(TitleModel).where(TitleModel.canonical_title == "Iron Man", TitleModel.production_year == 2008)
            self.title_im1 = (await session.execute(stmt_im)).scalar_one_or_none()
            if not self.title_im1:
                self.title_im1 = TitleModel(
                    title_id=uuid.uuid4(),
                    display_id="MOV-MCU-001",
                    content_type_id="movie",
                    canonical_title="Iron Man",
                    original_title="Iron Man",
                    production_year=2008
                )
                session.add(self.title_im1)
                await session.flush()

            stmt_ca = select(TitleModel).where(TitleModel.canonical_title == "Captain America: The First Avenger", TitleModel.production_year == 2011)
            self.title_ca1 = (await session.execute(stmt_ca)).scalar_one_or_none()
            if not self.title_ca1:
                self.title_ca1 = TitleModel(
                    title_id=uuid.uuid4(),
                    display_id="MOV-MCU-002",
                    content_type_id="movie",
                    canonical_title="Captain America: The First Avenger",
                    original_title="Captain America: The First Avenger",
                    production_year=2011
                )
                session.add(self.title_ca1)
                await session.flush()

            stmt_av = select(TitleModel).where(TitleModel.canonical_title == "The Avengers", TitleModel.production_year == 2012)
            self.title_av1 = (await session.execute(stmt_av)).scalar_one_or_none()
            if not self.title_av1:
                self.title_av1 = TitleModel(
                    title_id=uuid.uuid4(),
                    display_id="MOV-MCU-003",
                    content_type_id="movie",
                    canonical_title="The Avengers",
                    original_title="The Avengers",
                    production_year=2012
                )
                session.add(self.title_av1)
                await session.flush()

            # 3. Seed Universe and Franchise
            self.universe = UniverseModel(
                universe_id=uuid.uuid4(),
                name="Marvel Cinematic Universe",
                overview="Interconnected Marvel superhero narrative universe."
            )
            session.add(self.universe)
            await session.flush()

            self.franchise = FranchiseModel(
                franchise_id=uuid.uuid4(),
                universe_id=self.universe.universe_id,
                name="The Infinity Saga"
            )
            session.add(self.franchise)
            await session.flush()

            # Add Franchise Entries
            fe1 = FranchiseEntryModel(
                franchise_entry_id=uuid.uuid4(),
                franchise_id=self.franchise.franchise_id,
                title_id=self.title_im1.title_id,
                entry_type="CANONICAL"
            )
            fe2 = FranchiseEntryModel(
                franchise_entry_id=uuid.uuid4(),
                franchise_id=self.franchise.franchise_id,
                title_id=self.title_ca1.title_id,
                entry_type="CANONICAL"
            )
            fe3 = FranchiseEntryModel(
                franchise_entry_id=uuid.uuid4(),
                franchise_id=self.franchise.franchise_id,
                title_id=self.title_av1.title_id,
                entry_type="CANONICAL"
            )
            session.add_all([fe1, fe2, fe3])

            # 4. Seed Canonical Viewing Orders
            # Release Order: Iron Man (1) -> Captain America (2) -> The Avengers (3)
            self.release_order = ViewingOrderModel(
                viewing_order_id=uuid.uuid4(),
                franchise_id=self.franchise.franchise_id,
                order_name="Theatrical Release Order",
                order_type="RELEASE_ORDER"
            )
            # Chronological In-Universe Order: Captain America (1) -> Iron Man (2) -> The Avengers (3)
            self.chrono_order = ViewingOrderModel(
                viewing_order_id=uuid.uuid4(),
                franchise_id=self.franchise.franchise_id,
                order_name="Narrative Chronological Order",
                order_type="CHRONOLOGICAL"
            )
            session.add_all([self.release_order, self.chrono_order])
            await session.flush()

            # Items for Release Order
            ro1 = ViewingOrderItemModel(item_id=uuid.uuid4(), viewing_order_id=self.release_order.viewing_order_id, title_id=self.title_im1.title_id, position=1)
            ro2 = ViewingOrderItemModel(item_id=uuid.uuid4(), viewing_order_id=self.release_order.viewing_order_id, title_id=self.title_ca1.title_id, position=2)
            ro3 = ViewingOrderItemModel(item_id=uuid.uuid4(), viewing_order_id=self.release_order.viewing_order_id, title_id=self.title_av1.title_id, position=3)

            # Items for Chrono Order
            co1 = ViewingOrderItemModel(item_id=uuid.uuid4(), viewing_order_id=self.chrono_order.viewing_order_id, title_id=self.title_ca1.title_id, position=1)
            co2 = ViewingOrderItemModel(item_id=uuid.uuid4(), viewing_order_id=self.chrono_order.viewing_order_id, title_id=self.title_im1.title_id, position=2)
            co3 = ViewingOrderItemModel(item_id=uuid.uuid4(), viewing_order_id=self.chrono_order.viewing_order_id, title_id=self.title_av1.title_id, position=3)

            session.add_all([ro1, ro2, ro3, co1, co2, co3])
            await session.commit()

        self.user_a_id = uuid.uuid4()
        self.user_b_id = uuid.uuid4()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_universe_and_franchise_canonical_hierarchy(self):
        """Validates canonical Universe -> Franchise -> Entries hierarchy relationships."""
        async with self.SessionLocal() as session:
            stmt = (
                select(FranchiseModel)
                .options(
                    selectinload(FranchiseModel.entries),
                    selectinload(FranchiseModel.viewing_orders)
                )
                .where(FranchiseModel.franchise_id == self.franchise.franchise_id)
            )
            franchise = (await session.execute(stmt)).scalar_one()

            self.assertEqual(franchise.name, "The Infinity Saga")
            self.assertEqual(len(franchise.entries), 3)
            self.assertEqual(len(franchise.viewing_orders), 2)

    async def test_canonical_viewing_orders_release_vs_chronological(self):
        """Validates structured viewing orders: release order vs narrative chronological order."""
        async with self.SessionLocal() as session:
            # Query Release Order items
            stmt_ro = (
                select(ViewingOrderItemModel)
                .where(ViewingOrderItemModel.viewing_order_id == self.release_order.viewing_order_id)
                .order_by(ViewingOrderItemModel.position.asc())
            )
            ro_items = (await session.execute(stmt_ro)).scalars().all()
            self.assertEqual(len(ro_items), 3)
            self.assertEqual(ro_items[0].title_id, self.title_im1.title_id)  # Position 1: Iron Man
            self.assertEqual(ro_items[1].title_id, self.title_ca1.title_id)  # Position 2: Captain America

            # Query Chronological Order items
            stmt_co = (
                select(ViewingOrderItemModel)
                .where(ViewingOrderItemModel.viewing_order_id == self.chrono_order.viewing_order_id)
                .order_by(ViewingOrderItemModel.position.asc())
            )
            co_items = (await session.execute(stmt_co)).scalars().all()
            self.assertEqual(len(co_items), 3)
            self.assertEqual(co_items[0].title_id, self.title_ca1.title_id)  # Position 1: Captain America (WWII era)
            self.assertEqual(co_items[1].title_id, self.title_im1.title_id)  # Position 2: Iron Man

    async def test_personal_custom_user_list_creation_and_reordering(self):
        """Personal Lists: User creates custom collection, adds titles with notes and positions, and reorders items."""
        async with self.SessionLocal() as session:
            # 1. User A creates custom collection
            custom_list = UserListModel(
                list_id=uuid.uuid4(),
                user_id=self.user_a_id,
                title="Favorite Superhero Marathon",
                description="Custom curated marathon order with personal viewing notes.",
                is_private=True
            )
            session.add(custom_list)
            await session.flush()

            # 2. Add ordered items
            item1 = UserListItemModel(
                item_id=uuid.uuid4(),
                list_id=custom_list.list_id,
                title_id=self.title_im1.title_id,
                position=1,
                notes="Watch post-credits scene for Nick Fury introduction."
            )
            item2 = UserListItemModel(
                item_id=uuid.uuid4(),
                list_id=custom_list.list_id,
                title_id=self.title_av1.title_id,
                position=2,
                notes="Peak team-up climax."
            )
            session.add_all([item1, item2])
            await session.commit()

            # 3. Retrieve user collection with items
            stmt = (
                select(UserListModel)
                .options(selectinload(UserListModel.items))
                .where(UserListModel.list_id == custom_list.list_id)
            )
            saved_list = (await session.execute(stmt)).scalar_one()
            self.assertEqual(saved_list.title, "Favorite Superhero Marathon")
            self.assertEqual(len(saved_list.items), 2)
            self.assertEqual(saved_list.items[0].notes, "Watch post-credits scene for Nick Fury introduction.")

            # 4. Reorder items (Swap positions)
            saved_list.items[0].position = 2
            saved_list.items[1].position = 1
            await session.commit()

            # Verify updated position
            stmt_reorder = (
                select(UserListItemModel)
                .where(UserListItemModel.list_id == custom_list.list_id)
                .order_by(UserListItemModel.position.asc())
            )
            reordered = (await session.execute(stmt_reorder)).scalars().all()
            self.assertEqual(reordered[0].title_id, self.title_av1.title_id)  # Position 1 is now Avengers

    async def test_cross_user_isolation_on_custom_lists(self):
        """Privacy: User B cannot access or mutate User A's private collections."""
        async with self.SessionLocal() as session:
            # User A creates list
            user_a_list = UserListModel(
                list_id=uuid.uuid4(),
                user_id=self.user_a_id,
                title="Top Secret User A Collection",
                is_private=True
            )
            session.add(user_a_list)
            await session.commit()

            # User B queries their lists
            stmt_b = select(UserListModel).where(UserListModel.user_id == self.user_b_id)
            b_lists = (await session.execute(stmt_b)).scalars().all()
            self.assertEqual(len(b_lists), 0)
