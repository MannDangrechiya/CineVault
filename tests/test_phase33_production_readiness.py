# CineVault OS — Phase 33 Production Readiness Tests
# Verifies all pre-launch verification checks:
# credentials check, TLS, JWT verification, observability, backup/recovery, privacy, and full readiness audit.

import pytest
from services.api.production_readiness import (
    ProductionReadinessAuditor,
    CheckStatus,
    ReadinessCheckCategory,
    production_auditor,
)


class TestPhase33ProductionReadiness:
    """Phase 33 — Production Readiness: credentials, TLS, auth, monitoring, backups, privacy."""

    def fresh_auditor(self) -> ProductionReadinessAuditor:
        return ProductionReadinessAuditor()

    def test_production_readiness_detects_insecure_dev_secrets(self):
        """Auditor fails if default/insecure development credentials are present."""
        auditor = self.fresh_auditor()
        insecure_env = {
            "JWT_SECRET": "dev_secret_key_12345",
            "DB_PASSWORD": "password",
            "KEYCLOAK_CLIENT_SECRET": "secret123",
        }
        result = auditor.verify_no_dev_credentials(insecure_env)
        assert result.status == CheckStatus.FAIL
        assert result.blocking is True
        assert "Insecure credentials detected" in result.details

    def test_production_readiness_passes_with_secure_credentials(self):
        """Auditor passes when all credentials are secure production values."""
        auditor = self.fresh_auditor()
        secure_env = {
            "JWT_SECRET": "c7a8f09b2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a",
            "DB_PASSWORD": "P$9vK!mX7#qL2wE5@rT8zY1*uI4oP6aS",
            "KEYCLOAK_CLIENT_SECRET": "9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b",
        }
        result = auditor.verify_no_dev_credentials(secure_env)
        assert result.status == CheckStatus.PASS

    def test_jwt_signature_enforcement_in_production(self):
        """JWT signature enforcement is mandatory and PASS in production mode."""
        auditor = self.fresh_auditor()
        result = auditor.verify_jwt_signature_enforcement(environment="production")
        assert result.status == CheckStatus.PASS
        assert result.blocking is True

    def test_jwt_signature_enforcement_warns_in_dev(self):
        """JWT signature enforcement reports WARN in local development mode."""
        auditor = self.fresh_auditor()
        result = auditor.verify_jwt_signature_enforcement(environment="local_development")
        assert result.status == CheckStatus.WARN
        assert result.blocking is False

    def test_tls_enforcement_pass_when_enabled(self):
        """TLS check passes when TLS is enabled."""
        auditor = self.fresh_auditor()
        result = auditor.verify_tls_enforcement(tls_enabled=True)
        assert result.status == CheckStatus.PASS

    def test_tls_enforcement_fails_when_disabled(self):
        """TLS check fails when TLS is disabled."""
        auditor = self.fresh_auditor()
        result = auditor.verify_tls_enforcement(tls_enabled=False)
        assert result.status == CheckStatus.FAIL
        assert result.blocking is True

    def test_observability_and_alerts_check(self):
        """Prometheus metrics exposition and structured logging check passes."""
        auditor = self.fresh_auditor()
        result = auditor.verify_observability_and_alerts()
        assert result.status == CheckStatus.PASS

    def test_backup_and_recovery_readiness_check(self):
        """Backup integrity and restore verification readiness check passes."""
        auditor = self.fresh_auditor()
        result = auditor.verify_backup_and_recovery_readiness()
        assert result.status == CheckStatus.PASS

    def test_privacy_lifecycle_check(self):
        """Privacy lifecycle and erasure check passes."""
        auditor = self.fresh_auditor()
        result = auditor.verify_privacy_lifecycle()
        assert result.status == CheckStatus.PASS

    def test_full_readiness_audit_overall_verdict(self):
        """Full readiness audit returns production_ready=True when all checks pass."""
        auditor = self.fresh_auditor()
        secure_env = {
            "JWT_SECRET": "strong_random_secret_token_value_xyz123456",
            "DB_PASSWORD": "strong_db_password_prod_secure_987",
        }
        report = auditor.run_full_readiness_audit(env_vars=secure_env)
        assert report["production_ready"] is True
        assert report["failed"] == 0
        assert report["total_checks"] >= 6
