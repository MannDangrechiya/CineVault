# CineVault OS — Production Bootstrap Runbook (Phase 3P)

## 1. Overview & Architecture

CineVault OS enforces a sovereign, invite-gated registration model with strict separation between development test fixtures and production environments:

- **Authentication**: Native sovereign HS256 JWT tokens.
- **Access Control (RBAC)**: Role boundaries enforced by policy engine (`system_admin`, `curator`, `authenticated_user`).
- **Registration**: Strictly invite-gated via cryptographically unique invite codes in `social.invite_token`. Normal registrations are permanently restricted to the `authenticated_user` role to prevent privilege escalation.
- **Catalog Taxonomy**: Non-sensitive reference classification metadata (`canonical.content_type`, `canonical.genre`, `canonical.credit_role`, `canonical.theme`, `canonical.keyword`, `canonical.platform`) is seeded via Flyway migration `V4.0`. Synthetic titles and test data in `db/dev-seed/` are **strictly forbidden** from production execution.

---

## 2. Prerequisites

Before bootstrapping a fresh production instance:
1. Docker and Docker Compose v2 installed on the host.
2. Production environment file `.env` prepared from `.env.production.example`.
3. Required environment variables populated:
   - `SITE_ADDRESS`: Public domain name (e.g. `cinevault.example.com`).
   - `CDN_HOSTNAME`: Artwork CDN domain (e.g. `cdn.example.com`).
   - `POSTGRES_PASSWORD`: Strong, random password (min 32 characters).
   - `JWT_SECRET_KEY`: Cryptographically secure secret (min 64 characters).
   - `ACME_EMAIL`: Operator email for automated TLS certificate alerts.

> [!WARNING]
> Never mount or execute `db/dev-seed/` on a production database. Doing so injects synthetic mock entities and test artifacts into the production catalog.

---

## 3. Step-by-Step Production Initialization

### Step 3.1: Start Database & Cache Infrastructure
Bring up PostgreSQL and Valkey:
```bash
docker compose -f infra/docker/docker-compose.prod.yml up -d postgres valkey
```
Verify PostgreSQL is healthy:
```bash
docker compose -f infra/docker/docker-compose.prod.yml ps postgres
```

### Step 3.2: Execute Flyway Schema Migrations
Run automated migrations through `V4.0`:
```bash
docker compose -f infra/docker/docker-compose.prod.yml run --rm flyway
```
This applies all DDL tables and the baseline reference taxonomy (`V4.0__seed_canonical_reference_taxonomy.sql`).

Verify taxonomy presence:
```bash
docker compose -f infra/docker/docker-compose.prod.yml exec postgres \
  psql -U cinevault_admin -d cinevault -c "SELECT * FROM canonical.content_type;"
```
Expected output:
```text
 content_type_id |     type_name     |                                    description                                    
-----------------+-------------------+-----------------------------------------------------------------------------------
 movie           | Feature Film      | Full-length motion picture released for theatrical, streaming, or physical media.
 tv_series       | Television Series | Episodic television or web broadcast content.
 short_film      | Short Film        | Motion picture with a runtime under 40 minutes.
```

### Step 3.3: Start Core Application Services
```bash
docker compose -f infra/docker/docker-compose.prod.yml up -d fastapi-backend nextjs-web caddy
```

### Step 3.4: Execute Operator Production Bootstrap
Run the idempotent bootstrap command via the running backend container:
```bash
docker compose -f infra/docker/docker-compose.prod.yml exec -it fastapi-backend \
  python -m services.api.scripts.bootstrap_production
```
The script will prompt interactively for:
1. **System Administrator Email**: e.g., `operator@yourdomain.com`
2. **System Administrator Password**: Strong password (8–72 characters, hidden input)

Alternatively, for non-interactive / automated provisioning, supply environment variables:
```bash
docker compose -f infra/docker/docker-compose.prod.yml exec \
  -e BOOTSTRAP_ADMIN_EMAIL="operator@yourdomain.com" \
  -e BOOTSTRAP_ADMIN_PASSWORD="YourSecurePasswordHere!" \
  fastapi-backend python -m services.api.scripts.bootstrap_production
```

**Output Summary**:
```text
============================================================
CineVault OS — Production Bootstrap Successful
============================================================
System Admin Email : operator@yourdomain.com
System Admin ID    : <UUIDv7>
Assigned Roles     : system_admin, curator, authenticated_user
Canonical Taxonomy : 3 content types verified
Initial Invite Code: <16-char-code>
Invite Link Path   : /register?code=<16-char-code>
============================================================
```

> [!IMPORTANT]
> The bootstrap command is **strictly idempotent**. If a system administrator account already exists, it terminates immediately with status 0 without modifying credentials or overwriting users.

---

## 4. First Login & Verification

### Step 4.1: Administrator Login
Authenticate against the API to retrieve a JWT access token:
```bash
curl -X POST "https://${SITE_ADDRESS}/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "operator@yourdomain.com", "password": "YourSecurePasswordHere!"}'
```
Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "roles": ["system_admin", "curator", "authenticated_user"]
}
```

### Step 4.2: Verify Identity (`/v1/auth/me`)
```bash
curl -s -X GET "https://${SITE_ADDRESS}/v1/auth/me" \
  -H "Authorization: Bearer <access_token>"
```

### Step 4.3: Verify Administrative Access (`/admin/*`)
Trigger metadata sync or background operations using the admin token:
```bash
curl -s -X POST "https://${SITE_ADDRESS}/admin/sync-metadata" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 100}'
```
Expected response: HTTP `202 Accepted`.

---

## 5. User Onboarding & Invite Lifecycle

1. Share the initial invite code generated during bootstrap (or generate additional codes via `POST /social/invites` while logged in).
2. The invitee registers via the web UI or API:
   ```bash
   curl -X POST "https://${SITE_ADDRESS}/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "friend@yourdomain.com",
       "password": "UserStrongPassword123!",
       "invite_code": "<16-char-code>"
     }'
   ```
3. Verify that registration without an invite code or with an already-used code is rejected with HTTP `400 Bad Request`.
4. Verify that the newly registered friend cannot access `/admin/*` (HTTP `403 Forbidden`).

---

## 6. Edge Gateway Decision: `/admin/*` Routing

In Phase 3P, `/admin/*` was routed through Caddy directly to `fastapi-backend:8000`:
- **Rationale**: Administrative operations (TMDB sync, IMDb bulk catalog ingest) must be accessible to operators managing the instance remotely without requiring direct container SSH access.
- **Security Boundary**: The endpoints (`/admin/sync-metadata`, `/admin/catalog/sync-bulk`) strictly enforce `require_system_admin`:
  - Unauthenticated requests receive HTTP `401 Unauthorized`.
  - Normal authenticated users receive HTTP `403 Forbidden`.
  - Curators without `system_admin` role receive HTTP `403 Forbidden`.
  - Only accounts with `system_admin` in their JWT claims can invoke admin routes.

---

## 7. Disaster Recovery & Backup Requirements

Before making schema or infrastructure changes:
1. Run automated backup script:
   - Linux: `./scripts/backup_postgres.sh`
   - Windows PowerShell: `./scripts/backup_postgres.ps1`
2. Verify backup archive in `backups/` directory.
3. If an abort or rollback is necessary:
   - Restore using `./scripts/restore_postgres.sh <backup_file>`
