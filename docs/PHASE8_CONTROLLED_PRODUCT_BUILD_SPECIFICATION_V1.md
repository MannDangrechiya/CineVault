# CineVault OS — Phase 8 Controlled Product Build Specification V1

**Document Type:** Controlled Product Build Baseline & Execution Plan  
**Status:** Phase 8 Baseline Established — Authorized for Incremental Construction  
**Date:** 2026-08-08  
**Scope:** Controlled Product Build Baseline across 18 Governance & Capability Domains, Repository Inventory, Gap Analysis, Build Order, Licensing Gate, and First Authorized Build Unit Definition  

---

## 1. Executive Baseline Summary

Phase 8 begins the controlled transition from the **Governed Implementation Baseline** (Phase 7 locked, 62/62 tests passing, 0 regressions, 0 security/privacy violations) to an **Actual Product Build + Production Readiness** pipeline.

In accordance with the Phase 8 Master Execution Prompt, this specification establishes the **Controlled Product Build Baseline**. It audits the exact current state of the repository, identifies backend and client capability gaps, details licensing boundaries, outlines the controlled build order, and specifies **Build Unit 8.1** as the first authorized build step.

---

## 2. Current Repository Implementation Inventory (Step 8.1)

| Component | Current State | Implemented? | Tested? | Production Ready? | Governance Status | Dependencies | Next Action |
|---|---|---|---|---|---|---|---|
| **Authentication** | Keycloak OIDC, PKCE S256, JWT/JWKS validation | YES | YES | Partial (Dev IdP) | `LOCKED & VALIDATED` | Keycloak, FastAPI | Wire prod IdP vendor when selected |
| **Authorization / RBAC** | 3-tier API, 6 service identities, curator WebAuthn guard | YES | YES | YES | `LOCKED & VALIDATED` | FastAPI, `auth/rbac.py` | Enforce on all new routes |
| **Public API (`/v1/*`)** | FastAPI routers (`titles`, `search`, `me`, `sync`) with mock payloads | Partial (Mock Data) | YES (Contracts) | NO (Needs DB queries) | `APPROVED BASELINE` | FastAPI, Pydantic | Replace mocks with DB queries |
| **Internal API (`/internal/v1/*`)** | Ingestion, reconciliation candidates, AI proposals, audit logging | Partial (Mock Data) | YES | Partial (Needs DB queries) | `LOCKED & VALIDATED` | FastAPI, `auth/audit.py` | Connect real quality/ingestion DB |
| **Database Schemas** | 5 PostgreSQL schemas (`canonical`, `personal`, `ingestion`, `quality`, `audit`) | YES | YES | YES (DDL Ready) | `LOCKED & VALIDATED` | PostgreSQL 16, Flyway | Build DB repository access layer |
| **Migrations** | 10 Flyway scripts (`V1.0..V1.8`, `R__seed_development_taxonomy.sql`) | YES | YES | YES | `LOCKED & VALIDATED` | Flyway, PgBouncer | Maintain schema discipline |
| **Canonical Identity** | UUIDv7 primary keys, display ID mappings, provenance tracking | YES (DDL & Specs) | YES | YES | `INHERITED CONSTRAINT` | PostgreSQL DDL | Implement UUIDv7 title CRUD |
| **Personal Data Isolation** | `personal` schema, append-only watch events, user title state, ratings | YES (DDL & Router) | YES | Partial (Needs DB queries) | `INHERITED CONSTRAINT` | PostgreSQL DDL | Connect DB repository to `/v1/me` |
| **Ingestion Pipeline** | `ingestion.raw_payload` table & router endpoint | Partial | YES | NO (Needs adapters) | `APPROVED BASELINE` | RabbitMQ, HTTP Client | Build provider fetcher adapters |
| **Raw Payload Capture** | Ingestion table for raw JSON, payload hash, provider ID | YES (DDL) | YES | Partial (Needs ingest worker)| `APPROVED BASELINE` | `ingestion.raw_payload` | Wire ingest worker payload writer |
| **Quality Pipeline** | `quality.reconciliation_candidate` schema | YES (DDL) | YES | NO (Needs engine) | `APPROVED BASELINE` | PostgreSQL DDL | Implement identity resolution |
| **Reconciliation Engine** | Curator `/promote` and `/reject` API endpoints with SHA-256 audit | Partial (Stubs) | YES | Partial | `INHERITED CONSTRAINT` | Audit logger, DDL | Wire canonical entity promoter |
| **AI Proposals Staging** | `quality.ai_proposal_staging` schema & router stub | YES (DDL & Router) | YES | Partial | `INHERITED CONSTRAINT` | `auth/rbac.py` | Implement AI proposal parser |
| **Search Engine** | `/v1/search` router with mock matching | Partial (Mock) | YES | NO (Needs FTS) | `APPROVED BASELINE` | PostgreSQL FTS/Trigram | Implement PostgreSQL FTS search |
| **Availability Domain** | Database schema structure for release/platform mapping | Partial (DDL) | YES | NO (Needs API/Ingest) | `APPROVED BASELINE` | Canonical DDL | Add availability DB queries |
| **Recommendation Engine** | Not implemented | NO | NO | NO | `APPROVED BASELINE` | User history, catalog | Candidate generation after DB layer |
| **Distributed Cache** | Valkey 8.0 client, atomic rate limiter, idempotency manager | YES | YES | YES | `LOCKED & VALIDATED` | Valkey 8.0 container | Use in DB caching layer |
| **Message Queue / DLX** | RabbitMQ 4.0 Quorum queues, DLX, retry topology (5000ms TTL) | YES | YES | YES | `LOCKED & VALIDATED` | RabbitMQ 4.0 container | Publish ingestion/sync events |
| **Offline Sync Engine** | `/v1/sync` router stub & outbox mutation contract | Partial (Stubs) | YES | NO (Needs outbox DB) | `APPROVED BASELINE` | PostgreSQL `personal` | Build durable outbox processor |
| **Observability** | Structured JSON logging, OTel W3C traceparent, Prometheus metrics | YES | YES | YES | `LOCKED & VALIDATED` | Prometheus, Loki, OTel | Instrument new build units |
| **Protected Audit Log** | `AuditLogger` emitting SHA-256 integrity-hashed audit entries | YES | YES | YES | `LOCKED & VALIDATED` | `auth/audit.py` | Log all curation events |
| **Export / Import** | Not implemented | NO | NO | NO | `APPROVED BASELINE` | Personal DB layer | Deferred to post-mobile client |
| **Flutter Mobile Client** | Not started | NO | NO | NO | `APPROVED BASELINE` | OpenAPI contracts | Build after backend API stable |
| **Control Room Admin UI**| API endpoints under `/internal/v1/*` | Partial (API Only) | YES | NO (Needs Web UI) | `LOCKED & VALIDATED` | `/internal/v1/*` APIs | Flutter/Web Admin UI build |
| **Provider Integrations** | Licensing boundaries & authority roles defined (KOBIS, TVDB) | Spec Only | YES (Mock) | NO (Needs real credentials)| `GOVERNED GATE` | Provider HTTP clients | Licensing gate validation |
| **CI/CD Automation** | `check-hygiene.ps1` and validation scripts | Local Only | YES | Deferred (`DEC-INFRA-DEF-03`)| `DEFERRED` | GitHub Actions | Post-Phase 8 deployment prep |
| **Deployment / Cloud** | Docker Compose dev stack (`postgres`, `valkey`, `rabbitmq`, `kong`) | Local Only | YES | Deferred (`DEC-INFRA-DEF-01`)| `DEFERRED` | Cloud Procurement | Local Docker execution |
| **Backup / DR** | Logical SQL dump scripts | Local Only | NO | Deferred (`DEC-PHYS-DEF-04`) | `DEFERRED` | Database Admin | Operational procedure doc |

