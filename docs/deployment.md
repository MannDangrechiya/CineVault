# CineVault OS — Production Deployment Guide (Phase W13)

## 1. Overview & Architectural Blueprint
CineVault OS is designed to be free-first, open-source friendly, self-hostable, and entirely independent of mandatory paid cloud providers.

### Production Topology:
```text
Client Browser / Mobile Web
            │
            ▼ (Ports 80 / 443, two HTTPS sites: SITE_ADDRESS + KEYCLOAK_HOSTNAME)
┌─────────────────────────────────────────────────────────────┐
│ Caddy v2 Edge Reverse Proxy (Automatic TLS per-site,        │
│ Security Headers: HSTS, X-Frame-Options, Nosniff — no CSP yet)│
└──────────────┬──────────────────────┬────────────────────┬───┘
               │                      │                    │
        /v1/*, /ai/*, /health*   /* (Next.js App)    KEYCLOAK_HOSTNAME
               │                      │                    │
               ▼                      ▼                    ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐ ┌───────────────────┐
│ FastAPI REST API Gateway    │ │ Next.js 15 Web Frontend     │ │ Keycloak 24 (OIDC) │
│ (4 Uvicorn Workers, Non-root│ │ (Standalone Node.js Server, │ │ own `keycloak` DB, │
│ Python 3.12 Slim Container) │ │ BFF API Proxy, HttpOnly)    │ │ KC_PROXY=edge      │
└──────────────┬──────────────┘ └─────────────────────────────┘ └─────────┬──────────┘
               │                                                          │
               ▼ (Port 6432)                                              ▼ (Port 5432)
┌─────────────────────────────┐
│ PgBouncer Connection Pooler │
│ (Transaction Pooling Mode)  │
└──────────────┬──────────────┘
               │
               ▼ (Port 5432)
┌─────────────────────────────┐   ┌─────────────────────────────┐
│ PostgreSQL 16 + pgvector    │   │ Valkey 8.0 Cache (RESP)     │
│ (6 Logical Schemas, 89k+    │   │ (Session & Rate Limiting)   │
│ Canonical Titles)           │   └─────────────────────────────┘
└─────────────────────────────┘   ┌─────────────────────────────┐
                                  │ RabbitMQ 4.0 Message Broker │
                                  │ (AMQP Ingestion & AI Tasks) │
                                  └─────────────────────────────┘
```

---

## 2. System Requirements
- **Host OS**: Linux (Ubuntu 22.04+, Debian 12+, Rocky Linux 9+), macOS 13+, or Windows 11 / Server with WSL2.
- **CPU**: 2 cores minimum (4+ cores recommended for high ingestion throughput).
- **RAM**: 4 GB RAM minimum (8 GB recommended for full local pgvector search & AI caching).
- **Disk**: 20 GB free disk space (SSD recommended for PostgreSQL & WAL).
- **Software**: Docker Engine 24+ and Docker Compose v2.20+.

---

## 3. Quick Start Deployment (Single-Command Docker Compose)

### Step 1: Clone Repository
```bash
git clone https://github.com/MannDangrechiya/CineVault.git
cd CineVault
```

### Step 2: Configure Environment
Copy the production environment template:
```bash
cp .env.production.example .env.prod
```
Edit `.env.prod` and supply strong passwords for:
- `POSTGRES_PASSWORD`
- `RABBITMQ_PASS`
- `JWT_SECRET_KEY` (64+ random characters)

And the following, **required** as of the Keycloak/TLS/storage wiring below — `docker compose up` refuses to start without them, naming exactly which one is missing (see §4):
```env
SITE_ADDRESS=cinevault.yourdomain.com
KEYCLOAK_HOSTNAME=auth.cinevault.yourdomain.com
KEYCLOAK_REALM=cinevault
KEYCLOAK_CLIENT_ID=cinevault-public-client
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=<GENERATE_STRONG_PASSWORD_HERE>
ACME_EMAIL=you@yourdomain.com
CDN_HOSTNAME=cdn.cinevault.yourdomain.com
S3_ACCESS_KEY_ID=<GENERATE_STRONG_ACCESS_KEY_HERE>
S3_SECRET_ACCESS_KEY=<GENERATE_STRONG_SECRET_KEY_HERE>
S3_ARTWORK_BUCKET=cinevault-artwork
SESSION_SECRET=<GENERATE_64_CHAR_RANDOM_STRING_HERE>
```
`CORS_ALLOWED_ORIGINS` and `CDN_BASE_URL` are no longer set by hand — `docker-compose.prod.yml` derives both from `SITE_ADDRESS`/`CDN_HOSTNAME` automatically. `S3_ACCESS_KEY_ID`/`S3_SECRET_ACCESS_KEY` double as both the self-hosted MinIO service's root credentials and the app's S3 client credentials — generate them the same way you'd generate any other strong password, they aren't tied to a real AWS account. `SESSION_SECRET` signs/encrypts the Next.js BFF session cookie (`apps/web/src/lib/auth/session.ts`) — generate it the same way as `JWT_SECRET_KEY` (e.g. `openssl rand -base64 48`); the web container now refuses to boot without it (`apps/web/src/instrumentation.ts`). `CDN_HOSTNAME` also now reaches the web image twice: once as a build-time arg (`NEXT_PUBLIC_CDN_HOSTNAME`, inlined into the client bundle — see `apps/web/Dockerfile`) and once as a container-runtime env var (read by `next.config.ts` when the standalone server starts) — both are derived automatically from the same `CDN_HOSTNAME` in `docker-compose.prod.yml`, nothing extra to set by hand.

