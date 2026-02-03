#!/usr/bin/env python3
"""
AI Project API Gateway v2.0
=========================
All projects unified API routing gateway with Web UI Dashboard
Port: 8080

Features:
- OpenAPI Documentation
- Health Check Dashboard
- Quick Links
- API Routing
- Backend/Frontend Service Management
- Real-time Status Monitoring

Update: Feb. 01, 2026
Editor: Brian Lee
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
import httpx
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os

# ============================================================
# Service Configuration
# ============================================================

BACKEND_SERVICES = {
    "dataset_gen": {
        "port": 4001,
        "name": "Dataset Generator",
        "description": "Dataset generation utility for ML/AI training",
        "path": "/home/ubuntu-02/ai_project/Dataset_Gen",
        "entry": "main.py"
    },
    "deepfake": {
        "port": 4002,
        "name": "TruthLens (DeepFake Detection)",
        "description": "Deepfake detection and analysis system",
        "path": "/home/ubuntu-02/ai_project/DeepFake-main",
        "entry": "src/main.py"
    },
    "a3_adep": {
        "port": 4003,
        "name": "A3-ADEP Agent Platform",
        "description": "Agent-based AI system with task orchestration",
        "path": "/home/ubuntu-02/ai_project/a3-adep",
        "entry": "backend/main.py"
    },
    "a3de": {
        "port": 4004,
        "name": "A3-ADE Development Environment",
        "description": "A3 Security development environment",
        "path": "/home/ubuntu-02/ai_project/a3de",
        "entry": "backend/main.py"
    },
    "carelink": {
        "port": 4005,
        "name": "AI CareLink Platform",
        "description": "Healthcare/caregiving AI platform",
        "path": "/home/ubuntu-02/ai_project/ai_carelink",
        "entry": "backend/main.py"
    },
    "cluster": {
        "port": 4006,
        "name": "AI Cluster PC",
        "description": "Cluster PC management system",
        "path": "/home/ubuntu-02/ai_project/ai_cluster_pc",
        "entry": "src/server.py"
    },
    "consulting": {
        "port": 4007,
        "name": "AI Consulting Assistant",
        "description": "Security consulting AI assistant",
        "path": "/home/ubuntu-02/ai_project/ai_consulting",
        "entry": "main.py"
    },
    "factory": {
        "port": 4008,
        "name": "AI Factory",
        "description": "AI Factory - Enterprise production system",
        "path": "/home/ubuntu-02/ai_project/ai_factory",
        "entry": "src/api/main.py"
    },
    "labor": {
        "port": 4009,
        "name": "AI Labor Compliance",
        "description": "Labor law compliance AI system",
        "path": "/home/ubuntu-02/ai_project/ai_labor",
        "entry": "backend/main.py"
    },
    "langgraph": {
        "port": 4010,
        "name": "AgentForge (LangGraph)",
        "description": "AI LangGraph platform for agent workflows",
        "path": "/home/ubuntu-02/ai_project/ai_langgraph",
        "entry": "api/main.py"
    },
    "multimodals": {
        "port": 4011,
        "name": "AI Multimodals",
        "description": "Multimodal AI system (audio/video/text)",
        "path": "/home/ubuntu-02/ai_project/ai_multimodals",
        "entry": "web/app.py"
    },
    "aialbm": {
        "port": 4012,
        "name": "AIALBM Memory Platform",
        "description": "AIALB AI platform with memory",
        "path": "/home/ubuntu-02/ai_project/aialbm",
        "entry": "app/main.py"
    },
    "enterprise": {
        "port": 4013,
        "name": "Enterprise Factory",
        "description": "Enterprise local LLM factory",
        "path": "/home/ubuntu-02/ai_project/enterprise_factory",
        "entry": "local-llm-os/backend/src/api/main.py"
    },
    "panda": {
        "port": 4014,
        "name": "Panda Chatbot",
        "description": "Panda chatbot system",
        "path": "/home/ubuntu-02/ai_project/panda_chetbot",
        "entry": "api/main.py"
    },
    "cluster_master": {
        "port": 8200,
        "name": "Cluster Master",
        "description": "Master cluster orchestration system",
        "path": "/home/ubuntu-02/ai_project/Cluster-Master",
        "entry": "src/server.py"
    },
}

FRONTEND_SERVICES = {
    "truthlens": {
        "port": 8001,
        "name": "TruthLens Web",
        "description": "DeepFake detection web interface",
        "path": "/home/ubuntu-02/ai_project/DeepFake-main/webpage_truthlens",
        "type": "Next.js"
    },
    "webpage_ainex": {
        "port": 8002,
        "name": "AiNex Web",
        "description": "AiNex static webpage",
        "path": "/home/ubuntu-02/ai_project/webpage_AiNex",
        "type": "Static"
    },
    "ainex_home": {
        "port": 3001,
        "name": "AiNex Home",
        "description": "AiNex & AgentForge homepage",
        "path": "/home/ubuntu-02/ai_project/AiNex_Home-main",
        "type": "Next.js"
    },
    "cluster_master_web": {
        "port": 3002,
        "name": "Cluster Master Web",
        "description": "Cluster Master webpage",
        "path": "/home/ubuntu-02/ai_project/webpage_ai_cluster_master",
        "type": "Next.js"
    },
    "aialbm_web": {
        "port": 3003,
        "name": "AIALBM Web",
        "description": "AIALBM webpage",
        "path": "/home/ubuntu-02/ai_project/webpage_aialbm",
        "type": "Next.js"
    },
    "carelink_web": {
        "port": 3004,
        "name": "CareLink Web",
        "description": "CareLink webpage",
        "path": "/home/ubuntu-02/ai_project/webpage_carelink",
        "type": "Next.js"
    },
    "ai_homepage": {
        "port": 3005,
        "name": "AI Homepage",
        "description": "AI Project homepage",
        "path": "/home/ubuntu-02/ai_project/ai_homepage",
        "type": "Next.js"
    },
    "carelink_frontend": {
        "port": 5005,
        "name": "AI CareLink UI",
        "description": "AI CareLink frontend application",
        "path": "/home/ubuntu-02/ai_project/ai_carelink/frontend",
        "type": "Next.js"
    },
    "langgraph_frontend": {
        "port": 5010,
        "name": "AgentForge UI",
        "description": "AgentForge frontend application",
        "path": "/home/ubuntu-02/ai_project/ai_langgraph/frontend",
        "type": "React/Vite"
    },
    "enterprise_frontend": {
        "port": 5013,
        "name": "Enterprise Factory UI",
        "description": "Enterprise Factory frontend",
        "path": "/home/ubuntu-02/ai_project/enterprise_factory/local-llm-os/frontend",
        "type": "React/Vite"
    },
    "unified_portal": {
        "port": 5015,
        "name": "Unified Portal",
        "description": "Unified portal frontend",
        "path": "/home/ubuntu-02/ai_project/unified_portal",
        "type": "React/Vite"
    },
    "a3de_frontend": {
        "port": 5004,
        "name": "A3-ADE UI",
        "description": "A3-ADE frontend application",
        "path": "/home/ubuntu-02/ai_project/a3de/frontend",
        "type": "React/Vite"
    },
}

# API Documentation for each service
API_DOCS = {
    "deepfake": {
        "endpoints": [
            {"method": "POST", "path": "/detect", "description": "Analyze media for deepfake detection"},
            {"method": "GET", "path": "/health", "description": "Service health check"},
            {"method": "GET", "path": "/models", "description": "List available detection models"},
        ]
    },
    "carelink": {
        "endpoints": [
            {"method": "POST", "path": "/auth/login", "description": "User authentication"},
            {"method": "GET", "path": "/patients", "description": "Get patient list"},
            {"method": "GET", "path": "/caregivers", "description": "Get caregiver list"},
            {"method": "POST", "path": "/appointments", "description": "Create appointment"},
        ]
    },
    "cluster": {
        "endpoints": [
            {"method": "GET", "path": "/workers", "description": "List worker nodes"},
            {"method": "POST", "path": "/tasks", "description": "Submit new task"},
            {"method": "GET", "path": "/status", "description": "Cluster status"},
            {"method": "DELETE", "path": "/tasks/{id}", "description": "Cancel task"},
        ]
    },
    "langgraph": {
        "endpoints": [
            {"method": "POST", "path": "/chat", "description": "AI chat conversation"},
            {"method": "POST", "path": "/rag/query", "description": "RAG query"},
            {"method": "GET", "path": "/agents", "description": "List available agents"},
            {"method": "POST", "path": "/workflow", "description": "Execute workflow"},
        ]
    },
    "a3de": {
        "endpoints": [
            {"method": "POST", "path": "/projects", "description": "Create new project"},
            {"method": "GET", "path": "/agents", "description": "List agents"},
            {"method": "POST", "path": "/code/generate", "description": "Generate code"},
        ]
    },
    "consulting": {
        "endpoints": [
            {"method": "POST", "path": "/diagnose", "description": "AI maturity diagnosis"},
            {"method": "GET", "path": "/reports", "description": "List reports"},
            {"method": "POST", "path": "/analyze", "description": "Scenario analysis"},
        ]
    },
    "cluster_master": {
        "endpoints": [
            {"method": "GET", "path": "/api/workers", "description": "List all workers"},
            {"method": "POST", "path": "/api/command", "description": "Execute command"},
            {"method": "GET", "path": "/api/status", "description": "System status"},
            {"method": "GET", "path": "/api/scheduler/jobs", "description": "List scheduled jobs"},
        ]
    },
}

# Service Categories for grouped view
SERVICE_CATEGORIES = {
    "AI Platforms": {
        "icon": "cube",
        "services": ["a3_adep", "a3de", "langgraph", "aialbm", "enterprise"]
    },
    "Detection & Analysis": {
        "icon": "shield",
        "services": ["deepfake"]
    },
    "Healthcare": {
        "icon": "heart",
        "services": ["carelink"]
    },
    "Infrastructure": {
        "icon": "server",
        "services": ["cluster", "cluster_master", "factory"]
    },
    "Assistants & Bots": {
        "icon": "message-circle",
        "services": ["consulting", "panda"]
    },
    "Data & ML": {
        "icon": "database",
        "services": ["dataset_gen", "multimodals"]
    },
    "Compliance": {
        "icon": "file-text",
        "services": ["labor"]
    },
}

# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="AI Project API Gateway",
    description="Unified API Gateway for all AI Projects with Web UI Dashboard",
    version="2.0.0",
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Helper Functions
# ============================================================

async def check_service_health(port: int, timeout: float = 2.0) -> dict:
    """Check service health status"""
    endpoints_to_try = ["/health", "/api/health", "/", "/api/"]

    for endpoint in endpoints_to_try:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(f"http://localhost:{port}{endpoint}")
                if response.status_code in [200, 307]:
                    return {
                        "status": "healthy",
                        "response_time": response.elapsed.total_seconds() * 1000,
                        "endpoint": endpoint
                    }
        except:
            continue

    return {"status": "unhealthy", "response_time": None, "endpoint": None}

async def check_all_services() -> dict:
    """Check all backend and frontend services"""
    results = {"backend": {}, "frontend": {}, "timestamp": datetime.now().isoformat()}

    # Check backend services
    backend_tasks = []
    for service_key, service_info in BACKEND_SERVICES.items():
        backend_tasks.append(check_service_health(service_info["port"]))

    backend_results = await asyncio.gather(*backend_tasks)
    for i, (service_key, service_info) in enumerate(BACKEND_SERVICES.items()):
        results["backend"][service_key] = {
            **service_info,
            **backend_results[i]
        }

    # Check frontend services
    frontend_tasks = []
    for service_key, service_info in FRONTEND_SERVICES.items():
        frontend_tasks.append(check_service_health(service_info["port"]))

    frontend_results = await asyncio.gather(*frontend_tasks)
    for i, (service_key, service_info) in enumerate(FRONTEND_SERVICES.items()):
        results["frontend"][service_key] = {
            **service_info,
            **frontend_results[i]
        }

    return results

# ============================================================
# Web UI Dashboard (HTML)
# ============================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ko" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Project API Gateway</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script>
    tailwind.config = {
        darkMode: ['selector', '[data-theme="dark"]'],
        theme: {
            extend: {
                fontFamily: { sans: ['Inter', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] },
            }
        }
    }
    </script>
    <style>
        :root {
            --bg-primary: #0a0a0a;
            --bg-secondary: #111111;
            --bg-tertiary: #171717;
            --border-color: #262626;
            --text-primary: #fafafa;
            --text-secondary: #a1a1aa;
            --text-tertiary: #71717a;
            --accent: #3b82f6;
            --success: #22c55e;
            --danger: #ef4444;
            --warning: #f59e0b;
        }
        [data-theme="light"] {
            --bg-primary: #ffffff;
            --bg-secondary: #f9fafb;
            --bg-tertiary: #f3f4f6;
            --border-color: #e5e7eb;
            --text-primary: #111827;
            --text-secondary: #6b7280;
            --text-tertiary: #9ca3af;
            --accent: #2563eb;
            --success: #16a34a;
            --danger: #dc2626;
            --warning: #d97706;
        }
        * { box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            margin: 0;
        }
        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-primary); }
        ::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-tertiary); }
        /* Card */
        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            transition: border-color 0.2s;
        }
        .card:hover { border-color: var(--text-tertiary); }
        /* Stat card */
        .stat-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .stat-value { font-size: 2rem; font-weight: 700; line-height: 1; }
        .stat-label { font-size: 0.75rem; color: var(--text-tertiary); margin-top: 6px; text-transform: uppercase; letter-spacing: 0.05em; }
        /* Table */
        .tbl { width: 100%; border-collapse: collapse; }
        .tbl th {
            text-align: left;
            padding: 10px 16px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-tertiary);
            border-bottom: 1px solid var(--border-color);
            background: var(--bg-tertiary);
        }
        .tbl td {
            padding: 12px 16px;
            font-size: 0.85rem;
            border-bottom: 1px solid var(--border-color);
            vertical-align: middle;
        }
        .tbl tr:last-child td { border-bottom: none; }
        .tbl tbody tr { transition: background 0.15s; }
        .tbl tbody tr:hover { background: var(--bg-tertiary); }
        /* Response time bar */
        .rt-bar { height: 6px; border-radius: 3px; min-width: 4px; transition: width 0.4s ease; }
        .rt-good { background: var(--success); }
        .rt-mid { background: var(--warning); }
        .rt-bad { background: var(--danger); }
        /* Status dot */
        .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; }
        .dot-healthy { background: var(--success); box-shadow: 0 0 6px var(--success); }
        .dot-unhealthy { background: var(--danger); }
        /* Collapsible */
        .collapsible-content { max-height: 0; overflow: hidden; transition: max-height 0.35s ease; }
        .collapsible-content.open { max-height: 2000px; }
        /* Skeleton */
        .skeleton {
            background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--border-color) 50%, var(--bg-tertiary) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: 6px;
        }
        @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
        /* Quick link */
        .qlink {
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            padding: 20px 16px; border-radius: 12px; text-decoration: none;
            background: var(--bg-secondary); border: 1px solid var(--border-color);
            transition: all 0.2s;
        }
        .qlink:hover { border-color: var(--accent); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(59,130,246,0.15); }
        /* Navbar */
        .navbar {
            position: sticky; top: 0; z-index: 50;
            background: var(--bg-primary);
            border-bottom: 1px solid var(--border-color);
            backdrop-filter: blur(12px);
            padding: 0 24px;
            height: 56px;
            display: flex; align-items: center; justify-content: space-between;
        }
        /* Search */
        .search-box {
            background: var(--bg-tertiary); border: 1px solid var(--border-color);
            border-radius: 8px; padding: 6px 12px; color: var(--text-primary);
            font-size: 0.85rem; outline: none; width: 260px; transition: border-color 0.2s;
            font-family: 'Inter', sans-serif;
        }
        .search-box:focus { border-color: var(--accent); }
        .search-box::placeholder { color: var(--text-tertiary); }
        /* Toggle */
        .theme-toggle {
            background: var(--bg-tertiary); border: 1px solid var(--border-color);
            border-radius: 8px; padding: 6px 10px; cursor: pointer;
            color: var(--text-secondary); font-size: 0.9rem; transition: all 0.2s;
        }
        .theme-toggle:hover { border-color: var(--accent); color: var(--text-primary); }
        /* Section header */
        .section-header {
            display: flex; align-items: center; justify-content: space-between;
            cursor: pointer; padding: 16px 20px; user-select: none;
        }
        .section-header h2 { font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); }
        .section-header .chevron { transition: transform 0.2s; color: var(--text-tertiary); }
        .section-header .chevron.open { transform: rotate(180deg); }
        /* Countdown ring */
        .countdown-ring { cursor: pointer; }
        .countdown-ring:hover .ring-bg { stroke: var(--text-tertiary); }
        /* Uptime ring */
        .uptime-ring-track { stroke: var(--border-color); }
        .uptime-ring-fill { transition: stroke-dashoffset 0.6s ease; }
        /* Footer */
        .footer { text-align: center; padding: 24px; font-size: 0.75rem; color: var(--text-tertiary); border-top: 1px solid var(--border-color); }
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar">
        <div style="display:flex;align-items:center;gap:12px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            <span style="font-weight:600;font-size:0.95rem;">API Gateway</span>
            <span style="font-size:0.7rem;color:var(--text-tertiary);padding:2px 8px;border:1px solid var(--border-color);border-radius:9999px;">v2.0</span>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
            <input type="text" id="search-input" class="search-box" placeholder="Search services...">
            <!-- Countdown ring -->
            <div class="countdown-ring" id="countdown-ring" onclick="refreshNow()" title="Click to refresh now">
                <svg width="32" height="32" viewBox="0 0 36 36">
                    <circle class="ring-bg" cx="18" cy="18" r="15" fill="none" stroke="var(--border-color)" stroke-width="2.5"/>
                    <circle id="countdown-circle" cx="18" cy="18" r="15" fill="none" stroke="var(--accent)" stroke-width="2.5"
                        stroke-dasharray="94.25" stroke-dashoffset="0" stroke-linecap="round"
                        transform="rotate(-90 18 18)"/>
                    <text id="countdown-text" x="18" y="19" text-anchor="middle" dominant-baseline="middle"
                        fill="var(--text-secondary)" font-size="9" font-family="JetBrains Mono">30</text>
                </svg>
            </div>
            <span id="last-check" style="font-size:0.75rem;color:var(--text-tertiary);min-width:60px;"></span>
            <button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()">
                <i class="fas fa-moon" id="theme-icon"></i>
            </button>
        </div>
    </nav>

    <div style="max-width:1200px;margin:0 auto;padding:24px;">
        <!-- Stats Bar -->
        <div id="stats-bar" style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:24px;">
            <div class="stat-card">
                <div class="stat-value" style="color:var(--text-primary);" id="stat-total">--</div>
                <div class="stat-label">Total</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color:var(--accent);" id="stat-backend">--</div>
                <div class="stat-label">Backend</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color:#a78bfa;" id="stat-frontend">--</div>
                <div class="stat-label">Frontend</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color:var(--success);" id="stat-healthy">--</div>
                <div class="stat-label">Healthy</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color:var(--danger);" id="stat-unhealthy">--</div>
                <div class="stat-label">Unhealthy</div>
            </div>
            <div class="stat-card" style="display:flex;flex-direction:column;align-items:center;justify-content:center;">
                <svg width="56" height="56" viewBox="0 0 56 56" id="uptime-svg">
                    <circle class="uptime-ring-track" cx="28" cy="28" r="24" fill="none" stroke-width="4"/>
                    <circle class="uptime-ring-fill" id="uptime-ring" cx="28" cy="28" r="24" fill="none"
                        stroke="var(--success)" stroke-width="4" stroke-dasharray="150.8" stroke-dashoffset="150.8"
                        stroke-linecap="round" transform="rotate(-90 28 28)"/>
                    <text id="uptime-text" x="28" y="28" text-anchor="middle" dominant-baseline="middle"
                        fill="var(--text-primary)" font-size="12" font-weight="600" font-family="JetBrains Mono">--%</text>
                </svg>
                <div class="stat-label" style="margin-top:4px;">Uptime</div>
            </div>
        </div>

        <!-- Quick Links -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px;">
            <a href="/health" class="qlink">
                <i class="fas fa-heart-pulse" style="font-size:1.3rem;color:var(--success);margin-bottom:8px;"></i>
                <span style="font-size:0.85rem;font-weight:500;color:var(--text-primary);">Health</span>
                <span style="font-size:0.7rem;color:var(--text-tertiary);margin-top:2px;">JSON endpoint</span>
            </a>
            <a href="/swagger" class="qlink">
                <i class="fas fa-book-open" style="font-size:1.3rem;color:var(--accent);margin-bottom:8px;"></i>
                <span style="font-size:0.85rem;font-weight:500;color:var(--text-primary);">Swagger</span>
                <span style="font-size:0.7rem;color:var(--text-tertiary);margin-top:2px;">OpenAPI UI</span>
            </a>
            <a href="/services" class="qlink">
                <i class="fas fa-layer-group" style="font-size:1.3rem;color:#a78bfa;margin-bottom:8px;"></i>
                <span style="font-size:0.85rem;font-weight:500;color:var(--text-primary);">Services</span>
                <span style="font-size:0.7rem;color:var(--text-tertiary);margin-top:2px;">All services</span>
            </a>
            <a href="/redoc" class="qlink">
                <i class="fas fa-file-lines" style="font-size:1.3rem;color:var(--warning);margin-bottom:8px;"></i>
                <span style="font-size:0.85rem;font-weight:500;color:var(--text-primary);">ReDoc</span>
                <span style="font-size:0.7rem;color:var(--text-tertiary);margin-top:2px;">API reference</span>
            </a>
        </div>

        <!-- API Routing (collapsible, default collapsed) -->
        <div class="card" style="margin-bottom:24px;">
            <div class="section-header" onclick="toggleSection('routing')">
                <h2><i class="fas fa-route" style="margin-right:8px;"></i>API Routing</h2>
                <i class="fas fa-chevron-down chevron" id="chevron-routing"></i>
            </div>
            <div class="collapsible-content" id="section-routing">
                <div style="padding:0 20px 20px;">
                    <p style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:12px;">All backend services are accessible through the gateway:</p>
                    <code style="display:block;background:var(--bg-tertiary);border:1px solid var(--border-color);border-radius:8px;padding:10px 16px;font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:var(--success);margin-bottom:16px;">
                        http://localhost:8080/api/{service_name}/{endpoint}
                    </code>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                        <div style="background:var(--bg-tertiary);border-radius:8px;padding:10px 14px;">
                            <div style="font-size:0.7rem;color:var(--text-tertiary);margin-bottom:4px;">DeepFake Detection</div>
                            <code style="font-size:0.8rem;color:var(--accent);font-family:'JetBrains Mono',monospace;">GET /api/deepfake/health</code>
                        </div>
                        <div style="background:var(--bg-tertiary);border-radius:8px;padding:10px 14px;">
                            <div style="font-size:0.7rem;color:var(--text-tertiary);margin-bottom:4px;">AI CareLink</div>
                            <code style="font-size:0.8rem;color:var(--accent);font-family:'JetBrains Mono',monospace;">POST /api/carelink/auth/login</code>
                        </div>
                        <div style="background:var(--bg-tertiary);border-radius:8px;padding:10px 14px;">
                            <div style="font-size:0.7rem;color:var(--text-tertiary);margin-bottom:4px;">Cluster Master</div>
                            <code style="font-size:0.8rem;color:var(--accent);font-family:'JetBrains Mono',monospace;">GET /api/cluster_master/api/workers</code>
                        </div>
                        <div style="background:var(--bg-tertiary);border-radius:8px;padding:10px 14px;">
                            <div style="font-size:0.7rem;color:var(--text-tertiary);margin-bottom:4px;">AgentForge</div>
                            <code style="font-size:0.8rem;color:var(--accent);font-family:'JetBrains Mono',monospace;">POST /api/langgraph/chat</code>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Backend Services -->
        <div class="card" style="margin-bottom:24px;">
            <div class="section-header" onclick="toggleSection('backend')">
                <h2><i class="fas fa-server" style="margin-right:8px;"></i>Backend Services <span id="backend-count" style="color:var(--text-tertiary);font-weight:400;"></span></h2>
                <i class="fas fa-chevron-down chevron open" id="chevron-backend"></i>
            </div>
            <div class="collapsible-content open" id="section-backend">
                <div style="overflow-x:auto;">
                    <table class="tbl">
                        <thead>
                            <tr>
                                <th>Service</th>
                                <th>Port</th>
                                <th>Direct URL</th>
                                <th>Gateway</th>
                                <th>Response Time</th>
                                <th style="text-align:center;">Status</th>
                            </tr>
                        </thead>
                        <tbody id="backend-table">
                            <tr><td colspan="6" style="padding:24px;text-align:center;">
                                <div style="display:flex;flex-direction:column;gap:8px;">
                                    <div class="skeleton" style="height:16px;width:80%;margin:0 auto;"></div>
                                    <div class="skeleton" style="height:16px;width:60%;margin:0 auto;"></div>
                                    <div class="skeleton" style="height:16px;width:70%;margin:0 auto;"></div>
                                </div>
                            </td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Frontend Services -->
        <div class="card" style="margin-bottom:24px;">
            <div class="section-header" onclick="toggleSection('frontend')">
                <h2><i class="fas fa-desktop" style="margin-right:8px;"></i>Frontend Applications <span id="frontend-count" style="color:var(--text-tertiary);font-weight:400;"></span></h2>
                <i class="fas fa-chevron-down chevron open" id="chevron-frontend"></i>
            </div>
            <div class="collapsible-content open" id="section-frontend">
                <div style="overflow-x:auto;">
                    <table class="tbl">
                        <thead>
                            <tr>
                                <th>Service</th>
                                <th>Type</th>
                                <th>Port</th>
                                <th>URL</th>
                                <th>Response Time</th>
                                <th style="text-align:center;">Status</th>
                            </tr>
                        </thead>
                        <tbody id="frontend-table">
                            <tr><td colspan="6" style="padding:24px;text-align:center;">
                                <div style="display:flex;flex-direction:column;gap:8px;">
                                    <div class="skeleton" style="height:16px;width:80%;margin:0 auto;"></div>
                                    <div class="skeleton" style="height:16px;width:60%;margin:0 auto;"></div>
                                    <div class="skeleton" style="height:16px;width:70%;margin:0 auto;"></div>
                                </div>
                            </td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            AI Project API Gateway v2.0.0 &middot; Port 8080 &middot; <span id="footer-time"></span>
        </div>
    </div>

    <script>
    // === State ===
    const backendServices = BACKEND_SERVICES_JSON;
    const frontendServices = FRONTEND_SERVICES_JSON;
    const serviceCategories = SERVICE_CATEGORIES_JSON;
    let healthData = null;
    let lastFetchTime = null;
    let countdownValue = 30;
    let countdownInterval = null;
    let searchTerm = '';
    let searchTimeout = null;

    // === Theme ===
    function initTheme() {
        const saved = localStorage.getItem('gw-theme') || 'dark';
        document.documentElement.setAttribute('data-theme', saved);
        updateThemeIcon(saved);
    }
    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('gw-theme', next);
        updateThemeIcon(next);
    }
    function updateThemeIcon(theme) {
        const icon = document.getElementById('theme-icon');
        icon.className = theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
    }

    // === Collapsible sections ===
    function initSections() {
        ['routing', 'backend', 'frontend'].forEach(id => {
            const saved = localStorage.getItem('gw-section-' + id);
            const el = document.getElementById('section-' + id);
            const chevron = document.getElementById('chevron-' + id);
            if (saved === 'open') {
                el.classList.add('open');
                chevron.classList.add('open');
            } else if (saved === 'closed') {
                el.classList.remove('open');
                chevron.classList.remove('open');
            }
            // defaults: routing=closed, backend/frontend=open (already set in HTML)
        });
    }
    function toggleSection(id) {
        const el = document.getElementById('section-' + id);
        const chevron = document.getElementById('chevron-' + id);
        const isOpen = el.classList.contains('open');
        el.classList.toggle('open');
        chevron.classList.toggle('open');
        localStorage.setItem('gw-section-' + id, isOpen ? 'closed' : 'open');
    }

    // === Search ===
    document.getElementById('search-input').addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchTerm = e.target.value.toLowerCase().trim();
            renderTables();
        }, 150);
    });

    // === Countdown ===
    function startCountdown() {
        countdownValue = 30;
        if (countdownInterval) clearInterval(countdownInterval);
        countdownInterval = setInterval(() => {
            countdownValue--;
            updateCountdownUI();
            if (countdownValue <= 0) {
                fetchHealth();
            }
        }, 1000);
    }
    function updateCountdownUI() {
        const circle = document.getElementById('countdown-circle');
        const text = document.getElementById('countdown-text');
        const circumference = 94.25;
        const offset = circumference * (1 - countdownValue / 30);
        circle.setAttribute('stroke-dashoffset', offset);
        text.textContent = countdownValue;
    }
    function refreshNow() {
        fetchHealth();
    }

    // === Last check time ===
    function updateLastCheck() {
        if (!lastFetchTime) return;
        const diff = Math.floor((Date.now() - lastFetchTime) / 1000);
        const el = document.getElementById('last-check');
        if (diff < 60) el.textContent = diff + 's ago';
        else el.textContent = Math.floor(diff / 60) + 'm ago';
    }
    setInterval(updateLastCheck, 1000);

    // === Response time helpers ===
    function rtClass(ms) {
        if (ms === null || ms === undefined) return '';
        if (ms < 50) return 'rt-good';
        if (ms < 150) return 'rt-mid';
        return 'rt-bad';
    }
    function rtWidth(ms) {
        if (ms === null || ms === undefined) return 0;
        return Math.min(100, Math.max(4, (ms / 300) * 100));
    }
    function rtLabel(ms) {
        if (ms === null || ms === undefined) return '--';
        return ms.toFixed(0) + 'ms';
    }

    // === Fetch health ===
    async function fetchHealth() {
        try {
            const res = await fetch('/health');
            healthData = await res.json();
            lastFetchTime = Date.now();
            countdownValue = 30;
            startCountdown();
            renderStats();
            renderTables();
        } catch (err) {
            console.error('Health fetch failed:', err);
            countdownValue = 30;
            startCountdown();
        }
    }

    // === Filter helper ===
    function matchesSearch(service, key) {
        if (!searchTerm) return true;
        const name = (service.name || '').toLowerCase();
        const desc = (service.description || '').toLowerCase();
        const port = String(service.port || '');
        const type = (service.type || '').toLowerCase();
        const k = key.toLowerCase();
        return name.includes(searchTerm) || desc.includes(searchTerm) || port.includes(searchTerm) || type.includes(searchTerm) || k.includes(searchTerm);
    }

    // === Render stats ===
    function renderStats() {
        if (!healthData) return;
        const be = Object.keys(healthData.backend || {}).length;
        const fe = Object.keys(healthData.frontend || {}).length;
        let healthy = 0, total = be + fe;
        Object.values(healthData.backend || {}).forEach(s => { if (s.status === 'healthy') healthy++; });
        Object.values(healthData.frontend || {}).forEach(s => { if (s.status === 'healthy') healthy++; });
        const unhealthy = total - healthy;
        const uptime = total > 0 ? Math.round((healthy / total) * 100) : 0;

        document.getElementById('stat-total').textContent = total;
        document.getElementById('stat-backend').textContent = be;
        document.getElementById('stat-frontend').textContent = fe;
        document.getElementById('stat-healthy').textContent = healthy;
        document.getElementById('stat-unhealthy').textContent = unhealthy;

        // Uptime ring
        const circumference = 150.8;
        const offset = circumference * (1 - uptime / 100);
        const ring = document.getElementById('uptime-ring');
        ring.setAttribute('stroke-dashoffset', offset);
        if (uptime >= 80) ring.setAttribute('stroke', 'var(--success)');
        else if (uptime >= 50) ring.setAttribute('stroke', 'var(--warning)');
        else ring.setAttribute('stroke', 'var(--danger)');
        document.getElementById('uptime-text').textContent = uptime + '%';

        document.getElementById('footer-time').textContent = new Date().toLocaleString('ko-KR');
    }

    // === Render tables ===
    function renderTables() {
        if (!healthData) return;

        // Backend
        const bt = document.getElementById('backend-table');
        let bRows = '';
        let bCount = 0;
        Object.entries(healthData.backend || {}).forEach(([key, svc]) => {
            if (!matchesSearch(svc, key)) return;
            bCount++;
            const isH = svc.status === 'healthy';
            const rt = svc.response_time;
            bRows += '<tr>' +
                '<td><div style="font-weight:500;">' + esc(svc.name) + '</div><div style="font-size:0.75rem;color:var(--text-tertiary);">' + esc(svc.description || '') + '</div></td>' +
                '<td><span style="font-family:JetBrains Mono,monospace;font-size:0.8rem;color:var(--warning);">' + svc.port + '</span></td>' +
                '<td><a href="http://localhost:' + svc.port + '" target="_blank" style="color:var(--accent);text-decoration:none;font-family:JetBrains Mono,monospace;font-size:0.8rem;">localhost:' + svc.port + '</a></td>' +
                '<td><code style="font-size:0.8rem;color:var(--success);font-family:JetBrains Mono,monospace;">/api/' + key + '/</code></td>' +
                '<td>' + renderRTCell(rt) + '</td>' +
                '<td style="text-align:center;"><span class="dot ' + (isH ? 'dot-healthy' : 'dot-unhealthy') + '"></span> <span style="font-size:0.8rem;color:' + (isH ? 'var(--success)' : 'var(--danger)') + ';">' + (isH ? 'Online' : 'Offline') + '</span></td>' +
            '</tr>';
        });
        bt.innerHTML = bRows || '<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--text-tertiary);">No matching services</td></tr>';
        document.getElementById('backend-count').textContent = '(' + bCount + ')';

        // Frontend
        const ft = document.getElementById('frontend-table');
        let fRows = '';
        let fCount = 0;
        Object.entries(healthData.frontend || {}).forEach(([key, svc]) => {
            if (!matchesSearch(svc, key)) return;
            fCount++;
            const isH = svc.status === 'healthy';
            const rt = svc.response_time;
            fRows += '<tr>' +
                '<td><div style="font-weight:500;">' + esc(svc.name) + '</div><div style="font-size:0.75rem;color:var(--text-tertiary);">' + esc(svc.description || '') + '</div></td>' +
                '<td><span style="font-size:0.75rem;padding:2px 8px;border-radius:9999px;background:var(--bg-tertiary);border:1px solid var(--border-color);">' + esc(svc.type || 'Web') + '</span></td>' +
                '<td><span style="font-family:JetBrains Mono,monospace;font-size:0.8rem;color:var(--warning);">' + svc.port + '</span></td>' +
                '<td><a href="http://localhost:' + svc.port + '" target="_blank" style="color:var(--accent);text-decoration:none;font-family:JetBrains Mono,monospace;font-size:0.8rem;">localhost:' + svc.port + '</a></td>' +
                '<td>' + renderRTCell(rt) + '</td>' +
                '<td style="text-align:center;"><span class="dot ' + (isH ? 'dot-healthy' : 'dot-unhealthy') + '"></span> <span style="font-size:0.8rem;color:' + (isH ? 'var(--success)' : 'var(--danger)') + ';">' + (isH ? 'Online' : 'Offline') + '</span></td>' +
            '</tr>';
        });
        ft.innerHTML = fRows || '<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--text-tertiary);">No matching services</td></tr>';
        document.getElementById('frontend-count').textContent = '(' + fCount + ')';
    }

    function renderRTCell(ms) {
        if (ms === null || ms === undefined) {
            return '<span style="font-size:0.75rem;color:var(--text-tertiary);">--</span>';
        }
        return '<div style="display:flex;align-items:center;gap:8px;">' +
            '<div style="flex:1;background:var(--bg-tertiary);border-radius:3px;height:6px;max-width:80px;">' +
                '<div class="rt-bar ' + rtClass(ms) + '" style="width:' + rtWidth(ms) + '%;"></div>' +
            '</div>' +
            '<span style="font-size:0.75rem;font-family:JetBrains Mono,monospace;color:var(--text-secondary);min-width:42px;">' + rtLabel(ms) + '</span>' +
        '</div>';
    }

    function esc(s) {
        const d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    // === Init ===
    initTheme();
    initSections();
    fetchHealth();
    </script>
</body>
</html>
"""

