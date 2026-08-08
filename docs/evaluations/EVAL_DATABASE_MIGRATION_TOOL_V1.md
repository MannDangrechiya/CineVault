# CineVault OS — Technology Evaluation: Database Migration Tool V1

**Document Type:** Technology Evaluation & Selection Proposal  
**Decision ID:** `DEC-PHYS-DEF-02` — Database Migration Tool Selection  
**Status:** Evaluation Complete — Awaiting Owner Approval  
**Date:** 2026-08-08  
**Selected Technology Recommendation:** Flyway (Apache License 2.0 — Redgate Open Source Community)  
**Alternative Candidate:** Atlas (Apache License 2.0 — Ariga)  
**Governance State:** PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED  
**Implementation Authorization:** NOT AUTHORIZED  

---

## 1. Decision Under Evaluation

* **Decision ID:** `DEC-PHYS-DEF-02`
* **Topic:** Database Migration Tool Selection
* **Originating Baseline:** Physical Database Design V1 (`docs/PHYSICAL_DATABASE_DESIGN_V1.md`, `DEC-PHYS-PRP-01`)
* **Current Governance State:** `DEFERRED` → `PROPOSED` (Awaiting Owner Review)
* **Objective:** Select a version-controlled database schema migration tool to execute, track, and validate DDL migration scripts across CineVault OS's 5 physical PostgreSQL schemas (`core`, `catalog`, `ingestion`, `quality`, `personal`), enforce transaction isolation, and support automated pre-deployment schema validation.

---

## 2. Canonical Architecture Requirements

Derived from locked baseline specifications (`Physical Database Design V1`, `Security Architecture V1`, `Infrastructure Architecture V1`):

```text
┌───────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────┐
│ Feature / Capability Requirement      │ Architectural Specification               │ Canonical Source Reference                │
├───────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. 5-Schema DDL Management            │ Versioning core, catalog, ingestion, quality, personal schemas│ Physical DB V1 (DEC-PHYS-PRP-01)│
│ 2. Plain SQL Migration File Support   │ Native versioned `.sql` files (`V1__...sql`)│ Physical DB V1 (DEC-PHYS-DEF-02)          │
│ 3. Migration History & Checksum Auth  │ Immutability verification of past DDL scripts│ Physical DB V1 (DEC-PHYS-DEF-02)        │
│ 4. Transactional DDL Executions      │ Postgres transactional DDL rollbacks on error│ Physical DB V1 (DEC-PHYS-PRP-01)         │
│ 5. CI/CD & Local Emulation Support    │ CLI runner in Docker container & CI pipeline│ Infrastructure V1 (DEC-INFRA-DEF-03)      │
└───────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Architecture Dependencies

* **Database Engine:** PostgreSQL 16+ (`DEC-PHYS-DEF-01`).
* **Connection Pool:** PgBouncer (`DEC-PHYS-DEF-03`) - migrations bypass pooler via direct admin DDL port.
* **CI/CD Pipeline:** GitHub Actions / Runner (`DEC-INFRA-DEF-03`) for automated dry-run linting.

---

## 4. Candidate Technologies Identified

Four candidate migration engines were evaluated:

1. **Flyway (Apache 2.0 Community Edition):** Standard versioned SQL file migration runner (`V1__init.sql`).
2. **Liquibase (Apache 2.0 Community Edition):** XML/YAML/JSON/SQL changelog migration engine.
3. **Atlas (Apache 2.0 / Ariga):** Declarative schema-as-code engine with automated migration linting.
4. **Sqitch (MIT / Perl):** Language-agnostic CLI tool using plain SQL scripts and target plan files.

---

## 5. Candidate Evaluation & Feature Compatibility Matrix

```text
┌───────────────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Dimension / Feature                   │ 1. Flyway         │ 2. Liquibase      │ 3. Atlas          │ 4. Sqitch         │
├───────────────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ License Type                          │ Apache 2.0 (OSI)  │ Apache 2.0 (OSI)  │ Apache 2.0 (OSI)  │ MIT               │
│ Migration Paradigm                    │ Imperative SQL    │ Imperative / DSL  │ Declarative / Diff│ Imperative SQL    │
│ Plain SQL Script Support              │ EXCELLENT         │ GOOD (Formatted)  │ EXCELLENT         │ EXCELLENT         │
│ Multi-Schema PostgreSQL Support       │ NATIVE (5 Schemas)│ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │
│ Checksum Hash Integrity Verification │ NATIVE            │ NATIVE            │ NATIVE            │ NATIVE            │
│ Learning Curve                        │ VERY LOW          │ MODERATE          │ MODERATE          │ LOW               │
│ CI/CD Container Image Availability    │ OFFICIAL DOCKER   │ OFFICIAL DOCKER   │ OFFICIAL DOCKER   │ COMMUNITY DOCKER  │
└───────────────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 6. Detailed Evaluation Dimensions

### Functional Compatibility & DX
Flyway operates directly on standard SQL scripts (`V1__create_core_schema.sql`, `V2__create_catalog_schema.sql`). It creates a `flyway_schema_history` table to track execution state and MD5 checksums. It supports PostgreSQL's native transactional DDL (`BEGIN ... ROLLBACK`), ensuring that if a DDL migration fails halfway through execution, PostgreSQL cleanly rolls back the entire migration transaction without leaving partial DDL changes.

### Security & Privacy
* Migrations run under a dedicated, short-lived DDL admin database user, separate from application runtime DML users (`app_api_user`, `app_worker_user`).
* Zero application data or secrets are stored in migration scripts.

---

## 7. Cost Model & 36-Month TCO

* **Software Cost:** $0 (Flyway Community Edition under Apache 2.0).
* **Infrastructure Cost:** $0 (Runs as ephemeral container job during deployment).
* **TCO Summary (36 Months):** $0.

---

## 8. Vendor Lock-In & Portability Analysis

* **Script Portability:** All migrations are standard PostgreSQL DDL SQL scripts. If Flyway is ever replaced, the DDL files remain 100% standard SQL usable by any PostgreSQL client (`psql`).
* **Lock-In Depth:** **LOW** (Standard SQL scripts).

---

## 9. Risk Assessment & Mitigations

* **Risk:** Enterprise feature gating in Flyway (e.g., advanced dry-run reports).
  * **Mitigation:** Rely exclusively on standard Open-Source SQL migration files and test migrations against local Postgres container instances before committing.

---

## 10. Recommended Technology Selection

* **Primary Recommendation:** **Flyway Community Edition (Apache License 2.0)**
* **Alternative Candidate:** **Atlas (Apache License 2.0 — Ariga)**
* **Justification:** Flyway provides the lowest operational complexity, native support for multi-schema PostgreSQL transactional DDL, direct SQL file versioning, and zero software cost.

---

## 11. Final Governance Status

Evaluation:
COMPLETE

Recommendation:
Flyway Community Edition (Apache License 2.0)

Governance:
PROPOSED TECHNOLOGY RECOMMENDATION

Approval:
OWNER REVIEW REQUIRED

Technology Approved:
NO

Implementation:
NOT AUTHORIZED
