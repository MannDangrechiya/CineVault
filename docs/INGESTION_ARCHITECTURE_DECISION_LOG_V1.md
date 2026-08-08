# CineVault OS — Ingestion Architecture Decision Log V1

**Document Type:** Ingestion Architecture Strategy Decision Log  
**Status:** Post-Owner Approval Baseline (Approved)  
**Date:** 2026-08-08  
**Scope:** Architectural Decisions Introduced, Inherited, or Approved in `docs/INGESTION_ARCHITECTURE_V1.md`  

---

## 1. Governance Overview

This Decision Log documents all architectural decisions associated with the CineVault OS Data Ingestion Architecture V1.

Following formal Project Owner review, all newly proposed architectural decisions (`DEC-ING-PRP-01` through `DEC-ING-PRP-06`) have received **Formal Project Owner Approval** for their conceptual direction.

### Historical Lifecycle Transition
Decisions preserve full historical traceability:
```text
PROPOSED ──▶ OWNER REVIEW ──▶ APPROVED (Conceptual Architecture Baseline)
```

> [!IMPORTANT]
> **CONCEPTUAL APPROVAL VS. IMPLEMENTATION DEFERRAL**  
> Project Owner approval authorizes **architectural concepts only**. It does NOT authorize code implementation, ORM models, physical database tables, background workers, queues, scrapers, or ETL jobs. Detailed physical storage, DDL, algorithmic thresholds, and queue orchestration remain deferred to their respective target phases.

---

## 2. Decision Log Matrix

### A. APPROVED INHERITED DECISIONS

| Decision ID | Decision Title | Baseline Source | Summary of Approved Decision |
|---|---|---|---|
| `DEC-ING-INH-01` | **UUIDv7 Canonical Key Minting** | ADR-001 | Canonical identities created at promotion are generated UUIDv7s. External provider IDs are mappings (`TitleExternalId`). |
| `DEC-ING-INH-02` | **Title / Edition / Release Invariants** | ADR-002 | Primary Edition (`is_primary = true`) mandatory for all promoted Titles. Distribution differences do not create new Editions. |
| `DEC-ING-INH-03` | **Personal Data Protection Isolation** | ADR-003, ADR-004 | Ingestion pipeline and provider deletions MUST NEVER mutate, overwrite, or delete User Personal Data (CAT-2). |
| `DEC-ING-INH-04` | **Domain-Specific Source Authority** | DS-01 | No single universal global provider. Authority is domain-scoped and rule-driven. |
| `DEC-ING-INH-05` | **TMDb Licensing Gate Requirement** | DS-02 | Commercial license verification mandatory before TMDb production activation. |
| `DEC-ING-INH-06` | **AniList Restricted Ingestion** | DS-03 | Bulk canonical ingestion prohibited; on-demand lookup/enrichment permitted. |
| `DEC-ING-INH-07` | **IMDb Public Dataset Exclusion** | DS-04 | IMDb public non-commercial datasets permanently blocked at Licensing Gate. |
| `DEC-ING-INH-08` | **Scraping Prohibition & JustWatch** | DS-05 | Web scraping public sites strictly prohibited. JustWatch conditional on partner contract. |
| `DEC-ING-INH-09` | **KOBIS Primary Korean Authority** | DEC-SRC-PRP-01 | Designated Primary Korean-Domain Authority in reconciliation engine. |
| `DEC-ING-INH-10` | **TheTVDB Secondary TV Authority** | DEC-SRC-PRP-02 | Designated Secondary TV Authority for television catalog structure. |
| `DEC-ING-INH-11` | **AI Proposal Classification** | ADR-004 | AI-generated outputs classified as CAT-6 proposals; direct canonical write prohibited. |

---

### B. NEWLY APPROVED PROPOSAL SET (Historical Traceability: PROPOSED ──▶ APPROVED)

