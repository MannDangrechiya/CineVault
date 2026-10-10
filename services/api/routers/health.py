# CineVault OS — Operational Health Probes Router
# Implements /health/liveness, /health/readiness, and /health/startup probes.
# W13: Fixed hardcoded timestamp, added real DB query check, sanitized response,
#      added startup probe.

from datetime import datetime, timezone
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from ..database import db_manager, async_check_db_health
from ..valkey import valkey_manager

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/liveness", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Liveness probe: verifies the API process is alive."""
    return {
        "status": "UP",
        "service": "CineVault OS API",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/readiness")
async def readiness_probe():
    """Readiness probe: verifies operational dependencies are available.
    Returns sanitized status without exposing internal topology."""
    db_health = db_manager.check_health()
    valkey_health = valkey_manager.check_health()

    # Also run a real SQL query to verify end-to-end DB connectivity
    db_query_ok = await async_check_db_health()

    is_ready = (
        db_health.get("status") == "HEALTHY" and
        db_query_ok and
        valkey_health.get("status") == "HEALTHY"
    )
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    # Sanitized response: expose only status, not internal addresses or topology
    payload = {
        "status": "READY" if is_ready else "NOT_READY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "database": "ok" if (db_health.get("status") == "HEALTHY" and db_query_ok) else "degraded",
            "cache": "ok" if valkey_health.get("status") == "HEALTHY" else "degraded",
        }
    }
    return JSONResponse(status_code=status_code, content=payload)

@router.get("/startup", status_code=status.HTTP_200_OK)
async def startup_probe():
    """Startup probe: verifies the application has completed initialization.
    Used by container orchestrators to determine when to begin liveness checks."""
    db_health = db_manager.check_health()
    db_query_ok = await async_check_db_health()

    is_started = db_health.get("status") == "HEALTHY" and db_query_ok
    status_code = status.HTTP_200_OK if is_started else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "STARTED" if is_started else "STARTING",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
