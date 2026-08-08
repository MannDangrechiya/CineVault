# CineVault OS — Technology Evaluation: Log Aggregation Backend V1

**Document Type:** Technology Evaluation & Selection Proposal  
**Decision ID:** `DEC-OBS-DEF-03` — Log Aggregation Backend Selection  
**Status:** Evaluation Complete — Awaiting Owner Approval  
**Date:** 2026-08-08  
**Selected Technology Recommendation:** Grafana Loki (AGPLv3 License — Grafana Open Source)  
**Alternative Candidate:** Vector (Apache 2.0 — Rust) + ClickHouse (Apache 2.0)  
**Governance State:** PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED  
**Implementation Authorization:** NOT AUTHORIZED  

---

## 1. Decision Under Evaluation

* **Decision ID:** `DEC-OBS-DEF-03`
* **Topic:** Log Aggregation Backend Technology Selection
* **Originating Baseline:** Observability & Operations Architecture V1 (`docs/OBSERVABILITY_OPERATIONS_ARCHITECTURE_V1.md`, `DEC-OBS-PRP-01`)
* **Current Governance State:** `DEFERRED` → `PROPOSED` (Awaiting Owner Review)
* **Objective:** Select a structured JSON log aggregation backend engine to ingest, index, query, and retain log streams from API gateway proxies, microservices, ingestion pipeline workers, keycloak identity servers, and database poolers, while enforcing UUIDv7 correlation ID lookups and mandatory personal data redaction (`CAT-2`).

---

## 2. Canonical Architecture Requirements

Derived from locked baseline specifications (`Observability Architecture V1`, `Security Architecture V1`):

```text
┌───────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────┐
│ Feature / Capability Requirement      │ Architectural Specification               │ Canonical Source Reference                │
├───────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. Structured JSON Log Processing     │ Standardized JSON format with UUIDv7 ID   │ Observability V1 (DEC-OBS-PRP-01)         │
│ 2. Microsecond Log Search & Query     │ Fast correlation ID trace-to-log lookup   │ Observability V1 (DEC-OBS-PRP-01)         │
│ 3. PII & Secret Redaction Filter      │ Automatic regex scrubbing of CAT-2 attributes│ Security V1 (DEC-SEC-PRP-08, OBS-PRP-07)│
│ 4. Efficient Object Storage Retention │ Low-cost S3 bucket log chunk storage      │ Observability V1 (DEC-OBS-PRP-01)         │
│ 5. Permissive Open-Source Licensing   │ Open source (No proprietary SaaS lock-in) │ Infrastructure V1 (DEC-INFRA-DEF-01)      │
└───────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Architecture Dependencies

* **Log Shippers:** Fluent Bit / Vector log agents on Kubernetes nodes.
* **Observability Visualizer:** Grafana Dashboard (`DEC-OBS-DEF-02`).
* **Object Storage Target:** S3 API compatible storage (`DEC-ING-PRP-05`) for log chunk retention.

---

## 4. Candidate Technologies Identified

Four log aggregation engines were evaluated:

1. **Grafana Loki (AGPLv3):** Horizontal, highly available, multi-tenant log aggregation system indexing metadata labels rather than full text.
2. **Vector + ClickHouse (Apache 2.0):** Rust-based log pipeline agent storing compressed columnar logs in ClickHouse.
3. **OpenSearch / Elasticsearch (Apache 2.0 / ALv2):** Full-text inverted index search engines.
4. **Datadog Log Management (Proprietary SaaS):** SaaS log management system.

---

## 5. Candidate Evaluation & Feature Compatibility Matrix

```text
┌───────────────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Dimension / Feature                   │ 1. Grafana Loki   │ 2. Vector+ClickH  │ 3. OpenSearch     │ 4. Datadog Logs   │
├───────────────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ License Type                          │ AGPLv3 (Open)     │ Apache 2.0 (Open) │ Apache 2.0        │ Proprietary SaaS  │
│ Storage Architecture                  │ S3 Object Chunks  │ ClickHouse Columns│ Inverted Index TS │ SaaS Multi-tenant │
│ Storage Compression Ratio             │ EXCELLENT (~10:1) │ EXCELLENT (~8:1)  │ MODERATE (~3:1)   │ SaaS Managed      │
│ Memory / RAM Footprint                │ LOW               │ MODERATE          │ HIGH (JVM Heavy)  │ SaaS Managed      │
│ Direct Grafana Metric-Trace Integration NATIVE EXCELLENT  │ EXCELLENT         │ GOOD              │ REQUIRES SAAS     │
│ PII Regex Scrubbing Pipeline          │ NATIVE (Loki Promtail) NATIVE (Vector)   │ SUPPORTED         │ SUPPORTED         │
│ 36-Month Cost Profile                 │ VERY LOW          │ LOW               │ HIGH (RAM Heavy)  │ EXTREMELY HIGH    │
└───────────────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 6. Detailed Evaluation Dimensions

### Functional Compatibility & Efficiency
Grafana Loki operates like Prometheus for logs: it indexes metadata labels (`app=api-gateway`, `env=production`, `level=error`) rather than full text, storing compressed log chunks directly in cost-effective S3 object storage targets (`DEC-ING-PRP-05`). This results in up to 90% lower RAM and storage overhead compared to Elasticsearch/OpenSearch, while maintaining rapid correlation lookup via `UUIDv7 X-Correlation-ID`.

### Security & Privacy
* Promtail / Vector log shippers execute mandatory regex scrubbing pipelines on Kubernetes nodes before log frames leave the local pod boundary, guaranteeing zero plaintext user emails, tokens, or personal data (`CAT-2`) reach Loki.

---

## 7. Cost Model & 36-Month TCO

* **Software Cost:** $0 (Grafana Loki AGPLv3).
* **Storage Cost:** ~500 GB compressed log chunks stored in S3 object storage (~$15/month = ~$540 / 36 months).
* **TCO Summary (36 Months):** ~$540 total log storage cost.

---

## 8. Vendor Lock-In & Portability Analysis

* **Data Portability:** Log streams use standard structured JSON formats. Chunks can be exported to raw JSON text files at any time.
* **Lock-In Depth:** **LOW** (Standard LogQL & JSON files).

---

## 9. Risk Assessment & Mitigations

* **Risk:** Log volume spikes during severe system outages causing storage pressure.
  * **Mitigation:** Enforce log retention expiration policies (30 days default) and drop debug-level log lines at the edge log shipper layer.

---

## 10. Recommended Technology Selection

* **Primary Recommendation:** **Grafana Loki (AGPLv3 License — Grafana Open Source)**
* **Alternative Candidate:** **Vector (Apache 2.0) + ClickHouse (Apache 2.0)**
* **Justification:** Grafana Loki provides high log compression, native S3 object storage target compatibility, seamless correlation with Prometheus metrics, and 90% lower resource costs than traditional inverted-index search engines.

---

## 11. Final Governance Status

Evaluation:
COMPLETE

Recommendation:
Grafana Loki (AGPLv3 License — Grafana Open Source)

Governance:
PROPOSED TECHNOLOGY RECOMMENDATION

Approval:
OWNER REVIEW REQUIRED

Technology Approved:
NO

Implementation:
NOT AUTHORIZED
