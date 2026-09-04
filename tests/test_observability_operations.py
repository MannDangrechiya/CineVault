# CineVault OS — Phase 5 Observability & Operations Test Suite
# Validates structured JSON logging, PII redaction, W3C traceparent propagation, Prometheus exposition format, and health probes.

import json
import logging
import unittest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.telemetry import (
    JSONFormatter,
    sanitize_value,
    metrics_collector
)

client = TestClient(app)

class TestObservabilityAndOperations(unittest.TestCase):

    def test_json_formatter_structure(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="cinevault.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Operational event test",
            args=(),
            exc_info=None
        )
        record.correlation_id = "018f2e4a-7b31-7000-8000-000000000000"
        record.trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
        
        output = formatter.format(record)
        data = json.loads(output)
        
        self.assertEqual(data["name"], "cinevault.test")
        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["message"], "Operational event test")
        self.assertEqual(data["service"], "cinevault-api-service")
        self.assertEqual(data["correlation_id"], "018f2e4a-7b31-7000-8000-000000000000")
        self.assertEqual(data["trace_id"], "4bf92f3577b34da6a3ce929d0e0e4736")

    def test_pii_sanitization_redacts_sensitive_fields(self):
        # Direct key redaction
        self.assertEqual(sanitize_value("password", "my_secret_pass"), "[REDACTED]")
        self.assertEqual(sanitize_value("token", "bearer_xyz_123"), "[REDACTED]")
        self.assertEqual(sanitize_value("watch_event_notes", "private note"), "[REDACTED]")
        
        # Non-sensitive field preservation
        self.assertEqual(sanitize_value("title_id", "018f2e4a-7b31-7000-8000-000000000001"), "018f2e4a-7b31-7000-8000-000000000001")
        
        # Nested dictionary redaction
        payload = {
            "title_id": "018f2e4a-7b31-7000-8000-000000000001",
            "user_data": {
                "email": "user@example.com",
                "watch_event_notes": "secret notes"
            }
        }
        cleaned = sanitize_value("data", payload)
        self.assertEqual(cleaned["user_data"]["email"], "[REDACTED]")
        self.assertEqual(cleaned["user_data"]["watch_event_notes"], "[REDACTED]")

    def test_traceparent_and_correlation_id_propagation(self):
        headers = {
            "X-Correlation-ID": "018f2e4a-7b31-7000-8000-000000000088",
            "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        }
        response = client.get("/v1/titles", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Correlation-ID"), "018f2e4a-7b31-7000-8000-000000000088")
        self.assertEqual(response.headers.get("traceparent"), "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01")

    def test_prometheus_metrics_exposition_format(self):
        # Invoke an endpoint to generate request metrics
        client.get("/v1/titles")
        
        response = client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        output = response.text
        
        self.assertIn("# HELP cinevault_http_requests_total", output)
        self.assertIn("# TYPE cinevault_http_requests_total counter", output)
        self.assertIn("# HELP cinevault_http_request_duration_seconds", output)
        self.assertIn("cinevault_dependency_health_status", output)
        self.assertIn("cinevault_quarantine_records_current", output)
        self.assertIn("cinevault_sync_outbox_backlog", output)

    def test_dependency_health_status_metrics_updates(self):
        metrics_collector.update_dependency_health("valkey", True)
        metrics_collector.update_dependency_health("storage", False)

        output = metrics_collector.generate_prometheus_output()
        self.assertIn('cinevault_dependency_health_status{dependency="valkey"} 1', output)
        self.assertIn('cinevault_dependency_health_status{dependency="storage"} 0', output)

    def test_health_readiness_and_liveness_probes(self):
        # Liveness
        res_live = client.get("/health/liveness")
        self.assertEqual(res_live.status_code, 200)
        self.assertEqual(res_live.json()["status"], "UP")
        
        # Readiness
        res_ready = client.get("/health/readiness")
        self.assertIn(res_ready.status_code, [200, 503])
        data = res_ready.json()
        self.assertIn("status", data)
        # W13 sanitized the readiness payload to "checks" (no internal topology
        # exposure); this test predated that change and asserted the old key.
        self.assertIn("checks", data)

if __name__ == "__main__":
    unittest.main()
