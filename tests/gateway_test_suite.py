#!/usr/bin/env python3
"""API Gateway test suite — E2E, A/B, and Chaos tests, run sequentially.

Targets a running gateway (default http://127.0.0.1:8080). Pure-synchronous
httpx + threads (the local asyncio/uvloop C stack is unstable in this env, so we
avoid async here). Emits a JSON results file and a human summary.

Usage:
    /usr/bin/python3 tests/gateway_test_suite.py [BASE_URL] [--json OUT]
"""
import sys
import json
import time
import statistics
import concurrent.futures as cf

import httpx

BASE = "http://127.0.0.1:8080"
JSON_OUT = "/tmp/gateway_test_results.json"


def _parse_args(argv):
    global BASE, JSON_OUT
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] == "--json":
            JSON_OUT = argv[i + 1]
            i += 2
            continue
        rest.append(argv[i])
        i += 1
    if rest:
        BASE = rest[0].rstrip("/")


client = httpx.Client(timeout=15.0)
results = {"e2e": [], "ab": {}, "chaos": [], "meta": {}}


def rec(bucket, name, ok, detail=""):
    results[bucket].append({"name": name, "pass": bool(ok), "detail": detail})
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))
    return ok


# ============================================================
# E2E — contract tests against every gateway endpoint
# ============================================================
def run_e2e():
    print("\n=== E2E TESTS ===")

    # Root dashboard
    r = client.get(f"{BASE}/")
    rec("e2e", "GET / returns 200 HTML",
        r.status_code == 200 and "text/html" in r.headers.get("content-type", "")
        and "API Gateway" in r.text,
        f"status={r.status_code}")

    # /services structure
    r = client.get(f"{BASE}/services")
    j = r.json()
    nb, nf = j.get("total_backend"), j.get("total_frontend")
    rec("e2e", "GET /services lists backend+frontend",
        r.status_code == 200 and nb and nf and "backend_services" in j,
        f"backend={nb} frontend={nf}")
    results["meta"]["total_backend"] = nb
    results["meta"]["total_frontend"] = nf

    # /health aggregate
    r = client.get(f"{BASE}/health")
    j = r.json()
    rec("e2e", "GET /health aggregates all services",
        r.status_code == 200 and "backend" in j and "frontend" in j
        and len(j["backend"]) == nb and len(j["frontend"]) == nf,
        f"checked {len(j.get('backend', {}))}+{len(j.get('frontend', {}))}")

    # health entries carry a real status field
    healthy = sum(1 for v in {**j.get("backend", {}), **j.get("frontend", {})}.values()
                  if v.get("status") == "healthy")
    rec("e2e", "/health entries carry status field",
        all("status" in v for v in j.get("backend", {}).values()),
        f"{healthy} services currently Online")
    results["meta"]["online_services"] = healthy

    # single health — valid backend
    r = client.get(f"{BASE}/health/backend/agentforge")
    rec("e2e", "GET /health/backend/agentforge valid",
        r.status_code == 200 and r.json().get("service") == "agentforge",
        f"status={r.status_code}")

    # single health — invalid name -> 404
    r = client.get(f"{BASE}/health/backend/nonesuch")
    rec("e2e", "GET /health/backend/<bad> -> 404", r.status_code == 404,
        f"status={r.status_code}")

    # single health — invalid type -> 400
    r = client.get(f"{BASE}/health/sideways/agentforge")
    rec("e2e", "GET /health/<badtype>/x -> 400", r.status_code == 400,
        f"status={r.status_code}")

    # OpenAPI surfaces
    for ep, ctype in [("/swagger", "text/html"), ("/redoc", "text/html"),
                      ("/openapi.json", "application/json")]:
        r = client.get(f"{BASE}{ep}")
        rec("e2e", f"GET {ep} -> 200",
            r.status_code == 200 and ctype in r.headers.get("content-type", ""),
            f"status={r.status_code}")

    # docs index + per-service + bad
    r = client.get(f"{BASE}/docs/api")
    rec("e2e", "GET /docs/api index", r.status_code == 200, f"status={r.status_code}")
    r = client.get(f"{BASE}/docs/api/agentforge")
    rec("e2e", "GET /docs/api/agentforge",
        r.status_code == 200 and r.json().get("service") == "agentforge",
        f"status={r.status_code}")
    r = client.get(f"{BASE}/docs/api/nonesuch")
    rec("e2e", "GET /docs/api/<bad> -> 404", r.status_code == 404,
        f"status={r.status_code}")

    # auto-recovery status
    r = client.get(f"{BASE}/auto-recovery/status")
    j = r.json()
    rec("e2e", "GET /auto-recovery/status",
        r.status_code == 200 and "enabled" in j,
        f"enabled={j.get('enabled')}")

    # proxy: unknown service -> 404 with available list
    r = client.get(f"{BASE}/api/nonesuch/health")
    rec("e2e", "GET /api/<unknown>/.. -> 404", r.status_code == 404,
        f"status={r.status_code}")

    # favicon
    r = client.get(f"{BASE}/favicon.ico")
    rec("e2e", "GET /favicon.ico -> 200", r.status_code == 200,
        f"status={r.status_code}")