---

## 3. Detailed Product Capability Inventory & Gaps

### 3.1 Backend Domain Foundations Gap
- **Current State:** PostgreSQL 16 database schemas are created via Flyway migrations (`V1.0..V1.8`). Seed taxonomies for genres, countries, and languages are populated (`R__seed_development_taxonomy.sql`).
- **Gap:** Missing an asynchronous database access / repository pattern layer in FastAPI (SQLAlchemy 2.0 Async / asyncpg) to execute real SQL queries against `canonical`, `personal`, `ingestion`, `quality`, and `audit` schemas.

### 3.2 API Completion Gap
- **Current State:** API endpoints exist under `/v1/*` and `/internal/v1/*` but return hardcoded mock response models.
- **Gap:** Routers need to be rewired to execute real database repository calls, apply dynamic SQL filtering, cursor-based pagination over UUIDv7 keys, header-based idempotency persistence, and real error responses.

### 3.3 Database Completion Gap
- **Current State:** Schemas and foreign keys are locked and valid.
- **Gap:** Need database repository classes for all domain models:
  - `CanonicalRepository`: Title, Edition, Release, Person, Genre, Country.
  - `PersonalRepository`: WatchEvent, UserTitleState, Rating, Review, Note, PersonalDataConflict.
  - `IngestionRepository`: RawPayload.
  - `QualityRepository`: ReconciliationCandidate, AIProposalStaging.
  - `AuditRepository`: SecurityAuditLog.

