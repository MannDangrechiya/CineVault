# CineVault OS — Authentication & Token Issuance Router (P0 Fix)
# P0 Fix: Removed arbitrary-password login and email-based role assignment.
# Local dev now uses bcrypt-hashed credential store; staging/production returns 501.

import time
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..config import config
from ..auth.dependencies import require_authenticated_user
from ..auth.jwt_validator import SecurityTokenClaims
from ..auth.user_directory import load_local_user_store as _load_local_user_store

logger = logging.getLogger("cinevault.routers.auth")

# Lazy-import jose for local dev HS256 JWT signing
try:
    from jose import jwt as jose_jwt
    _JOSE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _JOSE_AVAILABLE = False

# Import bcrypt directly for password verification
try:
    import bcrypt
    _BCRYPT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _BCRYPT_AVAILABLE = False

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

    if not _BCRYPT_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "bcrypt is not installed. Cannot verify passwords. "
                "Run: pip install bcrypt"
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
    try:
        password_bytes = body.password.encode("utf-8")[:72]
        hash_bytes = user_record["hash"].encode("utf-8")
        password_valid = bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as exc:
        logger.error("Bcrypt checkpw failed: %s", exc)
        password_valid = False

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


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=LoginResponse)
async def refresh(body: RefreshRequest):
    """
    Exchanges a still-valid refresh token for a fresh access token, without
    requiring the user to re-enter credentials.

    This endpoint didn't exist at all until now: the Next.js BFF's refresh
    flow (middleware.ts / api/proxy) was built to call it (or the real
    Keycloak token endpoint) once an access token expired, but real Keycloak
    has been down in this environment (`docker ps` shows it Exited days ago)
    and there was nowhere else for a local-dev-issued `rt_local_*` refresh
    token to be redeemed. Combined with a separate bug where the session
    cookie's own expiry never actually reflected the real ~24h access-token
    lifetime, the refresh path never even got a chance to fire -- every
    authenticated call after ~24h silently sent an already-expired token:
    endpoints requiring auth 401'd, endpoints with an optional-auth fallback
    ran as the anonymous default user instead (looked like success, wrote to
    nobody's real account). See WEB_FEATURE_AUDIT.md.

    - In local_development: validates the `rt_local_{user_id}_{issued_at}`
      opaque reference format (not cryptographically significant, matching
      how /login mints it -- this endpoint's whole reason to exist is local
      dev without a running Keycloak), re-resolves that user_id against the
      local credential store, and mints a fresh JWT + refresh token pair.
    - In staging / production: 501, same as /login -- real deployments use
      Keycloak's own token endpoint directly, never this one.
    """
    if config.environment not in ("local_development",):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "Local refresh-token exchange is only available in local development. "
                "Use the Keycloak OIDC token endpoint in staging and production."
            ),
        )

    if not _JOSE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="python-jose is not installed. Cannot issue JWT tokens.",
        )

    token = (body.refresh_token or "").strip()
    parts = token.split("_")
    if len(parts) < 4 or parts[0] != "rt" or parts[1] != "local":
        logger.warning("Refresh attempted with malformed/foreign refresh token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unrecognized refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # user_id (a UUID, hyphens not underscores) is everything between the
    # "rt_local_" prefix and the final "_<issued_at timestamp>" segment.
    user_id = "_".join(parts[2:-1])

    local_users = _load_local_user_store()
    user_record = next(
        (rec for rec in local_users.values() if rec.get("user_id") == user_id),
        None,
    )
    if not user_record:
        logger.warning("Refresh token references unknown user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token no longer maps to a known account. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = next(
        (addr for addr, rec in local_users.items() if rec.get("user_id") == user_id),
        f"{user_id}@cinevault.local",
    )
    username = email.split("@")[0]
    roles = user_record["roles"]

    access_token = _generate_local_dev_jwt(
        user_id=user_id,
        email=email,
        username=username,
        roles=roles,
    )
    new_refresh_token = f"rt_local_{user_id}_{int(time.time())}"

    logger.info("Refreshed access token for user_id=%s via local refresh flow", user_id)

    return LoginResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user_id=user_id,
        email=email,
        roles=roles,
    )


class UserIdentityResponse(BaseModel):
    sub: str
    email: Optional[str] = None
    username: Optional[str] = None
    roles: List[str] = []


@router.get("/me", response_model=UserIdentityResponse)
async def get_current_user_identity(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
):
    """
    Returns safe identity information for the current authenticated user.
    Never exposes tokens, client secrets, or credentials.
    """
    return UserIdentityResponse(
        sub=claims.sub,
        email=claims.email,
        username=claims.preferred_username,
        roles=claims.roles,
    )

