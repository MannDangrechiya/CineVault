# CineVault OS — Phase 17: Import / Export Verification Tests
# Validates full personal data export, import identity matching, conflict detection/preview, and controlled apply

from unittest import IsolatedAsyncioTestCase
import uuid
import time
import base64
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.database import engine
from services.api.models.canonical import TitleModel, ContentTypeModel
from services.api.models.personal import (
    WatchEventModel, RatingModel, UserTitleStateModel, NoteModel, UserListModel, UserListItemModel
)
from services.api.repositories.personal import personal_repository
from services.api.schemas.personal import (
    WatchEventCreate, RatingCreate, UserTitleStateUpdate, NoteCreate,
    ImportItemPayload, ImportConflictStrategyEnum
)

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

class Phase17ImportExportTestCase(IsolatedAsyncioTestCase):
    """Executes complete Phase 17 verification for personal data export, validation, conflict preview, and controlled import."""

    async def asyncSetUp(self):
        self._conn = await engine.connect()
        self._outer_txn = await self._conn.begin()
        self.SessionLocal = async_sessionmaker(
            bind=self._conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        self.user_a_id = str(uuid.uuid4())
        self.user_b_id = str(uuid.uuid4())

        async with self.SessionLocal() as session:
            movie_type = await session.get(ContentTypeModel, "movie")
            if not movie_type:
                session.add(ContentTypeModel(content_type_id="movie", type_name="Feature Film"))

            self.title1 = TitleModel(
                title_id=uuid.uuid4(),
                display_id="MOV-EXP-001",
                content_type_id="movie",
                canonical_title="Cyberpunk 2099",
                original_title="Cyberpunk 2099",
                production_year=2025
            )
            self.title2 = TitleModel(
                title_id=uuid.uuid4(),
                display_id="MOV-EXP-002",
                content_type_id="movie",
                canonical_title="Solaris Reborn",
                original_title="Solaris Reborn",
                production_year=2026
            )
            session.add_all([self.title1, self.title2])
            await session.commit()

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    async def test_full_personal_data_export(self):
        """Export: Generates comprehensive export archive of user's personal media data."""
        async with self.SessionLocal() as session:
            # Seed User A data
            await personal_repository.create_watch_event(
                db=session, user_id=self.user_a_id,
                body=WatchEventCreate(title_id=str(self.title1.title_id), watched_at=datetime.now(timezone.utc).isoformat(), notes="First viewing")
            )
            await personal_repository.set_rating(
                db=session, user_id=self.user_a_id,
                body=RatingCreate(title_id=str(self.title1.title_id), rating_value=9)
            )
            await personal_repository.update_user_title_state(
                db=session, user_id=self.user_a_id, title_id=str(self.title1.title_id),
                body=UserTitleStateUpdate(manual_status_override="COMPLETED", is_favorite=True)
            )
            await personal_repository.create_note(
                db=session, user_id=self.user_a_id,
                body=NoteCreate(title_id=str(self.title1.title_id), note_text="Masterpiece visual design")
            )
            await session.commit()

            export_res = await personal_repository.export_user_data(db=session, user_id=self.user_a_id)

            self.assertEqual(export_res.user_id, self.user_a_id)
            self.assertEqual(len(export_res.watch_history), 1)
            self.assertEqual(len(export_res.ratings), 1)
            self.assertEqual(export_res.ratings[0]["rating_value"], 9)
            self.assertEqual(len(export_res.user_title_states), 1)
            self.assertTrue(export_res.user_title_states[0]["is_favorite"])
            self.assertEqual(len(export_res.private_notes), 1)

    async def test_import_validation_and_conflict_preview(self):
        """Import Preview: Validates match rates and detects conflicting existing ratings/states."""
        async with self.SessionLocal() as session:
            # Seed existing rating of 8 for title1
            await personal_repository.set_rating(
                db=session, user_id=self.user_a_id,
                body=RatingCreate(title_id=str(self.title1.title_id), rating_value=8)
            )
            await session.commit()

            import_payload = [
                # Title 1: matches existing title, but provides conflicting rating of 10
                ImportItemPayload(
                    canonical_title="Cyberpunk 2099",
                    production_year=2025,
                    rating_value=10,
                    manual_status_override="COMPLETED"
                ),
                # Title 2: matches existing title 2 with new watch event
                ImportItemPayload(
                    canonical_title="Solaris Reborn",
                    production_year=2026,
                    watched_at=datetime.now(timezone.utc).isoformat(),
                    rating_value=9
                ),
                # Title 3: Unknown title
                ImportItemPayload(
                    canonical_title="Unknown Unreleased Odyssey",
                    production_year=2099
                )
            ]

            preview = await personal_repository.preview_user_import(db=session, user_id=self.user_a_id, items=import_payload)

            self.assertEqual(preview.total_items, 3)
            self.assertEqual(preview.matched_titles, 2)
            self.assertEqual(preview.unmatched_titles, 1)
            self.assertEqual(preview.conflicts_count, 1)
            self.assertEqual(preview.conflicts[0].field_name, "rating_value")
            self.assertEqual(preview.conflicts[0].existing_value, 8)
            self.assertEqual(preview.conflicts[0].imported_value, 10)

    async def test_controlled_import_apply_with_conflict_strategies(self):
        """Import Apply: Respects user conflict strategy and never silently overwrites data."""
        async with self.SessionLocal() as session:
            # Seed initial rating of 7
            await personal_repository.set_rating(
                db=session, user_id=self.user_a_id,
                body=RatingCreate(title_id=str(self.title1.title_id), rating_value=7)
            )
            await session.commit()

            import_items = [
                ImportItemPayload(
                    title_id=str(self.title1.title_id),
                    rating_value=10,
                    is_favorite=True
                )
            ]

            # 1. Apply with KEEP_EXISTING -> rating remains 7
            res_keep = await personal_repository.apply_user_import(
                db=session, user_id=self.user_a_id, items=import_items, conflict_strategy="KEEP_EXISTING"
            )
            self.assertEqual(res_keep.applied_count, 1)
            ratings = await personal_repository.list_ratings(db=session, user_id=self.user_a_id)
            r_keep = next((r for r in ratings if r.title_id == str(self.title1.title_id)), None)
            self.assertIsNotNone(r_keep)
            self.assertEqual(r_keep.rating_value, 7)

            # 2. Apply with OVERWRITE -> rating becomes 10
            res_overwrite = await personal_repository.apply_user_import(
                db=session, user_id=self.user_a_id, items=import_items, conflict_strategy="OVERWRITE"
            )
            self.assertEqual(res_overwrite.applied_count, 1)
            self.assertGreaterEqual(res_overwrite.conflicts_resolved, 1)
            ratings_after = await personal_repository.list_ratings(db=session, user_id=self.user_a_id)
            r_over = next((r for r in ratings_after if r.title_id == str(self.title1.title_id)), None)
            self.assertIsNotNone(r_over)
            self.assertEqual(r_over.rating_value, 10)