### 3.4 Ingestion Readiness
- **Current State:** `ingestion.raw_payload` table and raw payload retrieval endpoints are built.
- **Gap:** Outbound HTTP provider fetchers (KOBIS API client, TVDB API client), rate limiters, payload hashing (`SHA-256`), and asynchronous background ingestion queue workers need implementation.

### 3.5 Search Readiness
- **Current State:** Unified search endpoint `/v1/search` is defined with query parameters (`q`, `type`, `content_type`, `year`, `limit`).
- **Gap:** Real PostgreSQL full-text search (FTS with `tsvector`/`tsquery` and trigram similarity `pg_trgm`) over `canonical.title`, `canonical.person`, and title alternate names, with script normalization and Unicode folding.

### 3.6 Personal Data Readiness
- **Current State:** DDL tables for watch events, user title states, ratings, reviews, notes, and personal data conflicts exist. Public router stubs exist.
- **Gap:** DB persistence for personal records, append-only watch log insertion, automatic user title state derivation (`COMPLETED`, `IN_PROGRESS`, `PLAN_TO_WATCH`), and personal data conflict resolution execution on catalog merges.

### 3.7 Recommendation Readiness
- **Current State:** Architecture baseline specifies hard filtering $\rightarrow$ candidate generation $\rightarrow$ similarity $\rightarrow$ personal taste $\rightarrow$ ranking $\rightarrow$ explanation.
- **Gap:** Full recommendation pipeline needs to be constructed on top of populated canonical titles and personal user history.

### 3.8 AI Assistant & Proposal Readiness
- **Current State:** `quality.ai_proposal_staging` schema and `/internal/v1/ai/proposals` router stubs exist. Invariant `AI -> quality.ai_proposal_staging -> human curation -> canonical` is strictly enforced in tests.
- **Gap:** LLM client wrapper (supporting prompt versioning, structured JSON extraction, confidence scoring, evidence attachment) and Control Room proposal review/promotion workflow.

### 3.9 Flutter / Client Readiness
- **Current State:** Target architecture designated as Flutter cross-platform client. No code currently in repository.
- **Gap:** Client workspace setup, clean architecture layers (Presentation, Application, Domain, Data, Core), state management (Riverpod/Bloc), API network client (Dio with JWT refresh), local database (Drift), and offline outbox sync manager.

### 3.10 Offline-Sync Readiness
- **Current State:** `/v1/sync` router stub and outbox mutation schema defined.
- **Gap:** Local client outbox queue, server-side durable outbox mutation ingest processor, server idempotency verification via Valkey/PostgreSQL, and conflict resolution strategy.

### 3.11 Control Room Readiness
- **Current State:** Internal curation API `/internal/v1/*` implemented with RBAC (`require_curator`, `require_system_admin`), WebAuthn fresh authentication guard, and SHA-256 audit logging.
- **Gap:** Frontend web/curation dashboard UI for Control Room operators to inspect ingestion runs, quarantine records, identity resolution candidates, and AI proposals.

