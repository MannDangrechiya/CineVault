# CineVault OS — Observability & Operations Specification V1

**Document Type:** Master Observability & Operations Specification  
**Status:** Approved & Baseline Locked  
**Date:** 2026-08-08  
**Scope:** Telemetry Pillars (Metrics, Structured JSON Logging, OpenTelemetry Traces, Health Probes), Log Sanitization & PII Privacy Filters, Context Propagation, Prometheus exposition format, and Incident Runbook guidelines.

---

## 1. Purpose & Scope

The purpose of the **Observability & Operations Specification V1** is to detail the technical execution of CineVault OS's vendor-neutral observability platform based on locked decisions `DEC-OBS-PRP-01` through `DEC-OBS-PRP-08`.

This specification details:
1. **Structured JSON Logging Strategy (DEC-OBS-PRP-01):** Standardized JSON logging with `UUIDv7` correlation IDs, service identity, and automated PII/secret redaction filters.
2. **End-to-End OpenTelemetry Distributed Tracing (DEC-OBS-PRP-02):** W3C `traceparent` and `X-Correlation-ID` header context propagation across API nodes and middleware.
3. **Prometheus Metrics & Health Probe Architecture (DEC-OBS-PRP-03):** Prometheus TSDB exposition format at `GET /metrics` and operational health probes at `/health/liveness` and `/health/readiness`.
4. **Ingestion & Provider Operations Monitoring (DEC-OBS-PRP-04):** Ingestion lifecycle transition counters and provider HTTP 429 rate-limit tracking.
5. **Quality, Quarantine & AI Proposal Monitoring (DEC-OBS-PRP-05):** Monitoring `quality.quarantine_record` accumulation (`CAT-6`) and AI proposal review queues.
6. **Database & Infrastructure Telemetry (DEC-OBS-PRP-06):** Dependency health status tracking for PgBouncer, Valkey, and RabbitMQ.
7. **Incident Runbooks & DLQ Protocols (DEC-OBS-PRP-07):** Operational protocols for DB failover, circuit breaker trips, and Dead-Letter Queue (DLQ) triage.
8. **SLO Framework (DEC-OBS-PRP-08):** 99.9% read availability, p95 < 200ms API latency, and < 2000ms sync push latency.

---

## 2. Four Telemetry Pillars Implementation

```text
┌───────────────────────────┬───────────────────────────────┬───────────────────────────────────────────┐
│ Observability Pillar      │ Implementation Component      │ Operational Contract                      │
├───────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 1. Structured JSON Logs   │ `JSONFormatter`               │ JSON stdout emission with timestamp,      │
│                           │ (`services/api/telemetry.py`) │ level, name, service, message, correlation│
│ 2. Distributed Tracing    │ `CorrelationAndMetricsMiddleware`│ W3C `traceparent` and `X-Correlation-ID` │
│                           │ (`services/api/telemetry.py`) │ context propagation across HTTP headers   │
│ 3. Metrics Exposition     │ `MetricsCollector`            │ Prometheus TSDB format at `GET /metrics`  │
│                           │ (`services/api/routers/metrics.py`) with HELP and TYPE descriptors       │
│ 4. Operational Probes     │ `health` router               │ `GET /health/liveness` (200 OK process)   │
│                           │ (`services/api/routers/health.py`) `GET /health/readiness` (Aggregated DB)│
└───────────────────────────┴───────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Log Privacy & PII Sanitization Engine

### 3.1 Privacy Guarantee
In compliance with `ADR-003`, `ADR-004`, and `DEC-OBS-INH-03`, telemetry payloads MUST NEVER log plaintext user personal data (`CAT-2` watch history, notes, addresses) or security secrets (passwords, tokens, keys).

### 3.2 Automated Redaction Rules
The `JSONFormatter` and `sanitize_value` utility intercept log data before emission:
- **Redacted Keys:** `password`, `secret`, `token`, `auth_token`, `authorization`, `watch_event_notes`, `user_address`, `email`, `access_token`.
- **Replacement Value:** `[REDACTED]` or `[REDACTED_SECRET]`.

---

## 4. Context Propagation Strategy

Every request flowing through the API service inherits and propagates two context identifiers:
1. `X-Correlation-ID`: `UUIDv7` unique request/transaction tracking key.
2. `traceparent`: W3C compliant trace context identifier (`00-<trace_id>-<span_id>-01`).

```text
Client ──▶ Kong Gateway Proxy ──▶ API Service ──▶ Response Headers
  │                                 │                    │
  └── X-Correlation-ID ─────────────┴── traceparent ─────┘
```

---

## 5. Prometheus TSDB Metrics Specification

The `GET /metrics` endpoint exposes standardized metrics:

```text
# HELP cinevault_http_requests_total Total HTTP requests handled by API service
# TYPE cinevault_http_requests_total counter
cinevault_http_requests_total{method="GET",path="/v1/titles",status="200"} 42

# HELP cinevault_http_request_duration_seconds Last HTTP request duration in seconds
# TYPE cinevault_http_request_duration_seconds gauge
cinevault_http_request_duration_seconds{method="GET",path="/v1/titles",status="200"} 0.0150

# HELP cinevault_auth_failures_total Total authentication failures
# TYPE cinevault_auth_failures_total counter
cinevault_auth_failures_total 0

# HELP cinevault_dependency_health_status Operational health status of dependencies (1=Healthy, 0=Unhealthy)
# TYPE cinevault_dependency_health_status gauge
cinevault_dependency_health_status{dependency="pgbouncer"} 1
cinevault_dependency_health_status{dependency="valkey"} 1
cinevault_dependency_health_status{dependency="rabbitmq"} 1

# HELP cinevault_quarantine_records_current Current count of quarantined payloads
# TYPE cinevault_quarantine_records_current gauge
cinevault_quarantine_records_current 0

# HELP cinevault_sync_outbox_backlog Current count of pending sync mutations
# TYPE cinevault_sync_outbox_backlog gauge
cinevault_sync_outbox_backlog 0
```

---

## 6. Health Probe Boundaries

### 6.1 Liveness Probe (`GET /health/liveness`)
- Status: `HTTP 200 OK`
- Purpose: Verifies API compute process is alive and responding.

### 6.2 Readiness Probe (`GET /health/readiness`)
- Status: `HTTP 200 OK` if all operational dependencies (PgBouncer, Valkey, RabbitMQ) are HEALTHY; `HTTP 503 SERVICE UNAVAILABLE` if any dependency is UNHEALTHY.
- Security Invariant: Zero credentials, passwords, internal topology parameters, or queue contents exposed in the JSON response payload.

---

## 7. Operational Incident Runbooks

1. **Primary Database Outage:** Probe fails → Failover to PostgreSQL Streaming Read Replica.
2. **Rate Limit / Circuit Trip:** HTTP 429 spikes → Circuit Breaker trips → Fallback to stale L2 Valkey cache.
3. **Dead-Letter Queue Accumulation:** `queue.dead_letter` depth > 10 → Alert operator → Triage quarantined payload checksums.
