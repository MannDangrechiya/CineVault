# CineVault OS — Infrastructure Architecture Decision Log V1

**Document Type:** Infrastructure Architecture Strategy Decision Log  
**Status:** Post-Owner Approval Baseline (Approved)  
**Date:** 2026-08-08  
**Scope:** Architectural Decisions Introduced, Inherited, or Approved in `docs/INFRASTRUCTURE_ARCHITECTURE_V1.md`  

---

## 1. Governance Overview

This Decision Log documents all architectural decisions associated with the CineVault OS Infrastructure Architecture V1.

Following formal Project Owner review, all eight proposed infrastructure architecture decisions (`DEC-INFRA-PRP-01` through `DEC-INFRA-PRP-08`) have received **Formal Project Owner Approval** for their conceptual/architectural design direction.

### Historical Lifecycle Transition
Decisions preserve full historical traceability:
```text
PROPOSED ──▶ OWNER REVIEW ──▶ APPROVED (Conceptual Architecture Baseline)
```

> [!IMPORTANT]
> **CONCEPTUAL APPROVAL VS. IMPLEMENTATION DEFERRAL**  
> Project Owner approval authorizes **architectural concepts only**. It does NOT authorize infrastructure provisioning, cloud resource creation, Terraform scripts, Kubernetes manifests, CI/CD pipeline automation, or deployment execution. Detailed physical implementation remains deferred to respective target phases.

---

## 2. Decision Log Matrix

### A. APPROVED INHERITED DOMAIN CONSTRAINTS

| Decision ID | Inherited Constraint | Baseline Source | Summary of Inherited Constraint |
|---|---|---|---|
| `DEC-INFRA-INH-01` | **UUIDv7 Canonical Identity Preservation** | ADR-001 | Compute and caching layers preserve UUIDv7 canonical keys. Provider IDs are mappings only. |
| `DEC-INFRA-INH-02` | **Content Hierarchy Resource Model** | ADR-002 | Runtime services observe `Title -> Edition -> Release` and `Title -> Season -> Episode` structure. |
| `DEC-INFRA-INH-03` | **Personal Data Isolation & Non-Destruction** | ADR-003, ADR-004 | Infrastructure maintains `personal` schema database isolation; watch events append-only; zero user data deletion on merge. |
| `DEC-INFRA-INH-04` | **AI Proposal Pipeline Isolation** | ADR-004 | AI infrastructure operates strictly in `quality.ai_proposal_staging` (`CAT-6`); zero direct canonical write access. |
| `DEC-INFRA-INH-05` | **Pre-Acquisition Licensing Gate Enforcement** | DEC-ING-PRP-01 | Ingestion runtime enforces licensing check before executing provider requests. Web scraping strictly prohibited. |
| `DEC-INFRA-INH-06` | **Domain Authority Provenance Lineage** | DS-01, DEC-SRC-PRP-01/02 | Observability and audit logs preserve credits for approved domain authorities (KOBIS Primary Korean, TheTVDB Secondary TV). |
| `DEC-INFRA-INH-07` | **Metadata vs Media Rights Segregation** | DEC-ING-PRP-05 | Object storage media proxy caches HTTPS URLs; binary media blobs excluded from database; storage does not grant licensing. |
| `DEC-INFRA-INH-08` | **Three-Tier API Boundary Isolation** | DEC-API-PRP-02 | Runtime network isolates Public Client API (`/v1/`), Internal Admin API (`/internal/v1/`), and Provider Integration Boundary. |
| `DEC-INFRA-INH-09` | **PostgreSQL Physical Database Baseline** | DEC-PHYS-PRP-01..12 | Database runtime targets PostgreSQL 16+ with 5 logical schemas (`canonical`, `personal`, `ingestion`, `quality`, `audit`). |

---

### B. NEWLY APPROVED PROPOSAL SET (Historical Traceability: PROPOSED ──▶ APPROVED)

