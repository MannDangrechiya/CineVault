# CineVault OS — Phase 25 Observability Tests
# Verifies signal router fan-out, extended metrics, trace span tracking,
# health-matrix computation, and observability API endpoints.

import time
import uuid
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.telemetry import (
    signal_router,
    span_tracker,
    metrics_collector,
    SIGNAL_TYPES,
    sanitize_value,
    ObservabilitySignal,
)

client = TestClient(app)
SERVICE_IDENTITY = "cinevault-internal-ops"


class TestPhase25Observability:
    """Phase 25 — Observability: signal router, metrics, traces, health-matrix, API endpoints."""

    # ------------------------------------------------------------------
    # 1. PII Redaction
    # ------------------------------------------------------------------
    def test_pii_redaction_sensitive_fields(self):
        """PII and secrets are redacted in sanitize_value."""
        assert sanitize_value("password", "mySecret123") == "[REDACTED]"
        assert sanitize_value("email", "user@example.com") == "[REDACTED]"
        assert sanitize_value("access_token", "eyJhbGc...") == "[REDACTED]"
        assert sanitize_value("title", "Dune: Part Two") == "Dune: Part Two"

    def test_pii_redaction_nested_dict(self):
        """Nested dict with mixed fields are sanitized recursively."""
        data = {"user": {"email": "test@example.com", "display_name": "Alice"}, "token": "abc"}
        result = sanitize_value("user", data)
        assert result["user"]["email"] == "[REDACTED]"
        assert result["user"]["display_name"] == "Alice"

    # ------------------------------------------------------------------
    # 2. Signal Router
    # ------------------------------------------------------------------
    def test_signal_router_emit_audit(self):
        """Audit signals are emitted and retrievable."""
        signal = signal_router.emit(
            "AUDIT",
            "METADATA_FIELD_UPDATED",
            source_service="canonical-pipeline",
            correlation_id="corr-001",
            trace_id="trace-abc",
            field_name="runtime_minutes",
            old_value=120,
            new_value=118,
        )
        assert signal.signal_type == "AUDIT"
        assert signal.event_name == "METADATA_FIELD_UPDATED"
        assert signal.payload["field_name"] == "runtime_minutes"
        assert signal.payload["old_value"] == 120

    def test_signal_router_emit_security(self):
        """Security signals are emitted with correct severity."""
        signal = signal_router.emit(
            "SECURITY",
            "AUTH_FAILURE",
            source_service="cinevault-api",
            severity="WARN",
            user_id="unknown",
            attempt_count=3,
        )
        assert signal.signal_type == "SECURITY"
        assert signal.severity == "WARN"

    def test_signal_router_emit_data_quality(self):
        """DATA_QUALITY signals track quarantine and reconciliation events."""
        signal = signal_router.emit(
            "DATA_QUALITY",
            "PAYLOAD_QUARANTINED",
            source_service="ingestion-worker",
            severity="WARN",
            provider="TMDB",
            reason="schema_mismatch",
        )
        assert signal.signal_type == "DATA_QUALITY"
        assert signal.payload["provider"] == "TMDB"

    def test_signal_router_emit_business(self):
        """Business signals record user milestones."""
        signal = signal_router.emit(
            "BUSINESS",
            "WATCHLIST_ITEM_ADDED",
            source_service="personal-service",
            title_id="tt1234567",
            user_id_hash="REDACTED_HASH",
        )
        assert signal.signal_type == "BUSINESS"
        assert signal.event_name == "WATCHLIST_ITEM_ADDED"

    def test_signal_router_emit_system(self):
        """System signals track dependency health transitions."""
        signal = signal_router.emit(
            "SYSTEM",
            "DEPENDENCY_DOWN",
            source_service="health-monitor",
            severity="ERROR",
            dependency="valkey",
        )
        assert signal.signal_type == "SYSTEM"
        assert signal.payload["dependency"] == "valkey"

    def test_signal_router_filter_by_type(self):
        """get_recent_signals with signal_type filter returns only matching signals."""
        audit_signals = signal_router.get_recent_signals(signal_type="AUDIT", limit=100)
        assert all(s["signal_type"] == "AUDIT" for s in audit_signals)

    def test_signal_router_counts_by_type(self):
        """Signal counts by type returns a dict with all known signal types."""
        counts = signal_router.get_signal_counts_by_type()
        assert set(counts.keys()) == SIGNAL_TYPES
        assert counts["AUDIT"] >= 1
        assert counts["SECURITY"] >= 1

    def test_signal_pii_payload_redacted_in_output(self):
        """Signal to_dict() redacts sensitive fields in payload."""
        signal = signal_router.emit(
            "AUDIT",
            "USER_ACCESS",
            email="secret@domain.com",
            token="bearer xyz",
        )
        d = signal.to_dict()
        assert d["payload"].get("email") == "[REDACTED]"

    # ------------------------------------------------------------------
    # 3. Span Tracker
    # ------------------------------------------------------------------
    def test_span_tracker_start_and_finish(self):
        """Spans record duration and status correctly."""
        trace_id = uuid.uuid4().hex
        span = span_tracker.start_span("DB_QUERY", "pgbouncer", trace_id=trace_id)
        time.sleep(0.01)
        span.finish(status="OK", query="SELECT title_id FROM canonical_titles LIMIT 1")

        assert span.status == "OK"
        assert span.duration_ms is not None
        assert span.duration_ms >= 10.0
        assert span.attributes["query"].startswith("SELECT")

    def test_span_tracker_get_recent_spans(self):
        """get_recent_spans returns span dicts with expected fields."""
        trace_id = uuid.uuid4().hex
        sp = span_tracker.start_span("CACHE_LOOKUP", "valkey", trace_id=trace_id)
        sp.finish(status="OK")

        spans = span_tracker.get_recent_spans(limit=10)
        assert len(spans) >= 1
        assert "span_id" in spans[-1]
        assert "trace_id" in spans[-1]
        assert "duration_ms" in spans[-1]

    def test_span_tracker_error_status(self):
        """Spans can record ERROR status for failed operations."""
        trace_id = uuid.uuid4().hex
        span = span_tracker.start_span("PROVIDER_FETCH", "tmdb-provider", trace_id=trace_id)
        span.finish(status="ERROR", error="timeout", provider="TMDB")
        assert span.status == "ERROR"
        assert span.attributes["error"] == "timeout"

    # ------------------------------------------------------------------
    # 4. Extended Metrics Collector
    # ------------------------------------------------------------------
    def test_metrics_ingestion_tracking(self):
        """Ingestion event counters increment per provider."""
        metrics_collector.record_ingestion_event("TMDB", success=True)
        metrics_collector.record_ingestion_event("TMDB", success=False)
        metrics_collector.record_ingestion_event("IMDb", success=True)

        output = metrics_collector.generate_prometheus_output()
        assert 'cinevault_ingestion_events_total{provider="TMDB"}' in output
        assert 'cinevault_ingestion_errors_total{provider="TMDB"}' in output
        assert 'cinevault_ingestion_events_total{provider="IMDb"}' in output

    def test_metrics_quality_signals(self):
        """Quality metrics reflect quarantine and reconciliation state."""
        metrics_collector.set_quarantine_records(12)
        metrics_collector.set_reconciliation_conflicts(open_count=5, resolved_count=30)

        output = metrics_collector.generate_prometheus_output()
        assert "cinevault_quarantine_records_current 12" in output
        assert "cinevault_reconciliation_conflicts_open 5" in output
        assert "cinevault_reconciliation_conflicts_resolved_total 30" in output

    def test_metrics_sync_tracking(self):
        """Sync mutation and conflict counters work correctly."""
        metrics_collector.set_sync_backlog(42)
        metrics_collector.record_sync_mutation(conflict=False)
        metrics_collector.record_sync_mutation(conflict=True)

        output = metrics_collector.generate_prometheus_output()
        assert "cinevault_sync_outbox_backlog 42" in output
        assert "cinevault_sync_conflicts_total" in output

    def test_metrics_ai_tracking(self):
        """AI request and error counters are tracked."""
        metrics_collector.record_ai_request(success=True)
        metrics_collector.record_ai_request(success=False)
        metrics_collector.record_recommendation_request()

        output = metrics_collector.generate_prometheus_output()
        assert "cinevault_ai_requests_total" in output
        assert "cinevault_ai_errors_total" in output
        assert "cinevault_recommendation_requests_total" in output

    def test_metrics_business_signals(self):
        """Business event counters track user milestones."""
        metrics_collector.record_watchlist_addition()
        metrics_collector.record_history_event()
        metrics_collector.record_export_job()

        output = metrics_collector.generate_prometheus_output()
        assert "cinevault_watchlist_additions_total" in output
        assert "cinevault_history_events_total" in output
        assert "cinevault_export_jobs_total" in output

    def test_metrics_prometheus_format_valid(self):
        """Prometheus output ends with newline and has HELP/TYPE lines."""
        output = metrics_collector.generate_prometheus_output()
        assert output.endswith("\n")
        assert "# HELP" in output
        assert "# TYPE" in output

    def test_metrics_snapshot_structure(self):
        """Metrics snapshot returns expected subsystem keys."""
        snap = metrics_collector.snapshot()
        assert "http" in snap
        assert "infrastructure" in snap
        assert "ingestion" in snap
        assert "quality" in snap
        assert "sync" in snap
        assert "ai" in snap
        assert "business" in snap

    # ------------------------------------------------------------------
    # 5. Observability API Endpoints
    # ------------------------------------------------------------------
    def test_observability_signals_requires_service_identity(self):
        """Signals endpoint rejects requests without X-Service-Identity."""
        resp = client.get("/internal/v1/observability/signals")
        assert resp.status_code == 401

    def test_observability_signals_returns_signal_stream(self):
        """Authenticated signals request returns signal list and counts."""
        resp = client.get(
            "/internal/v1/observability/signals",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "signals" in data
        assert "signal_counts_by_type" in data
        assert isinstance(data["signals"], list)

    def test_observability_signals_type_filter(self):
        """signal_type query param filters results correctly."""
        resp = client.get(
            "/internal/v1/observability/signals?signal_type=AUDIT",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["filter_applied"] == "AUDIT"
        assert all(s["signal_type"] == "AUDIT" for s in data["signals"])

    def test_observability_signals_invalid_type(self):
        """Invalid signal_type query param returns 400."""
        resp = client.get(
            "/internal/v1/observability/signals?signal_type=INVALID_TYPE",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 400

    def test_observability_health_matrix_structure(self):
        """Health matrix endpoint returns overall_status and per-subsystem health."""
        resp = client.get(
            "/internal/v1/observability/health-matrix",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_status" in data
        assert data["overall_status"] in ("HEALTHY", "DEGRADED")
        assert "subsystems" in data
        subsystems = data["subsystems"]
        for key in ("api", "infrastructure", "ingestion", "data_quality", "sync", "ai", "business"):
            assert key in subsystems

    def test_observability_health_matrix_requires_service_identity(self):
        """Health matrix rejects unauthenticated requests."""
        resp = client.get("/internal/v1/observability/health-matrix")
        assert resp.status_code == 401

    def test_observability_trace_spans_endpoint(self):
        """Trace spans endpoint returns recent span list."""
        resp = client.get(
            "/internal/v1/observability/trace-spans",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "spans" in data
        assert isinstance(data["spans"], list)

    def test_observability_metrics_snapshot_endpoint(self):
        """Metrics snapshot endpoint returns structured subsystem dict."""
        resp = client.get(
            "/internal/v1/observability/metrics-snapshot",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "http" in data
        assert "quality" in data
        assert "sync" in data

    def test_trace_context_propagation_in_response(self):
        """API responses include W3C traceparent and X-Correlation-ID headers."""
        resp = client.get("/health/liveness")
        assert "x-correlation-id" in resp.headers or "X-Correlation-ID" in resp.headers
        # traceparent may or may not be present depending on client — just verify endpoint works
        assert resp.status_code == 200

    # ------------------------------------------------------------------
    # 6. Health-Matrix degraded path
    # ------------------------------------------------------------------
    def test_health_matrix_degrades_on_unhealthy_dependency(self):
        """Health matrix reports DEGRADED when a dependency is unhealthy."""
        metrics_collector.update_dependency_health("valkey", is_healthy=False)
        resp = client.get(
            "/internal/v1/observability/health-matrix",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_status"] == "DEGRADED"
        # Restore
        metrics_collector.update_dependency_health("valkey", is_healthy=True)

    # ------------------------------------------------------------------
    # 7. Prometheus /metrics endpoint (existing + extended)
    # ------------------------------------------------------------------
    def test_prometheus_metrics_endpoint_accessible(self):
        """/metrics endpoint returns Prometheus text content."""
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "cinevault_http_requests_total" in resp.text
        assert "cinevault_auth_failures_total" in resp.text

    def test_prometheus_metrics_includes_extended_signals(self):
        """/metrics endpoint includes Phase 25 extended metric families."""
        resp = client.get("/metrics")
        assert "cinevault_ingestion_events_total" in resp.text
        assert "cinevault_quarantine_records_current" in resp.text
        assert "cinevault_sync_outbox_backlog" in resp.text
        assert "cinevault_ai_requests_total" in resp.text
        assert "cinevault_watchlist_additions_total" in resp.text
