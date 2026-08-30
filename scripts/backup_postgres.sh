#!/usr/bin/env bash
# ==============================================================================
# CineVault OS — Automated PostgreSQL Backup Script (Free & Self-Hosted)
# ==============================================================================
# Dumps the entire database using custom-format binary compression (pg_dump -F c).
# Supports retention pruning (defaults to keeping 14 days of backups).
#
# Usage:
#   ./scripts/backup_postgres.sh [/path/to/backup/dir]
#
# Environment variables:
#   POSTGRES_HOST (default: localhost)
#   POSTGRES_PORT (default: 5432)
#   POSTGRES_DB   (default: cinevault)
#   POSTGRES_USER (default: cinevault_dev)
#   PGPASSWORD    (optional)
#   BACKUP_RETENTION_DAYS (default: 14)
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${1:-${BACKUP_DIR:-./backups}}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="cinevault_backup_${TIMESTAMP}.dump"
FILEPATH="${BACKUP_DIR}/${FILENAME}"

mkdir -p "${BACKUP_DIR}"

echo "[INFO] Starting CineVault database backup at $(date)..."
echo "[INFO] Target: ${FILEPATH}"

PG_HOST="${POSTGRES_HOST:-localhost}"
PG_PORT="${POSTGRES_PORT:-5432}"
PG_DB="${POSTGRES_DB:-cinevault}"
PG_USER="${POSTGRES_USER:-cinevault_dev}"

# If running against Docker container directly:
if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q "^cinevault-.*postgres"; then
    CONTAINER_NAME=$(docker ps --format '{{.Names}}' | grep "^cinevault-.*postgres" | head -n 1)
    echo "[INFO] Using Docker container: ${CONTAINER_NAME}"
    docker exec -e PGPASSWORD="${PGPASSWORD:-dev_postgres_password_change_me}" "${CONTAINER_NAME}" \
        pg_dump -U "${PG_USER}" -d "${PG_DB}" -F c -b -v > "${FILEPATH}"
else
    pg_dump -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d "${PG_DB}" -F c -b -v -f "${FILEPATH}"
fi

BACKUP_SIZE=$(ls -lh "${FILEPATH}" | awk '{print $5}')
echo "[SUCCESS] Database backup created successfully (${BACKUP_SIZE}): ${FILEPATH}"

# Prune older backups
echo "[INFO] Pruning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "cinevault_backup_*.dump" -type f -mtime +"${RETENTION_DAYS}" -exec rm -f {} \;
echo "[SUCCESS] Backup workflow completed."
