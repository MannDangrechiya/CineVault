# CineVault OS — Technology Evaluation: Backup / DR Storage Target V1

**Document Type:** Technology Evaluation & Selection Proposal  
**Decision ID:** `DEC-PHYS-DEF-04` — Backup Cloud Storage Target & Tooling Selection  
**Status:** Evaluation Complete — Awaiting Owner Approval  
**Date:** 2026-08-08  
**Selected Technology Recommendation:** pgBackRest (PostgreSQL Open-Source License) + Multi-Region S3 Target  
**Alternative Candidate:** WAL-G (Apache License 2.0)  
**Governance State:** PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED  
**Implementation Authorization:** NOT AUTHORIZED  

---

## 1. Decision Under Evaluation

* **Decision ID:** `DEC-PHYS-DEF-04`
* **Topic:** Backup / Disaster Recovery Storage Target & Tooling Selection
* **Originating Baseline:** Physical Database Design V1 (`docs/PHYSICAL_DATABASE_DESIGN_V1.md`, `DEC-PHYS-PRP-04`) & Infrastructure Architecture V1 (`docs/INFRASTRUCTURE_ARCHITECTURE_V1.md`)
* **Current Governance State:** `DEFERRED` → `PROPOSED` (Awaiting Owner Review)
* **Objective:** Select a dedicated backup management engine and resilient storage target capability to perform continuous WAL archive streaming, automated daily full/incremental database backups, encrypted multi-region storage, and automated Point-In-Time Recovery (PITR) to fulfill RPO < 5 min and RTO < 1 hour requirements.

---

## 2. Canonical Architecture Requirements

Derived from locked baseline specifications (`Physical Database Design V1`, `Infrastructure Architecture V1`, `Security Architecture V1`):

```text
┌───────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────┐
│ Feature / Capability Requirement      │ Architectural Specification               │ Canonical Source Reference                │
├───────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. Point-In-Time Recovery (PITR)     │ Granular transaction recovery (RPO < 5m)  │ Physical DB V1 (DEC-PHYS-PRP-04)         │
│ 2. Continuous WAL Archive Streaming   │ Real-time WAL file archiving to object store│ Physical DB V1 (DEC-PHYS-PRP-04)        │
│ 3. Parallel Compression & Encryption  │ AES-256 client-side encryption before push│ Security V1 (DEC-SEC-PRP-09)              │
│ 4. Multi-Region DR Bucket Target      │ Cross-region immutable object storage target│ Physical DB V1 (DEC-PHYS-PRP-04)        │
│ 5. Automated Backup Verification      │ Automated restoration verification script │ Physical DB V1 (DEC-PHYS-PRP-04)         │
└───────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Architecture Dependencies

* **Database Engine:** PostgreSQL 16+ (`DEC-PHYS-DEF-01`).
* **Object Storage Target:** S3 API compatible storage (`DEC-ING-PRP-05`).
* **Cloud Compute:** Multi-AZ container instances (`DEC-INFRA-DEF-01`).

---

## 4. Candidate Technologies Identified

Four backup engines and target architectures were evaluated:

1. **pgBackRest + Multi-Region S3 (PostgreSQL License):** Enterprise-grade, parallelized backup and WAL restore utility designed specifically for PostgreSQL.
2. **WAL-G + S3 (Apache 2.0):** High-speed Go-based backup tool for PostgreSQL.
3. **Barman (GPLv3 — EnterpriseDB):** Backup and recovery manager for PostgreSQL.
4. **Cloud Managed Automated Snapshots (RDS / Cloud SQL):** Vendor-specific cloud snapshot service.

---

## 5. Candidate Evaluation & Feature Compatibility Matrix

```text
┌───────────────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Dimension / Feature                   │ 1. pgBackRest     │ 2. WAL-G          │ 3. Barman         │ 4. Managed Cloud  │
├───────────────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ License Type                          │ PostgreSQL (OSI)  │ Apache 2.0        │ GPLv3             │ Proprietary Cloud │
│ Continuous WAL Streaming              │ NATIVE EXCELLENT  │ NATIVE EXCELLENT  │ SUPPORTED         │ PROPRIETARY       │
│ Parallel Compression / Encryption     │ NATIVE (lz4/zst)  │ NATIVE (lz4/zst)  │ MODERATE          │ CLOUD-MANAGED     │
│ Direct S3 / Multi-Region Target       │ NATIVE            │ NATIVE            │ REQUIRES PLUGIN   │ REGION BOUND      │
│ Point-In-Time Recovery (PITR) RPO     │ < 1 minute        │ < 1 minute        │ < 5 minutes       │ Cloud Dependent   │
│ Delta / Differential Backups          │ NATIVE            │ NATIVE            │ SUPPORTED         │ Snapshot Based    │
│ Vendor Lock-In Risk                   │ NONE (Zero Risk)  │ NONE (Zero Risk)  │ LOW               │ HIGH              │
└───────────────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 6. Detailed Evaluation Dimensions

### Functional Compatibility & Disaster Recovery
pgBackRest provides asynchronous WAL archiving, parallel block-level delta backups, page checksum validation, and native S3 object store integration. In a disaster recovery event, pgBackRest can perform a full database restore from multi-region S3 object storage to any point in time up to the exact second before data corruption occurred.

### Security & Compliance
* All WAL segments and database data blocks are encrypted at rest using AES-256 keys managed via KMS / Secrets Manager before transmission (`client-side encryption`).
* Object storage buckets are configured with **S3 Object Lock (WORM compliance)** to prevent malicious or accidental backup deletion/ransomware modification.

---

## 7. Cost Model & 36-Month TCO

* **Software Cost:** $0 (Open Source PostgreSQL License).
* **Storage Cost:** ~1 TB WAL & Differential Backup retention in primary + secondary DR S3 bucket (~$45/month = ~$1,620 / 36 months).
* **TCO Summary (36 Months):** ~$1,620 total backup storage cost.

---

## 8. Vendor Lock-In & Portability Analysis

* **Data Portability:** Backup archives use standard PostgreSQL data directory formats. Can be restored onto any PostgreSQL 16+ server running on any cloud or local hardware.
* **Lock-In Depth:** **LOW** (Open-source backup tool & standard PostgreSQL files).

---

## 9. Risk Assessment & Mitigations

* **Risk:** WAL archiving bottleneck under extreme write spikes.
  * **Mitigation:** Configure pgBackRest asynchronous archiving processes (`process-max = 4`) and local staging spool directory.

---

## 10. Recommended Technology Selection

* **Primary Recommendation:** **pgBackRest (PostgreSQL License) + Multi-Region S3 Storage Target**
* **Alternative Candidate:** **WAL-G (Apache License 2.0)**
* **Justification:** pgBackRest is the undisputed gold standard for PostgreSQL backup, offering parallel compression/encryption, WORM-compliant multi-region S3 storage targets, and deterministic PITR recovery.

---

## 11. Final Governance Status

Evaluation:
COMPLETE

Recommendation:
pgBackRest (PostgreSQL License) + Multi-Region S3 Target

Governance:
PROPOSED TECHNOLOGY RECOMMENDATION

Approval:
OWNER REVIEW REQUIRED

Technology Approved:
NO

Implementation:
NOT AUTHORIZED
