# CineVault OS — Background Jobs Internal Router (Phase 26)
# Exposes job management endpoints:
#   POST /internal/v1/jobs/submit              — submit a background job
#   GET  /internal/v1/jobs/{job_id}/status     — get job status
#   POST /internal/v1/jobs/{job_id}/cancel     — cancel pending/failed job
#   GET  /internal/v1/jobs/summary             — queue depth and status summary
#   GET  /internal/v1/jobs/dead-letter         — dead-letter queue inspection
#   POST /internal/v1/jobs/recover             — trigger stuck-job recovery scan
#
# Access restricted to internal service identity (X-Service-Identity header).

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from ..jobs import (
    job_registry,
    JobType,
    BackpressureError,
    DuplicateJobError,
    retry_delay_seconds,
)

router = APIRouter(
    prefix="/internal/v1/jobs",
    tags=["Background Jobs"],
)


def _require_service_identity(request: Request):
    identity = request.headers.get("X-Service-Identity", "")
    if not identity:
        raise HTTPException(status_code=401, detail="X-Service-Identity header required")
    return identity


class JobSubmitRequest(BaseModel):
    job_type: str
    payload: Dict[str, Any]
    idempotency_key: Optional[str] = None
    correlation_id: Optional[str] = None


@router.post("/submit", status_code=202)
async def submit_job(request: Request, body: JobSubmitRequest):
    """
    Submit a background job to the appropriate workload queue.
    Enforces idempotency (returns existing job if same idempotency_key).
    Enforces backpressure limits per job type.
    """
    _require_service_identity(request)

    # Validate job type
    try:
        job_type = JobType(body.job_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job_type '{body.job_type}'. Must be one of: {[t.value for t in JobType]}"
        )

    try:
        job = job_registry.submit(
            job_type=job_type,
            payload=body.payload,
            idempotency_key=body.idempotency_key,
            correlation_id=body.correlation_id,
        )
    except BackpressureError as e:
        raise HTTPException(status_code=429, detail=str(e))

    return {
        "job_id": job.job_id,
        "job_type": job.job_type,
        "status": job.status,
        "idempotency_key": job.idempotency_key,
        "submitted_at": job.submitted_at,
        "message": "Job accepted" if job.attempt_count == 0 else "Existing job returned (idempotent)",
    }


@router.get("/{job_id}/status")
async def get_job_status(request: Request, job_id: str):
    """Returns current status and lifecycle details of a job by ID."""
    _require_service_identity(request)

    job = job_registry.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    data = job.to_dict()

    # Include retry delay hint for FAILED jobs that can still be retried
    if job.status.value == "FAILED":
        data["next_retry_delay_s"] = retry_delay_seconds(job.attempt_count)

    return data


@router.post("/{job_id}/cancel")
async def cancel_job(request: Request, job_id: str):
    """Cancels a PENDING or FAILED job. Cannot cancel RUNNING or SUCCEEDED jobs."""
    _require_service_identity(request)

    job = job_registry.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    try:
        job = job_registry.cancel(job_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return {"job_id": job_id, "status": job.status, "message": "Job cancelled"}


@router.get("/summary")
async def get_jobs_summary(request: Request):
    """Returns queue depth, pending counts per job type, and overall status distribution."""
    _require_service_identity(request)
    return job_registry.get_status_summary()


@router.get("/dead-letter")
async def get_dead_letter_jobs(request: Request, limit: int = 50):
    """Returns jobs that have been moved to the dead-letter queue after exhausting retries."""
    _require_service_identity(request)
    jobs = job_registry.get_dead_letter_jobs(limit=limit)
    return {
        "dead_letter_jobs": jobs,
        "total_returned": len(jobs),
    }


@router.post("/recover")
async def trigger_recovery(request: Request):
    """Scans for jobs stuck in RUNNING state beyond threshold and resets them for retry."""
    _require_service_identity(request)
    recovered = job_registry.recover_stuck_jobs(stuck_threshold_seconds=300.0)
    return {
        "recovered_job_ids": recovered,
        "recovered_count": len(recovered),
    }
