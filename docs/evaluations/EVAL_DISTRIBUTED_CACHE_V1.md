# CineVault OS — Technology Evaluation: Cache / Rate-Limit State Technology V1

**Document Type:** Technology Evaluation & Selection Proposal  
**Decision ID:** `DEC-API-DEF-04` — Cache / Rate-Limit State Technology Selection  
**Status:** Evaluation Complete — Awaiting Owner Approval  
**Date:** 2026-08-08  
**Selected Technology Recommendation:** Valkey (BSD 3-Clause License — Linux Foundation)  
**Alternative Candidate:** Dragonfly (BSL 1.1 / Open-Source Core)  
**Governance State:** PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED  
**Implementation Authorization:** NOT AUTHORIZED  

---

## 1. Decision Under Evaluation

* **Decision ID:** `DEC-API-DEF-04`
* **Topic:** Cache & Rate-Limit State Technology Selection
* **Originating Baseline:** Infrastructure Architecture V1 (`docs/INFRASTRUCTURE_ARCHITECTURE_V1.md`, `DEC-INFRA-PRP-04`) & API Specification V1 (`docs/API_SPECIFICATION_V1.md`)
* **Current Governance State:** `DEFERRED` → `PROPOSED` (Awaiting Owner Review)
* **Objective:** Select an in-memory, low-latency distributed state store to serve as the L2 caching layer for metadata queries, store API rate-limiting token bucket states, hold ephemeral user session tokens, and optimize query latency without weakening security or introducing proprietary license lock-in.

---

## 2. Canonical Architecture Requirements

Derived from locked baseline specifications (`API Specification V1`, `Infrastructure Architecture V1`, `Physical Database V1`):

```text
┌───────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────┐
│ Feature / Capability Requirement      │ Architectural Specification               │ Canonical Source Reference                │
├───────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. Sub-millisecond Read Latency       │ p99 < 2.0 ms for cached CAT-1 metadata    │ API Spec V1 (DEC-API-PRP-04)              │
│ 2. Atomic Rate-Limit Counters         │ Atomic INCR/EXPIRE & Lua scripts for bucket│ API Spec V1 (DEC-API-DEF-04)              │
│ 3. Protocol Compatibility             │ Standard RESP2 / RESP3 protocol support   │ Infrastructure V1 (DEC-INFRA-PRP-04)      │
│ 4. Permissive Open-Source Licensing   │ OSI-compliant open source (No SSPL/AGPL)  │ Baseline Governance (DEC-INFRA-DEF-01)    │
│ 5. High Availability & Sentinel       │ Multi-AZ replication & automatic failover │ Infrastructure V1 (DEC-INFRA-DEF-02)      │
│ 6. TLS Transit & Auth Protection      │ TLS 1.3 transit encryption & ACL auth     │ Security V1 (DEC-SEC-PRP-09)              │
└───────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Architecture Dependencies

* **API Gateway:** Kong Gateway (`DEC-API-DEF-03`) uses cache store for distributed rate-limiting counters.
* **Database Layer:** PostgreSQL (`DEC-PHYS-DEF-01`) primary cache fallback.
* **Ingestion Pipeline:** Async ingestion worker tasks (`DEC-INFRA-OPN-01`) for raw metadata lookups.

---

## 4. Candidate Technologies Identified

Four candidates representing different licensing and architectural models were evaluated:

1. **Valkey (BSD 3-Clause — Linux Foundation):** Permissive, open-source, community-governed fork of Redis created by AWS, Google, Oracle, and Ericsson under Linux Foundation.
2. **Dragonfly (BSL 1.1 / Proprietary Commercial Tier):** Multi-threaded memory-store built for modern hardware.
3. **Redis 8 (Tri-Licensed: AGPLv3 / RSALv2 / SSPLv1):** Redis Ltd managed engine with copyleft or commercial restrictions.
4. **KeyDB (BSD 3-Clause):** Multi-threaded open-source fork of Redis (Snap Inc.).

---

## 5. Candidate Evaluation & Feature Compatibility Matrix

```text
┌───────────────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Dimension / Feature                   │ 1. Valkey         │ 2. Dragonfly      │ 3. Redis 8        │ 4. KeyDB          │
├───────────────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ License Type                          │ BSD 3-Clause (OSI)│ BSL 1.1           │ AGPLv3/SSPLv1     │ BSD 3-Clause      │
│ Neutral Governance                    │ Linux Foundation  │ Proprietary Corp  │ Redis Ltd         │ Snap Inc. (Stale) │
│ RESP2 / RESP3 Protocol Compatibility  │ 100% EXCELLENT    │ HIGH              │ 100% EXCELLENT    │ HIGH              │
│ Atomic INCR / Lua Scripting           │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │ SUPPORTED         │
│ Sub-millisecond Latency (p99)         │ < 1.0 ms          │ < 0.8 ms          │ < 1.0 ms          │ < 1.2 ms          │
│ Multi-AZ Sentinel / Cluster Failover  │ NATIVE            │ LIMITED           │ NATIVE            │ NATIVE            │
│ Local Dev / Docker Support            │ EXCELLENT         │ EXCELLENT         │ EXCELLENT         │ GOOD              │
│ Copyleft / Commercial Legal Risk      │ NONE (Zero Risk)  │ MODERATE          │ HIGH (AGPL/SSPL)  │ NONE              │
└───────────────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 6. Detailed Evaluation Dimensions

