# CineVault OS — Data Quality & Reconciliation Decision Log V1

**Document Type:** Data Quality & Reconciliation Architecture Strategy Decision Log  
**Status:** Post-Owner Approval Baseline (Approved)  
**Date:** 2026-08-08  
**Scope:** Architectural Decisions Introduced, Inherited, or Approved in `docs/DATA_QUALITY_RECONCILIATION_ARCHITECTURE_V1.md`  

---

## 1. Governance Overview

This Decision Log documents all architectural decisions associated with the CineVault OS Data Quality & Reconciliation Architecture V1.

Following formal Project Owner review, all newly proposed architectural decisions (`DEC-QUAL-PRP-01` through `DEC-QUAL-PRP-06`) have received **Formal Project Owner Approval** for their conceptual direction.

### Historical Lifecycle Transition
Decisions preserve full historical traceability:
```text
PROPOSED ──▶ OWNER REVIEW ──▶ APPROVED (Conceptual Architecture Baseline)
```

> [!IMPORTANT]
> **CONCEPTUAL APPROVAL VS. IMPLEMENTATION DEFERRAL**  
> Project Owner approval authorizes **architectural concepts only**. It does NOT authorize code implementation, ORM models, physical database tables, matching algorithms, fuzzy search code, ML models, background workers, queues, scrapers, or production reconciliation jobs. Detailed physical storage, DDL, algorithmic weights, and scoring formulas remain deferred to their respective target phases.

---

## 2. Decision Log Matrix

### A. APPROVED INHERITED DECISIONS

| Decision ID | Decision Title | Baseline Source | Summary of Approved Decision |
|---|---|---|---|
| `DEC-QUAL-INH-01` | **UUIDv7 Canonical Key Minting** | ADR-001 | Canonical identities created at promotion are generated UUIDv7s. External provider IDs are mappings (`TitleExternalId`). |
| `DEC-QUAL-INH-02` | **Title / Edition / Release Boundaries** | ADR-002 | Material content differences create Editions; distribution differences create Releases. Primary Edition invariant enforced. |
| `DEC-QUAL-INH-03` | **Personal Data Safety & Conflict Isolation** | ADR-003, ADR-004 | Entity merges and splits MUST NEVER alter or delete User Personal Data (`CAT-2`). Generates `PersonalDataConflict` or `UserSplitResolution` records. |
| `DEC-QUAL-INH-04` | **Domain-Specific Source Authority** | DS-01 | No universal provider. Authority is domain-scoped and rule-driven. |
| `DEC-QUAL-INH-05` | **Korean Cinema Primary Authority** | DEC-SRC-PRP-01 | KOBIS / KOFIC designated Primary Korean-Domain Authority in reconciliation engine. |
| `DEC-QUAL-INH-06` | **Secondary TV Authority** | DEC-SRC-PRP-02 | TheTVDB designated Secondary TV Authority for television catalog structure. |
| `DEC-QUAL-INH-07` | **Ingestion Match Taxonomy Baseline** | DEC-ING-PRP-04 | Reconciler adopts approved 6 match states (`MATCH_EXACT`, `MATCH_AMBIGUOUS`, `NO_MATCH`, `MERGE_CANDIDATE`, `SPLIT_CANDIDATE`, `REQUIRES_REVIEW`). |
| `DEC-QUAL-INH-08` | **Media Rights Isolation** | DEC-ING-PRP-05 | Structured metadata rights and media/image usage rights remain segregated governance dimensions. |
| `DEC-QUAL-INH-09` | **AI Proposal Governance** | ADR-004 | AI-generated outputs classified as `CAT-6` proposals; direct canonical write prohibited. |

---

### B. NEWLY APPROVED PROPOSAL SET (Historical Traceability: PROPOSED ──▶ APPROVED)

