# CineVault OS — Phase W12: Web Product Completeness & Real-World Launch Readiness
# Comprehensive integration test suite verifying end-to-end product flows, personal lifecycle,
# collections curation, multiplayer social mechanics, import/export portability, and user isolation.

import base64
import json
import uuid
import zipfile
import io
from datetime import datetime, timezone
import pytest
from unittest import IsolatedAsyncioTestCase
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.main import app
from services.api.database import engine
from services.api.models.canonical import (
    TitleModel, ContentTypeModel, GenreModel, TitleGenreModel
)
from services.api.models.personal import (
    LibraryEntryModel, UserTitleStateModel, WatchEventModel,
    RatingModel, NoteModel, ReviewModel,
    UserListModel, UserListItemModel
)
from services.api.models.social import (
    FriendshipModel, RecommendationModel, WatchClubModel,
    ChallengeModel, PickRoomModel, PickRoomCandidateModel
)

DEV_USER_ID = "00000000-0000-0000-0000-000000000001"
CURATOR_USER_ID = "00000000-0000-0000-0000-000000000002"

def make_dev_token(user_id=None, role="AuthenticatedUser", roles=None, email=None):
    uid = str(user_id or uuid.uuid4())
    roles_list = roles or ([role] if role else ["AuthenticatedUser"])
    header = {"alg": "RS256", "typ": "JWT", "kid": "cinevault-dev-key"}
    exp_time = int(datetime.now(timezone.utc).timestamp()) + 3600
    payload = {
        "sub": uid,
        "iss": "http://localhost:8080/realms/cinevault-dev",
        "aud": "cinevault-api-gateway",
        "exp": exp_time,
        "realm_access": {"roles": roles_list},
        "email": email or f"user_{uid[:8]}@cinevault.local"
    }
    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig_b64 = base64.urlsafe_b64encode(b"mock-local-signature").decode().rstrip("=")
    return f"{h_b64}.{p_b64}.{sig_b64}"

DEV_TOKEN = make_dev_token(DEV_USER_ID, roles=["AuthenticatedUser", "Curator", "SystemAdmin"])
CURATOR_TOKEN = make_dev_token(CURATOR_USER_ID, roles=["AuthenticatedUser", "Curator"])

