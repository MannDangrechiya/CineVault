# CineVault OS — Infrastructure Integration Test Suite
# Validates connectivity checks for PostgreSQL and Valkey distributed state
# (PgBouncer was removed in the Phase 3 infrastructure consolidation — the
# API connects directly to Postgres via a bounded SQLAlchemy pool now)

import unittest
from services.api.database import db_manager
from services.api.valkey import valkey_manager

class TestInfrastructureIntegration(unittest.TestCase):

    def test_postgres_health_check_structure(self):
        result = db_manager.check_health()
        self.assertIn("status", result)
        self.assertIn("target", result)

    def test_valkey_health_check_structure(self):
        result = valkey_manager.check_health()
        self.assertIn("status", result)
        self.assertIn("target", result)

if __name__ == "__main__":
    unittest.main()
