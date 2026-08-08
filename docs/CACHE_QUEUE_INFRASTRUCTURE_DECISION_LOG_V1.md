# CineVault OS — Cache & Queue Infrastructure Decision Log V1

**Document Type:** Infrastructure Implementation Strategy & Governance Decision Log  
**Status:** Implementation Proposal Baseline (Awaiting Project Owner Approval)  
**Date:** 2026-08-08  
**Scope:** Governance transitions, technology candidate proposals, and historical decision mapping for Phase 4 Cache & Queue Infrastructure.

---

## 1. Governance Overview

This Decision Log formally records the technology implementations introduced in **Phase 4 — Cache & Queue Infrastructure** and reconciles them with the CineVault OS Governance Baseline (`Architecture Baseline V1`, `Infrastructure Architecture V1`, `API Specification V1`, `Physical Database Design V1`, `Security Architecture V1`, and `Observability Architecture V1`).

During Phase 4 execution, four concrete technology choices were implemented to establish the distributed caching, rate limiting, connection pooling, and message broker stack:
1. **Valkey** (BSD 3-Clause — Linux Foundation) for distributed caching and rate limiting state.
2. **RabbitMQ** (MPL 2.0) with AMQP 0-9-1, Quorum Queues (`x-queue-type: quorum`), Dead-Letter Exchanges (`cinevault.dlx`), and retry queues.
3. **Kong Gateway** (DB-less 3.6) for edge proxying and distributed rate limiting enforcement (`policy: redis`).
4. **PgBouncer** (Transaction mode) for PostgreSQL connection pooling and readiness probing.

> [!IMPORTANT]
> **PROPOSAL CLASSIFICATION & OWNER APPROVAL REQUIREMENT**  
> All implementation selections in Phase 4 are classified as **IMPLEMENTATION PROPOSALS (`PROPOSED / OWNER APPROVAL PENDING`)**.  
> The underlying historical architectural decisions (`DEC-API-DEF-03`, `DEC-API-DEF-04`, `DEC-PHYS-DEF-03`, `DEC-INFRA-OPN-01`) are NOT auto-approved by implementation. They remain historically linked as implementation candidates awaiting formal Project Owner Sign-Off.

---

## 2. Historical Lifecycle Transition Mapping

```text
Historical Decision (DEFERRED / OPEN)
       │
       ▼
Implementation Candidate Selected & Implemented (Phase 4 Code Artifacts)
       │
       ▼
Phase 4 Implementation Decision Recorded (DEC-CQI-PRP-01..04)
       │
       ▼
OWNER APPROVAL PENDING (Awaiting Project Owner Governance Pass)
```

---

## 3. Decision Log Matrix

| Decision ID | Implementation Title | Historical Governance Link | Historical Transition | Current Status | Owner Approval Requirement |
|---|---|---|---|---|---|
| `DEC-CQI-PRP-01` | **Valkey Distributed Cache & Rate-Limit Store** | `DEC-API-DEF-04` (Physical Cache Storage Technology) | Previously `DEFERRED` ──▶ Implementation Candidate Selected (Valkey 8.0) | `PROPOSED (IMPLEMENTATION CANDIDATE)` | Project Owner sign-off required to finalize Valkey as permanent L2 cache baseline. |
| `DEC-CQI-PRP-02` | **RabbitMQ Queue Broker & Quorum Queue Topology** | `DEC-INFRA-OPN-01` (Queue Broker Technology Standard) | Previously `OPEN` ──▶ Implementation Candidate Selected (RabbitMQ 4.0 AMQP 0-9-1) | `PROPOSED (IMPLEMENTATION CANDIDATE)` | Project Owner sign-off required to finalize RabbitMQ as permanent AMQP broker baseline. |
| `DEC-CQI-PRP-03` | **Kong Gateway API & Rate-Limiting Implementation** | `DEC-API-DEF-03` (API Gateway Technology Selection) | Previously `DEFERRED` ──▶ Implementation Candidate Selected (Kong 3.6 DB-less) | `PROPOSED (IMPLEMENTATION CANDIDATE)` | Project Owner sign-off required to finalize Kong Gateway as permanent edge proxy baseline. |
| `DEC-CQI-PRP-04` | **PgBouncer Connection Pooling Implementation** | `DEC-PHYS-DEF-03` (PostgreSQL Connection Pool Topology) | Previously `DEFERRED` ──▶ Implementation Candidate Selected (PgBouncer Transaction Pooler) | `PROPOSED (IMPLEMENTATION CANDIDATE)` | Project Owner sign-off required to finalize PgBouncer as permanent connection pooler baseline. |

---

## 4. Detailed Decision Rationale & Boundaries

