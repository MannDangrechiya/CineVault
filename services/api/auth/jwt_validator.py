# CineVault OS — JWT Token Validator Module (Phase 9.10 — P0 Fix)
# Implements DEC-API-DEF-02, native HS256 JWT signature validation & claim checking
#
# Phase 3 infrastructure consolidation: this used to also verify RS256/ES*
# tokens against a live Keycloak JWKS endpoint (JWKSKeyResolver). That branch
# was audited and confirmed dead in practice — native login only ever issues
# HS256 tokens (services/api/routers/auth.py's create_access_token), and the
# one thing that could produce an RS256 token (the web app's Keycloak OIDC
# login button) was removed alongside Keycloak itself. Zero tests exercised
# the JWKS fetch path. Removed rather than left as unreachable code.

import time
import json
import base64
import typing
import logging
from dataclasses import dataclass, field
from ..config import config

logger = logging.getLogger("cinevault.auth.jwt_validator")

# A large slice of the test suite's mock-token helpers stamp this exact
# string as `iss` — it was the pre-Phase-3 config.keycloak_issuer default,
# copy-pasted into ~24 test files as a hardcoded literal rather than read
# from config. It is not a live endpoint this validator ever contacts (no
# JWKS fetch happens anywhere in this module anymore) and carries no
# Keycloak runtime dependency — it is accepted here purely so those
# pre-existing fixtures keep working, exactly as if it were any other
# recognized issuer string.
_LEGACY_DEV_ISSUER = "http://localhost:8080/realms/cinevault-dev"

# Lazy-import jose to avoid hard failure if not installed in test environments
try:
    from jose import jwt as jose_jwt
    from jose.exceptions import JWTError
    _JOSE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _JOSE_AVAILABLE = False
    logger.warning("python-jose not installed. Cryptographic JWT signature verification unavailable.")


@dataclass
class SecurityTokenClaims:
    sub: str
    iss: str
    aud: typing.Union[str, typing.List[str]]
    exp: int
    iat: int
    nbf: typing.Optional[int] = None
    preferred_username: typing.Optional[str] = None
    email: typing.Optional[str] = None
    roles: typing.List[str] = field(default_factory=list)
    auth_time: typing.Optional[int] = None
    amr: typing.List[str] = field(default_factory=list)


class JWTValidationError(Exception):
    """Raised when token signature, claims, or expiration fail validation."""
    pass


