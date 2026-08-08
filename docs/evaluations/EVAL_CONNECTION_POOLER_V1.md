# CineVault OS — Technology Evaluation: Database Connection Pooling V1

**Document Type:** Technology Evaluation & Selection Proposal  
**Decision ID:** `DEC-PHYS-DEF-03` — Connection Pool Topology Selection  
**Status:** Evaluation Complete — Awaiting Owner Approval  
**Date:** 2026-08-08  
**Selected Technology Recommendation:** PgBouncer (BSD / PostgreSQL Open-Source License)  
**Alternative Candidate:** Supavisor (MIT License — Supabase Open Source)  
**Governance State:** PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED  
**Implementation Authorization:** NOT AUTHORIZED  

---

## 1. Decision Under Evaluation

* **Decision ID:** `DEC-PHYS-DEF-03`
* **Topic:** Connection Pooling Technology & Topology Selection
* **Originating Baseline:** Physical Database Design V1 (`docs/PHYSICAL_DATABASE_DESIGN_V1.md`, `DEC-PHYS-PRP-03`)
* **Current Governance State:** `DEFERRED` → `PROPOSED` (Awaiting Owner Review)
* **Objective:** Select a dedicated connection pooling proxy layer to multiplex thousands of short-lived client API request connections and background worker processes into a stable set of backend PostgreSQL server connections, preventing backend process fork exhaustion and maintaining query throughput.

---

## 2. Canonical Architecture Requirements

Derived from locked baseline specifications (`Physical Database Design V1`, `Infrastructure Architecture V1`):

```text
┌───────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────┐
│ Feature / Capability Requirement      │ Architectural Specification               │ Canonical Source Reference                │
├───────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. Connection Multiplexing            │ 1,000+ client connections -> 50-100 DB conn│ Physical DB V1 (DEC-PHYS-PRP-03)         │
│ 2. Transaction Pooling Mode           │ Release connection back to pool upon `COMMIT`│ Physical DB V1 (DEC-PHYS-PRP-03)         │
│ 3. Sub-millisecond Proxy Latency      │ Overhead < 0.5 ms per transaction         │ Physical DB V1 (DEC-PHYS-PRP-03)          │
│ 4. TLS 1.3 Encryption & SCRAM-SHA-256 │ Secure client-to-pooler & pooler-to-DB auth│ Security V1 (DEC-SEC-PRP-09)              │
│ 5. Prometheus Observability Metrics   │ Connection count, wait times, query rates │ Observability V1 (DEC-OBS-PRP-03)         │
└───────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Architecture Dependencies

* **Database Engine:** PostgreSQL 16+ (`DEC-PHYS-DEF-01`).
* **API Microservices:** Fast API / Go pods (`DEC-API-DEF-01`).
* **Ingestion Workers:** Asynchronous task workers (`DEC-INFRA-OPN-01`).

---

## 4. Candidate Technologies Identified

Four connection pooling technologies were evaluated:

1. **PgBouncer (BSD / PostgreSQL License):** Industry-standard lightweight connection pooler.
2. **Supavisor (MIT License — Supabase):** Modern cloud-native Elixir-based connection pooler.
3. **Odyssey (PostgreSQL License — Yandex):** Multi-threaded connection pooler built for high concurrency.
4. **Pgpool-II (BSD-like License):** Feature-heavy pooler with query caching and replication features.

---

## 5. Candidate Evaluation & Feature Compatibility Matrix

```text
┌───────────────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Dimension / Feature                   │ 1. PgBouncer      │ 2. Supavisor      │ 3. Odyssey        │ 4. Pgpool-II      │
├───────────────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ License Type                          │ BSD (PostgreSQL)  │ MIT               │ PostgreSQL        │ BSD-like          │
│ Pooling Paradigm                      │ Transaction/Session│ Multi-tenant/Edge │ Multi-threaded    │ Heavy Proxy       │
│ Memory Footprint                      │ ~2 MB / 1k conns  │ ~30 MB / 1k conns │ ~10 MB / 1k conns │ ~50 MB / 1k conns │
│ Transaction Mode Stability            │ EXCELLENT (Gold)  │ GOOD              │ GOOD              │ MODERATE          │
│ SCRAM-SHA-256 & TLS 1.3 Support       │ NATIVE            │ NATIVE            │ NATIVE            │ SUPPORTED         │
│ Operational Overhead                  │ VERY LOW          │ MODERATE          │ MODERATE          │ HIGH              │
│ Cloud & Managed Postgres Ubiquity     │ UNIVERSAL         │ GROWING           │ LIMITED           │ MODERATE          │
└───────────────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 6. Detailed Evaluation Dimensions

### Functional Compatibility & Efficiency
PgBouncer operating in **Transaction Mode (`pool_mode = transaction`)** provides maximum connection reuse. Client applications obtain a connection for the exact duration of a database transaction (`BEGIN ... COMMIT`) and release it immediately back to the pool, allowing 100 backend PostgreSQL connections to easily service 2,000+ concurrent application threads.

### Security & Observability
* Full support for SCRAM-SHA-256 password authentication pass-through and TLS 1.3 client encryption.
* Native `SHOW POOLS` administrative commands and `pgbouncer_exporter` integration for Prometheus metric scraping.

---

## 7. Cost Model & 36-Month TCO

* **Software Cost:** $0 (Open Source PostgreSQL BSD License).
* **Infrastructure Cost:** Ephemeral sidecar / dedicated proxy pods (~$30/month = ~$1,080 / 36 months).
* **TCO Summary (36 Months):** ~$1,080 total infrastructure cost.

---

## 8. Vendor Lock-In & Portability Analysis

* **Protocol Portability:** Standard PostgreSQL wire protocol (`libpq`).
* **Lock-In Depth:** **LOW** (Standard wire protocol proxy).

---

## 9. Risk Assessment & Mitigations

* **Risk:** Prepared statements incompatibility in transaction pooling mode.
* **Mitigation:** Use `protocol_prepared_statements = true` (PgBouncer 1.21+) or client-side explicit prepared statement configuration.

---

## 10. Recommended Technology Selection

* **Primary Recommendation:** **PgBouncer (BSD / PostgreSQL Open-Source License)**
* **Alternative Candidate:** **Supavisor (MIT License — Supabase Open Source)**
* **Justification:** PgBouncer is the battle-tested, lightweight industry standard with minimal memory overhead, zero software cost, and universal compatibility across cloud and local environments.

---

## 11. Final Governance Status

Evaluation:
COMPLETE

Recommendation:
PgBouncer (BSD / PostgreSQL Open-Source License)

Governance:
PROPOSED TECHNOLOGY RECOMMENDATION

Approval:
OWNER REVIEW REQUIRED

Technology Approved:
NO

Implementation:
NOT AUTHORIZED
