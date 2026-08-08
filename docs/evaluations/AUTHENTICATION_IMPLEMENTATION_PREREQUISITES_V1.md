# CineVault OS — Authentication Implementation Prerequisites V1

**Document Type:** Implementation Prerequisite Specification  
**Decision ID:** `DEC-API-DEF-02` — Authentication Provider & OAuth Server  
**Approved Technology:** Keycloak (Self-Hosted Open-Source Identity Server — Apache License 2.0)  
**Owner Approval Date:** 2026-08-08  
**Status:** Prerequisite Gate Active (Implementation NOT YET AUTHORIZED)  
**Scope:** Mandatory Technical, Governance, Security, and Testing Prerequisites Required BEFORE Keycloak Configuration or Authentication Code Implementation  

---

## 1. Purpose

The purpose of this specification is to define the mandatory prerequisites, deployment topologies, security acceptance tests, and operational validations that MUST be completed before authentication source code, Keycloak container configuration, OAuth client creation, or database DDL execution is authorized.

Following Project Owner approval of **DEC-API-DEF-02** on **2026-08-08**, Keycloak (Apache License 2.0) is the approved authentication technology. However, technology approval DOES NOT authorize physical implementation code writing or production infrastructure provisioning.

---

## 2. Master Prerequisites Status Matrix

