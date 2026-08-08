# CineVault OS — Technology Evaluation: Queue Broker Technology V1

**Document Type:** Technology Evaluation & Selection Proposal  
**Decision ID:** `DEC-INFRA-OPN-01` — Queue Broker Technology Selection  
**Status:** Evaluation Complete — Awaiting Owner Approval  
**Date:** 2026-08-08  
**Selected Technology Recommendation:** RabbitMQ (Mozilla Public License 2.0 — VMware / Broadcom Open Source)  
**Alternative Candidate:** NATS JetStream (Apache License 2.0 — CNCF)  
**Governance State:** PROPOSED TECHNOLOGY RECOMMENDATION — OWNER REVIEW REQUIRED  
**Implementation Authorization:** NOT AUTHORIZED  

---

## 1. Decision Under Evaluation

* **Decision ID:** `DEC-INFRA-OPN-01`
* **Topic:** Queue Broker Technology Selection
* **Originating Baseline:** Infrastructure Architecture V1 (`docs/INFRASTRUCTURE_ARCHITECTURE_V1.md`, `DEC-INFRA-PRP-05`) & Ingestion Architecture V1 (`docs/INGESTION_ARCHITECTURE_V1.md`)
* **Current Governance State:** `OPEN` → `PROPOSED` (Awaiting Owner Review)
* **Objective:** Select an asynchronous message queue broker to manage ingestion pipeline worker tasks (`CAT-5` payload ingestion, artwork proxy processing, metadata normalization, quality reconciliation), support Dead-Letter Queues (DLQ), enforce message durability, and handle retry exponential backoff.

---

## 2. Canonical Architecture Requirements

Derived from locked baseline specifications (`Ingestion Architecture V1`, `Infrastructure Architecture V1`, `Observability Architecture V1`):

