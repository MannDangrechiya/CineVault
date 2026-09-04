# CineVault OS — Database Integration Module
# Connects API service directly to PostgreSQL (ADR-001, superseded by the
# Phase 3 infrastructure consolidation: PgBouncer was removed after auditing
# found SQLAlchemy already used NullPool — zero pooling of its own — and
# delegated all connection-count control to PgBouncer's transaction-mode
# pool. CI's test suite already ran this way, straight against
# postgres:5432, with no PgBouncer container in the loop at all. Postgres's
# own default max_connections is 100; with 4 uvicorn workers (see
# services/api/Dockerfile) each opening up to pool_size + max_overflow
# connections, the bounded pool below caps total usage at 4 * 10 = 40,
# leaving headroom for Keycloak, Flyway, and manual psql/GUI access. Raise
# postgres's max_connections before raising these if this ever needs to
# scale past the "owner + a handful of friends" profile this stack targets.

import socket
import sys
import logging
from typing import Dict, Any, AsyncGenerator, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from .config import config

logger = logging.getLogger("cinevault.database")

# Build async database connection URL
async_db_url = f"postgresql+asyncpg://{config.postgres_user}:{config.postgres_password}@{config.postgres_host}:{config.postgres_port}/{config.postgres_db}"

# asyncpg connections are bound to the event loop that created them.
# A real pool (below) retains and reuses open connections across checkouts —
# exactly what production wants, since one Uvicorn worker runs exactly one
# long-lived event loop for its whole life. But this test suite runs many
# unittest.IsolatedAsyncioTestCase / TestClient-based tests, each of which
# gets its own fresh event loop, while this module's `engine` is a single
# import-time singleton shared by all of them — a connection checked out in
# one test's loop and reused in a later test's *different* loop raises
# "got Future ... attached to a different loop" (confirmed the hard way: this
# surfaced as ~130 unrelated-looking test failures the first time this pool
# was made real, all downstream of the same cross-loop reuse). NullPool never
# retains a connection between checkouts, which is why the suite has always
# safely run this way — detect that case and keep it, everywhere else use a
# real bounded pool sized for Postgres's default max_connections=100 across
# 4 uvicorn workers (see services/api/Dockerfile): 4 * (pool_size +
# max_overflow) = 40, leaving headroom for Keycloak, Flyway, and manual
# psql/GUI access. Raise postgres's max_connections before raising these if
# this ever needs to scale past the "owner + a handful of friends" profile
# this stack targets.
_running_under_pytest = "pytest" in sys.modules
_pool_kwargs: Dict[str, Any] = (
    {"poolclass": NullPool}
    if _running_under_pytest
    else {
        "poolclass": AsyncAdaptedQueuePool,
        "pool_size": 5,
        "max_overflow": 5,
        "pool_pre_ping": True,
    }
)

engine = create_async_engine(
    async_db_url,
    echo=config.debug,
    connect_args={
        # No TLS between the API and Postgres on the internal Docker network
        # (the Postgres container has no TLS configured); asyncpg's default
        # SSL-first negotiation against a plaintext listener breaks the
        # socket mid-handshake.
        "ssl": False,
        "timeout": 5.0,
    },
    **_pool_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

def is_db_available() -> bool:
    """Fast probe of Postgres connectivity."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.2)
        result = sock.connect_ex((config.postgres_host, config.postgres_port))
        sock.close()
        return result == 0
    except Exception:
        return False

async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """Dependency for providing asynchronous database session per request.

    On connection failure, this only degrades to `yield None` (letting individual
    repositories fall back to their explicit dev-only in-memory paths) when
    `config.allow_seed_fallback` is set — which is only true by default in
    local_development (see config.py). In every other environment a connection
    failure raises a real 503 so production/staging outages surface as errors
    instead of silently masquerading as empty or fabricated data.
    """
    if not is_db_available():
        if config.allow_seed_fallback:
            logger.warning("Database connection unavailable, falling back to seed repository.")
            yield None
            return
        else:
            logger.error("Database connection unavailable")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable",
            )

    has_yielded = False
    try:
        async with AsyncSessionLocal() as session:
            has_yielded = True
            try:
                yield session
                await session.commit()
            except Exception:
                try:
                    await session.rollback()
                except Exception:
                    pass
                raise
    except (socket.error, OSError) as e:
        if not has_yielded:
            if config.allow_seed_fallback:
                logger.warning(f"Database connection unavailable, falling back to seed repository: {e}")
                yield None
            else:
                logger.error(f"Database connection unavailable: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database connection unavailable",
                )
        else:
            raise

class DatabaseManager:
    """Manages Postgres connection checks and health status."""

    def __init__(self):
        self.host = config.postgres_host
        self.port = config.postgres_port
        self.db = config.postgres_db
        self.user = config.postgres_user

    def check_health(self) -> Dict[str, Any]:
        """
        Verifies connectivity to the Postgres socket.
        Returns health status dictionary for readiness probe.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()

            if result == 0:
                return {
                    "status": "HEALTHY",
                    "target": f"{self.host}:{self.port}",
                    "database": self.db
                }
            else:
                return {
                    "status": "UNHEALTHY",
                    "target": f"{self.host}:{self.port}",
                    "error": f"Connection refused or unreachable (code {result})"
                }
        except Exception as e:
            return {
                "status": "UNHEALTHY",
                "target": f"{self.host}:{self.port}",
                "error": str(e)
            }

db_manager = DatabaseManager()


async def async_check_db_health() -> bool:
    """Executes a real SQL query (SELECT 1) to verify end-to-end database
    connectivity through the async engine. Returns True if the query succeeds,
    False otherwise. This complements the socket-level check in DatabaseManager
    by verifying that the full connection pipeline (auth, pool, query) works."""
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            row = result.scalar()
            return row == 1
    except Exception as e:
        logger.warning(f"Database async health check failed: {e}")
        return False
