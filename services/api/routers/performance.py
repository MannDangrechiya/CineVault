# CineVault OS — Performance Internal Router (Phase 27)
# Exposes benchmark and performance measurement endpoints:
#   GET /internal/v1/performance/benchmark-report — full performance report
#   GET /internal/v1/performance/latency/{operation} — per-operation latency stats
#   GET /internal/v1/performance/cache-stats — cache hit/miss ratios
#   GET /internal/v1/performance/slow-queries — recent slow operation events
#
# Access restricted to internal service identity (X-Service-Identity header).

from fastapi import APIRouter, HTTPException, Query, Request

from ..performance import (
    latency_histogram,
    cache_metrics,
    slow_query_detector,
    benchmark_reporter,
    QueryBudget,
)

router = APIRouter(
    prefix="/internal/v1/performance",
    tags=["Performance"],
)


def _require_service_identity(request: Request):
    identity = request.headers.get("X-Service-Identity", "")
    if not identity:
        raise HTTPException(status_code=401, detail="X-Service-Identity header required")
    return identity


@router.get("/benchmark-report")
async def get_benchmark_report(request: Request):
    """
    Returns a comprehensive performance benchmark report including:
    - Latency histograms (P50/P95/P99) per operation
    - Cache hit/miss ratios per namespace
    - Recent slow query events
    - Query budget configuration
    - Evidence-based scale tier targets
    """
    _require_service_identity(request)
    return benchmark_reporter.generate_report()


@router.get("/latency/{operation}")
async def get_latency_stats(request: Request, operation: str):
    """Returns P50/P95/P99 latency stats for a specific named operation."""
    _require_service_identity(request)
    summary = latency_histogram.summary(operation)
    if summary.get("count", 0) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No latency data recorded for operation '{operation}'"
        )
    return summary


@router.get("/cache-stats")
async def get_cache_stats(request: Request):
    """Returns cache hit/miss ratios across all tracked namespaces."""
    _require_service_identity(request)
    return cache_metrics.summary()


@router.get("/slow-queries")
async def get_slow_queries(request: Request, limit: int = Query(50, ge=1, le=500)):
    """Returns recent slow operation events that exceeded their configured thresholds."""
    _require_service_identity(request)
    return {
        "slow_events": slow_query_detector.get_recent_slow_events(limit=limit),
        "total_slow_event_count": slow_query_detector.get_slow_event_count(),
    }
