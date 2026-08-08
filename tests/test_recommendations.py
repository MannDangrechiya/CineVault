# CineVault OS — Test Suite for Build Unit 8.7: Recommendation Foundation Engine

import time
import base64
import json
import unittest
import asyncio
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.repositories.recommendations import recommendation_repository
from services.api.schemas.recommendations import RecommendationModeEnum, ColdStartPreferenceInput

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

class TestRecommendationEngine(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.user_id = "018f4a00-0000-7000-8000-000000000099"
        self.user_jwt = generate_mock_jwt(["AuthenticatedUser"], sub=self.user_id)
        self.auth_headers = {"Authorization": f"Bearer {self.user_jwt}"}

    def test_anonymous_access_to_recommendations_denied(self):
        """Verifies unauthenticated requests to recommendations endpoint are rejected with 401."""
        response = self.client.get("/v1/recommendations")
        self.assertEqual(response.status_code, 401)

    def test_authenticated_recommendations_tonight_mode(self):
        """Verifies authenticated user can retrieve personalized recommendations in TONIGHT mode."""
        response = self.client.get("/v1/recommendations?mode=tonight&limit=5", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mode"], "tonight")
        self.assertGreater(data["total"], 0)
        self.assertLessEqual(len(data["data"]), 5)

        first_item = data["data"][0]
        self.assertIn("title_id", first_item)
        self.assertIn("recommendation_score", first_item)
        self.assertGreaterEqual(first_item["recommendation_score"], 0.0)
        self.assertIn("explanation", first_item)
        self.assertGreater(len(first_item["explanation"]["explanation_text"]), 0)

    def test_hard_filter_under_90_mode(self):
        """Verifies UNDER_90 recommendation mode applies strict max runtime filter <= 90 mins."""
        response = self.client.get("/v1/recommendations?mode=under_90", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        for item in data["data"]:
            if item["runtime_minutes"] is not None:
                self.assertLessEqual(item["runtime_minutes"], 90)

    def test_genre_hard_filter(self):
        """Verifies explicit genre filter restricts returned recommendations."""
        response = self.client.get("/v1/recommendations?genre=Action", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        for item in data["data"]:
            genres_lower = [g.lower() for g in item["genres"]]
            self.assertIn("action", genres_lower)

    def test_similar_titles_endpoint(self):
        """Verifies GET /v1/recommendations/similar/{title_id} returns content-similar titles."""
        seed_id = "018f4a00-0000-7000-8000-000000000001" # Inception
        response = self.client.get(f"/v1/recommendations/similar/{seed_id}?limit=3", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mode"], "because_you_liked")
        self.assertLessEqual(len(data["data"]), 3)

        for item in data["data"]:
            self.assertEqual(item["explanation"]["seed_title_name"], "Inception")

    def test_cold_start_recommendations_endpoint(self):
        """Verifies POST /v1/recommendations/cold-start generates cold start recommendations."""
        payload = {
            "preferred_genres": ["Sci-Fi", "Mystery"],
            "min_release_year": 2000
        }

        response = self.client.post("/v1/recommendations/cold-start", json=payload, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mode"], "cold_start")
        self.assertTrue(data["is_cold_start"])
        self.assertGreater(len(data["data"]), 0)

        for item in data["data"]:
            self.assertGreaterEqual(item["release_year"], 2000)

    def test_explain_recommendation_endpoint(self):
        """Verifies POST /v1/recommendations/explain returns grounded diagnostic score breakdown."""
        payload = {
            "title_id": "018f4a00-0000-7000-8000-000000000001",
            "seed_title_id": "018f4a00-0000-7000-8000-000000000002"
        }

        response = self.client.post("/v1/recommendations/explain", json=payload, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title_id"], "018f4a00-0000-7000-8000-000000000001")
        self.assertIn("score_breakdown", data)
        self.assertIn("explanation", data)
        self.assertIn("total_score", data["score_breakdown"])

    def test_repository_get_recommendations_logic(self):
        """Verifies repository logic directly for candidate generation and deterministic ranking."""
        res = asyncio.run(recommendation_repository.get_recommendations(
            db=None,
            user_id=self.user_id,
            mode=RecommendationModeEnum.TONIGHT,
            limit=5
        ))
        self.assertGreater(res.total, 0)
        self.assertEqual(res.mode, RecommendationModeEnum.TONIGHT)

        # Scores must be sorted descending
        scores = [item.recommendation_score for item in res.data]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_cat2_privacy_isolation_no_personal_data_leakage(self):
        """Verifies CAT-2 personal data is isolated and not leaked into recommendation responses."""
        response = self.client.get("/v1/recommendations", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        content_str = response.text

        # Ensure no user PII or raw credentials are leaked
        self.assertNotIn("password", content_str)
        self.assertNotIn("secret", content_str)
        self.assertNotIn("user@cinevault.local", content_str)

if __name__ == "__main__":
    unittest.main()
