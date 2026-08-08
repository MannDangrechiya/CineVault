# CineVault OS — Technology Evaluation: SIEM / Security Analytics V1

**Document Type:** Technology Evaluation & Selection Proposal  
**Decision ID:** `DEC-SEC-OPN-02` — SIEM / Security Analytics Platform Selection  
**Status:** Evaluation Complete — Awaiting Owner Approval  
**Date:** 2026-08-08  
**Selected Technology Recommendation:** Wazuh (GPLv2 Open-Source SIEM & XDR Engine)  
**Alternative Candidate:** OpenSearch Security Analytics (Apache License 2.0)  
**Governance State:** PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED  
**Implementation Authorization:** NOT AUTHORIZED  

---

## 1. Decision Under Evaluation

* **Decision ID:** `DEC-SEC-OPN-02`
* **Topic:** SIEM & Security Analytics Platform Selection
* **Originating Baseline:** Security Architecture V1 (`docs/SECURITY_ARCHITECTURE_V1.md`, `DEC-SEC-PRP-11`)
* **Current Governance State:** `OPEN` → `PROPOSED` (Awaiting Owner Review)
* **Objective:** Select a Security Information and Event Management (SIEM) and Extended Detection and Response (XDR) platform to analyze security audit logs (`DEC-SEC-PRP-08`), detect privileged Control Room authentication anomalies, monitor Keycloak MFA events, enforce audit log tamper checks, and evaluate MITRE ATT&CK security threat rules.

---

## 2. Canonical Architecture Requirements

Derived from locked baseline specifications (`Security Architecture V1`, `Observability Architecture V1`):

```text
┌───────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────┐
│ Feature / Capability Requirement      │ Architectural Specification               │ Canonical Source Reference                │
├───────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. Mandatory Audit Log Integrity      │ Tamper check & cryptographic hash validation│ Security V1 (DEC-SEC-PRP-11, SEC-OPN-02)│
│ 2. Keycloak Auth & MFA Threat Detection│ Real-time detection of brute-force & MFA fail│ Security V1 (DEC-SEC-PRP-02, SEC-OPN-01)│
│ 3. SIGMA & MITRE ATT&CK Mapping       │ Out-of-the-box rule evaluation engine     │ Security V1 (DEC-SEC-PRP-11)              │
│ 4. Personal Data Isolation Safeguards │ Zero ingestion of CAT-2 user personal data│ Security V1 (DEC-SEC-PRP-08, ADR-003)    │
│ 5. Permissive Open-Source Licensing   │ Open source (No proprietary SaaS lock-in) │ Security V1 (DEC-SEC-OPN-02)              │
└───────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Architecture Dependencies

* **Identity Provider:** Keycloak authentication audit logs (`DEC-API-DEF-02`).
* **MFA Architecture:** Control Room WebAuthn hybrid logs (`DEC-SEC-OPN-01`).
* **API Gateway & Proxy:** Kong Gateway access logs (`DEC-API-DEF-03`).

---

## 4. Candidate Technologies Identified

Four security analytics platforms were evaluated:

1. **Wazuh (GPLv2 Open Source):** Enterprise open-source SIEM & XDR platform providing log analysis, file integrity monitoring (FIM), vulnerability detection, and active threat response.
2. **Security Onion (GPLv2 Open Source):** Enterprise security monitoring & threat hunting platform.
3. **OpenSearch Security Analytics (Apache 2.0):** OpenSearch security analytics plugin.
4. **Datadog Cloud SIEM (Proprietary SaaS):** SaaS cloud security management tool.

---

## 5. Candidate Evaluation & Feature Compatibility Matrix

```text
┌───────────────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Dimension / Feature                   │ 1. Wazuh          │ 2. Security Onion │ 3. OpenSearch Sec │ 4. Datadog SIEM   │
├───────────────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ License Type                          │ GPLv2 Open Source │ GPLv2 Open Source │ Apache 2.0        │ Proprietary SaaS  │
│ File Integrity Monitoring (FIM)       │ NATIVE EXCELLENT  │ SUPPORTED         │ REQUIRES AGENT    │ SUPPORTED         │
│ Keycloak & OIDC Audit Parsing Rules   │ NATIVE            │ SUPPORTED         │ SUPPORTED         │ NATIVE            │
│ MITRE ATT&CK Framework Mapping        │ NATIVE            │ SUPPORTED         │ NATIVE            │ NATIVE            │
│ Audit Log Tamper Check Verification   │ NATIVE EXCELLENT  │ SUPPORTED         │ SUPPORTED         │ SAAS MANAGED      │
│ Operational Complexity                │ MODERATE          │ HIGH              │ MODERATE          │ LOW               │
│ 36-Month Cost Profile                 │ VERY LOW          │ LOW               │ MODERATE          │ EXTREMELY HIGH    │
└───────────────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 6. Detailed Evaluation Dimensions

### Functional Compatibility & Security Architecture Fit
Wazuh parses Keycloak audit events, Kubernetes API audit logs, and PostgreSQL access logs, evaluating rules for anomalous Curator login attempts, MFA bypass attempts, or unauthorized DDL operations. Its built-in **File Integrity Monitoring (FIM)** monitors critical configuration files (`/etc/keycloak`, `/etc/kong`, `/etc/postgresql`) to detect unauthorized modifications instantly.

### Security & Privacy Safeguards
* Ingests strictly operational security event metadata (user ID, timestamp, event type, source IP hash, success status).
* Zero user personal data (`CAT-2` watch history, real names, billing info) is processed or stored by the SIEM.

---

## 7. Cost Model & 36-Month TCO

* **Software Cost:** $0 (Wazuh GPLv2 Open Source Engine).
* **Infrastructure Cost:** 1-node / 2-node Wazuh Manager pod + indexer storage (~$90/month = ~$3,240 / 36 months).
* **Comparison (Datadog Cloud SIEM):** ~$600/month for security log volume (~$21,600 / 36 months).
* **TCO Summary (36 Months):** ~$3,240 total infrastructure cost (saving ~$18,000+ vs SaaS).

---

## 8. Vendor Lock-In & Portability Analysis

* **Rule Format:** Standard SIGMA rules and JSON log formats.
* **Lock-In Depth:** **LOW** (Standard SIGMA rule format).

---

## 9. Risk Assessment & Mitigations

* **Risk:** Index storage growth under high audit log volume.
  * **Mitigation:** Enforce index lifecycle management (ILM) archiving old audit indexes to cold S3 storage after 90 days.

---

## 10. Recommended Technology Selection

* **Primary Recommendation:** **Wazuh (GPLv2 Open-Source SIEM & XDR Engine)**
* **Alternative Candidate:** **OpenSearch Security Analytics (Apache License 2.0)**
* **Justification:** Wazuh provides enterprise open-source SIEM capabilities, native File Integrity Monitoring (FIM), Keycloak audit rule parsing, MITRE ATT&CK threat mapping, and zero license costs.

---

## 11. Final Governance Status

Evaluation:
COMPLETE

Recommendation:
Wazuh (GPLv2 Open-Source SIEM & XDR Engine)

Governance:
PROPOSED TECHNOLOGY RECOMMENDATION

Approval:
OWNER REVIEW REQUIRED

Technology Approved:
NO

Implementation:
NOT AUTHORIZED
