#!/bin/bash
# AI Project - 모든 서비스 중지 스크립트

echo "=========================================="
echo " AI Project Services Shutdown Script"
echo "=========================================="

echo "Stopping Streamlit servers..."
pkill -f "streamlit run" 2>/dev/null

echo "Stopping all Python HTTP servers..."
pkill -f "python3 -m http.server" 2>/dev/null

echo "Stopping all uvicorn servers..."
pkill -f "uvicorn" 2>/dev/null

echo "Stopping Flask-SocketIO (multimodals)..."
pkill -f "import app as a" 2>/dev/null

echo "Stopping all Node.js development servers..."
pkill -f "npm run dev" 2>/dev/null
pkill -f "next dev" 2>/dev/null
pkill -f "next-server" 2>/dev/null
pkill -f "vite" 2>/dev/null

echo "Stopping AIMES Docker services..."
cd /home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Food 2>/dev/null && docker compose down 2>/dev/null

echo "Stopping API Gateway v2..."
pkill -f "api_gateway_v2" 2>/dev/null

sleep 2

# Verify nothing is left on known ports
PORTS=(4001 4002 4004 4005 4006 4007 4008 4009 4010 4011 4012 4013 4014 4015 4016 8200 8006 18080 8001 8002 8003 8004 3001 3002 3003 3004 3005 3006 3007 3010 5004 5005 5010 5013 5015 8080)
REMAINING=0
for port in "${PORTS[@]}"; do
    if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
        echo "  WARNING: port ${port} still in use"
        REMAINING=$((REMAINING + 1))
    fi
done

echo ""
echo "=========================================="
if [ "$REMAINING" -eq 0 ]; then
    echo " All services stopped successfully!"
else
    echo " ${REMAINING} port(s) still in use (see above)"
fi
echo "=========================================="
