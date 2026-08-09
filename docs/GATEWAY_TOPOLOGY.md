# CineVault OS — Kong Gateway Topology & Routing Architecture

## Overview
CineVault OS uses **Kong Gateway (v3.6)** in DB-Less mode as the API Gateway for all incoming client and internal network traffic. Kong runs locally in Docker Compose on ports **8000** (Proxy) and **8001** (Admin API).

```
[Flutter Client / Web UI]
           │
           │ HTTP Request (port 8000)
           ▼
┌────────────────────────────────────────────────────────┐
│                   Kong Gateway                         │
│  - DB-Less mode (/usr/local/kong/declarative/kong.yml) │
│  - Plugins: Request Transformer, Rate Limiting, CORS   │
└────────────────────────────────────────────────────────┘
           │
           │ Proxy (Host network / host.docker.internal:8000)
           ▼
┌────────────────────────────────────────────────────────┐
│                   FastAPI Service                      │
│  - OIDC / JWT Verification                             │
│  - Async PostgreSQL (PgBouncer) + Valkey + RabbitMQ    │
└────────────────────────────────────────────────────────┘
```

---

## Topology & Network Port Mapping

| Component | Container Name | Host Port | Internal Port | Description |
|-----------|----------------|-----------|---------------|-------------|
| **Kong Proxy** | `cinevault-local-kong` | `8000` | `8000` | Primary entry point for client API requests |
| **Kong Admin API** | `cinevault-local-kong` | `8001` | `8001` | Gateway administration and health inspection |
| **FastAPI Backend** | Host process / Container | N/A | `8000` | FastAPI application listening on backend port |
| **Valkey Cache** | `cinevault-local-valkey` | `6379` | `6379` | Shared Redis-compatible rate limiter storage |
| **PgBouncer** | `cinevault-local-pgbouncer` | `6432` | `6432` | PostgreSQL connection pooler |
| **Keycloak OIDC** | `cinevault-local-keycloak` | `8080` | `8080` | OIDC Realm & JWKS provider |
| **MinIO Storage** | `cinevault-local-minio` | `9000` / `9001` | `9000` / `9001` | S3-compatible artwork storage & Web Console |

---

## Route Configuration (`kong.yml`)

### 1. Public API Route
- **Service Name**: `cinevault-public-api`
- **Path Match**: `/v1`
- **Upstream Target**: `http://host.docker.internal:8000/v1`
- **Plugins**:
  - `request-transformer`: Injects default `X-Correlation-ID` header.
  - `rate-limiting`: 600 requests/minute backed by Valkey (`redis_host: valkey`, port 6379).
  - `cors`: Permits cross-origin requests with `Authorization`, `Content-Type`, `X-Correlation-ID`, `X-Idempotency-Key` headers.

### 2. Internal Admin Route
- **Service Name**: `cinevault-internal-api`
- **Path Match**: `/internal/v1`
- **Upstream Target**: `http://host.docker.internal:8000/internal/v1`
- **Plugins**:
  - `rate-limiting`: 1200 requests/minute.

### 3. Health & Status Route
- **Service Name**: `cinevault-health-api`
- **Path Match**: `/health`
- **Upstream Target**: `http://host.docker.internal:8000/health`

---

## Local Verification Commands

```bash
# 1. Start the Docker infrastructure stack
docker-compose up -d

# 2. Check Kong Gateway status via Admin API (port 8001)
curl -s http://localhost:8001/status | jq .

# 3. List configured routes in Kong
curl -s http://localhost:8001/routes | jq .

# 4. Verify public API routing through Kong Proxy (port 8000)
curl -i http://localhost:8000/v1/health

# 5. Verify rate limiting headers in Kong response
curl -i http://localhost:8000/v1/titles
# Expected headers:
# X-RateLimit-Limit-Minute: 600
# X-RateLimit-Remaining-Minute: 599
```
