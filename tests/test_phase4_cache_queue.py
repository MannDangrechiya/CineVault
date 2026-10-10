# CineVault OS — Phase 4 Cache Infrastructure Test Suite
# Validates Valkey (cache-aside, idempotency, failure resilience) and the
# aggregated readiness probe. RabbitMQ and Kong were audited and removed in
# the Phase 3 infrastructure consolidation — see docs/GATEWAY_TOPOLOGY.md and
# the ai_worker removal commit for why neither was a real dependency.

import unittest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.valkey import ValkeyManager, valkey_manager

client = TestClient(app)

class TestPhase4CacheInfrastructure(unittest.TestCase):

    def setUp(self):
        self.valkey = valkey_manager

    # -------------------------------------------------------------------------
    # 1. Valkey Tests
    # -------------------------------------------------------------------------
    def test_valkey_health_check_structure(self):
        health = self.valkey.check_health()
        self.assertIn("status", health)
        self.assertIn("target", health)

    def test_valkey_read_write_operations(self):
        test_key = "test:phase4:key"
        test_val = "valkey_distributed_state_test"

        # Set & Get
        set_res = self.valkey.set(test_key, test_val, ttl=30)
        if set_res:
            get_val = self.valkey.get(test_key)
            self.assertEqual(get_val, test_val)
            self.valkey.delete(test_key)

    def test_valkey_idempotency_check(self):
        idem_key = "018f2e4a-7b31-7000-8000-000000000099"
        client = self.valkey.get_client()
        if client:
            # Live Valkey container test
            is_new = self.valkey.check_and_set_idempotency(idem_key, ttl=10)
            self.assertTrue(is_new)
            is_duplicate = not self.valkey.check_and_set_idempotency(idem_key, ttl=10)
            self.assertTrue(is_duplicate)
            self.valkey.delete(f"idempotency:{idem_key}")
        else:
            # Offline fallback test (fail-open mode)
            is_new = self.valkey.check_and_set_idempotency(idem_key, ttl=10)
            self.assertTrue(is_new)

    def test_valkey_failure_resilience_fallback(self):
        # Instantiate ValkeyManager pointing to an unreachable port
        bad_valkey = ValkeyManager(host="localhost", port=59999)
        health = bad_valkey.check_health()
        self.assertEqual(health["status"], "UNHEALTHY")

        # Ensure operations fail gracefully without raising unhandled exception
        res_get = bad_valkey.get("any_key")
        self.assertIsNone(res_get)

    # -------------------------------------------------------------------------
    # 2. Readiness Probe Tests
    # -------------------------------------------------------------------------
    def test_readiness_probe_aggregated_health(self):
        response = client.get("/health/readiness")
        self.assertIn(response.status_code, [200, 503])
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("checks", data)
        self.assertIn("database", data["checks"])
        self.assertIn("cache", data["checks"])

    def test_security_no_credentials_leaked_in_health_response(self):
        response = client.get("/health/readiness")
        content_str = response.text.lower()
        self.assertNotIn("dev_postgres_password", content_str)
        self.assertNotIn("secret", content_str)

if __name__ == "__main__":
    unittest.main()
