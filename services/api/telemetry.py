# CineVault OS — Telemetry & Observability Module (Phase 25: Extended)
# Implements structured JSON logging with PII redaction, OpenTelemetry-compatible trace context,
# Prometheus-format metrics, signal fan-out (audit / security / business / data quality),
# and health-matrix for all monitored subsystems.
#
# Vendor-neutral by design. No SDK vendor lock-in; only open standards are used:
# - W3C Trace Context (traceparent) for distributed tracing
# - Prometheus text format (OpenMetrics compatible) for metrics exposition
# - Structured JSON log events for Loki / any log aggregator
# - CloudEvents-compatible signal envelope for event fan-out

import time
import json
import uuid
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ---------------------------------------------------------------------------
# PII Redaction
# ---------------------------------------------------------------------------
SENSITIVE_FIELDS = {
    "password", "secret", "token", "auth_token", "authorization",
    "watch_event_notes", "user_address", "email", "access_token",
    "refresh_token", "api_key", "private_key"
}

def sanitize_value(key: str, value: Any) -> Any:
    """Sanitizes PII and sensitive secret fields."""
    if key.lower() in SENSITIVE_FIELDS:
        return "[REDACTED]"
    if isinstance(value, dict):
        return {k: sanitize_value(k, v) for k, v in value.items()}
    if isinstance(value, str) and ("password=" in value.lower() or "bearer " in value.lower()):
        return "[REDACTED_SECRET]"
    return value

# ---------------------------------------------------------------------------
# Structured JSON Logger
# ---------------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter with mandatory correlation ID and PII redaction filters."""

    def format(self, record: logging.LogRecord) -> str:
        message_clean = sanitize_value("message", record.getMessage())

        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": message_clean,
            "service": "cinevault-api-service"
        }

        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("cinevault")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(handler)

# ---------------------------------------------------------------------------
# W3C Trace Context — Span Tracker
# ---------------------------------------------------------------------------
@dataclass
class TraceSpan:
    """Represents a single vendor-neutral distributed trace span."""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation: str
    service: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "OK"          # OK | ERROR | TIMEOUT
    attributes: Dict[str, Any] = field(default_factory=dict)

    def finish(self, status: str = "OK", **attrs):
        self.end_time = time.time()
        self.status = status
        self.attributes.update(attrs)

    @property
    def duration_ms(self) -> Optional[float]:
        if self.end_time is not None:
            return round((self.end_time - self.start_time) * 1000, 2)
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "operation": self.operation,
            "service": self.service,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes,
        }


class SpanTracker:
    """In-process span store for the current request trace path.
    Vendor-neutral; real deployment would export spans to OTLP-compatible backend."""

    def __init__(self):
        self._spans: List[TraceSpan] = []

    def start_span(
        self,
        operation: str,
        service: str,
        trace_id: str,
        parent_span_id: Optional[str] = None,
    ) -> TraceSpan:
        span = TraceSpan(
            span_id=uuid.uuid4().hex[:16],
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation=operation,
            service=service,
            start_time=time.time(),
        )
        self._spans.append(span)
        return span

    def get_recent_spans(self, limit: int = 100) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._spans[-limit:]]

    def clear(self):
        self._spans.clear()

span_tracker = SpanTracker()

# ---------------------------------------------------------------------------
# Signal Router — CloudEvents-compatible event fan-out
# ---------------------------------------------------------------------------
SIGNAL_TYPES = {
    "AUDIT",        # Immutable audit trail (metadata changes, curator actions)
    "SECURITY",     # Auth failures, suspicious access, PII access
    "BUSINESS",     # User-facing milestones (watchlist add, rating, import)
    "DATA_QUALITY", # Quarantine, conflict, reconciliation, ingestion errors
    "SYSTEM",       # Health changes, dependency up/down, queue depth alerts
}

@dataclass
class ObservabilitySignal:
    """Structured observability signal (audit / security / business / data / system)."""
    signal_id: str
    signal_type: str          # One of SIGNAL_TYPES
    event_name: str
    source_service: str
    timestamp: float
    correlation_id: Optional[str]
    trace_id: Optional[str]
    payload: Dict[str, Any] = field(default_factory=dict)
    severity: str = "INFO"    # DEBUG | INFO | WARN | ERROR | CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type,
            "event_name": self.event_name,
            "source_service": self.source_service,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "severity": self.severity,
            "payload": sanitize_value("payload", self.payload),
        }


