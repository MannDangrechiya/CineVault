# CineVault OS — JWT / JWKS Token Validator Module (Phase 9.10 — P0 Fix)
# Implements DEC-API-DEF-02, OIDC / JWT signature validation & claim checking
# P0 Fix: Replaced mock JWKS resolver with real HTTP fetch + RS256 cryptographic verification

import time
import json
import base64
import typing
import logging
from dataclasses import dataclass, field
from ..config import config

logger = logging.getLogger("cinevault.auth.jwt_validator")

# Lazy-import jose to avoid hard failure if not installed in test environments
try:
    from jose import jwt as jose_jwt
    from jose import jwk as jose_jwk
    from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
    _JOSE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _JOSE_AVAILABLE = False
    logger.warning("python-jose not installed. Cryptographic JWT signature verification unavailable.")

try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:  # pragma: no cover
    _HTTPX_AVAILABLE = False
    logger.warning("httpx not installed. JWKS HTTP fetch unavailable.")


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


class JWKSKeyResolver:
    """
    Real JWKS Key Resolver with TTL-based in-memory cache.
    Fetches public keys from the Keycloak JWKS endpoint and caches them for
    JWKS_CACHE_TTL_SECONDS (default 300 seconds / 5 minutes) to avoid
    hammering the identity provider on every request.
    """

    JWKS_CACHE_TTL_SECONDS = 300  # 5-minute cache

    def __init__(self, jwks_uri: str):
        self.jwks_uri = jwks_uri
        # key_cache: maps kid -> JWK key dict
        self._key_cache: typing.Dict[str, dict] = {}
        self._last_fetch: float = 0.0

    def _should_refresh(self) -> bool:
        return (time.monotonic() - self._last_fetch) >= self.JWKS_CACHE_TTL_SECONDS

    def _fetch_jwks(self) -> None:
        """Fetches JWKS from the identity provider and refreshes the key cache."""
        if not _HTTPX_AVAILABLE:
            raise JWTValidationError(
                "httpx is required for JWKS fetching but is not installed."
            )
        try:
            response = httpx.get(self.jwks_uri, timeout=5.0)
            response.raise_for_status()
            jwks = response.json()
            self._key_cache = {
                key["kid"]: key
                for key in jwks.get("keys", [])
                if "kid" in key
            }
            self._last_fetch = time.monotonic()
            logger.info(
                "JWKS refreshed from %s — %d keys cached.",
                self.jwks_uri,
                len(self._key_cache),
            )
        except httpx.HTTPError as exc:
            raise JWTValidationError(
                f"Failed to fetch JWKS from '{self.jwks_uri}': {exc}"
            ) from exc
        except Exception as exc:
            raise JWTValidationError(
                f"Unexpected error while fetching JWKS: {exc}"
            ) from exc

    def get_public_key(self, kid: str) -> dict:
        """
        Returns the JWK public key dict for the given key ID.
        Refreshes the cache if stale or if the kid is unknown (key rotation).
        """
        if self._should_refresh() or kid not in self._key_cache:
            self._fetch_jwks()

        if kid not in self._key_cache:
            raise JWTValidationError(
                f"Public key '{kid}' not found in JWKS after refresh. "
                "The token may have been issued by an unknown or misconfigured identity provider."
            )

        return self._key_cache[kid]


class JWTValidator:
    """
    Authoritative OIDC JWT Token Validator for CineVault API Gateway / Backend Services.

    Validation pipeline:
    1. Structural decode (3-part JWT check).
    2. Cryptographic RS256 signature verification via real JWKS public key.
       - In local_development: signature verification is SKIPPED (Keycloak may be offline).
       - In staging / production: signature verification is MANDATORY.
    3. Claim validation: issuer, audience, expiry (exp), not-before (nbf).
    """

    def __init__(
        self,
        expected_issuer: str = None,
        expected_audience: str = None,
    ):
        self.expected_issuer = expected_issuer or config.keycloak_issuer
        self.expected_audience = expected_audience or config.keycloak_audience
        self.jwks_resolver = JWKSKeyResolver(jwks_uri=config.jwks_uri)

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
        Cryptographically verifies the JWT RS256 signature against the JWKS public key.

        - In local_development: SKIPPED (Keycloak may not be running).
          A warning is emitted so developers are aware.
        - In staging/production: MANDATORY. Raises JWTValidationError on failure.
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

        kid = header.get("kid")
        if not kid:
            raise JWTValidationError(
                "JWT header is missing the 'kid' (Key ID) claim required for JWKS lookup."
            )

        alg = header.get("alg", "RS256").upper()
        if alg not in {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"}:
            raise JWTValidationError(
                f"Unsupported or insecure JWT algorithm '{alg}'. "
                "Only RSA and EC algorithms are permitted."
            )

        try:
            jwk_key_dict = self.jwks_resolver.get_public_key(kid)
            public_key = jose_jwk.construct(jwk_key_dict, algorithm=alg)
            # jose.jwt.decode performs full signature + claims verification internally.
            # We call it here solely for signature verification; claim validation is
            # done separately in validate_claims() for finer-grained error messages.
            jose_jwt.decode(
                token,
                public_key,
                algorithms=[alg],
                audience=self.expected_audience,
                issuer=self.expected_issuer,
                options={"verify_exp": False},  # expiry checked in validate_claims
            )
        except ExpiredSignatureError:
            # Signature is valid but exp has passed — let validate_claims report this
            pass
        except JWTClaimsError as exc:
            raise JWTValidationError(f"JWT claims rejected during signature verification: {exc}") from exc
        except JWTError as exc:
            raise JWTValidationError(
                f"JWT RS256 signature verification failed: {exc}"
            ) from exc
        except JWTValidationError:
            raise
        except Exception as exc:
            raise JWTValidationError(
                f"Unexpected error during signature verification: {exc}"
            ) from exc

    def validate_claims(
        self,
        payload: dict,
        now: typing.Optional[int] = None,
    ) -> SecurityTokenClaims:
        """Validates standard JWT claims: issuer, audience, expiry, not-before."""
        if now is None:
            now = int(time.time())

        # 1. Issuer Validation
        iss = payload.get("iss")
        if not iss or iss != self.expected_issuer:
            raise JWTValidationError(
                f"Invalid issuer: expected '{self.expected_issuer}', got '{iss}'."
            )

        # 2. Audience Validation
        aud = payload.get("aud")
        if not aud:
            raise JWTValidationError("Missing audience claim 'aud'.")
        valid_audiences = {self.expected_audience, "cinevault-public-client"}
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

        # Extract Realm Roles & Authentication Method Reference
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
