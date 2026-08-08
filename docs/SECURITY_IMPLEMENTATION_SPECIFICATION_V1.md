# CineVault OS — Security Implementation Specification V1

**Document Type:** Master Security Implementation Specification  
**Status:** Implementation Complete — Governance Transition Phase  
**Date:** 2026-08-08  
**Scope:** Phase 6 Security Implementation, Zero Trust Service Identity Isolation, High-Risk Operations & WebAuthn/MFA, 3-Tier API Security, Protected Security Audit Logger, Cryptography Baseline, Cache & Queue Security, and Test Coverage Baseline  

---

## 1. Executive Summary

The **CineVault OS Security Implementation Specification V1** formalizes the concrete security controls implemented in Phase 6 of the CineVault OS architecture.

This specification translates all locked security architecture requirements (`docs/SECURITY_ARCHITECTURE_V1.md`, `docs/SECURITY_ARCHITECTURE_DECISION_LOG_V1.md`) into executable code, zero-trust policy engines, protected audit loggers, cache/queue security controls, and automated test assertions.

All 12 inherited security constraints remain 100% preserved. Deferred technology selections (OAuth servers, WAF vendor, cloud KMS, SIEM platform) remain deferred without inventing synthetic dependencies.

---

## 2. Classification Matrix

Each component of the security specification is categorized into one of four formal governance tiers:

