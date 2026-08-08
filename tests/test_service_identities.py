# CineVault OS — Service Identities & Machine Identity Isolation Test Suite
# Validates machine service boundaries and action restriction enforcement across all compute workloads

import unittest
from services.api.auth.rbac import RBACPolicyEngine, AuthorizationError

class TestServiceIdentityBoundaries(unittest.TestCase):

    def test_ingestion_service_canonical_write_prohibition(self):
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-ingest-service", "CANONICAL_WRITE_TITLE")

    def test_ingestion_service_raw_payload_write_permitted(self):
        # Must not raise error
        RBACPolicyEngine.enforce_service_isolation("cinevault-ingest-service", "RAW_PAYLOAD_INSERT")

    def test_ai_service_canonical_write_prohibition(self):
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-ai-service", "CANONICAL_WRITE_EDITION")

    def test_analytics_service_personal_data_access_prohibition(self):
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-analytics-service", "PERSONAL_READ_WATCH_EVENT")
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-analytics-service", "CANONICAL_WRITE_TITLE")

    def test_sync_processor_canonical_write_prohibition(self):
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-sync-processor", "CANONICAL_WRITE_RELEASE")

    def test_quality_service_canonical_write_prohibition(self):
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-quality-service", "CANONICAL_WRITE_TITLE")

    def test_public_api_internal_admin_prohibition(self):
        with self.assertRaises(AuthorizationError):
            RBACPolicyEngine.enforce_service_isolation("cinevault-public-api", "INTERNAL_ADMIN_MUTATE")

if __name__ == "__main__":
    unittest.main()
