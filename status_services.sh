#!/bin/bash
#
# AI Project API Gateway — Service Status
# =======================================
# Queries the running gateway's /health endpoint and prints a live status table
# for every registered backend & frontend service. Always in sync with the
# registry in api_gateway_v2.py (no hardcoded service list).
#
# Usage: ./status_services.sh [GATEWAY_URL]   (default http://localhost:8080)
#
GW="${1:-http://localhost:8080}"
PYTHON="${GATEWAY_PYTHON:-/usr/bin/python3}"
[ -x "$PYTHON" ] || PYTHON="python3"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         AI Project API Gateway — Service Status            ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo "Gateway: $GW"
echo ""

if ! curl -s -m 3 -o /dev/null "$GW/services"; then
    echo "[ERROR] Gateway not reachable at $GW"
    echo "Start it with: ./start_gateway.sh"
    exit 1
fi

HEALTH_JSON="$(mktemp)"
trap 'rm -f "$HEALTH_JSON"' EXIT
curl -s -m 40 "$GW/health" -o "$HEALTH_JSON"
HEALTH_JSON="$HEALTH_JSON" "$PYTHON" - <<'PY'
import os, json
d = json.load(open(os.environ["HEALTH_JSON"]))
def section(title, items):
    print(f"\n=== {title} ({len(items)}) ===")
    print(f"  {'SERVICE':28} {'PORT':>6}  {'STATUS':9} {'RT(ms)':>8}  ENDPOINT")
    online = 0
    for k, v in sorted(items.items()):
        st = v.get("status", "?")
        online += st == "healthy"
        rt = v.get("response_time")
        rt = f"{rt:.1f}" if isinstance(rt, (int, float)) else "-"
        flag = "\033[32mOnline \033[0m" if st == "healthy" else "\033[31mOffline\033[0m"
        print(f"  {k:28} {v.get('port',''):>6}  {flag}  {rt:>8}  {v.get('endpoint') or '-'}")
    return online, len(items)
bo, bn = section("Backend Services", d.get("backend", {}))
fo, fn = section("Frontend Services", d.get("frontend", {}))
print(f"\nTotal: {bo+fo}/{bn+fn} Online  (Backend {bo}/{bn}, Frontend {fo}/{fn}, Gateway 1/1)")
PY
