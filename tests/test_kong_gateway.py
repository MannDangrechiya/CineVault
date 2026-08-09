# CineVault OS — Kong API Gateway Routing & Rate Limiting Integration Tests (Phase 9.11)

import yaml
import pytest
from unittest.mock import MagicMock
from fastapi import Request
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.rate_limiter import rate_limiter, RateLimitExceededError

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
