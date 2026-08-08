# CineVault OS — Cache & Queue Infrastructure Specification V1

**Document Type:** Master Infrastructure Specification  
**Status:** Approved Phase 4 Baseline  
**Date:** 2026-08-08  
**Scope:** Distributed In-Memory Cache (Valkey), API Gateway Rate Limiting Integration (Kong → Valkey), AMQP Message Broker (RabbitMQ), Quorum Queues, Dead-Letter Exchanges (DLX), Retry/Rejection Topologies, Correlation Tracking, Ephemeral Idempotency, and Health Probes.

---

## 1. Purpose & Scope

The purpose of the **Cache & Queue Infrastructure Specification V1** is to establish the authoritative physical architecture and execution mechanics for CineVault OS's distributed state caching and asynchronous messaging infrastructure.

This specification details:
1. **Valkey** as the approved RESP-compatible distributed cache and rate-limiting state store.
2. **Kong Gateway → Valkey** distributed rate-limiting integration.
3. **RabbitMQ** as the approved AMQP 0-9-1 message broker.
4. **Quorum Queues** (`x-queue-type: quorum`) for data durability and fault tolerance.
5. **Dead-Letter Exchange (DLX)** (`cinevault.dlx`) and rejection routing for failed messages.
6. **Retry Topology** with exponential backoff and message TTL routing.
7. **Message Safety & Correlation ID** propagation (UUIDv7) across transport boundaries.
8. **Idempotency Strategy** to handle at-least-once message delivery.
9. **Health Check Probes** for operational liveness and readiness monitoring.

---

## 2. Governance Distinction Matrix

| Feature / Topology | Governance Level | Approved Baseline Reference / Dev Default |
|---|---|---|
| Distributed Cache Engine | **OWNER APPROVED ARCHITECTURE** | Valkey 8.0 (Linux Foundation BSD 3-Clause RESP engine) |
| Message Broker Standard | **OWNER APPROVED ARCHITECTURE** | RabbitMQ 4.0 (AMQP 0-9-1 protocol) |
| Queue Storage Engine | **OWNER APPROVED ARCHITECTURE** | Quorum Queues (`x-queue-type: quorum` Raft consensus) |
| Dead-Letter Exchange | **OWNER APPROVED ARCHITECTURE** | `cinevault.dlx` Direct Exchange |
| Egress & Public Rate Limits | **DEVELOPMENT IMPLEMENTATION DEFAULT** | Public Read: 600 req/min; Search: 120 req/min; Admin: 1200 req/min |
| Retry TTL Window | **DEVELOPMENT IMPLEMENTATION DEFAULT** | 5000 ms retry TTL delay; 3 max retry attempts |
| Max Message Payload Size | **DEVELOPMENT IMPLEMENTATION DEFAULT** | 512 KB per payload |

---

## 3. Valkey Distributed Cache Architecture

### 3.1 Overview & Responsibilities
Valkey serves as the L2 distributed cache and fast state backend.

**Permitted Cache Workloads:**
- API Gateway Rate-Limit counters and token bucket states.
- Ephemeral user session token metadata (hashed tokens only).
- Ephemeral idempotency checking keys (`idempotency:<uuid>`).
- L2 cached canonical title metadata (`CAT-1`).

**Prohibited Cache Workloads:**
- User personal data (`CAT-2` watch history, ratings).
- Plaintext authentication secrets or raw provider API keys.
- Un-reconciled raw provider payloads (`CAT-5`).
- AI proposals (`CAT-6`).

### 3.2 Connectivity & Security
- Protocol: RESP2 / RESP3 wire-compatible protocol.
- Local Container Port: `6379`.
- Auth: Local development authentication mode; zero production credentials committed.
- Health Check: `valkey-cli ping` returning `PONG`.

---

## 4. Kong → Valkey Rate Limiting Integration

### 4.1 Topology
Client traffic flows through Kong Gateway, which executes the `rate-limiting` plugin backed by Valkey:

```text
Client
  ↓ (HTTPS Request)
Kong Gateway Proxy (Port 8000)
  ↓ (Atomic INCR / EXPIRE over RESP)
Valkey Rate-Limit Counters (Port 6379)
  ↓ (Request permitted within threshold)
FastAPI Application Service (Port 8000 /internal/v1)
```

### 4.2 Kong Configuration
In `config/kong/kong.yml`:
```yaml
plugins:
  - name: rate-limiting
    config:
      minute: 600
      policy: redis
      redis_host: valkey
      redis_port: 6379
      redis_timeout: 2000
```

### 4.3 Limits & Failure Behavior
- Public API Route (`/v1/*`): 600 requests / minute default limit.
- Internal Admin Route (`/internal/v1/*`): 1200 requests / minute default limit.
- **Failure Behavior:** If Valkey becomes unreachable, Kong logs the error and falls open (or returns HTTP 500 depending on policy), maintaining service availability for non-rate-limited routes while raising critical readiness alerts.

---

## 5. RabbitMQ AMQP Message Broker & Queue Topology

### 5.1 Architecture Overview
RabbitMQ manages asynchronous task queues for background workers (ingestion, quality checks, reconciliation, sync, artwork media).

### 5.2 Required Exchanges
1. `cinevault.ingestion.direct` (Direct Exchange, Durable) — Main workload distribution exchange.
2. `cinevault.dlx` (Direct Exchange, Durable) — Dead-Letter Exchange for rejected/failed messages.

