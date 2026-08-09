# CineVault OS — FastAPI Authentication & Authorization Dependencies (P0 Fix)
# Bridges JWT / RBAC engine to FastAPI endpoint dependency injection.
# P0 Fix: Wired verify_token_signature() between structural decode and claim validation.

from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from .jwt_validator import JWTValidator, JWTValidationError, SecurityTokenClaims
from .rbac import RBACPolicyEngine, AuthorizationError, HighRiskAuthError
from ..telemetry import metrics_collector

jwt_validator = JWTValidator()


def extract_bearer_token(request: Request) -> Optional[str]:
    """Extracts the Bearer token string from the Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


async def get_optional_claims(request: Request) -> Optional[SecurityTokenClaims]:
    """
    Attempts to extract and fully validate a JWT token.
    Returns None for unauthenticated requests rather than raising an error.
    Used for public endpoints that permit anonymous access.
    """
    token = extract_bearer_token(request)
    if not token:
        return None
    try:
        # Step 1: Structural decode (no signature check yet)
        header, payload = jwt_validator.decode_unverified_token(token)
        # Step 2: Cryptographic signature verification (RS256 via JWKS)
        jwt_validator.verify_token_signature(token, header, payload)
        # Step 3: Claims validation (issuer, audience, expiry, nbf)
        return jwt_validator.validate_claims(payload)
    except JWTValidationError:
        metrics_collector.record_auth_failure()
        return None


async def get_current_claims(request: Request) -> SecurityTokenClaims:
    """
    Extracts and fully validates a JWT token. Raises HTTP 401 on any failure.
    Used for protected endpoints requiring authenticated access.

    Validation order:
    1. Bearer token presence
    2. Structural decode (format check)
    3. RS256 cryptographic signature verification via JWKS
    4. Claim validation (issuer, audience, exp, nbf, sub)
    """
    token = extract_bearer_token(request)
    if not token:
        metrics_collector.record_auth_failure()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Expected: Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        # Step 1: Structural decode (3-part check, staging mock rejection)
        header, payload = jwt_validator.decode_unverified_token(token)
        # Step 2: Cryptographic RS256 signature verification via JWKS public key
        jwt_validator.verify_token_signature(token, header, payload)
        # Step 3: Standard claim validation (iss, aud, exp, nbf, sub)
        return jwt_validator.validate_claims(payload)
    except JWTValidationError as exc:
        metrics_collector.record_auth_failure()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"JWT validation failed: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def require_authenticated_user(
    claims: SecurityTokenClaims = Depends(get_current_claims),
) -> SecurityTokenClaims:
    """Requires the token holder to have at least the authenticated_user role."""
    if not RBACPolicyEngine.is_authenticated_user(claims):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: authenticated_user role required.",
        )
    return claims


async def require_curator(
    claims: SecurityTokenClaims = Depends(get_current_claims),
) -> SecurityTokenClaims:
    """Requires the token holder to have the curator or system_admin role."""
    if not RBACPolicyEngine.is_curator(claims):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: curator or system_admin role required.",
        )
    return claims


async def require_system_admin(
    claims: SecurityTokenClaims = Depends(get_current_claims),
) -> SecurityTokenClaims:
    """Requires the token holder to have the system_admin role."""
    if not RBACPolicyEngine.is_system_admin(claims):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: system_admin role required.",
        )
    return claims


async def verify_service_identity(request: Request) -> str:
    """Validates machine service identity headers for internal service-to-service calls."""
    client_id = request.headers.get("X-Service-Identity", "anonymous-client")
    action = request.headers.get("X-Service-Action", "READ")
    try:
        RBACPolicyEngine.enforce_service_isolation(client_id, action)
    except AuthorizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return client_id
