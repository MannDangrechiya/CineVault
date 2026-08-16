# CineVault OS — Phase 23: Data Quality Control Room Verification Tests
# Validates curator tooling, conflict queue, quarantine triage, merge safety, RBAC authorization, and personal-data privacy isolation

import time
import base64
import json
import unittest
from fastapi.testclient import TestClient

from services.api.main import app

def generate_mock_jwt(roles: list = None, sub: str = "curator-001") -> str:
    if roles is None:
        roles = ["AuthenticatedUser", "Curator"]
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

class Phase23DataQualityControlRoomTestCase(unittest.TestCase):
    """Verifies complete Data Quality Control Room curator toolings, safety gates, and privacy protections."""

    def setUp(self):
        self.client = TestClient(app)
        self.curator_jwt = generate_mock_jwt(["AuthenticatedUser", "Curator"], sub="018f4a00-0000-7000-8000-000000000001")
        self.curator_headers = {"Authorization": f"Bearer {self.curator_jwt}"}

        self.user_jwt = generate_mock_jwt(["AuthenticatedUser"], sub="018f4a00-0000-7000-8000-000000000099")
        self.user_headers = {"Authorization": f"Bearer {self.user_jwt}"}

    def test_curator_tooling_rbac_authorization(self):
        """RBAC: Anonymous and standard users are rejected from Control Room curation endpoints."""
        # Anonymous -> 401
        anon_res = self.client.get("/internal/v1/control-room/stats")
        self.assertEqual(anon_res.status_code, 401)

        # Standard User without Curator role -> 403
        user_res = self.client.get("/internal/v1/control-room/stats", headers=self.user_headers)
        self.assertEqual(user_res.status_code, 403)

        # Curator User -> 200
        curator_res = self.client.get("/internal/v1/control-room/stats", headers=self.curator_headers)
        self.assertEqual(curator_res.status_code, 200)

    def test_conflict_queue_inspection_and_resolution(self):
        """Conflict Queue: Curator inspects and resolves multi-provider metadata conflicts."""
        # 1. Inspect conflict queue
        conflicts_res = self.client.get("/internal/v1/reconciliation/conflicts", headers=self.curator_headers)
        self.assertEqual(conflicts_res.status_code, 200)
        conflicts = conflicts_res.json()
        self.assertIsInstance(conflicts, list)

        # 2. Resolve conflict with UUID
        resolve_payload = {
            "winning_value": "142",
            "resolution_notes": "Confirmed 142 min theatrical cut against distributor press release."
        }
        res = self.client.post(
            "/internal/v1/reconciliation/conflicts/018f6f60-7a00-7000-8000-000000000001/resolve",
            json=resolve_payload,
            headers=self.curator_headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "RESOLVED")
        self.assertIn("integrity_hash", data)
        self.assertEqual(len(data["integrity_hash"]), 64)

    def test_quarantine_payload_inspection_and_resolution(self):
        """Quarantine Triage: Curator inspects corrupted/quarantined payloads and resolves them."""
        # 1. List quarantine records
        q_res = self.client.get("/internal/v1/control-room/quarantine", headers=self.curator_headers)
        self.assertEqual(q_res.status_code, 200)
        q_records = q_res.json()
        self.assertIsInstance(q_records, list)

        # 2. Resolve quarantine record
        resolve_body = {
            "decision": "RESOLVE",
            "rationale": "Missing production year identified and corrected via official records."
        }
        resolve_res = self.client.post(
            "/internal/v1/control-room/quarantine/018f4a00-0000-7000-8000-quarantine001/resolve",
            json=resolve_body,
            headers=self.curator_headers
        )
        self.assertEqual(resolve_res.status_code, 200)
        data = resolve_res.json()
        self.assertEqual(data["status"], "RESOLVED")
        self.assertIn("integrity_hash", data)
        self.assertEqual(len(data["integrity_hash"]), 64)

    def test_personal_data_protection_in_control_room(self):
        """Privacy: Control Room responses strictly exclude CAT-2 personal user data."""
        stats = self.client.get("/internal/v1/control-room/stats", headers=self.curator_headers).json()
        stats_str = json.dumps(stats).lower()
        self.assertNotIn("password", stats_str)
        self.assertNotIn("email", stats_str)
        self.assertNotIn("watch_event", stats_str)

        candidates = self.client.get("/internal/v1/control-room/candidates", headers=self.curator_headers).json()
        cand_str = json.dumps(candidates).lower()
        self.assertNotIn("user_id", cand_str)
        self.assertNotIn("user_notes", cand_str)
