# CineVault OS — Observability & Operations Decision Log V1

**Document Type:** Observability & Operations Strategy Decision Log  
**Status:** Approved & Baseline Locked  
**Owner Approval Date:** 2026-08-08  
**Scope:** Architectural Decisions Inherited, Approved, or Deferred in `docs/OBSERVABILITY_OPERATIONS_ARCHITECTURE_V1.md`  

---

## 1. Governance Overview

This Decision Log categorizes all architectural decisions associated with the CineVault OS Observability & Operations Architecture V1.

Following formal Project Owner review on **2026-08-08**, all eight proposed observability architecture decisions (`DEC-OBS-PRP-01` through `DEC-OBS-PRP-08`) have received **Explicit Project Owner Approval** via the Control Room workflow and are now officially **BASELINE LOCKED**.

### Historical Lifecycle Transition
Decisions preserve full historical traceability:
```text
PROPOSED ──▶ OWNER REVIEW ──▶ OWNER APPROVED / BASELINE LOCKED (2026-08-08)
```

> [!IMPORTANT]
> **CONCEPTUAL BASELINE LOCK VS. TECHNOLOGY SELECTION**  
> Project Owner approval locks the **conceptual observability architecture** and numerical SLO targets (`DEC-OBS-PRP-08`). It does NOT resolve deferred vendor selections (alert routing SaaS, observability backends, log aggregators) nor does it authorize dashboard creation, code implementation, or cloud monitoring deployment.

---

## 2. Decision Log Matrix

### A. APPROVED INHERITED DOMAIN CONSTRAINTS

| Decision ID | Inherited Constraint | Baseline Source | Governance Status | Summary of Inherited Constraint |
|---|---|---|---|---|
| `DEC-OBS-INH-01` | **UUIDv7 Identity Correlation** | ADR-001 | `INHERITED` | Correlation IDs and trace context use UUIDv7 keys. Provider IDs are mappings only. |
| `DEC-OBS-INH-02` | **Content Hierarchy Telemetry Model** | ADR-002 | `INHERITED` | Latency histograms and trace spans observe `Title -> Edition -> Release` structure. |
| `DEC-OBS-INH-03` | **Personal Data Privacy in Telemetry** | ADR-003, ADR-004 | `INHERITED` | Telemetry MUST NOT log user personal data (`CAT-2`), watch logs, or auth tokens. |
| `DEC-OBS-INH-04` | **AI Proposal Boundary Monitoring** | ADR-004, DEC-SEC-PRP-07 | `INHERITED` | AI proposals (`CAT-6`) monitored as untrusted proposal queues; direct canonical write prohibited. |
| `DEC-OBS-INH-05` | **Pre-Acquisition Licensing Verification** | DEC-ING-PRP-01 | `INHERITED` | Ingestion telemetry tracks Pre-Acquisition Gate checks; rejects unauthorized sources. |
| `DEC-OBS-INH-06` | **Domain Authority Provenance Lineage** | DS-01, DEC-SRC-PRP-01/02 | `INHERITED` | Audit and lineage logs credit approved domain authorities (KOBIS Primary, TheTVDB Secondary). |
| `DEC-OBS-INH-07` | **Metadata vs Media Rights Isolation** | DEC-ING-PRP-05 | `INHERITED` | Object storage metrics track HTTPS URL proxy caches without storing binary media blobs. |
| `DEC-OBS-INH-08` | **Three-Tier API Isolation Monitoring** | DEC-API-PRP-02 | `INHERITED` | SLI/SLO tracking isolates public REST API performance from internal curation tools. |
| `DEC-OBS-INH-09` | **PostgreSQL Physical Performance Telemetry** | DEC-PHYS-PRP-01..12 | `INHERITED` | Database monitoring tracks connection pool utilization, replication lag, and continuous WAL archival. |
| `DEC-OBS-INH-10` | **5-Zone Security Perimeter Monitoring** | DEC-INFRA-PRP-06 | `INHERITED` | Telemetry collectors observe zero-trust network boundaries across 5 security zones. |
| `DEC-OBS-INH-11` | **Encryption in Transit & at Rest Requirement** | DEC-SEC-INH-11 | `INHERITED` | Telemetry transport and storage must be encrypted. Proposed standards: `DEC-SEC-PRP-09`. |
| `DEC-OBS-INH-12` | **Privileged Session Protection Constraint** | DEC-SEC-INH-12 | `INHERITED` | Audit runbooks observe privileged session protection and re-authentication rules (`DEC-SEC-PRP-10`). |
| `DEC-OBS-INH-13` | **RPO < 5 Min & RTO < 1 Hr Recovery Baseline** | DEC-INFRA-PRP-08 | `INHERITED` | Disaster recovery monitoring inherits RPO < 5 minutes and RTO < 1 hour target objectives. |

---

### B. OWNER-APPROVED & LOCKED OBSERVABILITY PROPOSALS

