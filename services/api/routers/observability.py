# CineVault OS — Observability Internal Router (Phase 25)
# Exposes internal observability endpoints:
#   GET /internal/v1/observability/signals        — recent signal stream (audit/security/business/data)
#   GET /internal/v1/observability/health-matrix  — structured health matrix across all subsystems
#   GET /internal/v1/observability/trace-spans    — recent distributed trace spans
#   GET /internal/v1/observability/metrics-snapshot — JSON snapshot of all metrics dimensions
#
# Vendor-neutral. No infrastructure vendor lock-in.
# Access restricted to internal service identity (X-Service-Identity header).

import time
from typing import Optional
from fastapi import APIRouter, Query, Request, HTTPException

from ..telemetry import signal_router, span_tracker, metrics_collector, SIGNAL_TYPES

router = APIRouter(
    prefix="/internal/v1/observability",
    tags=["Observability"],
)

def _require_service_identity(request: Request):
    """Enforce internal service identity on observability endpoints."""
    identity = request.headers.get("X-Service-Identity", "")
    if not identity:
        raise HTTPException(status_code=401, detail="X-Service-Identity header required for observability endpoints")
    return identity


@router.get("/signals")
async def get_observability_signals(
    request: Request,
    signal_type: Optional[str] = Query(None, description="Filter by signal type: AUDIT | SECURITY | BUSINESS | DATA_QUALITY | SYSTEM"),
    limit: int = Query(50, ge=1, le=500),
):
    """
    Returns recent observability signals fanned-out by the signal router.
    Supports filtering by signal type. Access restricted to internal service identities.
    """
    _require_service_identity(request)

    if signal_type and signal_type not in SIGNAL_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid signal_type. Must be one of: {sorted(SIGNAL_TYPES)}"
        )

    signals = signal_router.get_recent_signals(signal_type=signal_type, limit=limit)
    counts = signal_router.get_signal_counts_by_type()

    return {
        "signals": signals,
        "total_returned": len(signals),
        "signal_counts_by_type": counts,
        "filter_applied": signal_type,
    }


@router.get("/health-matrix")
async def get_health_matrix(request: Request):
    """
    Returns a structured health matrix across all CineVault OS monitored subsystems:
    API, ingestion, quality, reconciliation, sync, database, providers, queues, storage, AI.

    Provides overall system status and per-subsystem health summary.
    Access restricted to internal service identities.
    """
    _require_service_identity(request)

    snapshot = metrics_collector.snapshot()
    infra = snapshot["infrastructure"]

    # Compute overall health: all dependencies healthy → HEALTHY, any down → DEGRADED
    all_healthy = all(v == "healthy" for v in infra.values())
    overall_status = "HEALTHY" if all_healthy else "DEGRADED"

    # Quality signals influence status
    quality = snapshot["quality"]
    if quality["quarantine_records"] > 100 or quality["reconciliation_conflicts_open"] > 50:
        overall_status = "DEGRADED"

    return {
        "overall_status": overall_status,
        "timestamp": time.time(),
        "subsystems": {
            "api": {
                "status": "HEALTHY",
                "metrics": snapshot["http"],
            },
            "infrastructure": {
                "status": overall_status,
                "dependencies": infra,
            },
            "ingestion": {
                "status": "HEALTHY" if snapshot["ingestion"]["errors_total"] == 0 else "DEGRADED",
                "metrics": snapshot["ingestion"],
            },
            "data_quality": {
                "status": "HEALTHY" if quality["reconciliation_conflicts_open"] == 0 and quality["quarantine_records"] == 0 else "ATTENTION",
                "metrics": quality,
            },
            "sync": {
                "status": "HEALTHY" if snapshot["sync"]["backlog"] < 1000 else "DEGRADED",
                "metrics": snapshot["sync"],
            },
            "ai": {
                "status": "HEALTHY" if snapshot["ai"]["errors_total"] == 0 else "DEGRADED",
                "metrics": snapshot["ai"],
            },
            "business": {
                "status": "HEALTHY",
                "metrics": snapshot["business"],
            },
        },
    }


@router.get("/trace-spans")
async def get_trace_spans(
    request: Request,
    limit: int = Query(50, ge=1, le=500),
):
    """
    Returns recent distributed trace spans captured across the API → queue → worker → provider → database path.
    Vendor-neutral W3C traceparent-based tracing. Access restricted to internal service identities.
    """
    _require_service_identity(request)
    spans = span_tracker.get_recent_spans(limit=limit)
    return {
        "spans": spans,
        "total_returned": len(spans),
    }


@router.get("/metrics-snapshot")
async def get_metrics_snapshot(request: Request):
    """
    Returns a structured JSON snapshot of all CineVault OS metrics dimensions.
    Complements the Prometheus text-format /metrics endpoint with structured access.
    Access restricted to internal service identities.
    """
    _require_service_identity(request)
    return metrics_collector.snapshot()
