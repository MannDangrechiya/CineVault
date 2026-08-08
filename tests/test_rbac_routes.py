# CineVault OS — Route-Level RBAC & Privilege Escalation Test Suite
# Enforces explicit permission boundaries across Public, Personal Data, Sync, and Control Room routes

import time
import unittest
from fastapi.testclient import TestClient
from services.api.main import app

def generate_mock_jwt(roles: list, sub: str = "user-123") -> str:
    # Generates unverified token format for test client header
    import base64, json
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

class TestRBACRouteBoundaries(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.user_jwt = generate_mock_jwt(["AuthenticatedUser"], sub="user-123")
        self.curator_jwt = generate_mock_jwt(["AuthenticatedUser", "Curator"], sub="curator-456")
        self.admin_jwt = generate_mock_jwt(["AuthenticatedUser", "Curator", "SystemAdmin"], sub="admin-789")

    def test_anonymous_access_to_public_catalog(self):
        response = self.client.get("/v1/titles")
        self.assertEqual(response.status_code, 200)

    def test_anonymous_access_to_personal_data_denied(self):
        response = self.client.get("/v1/me/watch-events")
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_access_to_personal_data_granted(self):
        headers = {"Authorization": f"Bearer {self.user_jwt}"}
        response = self.client.get("/v1/me/watch-events", headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_access_to_internal_admin_denied(self):
        headers = {"Authorization": f"Bearer {self.user_jwt}"}
        response = self.client.get("/internal/v1/ingestion/runs", headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_curator_access_to_internal_admin_granted(self):
        headers = {"Authorization": f"Bearer {self.curator_jwt}"}
        response = self.client.get("/internal/v1/ingestion/runs", headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_system_admin_access_to_internal_admin_granted(self):
        headers = {"Authorization": f"Bearer {self.admin_jwt}"}
        response = self.client.get("/internal/v1/ingestion/runs", headers=headers)
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
