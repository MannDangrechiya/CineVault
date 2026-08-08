# CineVault OS — Technology Decision Record: Authentication Provider & OAuth Server V1

**Document Type:** Formal Technology Decision Record  
**Decision ID:** `DEC-API-DEF-02` — Authentication Provider & OAuth Server Selection  
**Status:** OWNER APPROVED TECHNOLOGY  
**Owner Approval Date:** 2026-08-08  
**Selected Technology:** Keycloak (Self-Hosted Open-Source Identity Server — Apache License 2.0)  
**Implementation Authorization:** NOT AUTHORIZED (Prerequisites & Technology Evaluation Phase Active)  

---

## 1. Decision ID & Metadata

* **Decision ID:** `DEC-API-DEF-02`
* **Topic:** Authentication Provider & OAuth Server Technology Selection
* **Originating Baseline:** API Specification V1 (`docs/API_SPECIFICATION_V1.md`) & Security Architecture V1 (`docs/SECURITY_ARCHITECTURE_V1.md`)
* **Governance Transition:** `DEFERRED` ──▶ `OWNER APPROVED TECHNOLOGY`
* **Owner Approval Date:** 2026-08-08
* **Evaluation Artifact:** [EVAL_AUTHENTICATION_PROVIDER_V1.md](file:///c:/Desktop/flutter_projects/CineVault/docs/evaluations/EVAL_AUTHENTICATION_PROVIDER_V1.md)

---

## 2. Problem Statement

CineVault OS requires a secure, standards-compliant, vendor-neutral identity provider to handle public client authentication (mobile/web apps), Control Room curator access, machine-to-machine worker tokens, and RBAC role propagation without introducing commercial seat-based paywalls, user PII data leakage, or vendor lock-in.

---

## 3. Locked Architecture Requirements

Derived from locked baseline documents (`ADR-001..004`, `API Specification V1`, `Security Architecture V1`, `Observability Architecture V1`, `Physical Database Design V1`):
1. **Public Client OAuth:** OAuth 2.1 / OIDC Authorization Code Flow with PKCE (`S256`).
2. **Control Room Curation:** Curator & System Administrator role enforcement with mandatory MFA (**DEC-SEC-PRP-02**).
3. **Privileged Session Timeout:** 15-minute curator session idle timeout (**DEC-SEC-PRP-10**).
4. **Machine-to-Machine Auth:** Service-to-service token authorization (**DEC-SEC-PRP-01**).
5. **Personal Data Isolation:** User PII credentials isolated within private perimeters (**ADR-003**).
6. **Low Lock-In:** Open OIDC standards; portable JWT/JWKS token formats.

---

## 4. Candidates Evaluated

1. **Keycloak:** Self-Hosted Open-Source Identity Server (Apache 2.0) — **SELECTED**
2. **Zitadel:** Open-Source Identity Server (AGPL 3.0 / SaaS) — *REJECTED / ALTERNATIVE*
3. **Auth0 by Okta:** Managed SaaS Platform — *REJECTED* (Paywalled MFA, MAU scaling costs)
4. **AWS Cognito:** Cloud-Native Managed Service — *REJECTED* (AWS lock-in, limited custom MFA)

---

## 5. Selected Technology

```text
===============================================================================
SELECTED TECHNOLOGY: Keycloak
ARCHITECTURAL MODEL: Self-Hosted Open-Source Identity Server
LICENSE:             Apache License 2.0
CNCF GOVERNANCE:     CNCF Incubating Project (Red Hat / Community Supported)
===============================================================================
```

---

## 6. Rationale: Why Keycloak Was Selected

1. **Standards Compliance:** Fully certified OIDC Provider supporting OAuth 2.1 Authorization Code Flow with PKCE (`S256`).
2. **Security & MFA:** Free WebAuthn/passkey and TOTP MFA for Control Room curators (**DEC-SEC-PRP-02**), with configurable session idle timeout policies (**DEC-SEC-PRP-10**).
3. **Data Perimeter:** Keeps user credentials within CineVault-controlled PostgreSQL database perimeters (**ADR-003**).
4. **Low Lock-In:** Open-source (Apache 2.0) with standard JWT/JWKS token formats.
5. **Cost Predictability:** Eliminates seat-based and MAU-based SaaS billing spikes.

---

## 7. Alternatives Rejected / Deferred

* **Zitadel:** Rejected as primary due to AGPL 3.0 license considerations vs Apache 2.0; preserved as official alternative candidate.
* **Auth0 by Okta:** Rejected due to $43k+ 36-month TCO, WebAuthn MFA paywalling, and 3rd-party SaaS PII delegation.
* **AWS Cognito:** Rejected due to AWS cloud vendor lock-in and limited session configuration granularities.

---

## 8. Security Implications

* **Token Validation:** API Gateways validate standard JWT signatures via Keycloak JWKS endpoints (`/.well-known/jwks.json`).
* **Zero Credential Exposure:** Provider API keys and database credentials stored exclusively in server-side Secrets Managers.
* **Operational Security Burden:** Keycloak security patching, CVE tracking, and JVM container hardening rest on CineVault operators.

---

## 9. Licensing Compliance

* **License:** Apache License 2.0.
* **Compliance:** 100% free open-source software with unrestricted commercial, modification, and redistribution rights. Zero per-user or MAU license fees.

---

## 10. Operational Implications

* **Infrastructure:** Deployable as high-availability Quarkus container pairs backed by PostgreSQL.
* **Maintenance:** Requires automated database migration execution, container upgrades, and continuous WAL archival integration (**DEC-PHYS-PRP-04**).

---

## 11. Cost Assumptions Summary

* **Estimated Infra Cost (10k MAU):** ~$30 - $60/month (Self-Hosted compute nodes).
* **Estimated Infra Cost (100k MAU):** ~$60 - $120/month.
* **36-Month Total Cost (100k MAU):** ~$2,160 (Compute/Infra) vs $43,200+ for Auth0 SaaS.

---

## 12. Lock-In Assessment

* **Protocol Layer:** Low protocol lock-in due to OIDC / OAuth 2.1 standard interfaces.
* **Residual Lock-In:** Provider-specific configuration lock-in exists across Keycloak realms, client scopes, and authentication execution flows.
* **Data Portability:** User profile data is SQL exportable.

---

## 13. Migration & Exit Requirements

* **Password-Hash Portability Uncertainty:** Password-hash migration is subject to algorithm compatibility (PBKDF2/Argon2) and requires a dedicated migration proof-of-concept (PoC) before any future provider replacement.
* **Zero Core Application Lock-In:** Core API controllers MUST NOT import Keycloak SDKs or depend on Keycloak Admin APIs.

---

## 14. Ten Explicit Owner Approval Conditions

> [!IMPORTANT]
> **MANDATORY IMPLEMENTATION CONDITIONS (Project Owner Approved 2026-08-08):**
> 1. Authentication integration MUST use standard OAuth/OIDC interfaces.
> 2. Authorization Code + PKCE (`S256`) MUST be used for applicable public clients.
> 3. CineVault domain identity and authorization models MUST remain independent of Keycloak-specific persistence structures.
> 4. Core application services MUST NOT become dependent on Keycloak Admin APIs, SPIs, extensions, or proprietary SDKs unless separately justified and approved.
> 5. Password-hash portability is NOT considered guaranteed; a future authentication migration proof-of-concept MUST verify credential migration feasibility before exit.
> 6. The 15-minute privileged curator session requirement MUST be validated through an explicit security acceptance test.
> 7. Keycloak high availability, backup/restore, upgrade, key rotation, compromise recovery, and operational monitoring MUST be validated before production authorization.
> 8. MFA implementation remains governed by **DEC-SEC-OPN-01** (MFA Protocol Evaluation). Keycloak selection DOES NOT silently resolve **DEC-SEC-OPN-01**.
> 9. No cloud provider, WAF, API gateway, cache, queue, CI/CD system, observability backend, or other deferred technology is approved by this decision.
> 10. Keycloak is approved as the authentication technology ONLY. This decision DOES NOT authorize code implementation or production deployment.

---

## 15. Implementation Prerequisites

Prior to code implementation, all items in [AUTHENTICATION_IMPLEMENTATION_PREREQUISITES_V1.md](file:///c:/Desktop/flutter_projects/CineVault/docs/evaluations/AUTHENTICATION_IMPLEMENTATION_PREREQUISITES_V1.md) MUST be established and validated.

---

## 16. Owner Approval Record

* **Approved By:** Project Owner via Control Room Workflow
* **Approval Date:** 2026-08-08
* **Approval Status:** `CONFIRMED`

---

## 17. Decision Status

```text
===============================================================================
DECISION STATUS: OWNER APPROVED TECHNOLOGY
IMPLEMENTATION AUTHORIZATION: NOT AUTHORIZED
===============================================================================
```

---