# ============================================================
# A/B — same logical outcome via two routing implementations
# Arm A: /health/backend/agentforge  (direct health-check code path)
# Arm B: /api/agentforge/api/health  (reverse-proxy passthrough code path)
# Compare latency distribution + success rate over N samples.
# ============================================================
def _bench(path, n=60):
    lat, ok = [], 0
    for _ in range(n):
        t0 = time.perf_counter()
        try:
            r = client.get(f"{BASE}{path}")
            dt = (time.perf_counter() - t0) * 1000
            lat.append(dt)
            if r.status_code == 200:
                ok += 1
        except Exception:
            lat.append((time.perf_counter() - t0) * 1000)
    lat.sort()
    return {
        "samples": n, "success": ok,
        "success_rate": round(ok / n, 3),
        "mean_ms": round(statistics.mean(lat), 2),
        "p50_ms": round(lat[len(lat) // 2], 2),
        "p95_ms": round(lat[min(len(lat) - 1, int(len(lat) * 0.95))], 2),
        "max_ms": round(max(lat), 2),
    }


def run_ab():
    print("\n=== A/B TEST (two routing implementations, same outcome) ===")
    n = 60
    arm_a = _bench("/health/backend/agentforge", n)   # direct health code
    arm_b = _bench("/api/agentforge/api/health", n)   # proxy passthrough code
    results["ab"] = {
        "hypothesis": "Both arms return agentforge health; compare latency & reliability of "
                      "the direct health-check path (A) vs the reverse-proxy path (B).",
        "arm_A_direct_health": arm_a,
        "arm_B_proxy_passthrough": arm_b,
    }
    faster = "A (direct)" if arm_a["mean_ms"] <= arm_b["mean_ms"] else "B (proxy)"
    overhead = round(abs(arm_b["mean_ms"] - arm_a["mean_ms"]), 2)
    results["ab"]["winner_lower_latency"] = faster
    results["ab"]["proxy_overhead_ms"] = round(arm_b["mean_ms"] - arm_a["mean_ms"], 2)
    print(f"  Arm A (direct health):  mean={arm_a['mean_ms']}ms p95={arm_a['p95_ms']}ms "
          f"success={arm_a['success_rate']}")
    print(f"  Arm B (proxy passthru): mean={arm_b['mean_ms']}ms p95={arm_b['p95_ms']}ms "
          f"success={arm_b['success_rate']}")
    print(f"  -> lower latency: {faster}; proxy overhead ~{overhead}ms/req")
    # Treat as pass if both arms are reliable (the experiment ran cleanly).
    rec("e2e", "A/B both arms reachable",
        arm_a["success_rate"] >= 0.9 and arm_b["success_rate"] >= 0.9,
        f"A={arm_a['success_rate']} B={arm_b['success_rate']}")


# ============================================================
# Chaos — fault injection; gateway must degrade gracefully & survive
# ============================================================
def run_chaos():
    print("\n=== CHAOS TESTS ===")

    # 1) Proxy to a registered-but-DOWN backend -> 503 (graceful), not a crash
    #    (pick a backend that is not currently listening)
    down = None
    h = client.get(f"{BASE}/health").json()
    for k, v in h.get("backend", {}).items():
        if v.get("status") != "healthy":
            down = k
            break
    if down:
        r = client.get(f"{BASE}/api/{down}/health")
        rec("chaos", f"proxy to DOWN backend '{down}' -> 503/502/504 (graceful)",
            r.status_code in (502, 503, 504),
            f"status={r.status_code}")
    else:
        rec("chaos", "proxy to DOWN backend", True, "no down backend to test (all Online)")

    # 2) Unknown service path -> 404, gateway unaffected
    r = client.get(f"{BASE}/api/__chaos__/x/y/z")
    rec("chaos", "unknown service path -> 404", r.status_code == 404,
        f"status={r.status_code}")

    # 3) Hostile paths: traversal, long path, weird chars -> handled, no 5xx-from-gateway crash
    hostile = [
        "/api/agentforge/../../etc/passwd",
        "/api/agentforge/" + "A" * 4000,
        "/api/agentforge/%00%01%02",
        "/health/backend/" + "x" * 2000,
    ]
    bad = []
    for p in hostile:
        try:
            r = client.get(f"{BASE}{p}")
            if r.status_code >= 500 and r.status_code not in (502, 503, 504):
                bad.append(f"{p[:40]}->{r.status_code}")
        except Exception as e:
            bad.append(f"{p[:40]}->EXC")
    rec("chaos", "hostile paths handled without gateway 500", not bad,
        "; ".join(bad) if bad else "all handled")

    # 4) Concurrency storm: 120 parallel requests mixing heavy /health + proxy
    paths = ["/health", "/services", "/api/agentforge/api/health",
             "/api/nonesuch/x", "/health/backend/aialbm"] * 24
    errors = 0
    t0 = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=40) as ex:
        futs = [ex.submit(lambda p=p: client.get(f"{BASE}{p}").status_code) for p in paths]
        for f in cf.as_completed(futs):
            try:
                code = f.result()
                # gateway-origin 500 = bad; upstream-driven 404/503 = fine
                if code == 500:
                    errors += 1
            except Exception:
                errors += 1
    dur = round((time.perf_counter() - t0) * 1000, 1)
    rec("chaos", f"120 concurrent reqs, no gateway 500 ({dur}ms)", errors == 0,
        f"{errors} hard errors")

    # 5) Survival: gateway still serves after the storm
    r = client.get(f"{BASE}/services")
    rec("chaos", "gateway alive after chaos", r.status_code == 200,
        f"status={r.status_code}")

    # 6) Malformed method on proxy (OPTIONS) -> not a crash
    r = client.request("OPTIONS", f"{BASE}/api/agentforge/api/health")
    rec("chaos", "OPTIONS on proxy handled", r.status_code < 500 or r.status_code in (502, 503, 504),
        f"status={r.status_code}")


def main():
    _parse_args(sys.argv[1:])
    print(f"Target gateway: {BASE}")
    results["meta"]["base_url"] = BASE
    results["meta"]["started"] = time.strftime("%Y-%m-%d %H:%M:%S")
    t0 = time.perf_counter()

    # sequential: E2E -> A/B -> Chaos
    run_e2e()
    run_ab()
    run_chaos()

    results["meta"]["duration_s"] = round(time.perf_counter() - t0, 2)
    # tallies
    def tally(bucket):
        items = results[bucket]
        p = sum(1 for x in items if x["pass"])
        return p, len(items)
    e_p, e_n = tally("e2e")
    c_p, c_n = tally("chaos")
    results["meta"]["e2e_pass"] = f"{e_p}/{e_n}"
    results["meta"]["chaos_pass"] = f"{c_p}/{c_n}"
    total_pass = e_p + c_p
    total = e_n + c_n
    results["meta"]["total_pass"] = f"{total_pass}/{total}"

    with open(JSON_OUT, "w") as f:
        json.dump(results, f, indent=2)

    print("\n=== SUMMARY ===")
    print(f"  E2E:   {e_p}/{e_n} passed")
    print(f"  Chaos: {c_p}/{c_n} passed")
    print(f"  A/B:   arm A {results['ab']['arm_A_direct_health']['mean_ms']}ms vs "
          f"arm B {results['ab']['arm_B_proxy_passthrough']['mean_ms']}ms "
          f"(proxy overhead {results['ab']['proxy_overhead_ms']}ms)")
    print(f"  Total: {total_pass}/{total} passed in {results['meta']['duration_s']}s")
    print(f"  JSON:  {JSON_OUT}")
    sys.exit(0 if total_pass == total else 1)


if __name__ == "__main__":
    main()
