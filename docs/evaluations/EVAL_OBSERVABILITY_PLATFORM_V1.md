# CineVault OS — Technology Evaluation: Observability Platform V1

**Document Type:** Technology Evaluation & Selection Proposal  
**Decision ID:** `DEC-OBS-DEF-02` — Observability Platform Selection  
**Status:** Evaluation Complete — Awaiting Owner Approval  
**Date:** 2026-08-08  
**Selected Technology Recommendation:** OpenTelemetry Collector + Prometheus + Grafana Stack (CNCF / Open Source)  
**Alternative Candidate:** SigNoz (AGPLv3 Open Source / ClickHouse Core)  
**Governance State:** PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED  
**Implementation Authorization:** NOT AUTHORIZED  

---

## 1. Decision Under Evaluation

* **Decision ID:** `DEC-OBS-DEF-02`
* **Topic:** Observability Platform & Telemetry Backend Technology Selection
* **Originating Baseline:** Observability & Operations Architecture V1 (`docs/OBSERVABILITY_OPERATIONS_ARCHITECTURE_V1.md`, `DEC-OBS-PRP-03`)
* **Current Governance State:** `DEFERRED` → `PROPOSED` (Awaiting Owner Review)
* **Objective:** Select an observability telemetry ingestion collector, metric backend, and visualization platform to collect OpenTelemetry traces, scrape Prometheus metrics, monitor SLO error budgets, and render operational dashboards while protecting sensitive personal data (`CAT-2`) from telemetry leaks.

---

## 2. Canonical Architecture Requirements

Derived from locked baseline specifications (`Observability Architecture V1`, `Security Architecture V1`):

```text
┌───────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────┐
│ Feature / Capability Requirement      │ Architectural Specification               │ Canonical Source Reference                │
├───────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. OpenTelemetry Protocol (OTLP) Std  │ OTLP gRPC/HTTP trace & metric ingestion   │ Observability V1 (DEC-OBS-PRP-03)         │
│ 2. UUIDv7 Correlation ID Propagation │ Distributed trace context header injection│ Observability V1 (DEC-OBS-PRP-01)         │
│ 3. Redaction of Personal Data         │ Automatic scrub of CAT-2 user attributes  │ Security V1 (DEC-SEC-PRP-08, OBS-PRP-07) │
│ 4. SLO Error Budget Monitoring        │ Real-time latency (p99) & availability    │ Observability V1 (DEC-OBS-PRP-04)         │
│ 5. Permissive Open-Source Licensing   │ Apache 2.0 / AGPLv3 (No proprietary SaaS) │ Infrastructure V1 (DEC-INFRA-DEF-01)      │
└───────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Architecture Dependencies

* **API Gateway & Microservices:** Inject OpenTelemetry trace context headers (`DEC-API-DEF-03`).
* **Log Aggregator:** Grafana Loki (`DEC-OBS-DEF-03`) integrated into Grafana dashboards.
* **Alert Router:** Grafana OnCall / Alertmanager (`DEC-OBS-DEF-01`).

---

## 4. Candidate Technologies Identified

Four observability platforms were evaluated:

1. **OpenTelemetry Collector + Prometheus + Grafana (CNCF / AGPLv3):** Industry-standard open-source observability stack.
2. **SigNoz (AGPLv3 / ClickHouse):** Open-source native OpenTelemetry APM platform.
3. **Datadog APM & Metrics (Proprietary SaaS):** SaaS observability platform.
4. **New Relic APM (Proprietary SaaS):** Managed SaaS observability platform.

---

## 5. Candidate Evaluation & Feature Compatibility Matrix

```text
┌───────────────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Dimension / Feature                   │ 1. OTel+Prom+Graf │ 2. SigNoz         │ 3. Datadog        │ 4. New Relic      │
├───────────────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ License / Delivery Model              │ Apache 2.0 / AGPL │ AGPLv3 / SaaS     │ Proprietary SaaS  │ Proprietary SaaS  │
│ Native OpenTelemetry (OTLP) Support   │ 100% NATIVE (CNCF)│ 100% NATIVE       │ REQUIRES TRANSLATOR REQUIRES TRANSLATOR │
│ Telemetry PII Scrubbing Processor     │ NATIVE (OTel Coll)│ SUPPORTED         │ CONFIGURABLE      │ CONFIGURABLE      │
│ Vendor Lock-In Depth                  │ **LOW**           │ LOW               │ HIGH (Proprietary)│ HIGH (Proprietary)│
│ Host / Metric Ingestion Cost          │ Infrastructure    │ Infrastructure    │ EXTREMELY EXPENSIVE VERY EXPENSIVE    │
│ Dashboard & Alerting Integration      │ EXCELLENT         │ GOOD              │ EXCELLENT         │ GOOD              │
└───────────────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 6. Detailed Evaluation Dimensions

### Functional Compatibility & PII Redaction
The **OpenTelemetry Collector** runs as a sidecar/daemonset, filtering all traces and metrics before ingestion. Redaction processors automatically strip personal user data (`CAT-2` email, IP address, auth tokens) before forwarding telemetry to Prometheus and Tempo/Jaeger backends. Grafana provides unified visual dashboards combining Prometheus metrics and OpenTelemetry trace graphs.

### Security & Privacy
* Zero plaintext credentials or personal data stored in metric labels or trace attributes.
* Telemetry transit encrypted via mTLS / TLS 1.3.

---

## 7. Cost Model & 36-Month TCO

* **Software Cost:** $0 (OpenTelemetry Apache 2.0 / Prometheus Apache 2.0 / Grafana AGPLv3).
* **Storage & Compute Cost:** Prometheus TSDB & Grafana pod storage (~$80/month = ~$2,880 / 36 months).
* **Comparison (Datadog):** Estimated ~$850/month for equivalent host & trace volume (~$30,600 / 36 months).
* **TCO Summary (36 Months):** ~$2,880 total infrastructure cost (saving ~$27,000+ vs SaaS).

---

## 8. Vendor Lock-In & Portability Analysis

* **Protocol Portability:** Standard OTLP protocol (OpenTelemetry) and Prometheus exposition format. Client SDKs are vendor-agnostic.
* **Lock-In Depth:** **LOW** (CNCF Open Standard).

---

## 9. Risk Assessment & Mitigations

* **Risk:** High memory usage in OpenTelemetry Collector under trace volume spikes.
  * **Mitigation:** Enable memory_limiter processor in OTel Collector and configure head-based/tail-based probabilistic sampling.

---

## 10. Recommended Technology Selection

* **Primary Recommendation:** **OpenTelemetry Collector + Prometheus + Grafana Stack (CNCF / Open Source)**
* **Alternative Candidate:** **SigNoz (AGPLv3 Open Source / ClickHouse Core)**
* **Justification:** Standard CNCF OpenTelemetry collector and Prometheus/Grafana stack eliminate SaaS vendor lock-in, provide built-in PII redaction processors, and reduce 36-month TCO by over $27,000.

---

## 11. Final Governance Status

Evaluation:
COMPLETE

Recommendation:
OpenTelemetry Collector + Prometheus + Grafana Stack (CNCF / Open Source)

Governance:
PROPOSED TECHNOLOGY RECOMMENDATION

Approval:
OWNER REVIEW REQUIRED

Technology Approved:
NO

Implementation:
NOT AUTHORIZED
