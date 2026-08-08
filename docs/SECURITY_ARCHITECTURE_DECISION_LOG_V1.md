# CineVault OS — Security Architecture Decision Log V1

**Document Type:** Security Architecture Strategy Decision Log  
**Status:** Approved & Baseline Locked  
**Owner Approval Date:** 2026-08-08  
**Scope:** Architectural Decisions Inherited, Approved, or Deferred in `docs/SECURITY_ARCHITECTURE_V1.md`  

---

## 1. Governance Overview

This Decision Log categorizes all architectural decisions associated with the CineVault OS Security Architecture V1.

Following formal Project Owner review on **2026-08-08**, all eleven proposed security architecture decisions (`DEC-SEC-PRP-01` through `DEC-SEC-PRP-11`) have received **Explicit Project Owner Approval** via the Control Room workflow and are now officially **BASELINE LOCKED**.

### Historical Lifecycle Transition
Decisions preserve full historical traceability:
```text
PROPOSED ──▶ OWNER REVIEW ──▶ OWNER APPROVED / BASELINE LOCKED (2026-08-08)
```

> [!IMPORTANT]
> **CONCEPTUAL BASELINE LOCK VS. TECHNOLOGY SELECTION**  
> Project Owner approval locks the **conceptual security architecture**. It does NOT resolve deferred technology selections (OAuth servers, WAF vendors, cloud KMS, SIEM platforms) nor does it authorize code implementation or cloud infrastructure provisioning.

---

## 2. Decision Log Matrix

### A. APPROVED INHERITED DOMAIN CONSTRAINTS

| Decision ID | Inherited Constraint | Baseline Source | Governance Status | Summary of Inherited Constraint |
|---|---|---|---|---|
| `DEC-SEC-INH-01` | **UUIDv7 Canonical Identity Preservation** | ADR-001 | `INHERITED` | Security architecture preserves UUIDv7 canonical keys. Provider IDs are mappings only. |
| `DEC-SEC-INH-02` | **Content Hierarchy Resource Model** | ADR-002 | `INHERITED` | Authorization perimeters observe `Title -> Edition -> Release` and `Title -> Season -> Episode` structure. |
| `DEC-SEC-INH-03` | **Personal Data Isolation & Non-Destruction** | ADR-003, ADR-004 | `INHERITED` | `CAT-2` User Personal Data isolated in `personal` schema; watch events append-only; zero user log deletion on merge. |
| `DEC-SEC-INH-04` | **AI Proposal Boundary Non-Canonical Constraint** | ADR-004 | `INHERITED` | AI infrastructure operates strictly in `quality.ai_proposal_staging` (`CAT-6`); direct canonical write access prohibited. |
| `DEC-SEC-INH-05` | **Pre-Acquisition Licensing Gate Enforcement** | DEC-ING-PRP-01 | `INHERITED` | Ingestion pipeline enforces licensing check before executing provider requests. Web scraping strictly prohibited. |
| `DEC-SEC-INH-06` | **Domain Authority Provenance Lineage** | DS-01, DEC-SRC-PRP-01/02 | `INHERITED` | Audit and lineage logs preserve credits for approved domain authorities (KOBIS Primary Korean, TheTVDB Secondary TV). |
| `DEC-SEC-INH-07` | **Metadata vs Media Rights Segregation** | DEC-ING-PRP-05 | `INHERITED` | Object storage media proxy caches HTTPS URLs; binary media blobs excluded from database; storage does not grant licensing. |
| `DEC-SEC-INH-08` | **Three-Tier API Boundary Isolation** | DEC-API-PRP-02 | `INHERITED` | Runtime network isolates Public Client API (`/v1/`), Internal Admin API (`/internal/v1/`), and Provider Integration Boundary. |
| `DEC-SEC-INH-09` | **PostgreSQL Physical Schema Security** | DEC-PHYS-PRP-01, DEC-PHYS-PRP-08 | `INHERITED` | PostgreSQL RBAC roles (`cinevault_app`, `cinevault_ingest`, `cinevault_admin`, `cinevault_analytics`) enforce schema access. |
| `DEC-SEC-INH-10` | **5-Zone Network Security Perimeter** | DEC-INFRA-PRP-06 | `INHERITED` | Network perimeters segmented into Edge/CDN/WAF Layer, DMZ Zone, Application Subnet, Worker Subnet, and Data Subnet. |
| `DEC-SEC-INH-11` | **Encryption in Transit & at Rest Requirement** | Base Security | `INHERITED` | Telemetry transport and storage must be encrypted. Proposed standards: `DEC-SEC-PRP-09`. |
| `DEC-SEC-INH-12` | **Privileged Session Protection Constraint** | Base Security | `INHERITED` | Audit runbooks observe privileged session protection and re-authentication rules (`DEC-SEC-PRP-10`). |

---

### B. OWNER-APPROVED & LOCKED SECURITY PROPOSALS

