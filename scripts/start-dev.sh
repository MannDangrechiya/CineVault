#!/usr/bin/env bash
# CineVault OS v2.0 — Development Environment Startup Script (Bash / POSIX)
# Usage: ./scripts/start-dev.sh [--no-docker] [--no-browser]

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${PORT:-8000}"
WEB_PORT=3000
START_DOCKER=true
OPEN_BROWSER=true

for arg in "$@"; do
  case $arg in
    --no-docker)
      START_DOCKER=false
      shift
      ;;
    --no-browser)
      OPEN_BROWSER=false
      shift
      ;;
  esac
done

echo ""
echo "================================================================="
echo "       🎬 CineVault OS v2.0 — Development Stack Launcher"
echo "================================================================="
echo " Root Directory: ${ROOT_DIR}"
echo " API Port:       ${API_PORT}"
echo " Web UI Port:    ${WEB_PORT}"
echo ""

# 1. Start Docker Infrastructure
if [ "$START_DOCKER" = true ]; then
  echo "[1/4] Checking Docker Infrastructure..."
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    (cd "${ROOT_DIR}" && docker compose up -d)
    echo "      ✓ Docker containers started."
  else
    echo "      ℹ Docker not running. Continuing in standalone mode."
  fi
fi

# 2. Check Ollama AI Engine
echo ""
echo "[2/4] Checking Ollama AI Neural Engine (Port 11434)..."
if curl -s -m 1 http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "      ✓ Ollama AI Brain active on http://localhost:11434"
else
  echo "      ℹ Ollama is not active on port 11434 (Optional for local AI matchmaking)."
fi

# 3. Launch FastAPI Backend Service
echo ""
echo "[3/4] Launching FastAPI Backend Service (Port ${API_PORT})..."
(cd "${ROOT_DIR}" && ENVIRONMENT=local_development PORT="${API_PORT}" python -m uvicorn services.api.main:app --host 0.0.0.0 --port "${API_PORT}" --reload) &
BACKEND_PID=$!
echo "${BACKEND_PID}" > "${ROOT_DIR}/.backend.pid"
echo "      ✓ Backend API launched (PID: ${BACKEND_PID})."

# 4. Launch Next.js Web Client
echo ""
echo "[4/4] Launching Next.js OLED Web Client (Port ${WEB_PORT})..."
(cd "${ROOT_DIR}/web" && npm run dev) &
WEB_PID=$!
echo "${WEB_PID}" > "${ROOT_DIR}/.web.pid"
echo "      ✓ Web client launched (PID: ${WEB_PID})."

echo ""
echo "================================================================="
echo "       🎉 CineVault OS v2.0 Services Active!"
echo "================================================================="
echo "  • Web Application:     http://localhost:${WEB_PORT}"
echo "  • Backend API & Docs:  http://localhost:${API_PORT}/docs"
echo "  • Social & AI Route:   http://localhost:${WEB_PORT}/social"
echo "  • Movies Catalog:      http://localhost:${WEB_PORT}/movies"
echo "  • TV Series Catalog:   http://localhost:${WEB_PORT}/series"
echo "  • Personal Dashboard:  http://localhost:${WEB_PORT}/dashboard"
echo "================================================================="
echo ""

if [ "$OPEN_BROWSER" = true ]; then
  sleep 2
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:${WEB_PORT}" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open "http://localhost:${WEB_PORT}" >/dev/null 2>&1 || true
  fi
fi

wait
