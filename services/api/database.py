# CineVault OS — Database Integration Module
# Connects API service to PostgreSQL via PgBouncer transaction pooler (ADR-001)

import socket
import logging
from typing import Dict, Any, AsyncGenerator, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from .config import config

logger = logging.getLogger("cinevault.database")

# Build async database connection URL
async_db_url = f"postgresql+asyncpg://{config.postgres_user}:{config.postgres_password}@{config.pgbouncer_host}:{config.pgbouncer_port}/{config.postgres_db}"

engine = create_async_engine(
    async_db_url,
    poolclass=NullPool,
    echo=config.debug,
    connect_args={
        # PgBouncer runs in `transaction` pool mode (docker-compose.yml), which can
        # hand a query to a different backend Postgres connection between statements.
        # asyncpg's default server-side prepared-statement cache assumes a stable
        # connection, so disable it to issue plain (unprepared) queries instead.
        "statement_cache_size": 0,
        # PgBouncer has no TLS configured; asyncpg's default SSL-first negotiation
        # against a plaintext listener breaks the socket mid-handshake.
        "ssl": False,
    }
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """Dependency for providing asynchronous database session per request.

    On connection failure, this only degrades to `yield None` (letting individual
    repositories fall back to their explicit dev-only in-memory paths) when
    `config.allow_seed_fallback` is set — which is only true by default in
    local_development (see config.py). In every other environment a connection
    failure raises a real 503 so production/staging outages surface as errors
    instead of silently masquerading as empty or fabricated data.
    """
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    except (socket.error, OSError) as e:
        if config.allow_seed_fallback:
            logger.warning(f"Database connection unavailable, falling back to seed repository: {e}")
            yield None
        else:
            logger.error(f"Database connection unavailable: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection unavailable",
            )

class DatabaseManager:
    """Manages PgBouncer connection pool checks and health status."""
    
    def __init__(self):
        self.host = config.pgbouncer_host
        self.port = config.pgbouncer_port
        self.db = config.postgres_db
        self.user = config.postgres_user

    def check_health(self) -> Dict[str, Any]:
        """
        Verifies connectivity to PgBouncer socket.
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
                    "pool_mode": "transaction",
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
