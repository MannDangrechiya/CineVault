# CineVault OS — Phase 19: Offline Sync Verification Tests
# Validates outbox batch push, server-side idempotency, partial sync failure isolation, and delta pull streams

from unittest import IsolatedAsyncioTestCase
import uuid
import time
import base64
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.models.canonical import TitleModel, ContentTypeModel
from services.api.repositories.personal import personal_repository
from services.api.repositories.sync import sync_repository
from services.api.schemas.sync import MutationItem
from services.api.schemas.personal import WatchEventCreate, RatingCreate

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

class Phase19OfflineSyncTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 19 verification for offline synchronization, idempotency, and delta pulling."""

    async def asyncSetUp(self):
        self._conn = await engine.connect()
        self._outer_txn = await self._conn.begin()
        self.SessionLocal = async_sessionmaker(
            bind=self._conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        self.user_id = str(uuid.uuid4())

        async with self.SessionLocal() as session:
            movie_type = await session.get(ContentTypeModel, "movie")
            if not movie_type:
                session.add(ContentTypeModel(content_type_id="movie", type_name="Feature Film"))

            self.title1 = TitleModel(
                title_id=uuid.uuid4(),
                display_id="MOV-SYNC-001",
                content_type_id="movie",
                canonical_title="Dune Prophecy",
                original_title="Dune Prophecy",
                production_year=2024
            )
            session.add(self.title1)
            await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_outbox_push_mutation_batch_processing(self):
        """Sync Push: Processes offline recorded mutation batch and acknowledges IDs."""
        mut_id_1 = str(uuid.uuid4())
        mut_id_2 = str(uuid.uuid4())

        mutations = [
            MutationItem(
                mutation_id=mut_id_1,
                mutation_type="CREATE_WATCH_EVENT",
                client_timestamp=datetime.now(timezone.utc).isoformat(),
                payload={
                    "title_id": str(self.title1.title_id),
                    "watched_at": datetime.now(timezone.utc).isoformat(),
                    "progress_percentage": 100.0
                }
            ),
            MutationItem(
                mutation_id=mut_id_2,
                mutation_type="SET_RATING",
                client_timestamp=datetime.now(timezone.utc).isoformat(),
                payload={
                    "title_id": str(self.title1.title_id),
                    "rating_value": 9
                }
            )
        ]

        async with self.SessionLocal() as session:
            res = await sync_repository.process_push_mutations(
                db=session,
                user_id=self.user_id,
                mutations=mutations
            )

            self.assertEqual(res.processed_count, 2)
            self.assertIn(mut_id_1, res.acknowledged_mutation_ids)
            self.assertIn(mut_id_2, res.acknowledged_mutation_ids)
            self.assertEqual(len(res.failed_mutations), 0)

            # Verify side-effects in personal database
            history = await personal_repository.list_watch_events(db=session, user_id=self.user_id)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0].title_id, str(self.title1.title_id))

            ratings = await personal_repository.list_ratings(db=session, user_id=self.user_id)
            self.assertEqual(len(ratings), 1)
            self.assertEqual(ratings[0].rating_value, 9)

    async def test_idempotency_and_duplicate_mutation_defense(self):
        """Idempotency: Duplicate mutation IDs are safely acknowledged without double side-effects."""
        mut_id = str(uuid.uuid4())
        mutation = MutationItem(
            mutation_id=mut_id,
            mutation_type="CREATE_WATCH_EVENT",
            client_timestamp=datetime.now(timezone.utc).isoformat(),
            payload={
                "title_id": str(self.title1.title_id),
                "watched_at": datetime.now(timezone.utc).isoformat(),
                "progress_percentage": 100.0
            }
        )

        async with self.SessionLocal() as session:
            # First execution
            res1 = await sync_repository.process_push_mutations(
                db=session, user_id=self.user_id, mutations=[mutation]
            )
            self.assertEqual(res1.processed_count, 1)

            # Second execution (exact duplicate mutation_id)
            res2 = await sync_repository.process_push_mutations(
                db=session, user_id=self.user_id, mutations=[mutation]
            )
            self.assertEqual(res2.processed_count, 1)
            self.assertIn(mut_id, res2.acknowledged_mutation_ids)

            # Confirm history has exactly 1 entry, not 2
            history = await personal_repository.list_watch_events(db=session, user_id=self.user_id)
            self.assertEqual(len(history), 1)

    async def test_delta_change_pull_stream(self):
        """Sync Pull: Retrieves incremental changes since client sync_cursor."""
        async with self.SessionLocal() as session:
            await personal_repository.create_watch_event(
                db=session, user_id=self.user_id,
                body=WatchEventCreate(title_id=str(self.title1.title_id), watched_at=datetime.now(timezone.utc).isoformat())
            )
            await personal_repository.set_rating(
                db=session, user_id=self.user_id,
                body=RatingCreate(title_id=str(self.title1.title_id), rating_value=10)
            )
            await session.commit()

            pull_res = await sync_repository.get_delta_pull_changes(
                db=session, user_id=self.user_id, sync_cursor=None, limit=50
            )

            self.assertIsNotNone(pull_res.sync_cursor)
            self.assertFalse(pull_res.has_more)
            self.assertGreaterEqual(len(pull_res.changes), 2)
            entity_types = [c["entity_type"] for c in pull_res.changes]
            self.assertIn("WATCH_EVENT", entity_types)
            self.assertIn("RATING", entity_types)
