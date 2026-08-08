# CineVault OS — Physical Database Design Decision Log V1

**Document Type:** Physical Database Architecture Strategy Decision Log  
**Status:** Post-Owner Approval Baseline (Approved)  
**Date:** 2026-08-08  
**Scope:** Architectural Decisions Introduced, Inherited, or Approved in `docs/PHYSICAL_DATABASE_DESIGN_V1.md`  

---

## 1. Governance Overview

This Decision Log documents all architectural decisions associated with the CineVault OS Physical Database Design V1.

Following formal Project Owner review, all twelve proposed physical database decisions (`DEC-PHYS-PRP-01` through `DEC-PHYS-PRP-12`) have received **Formal Project Owner Approval** for their conceptual/architectural design direction.

### Historical Lifecycle Transition
Decisions preserve full historical traceability:
```text
PROPOSED ──▶ OWNER REVIEW ──▶ APPROVED (Conceptual Architecture Baseline)
```

> [!IMPORTANT]
> **CONCEPTUAL APPROVAL VS. IMPLEMENTATION DEFERRAL**  
> Project Owner approval authorizes **architectural concepts only**. It does NOT authorize SQL file creation, DDL execution, database migrations, PostgreSQL database provisioning, ORM models, database client repositories, or production infrastructure. Detailed physical implementation remains deferred to respective target phases.

---

## 2. Decision Log Matrix

### A. APPROVED INHERITED DOMAIN CONSTRAINTS

| Decision ID | Inherited Domain Constraint | Baseline Source | Summary of Inherited Constraint |
|---|---|---|---|
| `DEC-PHYS-INH-01` | **UUIDv7 Canonical Identity Constraint** | ADR-001 | Canonical entity primary keys use 128-bit native UUIDv7 keys. External provider IDs are mappings only. (Physical PostgreSQL type & generation strategy are `PROPOSED` under `DEC-PHYS-PRP-02`). |
| `DEC-PHYS-INH-02` | **Content Hierarchy Constraint** | ADR-002 | Physical structure mirrors `Title -> Edition -> Release` and `Title -> Season -> Episode`. Primary Edition invariant enforced. (Partial index implementation is `PROPOSED` under `DEC-PHYS-PRP-09`). |
| `DEC-PHYS-INH-03` | **Personal Data Safety & Isolation Constraint** | ADR-003, ADR-004 | User personal data must remain isolated and protected. WatchEvents append-only. Merges/splits generate conflict rows. (Exact `personal` schema name is `PROPOSED` under `DEC-PHYS-PRP-01`). |
| `DEC-PHYS-INH-04` | **Durable Offline Outbox Requirement** | ADR-004, DEC-API-PRP-07 | Offline mutations require durable outbox staging and conflict handling. (Exact table `personal.sync_outbox_mutation` is `PROPOSED` under `DEC-PHYS-PRP-10`). |
| `DEC-PHYS-INH-05` | **Domain Authority & Provenance Constraint** | DS-01, DEC-SRC-PRP-01/02, DEC-QUAL-PRP-05 | Decision evidence lineage required crediting approved authorities. (Exact table `audit.attribute_evidence_lineage` is `PROPOSED` under `DEC-PHYS-PRP-05`). |
| `DEC-PHYS-INH-06` | **Immutable Raw Payload Capture Boundary** | DEC-ING-PRP-02 | Raw external payloads captured immutably. (Exact table `ingestion.raw_payload_capture`, JSONB payload, SHA-256 checksum are `PROPOSED` under `DEC-PHYS-PRP-03`). |
| `DEC-PHYS-INH-07` | **Quality Failure & Quarantine Governance** | DEC-QUAL-PRP-06 | Failed payloads staged in quarantine covering 7 failure categories. (Exact table `quality.quarantine_record` and JSONB structure are `PROPOSED` under `DEC-PHYS-PRP-04`). |
| `DEC-PHYS-INH-08` | **Metadata vs Media Rights Segregation** | DEC-ING-PRP-05 | Metadata rights and media rights remain separate governance dimensions. (HTTPS URL strings / binary media exclusion are `PROPOSED` under `DEC-PHYS-PRP-11`). |
| `DEC-PHYS-INH-09` | **AI Proposal Non-Canonical Constraint** | ADR-004 | AI-generated data cannot directly become canonical truth. (Exact table `quality.ai_proposal_staging` is `PROPOSED` under `DEC-PHYS-PRP-12`). |

