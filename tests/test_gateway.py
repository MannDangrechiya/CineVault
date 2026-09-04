# CineVault OS — Phase 3 Gateway & Proxy Test Suite
# Validates FastAPI's edge-facing behavior (health, correlation ID propagation,
# error shape) directly. Kong was audited and removed in the Phase 3
# infrastructure consolidation — it was never a real dependency of these
# checks (they exercise the FastAPI app via TestClient, not a live gateway).

import unittest
from fastapi.testclient import TestClient
from services.api.main import app

class TestGatewayAndProxyRouting(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_health_liveness_endpoint(self):
        response = self.client.get("/health/liveness")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "UP")
        self.assertIn("X-Correlation-ID", response.headers)

    def test_health_readiness_endpoint(self):
        response = self.client.get("/health/readiness")
        self.assertIn(response.status_code, [200, 503, 530])
        data = response.json()
        self.assertIn("dependencies", data)

    def test_correlation_id_propagation(self):
        custom_corr_id = "018f2e4a-7b31-7000-8000-999999999999"
        response = self.client.get("/v1/titles", headers={"X-Correlation-ID": custom_corr_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Correlation-ID"), custom_corr_id)

    def test_invalid_route_returns_json_error(self):
        response = self.client.get("/v1/non-existent-route")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], "HTTP_ERROR")

if __name__ == "__main__":
    unittest.main()
