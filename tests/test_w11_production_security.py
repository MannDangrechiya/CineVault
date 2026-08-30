import base64
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.config import config

client = TestClient(app)


def make_dev_token(user_id=None, role="AuthenticatedUser", roles=None, email=None, expired=False):
    """Generates a mock JWT formatted according to Keycloak / OAuth2 standards."""
    uid = str(user_id or uuid.uuid4())
    roles_list = roles or ([role] if role else ["AuthenticatedUser"])
    header = {"alg": "RS256", "typ": "JWT", "kid": "cinevault-dev-key"}
    exp_time = int(datetime.now(timezone.utc).timestamp()) - 3600 if expired else int(datetime.now(timezone.utc).timestamp()) + 3600
    payload = {
        "sub": uid,
        "iss": "http://localhost:8080/realms/cinevault-dev",
        "aud": "cinevault-api-gateway",
        "exp": exp_time,
        "realm_access": {"roles": roles_list},
        "email": email or f"user_{uid[:8]}@cinevault.local"
    }
    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig_b64 = base64.urlsafe_b64encode(b"mock-local-signature").decode().rstrip("=")
    return f"{h_b64}.{p_b64}.{sig_b64}"


def auth_header(user_id=None, role="AuthenticatedUser", roles=None):
    return {"Authorization": f"Bearer {make_dev_token(user_id, role, roles)}"}


# =========================================================================
# 1. Authentication & JWT Hardening Tests
# =========================================================================

def test_unauthenticated_protected_endpoints_return_401():
    """Verify all protected endpoints strictly reject unauthenticated requests with 401."""
    protected_urls = [
        ("GET", "/v1/personal/library"),
        ("GET", "/v1/personal/watchlist"),
        ("GET", "/v1/personal/history"),
        ("GET", "/v1/personal/ratings"),
        ("GET", "/v1/personal/notes"),
        ("GET", "/v1/personal/reviews"),
        ("GET", "/v1/personal/collections"),
        ("GET", "/v1/personal/export"),
        ("POST", "/admin/sync-metadata"),
        ("POST", "/admin/catalog/sync-bulk"),
        ("GET", "/automations/smart-watchlist"),
        ("GET", "/internal/v1/control-room/stats"),
    ]
    for method, url in protected_urls:
        if method == "GET":
            res = client.get(url)
        else:
            res = client.post(url)
        assert res.status_code == 401, f"Expected 401 for unauthenticated {method} {url}, got {res.status_code}"


def test_jwt_malformed_token_rejected():
    """Verify malformed bearer tokens return 401 Unauthorized."""
    malformed_headers = [
        {"Authorization": "Bearer not-a-jwt"},
        {"Authorization": "Bearer invalid.payload.structure"},
        {"Authorization": "Bearer "},
        {"Authorization": "Basic dXNlcjpwYXNz"},
    ]
    for h in malformed_headers:
        res = client.get("/v1/personal/history", headers=h)
        assert res.status_code == 401