### 3.12 Production Readiness Gaps
- **Current State:** Docker Compose local infrastructure operational.
- **Gap:** Production IdP vendor deployment (`DEC-API-DEF-02`), Cloud infrastructure IaC (`DEC-INFRA-DEF-02`), CI/CD automation pipelines (`DEC-INFRA-DEF-03`), commercial alerting integration (`DEC-OBS-DEF-01`), and automated database backup/DR execution.

---

## 4. Licensing & External Provider Access Gate (Step 8.4)

| Provider | Authority Role | Data / API | Licensing Status | Permitted Usage | Access Constraint | Operational Status |
|---|---|---|---|---|---|---|
| **KOBIS / KOFIC** | Primary Korean-Domain Authority | Korean box office, film metadata, credits | Approved Authority | Canonical Korean Title Metadata | Official API Key Required | Gate Passed for Integration Dev |
| **TheTVDB** | Secondary TV Authority | TV series, seasons, episodes | Approved Authority | Secondary TV Metadata | Licensed API Key Required | Gate Passed for Integration Dev |
| **TMDb** | Candidate Provider | Global movies, TV, credits, images | Candidate Subject to Review | Non-Commercial / Partner Terms | API Key Server-Side Only | Candidate Staging Only |
| **IMDb Datasets** | Excluded | IMDb TSV files | EXCLUDED | Direct ingestion prohibited | Commercial terms required | PROHIBITED |
| **JustWatch** | Web Scraping / Partner | Streaming availability | Scraping PROHIBITED | Partner API Candidate Only | No Web Scraping Allowed | PROHIBITED (Scraping) |
| **Wikidata** | Reference Authority | Entity links, SPARQL reference | Open Knowledge | Structured reference resolution | Rate-limited SPARQL calls | Candidate Reference |

### Non-Negotiable Integration Invariants:
1. **Zero Web Scraping:** All data acquisition must occur via authorized API endpoints or explicit static data files.
2. **Zero Provider Key Leakage:** External API keys must reside strictly in server-side environment configurations (`.env`). Provider credentials MUST NEVER be embedded in source code or sent to Flutter mobile clients.
3. **Pre-Acquisition Gate:** Ingestion services must verify provider license status prior to making network requests.

---

## 5. Deferred Decision & Operational Parameter Status (Step 8.3)

| Decision ID | Subject Topic | Historical Status | Target Phase | Build Unit Impact | Resolution Approach |
|---|---|---|---|---|---|
| `DEC-API-DEF-05` | Sync Payload Serialization | `DEFERRED` | Sync Phase | Unit 8.7 (Sync Engine) | Use JSON outbox for initial build; Protobuf deferred |
| `DEC-ING-OPN-02` | CAT-5 Raw Payload Retention | `OPEN` | Ingestion Phase | Unit 8.4 (Ingestion) | Default retention: 90 days raw payload archive in `ingestion.raw_payload` |
| `DEC-QUAL-OPN-02` | Quarantine Retention Window | `OPEN` | Quality Phase | Unit 8.5 (Reconciliation)| Default retention: 30 days pending curation before auto-archiving |
| `DEC-INFRA-DEF-01` | Cloud Provider & WAF Selection | `DEFERRED` | Procurement | Operations | Retain local Docker stack; cloud deployment stays deferred |
| `DEC-INFRA-DEF-02` | Kubernetes Manifests & IaC | `DEFERRED` | Infra Phase | Operations | Retain Docker Compose baseline; IaC stays deferred |
| `DEC-INFRA-DEF-03` | CI/CD Pipeline Automation | `DEFERRED` | DevOps Phase | Operations | Retain local powershell scripts (`check-hygiene.ps1`); CI YAML stays deferred |

---

## 6. Governed Product Build Order (Step 8.2)

