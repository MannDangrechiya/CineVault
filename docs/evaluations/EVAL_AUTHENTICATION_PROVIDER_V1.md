# CineVault OS — Technology Evaluation: Authentication Provider & OAuth Server V1

**Document Type:** Technology Evaluation & Selection Proposal  
**Decision ID:** `DEC-API-DEF-02` — Authentication Provider & OAuth Server Selection  
**Status:** OWNER APPROVED TECHNOLOGY (Project Owner Approved — 2026-08-08)  
**Date:** 2026-08-08  
**Selected Technology:** Keycloak (Self-Hosted Open-Source Identity Server — Apache License 2.0)  
**Implementation Authorization:** NOT AUTHORIZED  

---

## 1. Executive Summary

This document presents the technical, security, operational, licensing, cost, and lock-in evaluation for **DEC-API-DEF-02 (Authentication Provider & OAuth Server Selection)** under the locked **CineVault OS Architecture Baseline V1** (`docs/ARCHITECTURE_BASELINE_V1.md`).

Four candidate architectural approaches were evaluated:
1. **Keycloak** (Self-Hosted Open-Source Identity Server — Apache 2.0)
2. **Auth0 by Okta** (Managed Identity Platform — SaaS)
3. **Zitadel** (Modern Cloud-Native & Open-Source Identity Platform — AGPL 3.0 / SaaS)
4. **AWS Cognito** (Cloud-Provider-Native Identity Service — AWS Managed)

### Recommended Selection for Owner Review
* **Recommended Candidate:** **Keycloak** (Self-Hosted Open-Source Identity Server — Apache 2.0)
* **Alternative Candidate:** **Zitadel** (Cloud / Self-Hosted Open-Source Identity Server — AGPL 3.0)
* **Governance Status:** `PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED`
* **Implementation Authorization:** `NOT AUTHORIZED` (No authentication code, secrets, OAuth client configuration, or cloud resources created).

---

## 2. Decision Under Evaluation

* **Decision ID:** `DEC-API-DEF-02`
* **Topic:** Authentication Provider & OAuth Server Technology Selection
* **Originating Baseline:** API Specification V1 (`docs/API_SPECIFICATION_V1.md`) & Security Architecture V1 (`docs/SECURITY_ARCHITECTURE_V1.md`)
* **Current Governance State:** `DEFERRED` (Postponed from initial architecture gates to technology evaluation phase).
* **Objective:** Evaluate candidate identity solutions against locked architecture requirements including public client authentication (OAuth 2.1 / OIDC with PKCE `S256`), Control Room Curator MFA (`DEC-SEC-PRP-02`), 15-minute curator session timeouts (`DEC-SEC-PRP-10`), RBAC role mapping, personal data isolation (`ADR-003`), and low protocol lock-in.

---

## 3. Canonical Architecture Requirements

Derived strictly from approved baseline documents (`ADR-001..004`, `API Specification V1`, `Security Architecture V1`, `Observability Architecture V1`, `Physical Database Design V1`):