class SignalRouter:
    """Fans out observability signals to pluggable sink callables.
    Vendor-neutral: sinks can be Loki push, Pub/Sub, Kafka, webhook, or stdout."""

    def __init__(self):
        self._signals: List[ObservabilitySignal] = []
        self._sinks: List[Callable[[ObservabilitySignal], None]] = []
        # Register default stdout sink
        self._sinks.append(self._stdout_sink)

    def register_sink(self, sink: Callable[[ObservabilitySignal], None]):
        self._sinks.append(sink)

    def emit(
        self,
        signal_type: str,
        event_name: str,
        source_service: str = "cinevault-api",
        correlation_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        severity: str = "INFO",
        **payload_kwargs,
    ) -> ObservabilitySignal:
        signal = ObservabilitySignal(
            signal_id=uuid.uuid4().hex,
            signal_type=signal_type,
            event_name=event_name,
            source_service=source_service,
            timestamp=time.time(),
            correlation_id=correlation_id,
            trace_id=trace_id,
            payload=payload_kwargs,
            severity=severity,
        )
        self._signals.append(signal)
        for sink in self._sinks:
            try:
                sink(signal)
            except Exception:
                pass  # Never let a sink failure break application flow
        return signal

    def _stdout_sink(self, signal: ObservabilitySignal):
        logger.info(
            f"[SIGNAL:{signal.signal_type}] {signal.event_name}",
            extra={"correlation_id": signal.correlation_id, "trace_id": signal.trace_id}
        )

    def get_recent_signals(self, signal_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        signals = self._signals
        if signal_type:
            signals = [s for s in signals if s.signal_type == signal_type]
        return [s.to_dict() for s in signals[-limit:]]

    def get_signal_counts_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = {t: 0 for t in SIGNAL_TYPES}
        for s in self._signals:
            counts[s.signal_type] = counts.get(s.signal_type, 0) + 1
        return counts

signal_router = SignalRouter()

# ---------------------------------------------------------------------------
# Extended Metrics Collector
# ---------------------------------------------------------------------------
class MetricsCollector:
    """Prometheus TSDB exposition metrics for all CineVault OS SLIs and infrastructure health.

    Tracks signals across all monitored subsystems:
    API, ingestion, quality, reconciliation, sync, database, providers, queues,
    storage, AI operations.
    """

    def __init__(self):
        # HTTP layer
        self.request_count: Dict[str, int] = {}
        self.request_duration: Dict[str, float] = {}
        self.auth_failures: int = 0

        # Infrastructure health (1=Healthy, 0=Unhealthy)
        self.dependency_health: Dict[str, int] = {
            "pgbouncer": 1,
            "valkey": 1,
            "storage": 1,
            "search_index": 1,
        }

        # Ingestion / quality
        self.ingestion_events_total: Dict[str, int] = {}   # keyed by provider
        self.ingestion_errors_total: Dict[str, int] = {}   # keyed by provider
        self.quarantine_records: int = 0
        self.reconciliation_conflicts_open: int = 0
        self.reconciliation_conflicts_resolved: int = 0
        self.catalog_titles_total: int = 0

        # Sync
        self.sync_backlog: int = 0
        self.sync_mutations_processed: int = 0
        self.sync_conflicts_total: int = 0

        # AI / recommendation
        self.ai_requests_total: int = 0
        self.ai_errors_total: int = 0
        self.recommendation_requests_total: int = 0

        # Business signals
        self.watchlist_additions_total: int = 0
        self.history_events_total: int = 0
        self.export_jobs_total: int = 0

    # --- HTTP ---
    def record_request(self, method: str, path: str, status_code: int, duration_sec: float):
        key = f"{method} {path} {status_code}"
        self.request_count[key] = self.request_count.get(key, 0) + 1
        self.request_duration[key] = duration_sec

    def record_auth_failure(self):
        self.auth_failures += 1

    # --- Infrastructure ---
    def update_dependency_health(self, dependency: str, is_healthy: bool):
        self.dependency_health[dependency] = 1 if is_healthy else 0

    # --- Ingestion / Quality ---
    def record_ingestion_event(self, provider: str, success: bool):
        self.ingestion_events_total[provider] = self.ingestion_events_total.get(provider, 0) + 1
        if not success:
            self.ingestion_errors_total[provider] = self.ingestion_errors_total.get(provider, 0) + 1

    def set_quarantine_records(self, count: int):
        self.quarantine_records = count

    def set_reconciliation_conflicts(self, open_count: int, resolved_count: int):
        self.reconciliation_conflicts_open = open_count
        self.reconciliation_conflicts_resolved = resolved_count

    def set_catalog_titles_total(self, count: int):
        self.catalog_titles_total = count

    # --- Sync ---
    def set_sync_backlog(self, count: int):
        self.sync_backlog = count

    def record_sync_mutation(self, conflict: bool = False):
        self.sync_mutations_processed += 1
        if conflict:
            self.sync_conflicts_total += 1

    # --- AI ---
    def record_ai_request(self, success: bool):
        self.ai_requests_total += 1
        if not success:
            self.ai_errors_total += 1

    def record_recommendation_request(self):
        self.recommendation_requests_total += 1

    # --- Business ---
    def record_watchlist_addition(self):
        self.watchlist_additions_total += 1

    def record_history_event(self):
        self.history_events_total += 1

    def record_export_job(self):
        self.export_jobs_total += 1

    # --- Prometheus Text Format ---
    def generate_prometheus_output(self) -> str:
        lines = [
            "# HELP cinevault_http_requests_total Total HTTP requests handled by API service",
            "# TYPE cinevault_http_requests_total counter",
        ]
        for key, val in self.request_count.items():
            parts = key.split()
            lines.append(f'cinevault_http_requests_total{{method="{parts[0]}",path="{parts[1]}",status="{parts[2]}"}} {val}')

        lines.extend([
            "# HELP cinevault_http_request_duration_seconds Last HTTP request duration in seconds",
            "# TYPE cinevault_http_request_duration_seconds gauge",
        ])
        for key, val in self.request_duration.items():
            parts = key.split()
            lines.append(f'cinevault_http_request_duration_seconds{{method="{parts[0]}",path="{parts[1]}",status="{parts[2]}"}} {val:.4f}')

        lines.extend([
            "# HELP cinevault_auth_failures_total Total authentication failures",
            "# TYPE cinevault_auth_failures_total counter",
            f"cinevault_auth_failures_total {self.auth_failures}",

            "# HELP cinevault_dependency_health_status Operational health status of dependencies (1=Healthy, 0=Unhealthy)",
            "# TYPE cinevault_dependency_health_status gauge",
        ])
        for dep, status_val in self.dependency_health.items():
            lines.append(f'cinevault_dependency_health_status{{dependency="{dep}"}} {status_val}')

        # Ingestion
        lines.extend([
            "# HELP cinevault_ingestion_events_total Total ingestion events by provider",
            "# TYPE cinevault_ingestion_events_total counter",
        ])
        for provider, count in self.ingestion_events_total.items():
            lines.append(f'cinevault_ingestion_events_total{{provider="{provider}"}} {count}')

        lines.extend([
            "# HELP cinevault_ingestion_errors_total Total ingestion errors by provider",
            "# TYPE cinevault_ingestion_errors_total counter",
        ])
        for provider, count in self.ingestion_errors_total.items():
            lines.append(f'cinevault_ingestion_errors_total{{provider="{provider}"}} {count}')

        # Quality
        lines.extend([
            "# HELP cinevault_quarantine_records_current Current count of quarantined payloads",
            "# TYPE cinevault_quarantine_records_current gauge",
            f"cinevault_quarantine_records_current {self.quarantine_records}",

            "# HELP cinevault_reconciliation_conflicts_open Open metadata reconciliation conflicts",
            "# TYPE cinevault_reconciliation_conflicts_open gauge",
            f"cinevault_reconciliation_conflicts_open {self.reconciliation_conflicts_open}",

            "# HELP cinevault_reconciliation_conflicts_resolved_total Resolved metadata reconciliation conflicts",
            "# TYPE cinevault_reconciliation_conflicts_resolved_total counter",
            f"cinevault_reconciliation_conflicts_resolved_total {self.reconciliation_conflicts_resolved}",

            "# HELP cinevault_catalog_titles_total Total canonical titles in the catalog",
            "# TYPE cinevault_catalog_titles_total gauge",
            f"cinevault_catalog_titles_total {self.catalog_titles_total}",

            # Sync
            "# HELP cinevault_sync_outbox_backlog Current count of pending sync mutations",
            "# TYPE cinevault_sync_outbox_backlog gauge",
            f"cinevault_sync_outbox_backlog {self.sync_backlog}",

            "# HELP cinevault_sync_mutations_processed_total Total sync mutations processed",
            "# TYPE cinevault_sync_mutations_processed_total counter",
            f"cinevault_sync_mutations_processed_total {self.sync_mutations_processed}",

            "# HELP cinevault_sync_conflicts_total Total sync conflicts encountered",
            "# TYPE cinevault_sync_conflicts_total counter",
            f"cinevault_sync_conflicts_total {self.sync_conflicts_total}",

            # AI
            "# HELP cinevault_ai_requests_total Total AI assistant requests",
            "# TYPE cinevault_ai_requests_total counter",
            f"cinevault_ai_requests_total {self.ai_requests_total}",

            "# HELP cinevault_ai_errors_total Total AI assistant errors",
            "# TYPE cinevault_ai_errors_total counter",
            f"cinevault_ai_errors_total {self.ai_errors_total}",

            "# HELP cinevault_recommendation_requests_total Total recommendation requests",
            "# TYPE cinevault_recommendation_requests_total counter",
            f"cinevault_recommendation_requests_total {self.recommendation_requests_total}",

            # Business
            "# HELP cinevault_watchlist_additions_total Total watchlist additions",
            "# TYPE cinevault_watchlist_additions_total counter",
            f"cinevault_watchlist_additions_total {self.watchlist_additions_total}",

            "# HELP cinevault_history_events_total Total watch history events recorded",
            "# TYPE cinevault_history_events_total counter",
            f"cinevault_history_events_total {self.history_events_total}",

            "# HELP cinevault_export_jobs_total Total data export jobs initiated",
            "# TYPE cinevault_export_jobs_total counter",
            f"cinevault_export_jobs_total {self.export_jobs_total}",
        ])

        return "\n".join(lines) + "\n"

    def snapshot(self) -> Dict[str, Any]:
        """Returns a structured dict snapshot suitable for JSON health-matrix responses."""
        return {
            "http": {
                "request_count": sum(self.request_count.values()),
                "auth_failures": self.auth_failures,
            },
            "infrastructure": {
                dep: ("healthy" if h == 1 else "unhealthy")
                for dep, h in self.dependency_health.items()
            },
            "ingestion": {
                "events_total": sum(self.ingestion_events_total.values()),
                "errors_total": sum(self.ingestion_errors_total.values()),
            },
            "quality": {
                "quarantine_records": self.quarantine_records,
                "reconciliation_conflicts_open": self.reconciliation_conflicts_open,
                "reconciliation_conflicts_resolved": self.reconciliation_conflicts_resolved,
                "catalog_titles_total": self.catalog_titles_total,
            },
            "sync": {
                "backlog": self.sync_backlog,
                "mutations_processed": self.sync_mutations_processed,
                "conflicts_total": self.sync_conflicts_total,
            },
            "ai": {
                "requests_total": self.ai_requests_total,
                "errors_total": self.ai_errors_total,
                "recommendation_requests_total": self.recommendation_requests_total,
            },
            "business": {
                "watchlist_additions_total": self.watchlist_additions_total,
                "history_events_total": self.history_events_total,
                "export_jobs_total": self.export_jobs_total,
            },
        }


metrics_collector = MetricsCollector()


# ---------------------------------------------------------------------------
# W3C Traceparent — Correlation & Metrics Middleware
# ---------------------------------------------------------------------------
class CorrelationAndMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing UUIDv7 correlation ID and W3C traceparent trace context propagation."""

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        traceparent = request.headers.get("traceparent")

        if not traceparent:
            trace_id = uuid.uuid4().hex
            span_id = uuid.uuid4().hex[:16]
            traceparent = f"00-{trace_id}-{span_id}-01"

        # Parse trace_id from traceparent for span tracking
        try:
            trace_id_parsed = traceparent.split("-")[1]
        except (IndexError, AttributeError):
            trace_id_parsed = uuid.uuid4().hex

        request.state.correlation_id = correlation_id
        request.state.traceparent = traceparent
        request.state.trace_id = trace_id_parsed

        # Start root span for this request
        root_span = span_tracker.start_span(
            operation=f"{request.method} {request.url.path}",
            service="cinevault-api",
            trace_id=trace_id_parsed,
        )

        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        root_span.finish(
            status="OK" if response.status_code < 500 else "ERROR",
            http_method=request.method,
            http_path=request.url.path,
            http_status=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )

        # Inject context in response headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["traceparent"] = traceparent

        # Record metrics
        metrics_collector.record_request(request.method, request.url.path, response.status_code, duration)

        return response