To ensure systematic progress without technical or governance debt, product construction will proceed in the following strict dependency order:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Phase 8 Controlled Product Build Order                                                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ BUILD UNIT 8.1 ──► Canonical Data Access & Title Domain Backend Completion (Current)   │
│ BUILD UNIT 8.2 ──► Personal Library, Watch Events & Ratings Persistence               │
│ BUILD UNIT 8.3 ──► Catalog Search & Script-Normalized FTS Engine                       │
│ BUILD UNIT 8.4 ──► Data Ingestion Engine & Provider Fetcher Adapters (KOBIS / TVDB)   │
│ BUILD UNIT 8.5 ──► Identity Resolution & Data Quality Reconciliation Engine           │
│ BUILD UNIT 8.6 ──► AI Proposal Staging Engine & Curator Workflow                       │
│ BUILD UNIT 8.7 ──► Outbox Mutation Processor & Offline Sync Server                     │
│ BUILD UNIT 8.8 ──► Recommendation Foundation Engine                                    │
│ BUILD UNIT 8.9 ──► Flutter Cross-Platform Client Foundation                            │
│ BUILD UNIT 8.10 ─► Control Room Admin Front-End UI                                   │
│ BUILD UNIT 8.11 ─► Production Readiness, Operations & Packaging                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. First Authorized Build Unit: Build Unit 8.1 (Step 8.5)

### Build Unit 8.1 Scope & Objective:
**Canonical Data Access & Title Domain Backend Completion**

* **Objective:** Implement real PostgreSQL database persistence for canonical catalog metadata (`canonical` schema: `title`, `title_edition`, `release`, `genre`, `country`, `person`, `title_credit`) using an asynchronous SQLAlchemy 2.0 / asyncpg repository layer in FastAPI. Replace hardcoded mock responses in `/v1/titles` with live database queries supporting dynamic filtering, cursor-based pagination over UUIDv7 keys, display ID lookups, external provider ID mapping, and provenance lineage!

### Scope Breakdown:
1. **Database Session & Connection Pool Manager:**
   - Implement `services/api/database.py` with async SQLAlchemy engine connecting to PgBouncer (`postgresql+asyncpg://`).
2. **Canonical Domain Repositories:**
   - Create `services/api/repositories/canonical.py`:
     - `get_title_by_id(title_id: UUID)`
     - `get_title_by_display_id(display_id: str)`
     - `get_title_by_external_id(provider: str, external_id: str)`
     - `list_titles(content_type, year, country, cursor, limit)`
     - `get_title_provenance(title_id: UUID)`
3. **ORM Models:**
   - Create `services/api/models/canonical.py` mapping PostgreSQL tables in `canonical` schema.
4. **Router Rewiring:**
   - Update `services/api/routers/titles.py` to inject database session dependency and invoke `CanonicalRepository` methods.
5. **Testing & Verification:**
   - Add integration tests in `tests/test_canonical_repository.py` verifying real PostgreSQL queries, pagination cursor generation, and display ID resolution.

---

## 8. Governance & Security Boundary Check

Build Unit 8.1 strictly preserves:
- `ADR-001`: UUIDv7 primary keys for all canonical title entities.
- `ADR-002`: Strict `Title -> Edition -> Release` hierarchy.
- `ADR-003`: Personal data isolation (`personal` schema untouched by canonical reads).
- `ADR-004`: Zero AI direct writes to canonical database.
- `DEC-API-PRP-02`: Public `/v1/titles` routes remain read-only for public clients.
- `DEC-PHYS-PRP-01`: Database connection accesses PostgreSQL via `cinevault_app` role with restricted privileges.

---

## 9. Verification & Acceptance Criteria

1. All existing 62 unit and integration tests continue to PASS with 0 regressions.
2. New database repository integration tests pass against PostgreSQL schema.
3. `/v1/titles` endpoints execute live SQL queries against PgBouncer and return canonical data models.
4. `/v1/titles/lookup` successfully resolves display IDs (e.g. `MOV-000001`) and external provider mappings to canonical UUIDv7 IDs.
5. `/v1/titles/{title_id}/provenance` returns valid provenance records.
6. Documentation is updated and changes committed via git.

---

## 10. Summary Status Verdict

```text
PHASE 8 CONTROLLED PRODUCT BUILD BASELINE: ESTABLISHED
FIRST AUTHORIZED BUILD UNIT: BUILD UNIT 8.1 (CANONICAL DATA ACCESS)
STATUS: READY FOR EXECUTION
```
