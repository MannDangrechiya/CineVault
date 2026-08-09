# CineVault OS — Authentication & Token Issuance Router (P0 Fix)
# P0 Fix: Removed arbitrary-password login and email-based role assignment.
# Local dev now uses bcrypt-hashed credential store; staging/production returns 501.

import os
import time
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..config import config

logger = logging.getLogger("cinevault.routers.auth")

# Lazy-import jose for local dev HS256 JWT signing
try:
    from jose import jwt as jose_jwt
    _JOSE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _JOSE_AVAILABLE = False

# Lazy-import passlib for bcrypt password verification
try:
    from passlib.context import CryptContext
    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _PASSLIB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PASSLIB_AVAILABLE = False
    _pwd_context = None

router = APIRouter(prefix="/v1/auth", tags=["Authentication & Identity"])


# ---------------------------------------------------------------------------
# Local Dev Credential Store
# ---------------------------------------------------------------------------
# Credentials are loaded from environment variables.  Each entry maps an email
# address to a bcrypt hash of the password.  To generate a hash:
#   python -c "from passlib.context import CryptContext; print(CryptContext(['bcrypt']).hash('your_password'))"
#
# The DEFAULT_* values below are intentionally insecure placeholder hashes for
# first-time dev setup.  Override via environment variables in your .env file.
#
# Dev default:  email=dev@cinevault.local  password=devpass
#               email=curator@cinevault.local  password=curatorpass
# ---------------------------------------------------------------------------

def _load_local_user_store() -> dict:
    """
    Builds the local dev credential store from environment variables.
    Schema: { email: { "hash": bcrypt_hash, "user_id": uuid_str, "roles": [...] } }
    """
    return {
        os.getenv("DEV_USER_EMAIL", "dev@cinevault.local"): {
            "hash": os.getenv(
                "DEV_USER_PASSWORD_HASH",
                # Default hash for password "devpass" — CHANGE IN YOUR .env
                "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGrmKGVkU2U4q3FJR8rMJWOF8Bu",
            ),
            "user_id": os.getenv(
                "DEV_USER_UUID",
                "018f0000-0000-7000-8000-000000000001",
            ),
            "roles": ["authenticated_user"],
        },
        os.getenv("DEV_CURATOR_EMAIL", "curator@cinevault.local"): {
            "hash": os.getenv(
                "DEV_CURATOR_PASSWORD_HASH",
                # Default hash for password "curatorpass" — CHANGE IN YOUR .env
                "$2b$12$vXJQ2lM3XCo1mOaFZTrJQOFKLKJ6cLbhKV3ViVJC6Fk6GiOrjLqT6",
            ),
            "user_id": os.getenv(
                "DEV_CURATOR_UUID",
                "018f0000-0000-7000-8000-000000000002",
            ),
            "roles": ["authenticated_user", "curator"],
        },
    }


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400
    user_id: str
    email: str
    roles: List[str]


def _generate_local_dev_jwt(
    user_id: str,
    email: str,
    username: str,
    roles: List[str],
    expires_in: int = 86400,
) -> str:
    """
    Generates an HS256-signed JWT for local development sessions.
    Signed with JWT_SECRET_KEY from config — NOT a mock unsigned token.
    This token WILL be rejected in staging/production by the JWT validator.
    """
    if not _JOSE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "python-jose is not installed. Cannot issue JWT tokens. "
                "Run: pip install 'python-jose[cryptography]'"
            ),
        )

    now = int(time.time())
    payload = {
        "iss": config.keycloak_issuer,
        "aud": config.keycloak_audience,
        "sub": user_id,
        "email": email,
        "preferred_username": username,
        "iat": now,
        "exp": now + expires_in,
        "nbf": now,
        "realm_access": {"roles": roles},
        "amr": ["pwd"],
        # 'kid' header not set for HS256 — dev-mode only
    }
    # HS256 signed with the configured local dev secret, tagged with cinevault-dev-key
    token = jose_jwt.encode(
        payload,
        config.jwt_secret_key,
        algorithm="HS256",
        headers={"kid": "cinevault-dev-key"},
    )
    return token


# Backward-compatible alias for unit test suites
generate_dev_jwt = _generate_local_dev_jwt


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """
    Authenticates user credentials and issues a signed JWT.

    - In local_development: validates against the local bcrypt credential store
      and returns an HS256-signed JWT.
    - In staging / production: returns 501 Not Implemented. Clients must
      authenticate via Keycloak PKCE/OIDC flow directly.
    """
    # --- Production guard: this endpoint is for local dev only ---
    if config.environment not in ("local_development",):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "Direct password login is only available in local development. "
                "Use the Keycloak OIDC authorization code flow in staging and production."
            ),
        )

    if not body.email or not body.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both email and password are required.",
        )

    if not _PASSLIB_AVAILABLE or _pwd_context is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "passlib is not installed. Cannot verify passwords. "
                "Run: pip install 'passlib[bcrypt]'"
            ),
        )

    # Load credential store fresh each call (allows env-var hot-reload in dev)
    local_users = _load_local_user_store()

    # --- Email lookup ---
    user_record = local_users.get(body.email.lower().strip())
    if not user_record:
        # Use the same error message as wrong password to prevent user enumeration
        logger.warning("Login attempt for unknown email: %s", body.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- Password verification (bcrypt constant-time compare) ---
    password_valid = _pwd_context.verify(body.password, user_record["hash"])
    if not password_valid:
        logger.warning("Failed password verification for email: %s", body.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = user_record["user_id"]
    roles = user_record["roles"]
    username = body.email.split("@")[0]

    access_token = _generate_local_dev_jwt(
        user_id=user_id,
        email=body.email,
        username=username,
        roles=roles,
    )
    # Refresh token: opaque reference token for local dev (not cryptographically significant)
    refresh_token = f"rt_local_{user_id}_{int(time.time())}"

    logger.info(
        "Successful local dev login: user_id=%s email=%s roles=%s",
        user_id,
        body.email,
        roles,
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id,
        email=body.email,
        roles=roles,
    )
