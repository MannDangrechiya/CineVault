# CineVault OS — Technology Evaluation: Object Storage Target V1

**Document Type:** Technology Evaluation & Selection Proposal  
**Decision ID:** `DEC-ING-PRP-05` — Object Storage Target Capability Selection  
**Status:** Evaluation Complete — Awaiting Owner Approval  
**Date:** 2026-08-08  
**Selected Technology Recommendation:** S3-Compatible Storage Capability (Cloudflare R2 / AWS S3 API Standard)  
**Alternative Candidate:** Garage Object Storage (Open Source Rust S3 Engine) / Ceph RADOS Gateway  
**Governance State:** PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED  
**Implementation Authorization:** NOT AUTHORIZED  

---

## 1. Decision Under Evaluation

* **Decision ID:** `DEC-ING-PRP-05`
* **Topic:** Object Storage Target Capability Selection
* **Originating Baseline:** Ingestion Architecture V1 (`docs/INGESTION_ARCHITECTURE_V1.md`, `DEC-ING-PRP-05`) & Data Source Registry V1 (`docs/DATA_SOURCE_REGISTRY_V1.md`)
* **Current Governance State:** `DEFERRED` → `PROPOSED` (Awaiting Owner Review)
* **Objective:** Select an object storage target capability to store raw provider payloads (`CAT-5`), proxied artwork image assets (`CAT-1`), poster thumbnails, and ingestion audit artifacts while enforcing strict S3-API abstraction, server-side encryption (`AES-256`), access control policies, and zero egress cost penalties.

---

## 2. Canonical Architecture Requirements

Derived from locked baseline specifications (`Ingestion Architecture V1`, `Security Architecture V1`, `Infrastructure Architecture V1`):

```text
┌───────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────┐
│ Feature / Capability Requirement      │ Architectural Specification               │ Canonical Source Reference                │
├───────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. Standard S3 API Compatibility     │ AWS S3 V4 signing signature protocol      │ Ingestion V1 (DEC-ING-PRP-05)             │
│ 2. Payload & Artwork Bucket Isolation │ Separate buckets for `raw-payloads`, `artwork`│ Ingestion V1 (DEC-ING-PRP-05)            │
│ 3. Server-Side Encryption (SSE-S3)    │ AES-256 encryption at rest                │ Security V1 (DEC-SEC-PRP-09)              │
│ 4. Egress Cost Minimization           │ Zero or low egress bandwidth fees for media│ Infrastructure V1 (DEC-INFRA-DEF-01)      │
│ 5. Lifecycle Retention Policies       │ Automatic expiration of raw CAT-5 payloads│ Ingestion V1 (DEC-ING-OPN-02)             │
│ 6. Local Development Emulator Support │ Local S3 emulator (Garage / MinIO / LocalStack)│ Infrastructure V1 (DEC-INFRA-PRP-01)   │
└───────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Architecture Dependencies

* **Ingestion Worker Pipeline:** Uploads raw provider payloads and fetches artwork (`DEC-ING-PRP-01`).
* **API Gateway / Edge CDN:** Serves cached poster thumbnails to client apps (`DEC-API-DEF-03`).
* **Backup Strategy:** WAL backup storage target (`DEC-PHYS-DEF-04`).

---

## 4. Candidate Technologies Identified

Four candidates representing different operational models (Managed SaaS, Self-Hosted Open Source, Multi-Cloud) were evaluated:

1. **Cloudflare R2 (Managed SaaS):** S3-compatible object storage with **$0 egress fees**, native Cloudflare CDN integration, and zero bucket maintenance.
2. **Garage Object Storage (AGPLv3 / Rust):** Actively maintained, lightweight open-source self-hosted distributed object store designed for multi-site deployment.
3. **AWS S3 / GCP Cloud Storage (Cloud Native):** Industry-standard managed cloud storage with extensive lifecycle rules and cross-region replication.
4. **Ceph RADOS Gateway (LGPL 2.1):** Enterprise-grade, self-hosted distributed storage cluster.

---

## 5. Candidate Evaluation & Feature Compatibility Matrix

```text
┌───────────────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Dimension / Feature                   │ 1. Cloudflare R2  │ 2. Garage (Rust)  │ 3. AWS S3         │ 4. Ceph RADOS GW  │
├───────────────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ Deployment Model                      │ Managed SaaS      │ Self-Hosted Open  │ Managed Cloud     │ Self-Hosted Open  │
│ S3 API V4 Compatibility               │ 100% EXCELLENT    │ HIGH              │ NATIVE STANDARD   │ 100% EXCELLENT    │
│ Bandwidth Egress Fees                 │ **$0 / GB (Free)**│ Infrastructure cost│ $0.09 / GB        │ Infrastructure cost│
│ Server-Side Encryption (AES-256)      │ NATIVE            │ SUPPORTED         │ NATIVE            │ SUPPORTED         │
│ Lifecycle Expiration Rules            │ SUPPORTED         │ SUPPORTED         │ NATIVE EXCELLENT  │ SUPPORTED         │
│ Operational Overhead                  │ ZERO              │ MODERATE          │ VERY LOW          │ HIGH              │
│ Local Dev Emulator Compatibility      │ Standard S3 SDK   │ EXCELLENT         │ AWS LocalStack    │ GOOD              │
└───────────────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 6. Detailed Evaluation Dimensions

