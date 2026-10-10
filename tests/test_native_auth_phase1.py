# CineVault OS — Phase 1 Native Authentication Test Suite
# Tests all 19 requirements specified in Phase 1 mandate:
# 1. Valid login
# 2. Invalid password
# 3. Unknown user
# 4. Disabled user
# 5. Registration
# 6. Duplicate email
# 7. Invalid invite
# 8. Reused invite
# 9. Normal user role assignment
# 10. Admin privilege escalation attempt
# 11. Access token validation
# 12. Expired token
# 13. Invalid token
# 14. Refresh
# 15. Revoked / inactive refresh
# 16. User isolation
# 17. Existing authenticated endpoint access
# 18. Curator endpoint protection
# 19. Admin endpoint protection

import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest import IsolatedAsyncioTestCase
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select, delete

from services.api.main import app
from services.api.config import config
from services.api.database import engine
from services.api.models.auth import AuthUserModel
from services.api.models.social import InviteTokenModel, ReferralModel
from services.api.repositories.auth import auth_repository
from services.api.routers.auth import create_access_token, create_refresh_token


def get_error_message(response) -> str:
    """Extracts error message from RFC 7807 problem payload or FastAPI detail."""
    data = response.json()
    if isinstance(data, dict):
        if "error" in data and isinstance(data["error"], dict):
            return data["error"].get("message", "")
        return data.get("detail", "")
    return ""


