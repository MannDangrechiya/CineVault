# CineVault OS — Database Outage Safety Verification (W2 Task 6)
#
# Verifies the core safety invariant this whole W2 fallback-safety pass is
# built on: a real Postgres/PgBouncer connection failure must produce a
# real error (503 Service Unavailable) in staging/production
# (config.allow_seed_fallback=False), never a 200 OK with fabricated data.
# The local-dev convenience path (allow_seed_fallback=True) is exercised
# too, to confirm it still works and is the ONLY way `db=None` can reach a
# repository/router in this codebase (see database.py's get_db()).
#
# These tests simulate the outage by patching AsyncSessionLocal to raise
# OSError on connect, rather than actually taking down the shared dev
# Postgres instance other tests depend on.

import asyncio
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from services.api import database as database_module
from services.api.main import app
from services.api.database import get_db


class _FailingSessionContextManager:
    """Mimics AsyncSessionLocal() failing to connect -- raises on __aenter__,
    the same way a real dead PgBouncer/Postgres socket would."""

    async def __aenter__(self):
        raise OSError("Connection refused (simulated PgBouncer outage)")

    async def __aexit__(self, exc_type, exc, tb):
        return False


def test_get_db_raises_503_when_seed_fallback_disallowed():
    """The staging/production invariant: allow_seed_fallback=False means a
    connection failure is a real error, not a silently-degraded session."""

    async def _drive():
        with patch.object(database_module, "AsyncSessionLocal", return_value=_FailingSessionContextManager()), \
             patch.object(database_module.config, "allow_seed_fallback", False):
            gen = get_db()
            await gen.__anext__()

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_drive())
    assert exc_info.value.status_code == 503


def test_get_db_yields_none_when_seed_fallback_explicitly_allowed():
    """The local-dev-only convenience path: only reachable when the flag is
    explicitly true (never the accidental default outside local_development,
    see config.py's ENVIRONMENT-gated default)."""

    async def _drive():
        with patch.object(database_module, "AsyncSessionLocal", return_value=_FailingSessionContextManager()), \
             patch.object(database_module.config, "allow_seed_fallback", True):
            gen = get_db()
            return await gen.__anext__()

    result = asyncio.run(_drive())
    assert result is None


def test_real_endpoint_returns_503_not_fabricated_data_on_outage():
    """End-to-end: with get_db() simulating a production-mode outage, a real
    request to a real endpoint must come back as 503 with no catalog data
    in the body -- not a 200 OK carrying seed/demo titles."""

    async def _failing_get_db():
        with patch.object(database_module, "AsyncSessionLocal", return_value=_FailingSessionContextManager()), \
             patch.object(database_module.config, "allow_seed_fallback", False):
            gen = get_db()
            async for session in gen:
                yield session  # pragma: no cover -- never reached, get_db raises first

    app.dependency_overrides[get_db] = _failing_get_db
    try:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/v1/titles")
        assert response.status_code == 503
        body = response.text
        # None of the historically-fabricated demo titles should ever
        # appear in an outage response.
        assert "Parasite" not in body
        assert "Sholay" not in body
        assert "Dark Knight" not in body
    finally:
        app.dependency_overrides.pop(get_db, None)
