#!/bin/bash
# AI Project - Essential Services Shutdown Script
# Stops only the 5 essential services (AEGIS + AiNex + API Gateway)

echo "=========================================="
echo " Essential Services Shutdown Script"
echo "=========================================="

echo "Stopping API Gateway v2..."
pkill -f "api_gateway_v2" 2>/dev/null

echo "Stopping AEGIS Backend (uvicorn on port 4015)..."
fuser -k 4015/tcp 2>/dev/null

echo "Stopping AiNex Backend (uvicorn on port 4007)..."
fuser -k 4007/tcp 2>/dev/null

echo "Stopping AEGIS Frontend (Next.js on port 4000)..."
fuser -k 4000/tcp 2>/dev/null

echo "Stopping AiNex Home Frontend (Next.js on port 3001)..."
fuser -k 3001/tcp 2>/dev/null

sleep 2

# Verify
PORTS=(4015 4007 4000 3001 8080)
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
    echo " All essential services stopped successfully!"
else
    echo " ${REMAINING} port(s) still in use (see above)"
fi
echo "=========================================="
