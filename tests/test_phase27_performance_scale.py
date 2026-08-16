# CineVault OS — Phase 27 Performance / Scale Tests
# Verifies latency histogram percentile tracking, cache-aside metrics,
# slow-query detection, query budget enforcement, benchmark reporter,
# and all 4 performance API endpoints.

import time
import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from services.api.performance import (
    LatencyHistogram,
    CacheAsideMetrics,
    SlowQueryDetector,
    QueryBudget,
    QueryBudgetExceededError,
    PerformanceBenchmarkReporter,
    latency_histogram,
    cache_metrics,
    slow_query_detector,
    benchmark_reporter,
)

client = TestClient(app)
SERVICE_IDENTITY = "cinevault-internal-ops"


class TestPhase27PerformanceScale:
    """Phase 27 — Performance / Scale: benchmarking, caching, slow-query detection, query budget."""

    # ------------------------------------------------------------------
    # 1. Latency Histogram
    # ------------------------------------------------------------------
    def test_histogram_records_samples(self):
        """Latency samples are recorded and counted."""
        h = LatencyHistogram()
        h.record("catalog_search", 45.2)
        h.record("catalog_search", 55.8)
        h.record("catalog_search", 120.0)
        summary = h.summary("catalog_search")
        assert summary["count"] == 3
        assert summary["min_ms"] == 45.2
        assert summary["max_ms"] == 120.0

    def test_histogram_p50_calculation(self):
        """P50 percentile is the median of recorded samples."""
        h = LatencyHistogram()
        for v in [10, 20, 30, 40, 50]:
            h.record("title_lookup", float(v))
        p50 = h.percentile("title_lookup", 50)
        assert p50 == 30.0  # median of [10,20,30,40,50]

    def test_histogram_p95_calculation(self):
        """P95 percentile returns 95th-percentile latency."""
        h = LatencyHistogram()
        for v in range(1, 101):  # 1..100ms
            h.record("analytics_query", float(v))
        p95 = h.percentile("analytics_query", 95)
        assert p95 >= 95.0

    def test_histogram_p99_calculation(self):
        """P99 percentile returns 99th-percentile latency."""
        h = LatencyHistogram()
        for v in range(1, 101):
            h.record("recommendation_query", float(v))
        p99 = h.percentile("recommendation_query", 99)
        assert p99 >= 99.0

    def test_histogram_returns_none_for_no_samples(self):
        """Percentile returns None if no samples exist for the operation."""
        h = LatencyHistogram()
        assert h.percentile("unknown_op", 50) is None

    def test_histogram_all_summaries(self):
        """all_summaries() returns list of per-operation summaries."""
        h = LatencyHistogram()
        h.record("op_a", 10.0)
        h.record("op_b", 20.0)
        summaries = h.all_summaries()
        ops = [s["operation"] for s in summaries]
        assert "op_a" in ops
        assert "op_b" in ops

    def test_histogram_ring_buffer_eviction(self):
        """Ring buffer evicts oldest sample when MAX_SAMPLES is reached."""
        h = LatencyHistogram()
        h.MAX_SAMPLES = 5  # Override for test
        for i in range(7):
            h.record("ring_test", float(i * 10))
        with h._lock:
            assert len(h._samples["ring_test"]) == 5

    # ------------------------------------------------------------------
    # 2. Cache-Aside Metrics
    # ------------------------------------------------------------------
    def test_cache_metrics_record_hit(self):
        """Cache hit ratio increases with hits."""
        m = CacheAsideMetrics()
        m.record_hit("titles")
        m.record_hit("titles")
        m.record_miss("titles")
        ratio = m.hit_ratio("titles")
        assert ratio == pytest.approx(2 / 3, rel=0.01)

    def test_cache_metrics_record_miss(self):
        """Cache miss is tracked correctly."""
        m = CacheAsideMetrics()
        m.record_miss("search")
        m.record_miss("search")
        ratio = m.hit_ratio("search")
        assert ratio == 0.0

    def test_cache_metrics_none_when_no_data(self):
        """Hit ratio returns None when no data has been recorded."""
        m = CacheAsideMetrics()
        assert m.hit_ratio("empty_namespace") is None

    def test_cache_metrics_summary_structure(self):
        """summary() returns dict with per-namespace hit/miss data."""
        m = CacheAsideMetrics()
        m.record_hit("recommendations")
        m.record_miss("recommendations")
        summary = m.summary()
        assert "recommendations" in summary
        assert "hits" in summary["recommendations"]
        assert "hit_ratio" in summary["recommendations"]

    # ------------------------------------------------------------------
    # 3. Slow Query Detector
    # ------------------------------------------------------------------
    def test_slow_query_detected_above_threshold(self):
        """Operations exceeding threshold are recorded as slow events."""
        detector = SlowQueryDetector()
        detector.THRESHOLDS["test_op"] = 50.0
        detector.check("test_op", 200.0)  # 200ms > 50ms threshold
        events = detector.get_recent_slow_events()
        assert len(events) == 1
        assert events[0]["operation"] == "test_op"
        assert events[0]["duration_ms"] == 200.0

    def test_slow_query_not_detected_below_threshold(self):
        """Operations under threshold are not recorded."""
        detector = SlowQueryDetector()
        detector.THRESHOLDS["fast_op"] = 500.0
        detector.check("fast_op", 100.0)  # 100ms < 500ms threshold
        assert detector.get_slow_event_count() == 0

    def test_slow_query_excess_ms_calculated(self):
        """excess_ms field correctly calculated."""
        detector = SlowQueryDetector()
        detector.THRESHOLDS["search_op"] = 100.0
        detector.check("search_op", 350.0)
        event = detector.get_recent_slow_events()[0]
        assert event["excess_ms"] == pytest.approx(250.0, abs=0.1)

    def test_slow_query_uses_default_threshold(self):
        """Unknown operations use the default threshold."""
        detector = SlowQueryDetector()
        # Default threshold is 500ms
        detector.check("unknown_operation", 600.0)
        assert detector.get_slow_event_count() == 1

    # ------------------------------------------------------------------
    # 4. Query Budget Enforcer
    # ------------------------------------------------------------------
    def test_query_budget_low_cost_passes(self):
        """Low-cost queries pass budget enforcement."""
        cost = QueryBudget.enforce(estimated_rows=1000, join_count=1, has_sort=True)
        assert cost == 2000  # 1000 * 1 * 2

    def test_query_budget_exceeded_raises_error(self):
        """Queries exceeding budget raise QueryBudgetExceededError."""
        with pytest.raises(QueryBudgetExceededError):
            QueryBudget.enforce(estimated_rows=600_000, join_count=2, has_sort=True)
            # cost = 600,000 * 2 * 2 = 2,400,000 > 1,000,000

    def test_query_budget_estimate_cost(self):
        """Cost estimation follows rows * joins * sort_factor formula."""
        cost = QueryBudget.estimate_cost(estimated_rows=1000, join_count=3, has_sort=True)
        assert cost == 1000 * 3 * 2  # = 6000

    def test_query_budget_no_sort_halves_cost(self):
        """Without sort, sort_factor is 1 (no multiplier)."""
        cost_with_sort = QueryBudget.estimate_cost(100, join_count=1, has_sort=True)
        cost_without_sort = QueryBudget.estimate_cost(100, join_count=1, has_sort=False)
        assert cost_with_sort == cost_without_sort * 2

    # ------------------------------------------------------------------
    # 5. Benchmark Reporter
    # ------------------------------------------------------------------
    def test_benchmark_reporter_structure(self):
        """Benchmark report contains all expected sections."""
        report = benchmark_reporter.generate_report()
        assert "latency_histograms" in report
        assert "cache_metrics" in report
        assert "slow_query_events" in report
        assert "query_budget" in report
        assert "benchmark_tiers" in report

    def test_benchmark_reporter_tiers(self):
        """Benchmark tiers are 5K, 10K, 100K, 1M."""
        report = benchmark_reporter.generate_report()
        tiers = report["benchmark_tiers"]["tiers"]
        assert 5_000 in tiers
        assert 100_000 in tiers
        assert 1_000_000 in tiers

    # ------------------------------------------------------------------
    # 6. Performance API Endpoints
    # ------------------------------------------------------------------
    def test_benchmark_report_endpoint(self):
        """GET /internal/v1/performance/benchmark-report returns full report."""
        # Record some data first
        latency_histogram.record("catalog_search", 78.5)
        cache_metrics.record_hit("titles")

        resp = client.get(
            "/internal/v1/performance/benchmark-report",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "latency_histograms" in data
        assert "cache_metrics" in data
        assert "benchmark_tiers" in data

    def test_benchmark_report_requires_service_identity(self):
        """Benchmark report endpoint requires X-Service-Identity."""
        resp = client.get("/internal/v1/performance/benchmark-report")
        assert resp.status_code == 401

    def test_latency_endpoint_returns_stats(self):
        """GET /internal/v1/performance/latency/{operation} returns percentile stats."""
        # Ensure we have samples
        latency_histogram.record("ingestion_batch", 500.0)
        latency_histogram.record("ingestion_batch", 800.0)

        resp = client.get(
            "/internal/v1/performance/latency/ingestion_batch",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["operation"] == "ingestion_batch"
        assert "p50_ms" in data
        assert "p95_ms" in data

    def test_latency_endpoint_not_found_for_unknown_op(self):
        """Unknown operation name returns 404."""
        resp = client.get(
            "/internal/v1/performance/latency/totally_unknown_op_xyz",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 404

    def test_cache_stats_endpoint(self):
        """GET /internal/v1/performance/cache-stats returns cache hit/miss summary."""
        cache_metrics.record_hit("search_results")
        cache_metrics.record_miss("search_results")
        resp = client.get(
            "/internal/v1/performance/cache-stats",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "search_results" in data

    def test_slow_queries_endpoint(self):
        """GET /internal/v1/performance/slow-queries returns slow event list."""
        resp = client.get(
            "/internal/v1/performance/slow-queries",
            headers={"X-Service-Identity": SERVICE_IDENTITY}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "slow_events" in data
        assert "total_slow_event_count" in data
        assert isinstance(data["slow_events"], list)
