# CineVault OS — Final Implementation Readiness Decision Log V1

**Document Type:** Master Implementation Readiness Decision Log  
**Status:** Implementation Readiness Complete — Final Owner Approval Pending  
**Date:** 2026-08-08  
**Scope:** Final Governance Decision Categorization, Inherited Constraints, Implemented Controls, Deferred Selections, and Open Decisions  

---

## 1. Executive Summary

This Decision Log categorizes all architectural and technical decisions across the complete lifecycle of **CineVault OS** up to **Phase 7 Final Implementation Readiness**.

Full historical traceability is preserved across four formal governance tiers:
* `INHERITED CONSTRAINT`: Locked invariants from master architecture ADRs and baseline specifications.
* `IMPLEMENTATION DECISION`: Concrete software/infra controls implemented in Phases 1–6.
* `DEFERRED DECISION`: Technology selections intentionally postponed to future phases.
* `OPEN DECISION`: Operational parameters pending vendor benchmarking or policy definition.

---

## 2. Decision Log Matrix

### A. APPROVED INHERITED DOMAIN CONSTRAINTS

| Decision ID | Inherited Constraint | Baseline Source | Status | Summary of Invariant |
|---|---|---|---|---|
| `DEC-SEC-INH-01` | **UUIDv7 Canonical Identity Preservation** | ADR-001 | `INHERITED CONSTRAINT` | Canonical primary keys preserve UUIDv7 format; external provider IDs map as secondary attributes. |
| `DEC-SEC-INH-02` | **Content Hierarchy Protection** | ADR-002 | `INHERITED CONSTRAINT` | Resource model observes strict `Title -> Edition -> Release` and `Title -> Season -> Episode` boundaries. |
| `DEC-SEC-INH-03` | **CAT-2 Personal Data Isolation & Non-Destruction** | ADR-003, ADR-004 | `INHERITED CONSTRAINT` | User watch logs and ratings reside strictly in `personal` schema; zero log deletion on catalog title merges. |
| `DEC-SEC-INH-04` | **AI Proposal Boundary Constraint** | ADR-004 | `INHERITED CONSTRAINT` | AI operations restricted to `quality.ai_proposal_staging` (`CAT-6`); direct canonical write paths prohibited. |
| `DEC-SEC-INH-05` | **Pre-Acquisition Licensing Gate** | DEC-ING-PRP-01 | `INHERITED CONSTRAINT` | Provider requests pass licensing gate prior to network egress. Web scraping strictly prohibited. |
| `DEC-SEC-INH-06` | **Domain Authority Provenance Lineage** | DS-01 | `INHERITED CONSTRAINT` | Credits authority provenance (KOBIS Primary Korean, TVDB Secondary TV) recorded in audit logs. |
| `DEC-SEC-INH-07` | **Metadata vs Media Rights Segregation** | DEC-ING-PRP-05 | `INHERITED CONSTRAINT` | Media proxy caches store HTTPS URLs only; binary media blobs excluded from database. |
| `DEC-SEC-INH-08` | **Three-Tier API Isolation** | DEC-API-PRP-02 | `INHERITED CONSTRAINT` | Gateway routes `/v1/` to public nodes and blocks public client access to `/internal/v1/` admin endpoints. |
| `DEC-SEC-INH-09` | **PostgreSQL Physical Schema Security** | DEC-PHYS-PRP-01 | `INHERITED CONSTRAINT` | PostgreSQL roles (`cinevault_app`, `cinevault_ingest`, `cinevault_admin`, `cinevault_analytics`) enforce schema RBAC. |
| `DEC-SEC-INH-10` | **Five-Zone Network Security Perimeter** | DEC-INFRA-PRP-06 | `INHERITED CONSTRAINT` | Network perimeters segmented across Edge/WAF, DMZ, App, Worker, and Data subnets. |
| `DEC-SEC-INH-11` | **Encryption in Transit & at Rest Requirement** | Base Security | `INHERITED CONSTRAINT` | TLS 1.3 standard for transport; AES-256 standard for storage volumes. |
| `DEC-SEC-INH-12` | **Privileged Session Protection Constraint** | Base Security | `INHERITED CONSTRAINT` | Control Room operations observe privileged session controls and re-authentication rules. |

---

### B. IMPLEMENTED TECHNICAL DECISIONS (PHASES 1–6)

