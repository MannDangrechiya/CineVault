# CineVault OS — Phase 31 CI/CD Workflow Validation Tests
# Verifies GitHub Actions workflow syntax, jobs, coverage (backend, frontend, Flutter, lint, security),
# and the release gate constraint (no automatic unapproved production deployments).

import os
import yaml
import pytest

WORKFLOWS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".github", "workflows")


class TestPhase31CICDWorkflows:
    """Phase 31 — CI/CD: workflow syntax, matrix testing, linting, security, and release gate enforcement."""

    def test_workflows_directory_exists(self):
        """GitHub workflows directory exists and contains yaml files."""
        assert os.path.isdir(WORKFLOWS_DIR)
        files = os.listdir(WORKFLOWS_DIR)
        assert "ci.yml" in files
        assert "release-gate.yml" in files

    def test_ci_workflow_valid_yaml(self):
        """ci.yml is valid YAML and parses properly."""
        ci_path = os.path.join(WORKFLOWS_DIR, "ci.yml")
        with open(ci_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert "jobs" in data
        assert "on" in data or True in data

    def test_ci_workflow_covers_all_required_components(self):
        """ci.yml includes jobs for backend tests, lint/security, frontend, and flutter."""
        ci_path = os.path.join(WORKFLOWS_DIR, "ci.yml")
        with open(ci_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        jobs = data["jobs"]
        assert "backend-lint-security" in jobs
        assert "backend-tests" in jobs
        assert "frontend-web-ci" in jobs
        assert "flutter-client-ci" in jobs

    def test_ci_workflow_backend_matrix(self):
        """Backend tests use a multi-version Python matrix."""
        ci_path = os.path.join(WORKFLOWS_DIR, "ci.yml")
        with open(ci_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        backend_job = data["jobs"]["backend-tests"]
        assert "strategy" in backend_job
        assert "matrix" in backend_job["strategy"]
        py_versions = backend_job["strategy"]["matrix"]["python-version"]
        assert "3.11" in py_versions
        assert "3.12" in py_versions

    def test_ci_workflow_has_services(self):
        """Backend CI provisions Postgres, Valkey, and RabbitMQ container services."""
        ci_path = os.path.join(WORKFLOWS_DIR, "ci.yml")
        with open(ci_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        services = data["jobs"]["backend-tests"]["services"]
        assert "postgres" in services
        assert "valkey" in services
        assert "rabbitmq" in services

    def test_release_gate_workflow_valid_yaml(self):
        """release-gate.yml is valid YAML and parses properly."""
        rg_path = os.path.join(WORKFLOWS_DIR, "release-gate.yml")
        with open(rg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert "jobs" in data
        assert "verify-release-gate" in data["jobs"]

    def test_release_gate_enforces_gated_production_deployment(self):
        """Constraint: Production deployment requires release gate verification and environment protection."""
        rg_path = os.path.join(WORKFLOWS_DIR, "release-gate.yml")
        with open(rg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        prod_job = data["jobs"]["deploy-production"]
        assert prod_job["environment"]["name"] == "production"
        assert "needs" in prod_job
        # Must depend on build and staging verification
        assert "build-and-package" in prod_job["needs"]
        assert "deploy-staging" in prod_job["needs"]