| Decision ID | Decision Title | Historical Transition | Scope of Conceptual Approval | Deferred Execution Scope |
|---|---|---|---|---|
| `DEC-INFRA-PRP-01` | **4-Tier Environment Model & Isolation** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | 4-tier model (`local`, `dev`, `staging`, `prod`) approved as operational boundary. | Physical environment provisioning & cloud accounts deferred (`DEC-INFRA-DEF-01`). |
| `DEC-INFRA-PRP-02` | **Independent Compute Workload Topology** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Separation into 8 discrete compute workloads approved. | Container orchestration & K8s deployment manifests deferred (`DEC-INFRA-DEF-02`). |
| `DEC-INFRA-PRP-03` | **PostgreSQL Primary / Replica Streaming Topology** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Multi-AZ Primary with Read Replica pool approved conceptually. | Database cloud instances & instance sizing deferred. |
| `DEC-INFRA-PRP-04` | **Distributed Cache / Rate-Limit Store Strategy** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Read-through caching for `CAT-1` metadata & rate-limit state store approved. Redis noted as candidate. | Physical cache technology & Redis key schemas deferred (`DEC-API-DEF-04`). |
| `DEC-INFRA-PRP-05` | **Asynchronous Queue Broker Topology & DLQ** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Dedicated task queues (`ingestion`, `quality`, `reconciliation`, `sync`, `dead_letter`) approved. | Queue broker technology standard remains OPEN (`DEC-INFRA-OPN-01`). |
| `DEC-INFRA-PRP-06` | **5-Zone Network Security Perimeter** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | 5-zone network security perimeter approved (Edge/CDN/WAF, DMZ, App, Worker, Data). | Specific cloud CDN, WAF, & VPC provisioning deferred (`DEC-INFRA-DEF-01`). |
| `DEC-INFRA-PRP-07` | **Prometheus / OpenTelemetry Observability Stack** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Prometheus metrics, JSON logging, & OpenTelemetry tracing approved conceptually. | Monitoring server deployment & dashboard creation deferred. |
| `DEC-INFRA-PRP-08` | **RPO < 5 Min / RTO < 1 Hr Recovery Target** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED WITH OWNER-REVIEWED TARGETS`** | RPO < 5 mins and RTO < 1 hr approved as current architectural recovery targets. | Documented as targets until operational testing; cloud backup target deferred (`DEC-PHYS-DEF-04`). |

---

### C. DEFERRED DECISIONS (Carried Forward & Postponed)

| Decision ID | Deferred Topic | Reason for Deferral | Target Phase |
|---|---|---|---|
| `DEC-INFRA-DEF-01` | **Cloud Infrastructure Provider & CDN Selection** | Vendor choice (AWS vs GCP vs Azure vs Cloudflare vs Self-Hosted) deferred. | Cloud Procurement Phase |
| `DEC-INFRA-DEF-02` | **Kubernetes Manifests & Terraform Scripting** | Infrastructure-as-code scripting prohibited in architecture phase. | Infrastructure Implementation Phase |
| `DEC-INFRA-DEF-03` | **CI/CD Pipeline Automation Scripting** | Pipeline YAML file creation (GitHub Actions / GitLab CI) deferred. | DevOps Implementation Phase |
| `DEC-API-DEF-02` | **Authentication Provider & OAuth Server Selection** | OAuth2 server technology selection deferred. | Security Implementation Phase |
| `DEC-API-DEF-03` | **API Gateway Technology Selection** | Gateway proxy technology (Kong vs Envoy vs NGINX) deferred. | Edge Infrastructure Phase |
| `DEC-API-DEF-04` | **Physical Cache Storage & Redis Key Schemas** | Fine-grained cache software selection (Redis vs Memcached) deferred. | Physical Cache Implementation Phase |
| `DEC-PHYS-DEF-02` | **Database Migration Tool Selection** | Migration tool (Flyway vs Liquibase vs Sqitch) deferred. | Database Infrastructure Phase |
| `DEC-PHYS-DEF-03` | **PostgreSQL Connection Pool Topology** | Connection pool technology (PgBouncer settings) deferred. | Deployment Phase |
| `DEC-PHYS-DEF-04` | **Backup / DR Cloud Infrastructure** | Backup cloud storage target selection deferred. | Operations Phase |

---

### D. OPEN QUESTIONS & BLOCKED DECISIONS

| Decision ID | Topic | Description & Barrier | Action Required |
|---|---|---|---|
| `DEC-INFRA-OPN-01` | **Queue Broker Technology Standard** | Evaluation between RabbitMQ (AMQP) vs Redis Streams vs NATS for asynchronous queue broker workload. | Queue workload benchmarking in implementation phase. |
| `DEC-INFRA-OPN-02` | **Multi-Region Read Replica Scale Topology** | Should read replicas be deployed across multiple geographical regions for global client latency optimization? | Global latency testing in mobile performance review phase. |
| `DEC-ING-OPN-02` | **Raw CAT-5 Payload Retention Policy** | Retention window for raw `CAT-5` payloads (indefinite storage vs 365-day cold archive) remains unfinalized. | Operational policy definition in storage planning phase. |
| `DEC-QUAL-OPN-02` | **Quarantine Retention Window** | Retention duration for quarantined invalid/ambiguous payloads before automated cleanup remains unfinalized. | Operational policy definition in storage planning phase. |
| `DEC-PHYS-OPN-01` | **Raw Payload Partition Granularity** | Should `ingestion.raw_payload_capture` use monthly or weekly range partitions based on initial ingest velocity? | Ingest volume benchmarking in implementation phase. |

---

## 3. Governance Summary Dashboard

```text
===============================================================================
CINEVAULT OS — INFRASTRUCTURE ARCHITECTURE V1 GOVERNANCE DASHBOARD
===============================================================================

DEC-INFRA-PRP-01   🟢 APPROVED
DEC-INFRA-PRP-02   🟢 APPROVED
DEC-INFRA-PRP-03   🟢 APPROVED
DEC-INFRA-PRP-04   🟢 APPROVED
DEC-INFRA-PRP-05   🟢 APPROVED
DEC-INFRA-PRP-06   🟢 APPROVED
DEC-INFRA-PRP-07   🟢 APPROVED
DEC-INFRA-PRP-08   🟢 APPROVED WITH OWNER-REVIEWED TARGETS

DEC-INFRA-DEF-01   🟡 DEFERRED
DEC-INFRA-DEF-02   🟡 DEFERRED
DEC-INFRA-DEF-03   🟡 DEFERRED

DEC-INFRA-OPN-01   🟡 OPEN
DEC-INFRA-OPN-02   🟡 OPEN

===============================================================================
FINAL ARCHITECTURE STATUS:
INFRASTRUCTURE ARCHITECTURE V1
APPROVED WITH DEFERRED INFRASTRUCTURE DECISIONS
===============================================================================
```

---
