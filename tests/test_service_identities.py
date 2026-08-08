# CineVault OS — Service Identities & Machine Identity Isolation Test Suite
# Validates machine service boundaries and action restriction enforcement

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
            RBACPolicyEngine.enforce_service_isolation("cinevault-ingest-service", "CANONICAL_WRITE_EDITION")

if __name__ == "__main__":
    unittest.main()
