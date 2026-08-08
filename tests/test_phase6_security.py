# CineVault OS — Phase 6 Security Implementation Comprehensive Test Suite
# Validates Authentication, Authorization, RBAC, Service Identities, 3-Tier API Isolation, CAT-2 Leakage Prevention,
# Provider Secret Isolation, AI Staging Boundary, Canonical Integrity, Privileged Sessions, Audit Integrity & Cryptography Baseline

import json
import time
import unittest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.auth.jwt_validator import JWTValidator, JWTValidationError, SecurityTokenClaims
from services.api.auth.rbac import (
    RBACPolicyEngine,
    AuthorizationError,
    HighRiskAuthError,
    verify_pkce_s256,
    CURATOR_SESSION_IDLE_TIMEOUT_SECONDS,
    HIGH_RISK_FRESH_AUTH_WINDOW_SECONDS
)
from services.api.auth.audit import audit_logger, AuditLogger
from services.api.telemetry import sanitize_value, JSONFormatter, metrics_collector
from services.api.valkey import valkey_manager
from services.api.rabbitmq import rabbitmq_manager, PayloadValidationError

def generate_mock_jwt(roles: list, sub: str = "user-sec-123", exp_delta: int = 900) -> str:
    import base64
    header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    now = int(time.time())
    payload_dict = {
        "sub": sub,
        "iss": "http://localhost:8080/realms/cinevault-dev",
        "aud": "cinevault-api-gateway",
        "exp": now + exp_delta,
        "iat": now,
        "realm_access": {"roles": roles}
    }
    payload = base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(b"mock_signature").decode().rstrip("=")
    return f"{header}.{payload}.{signature}"

