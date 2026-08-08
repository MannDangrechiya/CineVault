# CineVault OS — Phase 2 Authentication & Authorization Test Suite
# Validates OIDC JWT claims, PKCE S256, RBAC enforcement, Service Isolation, Privileged Sessions & High-Risk MFA

import time
import unittest
from services.api.auth.jwt_validator import JWTValidator, JWTValidationError, SecurityTokenClaims
from services.api.auth.rbac import (
    RBACPolicyEngine,
    AuthorizationError,
    HighRiskAuthError,
    verify_pkce_s256,
    CURATOR_SESSION_IDLE_TIMEOUT_SECONDS,
    HIGH_RISK_FRESH_AUTH_WINDOW_SECONDS
)

class TestAuthenticationAndAuthorization(unittest.TestCase):

    def test_pkce_s256_verification(self):
        # Valid RFC 7636 Appendix A PKCE pair
        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        challenge = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
        self.assertTrue(verify_pkce_s256(verifier, challenge))

        # Invalid verifier
        self.assertFalse(verify_pkce_s256("wrong_verifier", challenge))

    def test_jwt_claims_validation_success(self):
        validator = JWTValidator()
        now = int(time.time())
        payload = {
            "sub": "user-uuid-123",
            "iss": "http://localhost:8080/realms/cinevault-dev",
            "aud": "cinevault-api-gateway",
            "exp": now + 900,
            "iat": now,
            "preferred_username": "dev_curator",
            "realm_access": {
                "roles": ["AuthenticatedUser", "Curator"]
            },
            "amr": ["webauthn"]
        }
        claims = validator.validate_claims(payload, now=now)
        self.assertEqual(claims.sub, "user-uuid-123")
        self.assertIn("Curator", claims.roles)
        self.assertTrue(RBACPolicyEngine.is_curator(claims))

    def test_jwt_claims_expired_token(self):
        validator = JWTValidator()
        now = int(time.time())
        payload = {
            "sub": "user-uuid-123",
            "iss": "http://localhost:8080/realms/cinevault-dev",
            "aud": "cinevault-api-gateway",
            "exp": now - 100,  # Expired
            "iat": now - 1000
        }
        with self.assertRaises(JWTValidationError):
            validator.validate_claims(payload, now=now)

    def test_curator_privileged_session_idle_timeout(self):
        now = int(time.time())
        claims = SecurityTokenClaims(
            sub="curator-123",
            iss="http://localhost:8080/realms/cinevault-dev",
            aud="cinevault-api-gateway",
            exp=now + 900,
            iat=now,
            roles=["Curator"]
        )

        # Active session (active 5 mins ago)
        RBACPolicyEngine.enforce_curator_access(claims, last_active_time=now - 300, now=now)

        # Expired idle session (active 16 mins ago > 15 min limit)
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_curator_access(claims, last_active_time=now - 1000, now=now)

    def test_service_identity_isolation(self):
        # Ingestion service must NOT be allowed to write directly to canonical schema
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-ingest-service", "CANONICAL_WRITE_TITLE")

        # Ingestion service allowed to write to ingestion raw payload capture
        RBACPolicyEngine.enforce_service_isolation("cinevault-ingest-service", "RAW_PAYLOAD_INSERT")

    def test_high_risk_fresh_webauthn_success(self):
        now = int(time.time())
        claims = SecurityTokenClaims(
            sub="admin-123",
            iss="http://localhost:8080/realms/cinevault-dev",
            aud="cinevault-api-gateway",
            exp=now + 900,
            iat=now,
            roles=["SystemAdmin"]
        )

        # High risk operation with fresh WebAuthn (authenticated 30s ago)
        RBACPolicyEngine.enforce_high_risk_operation(
            claims=claims,
            operation_name="ENTITY_MERGE",
            auth_time=now - 30,
            amr=["webauthn"],
            now=now
        )

    def test_high_risk_totp_rejection(self):
        now = int(time.time())
        claims = SecurityTokenClaims(
            sub="admin-123",
            iss="http://localhost:8080/realms/cinevault-dev",
            aud="cinevault-api-gateway",
            exp=now + 900,
            iat=now,
            roles=["SystemAdmin"]
        )

        # High risk operation with TOTP -> MUST BE REJECTED
        with self.assertRaises(HighRiskAuthError):
            RBACPolicyEngine.enforce_high_risk_operation(
                claims=claims,
                operation_name="ENTITY_MERGE",
                auth_time=now - 10,
                amr=["totp"],
                now=now
            )

    def test_high_risk_expired_webauthn_window(self):
        now = int(time.time())
        claims = SecurityTokenClaims(
            sub="admin-123",
            iss="http://localhost:8080/realms/cinevault-dev",
            aud="cinevault-api-gateway",
            exp=now + 900,
            iat=now,
            roles=["SystemAdmin"]
        )

        # High risk operation with WebAuthn older than 60s (75s ago) -> MUST BE REJECTED
        with self.assertRaises(HighRiskAuthError):
            RBACPolicyEngine.enforce_high_risk_operation(
                claims=claims,
                operation_name="ROLE_PROMOTION",
                auth_time=now - 75,
                amr=["webauthn"],
                now=now
            )

if __name__ == "__main__":
    unittest.main()
