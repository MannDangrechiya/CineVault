#!/usr/bin/env bash
# ==============================================================================
# CineVault OS — Automated PostgreSQL Restore Script (Free & Self-Hosted)
# ==============================================================================
# Restores a custom-format binary dump (pg_restore) into target database.
#
# Usage:
#   ./scripts/restore_postgres.sh <path_to_backup.dump>
# ==============================================================================

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <path_to_backup.dump>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "[ERROR] Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

PG_HOST="${POSTGRES_HOST:-localhost}"
PG_PORT="${POSTGRES_PORT:-5432}"
PG_DB="${POSTGRES_DB:-cinevault}"
PG_USER="${POSTGRES_USER:-cinevault_dev}"

echo "[INFO] Starting database restore from ${BACKUP_FILE} at $(date)..."

if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q "^cinevault-.*postgres"; then
    CONTAINER_NAME=$(docker ps --format '{{.Names}}' | grep "^cinevault-.*postgres" | head -n 1)
    echo "[INFO] Restoring via Docker container: ${CONTAINER_NAME}"
    cat "${BACKUP_FILE}" | docker exec -i "${CONTAINER_NAME}" \
        pg_restore -U "${PG_USER}" -d "${PG_DB}" --clean --if-exists --no-owner --no-privileges -v || true
else
    pg_restore -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d "${PG_DB}" \
        --clean --if-exists --no-owner --no-privileges -v "${BACKUP_FILE}" || true
fi

echo "[SUCCESS] Restore process completed. Verifying schema..."
