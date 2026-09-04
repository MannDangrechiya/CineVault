# CineVault OS — Production System Bootstrap Utility
# Initializes the initial System Administrator account and generates the
# first invite token for invite-gated registration on a fresh production deployment.
#
# Idempotent & Safe:
# - Detects if a system_admin already exists and exits without modifying credentials.
# - Never logs plaintext passwords or writes credentials to git.
# - Enforces strict validation (bcrypt work factor 12, email regex, 8-72 char passwords).

import argparse
import asyncio
import getpass
import logging
import os
import re
import secrets
import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import asyncpg

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
logger = logging.getLogger("cinevault.bootstrap")


def validate_credentials(email: str, password: str) -> Tuple[str, str]:
    clean_email = (email or "").strip().lower()
    if not clean_email or not EMAIL_REGEX.match(clean_email):
        raise ValueError("Invalid administrator email address format.")

    if not password or len(password) < 8 or len(password) > 72:
        raise ValueError("Administrator password must be between 8 and 72 characters.")

    return clean_email, password


def hash_password(password: str) -> str:
    import bcrypt

    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(12)
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


async def check_existing_admin(conn: asyncpg.Connection) -> Optional[str]:
    row = await conn.fetchrow(
        """
        SELECT email FROM auth.user
        WHERE 'system_admin' = ANY(roles)
        LIMIT 1;
        """
    )
    return row["email"] if row else None


async def ensure_canonical_taxonomy(conn: asyncpg.Connection) -> int:
    """Verifies and ensures minimum reference content types exist."""
    row = await conn.fetchrow("SELECT COUNT(*) AS cnt FROM canonical.content_type;")
    count = row["cnt"] if row else 0
    if count == 0:
        await conn.execute(
            """
            INSERT INTO canonical.content_type (content_type_id, type_name, description) VALUES
            ('movie', 'Feature Film', 'Full-length motion picture released for theatrical, streaming, or physical media.'),
            ('tv_series', 'Television Series', 'Episodic television or web broadcast content.'),
            ('short_film', 'Short Film', 'Motion picture with a runtime under 40 minutes.')
            ON CONFLICT (content_type_id) DO NOTHING;
            """
        )
        row = await conn.fetchrow("SELECT COUNT(*) AS cnt FROM canonical.content_type;")
        count = row["cnt"] if row else 0
    return count


async def create_bootstrap_admin_and_invite(
    conn: asyncpg.Connection,
    email: str,
    password_hash: str,
) -> Tuple[uuid.UUID, str]:
    admin_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=30)
    token = secrets.token_urlsafe(16)

    async with conn.transaction():
        # 1. Insert System Admin user
        await conn.execute(
            """
            INSERT INTO auth.user (user_id, email, password_hash, roles, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7);
            """,
            admin_id,
            email,
            password_hash,
            ["system_admin", "curator", "authenticated_user"],
            True,
            now,
            now,
        )

        # 2. Insert initial bootstrap invite token
        preview_json = (
            '{"top_genres": ["Cinema", "Sci-Fi", "Drama"], "recent_watched_titles": [], "total_watched_count": 0}'
        )
        await conn.execute(
            """
            INSERT INTO social.invite_token (token, inviter_id, preview_data_json, expires_at, created_at)
            VALUES ($1, $2, $3::jsonb, $4, $5);
            """,
            token,
            admin_id,
            preview_json,
            expires_at,
            now,
        )

    return admin_id, token


async def run_bootstrap(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    admin_email: Optional[str] = None,
    admin_password: Optional[str] = None,
) -> int:
    conn = None
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            timeout=15.0,
        )

        existing_admin = await check_existing_admin(conn)
        if existing_admin:
            print(f"[INFO] CineVault OS is already bootstrapped. Existing system admin: {existing_admin}")
            return 0

        # Validate or prompt for credentials
        email = admin_email or os.getenv("BOOTSTRAP_ADMIN_EMAIL")
        raw_password = admin_password or os.getenv("BOOTSTRAP_ADMIN_PASSWORD")

        if not email:
            if sys.stdin.isatty():
                email = input("Enter System Administrator Email: ").strip()
            else:
                print("[ERROR] Administrator email must be provided via --email or BOOTSTRAP_ADMIN_EMAIL.", file=sys.stderr)
                return 1

        if not raw_password:
            if sys.stdin.isatty():
                raw_password = getpass.getpass("Enter System Administrator Password (8-72 chars): ").strip()
            else:
                print("[ERROR] Administrator password must be provided via --password or BOOTSTRAP_ADMIN_PASSWORD.", file=sys.stderr)
                return 1

        clean_email, clean_password = validate_credentials(email, raw_password)
        pw_hash = hash_password(clean_password)

        # Ensure reference taxonomy is ready
        taxonomy_count = await ensure_canonical_taxonomy(conn)

        # Create admin and initial invite
        admin_id, invite_token = await create_bootstrap_admin_and_invite(conn, clean_email, pw_hash)

        print("=" * 60)
        print("CineVault OS — Production Bootstrap Successful")
        print("=" * 60)
        print(f"System Admin Email : {clean_email}")
        print(f"System Admin ID    : {admin_id}")
        print(f"Assigned Roles     : system_admin, curator, authenticated_user")
        print(f"Canonical Taxonomy : {taxonomy_count} content types verified")
        print(f"Initial Invite Code: {invite_token}")
        print(f"Invite Link Path   : /register?code={invite_token}")
        print("=" * 60)
        print("[NOTICE] Store this initial invite code securely to register the first friend account.")
        return 0

    except Exception as exc:
        print(f"[ERROR] Production bootstrap failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if conn:
            await conn.close()


def main():
    parser = argparse.ArgumentParser(description="CineVault OS — Production Bootstrap CLI")
    parser.add_argument("--host", default=os.getenv("POSTGRES_HOST", "localhost"), help="PostgreSQL host")
    parser.add_argument("--port", type=int, default=int(os.getenv("POSTGRES_PORT", "5432")), help="PostgreSQL port")
    parser.add_argument("--db", default=os.getenv("POSTGRES_DB", "cinevault"), help="Database name")
    parser.add_argument("--user", default=os.getenv("POSTGRES_USER", "cinevault_admin"), help="Database username")
    parser.add_argument("--password", default=os.getenv("POSTGRES_PASSWORD", ""), help="Database password")
    parser.add_argument("--email", default=None, help="System administrator email")
    parser.add_argument("--admin-password", default=None, help="System administrator password")

    args = parser.parse_args()

    exit_code = asyncio.run(
        run_bootstrap(
            host=args.host,
            port=args.port,
            database=args.db,
            user=args.user,
            password=args.password,
            admin_email=args.email,
            admin_password=args.admin_password,
        )
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