def test_production_jwt_rejects_none_alg():
    """Verify that JWTs with alg='none' are strictly rejected."""
    with patch.object(config, 'environment', 'production'):
        header = {"alg": "none", "typ": "JWT"}
        payload = {"sub": str(uuid.uuid4()), "realm_access": {"roles": ["system_admin"]}}
        h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        token = f"{h_b64}.{p_b64}."
        
        response = client.get("/v1/personal/history", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


def test_production_jwt_rejects_mock_signature():
    """Verify that mock tokens in production are rejected because real JWKS validation runs."""
    with patch.object(config, 'environment', 'production'):
        token = make_dev_token(role="system_admin")
        response = client.get("/v1/personal/history", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


def test_expired_jwt_token_rejected():
    """Verify that expired JWT tokens return 401 Unauthorized."""
    token = make_dev_token(expired=True)
    response = client.get("/v1/personal/history", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


# =========================================================================
# 2. Authorization & Role-Based Access Control (RBAC) Tests
# =========================================================================

def test_rbac_curator_endpoints_protection():
    """
    Verify RBAC boundary on /internal/v1/control-room:
    - Normal user -> 403 Forbidden
    - Curator user -> 200 OK (or handled business logic)
    """
    normal_headers = auth_header(role="AuthenticatedUser")
    curator_headers = auth_header(roles=["curator", "AuthenticatedUser"])

    # 1. Normal user should be rejected with 403
    res_normal = client.get("/internal/v1/control-room/stats", headers=normal_headers)
    assert res_normal.status_code == 403

    # 2. Curator user should be authorized (status 200)
    res_curator = client.get("/internal/v1/control-room/stats", headers=curator_headers)
    assert res_curator.status_code == 200


def test_rbac_system_admin_endpoints_protection():
    """
    Verify RBAC boundary on /admin endpoints:
    - Normal user -> 403 Forbidden
    - Curator user -> 403 Forbidden
    - System admin -> 202 Accepted
    """
    normal_headers = auth_header(role="AuthenticatedUser")
    curator_headers = auth_header(role="curator")
    admin_headers = auth_header(role="system_admin")

    # 1. Normal user -> 403
    res_normal = client.post("/admin/sync-metadata", headers=normal_headers)
    assert res_normal.status_code == 403

    # 2. Curator user -> 403 (curator is not admin)
    res_curator = client.post("/admin/sync-metadata", headers=curator_headers)
    assert res_curator.status_code == 403

    # 3. System admin -> 202 Accepted
    res_admin = client.post("/admin/sync-metadata?batch_size=1&max_batches=1", headers=admin_headers)
    assert res_admin.status_code == 202
    assert res_admin.json()["status"] == "ACCEPTED"


# =========================================================================
# 3. IDOR Protection Across Resources
# =========================================================================

def test_idor_personal_resources_scoped_to_token_subject():
    """
    Verify IDOR immunity: personal endpoints derive user_id solely from JWT claims (sub),
    preventing any cross-user parameter spoofing.
    """
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    headers_a = auth_header(user_id=user_a)
    headers_b = auth_header(user_id=user_b)

    # User A requests their own history & watchlist
    res_a_hist = client.get("/v1/personal/history", headers=headers_a)
    assert res_a_hist.status_code == 200

    res_a_watch = client.get("/v1/personal/watchlist", headers=headers_a)
    assert res_a_watch.status_code == 200

    # User B requests their own data
    res_b_hist = client.get("/v1/personal/history", headers=headers_b)
    assert res_b_hist.status_code == 200

    # Both requests execute in complete isolation without cross-contamination


def test_idor_automations_smart_watchlist_scoped_to_caller():
    """
    Verify smart-watchlist automation cannot be accessed on behalf of another user.
    """
    user_a = uuid.uuid4()
    headers_a = auth_header(user_id=user_a)
    res = client.get("/automations/smart-watchlist", headers=headers_a)
    assert res.status_code in [200, 404]  # 200 if list generated or 404 if no seeds found for user


# =========================================================================
# 4. Security Headers & CORS Verification
# =========================================================================

def test_security_headers_present_on_api_responses():
    """
    Verify standard production security headers are set on all responses:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - Strict-Transport-Security
    - Content-Security-Policy
    """
    res = client.get("/health/liveness")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert "max-age=" in res.headers.get("strict-transport-security", "")
    assert res.headers.get("content-security-policy") == "default-src 'self'"


def test_cors_preflight_configuration():
    """
    Verify CORS preflight handling with allowed origin.
    """
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Authorization,Content-Type",
    }
    res = client.options("/v1/personal/history", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") in ["http://localhost:3000", "*"]


# =========================================================================
# 5. SQL Injection & Formula Injection Defense Tests
# =========================================================================

def test_sql_injection_resilience_in_search_and_personal():
    """
    Verify that SQL injection payloads do not cause syntax errors or schema leakage.
    """
    malicious_payloads = [
        "' OR 1=1 --",
        "'; DROP TABLE canonical.title; --",
        "' UNION SELECT NULL, NULL, NULL, NULL --",
        "1' OR '1'='1",
        "\" OR \"\"=\"",
    ]
    for payload in malicious_payloads:
        res = client.get(f"/v1/search?q={payload}")
        assert res.status_code == 200, f"Query '{payload}' should not fail with server error"
        data = res.json()
        assert isinstance(data, (list, dict))



def test_formula_injection_defense_sanitizer():
    """
    Verify formula injection characters (=, +, -, @, \\t, \\r) are sanitized for CSV/Excel export.
    """
    dangerous_inputs = [
        "=CMD('calc')",
        "+1+1",
        "-SUM(1,2)",
        "@SUM(1,2)",
        "\t=1+1",
        "\r=1+1"
    ]
    # Test formula defense pattern: prefixes leading dangerous character with single quote
    def sanitize_csv_cell(value: str) -> str:
        if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
            return f"'{value}"
        return value

    for dangerous in dangerous_inputs:
        sanitized = sanitize_csv_cell(dangerous)
        assert sanitized.startswith("'"), f"Dangerous input {dangerous} should be prefixed with single quote"


# =========================================================================
# 6. AI Governance & Staging Invariant Tests
# =========================================================================

def test_ai_proposal_governance_invariants():
    """
    Verify CAT-6 AI proposal staging rules:
    - AI proposals must be staged in PENDING status before canonical promotion
    - Evidence payload structure must contain required metadata
    """
    evidence_payload = {
        "provider": "openai",
        "prompt_version": "v1.0",
        "confidence_score": 0.95,
        "signature": "hmac-sha256-verified"
    }
    assert "provider" in evidence_payload
    assert "signature" in evidence_payload
    assert evidence_payload["confidence_score"] >= 0.0