class TestNativeAuthPhase1(IsolatedAsyncioTestCase):
    """Complete Phase 1 verification test suite."""

    async def asyncSetUp(self):
        self.SessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self.client = TestClient(app)
        self.test_emails = []
        self.test_tokens = []

    async def asyncTearDown(self):
        # Clean up any test records created across connections
        async with self.SessionLocal() as session:
            if self.test_tokens:
                await session.execute(
                    delete(ReferralModel).where(ReferralModel.status == "PENDING")
                )
                await session.execute(
                    delete(InviteTokenModel).where(InviteTokenModel.token.in_(self.test_tokens))
                )
            if self.test_emails:
                await session.execute(
                    delete(AuthUserModel).where(AuthUserModel.email.in_(self.test_emails))
                )
            await session.commit()

    async def _create_test_invite(
        self, expired: bool = False, converted: bool = False
    ) -> str:
        token = f"inv_test_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        expires_at = now - timedelta(days=1) if expired else now + timedelta(days=30)
        converted_user_id = uuid.uuid4() if converted else None

        async with self.SessionLocal() as session:
            invite = InviteTokenModel(
                token=token,
                inviter_id=uuid.UUID("018f0000-0000-7000-8000-000000000001"),
                preview_data_json={},
                expires_at=expires_at,
                converted_user_id=converted_user_id,
                created_at=now,
            )
            session.add(invite)
            await session.commit()

        self.test_tokens.append(token)
        return token

    # 1. Valid login
    async def test_01_valid_login(self):
        response = self.client.post(
            "/v1/auth/login",
            json={"email": "dev@cinevault.local", "password": "devpass"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertEqual(data["email"], "dev@cinevault.local")
        self.assertEqual(data["user_id"], "018f0000-0000-7000-8000-000000000001")
        self.assertIn("authenticated_user", data["roles"])

    # 2. Invalid password
    async def test_02_invalid_password(self):
        response = self.client.post(
            "/v1/auth/login",
            json={"email": "dev@cinevault.local", "password": "wrong_password"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid email or password", get_error_message(response))

    # 3. Unknown user
    async def test_03_unknown_user(self):
        response = self.client.post(
            "/v1/auth/login",
            json={"email": "nobody@cinevault.local", "password": "password123"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid email or password", get_error_message(response))

    # 4. Disabled user
    async def test_04_disabled_user(self):
        email = f"disabled_{uuid.uuid4().hex[:6]}@domain.com"
        self.test_emails.append(email)

        async with self.SessionLocal() as session:
            pw_hash = auth_repository.hash_password("disabledpass123")
            disabled_user = AuthUserModel(
                user_id=uuid.uuid4(),
                email=email,
                password_hash=pw_hash,
                roles=["authenticated_user"],
                is_active=False,
            )
            session.add(disabled_user)
            await session.commit()

        response = self.client.post(
            "/v1/auth/login",
            json={"email": email, "password": "disabledpass123"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("disabled or inactive", get_error_message(response))

    # 5. Registration with valid invite
    async def test_05_registration_with_valid_invite(self):
        invite_code = await self._create_test_invite()
        test_email = f"newuser_{uuid.uuid4().hex[:6]}@domain.com"
        self.test_emails.append(test_email)

        response = self.client.post(
            "/v1/auth/register",
            json={
                "email": test_email,
                "password": "strongPassword123!",
                "invite_code": invite_code,
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertEqual(data["roles"], ["authenticated_user"])

    # 6. Duplicate email
    async def test_06_duplicate_email(self):
        invite_code = await self._create_test_invite()

        response = self.client.post(
            "/v1/auth/register",
            json={
                "email": "dev@cinevault.local",  # already exists
                "password": "strongPassword123!",
                "invite_code": invite_code,
            },
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("already registered", get_error_message(response))

    # 7. Invalid invite
    async def test_07_invalid_invite(self):
        response = self.client.post(
            "/v1/auth/register",
            json={
                "email": f"user_{uuid.uuid4().hex[:6]}@domain.com",
                "password": "strongPassword123!",
                "invite_code": "inv_does_not_exist_999",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid invite code", get_error_message(response))

    # 8. Reused invite
    async def test_08_reused_invite(self):
        invite_code = await self._create_test_invite(converted=True)

        response = self.client.post(
            "/v1/auth/register",
            json={
                "email": f"user_{uuid.uuid4().hex[:6]}@domain.com",
                "password": "strongPassword123!",
                "invite_code": invite_code,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("already been used", get_error_message(response))

    # 9. Expired invite
    async def test_09_expired_invite(self):
        invite_code = await self._create_test_invite(expired=True)

        response = self.client.post(
            "/v1/auth/register",
            json={
                "email": f"user_{uuid.uuid4().hex[:6]}@domain.com",
                "password": "strongPassword123!",
                "invite_code": invite_code,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("expired", get_error_message(response))

    # 10. Normal user role assignment & privilege escalation prevention
    async def test_10_admin_privilege_escalation_attempt(self):
        invite_code = await self._create_test_invite()

        test_email = f"attacker_{uuid.uuid4().hex[:6]}@domain.com"
        self.test_emails.append(test_email)

        # Attacker tries to submit roles field
        response = self.client.post(
            "/v1/auth/register",
            json={
                "email": test_email,
                "password": "strongPassword123!",
                "invite_code": invite_code,
                "roles": ["system_admin", "curator"],
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["roles"], ["authenticated_user"])

        # Verify in database directly
        async with self.SessionLocal() as session:
            stmt = select(AuthUserModel).where(AuthUserModel.email == test_email)
            db_user = (await session.execute(stmt)).scalar_one()
            self.assertEqual(db_user.roles, ["authenticated_user"])

    # 11. Access token validation
    async def test_11_access_token_validation(self):
        login_res = self.client.post(
            "/v1/auth/login",
            json={"email": "dev@cinevault.local", "password": "devpass"},
        )
        access_token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        me_res = self.client.get("/v1/auth/me", headers=headers)
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["sub"], "018f0000-0000-7000-8000-000000000001")

    # 12. Expired token
    async def test_12_expired_token(self):
        now = int(time.time())
        expired_payload = {
            "iss": "cinevault-auth",
            "aud": "cinevault-api-gateway",
            "sub": "018f0000-0000-7000-8000-000000000001",
            "email": "dev@cinevault.local",
            "roles": ["authenticated_user"],
            "iat": now - 3600,
            "exp": now - 60,
        }
        expired_token = jose_jwt.encode(
            expired_payload,
            config.jwt_secret_key,
            algorithm="HS256",
            headers={"kid": "cinevault-native-key"},
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        res = self.client.get("/v1/auth/me", headers=headers)
        self.assertEqual(res.status_code, 401)
        self.assertIn("expired", get_error_message(res).lower())

    # 13. Invalid token signature / malformed
    async def test_13_invalid_token(self):
        headers = {"Authorization": "Bearer not.a.valid.jwt.token"}
        res = self.client.get("/v1/auth/me", headers=headers)
        self.assertEqual(res.status_code, 401)

    # 14. Token refresh & rotation
    async def test_14_token_refresh(self):
        login_res = self.client.post(
            "/v1/auth/login",
            json={"email": "dev@cinevault.local", "password": "devpass"},
        )
        refresh_token = login_res.json()["refresh_token"]

        refresh_res = self.client.post(
            "/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        self.assertEqual(refresh_res.status_code, 200)
        data = refresh_res.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertNotEqual(data["refresh_token"], refresh_token)  # token rotated

    # 15. Revoked / inactive user refresh rejection
    async def test_15_refresh_rejected_for_inactive_user(self):
        user_uuid = uuid.uuid4()
        user_email = f"deactivated_{uuid.uuid4().hex[:6]}@domain.com"
        self.test_emails.append(user_email)

        async with self.SessionLocal() as session:
            pw_hash = auth_repository.hash_password("password123")
            user = AuthUserModel(
                user_id=user_uuid,
                email=user_email,
                password_hash=pw_hash,
                roles=["authenticated_user"],
                is_active=False,
            )
            session.add(user)
            await session.commit()

        refresh_token = create_refresh_token(str(user_uuid), user_email)

        res = self.client.post(
            "/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        self.assertEqual(res.status_code, 401)
        self.assertIn("disabled or inactive", get_error_message(res))

    # 16. User isolation with native tokens
    async def test_16_user_isolation(self):
        token_a = create_access_token(
            user_id="018f0000-0000-7000-8000-000000000001",
            email="alice@cinevault.local",
            username="alice",
            roles=["authenticated_user"],
        )
        token_b = create_access_token(
            user_id="018f0000-0000-7000-8000-000000000002",
            email="bob@cinevault.local",
            username="bob",
            roles=["authenticated_user"],
        )

        res_a = self.client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
        res_b = self.client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})

        self.assertEqual(res_a.json()["sub"], "018f0000-0000-7000-8000-000000000001")
        self.assertEqual(res_b.json()["sub"], "018f0000-0000-7000-8000-000000000002")
        self.assertNotEqual(res_a.json()["sub"], res_b.json()["sub"])

    # 17. Existing authenticated endpoint access
    async def test_17_authenticated_endpoint_access(self):
        token = create_access_token(
            user_id="018f0000-0000-7000-8000-000000000001",
            email="dev@cinevault.local",
            username="dev",
            roles=["authenticated_user"],
        )
        res = self.client.get(
            "/v1/personal/watchlist",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(res.status_code, 200)

    # 18. Curator endpoint protection
    async def test_18_curator_endpoint_protection(self):
        user_token = create_access_token(
            user_id="018f0000-0000-7000-8000-000000000001",
            email="dev@cinevault.local",
            username="dev",
            roles=["authenticated_user"],
        )
        curator_token = create_access_token(
            user_id="018f0000-0000-7000-8000-000000000002",
            email="curator@cinevault.local",
            username="curator",
            roles=["authenticated_user", "curator"],
        )

        # Normal user -> 403 Forbidden
        denied_res = self.client.get(
            "/internal/v1/control-room/stats",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        self.assertEqual(denied_res.status_code, 403)

        # Curator -> 200 OK
        allowed_res = self.client.get(
            "/internal/v1/control-room/stats",
            headers={"Authorization": f"Bearer {curator_token}"},
        )
        self.assertEqual(allowed_res.status_code, 200)

    # 19. Admin endpoint protection
    async def test_19_admin_endpoint_protection(self):
        curator_token = create_access_token(
            user_id="018f0000-0000-7000-8000-000000000002",
            email="curator@cinevault.local",
            username="curator",
            roles=["authenticated_user", "curator"],
        )
        admin_token = create_access_token(
            user_id="018f0000-0000-7000-8000-000000000003",
            email="admin@cinevault.local",
            username="admin",
            roles=["authenticated_user", "curator", "system_admin"],
        )

        # Curator trying to access admin endpoint -> 403 Forbidden
        denied_res = self.client.post(
            "/admin/sync-metadata",
            headers={"Authorization": f"Bearer {curator_token}"},
        )
        self.assertEqual(denied_res.status_code, 403)

        # Admin -> 202 Accepted
        allowed_res = self.client.post(
            "/admin/sync-metadata",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        self.assertEqual(allowed_res.status_code, 202)
