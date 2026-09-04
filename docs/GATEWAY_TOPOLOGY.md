# CineVault OS — Edge Gateway Topology & Routing Architecture

> **Phase 3 update:** Kong was audited and removed. It was never wired into
> `docker-compose.prod.yml` (production never had a Kong service), and in dev
> it collided on host port 8000 with FastAPI's own default bind — it wasn't a
> reliably functioning part of the local workflow either. **Caddy is, and has
> always effectively been, the sole edge gateway.** This document now
> describes the real topology instead of the aspirational one.

## Overview

CineVault OS uses **Caddy 2** as the sole public-facing reverse proxy and TLS
terminator. It is the only container that publishes ports to the host
(`80`/`443`) in production.

```
                    INTERNET
                       │
                       ▼
                  CADDY :443
        (automatic HTTPS, security headers,
         zstd/gzip compression)
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   SITE_ADDRESS   KEYCLOAK_HOSTNAME  CDN_HOSTNAME
   /v1,/ai,/social      │           (artwork reads)
   /automations,        ▼
   /internal/*      keycloak:8080
   /health,/docs   (see Keycloak
        │           decommission
        ▼             note below)
  fastapi-backend:8000
        │
   catch-all /*
        ▼
   nextjs-web:3000
```

## Topology & Port Mapping (production)

| Component | Container Name | Host Port | Internal Port | Notes |
|---|---|---|---|---|
| **Caddy** | `cinevault-prod-caddy` | `80`, `443` | `80`, `443` | Only container exposed to the host |
| **FastAPI Backend** | `cinevault-prod-backend` | — (internal only) | `8000` | Reached only via Caddy or the Docker network |
| **Next.js Web** | `cinevault-prod-web` | — (internal only) | `3000` | Reached only via Caddy |
| **Postgres** | `cinevault-prod-postgres` | — (internal only) | `5432` | Never published to host |
| **Valkey** | `cinevault-prod-valkey` | — (internal only) | `6379` | Never published to host |

Rate limiting and request routing are handled in FastAPI itself
(`services/api/rate_limiter.py`, Valkey-backed) rather than by a gateway
plugin — there is no separate API-gateway-level rate limiter.

## Route configuration (`infra/docker/Caddyfile`)

- `{$SITE_ADDRESS}` → `/v1/*`, `/ai/*`, `/social/*`, `/automations/*`,
  `/internal/*` (except the three internal-only sub-paths below), `/health*`,
  `/docs*`, `/openapi.json` → proxied to `fastapi-backend:8000`
- `{$SITE_ADDRESS}` → `/internal/v1/jobs/*`, `/internal/v1/performance/*`,
  `/internal/v1/observability/*` → **blocked at the edge** (`respond 404`);
  these routers only check a spoofable header and are reachable
  internally-only over the Docker network
- `{$SITE_ADDRESS}` → `/metrics*` → **blocked at the edge** (unauthenticated
  Prometheus text output; no scraper needs it public)
- `{$SITE_ADDRESS}` → `/*` (catch-all) → `nextjs-web:3000`
- `{$CDN_HOSTNAME}` → `/*` → artwork storage (see the storage-migration note
  in `docs/storage_cdn.md` for the current backend)

Each site gets its own automatic Let's Encrypt certificate; HTTP is
redirected to HTTPS by default.

## Local verification

```bash
curl -i https://<SITE_ADDRESS>/health/liveness
curl -i https://<SITE_ADDRESS>/v1/titles
```

No gateway-specific admin API exists — Caddy is configured declaratively via
`infra/docker/Caddyfile` and has no runtime admin endpoint exposed
(`admin off` in production).
