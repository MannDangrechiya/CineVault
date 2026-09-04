# CineVault OS — Production Bootstrap & Admin RBAC Integration Tests (Phase 3P)
# Tests blank-database bootstrap logic, idempotency, and admin authorization boundaries.

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.routers.auth import generate_dev_jwt
from services.api.scripts.bootstrap_production import (
    validate_credentials,
    hash_password,
    check_existing_admin,
    create_bootstrap_admin_and_invite,
    ensure_canonical_taxonomy,
)

client = TestClient(app)


def test_bootstrap_credential_validation():
    # Valid credentials
    email, pw = validate_credentials("admin@cinevault.org", "SuperSecurePassword123!")
    assert email == "admin@cinevault.org"
    assert pw == "SuperSecurePassword123!"

    # Invalid email
    with pytest.raises(ValueError, match="Invalid administrator email"):
        validate_credentials("not-an-email", "SuperSecurePassword123!")

    # Password too short (<8)
    with pytest.raises(ValueError, match="between 8 and 72 characters"):
        validate_credentials("admin@cinevault.org", "short")

    # Password too long (>72)
    with pytest.raises(ValueError, match="between 8 and 72 characters"):
        validate_credentials("admin@cinevault.org", "a" * 73)


def test_bootstrap_password_hashing():
    pw = "AdminSecretPass123"
    hashed = hash_password(pw)
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert hashed != pw


@pytest.mark.anyio
async def test_check_existing_admin_empty_and_populated():
    mock_conn = AsyncMock()

    # Case 1: No admin exists
    mock_conn.fetchrow.return_value = None
    result = await check_existing_admin(mock_conn)
    assert result is None

    # Case 2: Admin exists
    mock_conn.fetchrow.return_value = {"email": "sysadmin@cinevault.org"}
    result = await check_existing_admin(mock_conn)
    assert result == "sysadmin@cinevault.org"


@pytest.mark.anyio
async def test_ensure_canonical_taxonomy_detects_and_populates():
    mock_conn = AsyncMock()

    # When taxonomy already exists
    mock_conn.fetchrow.side_effect = [{"cnt": 3}]
    cnt = await ensure_canonical_taxonomy(mock_conn)
    assert cnt == 3
    assert mock_conn.execute.call_count == 0

    # When taxonomy is empty
    mock_conn.fetchrow.side_effect = [{"cnt": 0}, {"cnt": 3}]
    cnt = await ensure_canonical_taxonomy(mock_conn)
    assert cnt == 3
    assert mock_conn.execute.call_count == 1


@pytest.mark.anyio
async def test_create_bootstrap_admin_and_invite():
    mock_conn = AsyncMock()
    mock_tx = AsyncMock()
    mock_conn.transaction = MagicMock()
    mock_conn.transaction.return_value.__aenter__.return_value = mock_tx

    admin_id, token = await create_bootstrap_admin_and_invite(
        conn=mock_conn,
        email="operator@cinevault.org",
        password_hash="$2b$12$mockhash",
    )

    assert isinstance(admin_id, uuid.UUID)
    assert len(token) >= 16
    assert mock_conn.execute.call_count == 2


def test_admin_route_unauthenticated_returns_401():
    """Calling /admin/* without token must return 401."""
    response = client.post("/admin/sync-metadata", json={"batch_size": 100})
    assert response.status_code == 401


def test_admin_route_normal_user_returns_403():
    """Authenticated user without system_admin role must be rejected with 403."""
    user_token = generate_dev_jwt(
        user_id="usr_normal_001",
        email="friend@cinevault.local",
        username="friend",
        roles=["authenticated_user"],
    )
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.post("/admin/sync-metadata", json={"batch_size": 100}, headers=headers)
    assert response.status_code == 403
    err_body = response.json()
    err_msg = err_body.get("error", {}).get("message", "") or err_body.get("detail", "")
    assert "system_admin" in err_msg


def test_admin_route_curator_returns_403():
    """Curator without system_admin role must be rejected with 403."""
    curator_token = generate_dev_jwt(
        user_id="usr_curator_001",
        email="curator@cinevault.local",
        username="curator",
        roles=["authenticated_user", "curator"],
    )
    headers = {"Authorization": f"Bearer {curator_token}"}
    response = client.post("/admin/sync-metadata", json={"batch_size": 100}, headers=headers)
    assert response.status_code == 403
    err_body = response.json()
    err_msg = err_body.get("error", {}).get("message", "") or err_body.get("detail", "")
    assert "system_admin" in err_msg


@patch("services.api.routers.admin.sync_missing_posters", new_callable=AsyncMock)
def test_admin_route_system_admin_succeeds_202(mock_sync):
    """System administrator with system_admin role succeeds with 202 Accepted."""
    mock_sync.return_value = {"processed": 0, "synced": 0, "not_found": 0, "errors": 0}
    admin_token = generate_dev_jwt(
        user_id="usr_sysadmin_001",
        email="admin@cinevault.local",
        username="sysadmin",
        roles=["authenticated_user", "curator", "system_admin"],
    )
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post("/admin/sync-metadata", json={"batch_size": 50}, headers=headers)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "ACCEPTED"
    assert data["job_id"].startswith("sync-meta-")
