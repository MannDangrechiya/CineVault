#!/usr/bin/env bash
# CineVault OS v2.0 — Development Environment Shutdown Script (Bash / POSIX)
# Usage: ./scripts/stop-dev.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo ""
echo "================================================================="
echo "       🛑 CineVault OS v2.0 — Development Stack Shutdown"
echo "================================================================="
echo ""

# 1. Stop Docker Infrastructure
echo "[1/2] Stopping Docker containers..."
if command -v docker >/dev/null 2>&1; then
  (cd "${ROOT_DIR}" && docker compose stop) || true
  echo "      ✓ Docker containers stopped."
fi

# 2. Stop Background Process IDs if recorded
echo ""
echo "[2/2] Terminating background processes and clearing ports..."
if [ -f "${ROOT_DIR}/.backend.pid" ]; then
  kill "$(cat "${ROOT_DIR}/.backend.pid")" 2>/dev/null || true
  rm -f "${ROOT_DIR}/.backend.pid"
fi

if [ -f "${ROOT_DIR}/.web.pid" ]; then
  kill "$(cat "${ROOT_DIR}/.web.pid")" 2>/dev/null || true
  rm -f "${ROOT_DIR}/.web.pid"
fi

# Kill any lingering processes on ports 3000, 8000, 8002
for port in 3000 8000 8002; do
  if command -v lsof >/dev/null 2>&1; then
    PID=$(lsof -ti tcp:${port} 2>/dev/null || true)
    if [ -n "$PID" ]; then
      kill -9 $PID 2>/dev/null || true
      echo "      ✓ Stopped process on port ${port} (PID: ${PID})"
    fi
  fi
done

echo ""
echo "================================================================="
echo "       💤 CineVault OS v2.0 environment successfully stopped."
echo "================================================================="
echo ""
