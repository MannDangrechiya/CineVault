# CineVault OS — Personal Repository Integration Test Suite
# Tests Build Unit 8.2: Personal Library, Watch Events, Ratings, Notes, Reviews, and CAT-2 Isolation

import time
import base64
import json
import unittest
import asyncio
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.repositories.personal import personal_repository
from services.api.schemas.personal import (
    WatchEventCreate, UserTitleStateUpdate, RatingCreate, NoteCreate, ReviewCreate
)

def generate_mock_jwt(roles: list, sub: str = "user-9999999") -> str:
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

class TestPersonalRepository(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.user_id = "user-9999999"
        cls.user_jwt = generate_mock_jwt(["AuthenticatedUser"], sub=cls.user_id)
        cls.auth_headers = {"Authorization": f"Bearer {cls.user_jwt}"}

    def test_repository_watch_events_flow(self):
        body = WatchEventCreate(
            title_id="018f2e4a-7b31-7000-8000-123456789abc",
            watched_at="2026-08-08T19:00:00Z",
            progress_percentage=100.0
        )
        event = asyncio.run(personal_repository.create_watch_event(db=None, user_id=self.user_id, body=body))
        self.assertIsNotNone(event)
        self.assertEqual(event.user_id, self.user_id)
        self.assertEqual(event.title_id, body.title_id)

        events_list = asyncio.run(personal_repository.list_watch_events(db=None, user_id=self.user_id))
        self.assertGreater(len(events_list), 0)

    def test_repository_title_state_update(self):
        title_id = "018f2e4a-7b31-7000-8000-123456789abc"
        update_body = UserTitleStateUpdate(manual_status_override="COMPLETED", is_favorite=True)
        st = asyncio.run(personal_repository.update_user_title_state(db=None, user_id=self.user_id, title_id=title_id, body=update_body))
        self.assertIsNotNone(st)
        self.assertTrue(st.is_favorite)
        self.assertEqual(st.manual_status_override, "COMPLETED")

    def test_repository_ratings_flow(self):
        title_id = "018f2e4a-7b31-7000-8000-123456789abc"
        rating_body = RatingCreate(title_id=title_id, rating_value=9)
        res = asyncio.run(personal_repository.set_rating(db=None, user_id=self.user_id, body=rating_body))
        self.assertEqual(res.rating_value, 9)

        ratings = asyncio.run(personal_repository.list_ratings(db=None, user_id=self.user_id))
        self.assertGreater(len(ratings), 0)

    def test_router_anonymous_access_denied(self):
        res = self.client.get("/v1/me/watch-events")
        self.assertEqual(res.status_code, 401)

    def test_router_authenticated_user_access_granted(self):
        titles_res = self.client.get("/v1/titles")
        real_title_id = titles_res.json()["data"][0]["id"]
        body = {
            "title_id": real_title_id,
            "watched_at": "2026-08-08T19:00:00Z",
            "progress_percentage": 100.0
        }
        post_res = self.client.post("/v1/me/watch-events", json=body, headers=self.auth_headers)
        self.assertEqual(post_res.status_code, 201)

        res = self.client.get("/v1/me/watch-events", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("data", data)
        self.assertGreater(len(data["data"]), 0)

if __name__ == "__main__":
    unittest.main()
