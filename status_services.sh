#!/bin/bash
# AI Project - 서비스 상태 확인 스크립트

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

UP=0
DOWN=0

check_service() {
    local name=$1
    local port=$2
    if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
        echo -e "  ${GREEN}[UP]${NC}   ${name} :${port}"
        UP=$((UP + 1))
    else
        echo -e "  ${RED}[DOWN]${NC} ${name} :${port}"
        DOWN=$((DOWN + 1))
    fi
}

echo "=========================================="
echo " AI Project Services Status"
echo "=========================================="
echo ""
echo "[Backend Services]"
echo "------------------------------------------"
check_service "dataset_gen       " 4001
check_service "deepfake          " 4002
check_service "a3de              " 4004
check_service "carelink          " 4005
check_service "cluster           " 4006
check_service "consulting        " 4007
check_service "factory           " 4008
check_service "labor             " 4009
check_service "langgraph         " 4010
check_service "multimodals       " 4011
check_service "aialbm            " 4012
check_service "enterprise        " 4013
check_service "panda             " 4014
check_service "cluster_master    " 8200

echo ""
echo "[Frontend Services]"
echo "------------------------------------------"
check_service "truthlens         " 8001
check_service "webpage_ainex     " 8002
check_service "ainex_home        " 3001
check_service "cluster_master_web" 3002
check_service "aialbm_web        " 3003
check_service "carelink_web      " 3004
check_service "ai_homepage       " 3005
check_service "carelink_frontend " 5005
check_service "langgraph_frontend" 5010
check_service "enterprise_frontend" 5013
check_service "unified_portal    " 5015
check_service "a3de_frontend     " 5004

echo ""
echo "[API Gateway]"
echo "------------------------------------------"
check_service "api_gateway       " 8080

echo ""
echo "=========================================="
TOTAL=$((UP + DOWN))
echo -e " Summary: ${GREEN}${UP}${NC} up / ${RED}${DOWN}${NC} down / ${TOTAL} total"
echo "=========================================="

# Gateway health check
echo ""
echo "[Gateway Health Check]"
echo "------------------------------------------"
HEALTH=$(curl -s --max-time 10 http://localhost:8080/health 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$HEALTH" ]; then
    eval "$(echo "$HEALTH" | python3 -c "
import sys, json
d = json.load(sys.stdin)
healthy = 0
total = 0
unhealthy = []
for section in ['backend', 'frontend']:
    services = d.get(section, {})
    for name, info in services.items():
        total += 1
        if info.get('status') == 'healthy':
            healthy += 1
        else:
            unhealthy.append(f'{name}: {info.get(\"status\", \"unknown\")}')
print(f'GW_HEALTHY={healthy}')
print(f'GW_TOTAL={total}')
if unhealthy:
    print('GW_UNHEALTHY=\"' + '\\n'.join(unhealthy) + '\"')
else:
    print('GW_UNHEALTHY=\"\"')
" 2>/dev/null)"
    echo -e "  Healthy: ${GREEN}${GW_HEALTHY}${NC} / ${GW_TOTAL}"
    if [ -n "$GW_UNHEALTHY" ]; then
        echo ""
        echo "  Unhealthy services:"
        echo "    $GW_UNHEALTHY"
    fi
else
    echo -e "  ${RED}Gateway not responding${NC}"
    echo "  Try: curl http://localhost:8080/health"
fi
echo ""