### 4.1 DEC-CQI-PRP-01: Valkey Distributed Cache & Rate-Limit State Store
* **Historical Decision Reference:** `DEC-API-DEF-04` (Physical Cache Storage Technology — Previously `DEFERRED`).
* **Implementation Technology:** Valkey 8.0-alpine (Linux Foundation — BSD 3-Clause License).
* **Rationale:** Valkey provides 100% RESP2/RESP3 wire protocol compatibility with Redis, sub-millisecond atomic counter increments (`INCR`, `EXPIRE`), atomic `SETNX` idempotency checking, zero SSPL/AGPL legal licensing risk, and full compatibility with Kong rate-limiting plugin (`policy: redis`).
* **Failure Boundary:** Cache GET errors or timeouts fail open for non-critical L2 metadata reads (falling back to database read replicas), but rate-limiting failure must maintain safety limits to prevent abuse.
* **Governance Status:** `PROPOSED (OWNER APPROVAL PENDING)`.

---

### 4.2 DEC-CQI-PRP-02: RabbitMQ Queue Broker & Quorum Queue Implementation
* **Historical Decision Reference:** `DEC-INFRA-OPN-01` (Queue Broker Technology Standard — Previously `OPEN`).
* **Implementation Technology:** RabbitMQ 4.0-management-alpine (MPL 2.0 License).
* **Rationale:** Native support for standard AMQP 0-9-1 protocol, Raft-based Quorum Queues (`x-queue-type: quorum`) for data persistence across restarts, native Dead-Letter Exchanges (`cinevault.dlx`), and per-queue/per-message TTL retry routing without custom code overhead.
* **Topology:** Queues: `queue.ingestion`, `queue.quality`, `queue.reconciliation`, `queue.sync`, `queue.media`, `queue.dead_letter`, `queue.ingestion.retry`.
* **Governance Status:** `PROPOSED (OWNER APPROVAL PENDING)`.

---

### 4.3 DEC-CQI-PRP-03: Kong API Gateway Implementation
* **Historical Decision Reference:** `DEC-API-DEF-03` (API Gateway Technology Selection — Previously `DEFERRED`).
* **Implementation Technology:** Kong Gateway 3.6-alpine (DB-less mode).
* **Rationale:** Declarative configuration management (`config/kong/kong.yml`), zero database runtime dependency for gateway routing, native `rate-limiting` plugin with `policy: redis` integration for Valkey, CORS validation, and correlation header injection (`X-Correlation-ID`).
* **Contract Invariance:** Preserves exact 3-tier API boundaries (`/v1/*`, `/internal/v1/*`, `/health`). Zero contract mutation.
* **Governance Status:** `PROPOSED (OWNER APPROVAL PENDING)`.

---

### 4.4 DEC-CQI-PRP-04: PgBouncer Connection Pooling Implementation
* **Historical Decision Reference:** `DEC-PHYS-DEF-03` (PostgreSQL Connection Pool Topology — Previously `DEFERRED`).
* **Implementation Technology:** PgBouncer (Latest Alpine container).
* **Rationale:** Lightweight transaction-mode pooling (`POOL_MODE: transaction`) insulating PostgreSQL from client thread scaling (supporting up to 1000 client connections over 20 server connections).
* **Health Integration:** Operational readiness probe checks PgBouncer TCP port (`6432`) as part of `/health/readiness`.
* **Governance Status:** `PROPOSED (OWNER APPROVAL PENDING)`.

---

## 5. Governance Summary Dashboard

```text
===============================================================================
CINEVAULT OS — PHASE 4 CACHE & QUEUE INFRASTRUCTURE DECISION DASHBOARD
===============================================================================

DEC-CQI-PRP-01   🟡 IMPLEMENTATION PROPOSAL (Valkey 8.0 RESP Cache)
DEC-CQI-PRP-02   🟡 IMPLEMENTATION PROPOSAL (RabbitMQ 4.0 AMQP / Quorum Queues)
DEC-CQI-PRP-03   🟡 IMPLEMENTATION PROPOSAL (Kong 3.6 Gateway / Redis Policy)
DEC-CQI-PRP-04   🟡 IMPLEMENTATION PROPOSAL (PgBouncer Transaction Pooler)

HISTORICAL REFERENCES PRESERVED:
DEC-API-DEF-04   🟡 Previously DEFERRED  ──▶ Linked to DEC-CQI-PRP-01
DEC-INFRA-OPN-01 🟡 Previously OPEN      ──▶ Linked to DEC-CQI-PRP-02
DEC-API-DEF-03   🟡 Previously DEFERRED  ──▶ Linked to DEC-CQI-PRP-03
DEC-PHYS-DEF-03  🟡 Previously DEFERRED  ──▶ Linked to DEC-CQI-PRP-04

===============================================================================
FINAL PHASE 4 GOVERNANCE STATUS:
IMPLEMENTATION VALIDATED
GOVERNANCE TRANSITION RECORDED
OWNER APPROVAL PENDING
===============================================================================
```
