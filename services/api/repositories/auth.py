# CineVault OS — Authentication Repository Layer
# Implements Phase 1 Sovereign Native Authentication Architecture

import logging
import uuid
from typing import Optional, List, Union
from datetime import datetime, timezone

try:
    import bcrypt
    _BCRYPT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _BCRYPT_AVAILABLE = False

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.auth import AuthUserModel
from ..auth.user_directory import load_local_user_store

logger = logging.getLogger("cinevault.repositories.auth")

# In-memory registry fallback for tests running without an active PostgreSQL session
_MEMORY_USERS: dict = {}


class InMemoryAuthUser:
    """Lightweight in-memory duck-type for AuthUserModel when DB session is not provided."""
    def __init__(self, user_id: uuid.UUID, email: str, password_hash: str, roles: List[str], is_active: bool = True):
        self.user_id = user_id
        self.email = email
        self.password_hash = password_hash
        self.roles = roles
        self.is_active = is_active
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class AuthRepository:
    """Repository handling auth.user queries, password hashing, and user creation."""

    @staticmethod
    def verify_password(plain_password: str, password_hash: str) -> bool:
        """Constant-time bcrypt password check."""
        if not _BCRYPT_AVAILABLE or not plain_password or not password_hash:
            return False
        try:
            pw_bytes = plain_password.encode("utf-8")[:72]
            hash_bytes = password_hash.encode("utf-8")
            return bcrypt.checkpw(pw_bytes, hash_bytes)
        except Exception as exc:
            logger.error("Bcrypt checkpw error: %s", exc)
            return False

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """Secure bcrypt password hashing with work factor 12."""
        if not _BCRYPT_AVAILABLE:
            raise RuntimeError("bcrypt is required for password hashing but is not installed.")
        pw_bytes = plain_password.encode("utf-8")[:72]
        salt = bcrypt.gensalt(12)
        return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")

    async def get_by_email(
        self, db: Optional[AsyncSession], email: str
    ) -> Optional[Union[AuthUserModel, InMemoryAuthUser]]:
        """Finds user by email address (case-insensitive)."""
        normalized_email = email.lower().strip()

        if db is not None:
            stmt = select(AuthUserModel).where(AuthUserModel.email == normalized_email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                return user

        # Fallback to in-memory runtime users
        if normalized_email in _MEMORY_USERS:
            return _MEMORY_USERS[normalized_email]

        # Fallback to dev store
        dev_store = load_local_user_store()
        if normalized_email in dev_store:
            rec = dev_store[normalized_email]
            return InMemoryAuthUser(
                user_id=uuid.UUID(rec["user_id"]),
                email=normalized_email,
                password_hash=rec["hash"],
                roles=rec.get("roles", ["authenticated_user"]),
                is_active=True,
            )

        return None

    async def get_by_id(
        self, db: Optional[AsyncSession], user_id: Union[uuid.UUID, str]
    ) -> Optional[Union[AuthUserModel, InMemoryAuthUser]]:
        """Finds user by user_id UUID."""
        if isinstance(user_id, str):
            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                return None
        else:
            user_uuid = user_id

        if db is not None:
            stmt = select(AuthUserModel).where(AuthUserModel.user_id == user_uuid)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                return user

        # Fallback to in-memory runtime users
        for u in _MEMORY_USERS.values():
            if u.user_id == user_uuid:
                return u

        # Fallback to dev store
        dev_store = load_local_user_store()
        for email, rec in dev_store.items():
            if rec["user_id"] == str(user_uuid):
                return InMemoryAuthUser(
                    user_id=user_uuid,
                    email=email,
                    password_hash=rec["hash"],
                    roles=rec.get("roles", ["authenticated_user"]),
                    is_active=True,
                )

        return None

    async def create_user(
        self,
        db: Optional[AsyncSession],
        email: str,
        password_hash: str,
        roles: Optional[List[str]] = None,
        is_active: bool = True,
        user_id: Optional[uuid.UUID] = None,
    ) -> Union[AuthUserModel, InMemoryAuthUser]:
        """Creates a new auth.user record."""
        normalized_email = email.lower().strip()
        assigned_roles = roles or ["authenticated_user"]
        uid = user_id or uuid.uuid4()

        if db is not None:
            user = AuthUserModel(
                user_id=uid,
                email=normalized_email,
                password_hash=password_hash,
                roles=assigned_roles,
                is_active=is_active,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(user)
            await db.flush()
            return user
        else:
            mem_user = InMemoryAuthUser(
                user_id=uid,
                email=normalized_email,
                password_hash=password_hash,
                roles=assigned_roles,
                is_active=is_active,
            )
            _MEMORY_USERS[normalized_email] = mem_user
            return mem_user


auth_repository = AuthRepository()