```text
┌───────────────────────────────────────┬───────────────────────┬───────────────────────────────────────────┐
│ Implementation Prerequisite           │ Status                │ Dependency / Blocking Decision            │
├───────────────────────────────────────┼───────────────────────┼───────────────────────────────────────────┤
│ 1. Keycloak Version & Base Image      │ READY                 │ Keycloak 26.x LTS Quarkus Distribution     │
│ 2. Deployment Topology                │ BLOCKED               │ Awaiting Cloud Provider (`DEC-INFRA-DEF-01`)│
│ 3. Realm & Client Isolation Model     │ READY                 │ Separate Client Scopes for Control Room   │
│ 4. OAuth 2.1 / OIDC Flow Specification│ READY                 │ Auth Code + PKCE (`S256`)                 │
│ 5. Access Token Lifetime Policy       │ READY                 │ Short-Lived Access Tokens (15 min)        │
│ 6. Refresh Token Rotation Policy      │ READY                 │ Refresh Token Rotation + Revocation       │
│ 7. Curator 15-Min Session Overrides   │ READY                 │ Control Room Client Session Overrides     │
│ 8. MFA Protocol & Integration         │ BLOCKED               │ Awaiting MFA Evaluation (`DEC-SEC-OPN-01`)│
│ 9. User Identity Mapping (`CAT-2`)    │ READY                 │ `personal` Schema UUIDv7 User Isolation   │
│ 10. RBAC Role Mapping Schema          │ READY                 │ 4 Core Roles (`Anonymous..Admin`)         │
│ 11. Service-to-Service M2M Auth       │ READY                 │ Client Credentials Grant / mTLS           │
│ 12. JWKS Key Rotation Protocol        │ READY                 │ Automated Key Rotation via JWKS Endpoint  │
│ 13. Audit Log Stream Integration      │ READY                 │ Structured JSON Audit Stream (Zap/Winston)│
│ 14. Connection Pooler Configuration   │ BLOCKED               │ Awaiting Pooler Selection (`DEC-PHYS-DEF-03`)│
│ 15. Backup / DR Archival Target       │ BLOCKED               │ Awaiting Backup Storage (`DEC-PHYS-DEF-04`)│
│ 16. Container Orchestration & IaC     │ BLOCKED               │ Awaiting Orchestrator (`DEC-INFRA-DEF-02`)│
│ 17. Security Acceptance Test Suite     │ READY                 │ Automated OIDC/PKCE Test Harness Spec     │
│ 18. Credential Migration Exit PoC     │ READY                 │ Password Hash Exit Migration Test Spec    │
└───────────────────────────────────────┴───────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Keycloak Version Selection Prerequisite

* **Prerequisite:** Select a stable, long-term support (LTS) release of the official Keycloak Quarkus distribution (`quay.io/keycloak/keycloak`).
* **Governance Rule:** Keycloak MUST be run in production-optimized Quarkus mode (`start --optimized`); legacy WildFly distributions are prohibited.

---

## 4. Deployment Topology Prerequisites

* **Prerequisite Status:** **`BLOCKED (Awaiting Cloud Infrastructure Selection — DEC-INFRA-DEF-01)`**
* **Requirement:** Keycloak compute nodes must be deployed in a high-availability container pair across multiple Availability Zones in private App subnets (Zone 3). Keycloak instances MUST NOT be exposed directly to the public internet without passing through the Edge WAF / API Gateway proxy.

---

## 5. Realm & Client Model Prerequisites

* **Prerequisite:** Establish distinct Client Scopes and Client ID perimeters for:
  1. `cinevault-mobile-app`: Public Native Client (OAuth 2.1 + PKCE `S256`, zero client secret).
  2. `cinevault-web-app`: Public Web Client (OAuth 2.1 + PKCE `S256`).
  3. `cinevault-control-room`: Privileged Internal Client (OAuth 2.1 + PKCE + Mandatory MFA + 15-Min Session Timeout).
  4. `cinevault-m2m-worker`: Confidential M2M Service Client (Client Credentials Grant + Service Tokens).

---

## 6. OAuth 2.1 / OIDC Flow Prerequisites

* **Prerequisite:** Public clients MUST enforce OAuth 2.1 Authorization Code Flow with PKCE (`S256` Challenge Method).
* **Governance Rule:** Implicit Flow (`response_type=token`) and Resource Owner Password Credentials Flow (`grant_type=password`) are strictly **PROHIBITED**.

---

## 7. Token & Refresh Policy Prerequisites

* **Access Token Lifespan:** Maximum 15 minutes.
* **Refresh Token Rotation:** Enforce Refresh Token Rotation with single-use refresh tokens. Reusing an old refresh token MUST trigger immediate revocation of the entire token family.

---

## 8. Privileged Curator Session Policy Prerequisites (`DEC-SEC-PRP-10`)

* **Prerequisite:** Enforce a 15-minute privileged session idle timeout for Control Room curators.
* **Technical Enforcement:** Configured via `cinevault-control-room` client-specific session idle overrides and authentication flow re-authentication rules.

---

## 9. MFA Protocol Prerequisite (`DEC-SEC-OPN-01`)

* **Prerequisite Status:** **`BLOCKED (Awaiting DEC-SEC-OPN-01 Evaluation)`**
* **Governance Rule:** Selection of Keycloak DOES NOT resolve **DEC-SEC-OPN-01** (Control Room MFA Protocol Standard). Specific MFA factors (TOTP vs WebAuthn/FIDO2 passkeys) remain governed by **DEC-SEC-OPN-01**.

---

## 10. Database & Storage Dependency Prerequisites

* **Prerequisite Status:** **`BLOCKED (Awaiting DEC-PHYS-DEF-03 & DEC-PHYS-DEF-04)`**
* **Requirements:** Keycloak database schema requires a dedicated PostgreSQL database user (`cinevault_keycloak`). Keycloak connection pooling depends on **DEC-PHYS-DEF-03** (Connection Pooler Topology) and WAL archival storage depends on **DEC-PHYS-DEF-04** (Backup Cloud Storage Target).

---

## 11. Security Acceptance Test Suite Specifications

Before production launch, an automated test harness MUST validate the following 6 security acceptance tests:
1. **PKCE Enforcement Test:** Verify that authorization code requests without `code_challenge` or with `code_challenge_method=plain` are rejected (`HTTP 400`).
2. **Curator Session Timeout Test:** Verify that curator idle sessions exceeding 15 minutes trigger mandatory re-authentication.
3. **M2M Token Perimeter Test:** Verify that M2M worker service tokens cannot access public client `/v1/*` endpoints.
4. **Token Family Revocation Test:** Verify that reusing a previously exchanged refresh token revokes all associated tokens.
5. **Audience Restriction Test:** Verify that JWT access tokens issued for public clients contain restricted `aud` claims.
6. **JWKS Key Rotation Test:** Verify that rotating token signing keys in Keycloak does not disrupt API Gateway JWKS validation.

---

## 12. Password-Hash Migration & Exit Proof-of-Concept (PoC) Specification

* **Prerequisite:** In accordance with Project Owner Approval Condition #5, password-hash portability is NOT guaranteed.
* **PoC Requirement:** Prior to production launch, a test migration PoC MUST verify whether exported password hashes (PBKDF2/Argon2) can be imported and validated in a secondary test identity system.

---

## 13. Implementation Safety Controls

```text
Application Code Files Created: 0
SQL/DDL Executed:              0
Database Migrations:           0
Keycloak Realms Created:       0
OAuth Clients Provisioned:     0
Secrets / Keys Generated:      0
Docker Containers Deployed:    0
===============================================================================
STATUS: PREREQUISITE SPECIFICATION ONLY — IMPLEMENTATION NOT AUTHORIZED
===============================================================================
```

---