### 5.3 Required Quorum Queues
All queues strictly declare `x-queue-type: quorum` for Raft-based high availability and disk persistence:

```text
┌─────────────────────────┬───────────────────────┬───────────────────────────────┬───────────────────────────────┐
│ Queue Name              │ Queue Type            │ Binding Key                   │ Dead-Letter Routing Key       │
├─────────────────────────┼───────────────────────┼───────────────────────────────┼───────────────────────────────┤
│ `queue.ingestion`       │ `quorum`              │ `ingestion.task`              │ `ingestion.dead_letter`       │
│ `queue.quality`         │ `quorum`              │ `quality.task`                │ `quality.dead_letter`         │
│ `queue.reconciliation`  │ `quorum`              │ `reconciliation.task`         │ `reconciliation.dead_letter`   │
│ `queue.sync`            │ `quorum`              │ `sync.task`                   │ `sync.dead_letter`           │
│ `queue.media`           │ `quorum`              │ `media.task`                  │ `media.dead_letter`          │
│ `queue.dead_letter`     │ `quorum`              │ `*.dead_letter`               │ N/A (Terminal Rejection Queue)│
│ `queue.ingestion.retry` │ `quorum`              │ `ingestion.retry`             │ Re-routes to `ingestion.task` │
└─────────────────────────┴───────────────────────┴───────────────────────────────┴───────────────────────────────┘
```

---

## 6. Dead-Letter Exchange (DLX) & Rejection Routing

### 6.1 Dead-Letter Flow
When a message processing fails permanently or exceeds maximum retries, the consumer rejects the message with `requeue=False`:

```text
[ Worker Consumer ]
       │
       ▼ (Processing failure / Permanent rejection)
[ NACK / Reject (requeue=False) ]
       │
       ▼ (RabbitMQ automatic routing)
[ Dead-Letter Exchange (cinevault.dlx) ]
       │
       ▼ (Routing key: *.dead_letter)
[ Dead-Letter Queue (queue.dead_letter) ]
       │
       ▼ (Retained for curator investigation & quarantine review)
```

---

## 7. Retry Topology & Exponential Backoff

### 7.1 Retry Flow
Transient failures (e.g. temporary network timeout) trigger the retry topology:

```text
[ Message Received ] ──▶ [ Temporary Processing Error ]
                                   │
                                   ▼
          [ Publish to queue.ingestion.retry with TTL ]
                                   │
                                   ▼ (5000 ms TTL expires)
          [ Dead-lettered back to cinevault.ingestion.direct ]
                                   │
                                   ▼
          [ Re-delivered to queue.ingestion for processing ]
```

---

## 8. Message Safety, Correlation ID & Idempotency

### 8.1 Message Safety
- **No Secrets:** Passwords, API secrets, OAuth tokens, and private keys MUST NOT be published in queue payloads.
- **No CAT-2 Plaintext:** User personal watch history notes, addresses, or unencrypted PII are forbidden in queue payloads. Payloads carry strictly entity identifiers (`title_id`, `user_id`, `provider_id`).
- **Size Limit:** Max payload size is strictly capped at **512 KB**.

### 8.2 Correlation ID Propagation
Every message published to RabbitMQ preserves the `UUIDv7` correlation ID:
- Header: `x-correlation-id`
- AMQP Property: `correlation_id`

### 8.3 Idempotency Strategy
- Message publishers generate or include an `x-idempotency-key` (UUIDv7).
- Consumers invoke `valkey_manager.check_and_set_idempotency(key, ttl=86400)` before processing.
- Duplicate deliveries are safely skipped without side effects.

---

## 9. Operational Health Checks

### 9.1 Readiness Probe Endpoint
`GET /health/readiness` evaluates PgBouncer, Valkey, and RabbitMQ:

```json
{
  "status": "READY",
  "dependencies": {
    "pgbouncer": {
      "status": "HEALTHY",
      "target": "localhost:6432"
    },
    "valkey": {
      "status": "HEALTHY",
      "target": "localhost:6379",
      "engine": "Valkey 8.0 (Linux Foundation RESP)"
    },
    "rabbitmq": {
      "status": "HEALTHY",
      "target": "localhost:5672",
      "engine": "RabbitMQ 4.0 (AMQP 0-9-1)"
    }
  }
}
```

*HTTP 200 OK* when all 3 dependencies are HEALTHY.  
*HTTP 503 SERVICE UNAVAILABLE* if any dependency fails.

---

## 10. Open Decisions Preservation

Phase 4 preserves the open governance state for the following decisions:
- `DEC-OBS-OPN-01`: Observability log storage backend
- `DEC-OBS-OPN-02`: Distributed tracing sampling rate
- `DEC-INFRA-OPN-02`: Multi-Region read replica scaling
- `DEC-ING-OPN-02`: Provider acquisition retention window
- `DEC-QUAL-OPN-02`: Quarantine payload auto-purge policy
- `DEC-PHYS-OPN-01`: Physical table partitioning threshold

---

## 11. Testing & Validation

Phase 4 infrastructure verification is executed via `tests/test_phase4_cache_queue.py`:
- Valkey read/write, atomic counters, idempotency, health checks.
- RabbitMQ connection, Quorum Queue creation, DLX routing, retry flow, correlation propagation.
- Kong → Valkey rate-limiting declarative config validation.
- Security and payload safety checks.
