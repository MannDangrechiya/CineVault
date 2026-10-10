# CineVault OS — Phase 2 Production Mode Native Auth Verification
# Proves that in production configuration (ENVIRONMENT="production"):
# 1. /v1/auth/login does NOT return 501
# 2. Login succeeds and returns signed JWT access & refresh tokens
# 3. /v1/auth/me validates the token and returns 200 with user identity
# 4. Protected API endpoints accept the native token
# 5. Token refresh works cleanly in production mode
# 6. Production security guards remain fully enforced

import os
import sys
from pathlib import Path
from unittest import IsolatedAsyncioTestCase

# Ensure production environment variables with secure non-default values
PROD_ENV = {
    "ENVIRONMENT": "production",
    "DEBUG": "false",
    "JWT_SECRET_KEY": "phase2-production-test-secret-key-that-is-very-long-and-secure-1234567890",
    "POSTGRES_PASSWORD": "custom_prod_db_password_1234567890",
    "ALLOW_SEED_FALLBACK": "false",
}

for k, v in PROD_ENV.items():
    os.environ[k] = v

from fastapi.testclient import TestClient
from services.api.config import config, APIConfig, _INSECURE_DEFAULTS
from services.api.main import app
from services.api.repositories.auth import auth_repository


class TestProductionModeAuth(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._orig_env = config.environment
        self._orig_debug = config.debug
        self._orig_seed = config.allow_seed_fallback
        self._orig_jwt = config.jwt_secret_key

        # Activate production mode with safe, secure secrets
        config.environment = "production"
        config.debug = False
        config.allow_seed_fallback = False
        config.jwt_secret_key = "phase2-production-test-secret-key-that-is-very-long-and-secure-1234567890"

    async def asyncTearDown(self):
        # Restore configuration
        config.environment = self._orig_env
        config.debug = self._orig_debug
        config.allow_seed_fallback = self._orig_seed
        config.jwt_secret_key = self._orig_jwt

    async def test_production_mode_auth_lifecycle(self):

        # 1. Verify production mode is active and guards are satisfied
        assert config.environment == "production"
        assert config.debug is False
        assert config.allow_seed_fallback is False

        client = TestClient(app)

        # 2. Prepare test user in database
        test_email = "prod_flutter_user@cinevault.local"
        test_pass = "ProductionPassword123!"

        # Ensure user exists in database
        existing = await auth_repository.get_by_email(None, test_email)
        if not existing:
            await auth_repository.create_user(
                db=None,
                email=test_email,
                password_hash=auth_repository.hash_password(test_pass),
                roles=["authenticated_user"],
                is_active=True,
            )

        # 3. Call POST /v1/auth/login — MUST NOT return 501
        login_res = client.post(
            "/v1/auth/login",
            json={"email": test_email, "password": test_pass},
        )

        assert login_res.status_code != 501, f"Expected non-501 status, got {login_res.status_code}"
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"

        data = login_res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["email"] == test_email
        assert "authenticated_user" in data["roles"]

        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # 4. Call /v1/auth/me with the issued JWT
        me_res = client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_res.status_code == 200, f"/v1/auth/me failed: {me_res.text}"
        me_data = me_res.json()
        assert me_data["email"] == test_email
        assert "authenticated_user" in me_data["roles"]

        # 5. Call protected personal library endpoint
        history_res = client.get(
            "/v1/personal/history",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert history_res.status_code in (200, 404), f"Protected endpoint failed: {history_res.status_code}"

        # 6. Call POST /v1/auth/refresh
        refresh_res = client.post(
            "/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_res.status_code == 200, f"Refresh failed: {refresh_res.text}"
        new_data = refresh_res.json()
        assert "access_token" in new_data
        assert new_data["access_token"] != access_token

        # 7. Unauthenticated request to /v1/auth/me is strictly rejected with 401
        unauth_res = client.get("/v1/auth/me")
        assert unauth_res.status_code == 401