### Step 3: Launch Production Stack
On Linux / macOS:
```bash
docker compose -f infra/docker/docker-compose.prod.yml up -d --build
```
On Windows:
```powershell
.\start-prod.ps1
```

### Step 4: Verify Deployment Health
```bash
curl -f http://localhost/health/readiness
```
Expected output:
```json
{
  "status": "READY",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "queue": "ok"
  }
}
```

Access the web application at `http://localhost` (or configured domain).

---

## 4. HTTPS, Domain & Keycloak Configuration

Caddy automatically obtains and renews TLS certificates via Let's Encrypt with zero manual Caddyfile editing — `infra/docker/Caddyfile` reads `SITE_ADDRESS` (the app) and `KEYCLOAK_HOSTNAME` (the identity provider) from the environment and serves each as its own HTTPS site, each with its own certificate. **Both DNS records must already point at this host before you start the stack**, or Let's Encrypt's HTTP-01 challenge will fail.

1. Point **three** DNS A/AAAA records at this host: your app domain (`SITE_ADDRESS`, e.g. `cinevault.yourdomain.com`), an auth subdomain (`KEYCLOAK_HOSTNAME`, e.g. `auth.cinevault.yourdomain.com`), and an artwork CDN subdomain (`CDN_HOSTNAME`, e.g. `cdn.cinevault.yourdomain.com`). Caddy provisions a separate Let's Encrypt certificate per hostname.
2. Set `SITE_ADDRESS`, `KEYCLOAK_HOSTNAME`, `CDN_HOSTNAME`, `KEYCLOAK_ADMIN_PASSWORD`, `S3_ACCESS_KEY_ID`/`S3_SECRET_ACCESS_KEY`, and the other vars from §2 in `.env.prod`. `docker compose up` will refuse to start (with a clear error naming the missing variable) if any required one is unset — this is deliberate: it fails closed instead of silently falling back to plain HTTP or an ambiguous `localhost` issuer.
3. Bring the stack up:
   ```bash
   docker compose -f infra/docker/docker-compose.prod.yml --env-file .env.prod up -d --build
   ```
   Caddy serves plain HTTP on `:80` only to redirect to HTTPS on `:443` and to complete the ACME challenge — it does not serve the app over HTTP. The `minio-init` job runs once at startup to create the artwork bucket and set it to anonymous-download (public reads only, no listing/writes) — `fastapi-backend` waits for it to finish before starting.
4. **One-time production realm setup**: the `keycloak` service starts with no realm imported (a real production realm needs real, randomly-generated client secrets, which shouldn't be baked into a committed file or an image-build step). Follow `packages/config/keycloak/README.md` to render `packages/config/keycloak/cinevault-realm-prod.template.json` with your real `SITE_ADDRESS` and import it via the Admin Console at `https://<KEYCLOAK_HOSTNAME>/admin/`. Until this step is done, login will fail with an OIDC discovery error — this is expected on a fresh deployment.
5. To change a domain later, update `.env.prod` and re-run `docker compose up -d caddy keycloak fastapi-backend nextjs-web` — Caddy will provision new certificates for the new hostnames automatically.

Not yet added at the Caddy layer: a Content-Security-Policy header (tracked as follow-up work — see the comment in `infra/docker/Caddyfile`). HSTS, X-Frame-Options, and the other hardened headers are already present on all three sites.

**Backing up MinIO**: `scripts/backup_postgres.sh`/`restore_postgres.sh` only cover Postgres. The artwork bucket lives in the `cinevault-prod-minio-data` Docker volume — back it up separately (e.g. `docker run --rm -v cinevault-prod-minio-data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/minio-data.tar.gz -C /data .`) if artwork durability matters to you beyond what's re-derivable from the ingestion pipeline.

---

## 5. Non-Docker / Bare-Metal Deployment

If running directly on host machines or dedicated VMs:

### 1. Database & Migrations:
```bash
# Initialize schemas
psql -U cinevault_admin -d cinevault -f packages/config/postgres/init-schemas.sql

# Run Flyway migrations
flyway -url=jdbc:postgresql://localhost:5432/cinevault \
       -user=cinevault_admin -password=your_password \
       -locations=filesystem:db/migrations migrate
```

### 2. FastAPI Backend:
```bash
pip install -r requirements.txt
uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Next.js Web Frontend:
```bash
cd apps/web
npm ci
npm run build
NODE_ENV=production PORT=3000 node .next/standalone/server.js
```
