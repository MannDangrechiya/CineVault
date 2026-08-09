# CineVault OS — Authorization & Security Policy Enforcement Module
# Implements CineVault RBAC, PKCE S256, Privileged Session Timeouts, High-Risk WebAuthn Guard

import hashlib
import base64
import time
import typing
from .jwt_validator import SecurityTokenClaims

class AuthorizationError(Exception):
    """Raised when access is denied due to role or security policy violation."""
    pass

class HighRiskAuthError(Exception):
    """Raised when high-risk operation fresh authentication check fails."""
    pass

# Privileged session idle timeout constant (15 minutes)
CURATOR_SESSION_IDLE_TIMEOUT_SECONDS = 900

# Fresh WebAuthn authentication window for high-risk operations (60 seconds)
HIGH_RISK_FRESH_AUTH_WINDOW_SECONDS = 60

# High-Risk Operations List (DEC-SEC-OPN-01)
HIGH_RISK_OPERATIONS = {
    "ENTITY_MERGE",
    "ENTITY_SPLIT",
    "CANONICAL_PROMOTION",
    "PROVIDER_CONFIG_CHANGE",
    "ROLE_PROMOTION",
    "PERSONAL_DATA_DISPUTE_RESOLUTION",
    "CREDENTIAL_KEY_OPERATION",
    "SECURITY_CONFIG_CHANGE"
}

def verify_pkce_s256(code_verifier: str, code_challenge: str) -> bool:
    """Validates PKCE S256 verifier against authorization code challenge."""
    if not code_verifier or not code_challenge:
        return False
    digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    calculated_challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
    return calculated_challenge == code_challenge.rstrip('=')

class RBACPolicyEngine:
    """Enforces CineVault human RBAC roles and machine service identity boundaries."""

    @staticmethod
    def is_anonymous(claims: typing.Optional[SecurityTokenClaims]) -> bool:
        return claims is None or "Anonymous" in claims.roles

    @staticmethod
    def is_authenticated_user(claims: SecurityTokenClaims) -> bool:
        roles = {r.lower() for r in claims.roles}
        return bool(roles.intersection({"authenticateduser", "authenticated_user", "curator", "systemadmin", "system_admin"}))

    @staticmethod
    def is_curator(claims: SecurityTokenClaims) -> bool:
        roles = {r.lower() for r in claims.roles}
        return bool(roles.intersection({"curator", "systemadmin", "system_admin"}))

    @staticmethod
    def is_system_admin(claims: SecurityTokenClaims) -> bool:
        roles = {r.lower() for r in claims.roles}
        return bool(roles.intersection({"systemadmin", "system_admin"}))

    @classmethod
    def enforce_read_access(cls, claims: typing.Optional[SecurityTokenClaims]) -> None:
        """All users (including Anonymous) can read public catalog data."""
        pass

    @classmethod
    def enforce_curator_access(cls, claims: SecurityTokenClaims, last_active_time: int, now: typing.Optional[int] = None) -> None:
        """Enforces Curator role requirement and 15-minute privileged session idle timeout."""
        if not cls.is_curator(claims):
            raise AuthorizationError("Access denied: Requires Curator or SystemAdmin role")

        if now is None:
            now = int(time.time())

        # Enforce 15-minute privileged session idle timeout
        idle_duration = now - last_active_time
        if idle_duration > CURATOR_SESSION_IDLE_TIMEOUT_SECONDS:
            raise AuthorizationError("Privileged session expired: 15-minute idle timeout exceeded. Re-authentication required.")

    @classmethod
    def enforce_service_isolation(cls, client_id: str, requested_action: str) -> None:
        """Enforces zero-trust service identity boundaries across all compute workloads."""
        if client_id == "cinevault-ingest-service":
            if requested_action.startswith("CANONICAL_WRITE"):
                raise AuthorizationError("Security Violation: Ingestion service is strictly prohibited from writing to canonical schema.")

        elif client_id == "cinevault-ai-service":
            if requested_action.startswith("CANONICAL_WRITE"):
                raise AuthorizationError("Security Violation: AI Proposal service operates strictly in quality.ai_proposal_staging (CAT-6) and is prohibited from direct canonical write access.")

        elif client_id == "cinevault-analytics-service":
            if requested_action.startswith("PERSONAL") or requested_action.startswith("CANONICAL_WRITE"):
                raise AuthorizationError("Security Violation: Analytics service is restricted to canonical read-only access and has ZERO access to personal CAT-2 data.")

        elif client_id == "cinevault-sync-processor":
            if requested_action.startswith("CANONICAL_WRITE"):
                raise AuthorizationError("Security Violation: Sync processor service operates strictly within personal schema and cannot modify canonical catalog data.")

        elif client_id == "cinevault-quality-service":
            if requested_action.startswith("CANONICAL_WRITE"):
                raise AuthorizationError("Security Violation: Quality service isolates raw payload quarantine and cannot write directly to canonical schema.")

        elif client_id == "cinevault-public-api":
            if requested_action.startswith("INTERNAL_ADMIN") or requested_action.startswith("CANONICAL_WRITE"):
                raise AuthorizationError("Security Violation: Public API nodes cannot execute internal admin operations or direct canonical mutations.")

    @classmethod
    def enforce_high_risk_operation(cls, claims: SecurityTokenClaims, operation_name: str, auth_time: typing.Optional[int], amr: typing.List[str], now: typing.Optional[int] = None) -> None:
        """
        Enforces Fresh WebAuthn requirement for High-Risk Operations (DEC-SEC-OPN-01):
        1. Operation must be in high-risk set.
        2. TOTP MUST NOT authorize high-risk operations (TOTP is rejected).
        3. WebAuthn/FIDO2 required in AMR claims.
        4. Fresh authentication window <= 60 seconds.
        """
        if operation_name not in HIGH_RISK_OPERATIONS:
            return

        if now is None:
            now = int(time.time())

        # 1. Reject TOTP for high-risk operations
        if "totp" in amr or "otp" in amr:
            raise HighRiskAuthError("Security Policy Rejection: TOTP authentication is prohibited for high-risk operations.")

        # 2. Require WebAuthn / FIDO2
        if "webauthn" not in amr and "fido2" not in amr:
            raise HighRiskAuthError("Security Policy Failure: High-risk operations require WebAuthn/FIDO2 hardware key authentication.")

        # 3. Require Fresh Authentication within 60-second window
        if not auth_time:
            raise HighRiskAuthError("Security Policy Failure: Missing auth_time timestamp for fresh authentication check.")

        auth_age = now - auth_time
        if auth_age > HIGH_RISK_FRESH_AUTH_WINDOW_SECONDS:
            raise HighRiskAuthError(f"Security Policy Failure: Fresh WebAuthn authentication window expired ({auth_age}s > {HIGH_RISK_FRESH_AUTH_WINDOW_SECONDS}s). Re-authenticate with security key.")