# ============================================================
# API Endpoints
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """API Gateway Dashboard - Web UI"""
    html = DASHBOARD_HTML.replace(
        "BACKEND_SERVICES_JSON",
        json.dumps(BACKEND_SERVICES)
    ).replace(
        "FRONTEND_SERVICES_JSON",
        json.dumps(FRONTEND_SERVICES)
    ).replace(
        "SERVICE_CATEGORIES_JSON",
        json.dumps(SERVICE_CATEGORIES)
    )
    return HTMLResponse(content=html)

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon"""
    favicon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.ico")
    if os.path.isfile(favicon_path):
        return FileResponse(favicon_path, media_type="image/x-icon")
    return Response(status_code=204)

@app.get("/services")
async def list_services():
    """List all registered services"""
    return {
        "backend_services": BACKEND_SERVICES,
        "frontend_services": FRONTEND_SERVICES,
        "total_backend": len(BACKEND_SERVICES),
        "total_frontend": len(FRONTEND_SERVICES)
    }

@app.get("/health")
async def health_check():
    """Check health status of all services"""
    return await check_all_services()

@app.get("/health/{service_type}/{service_name}")
async def health_check_single(service_type: str, service_name: str):
    """Check health status of a specific service"""
    if service_type == "backend":
        if service_name not in BACKEND_SERVICES:
            raise HTTPException(status_code=404, detail=f"Backend service '{service_name}' not found")
        port = BACKEND_SERVICES[service_name]["port"]
    elif service_type == "frontend":
        if service_name not in FRONTEND_SERVICES:
            raise HTTPException(status_code=404, detail=f"Frontend service '{service_name}' not found")
        port = FRONTEND_SERVICES[service_name]["port"]
    else:
        raise HTTPException(status_code=400, detail="Invalid service type. Use 'backend' or 'frontend'")

    result = await check_service_health(port)
    return {
        "service": service_name,
        "type": service_type,
        "port": port,
        **result
    }

@app.get("/docs/api")
async def api_documentation():
    """Get API documentation for all services"""
    return {
        "title": "AI Project API Documentation",
        "version": "2.0.0",
        "base_url": "http://localhost:8080",
        "services": API_DOCS,
        "routing_pattern": "/api/{service_name}/{endpoint}",
        "note": "Detailed OpenAPI documentation available at /swagger or /redoc"
    }

@app.get("/docs/api/{service_name}")
async def service_api_documentation(service_name: str):
    """Get API documentation for a specific service"""
    if service_name not in API_DOCS:
        raise HTTPException(status_code=404, detail=f"API documentation for '{service_name}' not found")

    service_info = BACKEND_SERVICES.get(service_name, {})
    return {
        "service": service_name,
        "name": service_info.get("name", service_name),
        "description": service_info.get("description", ""),
        "port": service_info.get("port"),
        "gateway_base_url": f"/api/{service_name}",
        "direct_url": f"http://localhost:{service_info.get('port', 'unknown')}",
        "endpoints": API_DOCS[service_name]["endpoints"]
    }

@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_request(service: str, path: str, request: Request):
    """Proxy requests to backend services"""
    if service not in BACKEND_SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found. Available services: {list(BACKEND_SERVICES.keys())}")

    port = BACKEND_SERVICES[service]["port"]
    target_url = f"http://localhost:{port}/{path}"

    # Handle query parameters
    if request.query_params:
        target_url += f"?{request.query_params}"

    # Read request body
    body = await request.body()

    # Copy headers (exclude host)
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                content=body,
                headers=headers,
            )

            # Return response
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    return JSONResponse(
                        content=response.json(),
                        status_code=response.status_code,
                        headers={"X-Proxied-From": f"localhost:{port}"}
                    )
                except:
                    pass

            return JSONResponse(
                content={"data": response.text, "status_code": response.status_code},
                status_code=response.status_code,
                headers={"X-Proxied-From": f"localhost:{port}"}
            )

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Service '{service}' (port {port}) is not available. Please ensure the service is running."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"Request to '{service}' timed out"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

# ============================================================
# Main Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║           AI Project API Gateway v2.0.0                   ║
    ║═══════════════════════════════════════════════════════════║
    ║  Dashboard:    http://localhost:8080                      ║
    ║  Health Check: http://localhost:8080/health               ║
    ║  OpenAPI Docs: http://localhost:8080/swagger              ║
    ║  API Docs:     http://localhost:8080/docs/api             ║
    ║  Services:     http://localhost:8080/services             ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=False)