---

### B. NEWLY APPROVED PROPOSAL SET (Historical Traceability: PROPOSED ──▶ APPROVED)

| Decision ID | Decision Title | Historical Transition | Scope of Conceptual Approval | Deferred Execution Scope |
|---|---|---|---|---|
| `DEC-PHYS-PRP-01` | **5-Schema Logical PostgreSQL Organization** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | 5-schema logical structure (`canonical`, `personal`, `ingestion`, `quality`, `audit`) approved as architectural boundary. | Physical schema DDL creation deferred (`DEC-PHYS-DEF-01`). |
| `DEC-PHYS-PRP-02` | **PostgreSQL `uuid` Type & UUIDv7 Generation Strategy** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | PostgreSQL `uuid` approved as physical representation for UUIDv7 primary keys. | Specific UUIDv7 extension, DB function, or library selection deferred to implementation. |
| `DEC-PHYS-PRP-03` | **Raw Payload SHA-256 & JSONB Staging Table** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Conceptual staging of raw payloads via `jsonb` and SHA-256 hex string approved (`DEC-ING-DEF-01`). | Actual DDL execution blocked; retention governed by `DEC-ING-OPN-02`. |
| `DEC-PHYS-PRP-04` | **7-Failure Category Quarantine Table** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Physical quarantine storage for 7 failure categories approved (`DEC-QUAL-DEF-01`). | Retention period unfinalized (`DEC-QUAL-OPN-02` remains OPEN); DDL execution blocked. |
| `DEC-PHYS-PRP-05` | **Operational Audit & Evidence Lineage Tables** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Physical structures for audit history and evidence lineage approved. | Exact DDL remains implementation work. |
| `DEC-PHYS-PRP-06` | **Tombstone & `canonical.identity_redirect` Structure** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Physical design for `canonical.identity_redirect` approved for conceptual entity `IdentityRedirect`. | Identity history preserved; historical reference destruction prohibited. |
| `DEC-PHYS-PRP-07` | **Declarative Time-Range Table Partitioning** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED WITH DEFERRED GRANULARITY`** | Declarative RANGE partitioning strategy approved for `watch_event`, `raw_payload_capture`, and `audit_log`. | Partition granularity remains OPEN (`DEC-PHYS-OPN-01`); partition creation blocked. |
| `DEC-PHYS-PRP-08` | **Role-Based Schema Security Topology** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Conceptual role separation (`cinevault_app`, `cinevault_ingest`, `cinevault_admin`, `cinevault_analytics`) approved. | Exact GRANTs, credentials, auth, and network policies deferred. |
| `DEC-PHYS-PRP-09` | **Partial Unique Index Primary Edition Protection** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED WITH INDEX FINALIZATION DEFERRED`** | Partial unique index design direction for single Primary Edition per Title approved. | Actual index creation blocked by `DEC-PHYS-DEF-05`. |
| `DEC-PHYS-PRP-10` | **Offline Sync Outbox Physical Table Structure** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Physical storage direction for `personal.sync_outbox_mutation` approved. | Serialization protocol remains deferred (`DEC-API-DEF-05`). |
| `DEC-PHYS-PRP-11` | **Rights-Aware Media URL Storage Strategy** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Physical separation of structured metadata and binary media approved. | Storing media URL does NOT grant media rights; access subject to licensing. |
| `DEC-PHYS-PRP-12` | **AI Proposal Staging Table Structure** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Physical isolation table `quality.ai_proposal_staging` approved. | AI proposals non-canonical; direct write path to canonical storage prohibited. |

---

