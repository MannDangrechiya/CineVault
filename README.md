# CineVault OS — Enterprise Monorepo

> **Personal Entertainment Knowledge Platform & Intelligent Media Operating System**

CineVault OS combines a global canonical entertainment catalog, personal watch tracking, social recommendation network, local AI brain, and media server webhooks into an enterprise-grade modular monorepo.

---

## 🏛️ Architecture Overview

```
CineVault/
├── apps/                        # Client Applications
│   ├── web/                     # Next.js 15 (React 19, TypeScript, OLED Dark UI)
│   └── mobile/                  # Flutter 3.24+ (Riverpod, Drift SQLite, Dio)
├── services/                    # Backend & Processing Services
│   ├── api/                     # FastAPI Modular Monolith (PostgreSQL, AsyncPG, Pydantic v2)
│   └── ai_worker/               # Background task & Celery worker placeholder
├── packages/                    # Shared Configurations & Contracts
│   ├── config/                  # Kong, Keycloak, Postgres, Loki, Prometheus, OTEL
│   └── contracts/               # OpenAPI specifications & shared types
├── infra/                       # Infrastructure & Deployment
│   ├── docker/                  # Local development Docker Compose stack
│   └── scripts/                 # PowerShell and Bash launcher & validation scripts
├── db/                          # Database Evolution
│   └── migrations/              # Flyway SQL migrations (V1.0 - V2.6)
├── docs/                        # Architecture & History
│   ├── architecture/            # Git rules, architecture plans, ADRs, canonical specs
│   └── pr_history/              # Phase-wise pull request ledgers
├── .github/workflows/           # CI/CD pipelines (ci.yml, release-gate.yml)
├── start.bat / stop.bat         # 1-click dev launcher & shutdown scripts
└── requirements.txt             # Python backend dependencies
```

---

## 🚀 Quick Start (Local Development)

### 1. Launch Stack
```cmd
.\start.bat
```
*(Or via PowerShell: `.\infra\scripts\start-dev.ps1`)*

### 2. Available Endpoints
* **Web UI (OLED Dark)**: [http://localhost:3000](http://localhost:3000)
* **Backend API & Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Keycloak SSO**: [http://localhost:8080](http://localhost:8080)
* **RabbitMQ Console**: [http://localhost:15672](http://localhost:15672) (guest / guest)
* **MinIO Console**: [http://localhost:9001](http://localhost:9001) (minioadmin / minioadmin)
* **Grafana Dashboards**: [http://localhost:3002](http://localhost:3002)

### 3. Stop Stack
```cmd
.\stop.bat
```
*(Or via PowerShell: `.\infra\scripts\stop-dev.ps1`)*

---

## 🧪 Testing & Validation

* **Backend Pytest**: `python -m pytest tests/ -v`
* **Flutter Tests**: `cd apps/mobile && flutter test`
* **Web Typecheck**: `cd apps/web && npm run build`
