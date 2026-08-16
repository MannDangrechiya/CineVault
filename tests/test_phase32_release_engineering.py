# CineVault OS — Phase 32 Release Engineering Tests
# Verifies release manifests, criteria validation (tests, migration, security, known issues, rollback plan),
# approval gates, deployment lifecycle, rollback execution, and environment profiles.

import pytest
from typing import Tuple
from services.api.release_engine import (
    ReleaseManager,
    ReleaseManifest,
    ReleaseStatus,
    Environment,
    ENVIRONMENT_PROFILES,
    release_manager,
)


class TestPhase32ReleaseEngineering:
    """Phase 32 — Release Engineering: manifests, mandatory criteria, approvals, deployment, rollback."""

    def fresh_mgr(self) -> ReleaseManager:
        return ReleaseManager()

    # ------------------------------------------------------------------
    # 1. Environment Profiles
    # ------------------------------------------------------------------
    def test_environment_profiles_exist_for_all_environments(self):
        """All 4 environments have defined profiles with required settings."""
        for env in Environment:
            assert env in ENVIRONMENT_PROFILES
            prof = ENVIRONMENT_PROFILES[env]
            assert "debug" in prof
            assert "allow_seed_fallback" in prof
            assert "enforce_strict_jwt_signatures" in prof
            assert "tls_required" in prof

    def test_production_environment_has_strict_security(self):
        """Production environment requires TLS and strict JWT signatures, disallows seed fallback."""
        prod = ENVIRONMENT_PROFILES[Environment.PRODUCTION]
        assert prod["tls_required"] is True
        assert prod["enforce_strict_jwt_signatures"] is True
        assert prod["allow_seed_fallback"] is False
        assert prod["debug"] is False

    # ------------------------------------------------------------------
    # 2. Release Manifest & Mandatory Criteria Validation
    # ------------------------------------------------------------------
    def test_valid_release_manifest_validates_successfully(self):
        """A complete release manifest with all 5 mandatory criteria passes validation."""
        mgr = self.fresh_mgr()
        manifest = mgr.create_release(
            version="1.0.0",
            target_environment=Environment.PRODUCTION,
            tests_passed=True,
            test_run_id="run-001",
            total_tests_count=250,
            migration_applied=True,
            migration_version="v001_canonical_schema",
            security_audit_passed=True,
            security_report_id="sec-001",
            known_issues=["Minor: dark mode toggle transition delay on safari"],
        )
        assert manifest.status == ReleaseStatus.VALIDATED
        valid, errors = manifest.validate_release_criteria()
        assert valid is True
        assert len(errors) == 0

    def test_release_rejected_if_tests_not_passed(self):
        """Release criteria fails if tests_passed is False."""
        mgr = self.fresh_mgr()
        manifest = mgr.create_release(
            version="1.0.0",
            target_environment=Environment.PRODUCTION,
            tests_passed=False,  # Failed tests
            test_run_id="run-002",
            total_tests_count=200,
            migration_applied=True,
            migration_version="v001",
            security_audit_passed=True,
            security_report_id="sec-001",
        )
        assert manifest.status == ReleaseStatus.DRAFT
        valid, errors = manifest.validate_release_criteria()
        assert valid is False
        assert any("tests" in e.lower() for e in errors)

    def test_release_rejected_if_migration_not_applied(self):
        """Release criteria fails if migration_applied is False."""
        mgr = self.fresh_mgr()
        manifest = mgr.create_release(
            version="1.0.0",
            target_environment=Environment.PRODUCTION,
            tests_passed=True,
            test_run_id="run-003",
            total_tests_count=200,
            migration_applied=False,  # Unapplied migration
            migration_version="",
            security_audit_passed=True,
            security_report_id="sec-001",
        )
        valid, errors = manifest.validate_release_criteria()
        assert valid is False
        assert any("migration" in e.lower() for e in errors)

    def test_release_rejected_if_security_audit_not_passed(self):
        """Release criteria fails if security_audit_passed is False."""
        mgr = self.fresh_mgr()
        manifest = mgr.create_release(
            version="1.0.0",
            target_environment=Environment.PRODUCTION,
            tests_passed=True,
            test_run_id="run-004",
            total_tests_count=200,
            migration_applied=True,
            migration_version="v001",
            security_audit_passed=False,  # Security failure
            security_report_id="",
        )
        valid, errors = manifest.validate_release_criteria()
        assert valid is False
        assert any("security" in e.lower() for e in errors)

    def test_release_rejected_if_invalid_semver(self):
        """Release criteria fails if version is not valid SemVer."""
        mgr = self.fresh_mgr()
        manifest = mgr.create_release(
            version="not-a-valid-version-number",
            target_environment=Environment.PRODUCTION,
            tests_passed=True,
            test_run_id="run-005",
            total_tests_count=200,
            migration_applied=True,
            migration_version="v001",
            security_audit_passed=True,
            security_report_id="sec-001",
        )
        valid, errors = manifest.validate_release_criteria()
        assert valid is False
        assert any("semver" in e.lower() for e in errors)

    # ------------------------------------------------------------------
    # 3. Approval & Deployment Lifecycle
    # ------------------------------------------------------------------
    def test_release_approval_and_deployment_lifecycle(self):
        """Happy path: DRAFT/VALIDATED -> APPROVED -> DEPLOYED."""
        mgr = self.fresh_mgr()
        manifest = mgr.create_release(
            version="1.0.0",
            target_environment=Environment.STAGING,
            tests_passed=True,
            test_run_id="run-006",
            total_tests_count=250,
            migration_applied=True,
            migration_version="v001",
            security_audit_passed=True,
            security_report_id="sec-001",
        )
        assert manifest.status == ReleaseStatus.VALIDATED

        # Approve
        approved = mgr.approve_release(manifest.release_id, approver_id="lead_eng_01")
        assert approved.status == ReleaseStatus.APPROVED
        assert approved.approved_by == "lead_eng_01"
        assert approved.approved_at is not None

        # Deploy
        deployed = mgr.deploy_release(manifest.release_id)
        assert deployed.status == ReleaseStatus.DEPLOYED
        assert deployed.deployed_at is not None

    def test_cannot_deploy_unapproved_release(self):
        """Attempting to deploy an unapproved release raises ValueError."""
        mgr = self.fresh_mgr()
        manifest = mgr.create_release(
            version="1.0.0",
            target_environment=Environment.PRODUCTION,
            tests_passed=True,
            test_run_id="run-007",
            total_tests_count=200,
            migration_applied=True,
            migration_version="v001",
            security_audit_passed=True,
            security_report_id="sec-001",
        )
        with pytest.raises(ValueError, match="APPROVED"):
            mgr.deploy_release(manifest.release_id)

    # ------------------------------------------------------------------
    # 4. Rollback Execution
    # ------------------------------------------------------------------
    def test_rollback_deployed_release(self):
        """Deployed release can be rolled back with documented reason."""
        mgr = self.fresh_mgr()
        manifest = mgr.create_release(
            version="1.0.0",
            target_environment=Environment.PRODUCTION,
            tests_passed=True,
            test_run_id="run-008",
            total_tests_count=250,
            migration_applied=True,
            migration_version="v001",
            security_audit_passed=True,
            security_report_id="sec-001",
        )
        mgr.approve_release(manifest.release_id, approver_id="lead_01")
        mgr.deploy_release(manifest.release_id)

        # Rollback
        rolled_back = mgr.rollback_release(manifest.release_id, reason="Elevated 500 error rate in region ap-south-1")
        assert rolled_back.status == ReleaseStatus.ROLLED_BACK
        assert rolled_back.rollback_at is not None

    def test_cannot_rollback_non_deployed_release(self):
        """Attempting to rollback a draft/approved release raises ValueError."""
        mgr = self.fresh_mgr()
        manifest = mgr.create_release(
            version="1.0.0",
            target_environment=Environment.PRODUCTION,
            tests_passed=True,
            test_run_id="run-009",
            total_tests_count=200,
            migration_applied=True,
            migration_version="v001",
            security_audit_passed=True,
            security_report_id="sec-001",
        )
        with pytest.raises(ValueError, match="DEPLOYED"):
            mgr.rollback_release(manifest.release_id, reason="premature rollback")

    # ------------------------------------------------------------------
    # 5. Queries & Listing
    # ------------------------------------------------------------------
    def test_list_releases_filtered_by_environment(self):
        """list_releases returns all releases or filtered by target environment."""
        mgr = self.fresh_mgr()
        mgr.create_release(
            version="1.0.0", target_environment=Environment.STAGING,
            tests_passed=True, test_run_id="r1", total_tests_count=100,
            migration_applied=True, migration_version="v1", security_audit_passed=True, security_report_id="s1"
        )
        mgr.create_release(
            version="1.0.0", target_environment=Environment.PRODUCTION,
            tests_passed=True, test_run_id="r2", total_tests_count=100,
            migration_applied=True, migration_version="v1", security_audit_passed=True, security_report_id="s2"
        )

        all_rel = mgr.list_releases()
        assert len(all_rel) == 2
        prod_only = mgr.list_releases(environment=Environment.PRODUCTION)
        assert len(prod_only) == 1
        assert prod_only[0]["target_environment"] == Environment.PRODUCTION