| Decision ID | Decision Title | Owner Approval Date | Governance Status | Scope of Approved Baseline |
|---|---|---|---|---|
| `DEC-SEC-PRP-01` | **Zero-Trust Service-to-Service Authorization** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Enforce mTLS or short-lived encrypted service tokens for M2M worker communication. |
| `DEC-SEC-PRP-02` | **Privileged Access / Control Room MFA Architecture** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Mandatory Multi-Factor Authentication (MFA) for `/internal/v1/*` curator endpoints. |
| `DEC-SEC-PRP-03` | **Defense-in-Depth API Security Controls** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Gateway rate-limiting, CORS perimeters, header sanitization, and RFC 7807 problem details safety. |
| `DEC-SEC-PRP-04` | **Personal Data Protection Security Model** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Append-only watch event rules and `personal_data_conflict` records during canonical entity merges. |
| `DEC-SEC-PRP-05` | **Canonical Integrity Protection Model** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Restrict `canonical` schema write permissions to unambiguous automated promotion and MFA curation. |
| `DEC-SEC-PRP-06` | **Provider Credential Isolation Model** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Store provider API keys exclusively in server-side Secrets Manager; zero client exposure. |
| `DEC-SEC-PRP-07` | **AI Proposal Security Boundary** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Confine AI strictly to `quality.ai_proposal_staging` (`CAT-6`) with mandatory human MFA curation. |
| `DEC-SEC-PRP-08` | **Security Audit & Evidence Architecture** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Log administrative actions to `audit.canonical_audit_log` and decision lineage to `audit.attribute_evidence_lineage`. |
| `DEC-SEC-PRP-09` | **Cryptographic Transport & At-Rest Protection Standards** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Propose TLS 1.3 standard for transit and AES-256 for storage volumes. Cloud KMS choice deferred. |
| `DEC-SEC-PRP-10` | **Privileged Session Timeout Policy** | 2026-08-08 | `OWNER APPROVED / LOCKED` | 15-minute curator session timeout with mandatory re-authentication for entity merges/splits. |
| `DEC-SEC-PRP-11` | **Security Audit Integrity Protection Model** | 2026-08-08 | `OWNER APPROVED / LOCKED` | Audit records must resist unauthorized modification. SIEM vendor remains DEFERRED. |

---

### C. DEFERRED DECISIONS (Carried Forward & Postponed)

| Decision ID | Deferred Topic | Reason for Deferral | Target Phase |
|---|---|---|---|
| `DEC-API-DEF-02` | **Authentication Provider & OAuth Server Selection** | Technology choice (Auth0 vs Keycloak vs Firebase vs Cognito) deferred. | Security Implementation Phase |
| `DEC-API-DEF-03` | **API Gateway Technology Selection** | Gateway proxy selection (Kong vs Envoy vs NGINX) deferred. | Edge Infrastructure Phase |
| `DEC-API-DEF-04` | **Physical Cache Storage & Key Schemas** | Cache software selection (Redis vs Memcached) deferred. | Physical Cache Implementation Phase |
| `DEC-PHYS-DEF-04` | **Backup / DR Cloud Storage Infrastructure Target** | Backup cloud target selection deferred. | Operations Phase |
| `DEC-INFRA-DEF-01` | **Cloud Infrastructure Provider & WAF Selection** | Cloud provider (AWS vs GCP vs Azure vs Cloudflare) deferred. | Cloud Procurement Phase |
| `DEC-INFRA-DEF-02` | **Kubernetes Manifests & Terraform Scripting** | Infrastructure-as-code scripting prohibited in architecture phase. | Infrastructure Implementation Phase |
| `DEC-INFRA-DEF-03` | **CI/CD Pipeline Automation Scripting** | Pipeline YAML file creation (GitHub Actions / GitLab CI) deferred. | DevOps Implementation Phase |

---

### D. OPEN QUESTIONS & BLOCKED DECISIONS

| Decision ID | Topic | Description & Barrier | Action Required |
|---|---|---|---|
| `DEC-SEC-OPN-01` | **Control Room MFA Protocol Standard** | Evaluation between TOTP (Authenticator Apps) vs WebAuthn / FIDO2 hardware keys for curator accounts. | Curator workflow review in security implementation phase. |
| `DEC-SEC-OPN-02` | **SIEM / Security Analytics Integration Platform** | Technology selection for centralized security log aggregation and threat detection. | Security tooling review in operations planning phase. |
| `DEC-INFRA-OPN-01` | **Queue Broker Technology Standard** | Evaluation between RabbitMQ (AMQP) vs Redis Streams vs NATS for asynchronous queue broker workload. | Queue workload benchmarking in implementation phase. |
| `DEC-INFRA-OPN-02` | **Multi-Region Read Replica Scale Topology** | Evaluation of multi-region read replica deployment for global client latency optimization. | Global latency testing in mobile performance review phase. |
| `DEC-ING-OPN-02` | **Raw CAT-5 Payload Retention Policy** | Retention window for raw `CAT-5` payloads (indefinite storage vs 365-day cold archive). | Operational policy definition in storage planning phase. |
| `DEC-QUAL-OPN-02` | **Quarantine Retention Window** | Retention duration for quarantined invalid/ambiguous payloads before automated cleanup. | Operational policy definition in storage planning phase. |
| `DEC-PHYS-OPN-01` | **Raw Payload Partition Granularity** | Monthly vs weekly range partition granularity for `ingestion.raw_payload_capture`. | Ingest volume benchmarking in implementation phase. |

---