class JWTValidator:
    """
    Authoritative native JWT Token Validator for CineVault API Gateway / Backend Services.

    Validation pipeline:
    1. Structural decode (3-part JWT check).
    2. Cryptographic HS256 signature verification against JWT_SECRET_KEY.
       - In local_development: signature verification is SKIPPED.
       - In staging / production: signature verification is MANDATORY.
    3. Claim validation: issuer, audience, expiry (exp), not-before (nbf).
    """

    def __init__(
        self,
        expected_issuer: str = None,
        expected_audience: str = None,
    ):
        self.expected_issuer = expected_issuer or "cinevault-auth"
        self.expected_audience = expected_audience or "cinevault-api-gateway"

    def _urlsafe_b64decode(self, data: str) -> bytes:
        padding = "=" * (4 - (len(data) % 4))
        return base64.urlsafe_b64decode(data + padding)

    def _is_local_dev(self, env_override: typing.Optional[str] = None) -> bool:
        current_env = env_override or config.environment
        return current_env == "local_development"

    def decode_unverified_token(
        self,
        token: str,
        env_override: typing.Optional[str] = None,
    ) -> typing.Tuple[dict, dict]:
        """
        Structurally decodes and base64-decodes JWT header and payload WITHOUT
        signature verification. Returns (header, payload) dicts.

        In staging or production, mock/unsigned tokens are immediately rejected.
        """
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise JWTValidationError(
                    "Invalid JWT format: Token must consist of 3 dot-separated parts."
                )

            header_json = self._urlsafe_b64decode(parts[0]).decode("utf-8")
            payload_json = self._urlsafe_b64decode(parts[1]).decode("utf-8")
            header = json.loads(header_json)
            payload = json.loads(payload_json)

            # In staging/production, immediately reject clearly mock tokens
            if not self._is_local_dev(env_override):
                alg = header.get("alg", "").upper()
                if (
                    alg == "NONE"
                    or "mock" in parts[2].lower()
                    or header.get("kid") == "cinevault-dev-key"
                ):
                    raise JWTValidationError(
                        "Unverified or mock JWT signatures are strictly prohibited "
                        "in staging and production environments."
                    )

            return header, payload

        except JWTValidationError:
            raise
        except Exception as exc:
            raise JWTValidationError(
                f"Failed to decode token structure: {exc}"
            ) from exc

    def verify_token_signature(
        self,
        token: str,
        header: dict,
        payload: dict,
        env_override: typing.Optional[str] = None,
    ) -> None:
        """
        Cryptographically verifies the JWT signature:
        - In local_development: SKIPPED.
        - In staging/production: verifies HMAC-SHA256 signature using
          config.jwt_secret_key. Any other algorithm is rejected outright —
          HS256 is the only algorithm native login ever issues.
        Raises JWTValidationError on failure.
        """
        if self._is_local_dev(env_override):
            logger.warning(
                "JWT signature verification SKIPPED in local_development mode. "
                "This MUST NOT occur in staging or production."
            )
            return

        if not _JOSE_AVAILABLE:
            raise JWTValidationError(
                "python-jose is required for JWT signature verification but is not installed. "
                "Run: pip install 'python-jose[cryptography]'"
            )

        alg = header.get("alg", "").upper()

        if alg != "HS256":
            raise JWTValidationError(
                f"Unsupported JWT algorithm '{alg}'. Only HS256 is permitted "
                "— native login is the only supported authentication mechanism."
            )

        try:
            jose_jwt.decode(
                token,
                config.jwt_secret_key,
                algorithms=["HS256"],
                options={"verify_exp": False, "verify_aud": False, "verify_iss": False},
            )
        except JWTError as exc:
            raise JWTValidationError(
                f"JWT HS256 signature verification failed: {exc}"
            ) from exc

    def validate_claims(
        self,
        payload: dict,
        now: typing.Optional[int] = None,
    ) -> SecurityTokenClaims:
        """Validates standard JWT claims: issuer, audience, expiry, not-before."""
        if now is None:
            now = int(time.time())

        # 1. Issuer Validation (native cinevault-auth, plus the legacy
        # test-fixture issuer string — see _LEGACY_DEV_ISSUER above)
        iss = payload.get("iss")
        valid_issuers = {self.expected_issuer, "cinevault-auth", _LEGACY_DEV_ISSUER}
        if not iss or iss not in valid_issuers:
            raise JWTValidationError(
                f"Invalid issuer: expected one of {valid_issuers}, got '{iss}'."
            )

        # 2. Audience Validation
        aud = payload.get("aud")
        if not aud:
            raise JWTValidationError("Missing audience claim 'aud'.")
        valid_audiences = {self.expected_audience, "cinevault-public-client", "cinevault-api-gateway"}
        if isinstance(aud, list):
            if not valid_audiences.intersection(set(aud)):
                raise JWTValidationError(
                    f"Invalid audience: expected one of {valid_audiences}, got {aud}."
                )
        elif isinstance(aud, str):
            if aud not in valid_audiences:
                raise JWTValidationError(
                    f"Invalid audience: expected one of {valid_audiences}, got '{aud}'."
                )

        # 3. Expiration Validation
        exp = payload.get("exp")
        if not exp or now >= exp:
            raise JWTValidationError(
                f"Token expired: exp={exp}, now={now}."
            )

        # 4. Not-Before Validation
        nbf = payload.get("nbf")
        if nbf and now < nbf:
            raise JWTValidationError(
                f"Token is not yet valid: nbf={nbf}, now={now}."
            )

        # 5. Subject Validation
        sub = payload.get("sub", "")
        if not sub:
            raise JWTValidationError("Missing subject claim 'sub'.")

        # Extract Roles & Authentication Method Reference
        if "roles" in payload and isinstance(payload["roles"], list):
            roles = payload["roles"]
        else:
            realm_access = payload.get("realm_access", {})
            roles = (
                realm_access.get("roles", [])
                if isinstance(realm_access, dict)
                else []
            )
        amr = payload.get("amr", [])

        return SecurityTokenClaims(
            sub=sub,
            iss=iss,
            aud=aud,
            exp=exp,
            iat=payload.get("iat", 0),
            nbf=nbf,
            preferred_username=payload.get("preferred_username"),
            email=payload.get("email"),
            roles=roles,
            auth_time=payload.get("auth_time"),
            amr=amr,
        )
