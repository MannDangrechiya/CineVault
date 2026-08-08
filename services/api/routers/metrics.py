# CineVault OS — Prometheus Metrics Router
# Exposes /metrics for OpenTelemetry / Prometheus scraper collection

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from ..telemetry import metrics_collector

router = APIRouter(tags=["Metrics"])

@router.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    """Returns Prometheus TSDB format metrics."""
    return metrics_collector.generate_prometheus_output()