```text
┌──────────────────────────────────────┬────────────────────────────────────────────────────────────────────────┐
│ Governance Classification            │ Definition & Scope                                                     │
├──────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ INHERITED CONSTRAINT                 │ Locked domain invariants from ADR-001..004, Data Model, & Sec Arch V1. │
│ IMPLEMENTATION DECISION              │ Concrete software controls implemented in Phase 6 codebase/tests.       │
│ DEFERRED DECISION                    │ Standing deferred technology choices postponed to future phases.       │
│ OPEN DECISION                        │ Operational parameters pending vendor benchmarking or policy definition.│
└──────────────────────────────────────┴────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Implemented Security Controls

### 3.1 Zero-Trust Service Identity Isolation (`DEC-SEC-IMP-01`)
* **Classification:** `IMPLEMENTATION DECISION`
* **Target Components:** `services/api/auth/rbac.py`, `services/api/auth/dependencies.py`
* **Behavior:** Machine workload service identities communicate over isolated perimeters with strict least-privilege action boundaries:
  * `cinevault-ingest-service`: `RAW_PAYLOAD_INSERT` permitted; `CANONICAL_WRITE` prohibited.
  * `cinevault-ai-service`: Operates strictly in `quality.ai_proposal_staging` (`CAT-6`); `CANONICAL_WRITE` prohibited.
  * `cinevault-analytics-service`: Read-only access to canonical catalog; `PERSONAL_READ`, `PERSONAL_WRITE`, `CANONICAL_WRITE` prohibited.
  * `cinevault-sync-processor`: Operates strictly in `personal` schema outbox; `CANONICAL_WRITE` prohibited.
  * `cinevault-quality-service`: Manages raw payload quarantine; `CANONICAL_WRITE` prohibited.
  * `cinevault-public-api`: Direct internal admin mutations or canonical catalog modifications prohibited.

### 3.2 Privileged Access & High-Risk Operations Guard (`DEC-SEC-IMP-02`)
* **Classification:** `IMPLEMENTATION DECISION`
* **Target Components:** `services/api/auth/rbac.py`, `services/api/routers/internal.py`
* **Behavior:** Destructive and critical control room operations (`ENTITY_MERGE`, `ENTITY_SPLIT`, `CANONICAL_PROMOTION`, `PROVIDER_CONFIG_CHANGE`, `ROLE_PROMOTION`, `PERSONAL_DATA_DISPUTE_RESOLUTION`, `CREDENTIAL_KEY_OPERATION`, `SECURITY_CONFIG_CHANGE`) enforce:
  1. Mandatory Multi-Factor Authentication (WebAuthn/FIDO2 hardware keys required).
  2. Fresh authentication window check ($\le 60$ seconds).
  3. Strict TOTP rejection for high-risk operations.
  4. 15-minute privileged session idle timeout (`CURATOR_SESSION_IDLE_TIMEOUT_SECONDS = 900`).

### 3.3 Protected Security Audit Logger (`DEC-SEC-IMP-03`)
* **Classification:** `IMPLEMENTATION DECISION`
* **Target Components:** `services/api/auth/audit.py`, `services/api/routers/internal.py`
* **Behavior:** Centralized `AuditLogger` emits structured, tamper-evident audit records (`AUDIT_AUTH_FAILURE`, `AUDIT_PRIVILEGED_ACCESS`, `AUDIT_CANONICAL_PROMOTION`, `AUDIT_ENTITY_MERGE`, `AUDIT_ENTITY_SPLIT`, `AUDIT_PROVIDER_CONFIG_CHANGE`, `AUDIT_AI_PROPOSAL_DECISION`, `AUDIT_SECURITY_POLICY_CHANGE`).
* **Integrity Protection:** Every audit record incorporates a SHA-256 integrity hash computed over canonical fields (`event_id`, `timestamp`, `event_type`, `actor_id`, `target_id`, `details_json`).

### 3.4 Cache Security & PII Sanitization (`DEC-SEC-IMP-04`)
* **Classification:** `IMPLEMENTATION DECISION`
* **Target Components:** `services/api/valkey.py`
* **Behavior:** `ValkeyManager.set()` invokes `_sanitize_cache_value()` to parse JSON strings and sanitize PII (`watch_event_notes`, `user_address`, `email`) and sensitive secrets (`password`, `token`, `auth_token`, `secret`) before caching.

### 3.5 Cryptography Baseline Verification (`DEC-SEC-IMP-05`)
* **Classification:** `IMPLEMENTATION DECISION`
* **Target Components:** `services/api/main.py`, `services/api/config.py`
* **Behavior:** Transport security enforced via HSTS headers (`Strict-Transport-Security: max-age=31536000; includeSubDomains`), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and PostgreSQL SSL mode `sslmode=require`. Storage volumes enforce AES-256 standard.

---

## 4. Inherited Security Constraints Log

| Constraint ID | Title | Baseline Source | Classification | Enforced Status |
|---|---|---|---|---|
| `DEC-SEC-INH-01` | UUIDv7 Canonical Identity Preservation | ADR-001 | `INHERITED CONSTRAINT` | **VERIFIED PASS** |
| `DEC-SEC-INH-02` | Content Hierarchy Resource Model | ADR-002 | `INHERITED CONSTRAINT` | **VERIFIED PASS** |
| `DEC-SEC-INH-03` | Personal Data Isolation & Non-Destruction | ADR-003, ADR-004 | `INHERITED CONSTRAINT` | **VERIFIED PASS** |
| `DEC-SEC-INH-04` | AI Proposal Boundary Non-Canonical Constraint | ADR-004 | `INHERITED CONSTRAINT` | **VERIFIED PASS** |
| `DEC-SEC-INH-05` | Pre-Acquisition Licensing Gate | DEC-ING-PRP-01 | `INHERITED CONSTRAINT` | **VERIFIED PASS** |
| `DEC-SEC-INH-06` | Domain Authority Provenance Lineage | DS-01 | `INHERITED CONSTRAINT` | **VERIFIED PASS** |
| `DEC-SEC-INH-07` | Metadata vs Media Rights Segregation | DEC-ING-PRP-05 | `INHERITED CONSTRAINT` | **VERIFIED PASS** |
| `DEC-SEC-INH-08` | Three-Tier API Boundary Isolation | DEC-API-PRP-02 | `INHERITED CONSTRAINT` | **VERIFIED PASS** |
| `DEC-SEC-INH-09` | PostgreSQL Physical Schema Security | DEC-PHYS-PRP-01 | `INHERITED CONSTRAINT` | **VERIFIED PASS** |
| `DEC-SEC-INH-10` | Five-Zone Network Security Perimeter | DEC-INFRA-PRP-06 | `INHERITED CONSTRAINT` | **VERIFIED PASS** |
| `DEC-SEC-INH-11` | Encryption in Transit & at Rest Requirement | Security Baseline | `INHERITED CONSTRAINT` | **VERIFIED PASS** |
| `DEC-SEC-INH-12` | Privileged Session Protection Constraint | Security Baseline | `INHERITED CONSTRAINT` | **VERIFIED PASS** |

---

## 5. Deferred Security Decisions Log

| Decision ID | Deferred Topic | Reason for Deferral | Target Phase | Classification |
|---|---|---|---|---|
| `DEC-API-DEF-02` | OAuth Server / IdP Vendor | Provider choice (Auth0 vs Keycloak vs Cognito) deferred. | Security Implementation | `DEFERRED DECISION` |
| `DEC-API-DEF-03` | API Gateway Software | Gateway proxy software selection deferred. | Edge Infrastructure | `DEFERRED DECISION` |
| `DEC-INFRA-DEF-01` | Cloud KMS Vendor | KMS vendor selection (AWS KMS vs GCP KMS vs HashiCorp Vault) deferred. | Cloud Procurement | `DEFERRED DECISION` |
| `DEC-SEC-OPN-02` | SIEM Platform | Security log aggregator selection deferred. | Operations Phase | `DEFERRED DECISION` |

---

## 6. Open Decisions Log

| Decision ID | Topic | Current Status | Action Required | Classification |
|---|---|---|---|---|
| `DEC-SEC-OPN-01` | Control Room MFA Protocol Standard | WebAuthn/FIDO2 hardware keys vs TOTP. Implemented requirement: WebAuthn required for high-risk; TOTP rejected. | Finalize curator hardware token vendor. | `OPEN DECISION` |
| `DEC-ING-OPN-02` | Raw CAT-5 Payload Retention | Ingestion raw payload retention window definition. | Operational policy definition in storage phase. | `OPEN DECISION` |
