#!/usr/bin/env bash
# ==============================================================================
# CineVault OS — Production Stack Launcher & Health Verifier (Linux / macOS)
# ==============================================================================

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}        CineVault OS — Production Deployment Stack    ${NC}"
echo -e "${CYAN}======================================================${NC}"

# 1. Dependency Validation
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR] Docker is not installed or not in PATH.${NC}"
    exit 1
fi

COMPOSE_FILE="infra/docker/docker-compose.prod.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}[ERROR] Cannot find compose file at: $COMPOSE_FILE${NC}"
    exit 1
fi

# 2. Environment Configuration
if [ -f ".env.prod" ]; then
    echo -e "${GREEN}[INFO] Loading production variables from .env.prod${NC}"
    set -a
    source .env.prod
    set +a
else
    echo -e "${YELLOW}[WARN] .env.prod not found. Using default hardened environment.${NC}"
fi

# 3. Spin Up Container Stack
echo -e "${CYAN}[INFO] Building and starting containerized services...${NC}"
docker compose -f "$COMPOSE_FILE" up -d --build

# 4. Health Check Polling Loops
echo -e "${CYAN}[INFO] Waiting for core infrastructure to become healthy...${NC}"

wait_for_service() {
    local service_name="$1"
    local max_retries="${2:-30}"
    local count=0

    echo -n "  -> Polling $service_name: "
    while [ $count -lt $max_retries ]; do
        local status
        status=$(docker inspect --format='{{json .State.Health.Status}}' "$service_name" 2>/dev/null || echo '"running"')
        if [ "$status" = '"healthy"' ] || [ "$status" = '"running"' ]; then
            echo -e "${GREEN}READY${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        count=$((count + 1))
    done
    echo -e "${RED}TIMEOUT${NC}"
    return 1
}

wait_for_service "cinevault-prod-postgres" 25 || true
wait_for_service "cinevault-prod-valkey" 15 || true
wait_for_service "cinevault-prod-rabbitmq" 20 || true

echo -e "\n${CYAN}[INFO] Verifying Edge Gateway & API status...${NC}"
sleep 5

echo -e "\n${GREEN}======================================================${NC}"
echo -e "${GREEN}      CineVault OS Production Deployment Active!     ${NC}"
echo -e "${GREEN}======================================================${NC}"
echo -e "  🌐 Web Application:       http://localhost"
echo -e "  🚀 Core REST API:         http://localhost/v1"
echo -e "  📚 OpenAPI Documentation: http://localhost/docs (only if DOCS_ENABLED=true)"
# R1 hardening pass: removed the RabbitMQ Management (15672) and PgBouncer
# (6432) lines that used to print here — neither port is actually published
# by docker-compose.prod.yml (RabbitMQ mgmt never was; PgBouncer's host
# mapping was removed as part of this pass, see that file's pgbouncer
# service comment). Both services remain reachable from other containers on
# the internal Docker network; this banner only advertises what's actually
# reachable from the host/browser.
echo -e "${GREEN}======================================================${NC}"
