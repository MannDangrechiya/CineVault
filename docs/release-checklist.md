# CineVault OS — Production Release Checklist (Phase W13)

Use this checklist before and after every production release or deployment.

---

## 1. Pre-Deployment Checks

- [ ] **Git Working Tree**:
  - `git status` shows a clean working tree.
  - Branch is up to date with `origin/master` (or target release branch).
  - No temporary debug files, `.env` files with live credentials, or uncommitted work.

- [ ] **Secrets & Configuration**:
  - Production `.env.prod` does NOT contain default development passwords.
  - `JWT_SECRET_KEY` is a cryptographically strong 64+ char random string.
  - `CORS_ALLOWED_ORIGINS` is configured with production domain(s).
  - `DOCS_ENABLED` is set to `false` (unless public API docs are explicitly intended).
  - `ALLOW_SEED_FALLBACK` is `false` (default for production).

- [ ] **Automated Test Regressions**:
  - Backend deployment suite passes: `pytest tests/test_w13_deployment_readiness.py`
  - Weekly backend regression (W3–W12) passes: 85+ tests green.
  - Disaster recovery test passes: `pytest tests/test_phase30_backup_disaster_recovery.py`
  - TypeScript check: `cd apps/web && npx tsc --noEmit` (0 errors).
  - ESLint check: `cd apps/web && npm run lint` (0 errors).
  - Production build: `cd apps/web && npm run build` (all routes compiled).

- [ ] **Pre-Release Database Backup**:
  - Run database dump before applying migrations:
    ```bash
    ./scripts/backup_postgres.sh ./backups
    ```
  - Verify backup file exists and has non-zero size.

---

## 2. Deployment Execution

- [ ] **Apply Migrations**:
  - Run Flyway migrations against target database.
  - Verify schema version is current with no errors.

- [ ] **Build & Start Services**:
  - Launch production stack:
    ```bash
    docker compose -f infra/docker/docker-compose.prod.yml up -d --build
    ```
  - Confirm all containers are healthy: `docker ps`

---

## 3. Post-Deployment Verification

- [ ] **Health & Readiness Check**:
  - `curl -f http://localhost:8000/health/liveness` -> `200 OK`
  - `curl -f http://localhost:8000/health/readiness` -> `200 OK` (all checks `ok`)

- [ ] **Security Headers Verification**:
  - Verify response headers from edge proxy:
    - `X-Content-Type-Options: nosniff`
    - `X-Frame-Options: DENY`
    - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
    - `Referrer-Policy: strict-origin-when-cross-origin`
    - `Permissions-Policy: camera=(), microphone=(), geolocation=()`

- [ ] **Smoke Test Critical Paths**:
  - [ ] Public Catalog: Browse `/movies` and `/series`
  - [ ] Search: Execute search query and verify real results
  - [ ] Title Detail: Open movie and series detail pages
  - [ ] User Auth: Sign in and verify session cookie (`HttpOnly; Secure; SameSite=Lax`)
  - [ ] Personal Vault: Add title to Watchlist and Library, record rating, write note
  - [ ] History & Continue Watching: Check history logs and series progress
  - [ ] Social & Clubs: Open `/social`, `/clubs`, `/friends`
  - [ ] Data Export: Download JSON and CSV exports from `/settings`
  - [ ] Oracle: Send prompt and verify structured response

---

## 4. Rollback Procedure (If Verification Fails)

1. Stop application traffic:
   ```bash
   docker compose -f infra/docker/docker-compose.prod.yml stop fastapi-backend nextjs-web
   ```
2. Restore database from pre-release backup:
   ```bash
   ./scripts/restore_postgres.sh ./backups/cinevault_backup_<TIMESTAMP>.dump
   ```
3. Check out previous release tag/commit in Git.
4. Rebuild and start previous container stack:
   ```bash
   docker compose -f infra/docker/docker-compose.prod.yml up -d --build
   ```
5. Verify health: `curl -f http://localhost:8000/health/readiness`
