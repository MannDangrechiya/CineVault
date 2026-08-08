# CineVault OS — API Specification Decision Log V1

**Document Type:** API Architecture Strategy Decision Log  
**Status:** Post-Owner Approval Baseline (Approved)  
**Date:** 2026-08-08  
**Scope:** Architectural Decisions Introduced, Inherited, or Approved in `docs/API_SPECIFICATION_V1.md`  

---

## 1. Governance Overview

This Decision Log documents all architectural decisions associated with the CineVault OS API Specification V1.

Following formal Project Owner review, all eleven proposed architectural decisions (`DEC-API-PRP-01` through `DEC-API-PRP-11`) have received **Formal Project Owner Approval** for their conceptual direction.

### Historical Lifecycle Transition
Decisions preserve full historical traceability:
```text
PROPOSED ──▶ OWNER REVIEW ──▶ APPROVED (Conceptual Architecture Baseline)
```

> [!IMPORTANT]
> **CONCEPTUAL APPROVAL VS. IMPLEMENTATION DEFERRAL**  
> Project Owner approval authorizes **architectural concepts only**. It does NOT authorize application code, FastAPI routes, Python controllers, ORM models, physical database tables, API gateway deployment topology, physical OpenAPI YAML files, or authentication provider infrastructure. Detailed physical implementation remains deferred to respective target phases.

---

## 2. Decision Log Matrix

### A. APPROVED INHERITED DOMAIN PRINCIPLES

| Decision ID | Inherited Domain Principle | Baseline Source | Summary of Inherited Constraint |
|---|---|---|---|
| `DEC-API-INH-01` | **UUIDv7 Canonical Path Identity Constraint** | ADR-001 | Public API path routing requires UUIDv7 canonical keys (`/v1/titles/{uuidv7}`). External provider IDs are mappings only. |
| `DEC-API-INH-02` | **Content Hierarchy Resource Model Constraint** | ADR-002 | API resources strictly mirror `Title -> Edition -> Release` and `Title -> Season -> Episode` domain hierarchies. |
| `DEC-API-INH-03` | **Personal Data Safety & Conflict Isolation Constraint** | ADR-003, ADR-004 | Personal data is isolated (`/v1/me/...`). WatchEvents are append-only. Personal data cannot be silently overwritten or destroyed during merges/splits. |
| `DEC-API-INH-04` | **Durable Offline Outbox Sync Requirement** | ADR-004 | Sync pipeline must support durable offline mutations, outbox tracking, idempotency, and conflict handling. |
| `DEC-API-INH-05` | **Domain Authority & Provenance Constraint** | DS-01, DEC-SRC-PRP-01/02, DEC-QUAL-PRP-05 | Authority roles (KOBIS Primary Korean, TheTVDB Secondary TV) and decision evidence lineage are inherited governance constraints. |
| `DEC-API-INH-06` | **Provider Payload Isolation Requirement** | DEC-ING-PRP-03 | Raw provider payload schemas (`CAT-5`) must not leak into public domain client representations (`CAT-1`). |
| `DEC-API-INH-07` | **Metadata vs Media Rights Segregation Requirement** | DEC-ING-PRP-05 | Structured metadata rights and media/image usage rights remain separate governance dimensions. |
| `DEC-API-INH-08` | **AI Proposal Non-Canonical Constraint** | ADR-004 | AI-generated data is `CAT-6` proposals and cannot directly write to `CAT-1` canonical storage. |
| `DEC-API-INH-09` | **Human Curation Review Governance Requirement** | DEC-QUAL-PRP-06 | High-risk candidate promotions, entity merges, and splits require human curation review. |

---

### B. NEWLY APPROVED PROPOSAL SET (Historical Traceability: PROPOSED ──▶ APPROVED)

| Decision ID | Decision Title | Historical Transition | Scope of Conceptual Approval | Deferred Execution Scope |
|---|---|---|---|---|
| `DEC-API-PRP-01` | **OpenAPI 3.1 Machine-Readable Standard** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | OpenAPI 3.1 approved as conceptual machine-readable contract standard. | Physical YAML/JSON spec file generation deferred (`DEC-API-DEF-01`). |
| `DEC-API-PRP-02` | **Three-Tier Logical API Boundary Architecture** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Logical separation (Public Client API, Internal Operational API, Provider Integration Boundary) approved. | Physical gateway & deployment topology remain deferred (`DEC-API-DEF-03`). |
| `DEC-API-PRP-03` | **Opaque Cursor-Based Pagination Model** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Opaque cursor-based pagination approved as API contract direction. | Physical database indexing & pagination queries remain deferred. |
| `DEC-API-PRP-04` | **RFC 7807 Standardized Problem Details Error Model** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | RFC 7807 problem details format approved for standardized API errors. | Middleware implementation deferred. |
| `DEC-API-PRP-05` | **URI Path Major Versioning Strategy** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | `/v1/` URI major versioning and 180-day sunset deprecation policy approved. | Routing middleware implementation deferred. |
| `DEC-API-PRP-06` | **Header-Based Idempotency Enforcement** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | `X-Idempotency-Key` or `mutation_id` idempotency requirement approved. | Physical persistence & storage mechanism remain deferred. |
| `DEC-API-PRP-07` | **REST Sync Endpoint Contract** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | `POST /v1/sync/push` and `GET /v1/sync/pull` REST endpoints using client mutation IDs approved. | Physical outbox payload schema & sync workers remain deferred (`DEC-API-DEF-05`). |
| `DEC-API-PRP-08` | **Canonical Provenance Disclosure Contract** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | `GET /v1/titles/{id}/provenance` response structure detailing provider & rule ID approved. | Internal operational details omitted from ordinary client responses. |
| `DEC-API-PRP-09` | **Rights-Aware Media Response Contract** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | `null` response behavior for un-permissioned artwork + `has_licensed_artwork` status flag approved. | Does NOT grant media licenses; actual access subject to provider rights. |
| `DEC-API-PRP-10` | **AI Proposal API Isolation Contract** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Isolation of AI suggestions strictly to `/internal/v1/ai/proposals` approved. | AI suggestions cannot directly write to canonical storage without human review. |
| `DEC-API-PRP-11` | **Internal Curation API Boundary** | `PROPOSED` ──▶ `OWNER REVIEW` ──▶ **`APPROVED`** | Internal endpoints (`/internal/v1/reconciliation/candidates`) for curation review approved. | Internal administrative endpoints MUST NOT be exposed as public APIs. |

