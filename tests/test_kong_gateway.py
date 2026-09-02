# CineVault OS — Kong API Gateway Routing & Rate Limiting Integration Tests (Phase 9.11)

import yaml
import pytest
from unittest.mock import MagicMock
from fastapi import Request
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.rate_limiter import rate_limiter, RateLimitExceededError
from services.api.valkey import valkey_manager

client = TestClient(app)

def test_kong_declarative_schema_parsing():
    with open("infra/kong/kong.yml", "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    assert config_data.get("_format_version") == "3.0"
    services = config_data.get("services", [])
    service_names = [s["name"] for s in services]

    assert "cinevault-public-api" in service_names
    assert "cinevault-internal-api" in service_names
    assert "cinevault-health-api" in service_names

def test_rate_limiting_enforces_429_too_many_requests():
    mock_request = MagicMock(spec=Request)
    mock_request.client.host = "192.168.1.99"
    scope = "TEST_SCOPE"
    limit = 3

    # rate_limiter is now Valkey-backed (P1 fix) and its counter persists
    # across process/test runs via a TTL, unlike the old purely in-memory
    # limiter that always started at zero. Clear this test's own key first
    # so re-running the suite within the same window doesn't inherit a
    # leftover count from a previous run.
    valkey_client = valkey_manager.get_client()
    if valkey_client is not None:
        valkey_client.delete(f"ratelimit:{scope}:{mock_request.client.host}")

    # Exhaust quota
    for _ in range(limit):
        rate_limiter.check_rate_limit(mock_request, scope, limit)

    # Exceed quota raises RateLimitExceededError (mapped by FastAPI to HTTP 429)
    with pytest.raises(RateLimitExceededError, match="Rate limit exceeded"):
        rate_limiter.check_rate_limit(mock_request, scope, limit)

def test_health_endpoint_accessibility():
    response = client.get("/health/liveness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
