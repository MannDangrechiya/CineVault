# CineVault OS — Background Job Scheduler & Worker Layer (Phase 26)
# Provides job envelope definitions, in-process job registry, status tracking,
# retry/backoff, backpressure, idempotency, dead-letter escalation, and recovery.
#
# Workloads covered:
#   ingestion, metadata_refresh, quality_processing, reconciliation,
#   availability_refresh, recommendations, export, sync
#
# Constraint: Queue is used for real workload only. This module does NOT
# introduce queue machinery purely for architectural decoration.

import uuid
import time
import logging
import threading
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

from .telemetry import signal_router, metrics_collector

logger = logging.getLogger("cinevault.jobs")

# ---------------------------------------------------------------------------
# Job Definitions
# ---------------------------------------------------------------------------
class JobType(str, Enum):
    INGESTION = "ingestion"
    METADATA_REFRESH = "metadata_refresh"
    QUALITY_PROCESSING = "quality_processing"
    RECONCILIATION = "reconciliation"
    AVAILABILITY_REFRESH = "availability_refresh"
    RECOMMENDATIONS = "recommendations"
    EXPORT = "export"
    SYNC = "sync"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"
    CANCELLED = "CANCELLED"


# Backpressure: max queue depth per job type before rejecting new submissions
BACKPRESSURE_LIMITS: Dict[str, int] = {
    JobType.INGESTION: 500,
    JobType.METADATA_REFRESH: 200,
    JobType.QUALITY_PROCESSING: 300,
    JobType.RECONCILIATION: 100,
    JobType.AVAILABILITY_REFRESH: 200,
    JobType.RECOMMENDATIONS: 50,
    JobType.EXPORT: 20,
    JobType.SYNC: 1000,
}

# Retry policy per job type
MAX_RETRIES: Dict[str, int] = {
    JobType.INGESTION: 3,
    JobType.METADATA_REFRESH: 3,
    JobType.QUALITY_PROCESSING: 2,
    JobType.RECONCILIATION: 2,
    JobType.AVAILABILITY_REFRESH: 3,
    JobType.RECOMMENDATIONS: 1,
    JobType.EXPORT: 2,
    JobType.SYNC: 5,
}


@dataclass
class JobEnvelope:
    """Represents a single unit of work with full lifecycle tracking."""
    job_id: str
    job_type: JobType
    payload: Dict[str, Any]
    idempotency_key: str
    correlation_id: str
    submitted_at: float
    status: JobStatus = JobStatus.PENDING
    attempt_count: int = 0
    max_attempts: int = 3
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    dead_letter_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # `payload` is intentionally excluded from the wire representation (matches
        # the prior manual field listing, which never surfaced the raw job payload here).
        data.pop("payload", None)
        return data


# ---------------------------------------------------------------------------
# Job Registry
# ---------------------------------------------------------------------------
class BackpressureError(Exception):
    """Raised when job submission is rejected due to queue depth limit."""
    pass


class DuplicateJobError(Exception):
    """Raised when a job with the same idempotency_key is already known."""
    pass