```text
┌───────────────────────────────────────┬───────────────────────────────────────────┬───────────────────────────────────────────┐
│ Feature / Capability Requirement      │ Architectural Specification               │ Canonical Source Reference                │
├───────────────────────────────────────┼───────────────────────────────────────────┼───────────────────────────────────────────┤
│ 1. Asynchronous Task Queueing         │ Ingestion worker job dispatching          │ Ingestion V1 (DEC-ING-PRP-01)             │
│ 2. Dead Letter Exchange (DLX) & DLQ   │ Automatic routing of failed jobs to DLQ   │ Ingestion V1 (DEC-ING-PRP-04)             │
│ 3. Explicit Consumer Acknowledgments  │ At-least-once message processing guarantee│ Infrastructure V1 (DEC-INFRA-PRP-05)      │
│ 4. Message Persistence & Durability   │ Persistent queues to disk across restarts │ Infrastructure V1 (DEC-INFRA-PRP-05)      │
│ 5. Priority & Backpressure Management │ Priority queues & queue length limits     │ Ingestion V1 (DEC-ING-PRP-03)             │
│ 6. Observability Metrics & Tracing    │ Prometheus queue depth metrics & OTel     │ Observability V1 (DEC-OBS-PRP-03)         │
└───────────────────────────────────────┴───────────────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Architecture Dependencies

* **Ingestion Pipeline:** Orchestrates incoming provider payloads (`DEC-ING-PRP-01`).
* **Cache Layer:** Valkey (`DEC-API-DEF-04`) for rate-limit lookup during ingestion fetch.
* **Database Layer:** PostgreSQL (`DEC-PHYS-DEF-01`) for persistence of normalized records.

---

## 4. Candidate Technologies Identified

Four candidates representing different messaging paradigms were evaluated:

1. **RabbitMQ (MPL 2.0):** Enterprise AMQP 0-9-1 / AMQP 1.0 broker with native DLX, Quorum Queues, and rich routing.
2. **NATS JetStream (Apache 2.0 — CNCF):** Ultra-lightweight Go-based messaging system with JetStream persistence.
3. **Valkey / Redis Streams (BSD 3-Clause):** Lightweight stream data structure inside Valkey cache.
4. **Apache Kafka (Apache 2.0):** Distributed log streaming platform built for high-throughput event logs.

---

## 5. Candidate Evaluation & Feature Compatibility Matrix

```text
┌───────────────────────────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────┐
│ Dimension / Feature                   │ 1. RabbitMQ       │ 2. NATS JetStream │ 3. Valkey Streams │ 4. Apache Kafka   │
├───────────────────────────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┤
│ Messaging Paradigm                    │ AMQP Broker       │ Cloud Native Msg  │ In-Memory Stream  │ Distributed Log   │
│ License Type                          │ MPL 2.0           │ Apache 2.0        │ BSD 3-Clause      │ Apache 2.0        │
│ Native Dead Letter Queue (DLQ)        │ NATIVE (DLX)      │ NATIVE (KV/Sub)   │ CUSTOM (Manual)   │ CUSTOM (Topic)    │
│ Message Priority Queues               │ NATIVE            │ LIMITED           │ NOT SUPPORTED     │ NOT SUPPORTED     │
│ At-Least-Once Delivery Guarantees     │ EXCELLENT (Quorum)│ EXCELLENT         │ GOOD              │ EXCELLENT         │
│ Memory Footprint                      │ ~120 MB / node    │ ~20 MB / node     │ Shared w/ Cache   │ ~1.5 GB / broker  │
│ Operational Overhead                  │ LOW               │ VERY LOW          │ MINIMAL           │ HIGH (JVM + Zoo)  │
│ Local Dev / Docker Support            │ EXCELLENT         │ EXCELLENT         │ EXCELLENT         │ MODERATE          │
└───────────────────────────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────┘
```

---

## 6. Detailed Evaluation Dimensions

### Functional Compatibility & Architecture Fit
RabbitMQ's AMQP routing keys, exchanges, and Quorum Queues directly match CineVault OS's ingestion pipeline requirements. Ingestion worker failures automatically route unacknowledged or rejected payloads to a Dead Letter Exchange (DLX) where quarantine mechanisms (`DEC-QUAL-OPN-02`) can inspect and re-queue payloads safely. Kafka requires significant cluster overhead and lacks native task-queue features like per-message TTL or priority routing.

### Security & Privacy
* Supports TLS 1.3 transit encryption, SASL PLAIN / EXTERNAL authentication, and RBAC virtual host isolation.
* Zero user personal data (`CAT-2`) is placed on queues; queues carry strictly job metadata and asset references (`CAT-5`).

### Operational Complexity & High Availability
RabbitMQ Quorum Queues (Raft consensus algorithm) provide multi-AZ high availability and data durability against node crashes without complex clustering setup.

---

## 7. Cost Model & 36-Month TCO

* **Software Cost:** $0 (Mozilla Public License 2.0).
* **Infrastructure Cost:** 3-node HA RabbitMQ Quorum cluster estimated at ~$150/month (~$5,400 / 36 months).
* **Operational Cost:** Minimal maintenance (Raft automatic cluster management).
* **TCO Summary (36 Months):** ~$5,400 total infrastructure cost.

---

## 8. Vendor Lock-In & Portability Analysis

* **Protocol Portability:** Standard open AMQP 0-9-1 and AMQP 1.0 protocols. Client libraries exist in all major languages.
* **Lock-In Depth:** **LOW** (Standard AMQP protocol).

---

## 9. Risk Assessment & Mitigations

* **Risk:** Erlang VM memory growth under high queue depth.
  * **Mitigation:** Enforce max queue length policies, Prometheus memory alarm triggers, and automated worker HPA scaling.

---

## 10. Recommended Technology Selection

* **Primary Recommendation:** **RabbitMQ (Mozilla Public License 2.0)**
* **Alternative Candidate:** **NATS JetStream (Apache License 2.0 — CNCF)**
* **Justification:** RabbitMQ provides mature AMQP protocol compliance, native Dead-Letter Exchanges (DLX), message priority routing, and Raft-based Quorum Queues perfect for ingestion task processing.

---

## 11. Final Governance Status

Evaluation:
COMPLETE

Recommendation:
RabbitMQ (Mozilla Public License 2.0)

Governance:
PROPOSED TECHNOLOGY RECOMMENDATION

Approval:
OWNER REVIEW REQUIRED

Technology Approved:
NO

Implementation:
NOT AUTHORIZED
