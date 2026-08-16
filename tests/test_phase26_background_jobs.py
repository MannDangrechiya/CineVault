# CineVault OS — Phase 26 Background Jobs / Queue Tests
# Verifies job submission, idempotency, backpressure, status lifecycle,
# dead-letter escalation, recovery, cancellation, and API endpoints.

import time
import uuid
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.jobs import (
    JobRegistry,
    JobType,
    JobStatus,
    BackpressureError,
    retry_delay_seconds,
    BACKPRESSURE_LIMITS,
    MAX_RETRIES,
)

client = TestClient(app)
SERVICE_IDENTITY = "cinevault-internal-ops"


class TestPhase26BackgroundJobs:
    """Phase 26 — Background Jobs / Queue: registry, lifecycle, idempotency, backpressure, DLQ, API."""

    # Use fresh registry per test to avoid cross-test pollution
    def fresh_registry(self) -> JobRegistry:
        return JobRegistry()

    # ------------------------------------------------------------------
    # 1. Job Submission
    # ------------------------------------------------------------------
    def test_submit_basic_job(self):
        """Jobs can be submitted and return a PENDING envelope."""
        reg = self.fresh_registry()
        job = reg.submit(
            job_type=JobType.INGESTION,
            payload={"provider": "TMDB", "title_id": "tt1234567"},
        )
        assert job.status == JobStatus.PENDING
        assert job.job_type == JobType.INGESTION
        assert job.attempt_count == 0
        assert job.job_id is not None

    def test_submit_all_job_types(self):
        """All 8 job types can be submitted without error."""
        reg = self.fresh_registry()
        for jt in JobType:
            job = reg.submit(job_type=jt, payload={"test": True})
            assert job.status == JobStatus.PENDING

    # ------------------------------------------------------------------
    # 2. Idempotency
    # ------------------------------------------------------------------
    def test_idempotent_submit_returns_same_job(self):
        """Submitting with the same idempotency_key returns the existing job."""
        reg = self.fresh_registry()
        idem = str(uuid.uuid4())
        job1 = reg.submit(JobType.SYNC, {"batch": 1}, idempotency_key=idem)
        job2 = reg.submit(JobType.SYNC, {"batch": 2}, idempotency_key=idem)
        assert job1.job_id == job2.job_id
        assert job2.payload == {"batch": 1}  # original payload preserved

    def test_different_idempotency_keys_create_different_jobs(self):
        """Different idempotency keys create separate job entries."""
        reg = self.fresh_registry()
        job1 = reg.submit(JobType.EXPORT, {"user": "a"}, idempotency_key="key-a")
        job2 = reg.submit(JobType.EXPORT, {"user": "b"}, idempotency_key="key-b")
        assert job1.job_id != job2.job_id

    # ------------------------------------------------------------------
    # 3. Backpressure
    # ------------------------------------------------------------------
    def test_backpressure_rejects_when_queue_full(self):
        """BackpressureError raised when pending job count hits limit."""
        reg = self.fresh_registry()
        limit = BACKPRESSURE_LIMITS[JobType.RECOMMENDATIONS]
        # Fill queue to limit
        for i in range(limit):
            reg.submit(JobType.RECOMMENDATIONS, {"i": i}, idempotency_key=f"bp-{i}")
        # Next submission should be rejected
        with pytest.raises(BackpressureError):
            reg.submit(JobType.RECOMMENDATIONS, {"overflow": True}, idempotency_key="bp-overflow")

    def test_backpressure_not_triggered_below_limit(self):
        """Submissions below limit succeed without error."""
        reg = self.fresh_registry()
        job = reg.submit(JobType.QUALITY_PROCESSING, {"check": "ok"})
        assert job.status == JobStatus.PENDING

    # ------------------------------------------------------------------
    # 4. Status Lifecycle
    # ------------------------------------------------------------------
    def test_job_lifecycle_pending_to_succeeded(self):
        """Full happy path: PENDING → RUNNING → SUCCEEDED."""
        reg = self.fresh_registry()
        job = reg.submit(JobType.METADATA_REFRESH, {"title_id": "tt9999"})
        assert job.status == JobStatus.PENDING

        reg.mark_running(job.job_id)
        job = reg.get_job(job.job_id)
        assert job.status == JobStatus.RUNNING
        assert job.attempt_count == 1
        assert job.started_at is not None

        reg.mark_succeeded(job.job_id, result={"updated_fields": 3})
        job = reg.get_job(job.job_id)
        assert job.status == JobStatus.SUCCEEDED
        assert job.result["updated_fields"] == 3
        assert job.completed_at is not None

    def test_job_failure_before_max_retries(self):
        """Job failure before max retries stays FAILED (not DEAD_LETTER)."""
        reg = self.fresh_registry()
        job = reg.submit(JobType.INGESTION, {"provider": "IMDb"}, max_retries_override=2)
        reg.mark_running(job.job_id)
        reg.mark_failed(job.job_id, error="provider_timeout")
        job = reg.get_job(job.job_id)
        # 1 attempt, max_attempts=3 (2 retries + initial), so not dead-letter yet
        assert job.status == JobStatus.FAILED
        assert job.error == "provider_timeout"

    def test_job_escalates_to_dead_letter_after_max_retries(self):
        """Job escalates to DEAD_LETTER after exhausting all retry attempts."""
        reg = self.fresh_registry()
        job = reg.submit(JobType.QUALITY_PROCESSING, {"batch": "x"}, max_retries_override=0)
        # max_attempts = 0 retries + 1 = 1 total attempt
        reg.mark_running(job.job_id)
        reg.mark_failed(job.job_id, error="permanent_failure")
        job = reg.get_job(job.job_id)
        assert job.status == JobStatus.DEAD_LETTER
        assert job.dead_letter_reason is not None
        assert "permanent_failure" in job.dead_letter_reason

    def test_job_cancellation(self):
        """PENDING jobs can be cancelled."""
        reg = self.fresh_registry()
        job = reg.submit(JobType.EXPORT, {"format": "json"})
        reg.cancel(job.job_id)
        job = reg.get_job(job.job_id)
        assert job.status == JobStatus.CANCELLED

    def test_cannot_cancel_running_job(self):
        """RUNNING jobs cannot be cancelled."""
        reg = self.fresh_registry()
        job = reg.submit(JobType.SYNC, {"delta": True})
        reg.mark_running(job.job_id)
        with pytest.raises(ValueError):
            reg.cancel(job.job_id)

    # ------------------------------------------------------------------
    # 5. Dead Letter Queue
    # ------------------------------------------------------------------
    def test_dead_letter_jobs_retrievable(self):
        """get_dead_letter_jobs returns DLQ entries."""
        reg = self.fresh_registry()
        job = reg.submit(JobType.RECONCILIATION, {"conflict_id": "c-001"}, max_retries_override=0)
        reg.mark_running(job.job_id)
        reg.mark_failed(job.job_id, error="irrecoverable")
        dlq = reg.get_dead_letter_jobs()
        assert any(j["job_id"] == job.job_id for j in dlq)
        assert any(j["status"] == "DEAD_LETTER" for j in dlq)

    # ------------------------------------------------------------------
    # 6. Recovery
    # ------------------------------------------------------------------
    def test_recover_stuck_running_job(self):
        """Stuck RUNNING jobs beyond threshold are recovered to FAILED or DEAD_LETTER."""
        reg = self.fresh_registry()
        job = reg.submit(JobType.AVAILABILITY_REFRESH, {"region": "IN"}, max_retries_override=2)
        reg.mark_running(job.job_id)
        # Manually backdate start time to simulate stuck job
        reg._jobs[job.job_id].started_at = time.time() - 400
        recovered = reg.recover_stuck_jobs(stuck_threshold_seconds=300.0)
        assert job.job_id in recovered
        job = reg.get_job(job.job_id)
        assert job.status in (JobStatus.FAILED, JobStatus.DEAD_LETTER)

    # ------------------------------------------------------------------
    # 7. Status Summary
    # ------------------------------------------------------------------
    def test_status_summary_structure(self):
        """get_status_summary returns expected keys."""
        reg = self.fresh_registry()
        reg.submit(JobType.INGESTION, {"p": "TMDB"})
        summary = reg.get_status_summary()
        assert "total_jobs" in summary
        assert "dead_letter_count" in summary
        assert "pending_by_type" in summary
        assert "status_counts" in summary

    # ------------------------------------------------------------------
    # 8. Retry Delay Calculator
    # ------------------------------------------------------------------
    def test_retry_delay_exponential_growth(self):
        """Retry delay grows exponentially with attempt count."""
        assert retry_delay_seconds(0) == 1.0   # 2^0 = 1
        assert retry_delay_seconds(1) == 2.0   # 2^1 = 2
        assert retry_delay_seconds(2) == 4.0   # 2^2 = 4
        assert retry_delay_seconds(3) == 8.0   # 2^3 = 8

    def test_retry_delay_capped_at_maximum(self):
        """Retry delay is capped at 60 seconds."""
        assert retry_delay_seconds(10) == 60.0  # 2^10=1024, capped to 60

    # ------------------------------------------------------------------
    # 9. Jobs API Endpoints
    # ------------------------------------------------------------------
    def test_jobs_submit_endpoint(self):
        """POST /internal/v1/jobs/submit returns 202 with job details."""
        resp = client.post(
            "/internal/v1/jobs/submit",
            headers={"X-Service-Identity": SERVICE_IDENTITY},
            json={
                "job_type": "ingestion",
                "payload": {"provider": "TMDB", "title_id": "tt0000001"},
                "idempotency_key": f"test-submit-{uuid.uuid4()}",
            }
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "job_id" in data
        assert data["status"] == "PENDING"

    def test_jobs_submit_requires_service_identity(self):
        """Job submission without X-Service-Identity is rejected with 401."""
        resp = client.post(
            "/internal/v1/jobs/submit",
            json={"job_type": "sync", "payload": {}}
        )
        assert resp.status_code == 401

    def test_jobs_submit_invalid_type(self):
        """Invalid job_type returns 400."""
        resp = client.post(
            "/internal/v1/jobs/submit",
            headers={"X-Service-Identity": SERVICE_IDENTITY},
            json={"job_type": "invalid_type", "payload": {}}
        )
        assert resp.status_code == 400

    def test_jobs_status_endpoint(self):
        """GET /internal/v1/jobs/{job_id}/status returns full job details."""
        # First submit
        submit_resp = client.post(
            "/internal/v1/jobs/submit",
            headers={"X-Service-Identity": SERVICE_IDENTITY},
            json={"job_type": "export", "payload": {"format": "json"}, "idempotency_key": f"status-test-{uuid.uuid4()}"}
        )
        job_id = submit_resp.json()["job_id"]

        status_resp = client.get(
            f"/internal/v1/jobs/{job_id}/status",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["job_id"] == job_id
        assert data["status"] == "PENDING"

    def test_jobs_status_not_found(self):
        """Non-existent job_id returns 404."""
        resp = client.get(
            "/internal/v1/jobs/non-existent-id/status",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 404

    def test_jobs_summary_endpoint(self):
        """GET /internal/v1/jobs/summary returns queue summary."""
        resp = client.get(
            "/internal/v1/jobs/summary",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_jobs" in data
        assert "pending_by_type" in data

    def test_jobs_dead_letter_endpoint(self):
        """GET /internal/v1/jobs/dead-letter returns DLQ list."""
        resp = client.get(
            "/internal/v1/jobs/dead-letter",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "dead_letter_jobs" in data
        assert isinstance(data["dead_letter_jobs"], list)

    def test_jobs_recovery_endpoint(self):
        """POST /internal/v1/jobs/recover returns recovered job IDs list."""
        resp = client.post(
            "/internal/v1/jobs/recover",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recovered_job_ids" in data
        assert isinstance(data["recovered_job_ids"], list)

    def test_jobs_idempotent_submit_via_api(self):
        """API idempotent submit returns same job_id for same idempotency_key."""
        idem = f"idem-api-{uuid.uuid4()}"
        payload = {"job_type": "sync", "payload": {"delta": True}, "idempotency_key": idem}
        headers = {"X-Service-Identity": SERVICE_IDENTITY}

        r1 = client.post("/internal/v1/jobs/submit", headers=headers, json=payload)
        r2 = client.post("/internal/v1/jobs/submit", headers=headers, json=payload)
        assert r1.status_code == 202
        assert r2.status_code == 202
        assert r1.json()["job_id"] == r2.json()["job_id"]
