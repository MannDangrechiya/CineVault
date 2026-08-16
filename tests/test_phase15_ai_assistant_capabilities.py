# CineVault OS — Phase 15: AI Assistant Capabilities Verification Tests
# Validates conversational search, title comparisons, marathon viewing plans, personal stats summaries, and privacy isolation

from unittest import IsolatedAsyncioTestCase
import uuid
import time
import base64
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.database import engine, get_db
from services.api.models.canonical import (
    TitleModel, ContentTypeModel, EditionModel, GenreModel, TitleGenreModel,
    PersonModel, CreditRoleModel, CreditModel, FranchiseModel, FranchiseEntryModel,
    ViewingOrderModel, ViewingOrderItemModel
)
from services.api.repositories.personal import personal_repository
from services.api.repositories.ai_assistant import ai_assistant_repository
from services.api.schemas.personal import WatchEventCreate, UserTitleStateUpdate, RatingCreate

def generate_mock_jwt(roles: list = None, sub: str = "018f4a00-0000-7000-8000-000000000099") -> str:
    if roles is None:
        roles = ["AuthenticatedUser"]
    header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    now = int(time.time())
    payload_dict = {
        "sub": sub,
        "iss": "http://localhost:8080/realms/cinevault-dev",
        "aud": "cinevault-api-gateway",
        "exp": now + 900,
        "iat": now,
        "realm_access": {"roles": roles}
    }
    payload = base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(b"mock_signature").decode().rstrip("=")
    return f"{header}.{payload}.{signature}"

class Phase15AIAssistantCapabilitiesTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 15 verification for advanced AI assistant capabilities and user privacy isolation."""

    async def asyncSetUp(self):
        self._conn = await engine.connect()
        self._outer_txn = await self._conn.begin()
        self.SessionLocal = async_sessionmaker(
            bind=self._conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        self.client = TestClient(app)

        self.user_a_id = str(uuid.uuid4())
        self.user_b_id = str(uuid.uuid4())
        self.jwt_a = generate_mock_jwt(["AuthenticatedUser"], sub=self.user_a_id)
        self.jwt_b = generate_mock_jwt(["AuthenticatedUser"], sub=self.user_b_id)
        self.headers_a = {"Authorization": f"Bearer {self.jwt_a}"}
        self.headers_b = {"Authorization": f"Bearer {self.jwt_b}"}

        async with self.SessionLocal() as session:
            movie_type = await session.get(ContentTypeModel, "movie")
            if not movie_type:
                session.add(ContentTypeModel(content_type_id="movie", type_name="Feature Film"))

            for g_id, g_name in [("sci_fi", "Sci-Fi"), ("mystery", "Mystery"), ("drama", "Drama")]:
                if not await session.get(GenreModel, g_id):
                    session.add(GenreModel(genre_id=g_id, name=g_name))

            for r_id, r_name, r_cat in [("DIRECTOR", "Director", "CREW"), ("ACTOR", "Actor", "CAST")]:
                if not await session.get(CreditRoleModel, r_id):
                    session.add(CreditRoleModel(credit_role_id=r_id, role_name=r_name, category=r_cat))

            # Director Person
            self.director_nolan = PersonModel(person_id=uuid.uuid4(), canonical_name="Christopher Nolan")
            session.add(self.director_nolan)
            await session.flush()

            # Film 1: Interstellar Odyssey
            self.film1 = TitleModel(
                title_id=uuid.uuid4(),
                display_id="MOV-AI-001",
                content_type_id="movie",
                canonical_title="Interstellar Odyssey",
                original_title="Interstellar Odyssey",
                production_year=2014
            )
            # Film 2: Quantum Oppenheimer
            self.film2 = TitleModel(
                title_id=uuid.uuid4(),
                display_id="MOV-AI-002",
                content_type_id="movie",
                canonical_title="Quantum Oppenheimer",
                original_title="Quantum Oppenheimer",
                production_year=2023
            )
            session.add_all([self.film1, self.film2])
            await session.flush()

            ed1 = EditionModel(edition_id=uuid.uuid4(), title_id=self.film1.title_id, edition_name="Theatrical", runtime_minutes=169, is_primary=True)
            ed2 = EditionModel(edition_id=uuid.uuid4(), title_id=self.film2.title_id, edition_name="Theatrical", runtime_minutes=180, is_primary=True)
            g1 = TitleGenreModel(title_id=self.film1.title_id, genre_id="sci_fi")
            g2 = TitleGenreModel(title_id=self.film2.title_id, genre_id="drama")
            c1 = CreditModel(credit_id=uuid.uuid4(), title_id=self.film1.title_id, person_id=self.director_nolan.person_id, credit_role_id="DIRECTOR")
            c2 = CreditModel(credit_id=uuid.uuid4(), title_id=self.film2.title_id, person_id=self.director_nolan.person_id, credit_role_id="DIRECTOR")

            # Franchise
            self.franchise = FranchiseModel(
                franchise_id=uuid.uuid4(),
                name="Nolan Cinematic Journey"
            )
            session.add(self.franchise)
            await session.flush()

            fe1 = FranchiseEntryModel(franchise_entry_id=uuid.uuid4(), franchise_id=self.franchise.franchise_id, title_id=self.film1.title_id, entry_type="CANONICAL")
            fe2 = FranchiseEntryModel(franchise_entry_id=uuid.uuid4(), franchise_id=self.franchise.franchise_id, title_id=self.film2.title_id, entry_type="CANONICAL")

            vo = ViewingOrderModel(
                viewing_order_id=uuid.uuid4(),
                franchise_id=self.franchise.franchise_id,
                order_name="Release Order",
                order_type="RELEASE_ORDER"
            )
            session.add(vo)
            await session.flush()

            item1 = ViewingOrderItemModel(item_id=uuid.uuid4(), viewing_order_id=vo.viewing_order_id, title_id=self.film1.title_id, position=1)
            item2 = ViewingOrderItemModel(item_id=uuid.uuid4(), viewing_order_id=vo.viewing_order_id, title_id=self.film2.title_id, position=2)

            session.add_all([ed1, ed2, g1, g2, c1, c2, fe1, fe2, item1, item2])
            await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_compare_titles_capability(self):
        """Capability: Comparative cinematic analysis between two works (genres, shared directors, runtimes)."""
        t1_id = str(self.film1.title_id)
        t2_id = str(self.film2.title_id)

        async with self.SessionLocal() as session:
            data = await ai_assistant_repository.compare_titles(db=session, title_id_1=t1_id, title_id_2=t2_id)

            self.assertEqual(data.title_1["canonical_title"], "Interstellar Odyssey")
            self.assertEqual(data.title_2["canonical_title"], "Quantum Oppenheimer")
            self.assertIn("Christopher Nolan", data.shared_directors)
            self.assertIn("Interstellar Odyssey", data.comparison_summary)

    async def test_build_viewing_plan_capability(self):
        """Capability: Builds structured marathon viewing sequence with estimated cumulative watch time."""
        f_id = str(self.franchise.franchise_id)

        async with self.SessionLocal() as session:
            data = await ai_assistant_repository.build_viewing_plan(db=session, franchise_id_or_keyword=f_id, order_mode="RELEASE_ORDER")

            self.assertEqual(data.viewing_order, "RELEASE_ORDER")
            self.assertEqual(data.total_titles, 2)
            self.assertEqual(data.total_runtime_minutes, 349)
            self.assertEqual(len(data.items), 2)
            self.assertEqual(data.items[0].canonical_title, "Interstellar Odyssey")
            self.assertEqual(data.items[1].canonical_title, "Quantum Oppenheimer")

    async def test_explain_personal_statistics_and_cross_user_isolation(self):
        """Capability & Privacy: Explains user's personal media patterns and strictly protects cross-user isolation."""
        async with self.SessionLocal() as session:
            # User A logs 1 watch event
            await personal_repository.create_watch_event(
                db=session, user_id=self.user_a_id,
                body=WatchEventCreate(title_id=str(self.film1.title_id), watched_at=datetime.now(timezone.utc).isoformat(), progress_percentage=100.0)
            )
            await session.commit()

            # Query stats for User A
            data_a = await ai_assistant_repository.explain_personal_statistics(db=session, user_id=self.user_a_id)
            self.assertEqual(data_a.user_id, self.user_a_id)
            self.assertEqual(data_a.total_titles, 1)
            self.assertGreater(data_a.total_watch_hours, 0.0)

            # Query stats for User B (must be 0, isolated from User A)
            data_b = await ai_assistant_repository.explain_personal_statistics(db=session, user_id=self.user_b_id)
            self.assertEqual(data_b.user_id, self.user_b_id)
            self.assertEqual(data_b.total_titles, 0)
            self.assertEqual(data_b.total_watch_hours, 0.0)
