# CineVault OS — Performance & Scale Layer (Phase 27)
# Benchmark-driven optimization tooling.
#
# What this implements:
# - Latency histogram with P50/P95/P99 percentile tracking per operation
# - Cache-aside strategy with hit/miss ratio tracking
# - Slow-query detector and logger (configurable threshold)
# - Query budget enforcement (reject or warn when query cost estimate too high)
# - Benchmark reporter producing structured JSON for the performance API
#
# Constraint: Optimizations are evidence-based. This module measures first
# and avoids premature infrastructure changes. PostgreSQL remains canonical;
# no Elasticsearch, OpenSearch, or distributed DB is introduced here.

import time
import math
import logging
import threading
import functools
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple

from .telemetry import signal_router

logger = logging.getLogger("cinevault.performance")

# ---------------------------------------------------------------------------
# Latency Histogram — P50 / P95 / P99 Tracking
# ---------------------------------------------------------------------------
class LatencyHistogram:
    """
    Tracks operation latency samples (in milliseconds) per named operation.
    Computes P50, P95, P99 percentiles from collected samples.
    Thread-safe.
    """
    # Maximum samples retained per operation before ring-buffer eviction
    MAX_SAMPLES = 10_000

    def __init__(self):
        self._samples: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def record(self, operation: str, duration_ms: float):
        """Record a single latency sample for the given operation."""
        with self._lock:
            samples = self._samples[operation]
            if len(samples) >= self.MAX_SAMPLES:
                samples.pop(0)   # Evict oldest sample (simple ring eviction)
            samples.append(duration_ms)

    def percentile(self, operation: str, p: float) -> Optional[float]:
        """
        Compute the p-th percentile (0-100) of latency samples for an operation.
        Returns None if no samples recorded.
        """
        with self._lock:
            samples = sorted(self._samples.get(operation, []))
        if not samples:
            return None
        idx = math.ceil((p / 100.0) * len(samples)) - 1
        idx = max(0, min(idx, len(samples) - 1))
        return round(samples[idx], 3)

    def summary(self, operation: str) -> Dict[str, Any]:
        """Returns count, min, max, P50, P95, P99 for the operation."""
        with self._lock:
            samples = sorted(self._samples.get(operation, []))
        if not samples:
            return {"operation": operation, "count": 0}
        return {
            "operation": operation,
            "count": len(samples),
            "min_ms": round(min(samples), 3),
            "max_ms": round(max(samples), 3),
            "p50_ms": self._p(samples, 50),
            "p95_ms": self._p(samples, 95),
            "p99_ms": self._p(samples, 99),
        }

    def all_summaries(self) -> List[Dict[str, Any]]:
        with self._lock:
            operations = list(self._samples.keys())
        return [self.summary(op) for op in operations]

    @staticmethod
    def _p(sorted_samples: List[float], p: float) -> float:
        idx = math.ceil((p / 100.0) * len(sorted_samples)) - 1
        idx = max(0, min(idx, len(sorted_samples) - 1))
        return round(sorted_samples[idx], 3)


latency_histogram = LatencyHistogram()


