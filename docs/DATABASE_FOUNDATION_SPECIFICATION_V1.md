# CineVault OS — Database Foundation Specification V1 (Phase 1)

**Document Type:** Database Implementation & Infrastructure Foundation Specification  
**Status:** IMPLEMENTED & VALIDATED  
**Phase:** 1 — Database Foundation  
**Date:** 2026-08-08  
**Approved Database Stack:** PostgreSQL 16+, Flyway Community Edition, PgBouncer  

---

## 1. Overview & Architecture Compliance

The **CineVault OS Database Foundation** implements the PostgreSQL physical database specification (`docs/PHYSICAL_DATABASE_DESIGN_V1.md`) using **Flyway Community Edition** as the single canonical migration authority and **PgBouncer** as the local connection pooler.

### Core Architectural Invariants Enforced
1. **Flyway Migration Authority:** All database DDL changes, schema definitions, constraints, indexes, roles, and synthetic seed data are managed exclusively through versioned Flyway migrations in `sql/migrations/`.
2. **UUIDv7 Canonical Identity (ADR-001):** Native PostgreSQL `uuid` primary keys across all canonical tables generated via internal `generate_uuid_v7()` function.
3. **5-Schema Partitioning (DEC-PHYS-PRP-01):** Logical separation into `canonical`, `personal`, `ingestion`, `quality`, and `audit` schemas.
4. **Personal Data Isolation (ADR-003, ADR-004):** `CAT-2` user personal data is isolated in the `personal` schema with zero foreign keys referencing raw ingestion tables.
5. **AI Write Boundary (ADR-004):** AI proposals (`CAT-6`) stage in `quality.ai_proposal_staging`. Physical RBAC (`cinevault_ingest`) prevents direct write access to `canonical` schema tables.
6. **PgBouncer Transaction Pooling:** Multiplexes local database connections in transaction mode (`pool_mode = transaction`).

---

## 2. Flyway Migration Inventory & Migration Chain

```text
┌──────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────┬─────────────────────────────┐
│ Version / File                               │ Description / Authority                                                │ Status                      │
├──────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┼─────────────────────────────┤
│ `V1.0__create_extensions_and_functions.sql` │ Installs `uuid-ossp`, `pg_trgm`, `citext`; creates `generate_uuid_v7()`│ VALIDATED                   │
│ `V1.1__create_logical_schemas.sql`           │ Creates `canonical`, `personal`, `ingestion`, `quality`, `audit`       │ VALIDATED                   │
│ `V1.2__create_canonical_tables.sql`          │ Creates 37 canonical domain tables (`title`, `edition`, `credit`, etc.)│ VALIDATED                   │
│ `V1.3__create_personal_tables.sql`           │ Creates 10 personal data tables (`watch_event`, `sync_outbox`, etc.)   │ VALIDATED                   │
│ `V1.4__create_ingestion_tables.sql`          │ Creates raw staging tables (`raw_payload_capture`, `checkpoint`)       │ VALIDATED                   │
│ `V1.5__create_quality_tables.sql`            │ Creates quarantine & AI staging tables (`ai_proposal_staging`, etc.)   │ VALIDATED                   │
│ `V1.6__create_audit_tables.sql`              │ Creates audit log & attribute evidence lineage tables                  │ VALIDATED                   │
│ `V1.7__create_indexes_and_constraints.sql`   │ Partial unique indexes, GIN trgm search, GIN jsonb path indexes        │ VALIDATED                   │
│ `V1.8__create_database_roles.sql`            │ Least-privilege roles (`cinevault_app`, `ingest`, `admin`, `analytics`)│ VALIDATED                   │
│ `R__seed_development_taxonomy.sql`           │ Repeatable synthetic seed data (DEVELOPMENT ONLY)                      │ VALIDATED                   │
└──────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────┴─────────────────────────────┘
```

---

## 3. Local Development Workflows & Bootstrap Commands

### Local Container Startup
```powershell
# Start local infrastructure stack (PostgreSQL, Flyway, PgBouncer, etc.)
docker compose up -d postgres flyway pgbouncer
```

### Running Migration Checks & Hygiene Verification
```powershell
# Run repository hygiene and secret scanner audit
powershell -ExecutionPolicy Bypass -File .\scripts\check-hygiene.ps1

# Run database foundation validation suite
powershell -ExecutionPolicy Bypass -File .\scripts\validate-database-foundation.ps1
```

---

## 4. Connection Topologies & Environment Ports

* **PostgreSQL Native (Direct DBA / Flyway Migrations):** `localhost:5432` (`cinevault_dev`)
* **PgBouncer Proxy (Application & Worker Microservices):** `localhost:6432` (`pool_mode = transaction`)

---

## 5. Security & Role Permissions Matrix

```text
┌───────────────────────┬────────────────────────────────────────────────────────────────────────────────┐
│ Role                  │ Permissions / Isolation Boundaries                                             │
├───────────────────────┼────────────────────────────────────────────────────────────────────────────────┤
│ `cinevault_app`       │ SELECT on `canonical`, SELECT/INSERT/UPDATE on `personal`                      │
│ `cinevault_ingest`    │ INSERT on `ingestion`, SELECT/INSERT/UPDATE on `quality` (ZERO write to `canonical`)│
│ `cinevault_admin`     │ SELECT/INSERT/UPDATE/DELETE across `canonical`, `quality`, `audit`              │
│ `cinevault_analytics` │ Read-only SELECT on `canonical` (ZERO access to `personal`)                    │
└───────────────────────┴────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Rollback Guidance

If a local development migration rollback is required:
1. `docker compose down -v` (destroys local docker volume).
2. Fix or update the Flyway migration script in `sql/migrations/`.
3. `docker compose up -d` (re-initializes PostgreSQL and re-applies all Flyway migrations from scratch).
