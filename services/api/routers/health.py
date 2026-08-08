# CineVault OS — Operational Health Probes Router
# Implements /health/liveness and /health/readiness probes across PgBouncer, Valkey, and RabbitMQ

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from ..database import db_manager
from ..valkey import valkey_manager
from ..rabbitmq import rabbitmq_manager

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/liveness", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Liveness probe: verifies the API process is alive."""
    return {
        "status": "UP",
        "service": "CineVault OS API",
        "timestamp": "2026-08-08T18:36:00Z"
    }

@router.get("/readiness")
async def readiness_probe():
    """Readiness probe: verifies operational dependencies (PgBouncer, Valkey, RabbitMQ)."""
    db_health = db_manager.check_health()
    valkey_health = valkey_manager.check_health()
    rabbitmq_health = rabbitmq_manager.check_health()
    
    is_ready = (
        db_health.get("status") == "HEALTHY" and
        valkey_health.get("status") == "HEALTHY" and
        rabbitmq_health.get("status") == "HEALTHY"
    )
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    
    payload = {
        "status": "READY" if is_ready else "NOT_READY",
        "dependencies": {
            "pgbouncer": db_health,
            "valkey": valkey_health,
            "rabbitmq": rabbitmq_health
        }
    }
    return JSONResponse(status_code=status_code, content=payload)
