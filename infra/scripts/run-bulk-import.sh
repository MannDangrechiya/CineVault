#!/usr/bin/env bash
# CineVault OS v2.0 — High-Speed Bulk IMDb Ingestion Launcher (Bash / POSIX)
# Usage:
#   ./infra/scripts/run-bulk-import.sh
#   ./infra/scripts/run-bulk-import.sh --min-votes 1000
#   ./infra/scripts/run-bulk-import.sh --dry-run
#   ./infra/scripts/run-bulk-import.sh --skip-download

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH}"

echo ""
echo "================================================================="
echo "       🎬 [CineVault OS] High-Speed IMDb Bulk Ingestion"
echo "================================================================="
echo " Root Directory: ${ROOT_DIR}"
echo " Script:         services/api/scripts/seed_bulk_imdb.py"
echo " Arguments:      $*"
echo ""

cd "${ROOT_DIR}"
python3 services/api/scripts/seed_bulk_imdb.py "$@"