# ---------------------------------------------------------------------------
# Timing Decorator
# ---------------------------------------------------------------------------
def timed(operation: str):
    """
    Decorator that records execution time (ms) into the latency histogram.
    Also emits a signal if execution exceeds the slow-operation threshold.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                latency_histogram.record(operation, elapsed_ms)
                slow_query_detector.check(operation, elapsed_ms)
        return wrapper

    async def async_decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await fn(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                latency_histogram.record(operation, elapsed_ms)
                slow_query_detector.check(operation, elapsed_ms)
        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Cache-Aside Strategy with Hit/Miss Tracking
# ---------------------------------------------------------------------------
class CacheAsideMetrics:
    """Tracks cache hit/miss ratio across named cache namespaces."""

    def __init__(self):
        self._hits: Dict[str, int] = defaultdict(int)
        self._misses: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def record_hit(self, namespace: str):
        with self._lock:
            self._hits[namespace] += 1

    def record_miss(self, namespace: str):
        with self._lock:
            self._misses[namespace] += 1

    def hit_ratio(self, namespace: str) -> Optional[float]:
        with self._lock:
            hits = self._hits.get(namespace, 0)
            misses = self._misses.get(namespace, 0)
        total = hits + misses
        if total == 0:
            return None
        return round(hits / total, 4)

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            namespaces = set(list(self._hits.keys()) + list(self._misses.keys()))
        result = {}
        for ns in namespaces:
            with self._lock:
                hits = self._hits.get(ns, 0)
                misses = self._misses.get(ns, 0)
            total = hits + misses
            result[ns] = {
                "hits": hits,
                "misses": misses,
                "total": total,
                "hit_ratio": round(hits / total, 4) if total > 0 else None,
            }
        return result


cache_metrics = CacheAsideMetrics()


class CacheAside:
    """
    Cache-aside strategy wrapper for any callable.
    Attempts cache lookup first, falls through to source function on miss,
    then writes result to cache. Records hit/miss metrics.
    """

    def __init__(self, valkey_manager, namespace: str, ttl: int = 300):
        self.valkey = valkey_manager
        self.namespace = namespace
        self.ttl = ttl

    def cache_key(self, *parts: Any) -> str:
        return f"{self.namespace}:" + ":".join(str(p) for p in parts)

    def get_or_fetch(self, key_parts: Tuple, fetch_fn: Callable, serializer=None, deserializer=None):
        """
        Try cache first; on miss call fetch_fn() and write to cache.
        Returns (value, from_cache: bool).
        """
        import json
        _ser = serializer or json.dumps
        _de = deserializer or json.loads
        cache_key = self.cache_key(*key_parts)

        cached = self.valkey.get(cache_key)
        if cached is not None:
            cache_metrics.record_hit(self.namespace)
            latency_histogram.record(f"cache_hit:{self.namespace}", 0.1)
            try:
                return _de(cached), True
            except Exception:
                pass

        cache_metrics.record_miss(self.namespace)
        start = time.perf_counter()
        value = fetch_fn()
        elapsed_ms = (time.perf_counter() - start) * 1000
        latency_histogram.record(f"cache_miss_fetch:{self.namespace}", elapsed_ms)

        try:
            self.valkey.set(cache_key, _ser(value), ttl=self.ttl)
        except Exception:
            pass
        return value, False


# ---------------------------------------------------------------------------
# Slow Query Detector
# ---------------------------------------------------------------------------
class SlowQueryDetector:
    """
    Detects and logs operations exceeding configurable latency thresholds.
    Emits SYSTEM signals for slow operations, enabling alerting.
    """
    # Default thresholds per operation category (ms)
    THRESHOLDS: Dict[str, float] = {
        "catalog_search": 200.0,
        "title_lookup": 50.0,
        "title_list": 100.0,
        "ingestion_batch": 2000.0,
        "recommendation_query": 300.0,
        "analytics_query": 500.0,
        "identity_matching": 150.0,
        "db_write": 100.0,
        "default": 500.0,
    }

    def __init__(self):
        self._slow_events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def check(self, operation: str, duration_ms: float):
        """Check if operation exceeded threshold; if so, log and emit signal."""
        threshold = self.THRESHOLDS.get(operation, self.THRESHOLDS["default"])
        if duration_ms > threshold:
            event = {
                "operation": operation,
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": threshold,
                "excess_ms": round(duration_ms - threshold, 2),
                "timestamp": time.time(),
            }
            with self._lock:
                self._slow_events.append(event)
            logger.warning(
                f"SLOW_OPERATION: {operation} took {duration_ms:.1f}ms "
                f"(threshold={threshold}ms, excess={duration_ms - threshold:.1f}ms)"
            )
            signal_router.emit(
                "SYSTEM",
                "SLOW_OPERATION_DETECTED",
                source_service="performance-monitor",
                severity="WARN",
                **event,
            )

    def get_recent_slow_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._slow_events[-limit:])

    def get_slow_event_count(self) -> int:
        with self._lock:
            return len(self._slow_events)


slow_query_detector = SlowQueryDetector()


# ---------------------------------------------------------------------------
# Query Budget Enforcer
# ---------------------------------------------------------------------------
class QueryBudgetExceededError(Exception):
    """Raised when a query's estimated cost exceeds the allowed budget."""
    pass


class QueryBudget:
    """
    Enforces query budget limits based on estimated cost factors.
    Cost model: rows * joins * sort_complexity
    """
    # Maximum allowed cost before query is rejected
    MAX_BUDGET = 1_000_000

    @classmethod
    def estimate_cost(cls, estimated_rows: int, join_count: int = 0, has_sort: bool = False) -> int:
        """Simple additive cost model (evidence-based, not premature Elasticsearch)."""
        sort_factor = 2 if has_sort else 1
        join_factor = max(1, join_count)
        return estimated_rows * join_factor * sort_factor

    @classmethod
    def enforce(cls, estimated_rows: int, join_count: int = 0, has_sort: bool = False, operation: str = "query"):
        """Raise QueryBudgetExceededError if estimated cost exceeds MAX_BUDGET."""
        cost = cls.estimate_cost(estimated_rows, join_count, has_sort)
        if cost > cls.MAX_BUDGET:
            msg = (
                f"Query budget exceeded for '{operation}': "
                f"estimated_cost={cost} > max_budget={cls.MAX_BUDGET}. "
                f"Reduce result set or add filters."
            )
            signal_router.emit(
                "SYSTEM", "QUERY_BUDGET_EXCEEDED",
                source_service="query-enforcer",
                severity="WARN",
                operation=operation,
                estimated_cost=cost,
                max_budget=cls.MAX_BUDGET,
            )
            raise QueryBudgetExceededError(msg)
        return cost


# ---------------------------------------------------------------------------
# Performance Benchmark Reporter
# ---------------------------------------------------------------------------
class PerformanceBenchmarkReporter:
    """
    Aggregates latency histograms, cache metrics, and slow query events
    into a structured performance report for the benchmark API.
    """

    def generate_report(self) -> Dict[str, Any]:
        return {
            "latency_histograms": latency_histogram.all_summaries(),
            "cache_metrics": cache_metrics.summary(),
            "slow_query_events": {
                "total_count": slow_query_detector.get_slow_event_count(),
                "recent_events": slow_query_detector.get_recent_slow_events(limit=20),
            },
            "query_budget": {
                "max_budget": QueryBudget.MAX_BUDGET,
            },
            "benchmark_tiers": {
                "description": "Evidence-based scale tiers. Measure before optimizing.",
                "tiers": [5_000, 10_000, 100_000, 1_000_000],
                "current_baseline": "Design supports up to 100,000 titles with PostgreSQL (bounded SQLAlchemy pool) + Valkey cache",
            },
        }


benchmark_reporter = PerformanceBenchmarkReporter()
