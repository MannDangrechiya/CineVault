# CineVault OS — Production Deployment Guide (Phase W13)

## 1. Overview & Architectural Blueprint
CineVault OS is designed to be free-first, open-source friendly, self-hostable, and entirely independent of mandatory paid cloud providers.

### Production Topology:
```text
Client Browser / Mobile Web
            │
            ▼ (Ports 80 / 443)
┌─────────────────────────────────────────────────────────────┐
│ Caddy v2 Edge Reverse Proxy (Automatic TLS, Compression,   │
│ Security Headers: CSP, HSTS, X-Frame-Options, Nosniff)     │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
        /v1/*, /ai/*, /health*          /* (Next.js App)
               │                              │
               ▼                              ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│ FastAPI REST API Gateway    │ │ Next.js 15 Web Frontend     │
│ (4 Uvicorn Workers, Non-root│ │ (Standalone Node.js Server, │
│ Python 3.12 Slim Container) │ │ BFF API Proxy, HttpOnly)    │
└──────────────┬──────────────┘ └─────────────────────────────┘
               │
               ▼ (Port 6432)
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
- `CORS_ALLOWED_ORIGINS` (e.g. `https://cinevault.example.com` or `http://localhost`)

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

## 4. HTTPS & Domain Configuration (Caddy)

Caddy automatically obtains and renews TLS certificates via Let's Encrypt / ZeroSSL with zero manual configuration.

1. Open `infra/docker/Caddyfile`.
2. Replace `:80` on line 10 with your fully qualified domain name:
```caddy
cinevault.yourdomain.com {
    encode zstd gzip
    
    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        Referrer-Policy strict-origin-when-cross-origin
        Permissions-Policy "camera=(), microphone=(), geolocation=()"
        -Server
    }

    handle /v1/* {
        reverse_proxy fastapi-backend:8000
    }
    handle /ai/* {
        reverse_proxy fastapi-backend:8000
    }
    handle /social/* {
        reverse_proxy fastapi-backend:8000
    }
    handle /health* {
        reverse_proxy fastapi-backend:8000
    }
    handle /* {
        reverse_proxy nextjs-web:3000
    }
}
```
3. Restart Caddy:
```bash
docker compose -f infra/docker/docker-compose.prod.yml restart caddy
```

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
