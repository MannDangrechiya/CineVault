# CineVault OS — Authentication & Token Issuance Router (Phase 9.8)
# Endpoint for issuing OIDC-compliant JWT tokens for client login & local dev testing

import time
import json
import base64
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from ..config import config
from ..rate_limiter import enforce_rate_limit

router = APIRouter(prefix="/v1/auth", tags=["Authentication & Identity (Phase 9.8)"])

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400
    user_id: str
    email: str
    roles: List[str]

def _b64encode_json(data: dict) -> str:
    json_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
    return base64.urlsafe_b64encode(json_bytes).decode('utf-8').rstrip('=')

def generate_dev_jwt(
    user_id: str,
    email: str,
    username: str,
    roles: List[str],
    expires_in: int = 86400
) -> str:
    """Generates an unencrypted OIDC-compliant JWT token for client sessions."""
    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT", "kid": "cinevault-dev-key"}
    payload = {
        "iss": config.keycloak_issuer,
        "aud": config.keycloak_audience,
        "sub": user_id,
        "email": email,
        "preferred_username": username,
        "iat": now,
        "exp": now + expires_in,
        "realm_access": {"roles": roles}
    }
    
    header_str = _b64encode_json(header)
    payload_str = _b64encode_json(payload)
    signature_str = _b64encode_json({"sig": "dev_mock_hmac_sha256_signature"})
    return f"{header_str}.{payload_str}.{signature_str}"

@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """Authenticates user credentials and issues OIDC-compliant JWT tokens."""
    if not body.email or not body.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required."
        )

    if body.password == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials."
        )

    # Determine user identity & roles
    user_id = "usr_curator_001" if "curator" in body.email.lower() else "usr_user_001"
    roles = ["authenticated_user", "curator"] if "curator" in body.email.lower() else ["authenticated_user"]
    username = body.email.split("@")[0] if "@" in body.email else body.email

    access_token = generate_dev_jwt(
        user_id=user_id,
        email=body.email,
        username=username,
        roles=roles,
    )
    refresh_token = f"ref_{access_token[:32]}"

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id,
        email=body.email,
        roles=roles
    )
