# CineVault OS — Backup & Disaster Recovery Runbook (Phase 30 / W11 / W13)

## 1. Overview & Disaster Recovery Invariants
CineVault enforces an automated backup and disaster recovery validation workflow to guarantee relational integrity and vector index preservation across all 6 logical PostgreSQL schemas:
1. `canonical` (CAT-1 Catalog, Titles, Editions, Releases, Credits, Genres, Streaming Offers)
2. `personal` (CAT-2 User Media Library, Watch Events, Ratings, Notes, Reviews, Collections, Streaks)
3. `social` (Friendships, Peer Recommendations, 384-dimensional pgvector Taste Profiles, Watch Clubs, Challenges, Pick Rooms)
4. `quality` (Ingestion Quarantine, CAT-6 AI Proposal Staging, Field Provenance, Reconciliation Candidates)
5. `ingestion` (Raw Payload Captures, Ingestion Runs, Provider Checkpoints, Data Source Registry)
6. `audit` (Immutable Tamper-Evident HMAC SHA-256 Audit Logs)

---

## 2. Recovery Objectives (RPO & RTO)
- **Recovery Point Objective (RPO)**: < 24 hours via automated daily dumps (or < 5 minutes with optional PostgreSQL continuous WAL archiving).
- **Recovery Time Objective (RTO)**: < 15 minutes to full operational recovery using binary `pg_restore`.

---

## 3. Automated Backup Procedures

### A. Linux / macOS / Docker Host (`backup_postgres.sh`)
```bash
# Make script executable
chmod +x ./scripts/backup_postgres.sh

# Run manual backup
./scripts/backup_postgres.sh ./backups

# Automated recurring schedule via cron (daily at 02:00 UTC)
# Edit crontab with `crontab -e`:
0 2 * * * cd /opt/cinevault && ./scripts/backup_postgres.sh /var/backups/cinevault >> /var/log/cinevault-backup.log 2>&1
```

### B. Windows / PowerShell Host (`backup_postgres.ps1`)
```powershell
# Run manual backup
.\scripts\backup_postgres.ps1 -BackupDir "C:\backups\cinevault" -RetentionDays 14

# Automated recurring schedule via Windows Task Scheduler:
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\CineVault\scripts\backup_postgres.ps1 -BackupDir C:\backups\cinevault"
$Trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "CineVault-PostgreSQL-Backup" -Action $Action -Trigger $Trigger -Description "Daily CineVault database backup"
```

---

## 4. Disaster Recovery & Restore Runbook

When full database recovery is required following data loss, corruption, or infrastructure migration:

### Step 1: Stop Traffic to API
To prevent partial writes during restore:
```bash
docker compose -f infra/docker/docker-compose.prod.yml stop fastapi-backend nextjs-web
```

### Step 2: Provision or Clean Target Database
If starting with a clean PostgreSQL container/server:
```sql
CREATE DATABASE cinevault;
```
If restoring into an existing corrupted database, ensure the database is clean or use `--clean` flag during restore.

### Step 3: Run Binary Restore
#### Via Linux / Docker:
```bash
chmod +x ./scripts/restore_postgres.sh
./scripts/restore_postgres.sh ./backups/cinevault_backup_YYYYMMDD_HHMMSS.dump
```
Or directly via `pg_restore`:
```bash
pg_restore -h localhost -p 5432 -U cinevault_admin -d cinevault \
    --clean --if-exists --no-owner --no-privileges -v \
    ./backups/cinevault_backup_YYYYMMDD_HHMMSS.dump
```

#### Via Windows PowerShell:
```powershell
.\scripts\restore_postgres.ps1 -BackupFile ".\backups\cinevault_backup_YYYYMMDD_HHMMSS.dump"
```

### Step 4: Verify Database Relational & Vector Integrity
Run the verification queries:
```sql
-- 1. Verify schema table count
SELECT schemaname, count(*) 
FROM pg_tables 
WHERE schemaname IN ('canonical', 'personal', 'social', 'quality', 'ingestion', 'audit') 
GROUP BY schemaname;

-- 2. Verify catalog record count
SELECT count(*) FROM canonical.title;

-- 3. Verify pgvector extension and cosine distance calculation
SELECT 
    p1.user_id AS user_1,
    p2.user_id AS user_2,
    1 - (p1.taste_vector <=> p2.taste_vector) AS cosine_similarity
FROM social.user_taste_profile p1
CROSS JOIN social.user_taste_profile p2
WHERE p1.user_id != p2.user_id
LIMIT 5;

-- 4. Verify foreign key constraints are active
SELECT conname, contype 
FROM pg_constraint 
WHERE contype = 'f' AND connamespace = 'personal'::regnamespace;
```

### Step 5: Run Automated Disaster Recovery Regression Test
```bash
pytest tests/test_phase30_backup_disaster_recovery.py -v
```

### Step 6: Restart API & Web Services
```bash
docker compose -f infra/docker/docker-compose.prod.yml up -d
```

### Step 7: Verify Application Health
```bash
curl -f http://localhost:8000/health/readiness
```
Expected output:
```json
{
  "status": "READY",
  "timestamp": "2026-08-30T...",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "queue": "ok"
  }
}
```

---

## 5. Forward-Only Migration Rollback Strategy
Flyway migrations in CineVault are strictly **forward-only** (`V1.0` through the current latest — check `db/migrations/` for the actual highest version, currently `V3.8`; don't rely on this number staying accurate as new migrations land).

If a bad migration occurs in production:
1. **Do not attempt manual reverse DDL on live tables.**
2. Restore the pre-migration backup dump using the procedure in Section 4.
3. Fix the migration script in source control and apply the corrected forward migration.
