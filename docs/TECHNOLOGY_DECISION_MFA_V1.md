# CineVault OS — Technology Decision Record: Control Room MFA Protocol Standard V1

**Document Type:** Formal Technology & Security Policy Decision Record  
**Decision ID:** `DEC-SEC-OPN-01` — Control Room MFA Protocol Standard  
**Status:** OWNER APPROVED SECURITY / TECHNOLOGY POLICY  
**Owner Approval Date:** 2026-08-08  
**Selected Strategy:** Option D — WebAuthn/FIDO2 Primary + Backup WebAuthn Key + Restricted TOTP Fallback + Mandatory Fresh WebAuthn for High-Risk Operations + Dual-Admin Break-Glass  
**Implementation Authorization:** NOT AUTHORIZED (Prerequisites & Technology Evaluation Phase Active)  

---

## 1. Decision ID & Metadata

* **Decision ID:** `DEC-SEC-OPN-01`
* **Topic:** Control Room Multi-Factor Authentication (MFA) Protocol Standard Evaluation
* **Originating Baseline:** Security Architecture V1 (`docs/SECURITY_ARCHITECTURE_V1.md`, `DEC-SEC-PRP-02`, `DEC-SEC-PRP-10`) & Keycloak Approval Condition #8 (`docs/TECHNOLOGY_DECISION_AUTHENTICATION_V1.md`)
* **Governance Transition:** `OPEN` ──▶ `OWNER APPROVED SECURITY / TECHNOLOGY POLICY`
* **Owner Approval Date:** 2026-08-08
* **Evaluation Artifact:** [EVAL_MFA_PROTOCOL_V1.md](file:///c:/Desktop/flutter_projects/CineVault/docs/evaluations/EVAL_MFA_PROTOCOL_V1.md)

---

## 2. Security Problem Statement

Control Room curators possess administrative privileges to execute canonical catalog entity merges and splits (`CAT-1`), review AI curation proposals (`CAT-6`), manage personal data disputes (`CAT-2`), and modify provider security configurations. Relying solely on single-factor passwords or phishable TOTP codes exposes administrative curation to real-time reverse-proxy phishing attacks (e.g. Evilginx) and unauthorized destructive catalog operations.

---

## 3. Locked Architecture Requirements

Derived from locked baseline documents (`ADR-001..004`, `Security Architecture V1`, `Observability Architecture V1`, `Keycloak Approval Conditions`):
1. **Control Room MFA Enforcement:** Mandatory MFA for `/internal/v1/*` endpoints (**DEC-SEC-PRP-02**).
2. **Privileged Session Timeout:** 15-minute curator session idle timeout (**DEC-SEC-PRP-10**).
3. **Destructive Action Re-Auth:** Re-authentication for entity merges/splits (**DEC-SEC-INH-12**, **DEC-SEC-PRP-04**).
4. **Audit Logging:** Structured audit event emission with UUIDv7 correlation IDs (**DEC-OBS-PRP-01**).
5. **Anti-Bypass Recovery Rule:** Account recovery MUST NOT become an unauthenticated MFA bypass.

---

## 4. Evaluated Approaches

1. **Option A:** WebAuthn Primary + Unlimited TOTP Fallback (*REJECTED — Phishing bypass risk*)
2. **Option B:** WebAuthn Primary + Backup WebAuthn Key + Controlled Recovery (*REJECTED — Operational lockout risk*)
3. **Option C:** WebAuthn/Passkey Primary + Secondary WebAuthn Authenticator (*REJECTED — Personal cloud keychain dependency*)
4. **Option D:** Hybrid Strategy (WebAuthn Primary + Backup WebAuthn Key + Restricted TOTP + Fresh WebAuthn for High-Risk Ops + Dual-Admin Break-Glass) — **SELECTED**

---

## 5. Selected Strategy

```text
===============================================================================
SELECTED MFA STRATEGY: Option D Hybrid Strategy
PRIMARY FACTOR:        WebAuthn / FIDO2 Hardware Security Key or Device-Bound Passkey
BACKUP FACTOR:         Secondary Registered WebAuthn / FIDO2 Hardware Security Key
RESTRICTED FALLBACK:   TOTP (RFC 6238) — Standard Login Only (Prohibited for High-Risk Ops)
HIGH-RISK RE-AUTH:     Mandatory Fresh WebAuthn (60-second window)
BREAK-GLASS:           Dual-Administrator Quorum (2-Hour Max Window)
===============================================================================
```

---

## 6. Rationale: Why WebAuthn / FIDO2

WebAuthn/FIDO2 security keys provide **origin-bound asymmetric cryptography** (`rpId`). Browser origin validation ensures that credentials cannot be intercepted or relayed by phishing proxy servers (Evilginx), providing robust phishing resistance for privileged administrative access.

---

## 7. TOTP Restriction Policy

* **Classification:** TOTP is classified as **`PHISHABLE`**.
* **Restriction:** TOTP is permitted **ONLY** as a restricted fallback for standard Curator login authentication.
* **Strict Prohibition:** TOTP is strictly **PROHIBITED** for high-risk privileged operations. TOTP CANNOT authorize entity merges, entity splits, role promotions, PII dispute resolutions, provider key ops, or security configuration changes.

---

## 8. Backup Authenticator Policy

Curators MUST register at least **two** independent WebAuthn/FIDO2 authenticators (a primary hardware key + a secondary hardware backup key stored in a secure location) during onboarding to prevent single-point-of-failure lockouts.

---

## 9. High-Risk Operation Policy

Fresh WebAuthn authentication (physical touch of a WebAuthn security key) is **MANDATORY** for the following 6 high-risk operations:
1. **Entity Merge (`CAT-1`):** Combining duplicate catalog titles/editions.
2. **Entity Split (`CAT-1`):** Separating combined catalog entities.
3. **Role Promotion:** Granting Curator or Administrator privileges.
4. **Personal Data Conflict Resolution (`CAT-2`):** Resolving user data dispute records.
5. **Provider Credential / Key Operations:** Rotating or accessing external API keys.
6. **Security Configuration Changes:** Modifying system security, network, or RBAC rules.

---

## 10. Re-Authentication Policy (60-Second Window)

* **Policy Rule:** High-risk operations require a fresh WebAuthn authentication prompt executed within a **60-second window** prior to operation execution (**`OWNER APPROVED SECURITY / OPERATIONAL POLICY`**).
* **Scope:** Re-authentication does NOT extend active session validity indefinitely.

---

## 11. Recovery Policy

1. Primary recovery utilizes the pre-registered secondary WebAuthn hardware key.
2. If both keys are lost, curator authenticates via restricted TOTP fallback for standard login + triggers mandatory out-of-band dual-administrator identity verification.
3. Password reset emails DO NOT grant MFA bypass.

---

## 12. Break-Glass Policy (`OWNER APPROVED POLICY`)

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│ APPROVED BREAK-GLASS EMERGENCY SPECIFICATION                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 1. Dual-Admin Quorum: Invocation requires out-of-band dual-administrator presence│
│    (two distinct System Administrators must authenticate out-of-band).         │
│ 2. Access Duration Window: Maximum 2 hours. Access automatically expires.       │
│ 3. Privilege Scope: Access is audit-logged with mandatory full session recording. │
│ 4. Post-Incident Requirements: Immediate credential rotation, Keycloak key     │
│    invalidation, and formal Control Room post-incident security review.           │
│ 5. Anti-Bypass Rule: Break-glass MUST NOT become a standard MFA bypass.         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 13. Keycloak Compatibility

* **WebAuthn Authenticators:** Supported natively via Keycloak WebAuthn execution flows.
* **TOTP Forms:** Supported natively via Keycloak OTP forms.
* **Step-Up Authentication:** Supported via client-specific authentication flows and `max_age` prompt enforcement (`SUPPORTED WITH CONDITIONS`).

---

## 14. Security Implications

* Eliminates reverse-proxy phishing attacks against Control Room curation endpoints.
* Prevents single compromised curator credentials from silently executing destructive catalog merges/splits.

---

## 15. Operational Implications

* Requires procuring 2 hardware security keys per curator (approx. 40 keys for 20 curators).
* Requires establishing curator onboarding SOPs and physical key inventory management.

---

## 16. Key Decision Risks

1. **Hardware Key Loss:** Risk of curator lockout if both primary and secondary keys are lost simultaneously.
2. **Keycloak Execution Flow Misconfiguration:** Risk of misconfiguring Keycloak step-up flows, allowing silent bypass of fresh WebAuthn re-prompts for entity merges/splits.

---

## 17. Risk Mitigations

* Mandate 2 registered WebAuthn keys per curator.
* Implement automated security acceptance tests validating 60-second fresh WebAuthn enforcement for merges/splits.
* Enforce dual-administrator break-glass quorum with 2-hour hard expiry.

---

## 18. Owner Approval Record

* **Approved By:** Project Owner via Control Room Workflow
* **Approval Date:** 2026-08-08
* **Approval Status:** `CONFIRMED`

---

## 19. Implementation Prerequisites

Prior to implementation, all items in [MFA_IMPLEMENTATION_PREREQUISITES_V1.md](file:///c:/Desktop/flutter_projects/CineVault/docs/evaluations/MFA_IMPLEMENTATION_PREREQUISITES_V1.md) MUST be established and validated.

---

## 20. Decision Status

```text
===============================================================================
DECISION STATUS: OWNER APPROVED SECURITY / TECHNOLOGY POLICY
IMPLEMENTATION AUTHORIZATION: NOT AUTHORIZED
===============================================================================
```

---
