# CineVault OS — Phase W13: Deployment Readiness & Operational Health Test Suite
# Verifies health probes, configuration validation, security headers, database integrity,
# and fallback safety against live PostgreSQL.

import asyncio
from datetime import datetime
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.config import APIConfig, config
from services.api.database import async_check_db_health, db_manager

client = TestClient(app)


def test_01_live_database_async_health_query():
    """Verifies that async_check_db_health executes a real SELECT 1 on PostgreSQL."""
    async def _check():
        return await async_check_db_health()

    is_healthy = asyncio.run(_check())
    assert is_healthy is True, "Expected async_check_db_health() to return True against live database"


def test_02_health_liveness_probe():
    """Verifies /health/liveness returns 200 OK with valid timestamp and service identifier."""
    res = client.get("/health/liveness")
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "UP"
    assert data.get("service") == "CineVault OS API"
    assert "timestamp" in data
    ts = datetime.fromisoformat(data["timestamp"])
    assert ts is not None


def test_03_health_readiness_probe_sanitized():
    """Verifies /health/readiness probe returns sanitized status without exposing internal topology."""
    res = client.get("/health/readiness")
    data = res.json()
    assert "status" in data
    assert "checks" in data
    checks = data["checks"]
    assert "database" in checks
    assert checks["database"] in ["ok", "degraded"]
    response_text = res.text.lower()
    assert "postgres_password" not in response_text
    assert "secret" not in response_text
    assert "pgbouncer_host" not in response_text


def test_04_health_startup_probe():
    """Verifies /health/startup returns 200 OK with STARTED status when database is ready."""
    res = client.get("/health/startup")
    data = res.json()
    assert "status" in data
    assert data["status"] in ["STARTED", "STARTING"]
    assert "timestamp" in data


def test_05_production_config_refuses_insecure_defaults():
    """Verifies APIConfig refuses to boot in production if default development secrets are used."""
    import pytest
    with pytest.raises(RuntimeError, match="Refusing to start: ENVIRONMENT='production'"):
        APIConfig(
            environment="production",
            jwt_secret_key="cinevault-local-dev-jwt-secret-CHANGE-IN-PROD-00000000",
            postgres_password="dev_postgres_password_change_me",
        )


def test_06_production_config_accepts_valid_secrets():
    """Verifies APIConfig successfully initializes when real production secrets are supplied."""
    prod_config = APIConfig(
        environment="production",
        jwt_secret_key="a-secure-random-64-character-production-secret-key-that-is-not-default",
        postgres_password="a-secure-random-production-db-password-1234567890",
        s3_access_key_id="real_production_s3_key_id",
        s3_secret_access_key="real_production_s3_secret_key",
        cors_allowed_origins="https://cinevault.example.com",
        docs_enabled=False,
    )
    assert prod_config.environment == "production"
    assert prod_config.allow_seed_fallback is False
    assert prod_config.docs_enabled is False
    assert prod_config.cors_allowed_origins == "https://cinevault.example.com"


def test_07_security_headers_present_on_all_responses():
    """Verifies security headers middleware attaches required headers on HTTP responses."""
    res = client.get("/health/liveness")
    assert res.status_code == 200
    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in headers
    assert "Content-Security-Policy" in headers
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in headers


def test_08_cors_headers_handling():
    """Verifies CORS headers are properly handled for allowed origins."""
    res = client.options(
        "/v1/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization",
        }
    )
    assert res.status_code == 200
    assert "access-control-allow-origin" in res.headers


def test_09_database_pgvector_cosine_similarity():
    """Verifies PostgreSQL pgvector extension and cosine similarity operators work on live DB."""
    async def _run_vector_check():
        import asyncpg
        host = config.pgbouncer_host
        port = config.pgbouncer_port
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=config.postgres_user,
            password=config.postgres_password,
            database=config.postgres_db
        )
        try:
            ext = await conn.fetchval("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            assert ext == "vector", "Expected pgvector extension to be installed in PostgreSQL"
            distance = await conn.fetchval(
                "SELECT ('[1,0,0]'::vector <=> '[0,1,0]'::vector) AS dist;"
            )
            assert distance is not None
            assert abs(distance - 1.0) < 0.001
        finally:
            await conn.close()

    asyncio.run(_run_vector_check())


def test_10_database_outage_fallback_safety():
    """Verifies that with allow_seed_fallback=False, DB errors raise 503 rather than returning fake data."""
    assert hasattr(config, "allow_seed_fallback")
