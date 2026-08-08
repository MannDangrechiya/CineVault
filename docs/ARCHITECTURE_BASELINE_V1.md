# CineVault OS — Architecture Baseline Specification V1

**Document Type:** Authoritative Architecture Baseline Index & Change-Control Standard  
**Status:** BASELINE LOCKED (Project Owner Approval Complete — 2026-08-08)  
**Implementation Authorization:** NOT YET AUTHORIZED  
**Date:** 2026-08-08  
**Scope:** Master Baseline Index across ADRs 001–004, Data Model V1, ERD V1, Data Dictionary V1, Data Source Registry V1, Ingestion V1, Data Quality V1, API Spec V1, Physical Database V1, Infrastructure V1, Security V1, and Observability & Operations V1  

---

## 1. Baseline Purpose

The purpose of the **CineVault OS Architecture Baseline V1** is to serve as the single authoritative, frozen, and immutable index of all conceptual architecture specifications, data ownership boundaries, security constraints, and operational SLAs governing CineVault OS.

This document synthesizes all approved architectural gates into a single locked baseline index. Any future modification to the architecture defined herein requires a formal Control Room Architecture Amendment Protocol.

---

## 2. Locked Architecture Layers

The CineVault OS architecture consists of 8 primary layers, all of which are officially **LOCKED**:

```text
┌───────────────────────────────────────┬───────────────────────┬───────────────────────────────────────────┐
│ Architecture Layer                    │ Governance Status     │ Approval Source & Baseline Standard       │
├───────────────────────────────────────┼───────────────────────┼───────────────────────────────────────────┤
│ 1. Data Model & ERD V1                │ BASELINE LOCKED       │ ADR-001..004, Data Model V1, ERD V1       │
│ 2. Data Source Registry V1            │ BASELINE LOCKED       │ DS-01..07, DEC-SRC-PRP-01..02             │
│ 3. Ingestion Architecture V1          │ BASELINE LOCKED       │ DEC-ING-PRP-01..06                        │
│ 4. Data Quality & Reconciliation V1   │ BASELINE LOCKED       │ DEC-QUAL-PRP-01..06                       │
│ 5. API Specification V1               │ BASELINE LOCKED       │ DEC-API-PRP-01..11                        │
│ 6. Physical Database Design V1        │ BASELINE LOCKED       │ DEC-PHYS-PRP-01..12                       │
│ 7. Infrastructure Architecture V1     │ BASELINE LOCKED       │ DEC-INFRA-PRP-01..08                      │
│ 8. Security Architecture V1           │ BASELINE LOCKED       │ DEC-SEC-PRP-01..11 (Approved 2026-08-08)  │
│ 9. Observability & Operations V1      │ BASELINE LOCKED       │ DEC-OBS-PRP-01..08 (Approved 2026-08-08)  │
└───────────────────────────────────────┴───────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Accepted Architecture Decision Records (ADRs)

* **ADR-001 (Canonical Identity & Classification):** UUIDv7 is the canonical identity standard. External provider IDs are mappings only. Data classified into `CAT-1` (Platform), `CAT-2` (Personal), `CAT-3` (Derived), `CAT-4` (Audit), `CAT-5` (Ingestion), and `CAT-6` (Proposals).
* **ADR-002 (Content Domain Model):** Rigid content hierarchy (`Title -> Edition -> Release` and `Title -> Season -> Episode`). Primary Edition invariant: exactly one `is_primary = true` per Title (`UNIQUE (title_id) WHERE (is_primary = true)`).
* **ADR-003 (Personal Data & Watch History):** `CAT-2` User Personal Data isolated in PostgreSQL `personal` schema. Watch events append-only; in-place deletes prohibited. Merges spawn `personal_data_conflict` records.
* **ADR-004 (Offline Sync & Data Ownership):** Durable offline sync via client UUIDv7 `mutation_id`. AI processing generated data classified as `CAT-6` non-canonical proposals.

---

## 4. Approved Data Source Strategy (`DEC-SRC-PRP-01..02`)

* **Domain Authority Matrix:** `DS-01` through `DS-07` registry bounds.
* **DEC-SRC-PRP-01:** KOBIS/KOFIC approved as Primary Korean-Domain Authority.
* **DEC-SRC-PRP-02:** TheTVDB approved as Secondary TV Authority.

---

## 5. Approved Ingestion Architecture (`DEC-ING-PRP-01..06`)

* **DEC-ING-PRP-01:** Pre-Acquisition Licensing Gate mandatory before external API fetching. Zero scraping.
* **DEC-ING-PRP-02:** Raw Payload Capture Staging (`ingestion.raw_payload_capture`, `CAT-5`).
* **DEC-ING-PRP-05:** Metadata vs Media Rights Segregation (HTTPS URL proxies only; zero media blobs).

---

## 6. Approved Data Quality & Reconciliation Architecture (`DEC-QUAL-PRP-01..06`)

* **DEC-QUAL-PRP-01:** 8-Layer Data Quality Verification Model.
* **DEC-QUAL-PRP-02:** 10-Dimension Quality Assessment Framework.
* **DEC-QUAL-PRP-04:** Automated Candidate Reconciliation & Lineage Line Tracking.
* **DEC-QUAL-PRP-06:** Control Room Human Curation Review Gate for ambiguous observations.

---

## 7. Approved API Architecture (`DEC-API-PRP-01..11`)

* **DEC-API-PRP-01:** OpenAPI 3.1 machine-readable contract standard.
* **DEC-API-PRP-02:** 3-Tier API Boundary Isolation (Public Client `/v1/`, Internal Admin `/internal/v1/`, Provider Integration Boundary).
* **DEC-API-PRP-06:** Cursor-based pagination and client UUIDv7 `mutation_id` idempotency.

---

## 8. Approved Physical Database Architecture (`DEC-PHYS-PRP-01..12`)

* **DEC-PHYS-PRP-01:** 5-Schema PostgreSQL Architecture (`canonical`, `personal`, `ingestion`, `quality`, `audit`).
* **DEC-PHYS-PRP-02:** Native `uuid` column type with internal UUIDv7 generation.
* **DEC-PHYS-PRP-08:** PostgreSQL Role-Based Access Control (`cinevault_app`, `cinevault_ingest`, `cinevault_admin`, `cinevault_analytics`).

---

## 9. Approved Infrastructure Architecture (`DEC-INFRA-PRP-01..08`)

* **DEC-INFRA-PRP-01:** 4-Tier Environment Model (`local`, `dev`, `staging`, `prod`).
* **DEC-INFRA-PRP-02:** 8 Independent Compute Workload Services.
* **DEC-INFRA-PRP-03:** PostgreSQL Multi-AZ Primary with Read Replica pool.
* **DEC-INFRA-PRP-04:** Distributed Cache / Rate-Limit State Store boundary.
* **DEC-INFRA-PRP-05:** Asynchronous Task Queues + Dead-Letter Queue (DLQ).
* **DEC-INFRA-PRP-06:** 5-Zone Network Security Perimeter (Edge, DMZ, App, Worker, Data).
* **DEC-INFRA-PRP-08:** RPO < 5 minutes and RTO < 1 hour recovery target baselines.

---

## 10. Approved Security Architecture (`DEC-SEC-PRP-01..11`)

* **DEC-SEC-PRP-01:** Zero-Trust Service-to-Service Authorization (mTLS / service tokens).
* **DEC-SEC-PRP-02:** Control Room MFA Architecture for internal curation.
* **DEC-SEC-PRP-03:** Defense-in-Depth API Security (Rate limits, CORS, RFC 7807 safety).
* **DEC-SEC-PRP-04:** Personal Data Protection Security Model (`personal` schema, append-only logs).
* **DEC-SEC-PRP-05:** Canonical Integrity Protection Model (Zero public/provider canonical write).
* **DEC-SEC-PRP-06:** Provider Credential Isolation Model (Server-side Secrets Manager injection).
* **DEC-SEC-PRP-07:** AI Proposal Security Boundary (AI confined to `CAT-6`; direct canonical write architecturally prohibited).
* **DEC-SEC-PRP-08:** Security Audit & Evidence Lineage Architecture.
* **DEC-SEC-PRP-09:** Cryptographic Transport & Storage Standards (TLS 1.3, AES-256).
* **DEC-SEC-PRP-10:** Privileged Session Timeout Policy (15-minute curator timeout).
* **DEC-SEC-PRP-11:** Security Audit Integrity Protection Model (Tamper-evident audit requirement).

---

## 11. Approved Observability & Operations Architecture (`DEC-OBS-PRP-01..08`)

* **DEC-OBS-PRP-01:** Standardized Structured JSON Logging & Correlation ID Strategy.
* **DEC-OBS-PRP-02:** End-to-End OpenTelemetry Distributed Tracing.
* **DEC-OBS-PRP-03:** Prometheus Metrics & Health Probe Architecture (`/health/*`).
* **DEC-OBS-PRP-04:** Ingestion Lifecycle & Provider Quota Monitoring.
* **DEC-OBS-PRP-05:** Quality Quarantine & AI Proposal Monitoring.
* **DEC-OBS-PRP-06:** Database Performance & Continuous WAL Archival Monitoring.
* **DEC-OBS-PRP-07:** Operational Incident Runbooks & DLQ Protocol.
* **DEC-OBS-PRP-08:** Service-Level Objective (SLO) Framework (99.9% read availability, p95 latency targets).

---

## 12. Inherited Decisions Summary

* `ADR-001` → `ADR-004`: Core canonical identity, domain hierarchy, personal data isolation, offline sync rules.
* `DEC-SEC-INH-01` → `DEC-SEC-INH-12`: UUIDv7 preservation, least privilege, encryption requirement, privileged session protection.
* `DEC-OBS-INH-01` → `DEC-OBS-INH-13`: Identity correlation, privacy in telemetry, RPO < 5 min & RTO < 1 hr baselines.

---

## 13. Owner-Approved / Baseline Locked Proposals

* **Data Source Registry:** `DEC-SRC-PRP-01..02`
* **Ingestion Architecture:** `DEC-ING-PRP-01..06`
* **Data Quality Architecture:** `DEC-QUAL-PRP-01..06`
* **API Specification:** `DEC-API-PRP-01..11`
* **Physical Database Design:** `DEC-PHYS-PRP-01..12`
* **Infrastructure Architecture:** `DEC-INFRA-PRP-01..08`
* **Security Architecture:** `DEC-SEC-PRP-01..11` (Approved 2026-08-08)
* **Observability Architecture:** `DEC-OBS-PRP-01..08` (Approved 2026-08-08)

---

## 14. Deferred Decisions Summary

The following technical execution items remain strictly **DEFERRED** and are not resolved by baseline locking:
* `DEC-API-DEF-02`: Authentication Provider & OAuth Server Selection
* `DEC-API-DEF-03`: API Gateway Technology Selection
* `DEC-API-DEF-04`: Physical Cache Storage & Key Schemas
* `DEC-PHYS-DEF-02`: Database Migration Tool Selection
* `DEC-PHYS-DEF-03`: Connection Pool Topology Selection
* `DEC-PHYS-DEF-04`: Backup Cloud Storage Target Selection
* `DEC-INFRA-DEF-01`: Cloud Infrastructure Provider & WAF Selection
* `DEC-INFRA-DEF-02`: Kubernetes Manifests & Terraform Scripting
* `DEC-INFRA-DEF-03`: CI/CD Pipeline Automation Scripting
* `DEC-OBS-DEF-01`: Alert Routing Platform Selection — DEFERRED
* `DEC-OBS-DEF-02`: Observability Platform Selection — DEFERRED
* `DEC-OBS-DEF-03`: Log Aggregation Backend Selection — DEFERRED

---

## 15. Open Questions Summary

The following analytical evaluation items remain **OPEN** and un-resolved:
* `DEC-SEC-OPN-01`: Control Room MFA Protocol Standard (TOTP vs WebAuthn)
* `DEC-SEC-OPN-02`: SIEM / Security Analytics Platform Evaluation
* `DEC-OBS-OPN-01`: Telemetry Metric & Trace Retention Policy (30d vs 90d)
* `DEC-OBS-OPN-02`: Automated Anomaly Detection Evaluation
* `DEC-INFRA-OPN-01`: Queue Broker Technology Standard (RabbitMQ vs Redis Streams vs NATS)
* `DEC-INFRA-OPN-02`: Multi-Region Read Replica Scale Topology
* `DEC-ING-OPN-02`: Raw CAT-5 Payload Retention Policy
* `DEC-QUAL-OPN-02`: Quarantine Retention Window
* `DEC-PHYS-OPN-01`: Raw Payload Partition Granularity

---

## 16. Vendor-Neutrality Statement

The CineVault OS Architecture Baseline V1 is strictly vendor-neutral. Zero vendor lock-in exists across the platform. All cloud providers (AWS, GCP, Azure), SaaS platforms (Auth0, Datadog, PagerDuty, Grafana Cloud), gateways (Kong, Envoy), and cache/queue software remain deferred until explicit technology selection gates.

---

## 17. Implementation Boundary Statement

> [!CAUTION]
> **IMPLEMENTATION BOUNDARY LOCK**  
> Baseline locking certifies that all conceptual architecture specifications are frozen. It does NOT authorize code implementation, SQL DDL execution, cloud resource provisioning, container deployment, or monitoring installation. Implementation remains strictly blocked until passing the Implementation Readiness Gate.

---

## 18. Baseline Change-Control Rules

1. **Immutability:** Locked architecture specifications (`V1`) CANNOT be modified via ad-hoc code edits or informal pull requests.
2. **Amendment Trigger:** Any proposed change to a locked architecture decision requires a formal Control Room Architecture Amendment Document.
3. **Owner Review:** Architecture amendments must pass validation and receive explicit Project Owner approval before taking effect.

---

## 19. Architecture Amendment Process

```text
Proposed Change ──▶ Architecture Amendment Doc ──▶ Validation Audit ──▶ Owner Approval ──▶ Baseline Update
```

---

## 20. Final Baseline Status

* **Architecture Baseline Status:** `BASELINE LOCKED`
* **Implementation Authorization:** `NOT YET AUTHORIZED`
* **Next Gate:** Implementation Readiness Gate & Technology Evaluation

---