### Functional & Egress Cost Analysis
Artwork and poster image delivery generate significant bandwidth egress. Cloudflare R2 provides complete S3 API compatibility with **$0 egress bandwidth fees**, saving thousands of dollars monthly compared to standard cloud providers (AWS S3 charges ~$0.09/GB egress). For self-hosted hybrid or local dev environments, **Garage** or standard S3 emulators provide 100% API portability.

### Security & Privacy
* Server-side encryption (`SSE-S3` AES-256) enabled by default for all object uploads.
* Raw provider payloads (`raw-payloads/`) are stored in private, un-proxied buckets accessible strictly via IAM API credentials.
* Zero user personal data (`CAT-2`) is stored in object storage; object storage is restricted to artwork (`CAT-1`) and provider raw responses (`CAT-5`).

---

## 7. Cost Model & 36-Month TCO

* **Cloudflare R2 Tier:** Storage at $0.015/GB/month; $0 egress fees.
* **Estimated Storage:** 2 TB media assets + raw payloads (~$30/month = ~$1,080 / 36 months).
* **Comparison (AWS S3):** 2 TB storage + 10 TB egress/month = ~$940/month (~$33,840 / 36 months).
* **TCO Summary (36 Months - R2):** ~$1,080 total storage cost (vs $33,840 on standard egress cloud).

---

## 8. Vendor Lock-In & Portability Analysis

* **API Portability:** 100% S3 API protocol standard (`boto3`, `@aws-sdk/client-s3`). Code relies strictly on standard S3 endpoints (`endpoint_url`).
* **Lock-In Depth:** **LOW** (Standard S3 API protocol).

---

## 9. Risk Assessment & Mitigations

* **Risk:** Cloudflare API availability or rate limits on write operations.
  * **Mitigation:** S3 API abstraction layer allows swapping `endpoint_url` to AWS S3, GCP Cloud Storage, or self-hosted Garage/Ceph instantly via environment variables without code modification.

---

## 10. Recommended Technology Selection

* **Primary Recommendation:** **S3-Compatible Capability using Cloudflare R2** (for Production zero-egress cost)
* **Alternative Candidate:** **Garage Object Storage / Ceph RADOS Gateway** (for Self-Hosted / Hybrid)
* **Justification:** Strict adherence to the standard S3 API protocol guarantees zero code lock-in, while Cloudflare R2 eliminates egress bandwidth penalties, saving over $30,000 across 36 months.

---

## 11. Final Governance Status

Evaluation:
COMPLETE

Recommendation:
S3-Compatible Object Storage Capability (Cloudflare R2 Primary / S3 API Standard)

Governance:
PROPOSED TECHNOLOGY RECOMMENDATION

Approval:
OWNER REVIEW REQUIRED

Technology Approved:
NO

Implementation:
NOT AUTHORIZED