class JobRegistry:
    """
    In-process job registry providing:
    - Job submission with idempotency enforcement
    - Backpressure limits per job type
    - Status tracking and result storage
    - Dead-letter escalation after max retries
    - Recovery scanning for stuck RUNNING jobs
    """

    def __init__(self):
        self._jobs: Dict[str, JobEnvelope] = {}             # job_id → JobEnvelope
        self._idempotency_index: Dict[str, str] = {}        # idempotency_key → job_id
        self._pending_by_type: Dict[str, List[str]] = {t: [] for t in JobType}
        self._dead_letter: List[str] = []
        self._lock = threading.Lock()

    # --- Submission ---
    def submit(
        self,
        job_type: JobType,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None,
        correlation_id: Optional[str] = None,
        max_retries_override: Optional[int] = None,
    ) -> JobEnvelope:
        """
        Submit a new job. Enforces idempotency, backpressure, and payload safety.
        Returns the existing job if already submitted with the same idempotency_key.
        """
        idem_key = idempotency_key or str(uuid.uuid4())
        corr_id = correlation_id or str(uuid.uuid4())

        with self._lock:
            # Idempotency: return existing job
            if idem_key in self._idempotency_index:
                existing_id = self._idempotency_index[idem_key]
                existing = self._jobs[existing_id]
                logger.info(f"Idempotent submit: returning existing job {existing_id} for key={idem_key}")
                return existing

            # Backpressure: reject if queue is too deep
            pending_count = len(self._pending_by_type.get(job_type, []))
            limit = BACKPRESSURE_LIMITS.get(job_type, 100)
            if pending_count >= limit:
                signal_router.emit(
                    "SYSTEM", "JOB_BACKPRESSURE_REJECT",
                    job_type=job_type, pending_count=pending_count, limit=limit,
                    severity="WARN"
                )
                raise BackpressureError(
                    f"Job queue for {job_type} is at capacity ({pending_count}/{limit}). "
                    f"Retry later or reduce submission rate."
                )

            max_att = max_retries_override if max_retries_override is not None else MAX_RETRIES.get(job_type, 3)

            job = JobEnvelope(
                job_id=str(uuid.uuid4()),
                job_type=job_type,
                payload=payload,
                idempotency_key=idem_key,
                correlation_id=corr_id,
                submitted_at=time.time(),
                max_attempts=max_att + 1,  # +1 to count initial attempt
            )

            self._jobs[job.job_id] = job
            self._idempotency_index[idem_key] = job.job_id
            self._pending_by_type[job_type].append(job.job_id)

            signal_router.emit(
                "SYSTEM", "JOB_SUBMITTED",
                job_id=job.job_id, job_type=job_type,
                correlation_id=corr_id
            )
            logger.info(f"Job submitted: {job.job_id} type={job_type}")
            return job

    # --- Status Updates ---
    def mark_running(self, job_id: str) -> JobEnvelope:
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.RUNNING
            job.started_at = time.time()
            job.attempt_count += 1
            return job

    def mark_succeeded(self, job_id: str, result: Optional[Dict[str, Any]] = None) -> JobEnvelope:
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.SUCCEEDED
            job.completed_at = time.time()
            job.result = result or {}
            self._remove_from_pending(job)
            signal_router.emit(
                "SYSTEM", "JOB_SUCCEEDED",
                job_id=job_id, job_type=job.job_type,
                duration_s=round(job.completed_at - (job.started_at or job.submitted_at), 3)
            )
            return job

    def mark_failed(self, job_id: str, error: str) -> JobEnvelope:
        """Marks a job as failed and escalates to dead-letter if max retries reached."""
        with self._lock:
            job = self._jobs[job_id]
            job.error = error
            job.completed_at = time.time()

            if job.attempt_count >= job.max_attempts:
                job.status = JobStatus.DEAD_LETTER
                job.dead_letter_reason = f"Exhausted {job.max_attempts} attempts. Last error: {error}"
                self._dead_letter.append(job_id)
                self._remove_from_pending(job)
                signal_router.emit(
                    "SYSTEM", "JOB_DEAD_LETTER",
                    job_id=job_id, job_type=job.job_type,
                    reason=job.dead_letter_reason,
                    severity="ERROR"
                )
                logger.error(f"Job {job_id} escalated to dead-letter: {job.dead_letter_reason}")
            else:
                job.status = JobStatus.FAILED
                signal_router.emit(
                    "SYSTEM", "JOB_FAILED",
                    job_id=job_id, job_type=job.job_type,
                    attempt=job.attempt_count, max_attempts=job.max_attempts,
                    error=error, severity="WARN"
                )
                logger.warning(f"Job {job_id} failed (attempt {job.attempt_count}/{job.max_attempts}): {error}")
            return job

    def cancel(self, job_id: str) -> JobEnvelope:
        with self._lock:
            job = self._jobs[job_id]
            if job.status not in (JobStatus.PENDING, JobStatus.FAILED):
                raise ValueError(f"Cannot cancel job in status {job.status}")
            job.status = JobStatus.CANCELLED
            self._remove_from_pending(job)
            return job

    def _remove_from_pending(self, job: JobEnvelope):
        pending = self._pending_by_type.get(job.job_type, [])
        if job.job_id in pending:
            pending.remove(job.job_id)

    # --- Queries ---
    def get_job(self, job_id: str) -> Optional[JobEnvelope]:
        return self._jobs.get(job_id)

    def get_status_summary(self) -> Dict[str, Any]:
        with self._lock:
            status_counts: Dict[str, int] = {s: 0 for s in JobStatus}
            for job in self._jobs.values():
                status_counts[job.status] = status_counts.get(job.status, 0) + 1

            return {
                "total_jobs": len(self._jobs),
                "dead_letter_count": len(self._dead_letter),
                "pending_by_type": {t: len(ids) for t, ids in self._pending_by_type.items()},
                "status_counts": status_counts,
            }

    def get_dead_letter_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            result = []
            for job_id in self._dead_letter[-limit:]:
                job = self._jobs.get(job_id)
                if job:
                    result.append(job.to_dict())
            return result

    def recover_stuck_jobs(self, stuck_threshold_seconds: float = 300.0) -> List[str]:
        """
        Scans for jobs stuck in RUNNING status for longer than threshold and marks them failed.
        Returns list of recovered job IDs.
        """
        now = time.time()
        recovered = []
        with self._lock:
            for job in list(self._jobs.values()):
                if job.status == JobStatus.RUNNING and job.started_at:
                    if (now - job.started_at) > stuck_threshold_seconds:
                        job.error = f"Job stuck for >{stuck_threshold_seconds}s — auto-recovered"
                        if job.attempt_count >= job.max_attempts:
                            job.status = JobStatus.DEAD_LETTER
                            job.dead_letter_reason = job.error
                            self._dead_letter.append(job.job_id)
                        else:
                            job.status = JobStatus.FAILED
                        recovered.append(job.job_id)
                        logger.warning(f"Recovered stuck job {job.job_id}")
        return recovered


# Singleton job registry
job_registry = JobRegistry()


# ---------------------------------------------------------------------------
# Exponential Backoff Retry Delay Calculator
# ---------------------------------------------------------------------------
def retry_delay_seconds(attempt: int, base: float = 2.0, cap: float = 60.0) -> float:
    """Computes exponential backoff delay: min(base^attempt, cap)."""
    return min(base ** attempt, cap)