class TestPhase6SecurityImplementation(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.user_jwt = generate_mock_jwt(["AuthenticatedUser"], sub="user-123")
        self.curator_jwt = generate_mock_jwt(["AuthenticatedUser", "Curator"], sub="curator-456")
        self.admin_jwt = generate_mock_jwt(["AuthenticatedUser", "Curator", "SystemAdmin"], sub="admin-789")

    # 1. Zero-Trust Service Identity Security
    def test_zero_trust_service_identity_matrix(self):
        # Ingestion service prohibited from writing canonical
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-ingest-service", "CANONICAL_WRITE_TITLE")

        # AI service prohibited from direct canonical writes (CAT-6 staging only)
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-ai-service", "CANONICAL_WRITE_SYNOPSIS")

        # Analytics service prohibited from reading CAT-2 personal data or writing canonical
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-analytics-service", "PERSONAL_READ_WATCH_HISTORY")
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-analytics-service", "CANONICAL_WRITE_RELEASE")

        # Sync processor prohibited from writing canonical
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-sync-processor", "CANONICAL_WRITE_SEASON")

        # Public API node prohibited from internal admin operations
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-public-api", "INTERNAL_ADMIN_MUTATE")

    # 2. Privileged Access & High-Risk Operations
    def test_privileged_access_high_risk_operations(self):
        now = int(time.time())
        admin_claims = SecurityTokenClaims(
            sub="admin-789",
            iss="http://localhost:8080/realms/cinevault-dev",
            aud="cinevault-api-gateway",
            exp=now + 900,
            iat=now,
            roles=["SystemAdmin"]
        )

        # Canonical promotion in high-risk set -> fresh WebAuthn required
        RBACPolicyEngine.enforce_high_risk_operation(
            claims=admin_claims,
            operation_name="CANONICAL_PROMOTION",
            auth_time=now - 20,
            amr=["webauthn"],
            now=now
        )

        # Provider config change in high-risk set -> TOTP rejected
        with self.assertRaises(HighRiskAuthError):
            RBACPolicyEngine.enforce_high_risk_operation(
                claims=admin_claims,
                operation_name="PROVIDER_CONFIG_CHANGE",
                auth_time=now - 10,
                amr=["totp"],
                now=now
            )

    # 3. 3-Tier API Boundary Isolation & Headers
    def test_three_tier_api_isolation(self):
        # Public client calling /v1/titles -> 200 OK
        resp = self.client.get("/v1/titles")
        self.assertEqual(resp.status_code, 200)

        # Public client trying /internal/v1/ingestion/runs without auth -> 401 Unauthorized
        resp = self.client.get("/internal/v1/ingestion/runs")
        self.assertEqual(resp.status_code, 401)

        # Non-curator user trying /internal/v1/ingestion/runs -> 403 Forbidden
        headers = {"Authorization": f"Bearer {self.user_jwt}"}
        resp = self.client.get("/internal/v1/ingestion/runs", headers=headers)
        self.assertEqual(resp.status_code, 403)

        # Curator trying /internal/v1/ingestion/runs -> 200 OK
        headers = {"Authorization": f"Bearer {self.curator_jwt}"}
        resp = self.client.get("/internal/v1/ingestion/runs", headers=headers)
        self.assertEqual(resp.status_code, 200)

        # Verify security headers present in all responses
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")
        self.assertIn("max-age=31536000", resp.headers.get("Strict-Transport-Security", ""))

    # 4. CAT-2 Personal Data Leakage Prevention
    def test_cat2_personal_data_leakage_prevention(self):
        # Telemetry PII redaction
        sanitized_note = sanitize_value("watch_event_notes", "Secret personal notes")
        self.assertEqual(sanitized_note, "[REDACTED]")

        sanitized_email = sanitize_value("email", "user@example.com")
        self.assertEqual(sanitized_email, "[REDACTED]")

        # Queue payload safety rejection for CAT-2 personal fields
        with self.assertRaises(PayloadValidationError):
            rabbitmq_manager.validate_payload_safety({"user_id": "123", "watch_event_notes": "my private notes"})

        # Cache sanitization for CAT-2 personal fields
        dirty_json = json.dumps({"title_id": "t1", "email": "user@test.com", "watch_event_notes": "sensitive"})
        clean_cache_val = valkey_manager._sanitize_cache_value(dirty_json)
        self.assertNotIn("user@test.com", clean_cache_val)
        self.assertIn("[REDACTED]", clean_cache_val)

        # Public API responses must not leak CAT-2 data
        resp = self.client.get("/v1/titles/018f2e4a-7b31-7000-8000-123456789abc")
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertNotIn("watch_event_notes", resp_data)
        self.assertNotIn("email", resp_data)

    # 5. Secret & Provider Credential Isolation
    def test_provider_credential_isolation(self):
        # Queue payload rejection for secrets
        with self.assertRaises(PayloadValidationError):
            rabbitmq_manager.validate_payload_safety({"provider": "TMDB", "auth_token": "secret_api_key_123"})

        with self.assertRaises(PayloadValidationError):
            rabbitmq_manager.validate_payload_safety({"provider": "KOBIS", "password": "super_secret_password"})

        # Telemetry secret redaction
        self.assertEqual(sanitize_value("secret", "my_api_key"), "[REDACTED]")
        self.assertEqual(sanitize_value("authorization", "Bearer secret_token"), "[REDACTED]")

        # Raw payload endpoint returned to curator must not leak internal DB credentials
        headers = {"Authorization": f"Bearer {self.curator_jwt}"}
        resp = self.client.get("/internal/v1/ingestion/raw-payloads/payload_001", headers=headers)
        self.assertEqual(resp.status_code, 200)
        body = resp.text
        self.assertNotIn("postgres://", body)
        self.assertNotIn("amqp://", body)

    # 6. AI Canonical Write Prohibition & Staging Boundary
    def test_ai_canonical_write_prohibition(self):
        # AI proposal endpoint lists proposals in CAT-6 staging
        headers = {"Authorization": f"Bearer {self.curator_jwt}"}
        resp = self.client.get("/internal/v1/ai/proposals", headers=headers)
        self.assertEqual(resp.status_code, 200)
        proposals = resp.json()
        self.assertGreaterEqual(len(proposals), 1)
        self.assertEqual(proposals[0]["provenance_type"], "AI_GENERATED")

        # AI identity cannot execute canonical write
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-ai-service", "CANONICAL_WRITE_TITLE")

    # 7. Canonical Integrity & Curation Promotion
    def test_canonical_integrity_and_curation_promotion(self):
        headers = {"Authorization": f"Bearer {self.curator_jwt}"}
        promotion_body = {
            "target_canonical_id": "018f2e4a-7b31-7000-8000-123456789abc",
            "rationale": "High confidence match from KOBIS primary authority."
        }
        resp = self.client.post("/internal/v1/reconciliation/candidates/cand_001/promote", json=promotion_body, headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "PROMOTED")
        self.assertIn("integrity_hash", data)
        self.assertEqual(len(data["integrity_hash"]), 64)

    # 8. Privileged Session Timeout Policy
    def test_privileged_session_idle_timeout(self):
        now = int(time.time())
        curator_claims = SecurityTokenClaims(
            sub="curator-456",
            iss="http://localhost:8080/realms/cinevault-dev",
            aud="cinevault-api-gateway",
            exp=now + 900,
            iat=now,
            roles=["Curator"]
        )

        # Active privileged session (10 mins idle < 15 min limit)
        RBACPolicyEngine.enforce_curator_access(curator_claims, last_active_time=now - 600, now=now)

        # Expired privileged session (16 mins idle > 15 min limit) -> AuthorizationError
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_curator_access(curator_claims, last_active_time=now - 960, now=now)

    # 9. Audit Integrity & SHA-256 Protection
    def test_audit_integrity_sha256_verification(self):
        audit_event = audit_logger.log_event(
            event_type="AUDIT_ENTITY_MERGE",
            actor_id="admin-789",
            target_id="title-001",
            details={"source_title_id": "title-002", "reason": "Duplicate release detected"}
        )

        self.assertIn("event_id", audit_event)
        self.assertIn("timestamp", audit_event)
        self.assertEqual(audit_event["event_type"], "AUDIT_ENTITY_MERGE")
        self.assertEqual(audit_event["actor_id"], "admin-789")

        # Verify SHA-256 hash calculation reproducibility
        expected_hash = AuditLogger._compute_integrity_hash(
            event_id=audit_event["event_id"],
            timestamp=audit_event["timestamp"],
            event_type=audit_event["event_type"],
            actor_id=audit_event["actor_id"],
            target_id=audit_event["target_id"],
            details_json=json.dumps(audit_event["details"], sort_keys=True)
        )
        self.assertEqual(audit_event["integrity_hash"], expected_hash)

if __name__ == "__main__":
    unittest.main()
