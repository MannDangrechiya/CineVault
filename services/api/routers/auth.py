# CineVault OS — Authentication & Token Issuance Router
# Implements Phase 1 Sovereign Native Authentication Architecture

import time
import re
import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..config import config
from ..database import get_db
from ..auth.dependencies import require_authenticated_user
from ..auth.jwt_validator import SecurityTokenClaims
from ..auth.user_directory import load_local_user_store as _load_local_user_store
from ..repositories.auth import auth_repository
from ..models.social import InviteTokenModel, ReferralModel
from ..repositories.social import SEED_INVITES

logger = logging.getLogger("cinevault.routers.auth")

# Lazy-import jose for HS256 JWT signing
try:
    from jose import jwt as jose_jwt
    from jose.exceptions import JWTError, ExpiredSignatureError
    _JOSE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _JOSE_AVAILABLE = False

router = APIRouter(prefix="/v1/auth", tags=["Authentication & Identity"])

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    invite_code: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400
    user_id: str
    email: str
    roles: List[str]


class UserIdentityResponse(BaseModel):
    sub: str
    email: Optional[str] = None
    username: Optional[str] = None
    roles: List[str] = []


def create_access_token(
    user_id: str,
    email: str,
    username: str,
    roles: List[str],
    expires_in: int = 86400,
) -> str:
    """
    Generates an HS256-signed JWT access token.
    Signed with JWT_SECRET_KEY from config.
    """
    if not _JOSE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="python-jose is not installed. Cannot issue JWT tokens.",
        )

    now = int(time.time())
    payload = {
        "jti": uuid.uuid4().hex,
        "iss": "cinevault-auth",
        "aud": "cinevault-api-gateway",
        "sub": user_id,
        "user_id": user_id,
        "email": email,
        "preferred_username": username,
        "roles": roles,
        "realm_access": {"roles": roles},
        "token_type": "access",
        "iat": now,
        "nbf": now,
        "exp": now + expires_in,
        "amr": ["pwd"],
    }
    return jose_jwt.encode(
        payload,
        config.jwt_secret_key,
        algorithm="HS256",
        headers={"kid": "cinevault-native-key", "alg": "HS256"},
    )


def create_refresh_token(
    user_id: str,
    email: str,
    expires_in: int = 30 * 86400,
) -> str:
    """
    Generates an HS256-signed JWT refresh token valid for 30 days.
    """
    if not _JOSE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="python-jose is not installed. Cannot issue JWT tokens.",
        )

    now = int(time.time())
    payload = {
        "jti": uuid.uuid4().hex,
        "iss": "cinevault-auth",
        "aud": "cinevault-api-gateway",
        "sub": user_id,
        "email": email,
        "token_type": "refresh",
        "iat": now,
        "nbf": now,
        "exp": now + expires_in,
    }
    return jose_jwt.encode(
        payload,
        config.jwt_secret_key,
        algorithm="HS256",
        headers={"kid": "cinevault-native-key", "alg": "HS256"},
    )


def _generate_local_dev_jwt(
    user_id: str,
    email: str,
    username: str,
    roles: List[str],
    expires_in: int = 86400,
) -> str:
    """
    Generates an HS256-signed JWT for local development sessions.
    Tagged with kid='cinevault-dev-key' which is rejected outside local_development.
    """
    if not _JOSE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="python-jose is not installed. Cannot issue JWT tokens.",
        )

    now = int(time.time())
    payload = {
        "iss": config.keycloak_issuer,
        "aud": config.keycloak_audience,
        "sub": user_id,
        "email": email,
        "preferred_username": username,
        "roles": roles,
        "realm_access": {"roles": roles},
        "iat": now,
        "exp": now + expires_in,
        "nbf": now,
        "amr": ["pwd"],
    }
    return jose_jwt.encode(
        payload,
        config.jwt_secret_key,
        algorithm="HS256",
        headers={"kid": "cinevault-dev-key"},
    )