---

### C. DEFERRED DECISIONS (Intentionally Postponed)

| Decision ID | Deferred Topic | Reason for Deferral | Target Phase |
|---|---|---|---|
| `DEC-API-DEF-01` | **Physical OpenAPI 3.1 YAML/JSON Files** | Spec document creation; physical YAML file generation deferred. | Implementation & OpenAPI Phase |
| `DEC-API-DEF-02` | **Authentication Provider & OAuth Server Selection** | OAuth2 server infrastructure (Keycloak, Auth0, Firebase Auth, Custom JWT) deferred. | Security & Auth Architecture Phase |
| `DEC-API-DEF-03` | **API Gateway & Reverse Proxy Topology** | Gateway technology selection (Kong, Envoy, NGINX) deferred. | Infrastructure & Deployment Phase |
| `DEC-API-DEF-04` | **Physical Cache Storage & Redis Key Schemas** | Storage engineering deferred. | Physical Storage Design Phase |
| `DEC-API-DEF-05` | **Sync Payload Serialization Protocol (Protobuf vs JSON)** | Serialization binary protocol choice deferred. | Offline Sync Implementation Phase |

---

### D. OPEN QUESTIONS & BLOCKED DECISIONS

| Decision ID | Topic | Description & Barrier | Action Required |
|---|---|---|---|
| `DEC-API-OPN-01` | **GraphQL Evaluation for Client Query Graph** | Should CineVault expose a GraphQL endpoint alongside REST `/v1/` for mobile query fetching in a future phase? | Evaluation in future mobile performance review pass. |
| `DEC-API-OPN-02` | **Sync Outbox Batch Size Limits** | What is the maximum recommended mutation batch size for `POST /v1/sync/push` on low-bandwidth mobile connections? | Benchmark testing in mobile network phase. |

---

## 3. Governance Summary Dashboard

```text
===============================================================================
CINEVAULT OS — API SPECIFICATION V1 GOVERNANCE DASHBOARD
===============================================================================

DEC-API-PRP-01   🟢 APPROVED  (OpenAPI 3.1 Machine-Readable Standard)
DEC-API-PRP-02   🟢 APPROVED  (Three-Tier Logical API Boundary Architecture)
DEC-API-PRP-03   🟢 APPROVED  (Opaque Cursor-Based Pagination Model)
DEC-API-PRP-04   🟢 APPROVED  (RFC 7807 Standardized Problem Details Error Model)
DEC-API-PRP-05   🟢 APPROVED  (URI Path Major Versioning Strategy)
DEC-API-PRP-06   🟢 APPROVED  (Header-Based Idempotency Enforcement)
DEC-API-PRP-07   🟢 APPROVED  (REST Sync Endpoint Contract)
DEC-API-PRP-08   🟢 APPROVED  (Canonical Provenance Disclosure Contract)
DEC-API-PRP-09   🟢 APPROVED  (Rights-Aware Media Response Contract)
DEC-API-PRP-10   🟢 APPROVED  (AI Proposal API Isolation Contract)
DEC-API-PRP-11   🟢 APPROVED  (Internal Curation API Boundary)

DEC-API-DEF-01   🟡 DEFERRED  (Physical OpenAPI 3.1 YAML/JSON Files)
DEC-API-DEF-02   🟡 DEFERRED  (Authentication Provider & OAuth Server Selection)
DEC-API-DEF-03   🟡 DEFERRED  (API Gateway & Reverse Proxy Topology)
DEC-API-DEF-04   🟡 DEFERRED  (Physical Cache Storage & Redis Key Schemas)
DEC-API-DEF-05   🟡 DEFERRED  (Sync Payload Serialization Protocol Choice)

DEC-API-OPN-01   🟡 OPEN      (GraphQL Evaluation for Client Query Graph)
DEC-API-OPN-02   🟡 OPEN      (Sync Outbox Batch Size Limits)

===============================================================================
FINAL ARCHITECTURE STATUS: API SPECIFICATION V1 APPROVED WITH DEFERRED API DECISIONS
===============================================================================
```

---
