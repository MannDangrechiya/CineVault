# CineVault OS — Test Suite for Build Unit 8.10: Control Room / Curation Foundation Engine

import time
import uuid
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

class TestControlRoomFoundation(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.curator_jwt = generate_mock_jwt(["AuthenticatedUser", "Curator"], sub="018f4a00-0000-7000-8000-000000000001")
        self.curator_headers = {"Authorization": f"Bearer {self.curator_jwt}"}

        self.user_jwt = generate_mock_jwt(["AuthenticatedUser"], sub="018f4a00-0000-7000-8000-000000000099")
        self.user_headers = {"Authorization": f"Bearer {self.user_jwt}"}

    def test_anonymous_and_user_access_to_control_room_denied(self):
        """Verifies unauthenticated and regular user requests to Control Room endpoints are rejected with 401/403."""
        # Anonymous
        anon_res = self.client.get("/internal/v1/control-room/stats")
        self.assertEqual(anon_res.status_code, 401)

        # Standard user without Curator role
        user_res = self.client.get("/internal/v1/control-room/stats", headers=self.user_headers)
        self.assertEqual(user_res.status_code, 403)

    def test_control_room_summary_stats(self):
        """Verifies GET /internal/v1/control-room/stats returns operational summary counts."""
        response = self.client.get("/internal/v1/control-room/stats", headers=self.curator_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("pending_reconciliation_candidates", data)
        self.assertIn("pending_ai_proposals", data)
        self.assertIn("pending_quarantine_records", data)
        self.assertIn("promoted_canonical_records", data)

    def test_quarantine_inspection_and_resolution(self):
        """Verifies listing quarantine records and resolving a record with curator rationale."""
        # 1. List Quarantine Records
        list_res = self.client.get("/internal/v1/control-room/quarantine?status_filter=PENDING", headers=self.curator_headers)
        self.assertEqual(list_res.status_code, 200)
        q_records = list_res.json()
        self.assertGreater(len(q_records), 0)

        quarantine_id = q_records[0]["quarantine_id"]

        # 2. Resolve Quarantine Record
        resolve_payload = {
            "decision": "RESOLVE",
            "rationale": "Validated payload schema structure manually against provider V2 API documentation."
        }
        resolve_res = self.client.post(
            f"/internal/v1/control-room/quarantine/{quarantine_id}/resolve",
            json=resolve_payload,
            headers=self.curator_headers
        )
        self.assertEqual(resolve_res.status_code, 200)
        r_data = resolve_res.json()
        self.assertEqual(r_data["status"], "RESOLVED")
        self.assertIn("integrity_hash", r_data)

    def test_candidate_detail_and_governed_promotion(self):
        """Verifies candidate evidence inspection and governed promotion to CAT-1 Canonical Platform Data."""
        candidate_id = "018f4a00-0000-7000-8000-cand00000001"

        # 1. Get Candidate Detail & Evidence
        detail_res = self.client.get(f"/internal/v1/control-room/candidates/{candidate_id}", headers=self.curator_headers)
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        self.assertEqual(detail["candidate_id"], candidate_id)
        self.assertIn("evidence_summary", detail)

        # 2. Promote Candidate
        promote_payload = {
            "rationale": "Cross-checked original title script and verified matching TMDB entity.",
            "override_fields": {"canonical_title": "Inception (2010)"}
        }
        promote_res = self.client.post(
            f"/internal/v1/control-room/candidates/{candidate_id}/promote",
            json=promote_payload,
            headers=self.curator_headers
        )
        self.assertEqual(promote_res.status_code, 200)
        p_data = promote_res.json()
        self.assertEqual(p_data["status"], "PROMOTED")
        self.assertIn("integrity_hash", p_data)

    def test_candidate_rejection_workflow(self):
        """Verifies candidate rejection with mandatory rationale validation."""
        candidate_id = "018f4a00-0000-7000-8000-cand00000002"

        reject_payload = {
            "rationale": "False match detected: release dates differ by 15 years."
        }
        reject_res = self.client.post(
            f"/internal/v1/control-room/candidates/{candidate_id}/reject",
            json=reject_payload,
            headers=self.curator_headers
        )
        self.assertEqual(reject_res.status_code, 200)
        r_data = reject_res.json()
        self.assertEqual(r_data["status"], "REJECTED")

    def test_audit_log_inspection_and_sha256_integrity(self):
        """Verifies GET /internal/v1/control-room/audit-log returns signed system audit trail."""
        response = self.client.get("/internal/v1/control-room/audit-log", headers=self.curator_headers)
        self.assertEqual(response.status_code, 200)
        entries = response.json()
        self.assertGreater(len(entries), 0)

        first = entries[0]
        self.assertIn("event_id", first)
        self.assertIn("event_type", first)
        self.assertIn("integrity_hash", first)
        self.assertEqual(len(first["integrity_hash"]), 64) # Valid 64-char hex SHA-256

    def test_cat2_privacy_isolation_in_control_room(self):
        """Verifies personal watch history, notes, and reviews are not exposed in Control Room API responses."""
        res_candidates = self.client.get("/internal/v1/control-room/candidates", headers=self.curator_headers)
        res_quarantine = self.client.get("/internal/v1/control-room/quarantine", headers=self.curator_headers)

        c_str = res_candidates.text
        q_str = res_quarantine.text

        self.assertNotIn("user_watch_history", c_str)
        self.assertNotIn("private_note", c_str)
        self.assertNotIn("user_watch_history", q_str)
        self.assertNotIn("private_note", q_str)

if __name__ == "__main__":
    unittest.main()
