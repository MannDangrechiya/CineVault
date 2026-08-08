# CineVault OS — Security Hardening & PII Leakage Test Suite
# Validates security headers, CORS origin restrictions, error message sanitization, and PII protection

import unittest
from fastapi.testclient import TestClient
from services.api.main import app

class TestSecurityHardening(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_security_headers_present(self):
        response = self.client.get("/health/liveness")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
        self.assertIn("Content-Security-Policy", response.headers)
        self.assertIn("Strict-Transport-Security", response.headers)

    def test_cors_preflight_headers(self):
        response = self.client.options(
            "/v1/titles",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://localhost:3000")

    def test_error_sanitization_does_not_leak_internals(self):
        # Trigger error
        response = self.client.get("/v1/titles/invalid-id-that-causes-error")
        self.assertEqual(response.status_code, 404)
        body = response.text
        self.assertNotIn("Traceback", body)
        self.assertNotIn("SELECT", body)
        self.assertNotIn("postgres", body)
        self.assertNotIn("password", body)

if __name__ == "__main__":
    unittest.main()
