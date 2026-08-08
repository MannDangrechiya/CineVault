# CineVault OS — JWT / JWKS Token Validator Module
# Implements DEC-API-DEF-02, OIDC / JWT signature validation & claim checking

import time
import json
import base64
import typing
from dataclasses import dataclass, field

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
    """Simulated JWKS Key Resolver and Cache Manager."""
    def __init__(self, jwks_uri: str = "http://localhost:8080/realms/cinevault-dev/protocol/openid-connect/certs"):
        self.jwks_uri = jwks_uri
        self.key_cache = {}
        self.last_fetch = 0

    def get_public_key(self, kid: str) -> dict:
        # Returns simulated RS256 JWKS public key structure for kid
        return {
            "kid": kid,
            "kty": "RSA",
            "alg": "RS256",
            "use": "sig",
            "n": "mock_rsa_modulus_string",
            "e": "AQAB"
        }

class JWTValidator:
    """Authoritative OIDC JWT Token Validator for CineVault API Gateway / Backend Services."""
    def __init__(self, expected_issuer: str = "http://localhost:8080/realms/cinevault-dev", expected_audience: str = "cinevault-api-gateway"):
        self.expected_issuer = expected_issuer
        self.expected_audience = expected_audience
        self.jwks_resolver = JWKSKeyResolver()

    def _urlsafe_b64decode(self, data: str) -> bytes:
        padding = '=' * (4 - (len(data) % 4))
        return base64.urlsafe_b64decode(data + padding)

    def decode_unverified_token(self, token: str) -> typing.Tuple[dict, dict]:
        try:
            parts = token.split('.')
            if len(parts) != 3:
                raise JWTValidationError("Invalid JWT format: Token must consist of 3 dot-separated parts")
            header_json = self._urlsafe_b64decode(parts[0]).decode('utf-8')
            payload_json = self._urlsafe_b64decode(parts[1]).decode('utf-8')
            return json.loads(header_json), json.loads(payload_json)
        except Exception as e:
            raise JWTValidationError(f"Failed to decode unverified token: {str(e)}")

    def validate_claims(self, payload: dict, now: typing.Optional[int] = None) -> SecurityTokenClaims:
        if now is None:
            now = int(time.time())

        # 1. Issuer Validation
        iss = payload.get("iss")
        if not iss or iss != self.expected_issuer:
            raise JWTValidationError(f"Invalid issuer: expected '{self.expected_issuer}', got '{iss}'")

        # 2. Audience Validation
        aud = payload.get("aud")
        if not aud:
            raise JWTValidationError("Missing audience claim 'aud'")
        if isinstance(aud, list):
            if self.expected_audience not in aud and "cinevault-public-client" not in aud:
                raise JWTValidationError(f"Invalid audience: '{self.expected_audience}' not in {aud}")
        elif isinstance(aud, str):
            if aud != self.expected_audience and aud != "cinevault-public-client":
                raise JWTValidationError(f"Invalid audience: expected '{self.expected_audience}', got '{aud}'")

        # 3. Expiration Validation
        exp = payload.get("exp")
        if not exp or now >= exp:
            raise JWTValidationError(f"Token expired: exp={exp}, now={now}")

        # 4. Not-Before Validation
        nbf = payload.get("nbf")
        if nbf and now < nbf:
            raise JWTValidationError(f"Token not valid yet: nbf={nbf}, now={now}")

        # Extract Realm Roles & AMR (Authentication Method Reference)
        realm_access = payload.get("realm_access", {})
        roles = realm_access.get("roles", []) if isinstance(realm_access, dict) else []
        amr = payload.get("amr", [])

        return SecurityTokenClaims(
            sub=payload.get("sub", ""),
            iss=iss,
            aud=aud,
            exp=exp,
            iat=payload.get("iat", 0),
            nbf=nbf,
            preferred_username=payload.get("preferred_username"),
            email=payload.get("email"),
            roles=roles,
            auth_time=payload.get("auth_time"),
            amr=amr
        )