# Backward-compatible alias for unit test suites
generate_dev_jwt = _generate_local_dev_jwt


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Authenticates user credentials against the sovereign auth.user database
    and issues signed native JWT access and refresh tokens.
    """
    if not body.email or not body.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both email and password are required.",
        )

    email = body.email.lower().strip()
    user = await auth_repository.get_by_email(db, email)

    if not user:
        logger.warning("Login attempt for unknown email: %s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not auth_repository.verify_password(body.password, user.password_hash):
        logger.warning("Failed password verification for email: %s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning("Login attempt for deactivated user: %s", email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = str(user.user_id)
    username = user.email.split("@")[0]
    roles = user.roles

    access_token = create_access_token(
        user_id=user_id_str,
        email=user.email,
        username=username,
        roles=roles,
    )
    refresh_token = create_refresh_token(
        user_id=user_id_str,
        email=user.email,
    )

    logger.info("Successful login for user_id=%s, email=%s", user_id_str, user.email)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id_str,
        email=user.email,
        roles=roles,
    )


@router.post("/register", response_model=LoginResponse)
async def register(
    body: RegisterRequest,
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Registers a new friend account into CineVault OS.
    Strictly invite-gated: requires a valid, unused, non-expired invite code from social.invite_token.
    Role assignment is hardcoded to 'authenticated_user' to prevent privilege escalation.
    """
    email = (body.email or "").lower().strip()
    if not email or not EMAIL_REGEX.match(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address format.",
        )

    password = body.password or ""
    if len(password) < 8 or len(password) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be between 8 and 72 characters.",
        )

    invite_code = (body.invite_code or "").strip()
    if not invite_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite code is required for registration.",
        )

    # 1. Validate Invite Code against social.invite_token
    inviter_id: Optional[uuid.UUID] = None
    now = datetime.now(timezone.utc)

    if db is not None:
        stmt = select(InviteTokenModel).where(InviteTokenModel.token == invite_code)
        invite_record = (await db.execute(stmt)).scalar_one_or_none()
        if not invite_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invite code.",
            )
        if invite_record.expires_at and invite_record.expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invite code has expired.",
            )
        if invite_record.converted_user_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invite code has already been used.",
            )
        inviter_id = invite_record.inviter_id
    else:
        seed_invite = SEED_INVITES.get(invite_code)
        if not seed_invite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invite code.",
            )
        if seed_invite.get("expires_at") and seed_invite["expires_at"] < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invite code has expired.",
            )
        if seed_invite.get("converted_user_id") is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invite code has already been used.",
            )
        inviter_id = seed_invite.get("inviter_id")

    # 2. Prevent Duplicate Email Registration
    existing_user = await auth_repository.get_by_email(db, email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    # 3. Create auth.user with strictly authenticated_user role
    password_hash = auth_repository.hash_password(password)
    new_user_id = uuid.uuid4()
    user = await auth_repository.create_user(
        db=db,
        email=email,
        password_hash=password_hash,
        roles=["authenticated_user"],
        is_active=True,
        user_id=new_user_id,
    )

    # 4. Consume Invite Token & Log Referral
    if db is not None and invite_record:
        invite_record.converted_user_id = new_user_id
        if inviter_id:
            referral = ReferralModel(
                referral_id=uuid.uuid4(),
                inviter_id=inviter_id,
                invitee_id=new_user_id,
                status="PENDING",
                created_at=now,
            )
            db.add(referral)
        await db.flush()
    elif seed_invite:
        seed_invite["converted_user_id"] = new_user_id

    user_id_str = str(user.user_id)
    username = email.split("@")[0]
    roles = ["authenticated_user"]

    access_token = create_access_token(
        user_id=user_id_str,
        email=user.email,
        username=username,
        roles=roles,
    )
    refresh_token = create_refresh_token(
        user_id=user_id_str,
        email=user.email,
    )

    logger.info("Successfully registered user: user_id=%s, email=%s", user_id_str, email)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id_str,
        email=user.email,
        roles=roles,
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    body: RefreshRequest,
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Exchanges a valid refresh token for a fresh access token and rotated refresh token.
    Supports native signed HS256 tokens and legacy local reference tokens.
    Verifies that the user account is still active in auth.user.
    """
    token = (body.refresh_token or "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required.",
        )

    user_id: Optional[str] = None

    if token.startswith("rt_local_"):
        # Legacy local development reference token: rt_local_{user_id}_{timestamp}
        parts = token.split("_")
        if len(parts) >= 4:
            user_id = "_".join(parts[2:-1])
    else:
        # Native signed JWT refresh token
        try:
            payload = jose_jwt.decode(
                token,
                config.jwt_secret_key,
                algorithms=["HS256"],
                options={"verify_exp": True, "verify_aud": False, "verify_iss": False},
            )
            if payload.get("token_type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type: expected refresh token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            user_id = payload.get("sub")
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or unrecognized refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_repository.get_by_id(db, user_id)
    if not user:
        logger.warning("Refresh token references unknown user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token no longer maps to a known account. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning("Refresh token attempt for inactive user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled or inactive. Please contact the administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = str(user.user_id)
    username = user.email.split("@")[0]
    roles = user.roles

    new_access_token = create_access_token(
        user_id=user_id_str,
        email=user.email,
        username=username,
        roles=roles,
    )
    new_refresh_token = create_refresh_token(
        user_id=user_id_str,
        email=user.email,
    )

    logger.info("Refreshed access token for user_id=%s", user_id_str)

    return LoginResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user_id=user_id_str,
        email=user.email,
        roles=roles,
    )


@router.get("/me", response_model=UserIdentityResponse)
async def get_current_user_identity(
    claims: SecurityTokenClaims = Depends(require_authenticated_user),
):
    """
    Returns safe identity information for the current authenticated user.
    Never exposes tokens, password hashes, or credentials.
    """
    return UserIdentityResponse(
        sub=claims.sub,
        email=claims.email,
        username=claims.preferred_username,
        roles=claims.roles,
    )
