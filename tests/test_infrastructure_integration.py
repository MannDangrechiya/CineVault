# CineVault OS — Infrastructure Integration Test Suite
# Validates connectivity checks for PgBouncer, PostgreSQL, and Valkey distributed state

import unittest
from services.api.database import db_manager
from services.api.valkey import valkey_manager

class TestInfrastructureIntegration(unittest.TestCase):

    def test_pgbouncer_health_check_structure(self):
        result = db_manager.check_health()
        self.assertIn("status", result)
        self.assertIn("target", result)

    def test_valkey_health_check_structure(self):
        result = valkey_manager.check_health()
        self.assertIn("status", result)
        self.assertIn("target", result)

if __name__ == "__main__":
    unittest.main()