| Decision ID | Decision Title | Historical Transition | Scope of Conceptual Approval | Deferred Execution Scope |
|---|---|---|---|---|
| `DEC-QUAL-PRP-01` | **8-Layer Data Quality Verification Model** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | 8-layer verification sequence (Source, Payload, Schema, Field, Entity, Relationship, Cross-Source, Canonical Gate) approved. | Exact validation scripts, physical quarantine tables, and pipeline execution code remain `DEFERRED`. |
| `DEC-QUAL-PRP-02` | **10-Dimension Quality Assessment Framework** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | 10 conceptual quality dimensions (Completeness, Validity, Consistency, Uniqueness, Accuracy, Timeliness, Provenance, Rights, Integrity, Conformity) approved. Universal opaque quality score rejected. | Numerical scoring formulas remain `DEFERRED`. |
| `DEC-QUAL-PRP-03` | **Matching Signals Taxonomy** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | 4 signal ranks (`STRONG`, `SUPPORTING`, `WEAK`, `MISLEADING`) approved. | Exact signal weighting and algorithmic scoring thresholds remain `DEFERRED` (`DEC-QUAL-DEF-03`). |
| `DEC-QUAL-PRP-04` | **False-Match Prevention Rules** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Explicit protection against false matches for remakes, adaptations, alternate cuts, OVAs, specials, and editions approved. | Matching algorithms, string similarity code, and ML models remain prohibited/`DEFERRED`. |
| `DEC-QUAL-PRP-05` | **Decision Evidence Lineage Model** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Immutable evidence record ("Why CineVault believes this fact") for every promoted attribute approved. Opaque "AI decided this" canonical outcomes strictly prohibited. | Physical DDL for evidence storage remains `DEFERRED`. |
| `DEC-QUAL-PRP-06` | **Quality Failure & Quarantine Taxonomy** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | 7 conceptual failure outcomes (`REJECT_LICENSE`, `REJECT_SYNTAX`, `REJECT_SCHEMA`, `QUARANTINE_INVALID`, `QUARANTINE_GRAPH`, `FLAG_CONFLICT`, `ACCEPT_WITH_WARNING`) approved. | Physical quarantine storage and automated purge implementations remain `DEFERRED`. |

---

### C. DEFERRED DECISIONS (Intentionally Postponed)

| Decision ID | Deferred Topic | Reason for Deferral | Target Phase |
|---|---|---|---|
| `DEC-QUAL-DEF-01` | **Physical Quality & Quarantine Staging DDL** | Database schema, DDL, table creation, and staging indexing prohibited in architecture phase. | Physical Database Design Phase |
| `DEC-QUAL-DEF-02` | **Automated Matching Algorithms & ML Models** | Algorithmic code, string similarity code, and ML models prohibited in architecture phase. | Reconciliation Implementation Phase |
| `DEC-QUAL-DEF-03` | **Numerical Confidence & Scoring Formulas** | Postponed per `DEC-ING-DEF-03`; exact scoring weights (e.g., 0.85 Jaro-Winkler) require empirical dataset calibration. | Algorithmic Calibration Phase |
| `DEC-QUAL-DEF-04` | **Control Room Curation UI Dashboard** | User interface implementation deferred. | Control Room UI Phase |
| `DEC-QUAL-DEF-05` | **Automatic Entity Merge & Split Rules** | High-risk entity merges/splits require manual curation until confidence thresholds are empirically validated. | Reconciliation Review Phase |

---

### D. OPEN QUESTIONS & BLOCKED DECISIONS

| Decision ID | Topic | Description & Barrier | Action Required |
|---|---|---|---|
| `DEC-QUAL-OPN-01` | **Fuzzy Matching Calibration Dataset** | What benchmark catalog dataset will be used to calibrate fuzzy matching confidence thresholds? | Selection of reference benchmark corpus in calibration phase. |
| `DEC-QUAL-OPN-02` | **Quarantine Retention & Purge Policy** | Retention duration for quarantined invalid/ambiguous payloads before automated cleanup. | Operational policy definition in storage planning phase. |

---

## 3. Governance Summary Dashboard

```text
===============================================================================
CINEVAULT OS — DATA QUALITY & RECONCILIATION ARCHITECTURE V1 GOVERNANCE DASHBOARD
===============================================================================

DEC-QUAL-PRP-01   🟢 APPROVED  (8-Layer Data Quality Verification Model)
DEC-QUAL-PRP-02   🟢 APPROVED  (10-Dimension Quality Assessment Framework)
DEC-QUAL-PRP-03   🟢 APPROVED  (Matching Signals Taxonomy)
DEC-QUAL-PRP-04   🟢 APPROVED  (False-Match Prevention Rules)
DEC-QUAL-PRP-05   🟢 APPROVED  (Decision Evidence Lineage Model)
DEC-QUAL-PRP-06   🟢 APPROVED  (Quality Failure & Quarantine Taxonomy)

DEC-QUAL-DEF-01   🟡 DEFERRED  (Physical Quality / Quarantine Staging DDL)
DEC-QUAL-DEF-02   🟡 DEFERRED  (Automated Matching Algorithms / ML Models)
DEC-QUAL-DEF-03   🟡 DEFERRED  (Numerical Confidence / Scoring Formulas)
DEC-QUAL-DEF-04   🟡 DEFERRED  (Control Room Curation UI Dashboard)
DEC-QUAL-DEF-05   🟡 DEFERRED  (Automatic Entity Merge / Split Rules)

DEC-QUAL-OPN-01   🟡 OPEN      (Reference Benchmark Catalog Corpus)
DEC-QUAL-OPN-02   🟡 OPEN      (Quarantine Retention Window & Purge Policy)

===============================================================================
FINAL ARCHITECTURE STATUS: DATA QUALITY & RECONCILIATION ARCHITECTURE V1 APPROVED WITH DEFERRED QUALITY DECISIONS
===============================================================================
```

---
