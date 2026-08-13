# CineVault OS — /v1/auth/me Endpoint Integration Test

from fastapi.testclient import TestClient
from services.api.main import app
from services.api.routers.auth import generate_dev_jwt

client = TestClient(app)


def test_auth_me_unauthenticated_returns_401():
    response = client.get("/v1/auth/me")
    assert response.status_code == 401


def test_auth_me_authenticated_returns_user_identity():
    token = generate_dev_jwt(
        user_id="usr_test_999",
        email="test_me@cinevault.local",
        username="test_me",
        roles=["authenticated_user"],
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["sub"] == "usr_test_999"
    assert data["email"] == "test_me@cinevault.local"
    assert data["username"] == "test_me"
    assert "authenticated_user" in data["roles"]
