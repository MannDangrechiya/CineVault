# CineVault OS — Keycloak OIDC & JWKS Token Validation Integration Tests (Phase 9.10)

import pytest
import time
from services.api.auth.jwt_validator import JWTValidator, JWTValidationError
from services.api.routers.auth import generate_dev_jwt

def test_dev_mode_token_decoding():
    validator = JWTValidator()
    token = generate_dev_jwt(
        user_id="usr_test_001",
        email="test@cinevault.local",
        username="test_user",
        roles=["authenticated_user"],
    )
    header, payload = validator.decode_unverified_token(token, env_override="local_development")
    claims = validator.validate_claims(payload)

    assert claims.sub == "usr_test_001"
    assert claims.email == "test@cinevault.local"
    assert "authenticated_user" in claims.roles

def test_staging_mode_rejects_mock_jwt_signatures():
    validator = JWTValidator()
    mock_token = generate_dev_jwt(
        user_id="usr_hacker_001",
        email="hacker@cinevault.local",
        username="hacker",
        roles=["curator"],
    )

    with pytest.raises(JWTValidationError, match="Unverified or mock JWT signatures"):
        validator.decode_unverified_token(mock_token, env_override="staging")

def test_production_mode_rejects_mock_jwt_signatures():
    validator = JWTValidator()
    mock_token = generate_dev_jwt(
        user_id="usr_hacker_002",
        email="hacker@cinevault.local",
        username="hacker",
        roles=["system_admin"],
    )

    with pytest.raises(JWTValidationError, match="Unverified or mock JWT signatures"):
        validator.decode_unverified_token(mock_token, env_override="production")

def test_claims_validation_expired_token():
    validator = JWTValidator()
    now = int(time.time())
    expired_payload = {
        "iss": "http://localhost:8080/realms/cinevault-dev",
        "aud": "cinevault-api-gateway",
        "sub": "usr_test",
        "exp": now - 3600,
        "iat": now - 7200,
        "realm_access": {"roles": ["authenticated_user"]}
    }

    with pytest.raises(JWTValidationError, match="Token expired"):
        validator.validate_claims(expired_payload, now=now)

def test_claims_validation_invalid_issuer():
    validator = JWTValidator()
    now = int(time.time())
    invalid_iss_payload = {
        "iss": "http://malicious-server.org/realms/evil",
        "aud": "cinevault-api-gateway",
        "sub": "usr_test",
        "exp": now + 3600,
        "iat": now,
        "realm_access": {"roles": ["authenticated_user"]}
    }

    with pytest.raises(JWTValidationError, match="Invalid issuer"):
        validator.validate_claims(invalid_iss_payload, now=now)
