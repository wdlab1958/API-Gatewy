#!/bin/bash
# AI Project - 모든 서비스 시작 스크립트 (v2)
# 실제 검증된 실행 방법 기반

BASE="/home/ubuntu-02/ai_project"
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
echo " AI Project Services Startup Script (v2)"
echo "=========================================="
echo ""
echo "[Backend Services - 15 services]"
echo "------------------------------------------"

# Dataset_Gen (4001) - Streamlit
start_service "dataset_gen" 4001 \
    "${BASE}/Dataset_Gen" \
    "myenv/bin/streamlit run main.py --server.port 4001 --server.headless true"

# DeepFake (4002)
start_service "deepfake" 4002 \
    "${BASE}/DeepFake-main/src" \
    "../venv/bin/uvicorn api_server:app --host 0.0.0.0 --port 4002"

# a3-adep (4003)
start_service "a3_adep" 4003 \
    "${BASE}/a3-adep" \
    "venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 4003"

# a3de (4004)
start_service "a3de" 4004 \
    "${BASE}/a3de/backend" \
    "../venv/bin/uvicorn main:app --host 0.0.0.0 --port 4004"

# ai_carelink (4005)
start_service "carelink" 4005 \
    "${BASE}/ai_carelink/backend" \
    "../venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 4005"

# ai_cluster_pc (4006)
start_service "cluster" 4006 \
    "${BASE}/ai_cluster_pc" \
    "venv/bin/uvicorn src.server:app --host 0.0.0.0 --port 4006"

# ai_consulting (4007)
start_service "consulting" 4007 \
    "${BASE}/ai_consulting" \
    "venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 4007"

# ai_factory (4008)
start_service "factory" 4008 \
    "${BASE}/ai_factory" \
    "venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 4008"

# ai_labor (4009)
start_service "labor" 4009 \
    "${BASE}/ai_labor" \
    "venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 4009"

# ai_langgraph (4010)
start_service "langgraph" 4010 \
    "${BASE}/ai_langgraph" \
    "venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 4010"

# ai_multimodals (4011) - Flask-SocketIO
start_service "multimodals" 4011 \
    "${BASE}/ai_multimodals/web" \
    '../venv/bin/python -c "import app as a; a.socketio.run(a.app, host='"'"'0.0.0.0'"'"', port=4011, debug=False, allow_unsafe_werkzeug=True)"'

# aialbm (4012)
start_service "aialbm" 4012 \
    "${BASE}/aialbm" \
    "aialb_venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 4012"

# enterprise_factory (4013)
start_service "enterprise" 4013 \
    "${BASE}/enterprise_factory/local-llm-os/backend" \
    "python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 4013"

# panda_chetbot (4014)
start_service "panda" 4014 \
    "${BASE}/panda_chetbot/api" \
    "../venv/bin/uvicorn main:app --host 0.0.0.0 --port 4014"

# Cluster Master (8200)
start_service "cluster_master" 8200 \
    "${BASE}/Cluster-Master" \
    "venv/bin/uvicorn src.server:app --host 0.0.0.0 --port 8200"

echo ""
echo "[Frontend Services - 12 services]"
echo "------------------------------------------"

# TruthLens (8001) - static
start_service "truthlens" 8001 \
    "${BASE}/DeepFake-main/webpage_truthlens" \
    "python3 -m http.server 8001"

# webpage_AiNex (8002) - static
start_service "webpage_ainex" 8002 \
    "${BASE}/webpage_AiNex" \
    "python3 -m http.server 8002"

# AiNex_Home (3001) - Next.js
start_service "ainex_home" 3001 \
    "${BASE}/AiNex_Home-main" \
    "npx next dev -p 3001"

# Cluster Master Web (3002) - Next.js
start_service "cluster_master_web" 3002 \
    "${BASE}/webpage_ai_cluster_master" \
    "npx next dev -p 3002"

# aialbm Web (3003) - Next.js
start_service "aialbm_web" 3003 \
    "${BASE}/webpage_aialbm" \
    "npx next dev -p 3003"

# carelink Web (3004) - Next.js
start_service "carelink_web" 3004 \
    "${BASE}/webpage_carelink" \
    "npx next dev -p 3004"

# ai_homepage (3005) - Next.js
start_service "ai_homepage" 3005 \
    "${BASE}/ai_homepage" \
    "npx next dev -p 3005"

# carelink Frontend (5005) - Next.js
start_service "carelink_frontend" 5005 \
    "${BASE}/ai_carelink/frontend" \
    "npx next dev -p 5005"

# langgraph Frontend (5010) - Vite
start_service "langgraph_frontend" 5010 \
    "${BASE}/ai_langgraph/frontend" \
    "npx vite --port 5010 --host"

# enterprise Frontend (5013) - Vite
start_service "enterprise_frontend" 5013 \
    "${BASE}/enterprise_factory/local-llm-os/frontend" \
    "npx vite --port 5013 --host"

# unified_portal (5015) - Vite
start_service "unified_portal" 5015 \
    "${BASE}/unified_portal" \
    "npx vite --port 5015 --host"

# a3de Frontend (5004) - Vite
start_service "a3de_frontend" 5004 \
    "${BASE}/a3de/frontend" \
    "node node_modules/vite/bin/vite.js --port 5004 --host"

echo ""
echo "[API Gateway]"
echo "------------------------------------------"

start_service "api_gateway" 8080 \
    "${BASE}" \
    "python3 API_Gateway/api_gateway_v2.py"

echo ""
echo "=========================================="
echo " Startup Summary"
echo "=========================================="
echo -e "  Started: ${GREEN}${STARTED}${NC}"
echo -e "  Skipped: ${YELLOW}${SKIPPED}${NC}"
echo -e "  Failed:  ${RED}${FAILED}${NC}"
TOTAL=$((STARTED + SKIPPED + FAILED))
echo "  Total:   ${TOTAL} / 28"
echo ""
echo "  API Gateway: http://localhost:8080"
echo "  Health Check: http://localhost:8080/health"
echo ""

# Wait a moment for services to fully initialize, then do health check
if [ "$STARTED" -gt 0 ]; then
    echo "Waiting for services to initialize..."
    sleep 5
    echo ""
    echo "[Health Check]"
    echo "------------------------------------------"
    HEALTH=$(curl -s --max-time 10 http://localhost:8080/health 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$HEALTH" ]; then
        eval "$(echo "$HEALTH" | python3 -c "
import sys, json
d = json.load(sys.stdin)
healthy = 0
total = 0
for section in ['backend', 'frontend']:
    for name, info in d.get(section, {}).items():
        total += 1
        if info.get('status') == 'healthy':
            healthy += 1
print(f'GW_HEALTHY={healthy}')
print(f'GW_TOTAL={total}')
" 2>/dev/null)"
        echo -e "  Gateway reports: ${GREEN}${GW_HEALTHY}${NC}/${GW_TOTAL} services healthy"
    else
        echo -e "  ${YELLOW}Gateway not responding yet - check manually:${NC}"
        echo "  curl http://localhost:8080/health"
    fi
fi

echo ""
echo "=========================================="
echo " Logs: ${LOG_DIR}/<service_name>.log"
echo "=========================================="
