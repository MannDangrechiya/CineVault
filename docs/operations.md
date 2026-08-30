# CineVault OS — Operations Handbook (Phase W13)

## 1. Daily Operations & Monitoring

### Health & Readiness Probes
| Endpoint | Purpose | Expected Status | Description |
|---|---|---|---|
| `GET /health/liveness` | Process Liveness | 200 OK | Confirms FastAPI process is responsive |
| `GET /health/readiness` | Dependency Check | 200 OK / 503 | Executes `SELECT 1` on PostgreSQL and checks Valkey & RabbitMQ |
| `GET /health/startup` | Startup Probe | 200 OK / 503 | Used by container orchestrators before routing traffic |

### Log Inspection
To view logs across all production containers in real time:
```bash
# All logs with timestamps
docker compose -f infra/docker/docker-compose.prod.yml logs -f --tail=100

# Backend API logs only
docker compose -f infra/docker/docker-compose.prod.yml logs -f fastapi-backend

# Next.js web frontend logs only
docker compose -f infra/docker/docker-compose.prod.yml logs -f nextjs-web

# Caddy access and error logs
docker compose -f infra/docker/docker-compose.prod.yml logs -f caddy
```

### Log Rotation (Self-Hosted Docker)
To prevent container logs from consuming unbounded disk space, configure Docker's local logging driver in `/etc/docker/daemon.json`:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "20m",
    "max-file": "5"
  }
}
```
Then restart Docker daemon (`sudo systemctl restart docker`).

---

## 2. Container Lifecycle & Restarts

### Graceful Rolling Restart
```bash
# Restart backend without dropping database connections
docker compose -f infra/docker/docker-compose.prod.yml restart fastapi-backend

# Restart frontend
docker compose -f infra/docker/docker-compose.prod.yml restart nextjs-web

# Full stack restart
docker compose -f infra/docker/docker-compose.prod.yml restart
```

### Clean Stack Rebuild (Zero Data Loss)
Volumes are external/persistent (`postgres-prod-data`, `valkey-prod-data`, etc.). Rebuilding images does **not** erase your data:
```bash
docker compose -f infra/docker/docker-compose.prod.yml down
docker compose -f infra/docker/docker-compose.prod.yml up -d --build
```

---

## 3. Database Maintenance & Migration Operations

### Apply New Migrations
When pulling an updated codebase with new Flyway migration files:
```bash
docker compose -f infra/docker/docker-compose.prod.yml run --rm flyway
```

### Database VACUUM & ANALYZE
For periodic maintenance on PostgreSQL tables:
```bash
docker exec -it cinevault-prod-postgres psql -U cinevault_admin -d cinevault -c "VACUUM ANALYZE;"
```

### Checking pgvector Index Health
```sql
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'user_taste_profile';
```

---

## 4. Troubleshooting Guide

### Issue: `/health/readiness` returns 503 Service Unavailable
1. Check database container status: `docker ps | grep postgres`
2. Check database logs: `docker compose -f infra/docker/docker-compose.prod.yml logs postgres`
3. Verify PgBouncer connection: `docker compose -f infra/docker/docker-compose.prod.yml logs pgbouncer`
4. Verify Valkey: `docker exec cinevault-prod-valkey valkey-cli ping`
5. Verify RabbitMQ: `docker exec cinevault-prod-rabbitmq rabbitmq-diagnostics ping`

### Issue: Next.js Frontend shows "Failed to reach CineVault API"
1. Verify `API_BASE_URL` in `docker-compose.prod.yml` points to `http://fastapi-backend:8000`.
2. Check network connectivity between containers:
   ```bash
   docker exec cinevault-prod-web wget -qO- http://fastapi-backend:8000/health/liveness
   ```
3. Check browser console for CSRF or origin mismatches.

### Issue: Application refuses to boot with "Refusing to start" error
CineVault blocks boot if `ENVIRONMENT=production` or `staging` but default development passwords (`dev_postgres_password_change_me`, `cinevault-local-dev-jwt-secret-...`) are still present. Update `.env.prod` with real generated secrets.
