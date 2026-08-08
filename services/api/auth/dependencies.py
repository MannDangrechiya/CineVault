# CineVault OS — FastAPI Authentication & Authorization Dependencies
# Bridges Phase 2 JWT / RBAC engine to FastAPI endpoint dependency injection

from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from .jwt_validator import JWTValidator, JWTValidationError, SecurityTokenClaims
from .rbac import RBACPolicyEngine, AuthorizationError, HighRiskAuthError
from ..telemetry import metrics_collector

jwt_validator = JWTValidator()

def extract_bearer_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None

async def get_optional_claims(request: Request) -> Optional[SecurityTokenClaims]:
    token = extract_bearer_token(request)
    if not token:
        return None
    try:
        header, payload = jwt_validator.decode_unverified_token(token)
        return jwt_validator.validate_claims(payload)
    except JWTValidationError as e:
        metrics_collector.record_auth_failure()
        return None

async def get_current_claims(request: Request) -> SecurityTokenClaims:
    token = extract_bearer_token(request)
    if not token:
        metrics_collector.record_auth_failure()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header with Bearer token."
        )
    try:
        header, payload = jwt_validator.decode_unverified_token(token)
        return jwt_validator.validate_claims(payload)
    except JWTValidationError as e:
        metrics_collector.record_auth_failure()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"JWT Token validation failed: {str(e)}"
        )

async def require_authenticated_user(claims: SecurityTokenClaims = Depends(get_current_claims)) -> SecurityTokenClaims:
    if not RBACPolicyEngine.is_authenticated_user(claims):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Authenticated User role required."
        )
    return claims

async def require_curator(claims: SecurityTokenClaims = Depends(get_current_claims)) -> SecurityTokenClaims:
    if not RBACPolicyEngine.is_curator(claims):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Curator or SystemAdmin role required."
        )
    return claims

async def require_system_admin(claims: SecurityTokenClaims = Depends(get_current_claims)) -> SecurityTokenClaims:
    if not RBACPolicyEngine.is_system_admin(claims):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: SystemAdmin role required."
        )
    return claims

async def verify_service_identity(request: Request) -> str:
    client_id = request.headers.get("X-Service-Identity", "anonymous-client")
    action = request.headers.get("X-Service-Action", "READ")
    try:
        RBACPolicyEngine.enforce_service_isolation(client_id, action)
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    return client_id