| Decision ID | Implementation Title | Implementation Target | Status | Summary of Implemented Control |
|---|---|---|---|---|
| `DEC-PHYS-IMP-01` | **Flyway SQL Schema Migrations** | `sql/migrations/V1.0..V1.8` | `IMPLEMENTED` | 5 schemas, 4 PostgreSQL RBAC roles, extensions, triggers, foreign keys. |
| `DEC-API-IMP-01` | **FastAPI Boundary & OpenAPI 3.1** | `services/api/main.py` | `IMPLEMENTED` | Public `/v1/` routes, internal `/internal/v1/` routes, cursor pagination, RFC 7807 error safety. |
| `DEC-API-IMP-02` | **JWT / JWKS Claims & PKCE S256** | `services/api/auth/jwt_validator.py` | `IMPLEMENTED` | Issuer/aud/exp validation, PKCE S256 verification, human RBAC policy engine. |
| `DEC-CACHE-IMP-01` | **Valkey Distributed Cache & Idempotency** | `services/api/valkey.py` | `IMPLEMENTED` | Valkey 8.0 cache manager, atomic rate limit counters, `check_and_set_idempotency`, PII sanitization. |
| `DEC-QUEUE-IMP-01` | **RabbitMQ Quorum Queues & DLX** | `services/api/rabbitmq.py` | `IMPLEMENTED` | RabbitMQ 4.0 AMQP Quorum Queues, Dead-Letter Exchange (`cinevault.dlx`), 5000ms TTL retry topology. |
| `DEC-OBS-IMP-01` | **Structured JSON Logging & Redaction** | `services/api/telemetry.py` | `IMPLEMENTED` | JSONFormatter structured logging with PII/secret redaction (`sanitize_value`). |
| `DEC-OBS-IMP-02` | **Prometheus Metrics Collector** | `services/api/telemetry.py` | `IMPLEMENTED` | Prometheus TSDB exposition metrics collector (`/metrics`). |
| `DEC-OBS-IMP-03` | **W3C Traceparent & Correlation Context** | `services/api/telemetry.py` | `IMPLEMENTED` | `CorrelationAndMetricsMiddleware` propagating `X-Correlation-ID` and `traceparent`. |
| `DEC-SEC-IMP-01` | **Zero-Trust Service Identity Isolation** | `services/api/auth/rbac.py` | `IMPLEMENTED` | `enforce_service_isolation` across all 6 service identities (`ingest`, `ai`, `analytics`, `sync`, `quality`, `public_api`). |
| `DEC-SEC-IMP-02` | **Privileged Access & High-Risk Auth Guard** | `services/api/auth/rbac.py` | `IMPLEMENTED` | `HIGH_RISK_OPERATIONS` WebAuthn fresh auth requirement ($\le 60$s), TOTP rejection, 15-min curator session idle timeout. |
| `DEC-SEC-IMP-03` | **Protected Security Audit Logger** | `services/api/auth/audit.py` | `IMPLEMENTED` | `AuditLogger` emitting structured audit logs with SHA-256 integrity checksums over canonical attributes. |

---

### C. DEFERRED DECISIONS (Carried Forward)

| Decision ID | Deferred Topic | Reason for Deferral | Target Phase | Status |
|---|---|---|---|---|
| `DEC-API-DEF-01` | **Physical OpenAPI 3.1 Specs** | Spec served dynamically by FastAPI (`/openapi.json`). | OpenAPI Phase | `DEFERRED` |
| `DEC-API-DEF-02` | **OAuth Server / IdP Vendor** | Keycloak dev container configured; production IdP vendor choice deferred. | Security Phase | `DEFERRED` |
| `DEC-API-DEF-03` | **API Gateway Technology Selection** | Kong Gateway 3.6 configured in dev stack; prod vendor choice deferred. | Edge Phase | `DEFERRED` |
| `DEC-API-DEF-04` | **Physical Cache Storage Technology** | Valkey 8.0 implemented; cloud cache cluster choice deferred. | Cache Phase | `DEFERRED` |
| `DEC-API-DEF-05` | **Sync Payload Serialization** | JSON outbox serialization implemented; Protobuf choice deferred. | Sync Phase | `DEFERRED` |
| `DEC-PHYS-DEF-04` | **Backup / DR Cloud Storage Target** | Backup cloud target selection deferred. | Operations Phase | `DEFERRED` |
| `DEC-INFRA-DEF-01` | **Cloud Provider & WAF Selection** | Cloud procurement deferred. | Cloud Procurement | `DEFERRED` |
| `DEC-INFRA-DEF-02` | **Kubernetes Manifests & IaC** | IaC scripting prohibited in architecture/local implementation phase. | Infra Phase | `DEFERRED` |
| `DEC-INFRA-DEF-03` | **CI/CD Pipeline Automation** | CI/CD YAML scripting deferred. | DevOps Phase | `DEFERRED` |

---

### D. OPEN DECISIONS & OPERATIONAL PARAMETERS

| Decision ID | Topic | Current State | Action Required | Status |
|---|---|---|---|---|
| `DEC-SEC-OPN-01` | **Control Room Hardware Key Standard** | WebAuthn hardware key required; TOTP rejected. | Select curator hardware key supplier. | `OPEN` |
| `DEC-SEC-OPN-02` | **SIEM Integration Platform** | Log aggregator selection deferred. | Security tooling review in operations phase. | `OPEN` |
| `DEC-ING-OPN-02` | **CAT-5 Payload Retention Duration** | Raw payload retention duration pending. | Operational policy definition in storage phase. | `OPEN` |
| `DEC-QUAL-OPN-02` | **Quarantine Retention Window** | Operational cleanup window definition pending. | Operational policy definition in storage phase. | `OPEN` |
