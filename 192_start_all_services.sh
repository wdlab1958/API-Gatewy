#!/bin/bash
# AI Project - Essential Services Startup Script
# Location: UD4M (192.168.0.2)
# Services: AEGIS + AiNex + API Gateway (5 services only)

export GATEWAY_HOST="192.168.0.2"

BASE="/home/wdlab/ai_project"
LOG_DIR="/tmp"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

STARTED=0
SKIPPED=0
FAILED=0

check_port() {
    local port=$1
    if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
        return 0  # port in use
    fi
    return 1  # port free
}

start_service() {
    local name=$1
    local port=$2
    local workdir=$3
    shift 3
    local cmd="$@"

    if check_port "$port"; then
        echo -e "  ${YELLOW}[SKIP]${NC} ${name} (port ${port} already in use)"
        SKIPPED=$((SKIPPED + 1))
        return
    fi

    cd "$workdir" || { echo -e "  ${RED}[FAIL]${NC} ${name} - directory not found: ${workdir}"; FAILED=$((FAILED + 1)); return; }
    eval "nohup $cmd > ${LOG_DIR}/${name}.log 2>&1 &"
    local pid=$!
    sleep 1

    if kill -0 "$pid" 2>/dev/null; then
        echo -e "  ${GREEN}[OK]${NC}   ${name} (port ${port}, PID ${pid})"
        STARTED=$((STARTED + 1))
    else
        echo -e "  ${RED}[FAIL]${NC} ${name} (port ${port}) - check ${LOG_DIR}/${name}.log"
        FAILED=$((FAILED + 1))
    fi
}

echo "=========================================="
echo " Essential Services Startup (UD4M)"
echo " GATEWAY_HOST=${GATEWAY_HOST}"
echo "=========================================="
echo ""

echo "[Backend Services]"
echo "------------------------------------------"

# AEGIS Backend (4015)
start_service "aegis" 4015 \
    "${BASE}/AEGIS/apps/api" \
    "venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 4015"

# AiNex Consulting Backend (4007)
start_service "consulting" 4007 \
    "${BASE}/AiNex" \
    "venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 4007"

echo ""
echo "[Frontend Services]"
echo "------------------------------------------"

# AEGIS Web (4000) - Next.js
start_service "aegis_frontend" 4000 \
    "${BASE}/AEGIS/apps/web" \
    "npx next dev -p 4000 --hostname 0.0.0.0"

# AiNex Home (3001) - Next.js
start_service "ainex_home" 3001 \
    "${BASE}/webpage_ainex_forge" \
    "npx next dev -p 3001"

echo ""
echo "[API Gateway]"
echo "------------------------------------------"

start_service "api_gateway" 8080 \
    "${BASE}" \
    "GATEWAY_HOST=${GATEWAY_HOST} API_Gateway/venv/bin/python3 API_Gateway/api_gateway_v2.py"

echo ""
echo "=========================================="
echo " Startup Summary"
echo "=========================================="
echo -e "  Started: ${GREEN}${STARTED}${NC}"
echo -e "  Skipped: ${YELLOW}${SKIPPED}${NC}"
echo -e "  Failed:  ${RED}${FAILED}${NC}"
TOTAL=$((STARTED + SKIPPED + FAILED))
echo "  Total:   ${TOTAL} / 5"
echo ""
echo "  API Gateway: http://${GATEWAY_HOST}:8080"
echo "  Health Check: http://${GATEWAY_HOST}:8080/health"
echo ""
