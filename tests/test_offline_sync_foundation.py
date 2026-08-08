# CineVault OS — Test Suite for Build Unit 8.9: Offline Sync Foundation Engine

import time
import uuid
import base64
import json
import unittest
import asyncio
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.repositories.sync import sync_repository
from services.api.repositories.personal import personal_repository
from services.api.schemas.sync import MutationItem

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

class TestOfflineSyncFoundation(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.user_id = "018f4a00-0000-7000-8000-000000000099"
        self.user_jwt = generate_mock_jwt(["AuthenticatedUser"], sub=self.user_id)
        self.auth_headers = {"Authorization": f"Bearer {self.user_jwt}"}

    def test_anonymous_sync_push_denied(self):
        """Verifies unauthenticated requests to /v1/sync/push are rejected with 401."""
        response = self.client.post("/v1/sync/push", json={"mutations": []})
        self.assertEqual(response.status_code, 401)

    def test_sync_push_and_idempotency_retry(self):
        """Verifies batch offline mutation push and server-side idempotency retry handling."""
        mutation_id_1 = str(uuid.uuid4())
        mutation_id_2 = str(uuid.uuid4())

        payload = {
            "mutations": [
                {
                    "mutation_id": mutation_id_1,
                    "mutation_type": "CREATE_WATCH_EVENT",
                    "client_timestamp": "2026-08-08T20:00:00Z",
                    "payload": {
                        "title_id": "018f4a00-0000-7000-8000-000000000001",
                        "progress_percentage": 100.0
                    }
                },
                {
                    "mutation_id": mutation_id_2,
                    "mutation_type": "SET_RATING",
                    "client_timestamp": "2026-08-08T20:01:00Z",
                    "payload": {
                        "title_id": "018f4a00-0000-7000-8000-000000000001",
                        "rating_value": 9
                    }
                }
            ]
        }

        # 1. Initial Push Submission
        response1 = self.client.post("/v1/sync/push", json=payload, headers=self.auth_headers)
        self.assertEqual(response1.status_code, 200)
        data1 = response1.json()
        self.assertEqual(data1["processed_count"], 2)
        self.assertIn(mutation_id_1, data1["acknowledged_mutation_ids"])
        self.assertIn(mutation_id_2, data1["acknowledged_mutation_ids"])

        # 2. Idempotent Retry Submission (exact same mutation IDs)
        response2 = self.client.post("/v1/sync/push", json=payload, headers=self.auth_headers)
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertEqual(data2["processed_count"], 2)
        self.assertIn(mutation_id_1, data2["acknowledged_mutation_ids"])
        self.assertIn(mutation_id_2, data2["acknowledged_mutation_ids"])

    def test_watch_event_append_only_preservation(self):
        """Verifies multiple watch events for same title are preserved as rewatches per ADR-003."""
        title_id = "018f4a00-0000-7000-8000-000000000002"
        mid_1 = str(uuid.uuid4())
        mid_2 = str(uuid.uuid4())

        payload1 = {
            "mutations": [{
                "mutation_id": mid_1,
                "mutation_type": "CREATE_WATCH_EVENT",
                "client_timestamp": "2026-08-08T18:00:00Z",
                "payload": {"title_id": title_id, "progress_percentage": 100.0}
            }]
        }
        payload2 = {
            "mutations": [{
                "mutation_id": mid_2,
                "mutation_type": "CREATE_WATCH_EVENT",
                "client_timestamp": "2026-08-08T19:00:00Z",
                "payload": {"title_id": title_id, "progress_percentage": 100.0}
            }]
        }

        r1 = self.client.post("/v1/sync/push", json=payload1, headers=self.auth_headers)
        r2 = self.client.post("/v1/sync/push", json=payload2, headers=self.auth_headers)

        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)

        events = asyncio.run(personal_repository.list_watch_events(db=None, user_id=self.user_id))
        self.assertGreaterEqual(len(events), 2)

    def test_sync_pull_delta_stream(self):
        """Verifies GET /v1/sync/pull returns delta change stream with updated cursor pointer."""
        response = self.client.get("/v1/sync/pull?limit=10", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("sync_cursor", data)
        self.assertIn("changes", data)
        self.assertIn("has_more", data)
        self.assertFalse(data["has_more"])

    def test_cross_user_mutation_isolation(self):
        """Verifies authenticated user A cannot pass user B's identity to mutate user B's personal data."""
        user_a_sub = "018f4a00-0000-7000-8000-000000000111"
        user_b_sub = "018f4a00-0000-7000-8000-000000000222"
        user_a_jwt = generate_mock_jwt(["AuthenticatedUser"], sub=user_a_sub)
        user_a_headers = {"Authorization": f"Bearer {user_a_jwt}"}

        mid = str(uuid.uuid4())
        payload = {
            "mutations": [{
                "mutation_id": mid,
                "mutation_type": "SET_RATING",
                "client_timestamp": "2026-08-08T20:00:00Z",
                "payload": {
                    "user_id": user_b_sub, # Attempted forged user ID
                    "title_id": "018f4a00-0000-7000-8000-000000000001",
                    "rating_value": 10
                }
            }]
        }

        response = self.client.post("/v1/sync/push", json=payload, headers=user_a_headers)
        self.assertEqual(response.status_code, 200)

        # Ratings for User B must be empty (User A cannot mutate User B)
        user_b_ratings = asyncio.run(personal_repository.list_ratings(db=None, user_id=user_b_sub))
        self.assertEqual(len(user_b_ratings), 0)

if __name__ == "__main__":
    unittest.main()