```text
┌───────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────┐
│ Domain Area                           │ Architectural Requirement                 │ Canonical Source Baseline                 │
├───────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. Public API Identity                │ OAuth 2.1 / OIDC Authorization Code + PKCE│ API Spec V1 (DEC-API-PRP-02, DEC-API-06)  │
│ 2. Public User Roles                  │ Anonymous, Authenticated User (`CAT-2`)   │ Security Architecture V1 (RBAC Matrix)    │
│ 3. Control Room Curator Roles         │ Curator, System Administrator (`CAT-1/4`) │ Security Architecture V1 (RBAC Matrix)    │
│ 4. Control Room MFA Enforcement       │ Mandatory MFA for `/internal/v1/*`        │ Security V1 (DEC-SEC-PRP-02, DEC-SEC-OPN-01)│
│ 5. Privileged Session Timeout         │ 15-minute curator session timeout         │ Security V1 (DEC-SEC-PRP-10, DEC-SEC-12)  │
│ 6. Machine-to-Machine (M2M) Auth      │ mTLS / Short-Lived Service Tokens         │ Security V1 (DEC-SEC-PRP-01)              │
│ 7. Personal Data Isolation            │ `CAT-2` User Personal Data in `personal`  │ ADR-003, Physical DB V1 (DEC-PHYS-PRP-01) │
│ 8. Offline Sync ID Propagation        │ Client UUIDv7 `mutation_id` in tokens/claims│ ADR-004, API Spec V1 (DEC-API-PRP-06)    │
│ 9. Cryptographic Standards            │ TLS 1.3 transit, AES-256 storage, JWKS    │ Security V1 (DEC-SEC-PRP-09, DEC-SEC-11)  │
│ 10. Audit Log Traceability            │ UUIDv7 Correlation ID propagation in logs │ Observability V1 (DEC-OBS-PRP-01)         │
│ 11. Low Lock-In Constraint            │ Open OIDC standards; portable data        │ Infrastructure V1 (DEC-INFRA-DEF-01)      │
└───────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 4. Evaluation Scope

### In-Scope
* Comprehensive evaluation of 4 candidate identity solutions.
* Technical analysis across standardized capability, security, MFA, licensing, cost, and lock-in dimensions.
* Architectural fit mapping against locked CineVault OS baselines.
* Exit and migration protocol formulation.
* Formulation of a single recommended proposal for Control Room Owner Review.

### Out-of-Scope (Prohibited)
* Writing authentication source code, controllers, or middleware.
* Provisioning cloud identity tenants or self-hosted identity servers.
* Creating OAuth client IDs, secrets, certificates, or redirect URIs.
* Granting automatic technology approval or authorization to execute implementation.

---

## 5. Research Method

Evaluation findings are based on empirical verification of official vendor documentation, standards specs, and licensing frameworks:
* **RFC Standards:** OAuth 2.1 Draft, RFC 7636 (PKCE), RFC 7519 (JWT), RFC 6749 (OAuth 2.0), OpenID Connect Core 1.0.
* **Keycloak Documentation:** Official Red Hat & Keycloak Community Documentation (Apache 2.0, certified OIDC Provider).
* **Auth0 Documentation:** Okta Customer Identity Cloud official pricing & feature specs.
* **Zitadel Documentation:** Official Zitadel Open Source & Cloud documentation (AGPL 3.0 / OpenID Certified).
* **AWS Cognito Documentation:** Official AWS Cognito Developer Guide & AWS Pricing Calculator.

---

## 6. Candidate Approaches Evaluated

```text
┌─────────────────────────────────────────┬───────────────────────────────┬───────────────────────────────────────────┐
│ Candidate                               │ Architectural Model           │ Primary Technology Stack                  │
├─────────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 1. Keycloak                             │ Self-Hosted Open Source (CNCF)│ Java / Quarkus, PostgreSQL backend        │
│ 2. Auth0 by Okta                        │ Managed SaaS Platform         │ Cloud Multi-Tenant SaaS                   │
│ 3. Zitadel                              │ Cloud Native / Open Source    │ Go, CockroachDB / PostgreSQL backend      │
│ 4. AWS Cognito                          │ Cloud-Provider-Native Service │ AWS Managed Serverless Service            │
└─────────────────────────────────────────┴───────────────────────────────┴───────────────────────────────────────────┘
```

---

## 7. Standards Compatibility Analysis

Capabilities are evaluated using strict governance terminology: `SUPPORTED`, `SUPPORTED WITH CONDITIONS`, `REQUIRES ADDITIONAL COMPONENT`, `NOT VERIFIED`.

```text
┌───────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Standard / Feature            │ 1. Keycloak       │ 2. Auth0          │ 3. Zitadel        │ 4. AWS Cognito    │
├───────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ Certified OIDC Provider       │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │
│ OAuth 2.1 / Auth Code + PKCE  │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │
│ PKCE S256 Challenge Method    │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │
│ JWT Validation & JWKS         │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │
│ Token Revocation & Introspection│ SUPPORTED       │ SUPPORTED         │ SUPPORTED         │ SUPPORTED W/ COND.│
│ Custom Claims Injection       │ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│
│ Client Credentials (M2M)      │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │ SUPPORTED W/ COND.│
└───────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 8. Security Evaluation

```text
┌───────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Security Criterion            │ 1. Keycloak       │ 2. Auth0          │ 3. Zitadel        │ 4. AWS Cognito    │
├───────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ Zero-Trust mTLS Boundary      │ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│
│ Credential Isolation          │ SUPPORTED (Local) │ SUPPORTED (SaaS)  │ SUPPORTED (Local) │ SUPPORTED (SaaS)  │
│ Token Signing Key Rotation    │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │
│ Brute-Force & Bot Defense     │ SUPPORTED         │ SUPPORTED (Paid)  │ SUPPORTED         │ SUPPORTED W/ COND.│
│ Personal Data Perimeter       │ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│
└───────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 9. Authentication Flows Analysis

### 9.1 Public Client Flow (Mobile / Web)
* **Requirement:** OAuth 2.1 Authorization Code Flow with PKCE (`S256`).
* **Evaluation:** All 4 candidates support PKCE (`S256`). Keycloak, Auth0, Zitadel, and Cognito allow enforcing PKCE at the client realm level.

### 9.2 Control Room Curator Flow
* **Requirement:** Authenticated Curator Role + Mandatory MFA + 15-Minute Session Timeout (**DEC-SEC-PRP-02, DEC-SEC-PRP-10**).
* **Evaluation:** 
  * **Keycloak:** Keycloak provides global realm-level or client-level SSO session idle timeout configuration. However, enforcing a 15-minute session idle timeout *specifically for Curator/Admin roles* is **SUPPORTED WITH CONDITIONS**. It requires establishing a distinct, isolated client configuration for Control Room applications or configuring step-up authentication flow policies, as role-specific session idle timeouts are not natively applied to individual role tags out of the box.
  * **Zitadel:** Native passkey/MFA step-up authentication and configurable client session lifetime.
  * **Auth0:** Supports step-up MFA via Actions; idle session timeouts configurable per tenant/client.
  * **Cognito:** MFA supported; session timeout configuration options are less granular across custom roles.

### 9.3 Machine-to-Machine (M2M) Service Flow
* **Requirement:** Background worker & ingestion service token authentication (**DEC-SEC-PRP-01**).
* **Evaluation:** Keycloak, Zitadel, and Auth0 support M2M Client Credentials Grant. AWS Cognito supports M2M with per-token request billing.

---

## 10. Multi-Factor Authentication (MFA) Evaluation (`DEC-SEC-OPN-01`)

```text
┌───────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ MFA Factor                    │ 1. Keycloak       │ 2. Auth0          │ 3. Zitadel        │ 4. AWS Cognito    │
├───────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ TOTP (Authenticator Apps)     │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │
│ WebAuthn / Passkeys (FIDO2)   │ SUPPORTED         │ SUPPORTED (Paid)  │ SUPPORTED         │ SUPPORTED W/ COND.│
│ SMS MFA                       │ REQ. ADD. COMP.   │ REQ. ADD. COMP.   │ REQ. ADD. COMP.   │ REQ. ADD. COMP.   │
│ Step-Up / Adaptive MFA        │ SUPPORTED W/ COND.│ SUPPORTED (Paid)  │ SUPPORTED W/ COND.│ SUPPORTED (Paid)  │
└───────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 11. Service-to-Service Authentication Compatibility

* **Keycloak:** Can be integrated into service mesh perimeters (Istio/Envoy) via standard OIDC client credentials or token exchange.
* **Auth0:** M2M tokens issued via Auth0 Management API; requires outbound HTTPS validation to Auth0 cloud endpoints.
* **Zitadel:** Native gRPC / REST API support with service user keys.
* **AWS Cognito:** Requires integration with AWS IAM or AWS API Gateway for service tokens.

---

## 12. Session & Token Management

```text
┌───────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Session Management Feature    │ 1. Keycloak       │ 2. Auth0          │ 3. Zitadel        │ 4. AWS Cognito    │
├───────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ 15-Min Curator Idle Timeout   │ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│
│ Immediate Token Revocation    │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │ SUPPORTED W/ COND.│
│ Refresh Token Rotation        │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │
│ Admin Session Invalidation    │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │ SUPPORTED W/ COND.│
└───────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 13. Audit & Observability Integration

* **Keycloak:** Emits structured audit events (`LOGIN`, `LOGIN_ERROR`, `CODE_TO_TOKEN`, `LOGOUT`) with client IP and user identity. Can be configured to export metrics to Prometheus and structured JSON logs to standard collectors (**DEC-OBS-PRP-01, DEC-OBS-PRP-03**).
* **Zitadel:** Emits structured JSON event logs for all state changes. Native OpenTelemetry tracing and Prometheus metrics.
* **Auth0:** Exports audit logs via EventBridge or Webhooks (requires paid add-ons for real-time streaming).
* **AWS Cognito:** Audit logs routed through AWS CloudTrail / CloudWatch Logs.

---

## 14. Privacy & Personal Data Perimeter (`ADR-003`)

* **Self-Hosting (Keycloak / Zitadel):** Self-hosting can keep identity data within CineVault-controlled infrastructure, subject to deployment configuration, telemetry, external identity providers, email providers, backups, and other integrations. User credentials (`CAT-2`) are managed within private database perimeters (`personal` schema or dedicated identity DB).
* **SaaS Platforms (Auth0 / AWS Cognito):** User credentials and authentication IP logs are stored on 3rd-party cloud infrastructure, requiring data processor compliance agreements (GDPR DPA, data residency controls).

---

## 15. Licensing Analysis

```text
┌───────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Licensing Dimension           │ 1. Keycloak       │ 2. Auth0          │ 3. Zitadel        │ 4. AWS Cognito    │
├───────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ License Type                  │ Apache 2.0        │ Proprietary SaaS  │ AGPL 3.0 / SaaS   │ Proprietary AWS   │
│ Open Source Rights            │ Open Source       │ Closed Source     │ Open Source       │ Closed Source     │
│ Self-Hosting Authorized       │ YES               │ NO (Cloud only)   │ YES (AGPL rules)  │ NO (AWS only)     │
│ Commercial Lock-in Risk       │ LOW               │ HIGH              │ LOW               │ HIGH              │
└───────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 16. Cost Model & Detailed Assumptions

To prevent misleading comparisons, software/license costs, infrastructure costs, and commercial SaaS fees are explicitly separated under explicit usage assumptions.

### 16.1 Cost Model Assumptions
1. **User Population Assumption:** 10,000 Monthly Active Users (MAU) in Year 1 scaling to 100,000 MAU in Year 3.
2. **MFA Usage Assumption:** 100% of Control Room curators (approx. 20 accounts) require WebAuthn/TOTP MFA. 10% of public users opt into MFA.
3. **Infrastructure Assumption (Self-Hosted):** High-availability pair of small compute nodes (2 vCPU, 4GB RAM) backing PostgreSQL instance in AWS `us-east-1` region.
4. **Support Assumption:** Community self-supported for open-source options; standard developer support for SaaS options.
5. **Pricing Source & Date:** Official public vendor pricing pages verified as of August 2026.

```text
┌───────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Cost Component                │ 1. Keycloak       │ 2. Auth0          │ 3. Zitadel        │ 4. AWS Cognito    │
├───────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ Software / License Cost       │ $0 (Free Apache)  │ Tier-based SaaS   │ $0 (Self-Hosted)  │ Tier-based AWS    │
│ Estimated Monthly Infra (10k) │ ~$30 - $60/mo     │ Included in SaaS  │ ~$30 - $60/mo     │ Included in MAU   │
│ Estimated Monthly Infra (100k)│ ~$60 - $120/mo    │ Included in SaaS  │ ~$60 - $120/mo    │ Included in MAU   │
│ Estimated SaaS Cost (10k MAU) │ $0                │ ~$240 - $800/mo*  │ $0 (Self-hosted)  │ ~$50 - $150/mo*   │
│ Estimated SaaS Cost (100k MAU)│ $0                │ ~$1,200 - $2,500/mo* $0 (Self-hosted) │ ~$550 - $1,200/mo*│
│ Operational Staffing Cost     │ Self-Managed      │ Minimal           │ Self-Managed      │ Low               │
└───────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

> [!NOTE]
> **SAAS PRICING DISCLAIMER:** Exact enterprise SaaS prices marked with `*` cannot be reliably determined solely from public pricing without formal vendor quotes due to modular add-on costs (custom domains, advanced security, WebAuthn MFA features). Vendor confirmation is required.

---

## 17. Operational Complexity Evaluation

* **Keycloak:** Requires managing a containerized Quarkus service and backing PostgreSQL database. Operational responsibilities include security patching, database migrations, backup validation, and high-availability replica management.
* **Zitadel:** Modern Go binary with low memory footprint (~50MB). Requires containerized deployment management on PostgreSQL or CockroachDB.
* **Auth0:** Zero infrastructure server maintenance; fully managed by Okta. High operational convenience, but zero infrastructure control.
* **AWS Cognito:** Managed AWS serverless resource; zero server maintenance, but operational configuration managed through AWS APIs/Console.

---

## 18. Scalability & High Availability

* **Keycloak:** Scalable via container replica scaling backed by PostgreSQL Read Replicas and Infinispan distributed caching.
* **Zitadel:** Multi-region active-active scalability backed by CockroachDB or distributed PostgreSQL.
* **Auth0 / AWS Cognito:** Global SaaS multi-region availability backed by vendor SLAs (99.9% to 99.99%).

---

## 19. Disaster Recovery & Backup Compatibility

* **Keycloak / Zitadel:** Database state is included in standard PostgreSQL continuous WAL archival and Point-In-Time Recovery (PITR) strategy (**DEC-PHYS-PRP-04**). Aligns with CineVault's **RPO < 5 min / RTO < 1 hr** recovery targets (**DEC-OBS-INH-13**).
* **Auth0 / AWS Cognito:** Disaster recovery managed by vendor. User export/import APIs subject to rate limits.

---

## 20. Developer Experience & Tooling Support

* **Keycloak:** Excellent local development support via official Docker images (`quay.io/keycloak/keycloak`). Enables local container spin-up in `docker-compose` environments for local API testing (**DEC-INFRA-PRP-01**).
* **Zitadel:** Excellent local development support via container or Go binary.
* **Auth0:** Requires cloud tenant connection for local development or third-party mock servers.
* **AWS Cognito:** Local testing requires LocalStack or live AWS dev tenant.

---

## 21. Flutter Client Compatibility

* **Public Client:** Flutter mobile applications use standard AppAuth SDKs or PKCE OAuth libraries.
* **Compatibility:** All 4 candidates support standard OIDC discovery endpoints (`/.well-known/openid-configuration`), standard `/oauth/authorize` with PKCE `S256`, and `/oauth/token` exchange.

---

## 22. Migration & Exit Strategy Protocol

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       VENDOR EXIT & PORTABILITY PROTOCOL                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 1. Identity Data Portability vs Credential Portability:                         │
│    - Identity/user profile data is fully portable via standard JSON/SQL export. │
│    - Password-hash migration MAY be possible when the destination identity      │
│      system supports the same hashing algorithm, parameters, and credential      │
│      representation. Seamless credential migration is NOT guaranteed and        │
│      requires an exit/migration proof-of-concept.                               │
│ 2. Keycloak Realm Export Limitations:                                           │
│    - Keycloak realm export exports configurations and user records, but does    │
│      NOT guarantee migration of active sessions, revocation lists, or custom SPI│
│      runtime state.                                                             │
│ 3. Standard OIDC Tokens: CineVault API services validate standard JWTs via      │
│    JWKS endpoints; zero vendor SDK dependencies in core controllers.            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 23. Lock-In Analysis Matrix

```text
┌───────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Lock-In Dimension             │ 1. Keycloak       │ 2. Auth0          │ 3. Zitadel        │ 4. AWS Cognito    │
├───────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ Protocol Layer Lock-In        │ LOW (OIDC Std)    │ LOW (OIDC Std)    │ LOW (OIDC Std)    │ MODERATE          │
│ Residual Provider Lock-In     │ MODERATE (Configs)│ HIGH (Custom API) │ MODERATE (Configs)│ HIGH (AWS SDK)    │
│ User Data Portability         │ COMPLETE (SQL)    │ RESTRICTED (API)  │ COMPLETE (SQL)    │ RESTRICTED (API)  │
│ Credential Portability        │ UNCERTAIN (PoC)   │ RESTRICTED        │ UNCERTAIN (PoC)   │ RESTRICTED        │
│ Overall Exit Complexity       │ MODERATE          │ HIGH              │ MODERATE          │ HIGH              │
└───────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

> [!IMPORTANT]
> **REVISION ON PROTOCOL LOCK-IN:**  
> The authentication protocol layer exhibits **low protocol lock-in** due to OIDC standards. However, residual provider-specific lock-in exists across realm configurations, role/group mappings, user attributes, authorization policies, admin REST APIs, extensions, and operational setups. Standard OIDC interfaces reduce migration risk but do not eliminate migration effort.

---

## 24. Candidate Comparison Matrix

```text
┌───────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Evaluation Dimension          │ 1. Keycloak       │ 2. Auth0          │ 3. Zitadel        │ 4. AWS Cognito    │
├───────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ Open Standards (OIDC/PKCE)    │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │
│ Control Room MFA & Passkeys   │ SUPPORTED         │ PAYWALLED         │ SUPPORTED         │ LIMITED           │
│ 15-Min Curator Idle Timeout   │ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│
│ Personal Data Perimeter       │ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│ SUPPORTED W/ COND.│
│ Local Dev (Docker Compose)    │ NATIVE            │ CLOUD REQUIRED    │ NATIVE            │ LOCALSTACK REQ.   │
│ Open-Source License           │ Apache 2.0        │ Proprietary SaaS  │ AGPL 3.0          │ Proprietary Cloud │
│ Protocol Layer Lock-In        │ LOW               │ LOW               │ LOW               │ MODERATE          │
│ Overall Architectural Fit     │ STRONG FIT        │ FIT W/ CONDITIONS │ STRONG FIT        │ WEAK FIT          │
└───────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 25. Architectural Fit Assessment

### 1. Keycloak: `STRONG FIT`
* **Rationale:** Open-source (Apache 2.0), certified OIDC provider, PKCE `S256` support, WebAuthn/passkey MFA support, customizable session idle rules via client isolation, local Docker Compose developer experience, and low protocol lock-in.

### 2. Zitadel: `STRONG FIT`
* **Rationale:** Modern open-source (AGPL 3.0) identity server written in Go. Excellent passkey support, native OIDC, low resource overhead, and strong open-source alternative to Keycloak.

### 3. Auth0 by Okta: `FIT WITH CONDITIONS`
* **Rationale:** Outstanding developer experience and quick setup, but paywalls passkey WebAuthn MFA, introduces MAU scaling costs, delegates user PII to 3rd-party SaaS, and creates commercial vendor lock-in.

### 4. AWS Cognito: `WEAK FIT`
* **Rationale:** Deeply tied to AWS ecosystem, limited custom MFA flexibility, proprietary SDK dependencies, and less granular session controls for Control Room curation workflows.

---

## 26. Decision-Critical Risks

1. **Keycloak Operational Ownership:** High operational burden of managing container deployment, JVM/Quarkus tuning, database indexing, and security patching.
2. **Upgrade & Security-Patch Responsibility:** Responsibility for monitoring CVE disclosures and performing Keycloak minor/major upgrades rests entirely on CineVault operators.
3. **Authentication Data Migration Complexity:** Migrating identity data between providers involves schema mappings, role transformations, and workflow adjustments.
4. **Password-Hash Portability Uncertainty:** Password-hash migration is subject to algorithm compatibility and requires an explicit proof-of-concept.
5. **Provider-Specific Configuration Migration:** Realm definitions, client scopes, and authentication execution flows are proprietary to Keycloak and cannot be directly imported into alternative identity servers.
6. **High Availability Requirements:** Ensuring 99.9% read availability for authentication endpoints requires multi-pod deployments and resilient PostgreSQL database backends.
7. **MFA & Account Recovery Operational Responsibility:** Self-hosting requires CineVault to operate custom SMS/Email gateways and administrative account recovery workflows.
8. **Backup & Restore Validation:** Failure to test Point-In-Time Recovery (PITR) of the Keycloak database could lead to identity state desynchronization during disasters.
9. **Key Rotation & Compromise Recovery:** Signing-key rotation must be managed correctly to avoid invalidating active client tokens across API gateways.
10. **Dependency on Future Release Behavior:** Future Keycloak major release updates could deprecate specific SPIs or configuration properties.

---

## 27. Technology Recommendation

```text
===============================================================================
PROPOSED SELECTION FOR OWNER REVIEW:
RECOMMENDED CANDIDATE: Keycloak (Self-Hosted Open-Source Identity Server — Apache 2.0)
ALTERNATIVE CANDIDATE: Zitadel (Open-Source Identity Server — AGPL 3.0)
===============================================================================
```

### Justification Summary
Keycloak is recommended because it aligns with locked CineVault OS architecture principles:
1. **Standards Compliance:** Certified OIDC provider supporting OAuth 2.1 Authorization Code Flow with PKCE (`S256`).
2. **Security & MFA:** Free WebAuthn/passkey and TOTP MFA for Control Room curators (**DEC-SEC-PRP-02**), with 15-minute session idle timeout support via client isolation (**DEC-SEC-PRP-10**).
3. **Data Perimeter:** Manages credentials within private PostgreSQL perimeters (**ADR-003**).
4. **Low Lock-In:** Open-source (Apache 2.0) with standard JWT/JWKS token formats.
5. **Cost Control:** Eliminates seat-based and MAU-based SaaS billing spikes.

---

## 28. Governance Classification

* **Current Governance State:** `DEFERRED` (`DEC-API-DEF-02`)
* **Evaluation Status:** `COMPLETE`
* **Proposal Classification:** `PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED`
* **Final Technology Approval State:** `NOT GRANTED`
* **Implementation Authorization:** `NOT AUTHORIZED`

---

## 29. Owner Approval Requirement

This evaluation report is submitted to the Control Room for formal Project Owner review.

```text
[ ] Project Owner Sign-Off: Approve Keycloak as Authentication Provider Technology for DEC-API-DEF-02
[ ] Project Owner Sign-Off: Approve Alternative Candidate (Zitadel)
[ ] Project Owner Decision: Reject Recommendation / Request Further Benchmark
```

---

## 30. Implementation Safety Verification

```text
Application Code Created:        0
SQL Scripts Executed:            0
Database Migrations:             0
OAuth Clients Provisioned:       0
Secrets / Keys Created:          0
Cloud Resources Provisioned:     0
Docker Containers Deployed:      0
===============================================================================
STATUS: GOVERNANCE EVALUATION ONLY — IMPLEMENTATION STRICTLY BLOCKED
===============================================================================
```

---

## 31. Sources & Evidence Base

1. **RFC 7636 (PKCE):** [IETF OAuth Proof Key for Code Exchange Standard](https://datatracker.ietf.org/doc/html/rfc7636)
2. **Keycloak Documentation:** [Keycloak Official Server Administration Guide & Apache 2.0 License Specs](https://www.keycloak.org/documentation)
3. **Zitadel Documentation:** [Zitadel Open Source Docs & AGPL 3.0 Specs](https://zitadel.com/docs)
4. **Auth0 Pricing Specs:** [Auth0 by Okta Customer Identity Cloud Pricing Tiers](https://auth0.com/pricing)
5. **AWS Cognito Pricing:** [Amazon Cognito Pricing Calculator & Developer Guide](https://aws.amazon.com/cognito/pricing/)

---
