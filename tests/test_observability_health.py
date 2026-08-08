# CineVault OS — Observability & Telemetry Test Suite
# Validates Prometheus metrics scraping, correlation ID propagation, and structured logging

import unittest
from fastapi.testclient import TestClient
from services.api.main import app

class TestObservabilityAndHealth(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_prometheus_metrics_endpoint(self):
        # Trigger an API request first to populate metrics
        self.client.get("/v1/titles")
        
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        content = response.text
        self.assertIn("cinevault_http_requests_total", content)
        self.assertIn("cinevault_http_request_duration_seconds", content)
        self.assertIn("cinevault_auth_failures_total", content)

    def test_structured_logger_formatting(self):
        from services.api.telemetry import JSONFormatter
        import logging
        
        formatter = JSONFormatter()
        record = logging.LogRecord("cinevault.test", logging.INFO, "path/to/file.py", 10, "Test log message", (), None)
        record.correlation_id = "018f2e4a-7b31-7000-8000-123456789abc"
        
        output = formatter.format(record)
        self.assertIn('"message": "Test log message"', output)
        self.assertIn('"correlation_id": "018f2e4a-7b31-7000-8000-123456789abc"', output)

if __name__ == "__main__":
    unittest.main()
