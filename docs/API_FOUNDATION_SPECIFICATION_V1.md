# CineVault OS — API Gateway & API Foundation Specification V1

**Document Type:** Technical Implementation & Specification Document  
**Status:** COMPLETE (Phase 3 Authorized Baseline)  
**Date:** 2026-08-08  
**Scope:** Local Gateway Architecture, Kong Proxy Routing, API Service Boundary, Authentication & RBAC Integration, JWT/JWKS Validation, Rate-Limiting, Health Probes, Correlation Identifiers, Observability, Safe Error Boundary, Local Execution & Verification  

---

## 1. Local Gateway Architecture

The CineVault OS Phase 3 API Gateway establishes the local development platform boundary using **Kong Gateway 3.6** in DB-less mode:

```text
Client (Flutter / Web / CLI)
           │
           ▼
     Kong Gateway (8000/8001)
     - Correlation Header Injection (X-Correlation-ID: UUIDv7)
     - Gateway Rate-Limiting (Valkey)
     - Local CORS Policies
           │
           ▼
   CineVault API Service (FastAPI :8000)
   - Route Handlers (/v1, /v1/me, /v1/sync, /internal/v1)
   - Keycloak JWT/JWKS Validation & Claims Parsing
   - Route-Level RBAC Policy Engine
   - Structured JSON Logging & Prometheus Metrics
           │
           ├───────────────────────────────┐
           ▼                               ▼
    PgBouncer Pooler (:6432)          Valkey Cache (:6379)
           │                          - Rate-limiting state
           ▼                          - Idempotency cache
    PostgreSQL 16 (:5432)
```

---

## 2. Kong Gateway Configuration & Routing

Kong is configured declaratively via `config/kong/kong.yml`:

| Service Identifier | Exposed Route | Upstream Service Target | Plugins Applied |
| :--- | :--- | :--- | :--- |
| `cinevault-public-api` | `/v1` | `http://host.docker.internal:8000/v1` | `request-transformer`, `rate-limiting` (600/min), `cors` |
| `cinevault-internal-api` | `/internal/v1` | `http://host.docker.internal:8000/internal/v1` | `rate-limiting` (1200/min) |
| `cinevault-health-api` | `/health` | `http://host.docker.internal:8000/health` | None |

### Security Boundaries
- Kong proxy port `8000` is bound locally.
- Kong admin API port `8001` is strictly non-public.
- Zero cloud or public DNS configurations exist in local setup.

---

## 3. Authentication & JWT/JWKS Validation

The API foundation integrates Phase 2 OIDC identity authentication:
- **Provider:** Keycloak (`http://localhost:8080/realms/cinevault-dev`).
- **JWKS Key Resolution:** Dynamically resolves RS256 public keys via `JWKSKeyResolver`.
- **Validation Controls:**
  1. Signature verification against realm public key.
  2. Issuer verification (`iss == http://localhost:8080/realms/cinevault-dev`).
  3. Audience verification (`aud == cinevault-api-gateway` or `cinevault-public-client`).
  4. Expiration (`exp > current_time`).
  5. Not-before evaluation (`nbf <= current_time`).
- **Secrets Safety:** Tokens, secrets, and private keys are never logged or committed.

---

## 4. Human RBAC & Machine Service Boundaries

Route-level access is enforced explicitly via FastAPI dependencies and `RBACPolicyEngine`:

| Role / Identity | Permitted Operations | Restricted Operations |
| :--- | :--- | :--- |
| **Anonymous** | Read public catalog (`GET /v1/titles/*`, `GET /v1/search`) | Personal data (`/v1/me/*`), Sync (`/v1/sync/*`), Control room (`/internal/*`) |
| **AuthenticatedUser** | Catalog read, personal logs (`/v1/me/*`), sync outbox push/pull (`/v1/sync/*`) | Control room administrative curation (`/internal/*`) |
| **Curator** | Public catalog, personal logs, sync, control room curation (`/internal/v1/*`) | Non-curator system settings |
| **SystemAdmin** | Full system operations | None |
| **Ingestion Service** | Ingestion payload write (`RAW_PAYLOAD_INSERT`) | **Canonical schema write strictly prohibited** (`CANONICAL_WRITE_*`) |

---

## 5. Offline Sync & Idempotency (ADR-004)

- **Push Endpoint:** `POST /v1/sync/push` processes outbox mutations recorded while client was offline.
- **Idempotency Keys:** Every state-changing request accepts `X-Idempotency-Key` or client-generated `mutation_id` (UUIDv7). Duplicate keys return cached responses without re-executing mutations.
- **Pull Stream:** `GET /v1/sync/pull` fetches delta updates based on sequential `sync_cursor` pointers.

---

## 6. Operational Health Probes

- **Liveness Probe:** `GET /health/liveness` (Returns HTTP 200 `status: UP`).
- **Readiness Probe:** `GET /health/readiness` (Verifies PgBouncer `:6432` and Valkey `:6379` socket connectivity).

---

## 7. Correlation Identifiers & Telemetry

- **Correlation ID Header:** `X-Correlation-ID` header (UUIDv7). Injected by Kong or middleware if missing, propagated downstream, included in structured logs and response headers.
- **Prometheus Metrics:** Exposed at `GET /metrics` (`cinevault_http_requests_total`, `cinevault_http_request_duration_seconds`, `cinevault_auth_failures_total`).
- **Structured JSON Logging:** Logs emitted in JSON format containing timestamp, level, logger name, message, and `correlation_id`.

---

## 8. Safe Error Boundary (RFC 7807)

All API errors return a sanitized JSON format:
```json
{
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "The requested Title entity 'invalid-id' was not found.",
    "status": 404,
    "correlation_id": "018f2e4a-7b31-7000-8000-123456789abc",
    "timestamp": "2026-08-08T18:25:00Z",
    "details": []
  }
}
```
Stack traces, SQL queries, database credentials, and Keycloak internal exceptions are strictly redacted.

---

## 9. Local Execution & Test Commands

### 1. Launch API Service
```bash
python -m services.api.main
```

### 2. Execute Full Phase 3 Test Suite
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 10. Troubleshooting Baseline

- **PgBouncer Connection Refused:** Confirm container `cinevault-local-pgbouncer` is healthy on port `6432`.
- **Valkey Connection Refused:** Confirm container `cinevault-local-valkey` is running on port `6379`.
- **JWT Validation Error:** Ensure Bearer token issuer matches `http://localhost:8080/realms/cinevault-dev`.
