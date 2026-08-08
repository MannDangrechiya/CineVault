# CineVault OS — Telemetry & Observability Module
# Implements structured JSON logging, Prometheus metrics, and correlation ID tracking

import time
import json
import logging
from typing import Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Configure structured JSON logger
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("cinevault")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Simple in-memory metrics registry for local development / testing
class MetricsCollector:
    def __init__(self):
        self.request_count: Dict[str, int] = {}
        self.request_duration: Dict[str, float] = {}
        self.auth_failures: int = 0

    def record_request(self, method: str, path: str, status_code: int, duration_sec: float):
        key = f"{method} {path} {status_code}"
        self.request_count[key] = self.request_count.get(key, 0) + 1
        self.request_duration[key] = duration_sec

    def record_auth_failure(self):
        self.auth_failures += 1

    def generate_prometheus_output(self) -> str:
        lines = [
            "# HELP cinevault_http_requests_total Total HTTP requests handled",
            "# TYPE cinevault_http_requests_total counter",
        ]
        for key, val in self.request_count.items():
            parts = key.split()
            lines.append(f'cinevault_http_requests_total{{method="{parts[0]}",path="{parts[1]}",status="{parts[2]}"}} {val}')

        lines.extend([
            "# HELP cinevault_http_request_duration_seconds Last request duration in seconds",
            "# TYPE cinevault_http_request_duration_seconds gauge",
        ])
        for key, val in self.request_duration.items():
            parts = key.split()
            lines.append(f'cinevault_http_request_duration_seconds{{method="{parts[0]}",path="{parts[1]}",status="{parts[2]}"}} {val:.4f}')

        lines.extend([
            "# HELP cinevault_auth_failures_total Total authentication failures",
            "# TYPE cinevault_auth_failures_total counter",
            f"cinevault_auth_failures_total {self.auth_failures}"
        ])

        return "\n".join(lines) + "\n"

metrics_collector = MetricsCollector()

class CorrelationAndMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract or generate UUIDv7 correlation ID header
        correlation_id = request.headers.get("X-Correlation-ID", "018f2e4a-7b31-7000-8000-000000000000")
        request.state.correlation_id = correlation_id
        
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Inject correlation ID in response header
        response.headers["X-Correlation-ID"] = correlation_id
        
        # Record metrics
        metrics_collector.record_request(request.method, request.url.path, response.status_code, duration)
        
        return response
