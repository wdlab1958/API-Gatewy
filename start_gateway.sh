#!/bin/bash
#
# AI Project API Gateway Starter
# ================================
# Starts the API Gateway on port 8080
#
# Usage: ./start_gateway.sh
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/api_gateway.log"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           AI Project API Gateway v2.0.0                   ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if gateway is already running
if pgrep -f "api_gateway_v2.py" > /dev/null 2>&1; then
    echo "[WARNING] API Gateway is already running!"
    echo "To restart, first run: pkill -f api_gateway_v2.py"
    exit 1
fi

# Check dependencies
echo "[1/3] Checking dependencies..."
python3 -c "import fastapi, httpx, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[INFO] Installing required packages..."
    pip3 install --user fastapi httpx uvicorn[standard] --quiet
fi

# Start the gateway
echo "[2/3] Starting API Gateway..."
cd "$SCRIPT_DIR"
nohup python3 api_gateway_v2.py > "$LOG_FILE" 2>&1 &
GATEWAY_PID=$!
sleep 2

# Verify startup
if ps -p $GATEWAY_PID > /dev/null 2>&1; then
    echo "[3/3] API Gateway started successfully!"
    echo ""
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│  Dashboard:     http://localhost:8080                   │"
    echo "│  Health Check:  http://localhost:8080/health            │"
    echo "│  OpenAPI Docs:  http://localhost:8080/swagger           │"
    echo "│  API Reference: http://localhost:8080/redoc             │"
    echo "│  Log File:      $LOG_FILE                  │"
    echo "│  PID:           $GATEWAY_PID                                     │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo ""
    echo "To stop: pkill -f api_gateway_v2.py"
else
    echo "[ERROR] Failed to start API Gateway!"
    echo "Check log file: $LOG_FILE"
    tail -20 "$LOG_FILE"
    exit 1
fi
