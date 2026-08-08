# CineVault OS — MFA Implementation Prerequisites V1

**Document Type:** Implementation Prerequisite Specification  
**Decision ID:** `DEC-SEC-OPN-01` — Control Room MFA Protocol Standard  
**Approved Strategy:** Option D — WebAuthn/FIDO2 Primary + Backup WebAuthn Key + Restricted TOTP Fallback + Mandatory Fresh WebAuthn for High-Risk Operations + Dual-Admin Break-Glass  
**Owner Approval Date:** 2026-08-08  
**Status:** Prerequisite Gate Active (Implementation NOT YET AUTHORIZED)  
**Scope:** Mandatory Technical, Governance, Security, and Testing Prerequisites Required BEFORE Keycloak MFA Execution Flow Scripting or Code Implementation  

---

## 1. Purpose

The purpose of this specification is to define the mandatory technical prerequisites, WebAuthn enrollment protocols, step-up execution rules, dual-admin break-glass procedures, and security acceptance test specifications that MUST be established BEFORE Keycloak MFA flows are configured or authentication source code is written.

Following Project Owner approval of **DEC-SEC-OPN-01** on **2026-08-08**, the Option D Hybrid MFA Strategy is the approved security policy. However, policy approval DOES NOT authorize physical code implementation, user credential creation, or infrastructure deployment.

---

## 2. Master Prerequisites Status Matrix

```text
┌───────────────────────────────────────┬───────────────────────┬───────────────────────────────────────────┐
│ Implementation Prerequisite           │ Status                │ Dependency / Baseline Reference           │
├───────────────────────────────────────┼───────────────────────┼───────────────────────────────────────────┤
│ 1. WebAuthn Origin Binding Spec (`rpId`)│ READY               │ Bound to CineVault Control Room Domain    │
│ 2. Primary Authenticator Enrollment   │ READY                 │ Mandatory Hardware Security Key Onboarding│
│ 3. Backup Authenticator Enrollment    │ READY                 │ Secondary Hardware Key Vault Storage      │
│ 4. TOTP Restricted Fallback Policy    │ READY                 │ Standard Login Only; High-Risk Prohibited │
│ 5. High-Risk Operation Step-Up Flow   │ READY                 │ Fresh WebAuthn Touch Required             │
│ 6. 60-Second Re-Auth Window           │ READY                 │ Prompt Expiry within 60 Seconds           │
│ 7. Curator / Admin Role Mapping       │ READY                 │ Keycloak Client Scope Isolation           │
│ 8. Anti-Bypass Recovery Rule          │ READY                 │ Password Resets DO NOT Bypass MFA         │
│ 9. Dual-Admin Break-Glass Quorum      │ READY                 │ Out-of-Band Dual-Admin Authentication     │
│ 10. 2-Hour Break-Glass Expiry         │ READY                 │ Hard 2-Hour Session Expiry                │
│ 11. Structured Audit Log Integration  │ READY                 │ UUIDv7 Correlation ID Stream Integration  │
│ 12. Post-Incident Credential Rotation │ READY                 │ Key Revocation & Password Invalidation    │
│ 13. Security Acceptance Test Harness  │ READY                 │ 6 Automated Security Acceptance Tests     │
│ 14. Keycloak Container Engine         │ READY                 │ Keycloak 26.x (`DEC-API-DEF-02`)          │
│ 15. Orchestration & IaC Scripting     │ BLOCKED               │ Awaiting IaC (`DEC-INFRA-DEF-02`)         │
│ 16. SIEM Audit Aggregator             │ BLOCKED               │ Awaiting SIEM (`DEC-SEC-OPN-02`)          │
└───────────────────────────────────────┴───────────────────────┴───────────────────────────────────────────┘
```

---

## 3. WebAuthn Configuration & Origin Binding Prerequisites

* **Relying Party ID (`rpId`):** Must be configured to match the exact canonical FQDN of the CineVault Control Room domain.
* **Attestation Preference:** Enforce `direct` or `indirect` attestation verification to validate genuine FIDO2 hardware security key authenticators.
* **User Verification:** Enforce `required` or `preferred` user verification (biometric PIN / hardware PIN).

---

## 4. Primary & Backup Authenticator Enrollment Prerequisites

1. **Primary Key Onboarding:** During initial curator onboarding, curators MUST enroll a primary WebAuthn hardware security key (e.g. YubiKey 5 Series) or device-bound platform passkey.
2. **Backup Key Onboarding:** Curators MUST enroll a secondary independent WebAuthn hardware key stored in a secure physical location.
3. **Enrollment Verification:** Enrollment of new authenticators requires out-of-band admin identity verification and step-up re-authentication.

---

## 5. TOTP Restricted Fallback Policy Prerequisites

* **Scope:** TOTP (RFC 6238) is permitted ONLY for standard Curator login authentication when WebAuthn keys are temporarily unavailable.
* **Strict Prohibition:** Keycloak execution flows MUST be configured such that TOTP CANNOT authorize high-risk operations (entity merges/splits, role grants, PII conflict resolution, provider key operations, or security config changes).

---

## 6. High-Risk Operation Step-Up Prerequisites

* **Operations Covered:** Entity Merges (`CAT-1`), Entity Splits (`CAT-1`), Role Promotions, Personal Data Dispute Resolutions (`CAT-2`), Provider Credential Operations, Security Configuration Changes.
* **Step-Up Rule:** Enforce a fresh WebAuthn prompt requiring physical touch of a WebAuthn security key within a **60-second window** prior to operation execution.

---

## 7. Dual-Admin Break-Glass Quorum Prerequisites

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│ BREAK-GLASS IMPLEMENTATION PREREQUISITES                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 1. Dual-Admin Quorum: Triggering emergency access requires out-of-band dual    │
│    authentication from TWO distinct System Administrators.                      │
│ 2. Ephemeral Credentials: Emergency keys stored in physical safes.               │
│ 3. 2-Hour Hard Expiry: Break-glass session tokens expire after exactly 2 hours.  │
│ 4. Post-Incident Protocol: Triggers mandatory credential rotation, session      │
│    revocation, and formal Control Room security review.                         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Security Acceptance Test Suite Specifications

Before production launch, an automated security test harness MUST validate:
1. **Phishing Immunity Test:** Verify WebAuthn authentication requests fail when origin headers do not match `rpId`.
2. **TOTP High-Risk Prohibition Test:** Verify that attempting an entity merge/split using a TOTP code is rejected (`HTTP 403 Forbidden`).
3. **60-Second Prompt Expiry Test:** Verify that high-risk operation requests submitted >60s after WebAuthn re-prompt are rejected.
4. **Anti-Bypass Recovery Test:** Verify that password reset workflows require MFA re-verification before granting curator access.
5. **Break-Glass Expiry Test:** Verify that emergency break-glass sessions terminate automatically after 2 hours.
6. **Dual-Admin Quorum Test:** Verify that single-admin break-glass requests are rejected.

---

## 9. Implementation Safety Controls

```text
Application Code Files Created: 0
Keycloak Realms Configured:     0
MFA Flow Execution Scripts:     0
Secrets / OTP Seeds Generated:  0
Docker Containers Deployed:     0
===============================================================================
STATUS: PREREQUISITE SPECIFICATION ONLY — IMPLEMENTATION NOT AUTHORIZED
===============================================================================
```

---
