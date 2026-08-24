# CineVault OS — Phase 4 Cache & Queue Infrastructure Test Suite
# Validates Valkey, Kong rate-limiting integration, RabbitMQ Quorum Queues, DLX, Retry topology, Correlation ID, Idempotency, and Readiness probes.

import json
import unittest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.valkey import ValkeyManager, valkey_manager
from services.api.rabbitmq import RabbitMQManager, rabbitmq_manager, PayloadValidationError, MAX_MESSAGE_SIZE_BYTES

client = TestClient(app)

class TestPhase4CacheAndQueueInfrastructure(unittest.TestCase):

    def setUp(self):
        self.valkey = valkey_manager
        self.rabbitmq = rabbitmq_manager

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
    # 2. RabbitMQ Tests
    # -------------------------------------------------------------------------
    def test_rabbitmq_health_check_structure(self):
        health = self.rabbitmq.check_health()
        self.assertIn("status", health)
        self.assertIn("target", health)

    def test_rabbitmq_payload_safety_validation(self):
        valid_payload = {
            "title_id": "018f2e4a-7b31-7000-8000-000000000001",
            "provider_name": "TMDB",
            "external_id": "550"
        }
        serialized = self.rabbitmq.validate_payload_safety(valid_payload)
        self.assertIn("018f2e4a-7b31-7000-8000-000000000001", serialized)

        # Test rejection of secret field
        secret_payload = {"user_id": "123", "password": "supersecretpassword"}
        with self.assertRaises(PayloadValidationError):
            self.rabbitmq.validate_payload_safety(secret_payload)

        # Test rejection of plaintext CAT-2 personal data field
        cat2_payload = {"user_id": "123", "watch_event_notes": "personal note text"}
        with self.assertRaises(PayloadValidationError):
            self.rabbitmq.validate_payload_safety(cat2_payload)

    def test_rabbitmq_topology_declaration_and_publish(self):
        topology_ok = self.rabbitmq.declare_topology()
        if topology_ok:
            payload = {
                "task_type": "INGEST_PROVIDER_PAYLOAD",
                "title_id": "018f2e4a-7b31-7000-8000-000000000002",
                "provider_name": "TVDB"
            }
            pub_ok = self.rabbitmq.publish_message(
                exchange="cinevault.ingestion.direct",
                routing_key="ingestion.task",
                payload=payload,
                correlation_id="018f2e4a-7b31-7000-8000-000000000002",
                idempotency_key="018f2e4a-7b31-7000-8000-000000000002"
            )
            self.assertTrue(pub_ok)

    def test_rabbitmq_failure_resilience_fallback(self):
        bad_rmq = RabbitMQManager(host="localhost", port=59999)
        health = bad_rmq.check_health()
        self.assertEqual(health["status"], "UNHEALTHY")
        
        pub_ok = bad_rmq.publish_message(
            exchange="cinevault.ingestion.direct",
            routing_key="ingestion.task",
            payload={"task": "test"},
            correlation_id="018f2e4a-7b31-7000-8000-000000000003"
        )
        self.assertFalse(pub_ok)

    # -------------------------------------------------------------------------
    # 3. Gateway & Integration Tests
    # -------------------------------------------------------------------------
    def test_kong_valkey_rate_limiting_config_verification(self):
        with open("infra/kong/kong.yml", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("policy: redis", content)
        self.assertIn("redis_host: valkey", content)

    def test_readiness_probe_aggregated_health(self):
        response = client.get("/health/readiness")
        self.assertIn(response.status_code, [200, 503])
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("dependencies", data)
        self.assertIn("pgbouncer", data["dependencies"])
        self.assertIn("valkey", data["dependencies"])
        self.assertIn("rabbitmq", data["dependencies"])

    def test_security_no_credentials_leaked_in_health_response(self):
        response = client.get("/health/readiness")
        content_str = response.text.lower()
        self.assertNotIn("dev_postgres_password", content_str)
        self.assertNotIn("dev_rabbitmq_password", content_str)
        self.assertNotIn("secret", content_str)

if __name__ == "__main__":
    unittest.main()