### C. DEFERRED DECISIONS (Intentionally Postponed)

| Decision ID | Deferred Topic | Reason for Deferral | Target Phase |
|---|---|---|---|
| `DEC-PHYS-DEF-01` | **Physical DDL Script Files (`.sql`)** | DDL creation prohibited in architecture phase. | Database Implementation Phase |
| `DEC-PHYS-DEF-02` | **Database Migration Tool Selection** | Migration tooling (Flyway vs Liquibase vs Sqitch) deferred. | Database Infrastructure Phase |
| `DEC-PHYS-DEF-03` | **PostgreSQL Connection Pool Topology** | Connection pooling (PgBouncer settings) deferred. | Infrastructure Deployment Phase |
| `DEC-PHYS-DEF-04` | **Backup & Disaster Recovery Infrastructure** | Backup cloud infrastructure selection deferred. | Operations Phase |
| `DEC-PHYS-DEF-05` | **Fine-Grained Physical Index Benchmarking** | Fine-grained index creation deferred until physical query benchmarking. | Database Implementation Phase |
| `DEC-ING-DEF-02` | **API Rate-Limiter / Throttling Queues** | Carried forward from Ingestion Architecture. | Ingestion Pipeline Phase |
| `DEC-API-DEF-05` | **Sync Payload Serialization Protocol** | Carried forward from API Specification. | Offline Sync Implementation Phase |

---

### D. OPEN QUESTIONS & BLOCKED DECISIONS

| Decision ID | Topic | Description & Barrier | Action Required |
|---|---|---|---|
| `DEC-ING-OPN-02` | **Raw CAT-5 Payload Retention Policy** | Retention window for raw `CAT-5` payloads (indefinite storage vs 365-day cold archive) remains unfinalized. | Operational policy definition in storage planning phase. |
| `DEC-QUAL-OPN-02` | **Quarantine Retention Window** | Retention duration for quarantined invalid/ambiguous payloads before automated cleanup remains unfinalized. | Operational policy definition in storage planning phase. |
| `DEC-PHYS-OPN-01` | **Raw Payload Partition Granularity** | Should `ingestion.raw_payload_capture` use monthly or weekly range partitions based on initial ingest velocity? | Ingest volume benchmarking in implementation phase. |

---

## 3. Governance Summary Dashboard

```text
===============================================================================
CINEVAULT OS — PHYSICAL DATABASE DESIGN V1 GOVERNANCE DASHBOARD
===============================================================================

DEC-PHYS-PRP-01   🟢 APPROVED
DEC-PHYS-PRP-02   🟢 APPROVED
DEC-PHYS-PRP-03   🟢 APPROVED
DEC-PHYS-PRP-04   🟢 APPROVED
DEC-PHYS-PRP-05   🟢 APPROVED
DEC-PHYS-PRP-06   🟢 APPROVED
DEC-PHYS-PRP-07   🟢 APPROVED / GRANULARITY DEFERRED
DEC-PHYS-PRP-08   🟢 APPROVED
DEC-PHYS-PRP-09   🟢 APPROVED / INDEX FINALIZATION DEFERRED
DEC-PHYS-PRP-10   🟢 APPROVED
DEC-PHYS-PRP-11   🟢 APPROVED
DEC-PHYS-PRP-12   🟢 APPROVED

DEC-PHYS-DEF-01   🟡 DEFERRED
DEC-PHYS-DEF-02   🟡 DEFERRED
DEC-PHYS-DEF-03   🟡 DEFERRED
DEC-PHYS-DEF-04   🟡 DEFERRED
DEC-PHYS-DEF-05   🟡 DEFERRED

DEC-ING-OPN-02    🟡 OPEN
DEC-QUAL-OPN-02   🟡 OPEN
DEC-PHYS-OPN-01   🟡 OPEN

===============================================================================
FINAL ARCHITECTURE STATUS:
PHYSICAL DATABASE DESIGN V1
APPROVED WITH DEFERRED PHYSICAL DECISIONS
===============================================================================
```

---