| Decision ID | Decision Title | Owner Approval Date | Governance Status | Scope of Approved Baseline |
|---|---|---|---|---|
| `DEC-OBS-PRP-01` | **Standardized Structured JSON Logging Strategy** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Structured JSON logs (Zap/Winston) with mandatory UUIDv7 Correlation ID propagation. |
| `DEC-OBS-PRP-02` | **End-to-End OpenTelemetry Distributed Tracing** | 2026-08-08 | `OWNER APPROVED / LOCKED` | OpenTelemetry / W3C Trace Context across API nodes, queues, and background workers. |
| `DEC-OBS-PRP-03` | **Prometheus Metrics & Health Probe Architecture** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Prometheus metric format and `/health/liveness` and `/health/readiness` probes. |
| `DEC-OBS-PRP-04` | **Ingestion Lifecycle & Provider Quota Monitoring** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Track 12-state ingestion transitions, HTTP 429 rate limit backoffs, and circuit breaker trips. |
| `DEC-OBS-PRP-05` | **Reconciliation Queue & Quarantine Monitoring** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Monitor `quality.quarantine_record` accumulation (`CAT-6`), AI proposal review rate, and match confidence. |
| `DEC-OBS-PRP-06` | **Database & WAL Archival Operational Telemetry** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Monitor connection pool exhaustion, streaming replication lag, disk space, and continuous WAL archival. |
| `DEC-OBS-PRP-07` | **Operational Incident Runbook & DLQ Protocol** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Operational runbooks for DB failover, circuit trips, outbox backlog, and DLQ triage. |
| `DEC-OBS-PRP-08` | **SLO & Alerting Threshold Framework** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Approve 99.9% read availability SLO, p95 latency targets (<200ms API, <2000ms sync), and error budget burn alerts. |

---

### C. DEFERRED DECISIONS (Carried Forward & Postponed)

| Decision ID | Deferred Topic | Reason for Deferral | Target Phase |
|---|---|---|---|
| `DEC-OBS-DEF-01` | **Alert Routing Platform Selection — DEFERRED** | Alert routing platform selection deferred. Zero vendor lock-in. | Operations Infrastructure Phase |
| `DEC-OBS-DEF-02` | **Observability Platform / Backend Selection — DEFERRED** | Observability platform / backend selection deferred. Zero vendor lock-in. | Cloud Procurement Phase |
| `DEC-OBS-DEF-03` | **Log Aggregation Backend Selection — DEFERRED** | Log aggregation backend selection deferred. Zero vendor lock-in. | Operations Infrastructure Phase |
| `DEC-INFRA-DEF-01` | **Cloud Infrastructure Provider & WAF Selection — DEFERRED** | Cloud provider selection deferred. | Cloud Procurement Phase |
| `DEC-API-DEF-02` | **Authentication Provider & OAuth Server Selection — DEFERRED** | OAuth2 server technology selection deferred. | Security Implementation Phase |
| `DEC-API-DEF-03` | **API Gateway Technology Selection — DEFERRED** | Gateway proxy technology selection deferred. | Edge Infrastructure Phase |
| `DEC-API-DEF-04` | **Physical Cache Storage & Key Schemas — DEFERRED** | Cache software selection deferred. | Physical Cache Implementation Phase |
| `DEC-PHYS-DEF-04` | **Backup / DR Cloud Storage Target — DEFERRED** | Backup cloud target selection deferred. | Operations Phase |

---

### D. OPEN QUESTIONS & BLOCKED DECISIONS

| Decision ID | Topic | Description & Barrier | Action Required |
|---|---|---|---|
| `DEC-OBS-OPN-01` | **Telemetry Metric & Trace Retention Policy** | Evaluation between 30-day vs 90-day retention windows for metric and trace telemetry data. | Storage cost benchmarking in operations planning phase. |
| `DEC-OBS-OPN-02` | **Automated Anomaly Detection Evaluation** | Evaluation of machine-learning dynamic baseline thresholds versus static alerting thresholds. | Operational evaluation in production trial phase. |
| `DEC-SEC-OPN-01` | **Control Room MFA Protocol Standard** | Evaluation between TOTP vs WebAuthn / FIDO2 hardware keys for curator accounts. | Curator workflow review in security implementation phase. |
| `DEC-SEC-OPN-02` | **SIEM / Security Analytics Integration Platform** | Technology selection for centralized security log aggregation and threat detection. | Security tooling review in operations planning phase. |
| `DEC-INFRA-OPN-01` | **Queue Broker Technology Standard** | Evaluation between RabbitMQ (AMQP) vs Redis Streams vs NATS for asynchronous queue workload. | Queue workload benchmarking in implementation phase. |
| `DEC-INFRA-OPN-02` | **Multi-Region Read Replica Scale Topology** | Evaluation of multi-region read replica deployment for global client latency optimization. | Global latency testing in mobile performance review phase. |
| `DEC-ING-OPN-02` | **Raw CAT-5 Payload Retention Policy** | Retention window for raw `CAT-5` payloads (indefinite storage vs 365-day cold archive). | Operational policy definition in storage planning phase. |
| `DEC-QUAL-OPN-02` | **Quarantine Retention Window** | Retention duration for quarantined invalid/ambiguous payloads before automated cleanup. | Operational policy definition in storage planning phase. |
| `DEC-PHYS-OPN-01` | **Raw Payload Partition Granularity** | Monthly vs weekly range partition granularity for `ingestion.raw_payload_capture`. | Ingest volume benchmarking in implementation phase. |

---