| Decision ID | Decision Title | Historical Transition | Scope of Conceptual Approval | Deferred Execution Scope |
|---|---|---|---|---|
| `DEC-ING-PRP-01` | **Pre-Acquisition Source Authorization & Licensing Gate** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Pre-acquisition 4-check authorization gate approved. Verifies terms prior to payload fetching. | Production provider access remains subject to actual licensing/access verification. |
| `DEC-ING-PRP-02` | **Immutable Raw Payload Capture Boundary (CAT-5)** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Immutable staging boundary for external payloads with SHA-256 checksums approved. | Physical storage design, DDL, indexing, retention policy, and purge/archive implementation remain `DEFERRED` (`DEC-ING-DEF-01`). |
| `DEC-ING-PRP-03` | **Provider-Neutral Intermediate Models** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Normalization/intermediate layer translating provider schemas prior to matching approved. | ORM models, implementation classes, and adapter code remain prohibited/`DEFERRED`. |
| `DEC-ING-PRP-04` | **Identity Resolution Match Taxonomy** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Conceptual match states (`MATCH_EXACT`, `MATCH_AMBIGUOUS`, `NO_MATCH`, `MERGE_CANDIDATE`, `SPLIT_CANDIDATE`, `REQUIRES_REVIEW`) approved. | Confidence thresholds, fuzzy algorithms, weighting, scoring, automatic merge/split rules remain `DEFERRED` (`DEC-ING-DEF-03`). |
| `DEC-ING-PRP-05` | **Metadata vs Media Rights Isolation Pipeline** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Separate governance dimensions for structured metadata vs image/media rights approved. | Media acquisition implementation, CDN proxying, and downloader code remain prohibited/`DEFERRED`. |
| `DEC-ING-PRP-06` | **Ingestion Lifecycle State Machine** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Conceptual 12-state ingestion lifecycle (`DISCOVERED` to `PROMOTED_CANONICAL`) approved. | Physical orchestration mechanisms (background workers, queues, schedulers, jobs) remain `DEFERRED` (`DEC-ING-DEF-02`). |

---

### C. DEFERRED DECISIONS (Intentionally Postponed)

| Decision ID | Deferred Topic | Reason for Deferral | Target Phase |
|---|---|---|---|
| `DEC-ING-DEF-01` | **Physical Raw Payload Database DDL** | Database schema, DDL, table creation, and storage indexing prohibited in architecture phase. | Physical Database Design Phase |
| `DEC-ING-DEF-02` | **API Rate-Limiter & Throttling Queues** | Network infrastructure code, background workers, and schedulers prohibited in architecture phase. | Ingestion Pipeline Phase |
| `DEC-ING-DEF-03` | **Fuzzy Matching Confidence Threshold Tuning** | Algorithmic tuning, scoring weights, and merge/split rules deferred. | Data Quality / Reconciliation Phase |
| `DEC-ING-DEF-04` | **Control Room Curation UI Workflows** | User interface and curation dashboard implementation deferred. | Control Room UI Phase |

---

### D. OPEN QUESTIONS & BLOCKED DECISIONS

| Decision ID | Topic | Description & Barrier | Action Required |
|---|---|---|---|
| `DEC-ING-OPN-01` | **TMDb Commercial Agreement Timeline** | TMDb production ingestion remains blocked (`DS-02`) until commercial agreement is signed. | Project Owner execution of TMDb commercial agreement. |
| `DEC-ING-OPN-02` | **Raw Capture Archival Policy** | Retention window for raw CAT-5 payloads (indefinite storage vs 365-day cold archive) remains unfinalized. | Operational policy definition in storage planning phase. |

---

## 3. Governance Summary Dashboard

```text
===============================================================================
CINEVAULT OS — INGESTION ARCHITECTURE V1 GOVERNANCE DASHBOARD
===============================================================================

DEC-ING-PRP-01   🟢 APPROVED  (Pre-Acquisition Source Authorization Gate)
DEC-ING-PRP-02   🟢 APPROVED  (Immutable Raw Payload Capture Boundary)
DEC-ING-PRP-03   🟢 APPROVED  (Provider-Neutral Intermediate Models)
DEC-ING-PRP-04   🟢 APPROVED  (Identity Resolution Match Taxonomy)
DEC-ING-PRP-05   🟢 APPROVED  (Metadata vs Media Rights Isolation)
DEC-ING-PRP-06   🟢 APPROVED  (Ingestion Lifecycle State Machine)

DEC-ING-DEF-01   🟡 DEFERRED  (Physical Raw Staging Table DDL)
DEC-ING-DEF-02   🟡 DEFERRED  (API Rate-Limiter / Throttling Queues)
DEC-ING-DEF-03   🟡 DEFERRED  (Fuzzy Matching Confidence Threshold Tuning)
DEC-ING-DEF-04   🟡 DEFERRED  (Control Room Curation UI Workflows)

DEC-ING-OPN-01   🟡 OPEN      (TMDb Commercial Agreement Timeline)
DEC-ING-OPN-02   🟡 OPEN      (Raw Capture Archival & Retention Policy)

===============================================================================
FINAL ARCHITECTURE STATUS: INGESTION ARCHITECTURE V1 APPROVED WITH DEFERRED ITEMS
===============================================================================
```

---