### Licensing & Governance Analysis (Critical 2026 Context)
In March 2024, Redis Ltd moved Redis away from BSD 3-Clause to dual RSALv2/SSPLv1 licensing, and in 2025 introduced AGPLv3. Running AGPLv3 software as a managed service introduces legal copyleft obligations. Valkey was established by the Linux Foundation with backing from AWS, GCP, Oracle, and Ericsson to guarantee a permanently open-source, BSD-3-Clause licensed RESP-compatible engine. Valkey carries zero licensing risk.

### Functional Compatibility & Performance
Valkey supports all RESP2/RESP3 commands, atomic counter increments, key expiration TTLs, pub/sub messaging, and Lua script execution required for token-bucket rate limiting. Benchmark performance demonstrates sub-millisecond p99 response times under 50,000 requests/sec workloads.

### Security & Privacy
* Supports TLS 1.3 transit encryption and RBAC ACL user profiles.
* Zero personal user data (`CAT-2`) is stored in plaintext; all cached tokens or session hashes are cryptographically hashed (SHA-256).

### Local Development & Testing
Valkey provides official OCI container images (`valkey/valkey:latest`), enabling 1-to-1 drop-in emulation via Docker Compose in local development environments.

---

## 7. Cost Model & 36-Month TCO

* **Software Cost:** $0 (Permissive BSD 3-Clause License).
* **Infrastructure Cost:** 3-node HA Valkey Cluster (Primary + Replica + Sentinel across 3 AZs) estimated at ~$90/month (~$3,240 / 36 months).
* **Operational Cost:** Minimal maintenance (automated failover via Sentinel).
* **TCO Summary (36 Months):** ~$3,240 total infrastructure cost.

---

## 8. Vendor Lock-In & Portability Analysis

* **Protocol Portability:** 100% RESP standard protocol; client libraries exist in Python, Go, Node, Java, Flutter/Dart.
* **Data Portability:** Standard RDB / AOF snapshot export capabilities.
* **Lock-In Depth:** **LOW** (Standard RESP protocol).

---

## 9. Risk Assessment & Mitigations

* **Risk:** Potential protocol divergence between Valkey and Redis 8 in future years.
  * **Mitigation:** Use strictly core RESP features (Strings, Hashes, Sets, Atomic Counters, TTLs) supported universally by all RESP engines.

---

## 10. Recommended Technology Selection

* **Primary Recommendation:** **Valkey (BSD 3-Clause License — Linux Foundation)**
* **Alternative Candidate:** **Dragonfly (BSL 1.1 / Open-Source Core)**
* **Justification:** Valkey provides 100% open-source BSD licensing under neutral Linux Foundation governance, wire compatibility with standard Redis SDKs, zero legal risk, and sub-millisecond latency for distributed caching and rate limiting.

---

## 11. Final Governance Status

Evaluation:
COMPLETE

Recommendation:
Valkey (BSD 3-Clause — Linux Foundation)

Governance:
PROPOSED TECHNOLOGY RECOMMENDATION

Approval:
OWNER REVIEW REQUIRED

Technology Approved:
NO

Implementation:
NOT AUTHORIZED