class PhaseW12WebProductCompletenessTestCase(IsolatedAsyncioTestCase):
    """End-to-end integration and regression suite for Phase W12 Web Launch Readiness."""

    async def asyncSetUp(self):
        self.client = TestClient(app)
        self.dev_headers = {"Authorization": f"Bearer {DEV_TOKEN}"}
        self.curator_headers = {"Authorization": f"Bearer {CURATOR_TOKEN}"}

        self._conn = await engine.connect()
        self._outer_txn = await self._conn.begin()
        self.SessionLocal = async_sessionmaker(
            bind=self._conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        async with self.SessionLocal() as session:
            # Ensure basic types and genres exist
            types = [("movie", "Feature Film"), ("series", "Television Series")]
            for t_id, t_name in types:
                if not await session.get(ContentTypeModel, t_id):
                    session.add(ContentTypeModel(content_type_id=t_id, type_name=t_name))

            genres = [("scifi", "Sci-Fi"), ("action", "Action"), ("drama", "Drama")]
            for g_id, g_name in genres:
                if not await session.get(GenreModel, g_id):
                    session.add(GenreModel(genre_id=g_id, name=g_name))

            await session.flush()

            # Seed Title 1: Interstellar
            stmt1 = select(TitleModel).where(TitleModel.canonical_title == "Interstellar", TitleModel.production_year == 2014)
            self.title1 = (await session.execute(stmt1)).scalar_one_or_none()
            if not self.title1:
                self.title1 = TitleModel(
                    title_id=uuid.uuid4(),
                    display_id="IMDB-tt0816692",
                    content_type_id="movie",
                    canonical_title="Interstellar",
                    original_title="Interstellar",
                    production_year=2014,
                    synopsis="A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival."
                )
                session.add(self.title1)
                await session.flush()

            # Seed Title 2: Severance
            stmt2 = select(TitleModel).where(TitleModel.canonical_title == "Severance", TitleModel.production_year == 2022)
            self.title2 = (await session.execute(stmt2)).scalar_one_or_none()
            if not self.title2:
                self.title2 = TitleModel(
                    title_id=uuid.uuid4(),
                    display_id="IMDB-tt11280740",
                    content_type_id="series",
                    canonical_title="Severance",
                    original_title="Severance",
                    production_year=2022,
                    synopsis="Mark leads a team of office workers whose memories have been surgically divided between their work and personal lives."
                )
                session.add(self.title2)
                await session.flush()

            await session.commit()

        self.title1_id = str(self.title1.title_id)
        self.title2_id = str(self.title2.title_id)

    async def asyncTearDown(self):
        await self._outer_txn.rollback()
        await self._conn.close()

    def test_1_catalog_and_display_id_search_resolution(self):
        """Validates catalog browsing, exact title lookup, and display ID resolution."""
        # 1. Exact title query
        res = self.client.get("/v1/search?q=Interstellar", headers=self.dev_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["total_hits"], 1)
        self.assertIn("Interstellar", [r["canonical_title"] for r in data["results"]])

        # 2. Display ID lookup with IMDB- prefix
        res_id = self.client.get(f"/v1/search?q={self.title1.display_id}", headers=self.dev_headers)
        self.assertEqual(res_id.status_code, 200)
        data_id = res_id.json()
        self.assertEqual(data_id["total_hits"], 1)
        self.assertEqual(data_id["results"][0]["canonical_title"], "Interstellar")

    def test_2_movie_and_series_detail_provenance(self):
        """Validates /v1/titles/{id} entity retrieval with complete metadata."""
        res_movie = self.client.get(f"/v1/titles/{self.title1_id}")
        self.assertEqual(res_movie.status_code, 200)
        movie_data = res_movie.json()
        self.assertEqual(movie_data["id"], self.title1_id)
        self.assertEqual(movie_data["canonical_title"], "Interstellar")
        self.assertEqual(movie_data["production_year"], 2014)

        res_series = self.client.get(f"/v1/titles/{self.title2_id}")
        self.assertEqual(res_series.status_code, 200)
        series_data = res_series.json()
        self.assertEqual(series_data["id"], self.title2_id)
        self.assertEqual(series_data["canonical_title"], "Severance")

    def test_3_personal_vault_complete_lifecycle(self):
        """Validates full personal lifecycle: library, watchlist, ratings, notes, reviews, scrobbling."""
        # 1. Add to Library
        res_lib = self.client.post("/v1/personal/library", json={"title_id": self.title1_id}, headers=self.dev_headers)
        self.assertIn(res_lib.status_code, (200, 201))

        # Check library listing
        get_lib = self.client.get("/v1/personal/library", headers=self.dev_headers)
        self.assertEqual(get_lib.status_code, 200)
        lib_items = get_lib.json()["items"]
        self.assertTrue(any(i["title_id"] == self.title1_id for i in lib_items))

        # 2. Add to Watchlist & Favorite
        res_ws = self.client.patch(
            f"/v1/me/title-states/{self.title1_id}",
            json={"manual_status_override": "WATCHLIST", "is_favorite": True},
            headers=self.dev_headers
        )
        self.assertEqual(res_ws.status_code, 200)
        ws_data = res_ws.json()
        self.assertEqual(ws_data["manual_status_override"], "WATCHLIST")
        self.assertTrue(ws_data["is_favorite"])

        # Check watchlist
        get_ws = self.client.get("/v1/personal/watchlist", headers=self.dev_headers)
        self.assertEqual(get_ws.status_code, 200)
        self.assertTrue(any(i["title_id"] == self.title1_id for i in get_ws.json()["items"]))

        # 3. Log Watch Event
        res_watch = self.client.post(
            "/v1/me/watch-events",
            json={
                "title_id": self.title1_id,
                "watched_at": datetime.now(timezone.utc).isoformat(),
                "progress_percentage": 100.0,
                "notes": "IMAX screening"
            },
            headers=self.dev_headers
        )
        self.assertIn(res_watch.status_code, (200, 201))

        # Check history
        get_hist = self.client.get("/v1/personal/history", headers=self.dev_headers)
        self.assertEqual(get_hist.status_code, 200)
        self.assertTrue(any(i["title_id"] == self.title1_id for i in get_hist.json()["items"]))

        # 4. Rating (1-10)
        res_rate = self.client.post(
            "/v1/me/ratings",
            json={"title_id": self.title1_id, "rating_value": 9},
            headers=self.dev_headers
        )
        self.assertIn(res_rate.status_code, (200, 201))
        self.assertEqual(res_rate.json()["rating_value"], 9)

        # 5. Private Note
        res_note = self.client.post(
            "/v1/me/notes",
            json={"title_id": self.title1_id, "note_text": "Favorite Hans Zimmer organ score."},
            headers=self.dev_headers
        )
        self.assertIn(res_note.status_code, (200, 201))
        note_id = res_note.json()["id"]

        # 6. Review
        res_rev = self.client.post(
            "/v1/me/reviews",
            json={
                "title_id": self.title1_id,
                "review_title": "Masterpiece of Sci-Fi Emotion",
                "review_text": "The tesseract sequence ties the entire emotional arc together.",
                "contains_spoilers": False
            },
            headers=self.dev_headers
        )
        self.assertIn(res_rev.status_code, (200, 201))
        review_id = res_rev.json()["id"]

        # 7. Verify Cleanup / Deletion
        del_rate = self.client.delete(f"/v1/me/ratings/{self.title1_id}", headers=self.dev_headers)
        self.assertEqual(del_rate.status_code, 200)

        del_note = self.client.delete(f"/v1/me/notes/{note_id}", headers=self.dev_headers)
        self.assertEqual(del_note.status_code, 200)

        del_rev = self.client.delete(f"/v1/me/reviews/{review_id}", headers=self.dev_headers)
        self.assertEqual(del_rev.status_code, 200)

        del_lib = self.client.delete(f"/v1/personal/library/{self.title1_id}", headers=self.dev_headers)
        self.assertEqual(del_lib.status_code, 200)

    def test_4_collections_lifecycle_and_curation(self):
        """Validates collection creation, item addition, retrieval, item removal, and deletion."""
        # 1. Create collection
        res_create = self.client.post(
            "/v1/personal/collections",
            json={
                "name": "Nolan Sci-Fi Marathons",
                "description": "Mind-bending cinematic universe viewing order",
                "is_private": False,
                "tags": ["SciFi", "Nolan"]
            },
            headers=self.dev_headers
        )
        self.assertEqual(res_create.status_code, 201)
        collection_id = res_create.json()["id"]

        # 2. Add title to collection
        res_add = self.client.post(
            f"/v1/personal/collections/{collection_id}/items",
            json={"title_id": self.title1_id, "notes": "Part 1: The Wormhole Journey"},
            headers=self.dev_headers
        )
        self.assertIn(res_add.status_code, (200, 201))

        # 3. Retrieve collection detail
        res_get = self.client.get(f"/v1/personal/collections/{collection_id}", headers=self.dev_headers)
        self.assertEqual(res_get.status_code, 200)
        detail = res_get.json()
        self.assertEqual(detail["collection"]["name"], "Nolan Sci-Fi Marathons")
        self.assertEqual(len(detail["items"]), 1)
        self.assertEqual(detail["items"][0]["title_id"], self.title1_id)

        # 4. Remove item
        res_rem = self.client.delete(
            f"/v1/personal/collections/{collection_id}/items/{self.title1_id}",
            headers=self.dev_headers
        )
        self.assertEqual(res_rem.status_code, 200)

        # 5. Delete collection
        res_del = self.client.delete(f"/v1/personal/collections/{collection_id}", headers=self.dev_headers)
        self.assertEqual(res_del.status_code, 200)

    def test_5_social_multiplayer_and_pick_rooms(self):
        """Validates social mechanics: friendship, peer recommendation, pick room voting, club activity."""
        # 1. Create friendship Dev -> Curator
        res_fr = self.client.post(
            "/social/friendships",
            json={"addressee_id": CURATOR_USER_ID},
            headers=self.dev_headers
        )
        self.assertIn(res_fr.status_code, (200, 201))
        friendship_id = res_fr.json()["friendship_id"]

        # 2. Curator accepts friendship
        res_acc = self.client.patch(
            f"/social/friendships/{friendship_id}",
            json={"status": "ACCEPTED"},
            headers=self.curator_headers
        )
        self.assertEqual(res_acc.status_code, 200)

        # 3. Send peer recommendation from Dev to Curator
        res_rec = self.client.post(
            "/social/recommendations",
            json={
                "title_id": self.title1_id,
                "recipient_id": CURATOR_USER_ID,
                "context_note": "You must watch Interstellar before the weekend!"
            },
            headers=self.dev_headers
        )
        self.assertEqual(res_rec.status_code, 201)

        # Curator checks inbox
        get_inbox = self.client.get("/social/recommendations?role=received", headers=self.curator_headers)
        self.assertEqual(get_inbox.status_code, 200)
        self.assertTrue(any(r["title_id"] == self.title1_id for r in get_inbox.json()))

        # 4. Create and Vote in Pick Room
        res_room = self.client.post(
            "/social/pick-rooms",
            json={
                "title": "Friday Night Sci-Fi Ballot",
                "candidate_title_ids": [self.title1_id, self.title2_id]
            },
            headers=self.dev_headers
        )
        self.assertEqual(res_room.status_code, 201)
        room_slug = res_room.json()["slug"]

        # Dev votes for Title 1
        res_v1 = self.client.post(
            f"/social/pick-rooms/{room_slug}/vote",
            json={"title_id": self.title1_id, "vote_type": "UPVOTE"},
            headers=self.dev_headers
        )
        self.assertEqual(res_v1.status_code, 200)

        # Curator votes for Title 1
        res_v2 = self.client.post(
            f"/social/pick-rooms/{room_slug}/vote",
            json={"title_id": self.title1_id, "vote_type": "UPVOTE"},
            headers=self.curator_headers
        )
        self.assertEqual(res_v2.status_code, 200)

        # Host closes room and resolves winner
        res_close = self.client.post(f"/social/pick-rooms/{room_slug}/close", headers=self.dev_headers)
        self.assertEqual(res_close.status_code, 200)
        self.assertEqual(res_close.json()["status"], "RESOLVED")
        self.assertEqual(res_close.json()["winning_title_id"], self.title1_id)

    def test_6_import_export_data_portability(self):
        """Validates all 4 export formats and 3-step import wizard conflict handling."""
        # 1. Test JSON Export
        res_json = self.client.get("/v1/personal/export?format=json", headers=self.dev_headers)
        self.assertEqual(res_json.status_code, 200)
        self.assertEqual(res_json.headers["content-type"], "application/json")
        export_data = res_json.json()
        self.assertIn("schema_version", export_data)
        self.assertIn("library", export_data)

        # 2. Test CSV Relational ZIP Export
        res_csv = self.client.get("/v1/personal/export?format=csv", headers=self.dev_headers)
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.headers["content-type"], "application/zip")
        with zipfile.ZipFile(io.BytesIO(res_csv.content)) as z:
            namelist = z.namelist()
            self.assertIn("manifest.json", namelist)
            self.assertIn("library.csv", namelist)

        # 3. Test Excel Export
        res_excel = self.client.get("/v1/personal/export?format=excel", headers=self.dev_headers)
        self.assertEqual(res_excel.status_code, 200)
        self.assertEqual(res_excel.headers["content-type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # 4. Test Markdown Export
        res_md = self.client.get("/v1/personal/export?format=markdown", headers=self.dev_headers)
        self.assertEqual(res_md.status_code, 200)
        self.assertIn("text/markdown", res_md.headers["content-type"])

        # 5. Test Import Preview
        import_payload = [
            {
                "canonical_title": "Interstellar",
                "production_year": 2014,
                "rating_value": 10,
                "manual_status_override": "COMPLETED",
                "notes": "Verified launch candidate import."
            }
        ]
        res_prev = self.client.post("/v1/personal/import/preview", json={"items": import_payload}, headers=self.dev_headers)
        self.assertEqual(res_prev.status_code, 200)
        prev_data = res_prev.json()
        self.assertEqual(prev_data["total_items"], 1)
        self.assertEqual(prev_data["matched_titles"], 1)

        # 6. Test Import Apply with MERGE strategy
        res_apply = self.client.post(
            "/v1/personal/import/apply",
            json={"items": import_payload, "conflict_strategy": "MERGE"},
            headers=self.dev_headers
        )
        self.assertEqual(res_apply.status_code, 200)
        apply_data = res_apply.json()
        self.assertGreaterEqual(apply_data["applied_count"], 1)
        self.assertEqual(apply_data["strategy_applied"], "MERGE")

    def test_7_multi_account_strict_data_isolation(self):
        """Validates zero cross-user IDOR leakage across personal library, notes, and collections."""
        # Dev user creates a private note
        res_note = self.client.post(
            "/v1/me/notes",
            json={"title_id": self.title2_id, "note_text": "Dev private confidential note."},
            headers=self.dev_headers
        )
        self.assertIn(res_note.status_code, (200, 201))
        dev_note_id = res_note.json()["id"]

        # Curator attempts to list notes for title 2
        res_cur_notes = self.client.get(f"/v1/me/notes?title_id={self.title2_id}", headers=self.curator_headers)
        self.assertEqual(res_cur_notes.status_code, 200)
        curator_notes = res_cur_notes.json()
        self.assertFalse(any(n["id"] == dev_note_id for n in curator_notes))

        # Curator attempts to delete Dev's note directly
        del_attempt = self.client.delete(f"/v1/me/notes/{dev_note_id}", headers=self.curator_headers)
        # Verify Dev note is untouched
        check_dev_note = self.client.get(f"/v1/me/notes?title_id={self.title2_id}", headers=self.dev_headers)
        self.assertTrue(any(n["id"] == dev_note_id for n in check_dev_note.json()))

        # Cleanup note
        self.client.delete(f"/v1/me/notes/{dev_note_id}", headers=self.dev_headers)
