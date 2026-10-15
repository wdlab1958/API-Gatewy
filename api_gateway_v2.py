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
- Auto-Recovery: Automatic restart of services that go Offline

Update: Mar. 07, 2026
Editor: Brian Lee
"""

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, Response
import httpx
import asyncio
from datetime import datetime
import json
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("api-gateway")

GATEWAY_HOST = os.environ.get("GATEWAY_HOST", "localhost")

# Bind host: default to loopback only. Override with GATEWAY_BIND_HOST=0.0.0.0 for LAN exposure.
GATEWAY_BIND_HOST = os.environ.get("GATEWAY_BIND_HOST", "127.0.0.1")

# CORS: explicit localhost allow-list by default; override with comma-separated GATEWAY_CORS_ORIGINS.
_default_cors_origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
GATEWAY_CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get("GATEWAY_CORS_ORIGINS", ",".join(_default_cors_origins)).split(",")
    if o.strip()
]

# API key for proxy/management endpoints. If unset/empty, auth is disabled (back-compat).
GATEWAY_API_KEY = os.environ.get("GATEWAY_API_KEY", "")


async def require_api_key(x_api_key: str = Header(default="")):
    """Env-driven API-key dependency. No-op when GATEWAY_API_KEY is unset (back-compat)."""
    if not GATEWAY_API_KEY:
        return
    if x_api_key != GATEWAY_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

# ============================================================
# Service Configuration
# ============================================================

BACKEND_SERVICES = {
    "notebooklm": {
        "port": 8013,
        "name": "Design NotebookLM (Server)",
        "description": "Notebook-style design ideation API server",
        "path": "/home/ubuntu-02/ai_project/02_Design_NotebookLM",
        "entry": "server/index.mjs",
        "scheme": "http",
        "health": "/api/health"
    },
    "fileforge": {
        "port": 8090,
        "name": "FileForge Backend",
        "description": "File processing & forge backend (FastAPI)",
        "path": "/home/ubuntu-02/ai_project/03_FileForge/backend",
        "entry": "main.py",
        "scheme": "http",
        "health": "/api/health"
    },
    "fileforge_py": {
        "port": 8091,
        "name": "FileForge-Python Backend",
        "description": "FileForge Python edition (FastAPI+NiceGUI). Native port 8090.",
        "path": "/home/ubuntu-02/ai_project/03_FileForge-Python/backend",
        "entry": "main.py",
        "scheme": "http",
        "health": "/health"
    },
    "autoflow": {
        "port": 8085,
        "name": "AutoFlow Backend",
        "description": "vLLM OpenClaw automation backend (FastAPI)",
        "path": "/home/ubuntu-02/ai_project/04_AutoFlow/vllm-openclaw-webapp/backend",
        "entry": "main.py",
        "scheme": "http",
        "health": "/api/health"
    },
    "wdlab_cli": {
        "port": 8877,
        "name": "WDLab CLI Backend",
        "description": "WDLab CLI web backend (FastAPI)",
        "path": "/home/ubuntu-02/ai_project/06_wdlab-CLI/backend",
        "entry": "main.py",
        "scheme": "http",
        "health": "/monitoring/health"
    },
    "expert100k": {
        "port": 8001,
        "name": "100K-Expert",
        "description": "100K multi-agent expert system (FastAPI)",
        "path": "/home/ubuntu-02/ai_project/100K-Expert",
        "entry": "main.py",
        "scheme": "http",
        "health": "/health"
    },
    "aegis": {
        "port": 4015,
        "name": "AEGIS API",
        "description": "AEGIS platform backend API (FastAPI)",
        "path": "/home/ubuntu-02/ai_project/AEGIS/apps/api",
        "entry": "main.py",
        "scheme": "http",
        "health": "/api/v1/health"
    },
    "aialbm": {
        "port": 8000,
        "name": "AIALBM Memory Platform",
        "description": "AIALB AI platform with memory (FastAPI)",
        "path": "/home/ubuntu-02/ai_project/AIALBM/app",
        "entry": "main.py",
        "scheme": "http",
        "health": "/health"
    },
    "agriprocess": {
        "port": 28080,
        "name": "AIMES AgriProcess Gateway",
        "description": "Agricultural process MES API gateway (Express)",
        "path": "/home/ubuntu-02/ai_project/AIMES-AgriProcess/services/api-gateway",
        "entry": "src/index.js",
        "scheme": "http",
        "health": "/health"
    },
    "argus": {
        "port": 8002,
        "name": "ARGUS Backend",
        "description": "ARGUS monitoring/analysis backend (FastAPI). Native port 8000.",
        "path": "/home/ubuntu-02/ai_project/ARGUS/backend",
        "entry": "main.py",
        "scheme": "http",
        "health": "/health"
    },
    "agentforge": {
        "port": 8003,
        "name": "AgentForge (LangGraph)",
        "description": "LangGraph agent workflow platform (FastAPI)",
        "path": "/home/ubuntu-02/ai_project/AgentForge/api",
        "entry": "main.py",
        "scheme": "http",
        "health": "/api/health"
    },
    "carelink": {
        "port": 8004,
        "name": "AI CareLink Backend",
        "description": "Healthcare/caregiving AI backend (FastAPI). Native port 8000.",
        "path": "/home/ubuntu-02/ai_project/AiCarelink/backend",
        "entry": "app/main.py",
        "scheme": "http",
        "health": "/health"
    },
    "ainex": {
        "port": 8005,
        "name": "AiNex Consulting",
        "description": "Multi-agent AI consulting assistant (FastAPI). Native port 8001.",
        "path": "/home/ubuntu-02/ai_project/AiNex",
        "entry": "main.py",
        "scheme": "http",
        "health": "/health"
    },
    "janggi": {
        "port": 8007,
        "name": "JangGi Backend",
        "description": "JangGi platform backend (FastAPI)",
        "path": "/home/ubuntu-02/ai_project/JangGi/backend",
        "entry": "main.py",
        "scheme": "http",
        "health": "/health"
    },
    "nexusai": {
        "port": 8008,
        "name": "NexusAI API",
        "description": "NexusAI platform backend API (FastAPI). Native port 8000.",
        "path": "/home/ubuntu-02/ai_project/NexusAI/apps/api",
        "entry": "main.py",
        "scheme": "http",
        "health": "/health"
    },
    "patentforge": {
        "port": 9700,
        "name": "PatentForge API",
        "description": "Patent drafting/analysis API (FastAPI)",
        "path": "/home/ubuntu-02/ai_project/PatentForge",
        "entry": "scripts/serve_api.py",
        "scheme": "http",
        "health": "/health"
    },
    "crawling": {
        "port": 3014,
        "name": "Project Crawling Server",
        "description": "Web crawling orchestration server (Express)",
        "path": "/home/ubuntu-02/ai_project/Project_Crawling/server",
        "entry": "index.ts",
        "scheme": "http",
        "health": "/api/health"
    },
    "selfsec": {
        "port": 8019,
        "name": "Self Security Consulting API",
        "description": "Self security consulting platform API (FastAPI). Native port 8080.",
        "path": "/home/ubuntu-02/ai_project/Self_Security_Consulting/platform",
        "entry": "main.py",
        "scheme": "http",
        "health": "/health"
    },
    "alphaforge": {
        "port": 8021,
        "name": "WDLAB AlphaForge Backend",
        "description": "Quant/alpha research backend (FastAPI). Native port 8080.",
        "path": "/home/ubuntu-02/ai_project/WDLAB-AlphaForge/src/alphaforge/backend",
        "entry": "main.py",
        "scheme": "http",
        "health": "/health"
    },
    "llmops": {
        "port": 18080,
        "name": "WDLAB LLMOps Backend",
        "description": "LLMOps observability/ops backend (FastAPI)",
        "path": "/home/ubuntu-02/ai_project/WDLAB-LLMOps/apps/backend",
        "entry": "main.py",
        "scheme": "http",
        "health": "/healthz"
    },
    "pokerface": {
        "port": 8012,
        "name": "PokerFace Backend",
        "description": "PokerFace game/analysis backend (FastAPI). Native port 8001.",
        "path": "/home/ubuntu-02/ai_project/PokerFace/backend",
        "entry": "app.py",
        "scheme": "http",
        "health": "/api/system/health"
    },
    "truthlens": {
        "port": 7000,
        "name": "TruthLens Gateway",
        "description": "DeepFake detection gateway (NestJS)",
        "path": "/home/ubuntu-02/ai_project/TruthLens/services/gateway",
        "entry": "src/main.ts",
        "scheme": "http",
        "health": "/api/v1/usage/stats"
    },
    "jangforge": {
        "port": 8014,
        "name": "WDLAB JangForge",
        "description": "Fermentation reasoning engine (FastAPI/LangGraph)",
        "path": "/home/ubuntu-02/ai_project/WDLAB-JangForge/jangforge-core/jangforge",
        "entry": "main.py",
        "scheme": "http",
        "health": "/health"
    },
    "ascm": {
        "port": 8006,
        "name": "ASCM Integration Gateway",
        "description": "SaaS subscription mgmt integration gateway (FastAPI)",
        "path": "/home/ubuntu-02/ai_project/ASCM/services/integration",
        "entry": "main.py",
        "scheme": "http",
        "health": "/health"
    },
    "pi5_edge": {
        "port": 18899,
        "name": "Pi5 Edge Device Gateway",
        "description": "Raspberry Pi5 edge device gateway (FastAPI)",
        "path": "/home/ubuntu-02/ai_project/Pi5-Edge-Device/pi5-gateway",
        "entry": "src/main.py",
        "scheme": "http",
        "health": "/health"
    },
    "pi5_aegis": {
        "port": 8088,
        "name": "Pi5 AEGIS Gateway",
        "description": "Raspberry Pi5 AEGIS edge gateway (FastAPI)",
        "path": "/home/ubuntu-02/ai_project/Pi5-AEGIS/gateway",
        "entry": "server.py",
        "scheme": "http",
        "health": "/health"
    },
}

FRONTEND_SERVICES = {
    "notebooklm_web": {
        "port": 3017,
        "name": "Design NotebookLM Web",
        "description": "Notebook design web UI (Vite/React)",
        "path": "/home/ubuntu-02/ai_project/02_Design_NotebookLM/app",
        "type": "Vite",
        "scheme": "http"
    },
    "fileforge_web": {
        "port": 5185,
        "name": "FileForge Web",
        "description": "FileForge frontend (Vite/React)",
        "path": "/home/ubuntu-02/ai_project/03_FileForge/frontend",
        "type": "Vite",
        "scheme": "http"
    },
    "autoflow_web": {
        "port": 5174,
        "name": "AutoFlow Web",
        "description": "AutoFlow frontend (Vite/React)",
        "path": "/home/ubuntu-02/ai_project/04_AutoFlow/vllm-openclaw-webapp/frontend",
        "type": "Vite",
        "scheme": "http"
    },
    "wdlab_cli_web": {
        "port": 5188,
        "name": "WDLab CLI Web",
        "description": "WDLab CLI frontend (Vite/React)",
        "path": "/home/ubuntu-02/ai_project/06_wdlab-CLI/frontend",
        "type": "Vite",
        "scheme": "http"
    },
    "aegis_web": {
        "port": 4000,
        "name": "AEGIS Web",
        "description": "AEGIS platform web interface (Next.js)",
        "path": "/home/ubuntu-02/ai_project/AEGIS/apps/web",
        "type": "Next.js",
        "scheme": "http"
    },
    "agriprocess_web": {
        "port": 5273,
        "name": "AIMES AgriProcess Web",
        "description": "Agricultural MES frontend (Vite/React)",
        "path": "/home/ubuntu-02/ai_project/AIMES-AgriProcess/frontend/web",
        "type": "Vite",
        "scheme": "http"
    },
    "argus_web": {
        "port": 3030,
        "name": "ARGUS Web",
        "description": "ARGUS frontend (Vite/React)",
        "path": "/home/ubuntu-02/ai_project/ARGUS/frontend",
        "type": "Vite",
        "scheme": "http"
    },
    "agentforge_web": {
        "port": 5175,
        "name": "AgentForge UI",
        "description": "AgentForge frontend (Vite/React). Native port 5174.",
        "path": "/home/ubuntu-02/ai_project/AgentForge/frontend",
        "type": "Vite",
        "scheme": "http"
    },
    "carelink_web": {
        "port": 3000,
        "name": "AI CareLink UI",
        "description": "CareLink frontend (Next.js)",
        "path": "/home/ubuntu-02/ai_project/AiCarelink/frontend",
        "type": "Next.js",
        "scheme": "http"
    },
    "janggi_web": {
        "port": 3021,
        "name": "JangGi Web",
        "description": "JangGi frontend (Next.js). Native port 3000.",
        "path": "/home/ubuntu-02/ai_project/JangGi/frontend",
        "type": "Next.js",
        "scheme": "http"
    },
    "nexusai_web": {
        "port": 3022,
        "name": "NexusAI Web",
        "description": "NexusAI web interface (Next.js). Native port 3000.",
        "path": "/home/ubuntu-02/ai_project/NexusAI/apps/web",
        "type": "Next.js",
        "scheme": "http"
    },
    "patentforge_web": {
        "port": 3023,
        "name": "PatentForge Web",
        "description": "PatentForge frontend (Next.js). Native port 3000.",
        "path": "/home/ubuntu-02/ai_project/PatentForge/apps/frontend",
        "type": "Next.js",
        "scheme": "http"
    },
    "crawling_web": {
        "port": 3013,
        "name": "Project Crawling Web",
        "description": "Crawling frontend (Vite/React)",
        "path": "/home/ubuntu-02/ai_project/Project_Crawling",
        "type": "Vite",
        "scheme": "http"
    },
    "selfsec_dashboard": {
        "port": 8501,
        "name": "Self Security Dashboard",
        "description": "Self security consulting dashboard (Streamlit)",
        "path": "/home/ubuntu-02/ai_project/Self_Security_Consulting/platform/dashboard",
        "type": "Streamlit",
        "scheme": "http"
    },
    "alphaforge_web": {
        "port": 3024,
        "name": "WDLAB AlphaForge Web",
        "description": "AlphaForge frontend (Next.js). Native port 3000.",
        "path": "/home/ubuntu-02/ai_project/WDLAB-AlphaForge/apps/frontend",
        "type": "Next.js",
        "scheme": "http"
    },
    "llmops_web": {
        "port": 18090,
        "name": "WDLAB LLMOps Web",
        "description": "LLMOps frontend (Vite/React)",
        "path": "/home/ubuntu-02/ai_project/WDLAB-LLMOps/apps/frontend",
        "type": "Vite",
        "scheme": "http"
    },
    "pokerface_web": {
        "port": 5176,
        "name": "PokerFace Web",
        "description": "PokerFace frontend (Vite/React)",
        "path": "/home/ubuntu-02/ai_project/PokerFace/frontend",
        "type": "Vite",
        "scheme": "http"
    },
    "slideeditor": {
        "port": 3025,
        "name": "SlideEditor",
        "description": "Slide editor app with embedded API (Vite/React). Native port 3000.",
        "path": "/home/ubuntu-02/ai_project/SlideEditor",
        "type": "Vite",
        "scheme": "http"
    },
    "truthlens_web": {
        "port": 7001,
        "name": "TruthLens Dashboard",
        "description": "TruthLens detection dashboard (Vite/React)",
        "path": "/home/ubuntu-02/ai_project/TruthLens/services/dashboard",
        "type": "Vite",
        "scheme": "http"
    },
    "ascm_web": {
        "port": 3010,
        "name": "ASCM Admin Dashboard",
        "description": "ASCM administration dashboard (Next.js)",
        "path": "/home/ubuntu-02/ai_project/ASCM/ASCM-main/admin-dashboard",
        "type": "Next.js",
        "scheme": "http"
    },
    "aimes_agricultural_web": {
        "port": 5301,
        "name": "AIMES Agricultural Web",
        "description": "AIMES Agricultural MES frontend. Native 5173.",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Agricultural/frontend/web",
        "type": "Vite",
        "scheme": "http"
    },
    "aimes_automotive_web": {
        "port": 5302,
        "name": "AIMES Automotive Web",
        "description": "AIMES Automotive MES frontend. Native 5174.",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Automotive/frontend/web",
        "type": "Vite",
        "scheme": "http"
    },
    "aimes_battery_web": {
        "port": 5303,
        "name": "AIMES Battery Web",
        "description": "AIMES Battery MES frontend. Native 5175.",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Battery/frontend/web",
        "type": "Vite",
        "scheme": "http"
    },
    "aimes_chemical_web": {
        "port": 5304,
        "name": "AIMES Chemical Web",
        "description": "AIMES Chemical MES frontend. Native 5176.",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Chemical/frontend/web",
        "type": "Vite",
        "scheme": "http"
    },
    "aimes_cosmetics_web": {
        "port": 5305,
        "name": "AIMES Cosmetics Web",
        "description": "AIMES Cosmetics MES frontend. Native 5177.",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Cosmetics/frontend/web",
        "type": "Vite",
        "scheme": "http"
    },
    "aimes_electronics_web": {
        "port": 5306,
        "name": "AIMES Electronics Web",
        "description": "AIMES Electronics MES frontend. Native 5178.",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Electronics/frontend/web",
        "type": "Vite",
        "scheme": "http"
    },
    "aimes_food_web": {
        "port": 5307,
        "name": "AIMES Food Web",
        "description": "AIMES Food MES frontend. Native 5179.",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Food/frontend/web",
        "type": "Vite",
        "scheme": "http"
    },
    "aimes_medical_web": {
        "port": 5308,
        "name": "AIMES Medical Web",
        "description": "AIMES Medical MES frontend. Native 5180.",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Medical/frontend/web",
        "type": "Vite",
        "scheme": "http"
    },
    "aimes_metal_web": {
        "port": 5309,
        "name": "AIMES Metal Web",
        "description": "AIMES Metal MES frontend. Native 5181.",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Metal/frontend/web",
        "type": "Vite",
        "scheme": "http"
    },
    "aimes_pharmaceutical_web": {
        "port": 5310,
        "name": "AIMES Pharmaceutical Web",
        "description": "AIMES Pharmaceutical MES frontend. Native 5182.",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Pharmaceutical/frontend/web",
        "type": "Vite",
        "scheme": "http"
    },
    "aimes_textile_web": {
        "port": 5311,
        "name": "AIMES Textile Web",
        "description": "AIMES Textile MES frontend. Native 5183.",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Textile/frontend/web",
        "type": "Vite",
        "scheme": "http"
    },
    "patentforge_webpage": {
        "port": 8201,
        "name": "PatentForge Homepage",
        "description": "PatentForge marketing webpage (Static)",
        "path": "/home/ubuntu-02/ai_project/PatentForge-Webpage",
        "type": "Static",
        "scheme": "http"
    },
    "alphaforge_webpage": {
        "port": 8202,
        "name": "AlphaForge Homepage",
        "description": "WDLAB AlphaForge marketing webpage (Static)",
        "path": "/home/ubuntu-02/ai_project/WDLAB-AlphaForge_Webpage",
        "type": "Static",
        "scheme": "http"
    },
    "llmops_webpage": {
        "port": 8203,
        "name": "LLMOps Homepage",
        "description": "WDLAB LLMOps marketing webpage (Static)",
        "path": "/home/ubuntu-02/ai_project/WDLAB-LLMOps_Webpage",
        "type": "Static",
        "scheme": "http"
    },
}

API_DOCS = {
    "notebooklm": {
        "name": "Design NotebookLM (Server)",
        "description": "Notebook-style design ideation API server",
        "base_url": "/api/notebooklm",
        "endpoints": [
            {
                "method": "GET",
                "path": "/api/health",
                "description": "Health check"
            }
        ]
    },
    "fileforge": {
        "name": "FileForge Backend",
        "description": "File processing & forge backend (FastAPI)",
        "base_url": "/api/fileforge",
        "endpoints": [
            {
                "method": "GET",
                "path": "/api/health",
                "description": "Health check"
            }
        ]
    },
    "fileforge_py": {
        "name": "FileForge-Python Backend",
        "description": "FileForge Python edition (FastAPI+NiceGUI). Native port 8090.",
        "base_url": "/api/fileforge_py",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "autoflow": {
        "name": "AutoFlow Backend",
        "description": "vLLM OpenClaw automation backend (FastAPI)",
        "base_url": "/api/autoflow",
        "endpoints": [
            {
                "method": "GET",
                "path": "/api/health",
                "description": "Health check"
            }
        ]
    },
    "wdlab_cli": {
        "name": "WDLab CLI Backend",
        "description": "WDLab CLI web backend (FastAPI)",
        "base_url": "/api/wdlab_cli",
        "endpoints": [
            {
                "method": "GET",
                "path": "/monitoring/health",
                "description": "Health check"
            }
        ]
    },
    "expert100k": {
        "name": "100K-Expert",
        "description": "100K multi-agent expert system (FastAPI)",
        "base_url": "/api/expert100k",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "aegis": {
        "name": "AEGIS API",
        "description": "AEGIS platform backend API (FastAPI)",
        "base_url": "/api/aegis",
        "endpoints": [
            {
                "method": "GET",
                "path": "/api/v1/health",
                "description": "Health check"
            }
        ]
    },
    "aialbm": {
        "name": "AIALBM Memory Platform",
        "description": "AIALB AI platform with memory (FastAPI)",
        "base_url": "/api/aialbm",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "agriprocess": {
        "name": "AIMES AgriProcess Gateway",
        "description": "Agricultural process MES API gateway (Express)",
        "base_url": "/api/agriprocess",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "argus": {
        "name": "ARGUS Backend",
        "description": "ARGUS monitoring/analysis backend (FastAPI). Native port 8000.",
        "base_url": "/api/argus",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "agentforge": {
        "name": "AgentForge (LangGraph)",
        "description": "LangGraph agent workflow platform (FastAPI)",
        "base_url": "/api/agentforge",
        "endpoints": [
            {
                "method": "GET",
                "path": "/api/health",
                "description": "Health check"
            }
        ]
    },
    "carelink": {
        "name": "AI CareLink Backend",
        "description": "Healthcare/caregiving AI backend (FastAPI). Native port 8000.",
        "base_url": "/api/carelink",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "ainex": {
        "name": "AiNex Consulting",
        "description": "Multi-agent AI consulting assistant (FastAPI). Native port 8001.",
        "base_url": "/api/ainex",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "janggi": {
        "name": "JangGi Backend",
        "description": "JangGi platform backend (FastAPI)",
        "base_url": "/api/janggi",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "nexusai": {
        "name": "NexusAI API",
        "description": "NexusAI platform backend API (FastAPI). Native port 8000.",
        "base_url": "/api/nexusai",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "patentforge": {
        "name": "PatentForge API",
        "description": "Patent drafting/analysis API (FastAPI)",
        "base_url": "/api/patentforge",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "crawling": {
        "name": "Project Crawling Server",
        "description": "Web crawling orchestration server (Express)",
        "base_url": "/api/crawling",
        "endpoints": [
            {
                "method": "GET",
                "path": "/api/health",
                "description": "Health check"
            }
        ]
    },
    "selfsec": {
        "name": "Self Security Consulting API",
        "description": "Self security consulting platform API (FastAPI). Native port 8080.",
        "base_url": "/api/selfsec",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "alphaforge": {
        "name": "WDLAB AlphaForge Backend",
        "description": "Quant/alpha research backend (FastAPI). Native port 8080.",
        "base_url": "/api/alphaforge",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "llmops": {
        "name": "WDLAB LLMOps Backend",
        "description": "LLMOps observability/ops backend (FastAPI)",
        "base_url": "/api/llmops",
        "endpoints": [
            {
                "method": "GET",
                "path": "/healthz",
                "description": "Health check"
            }
        ]
    },
    "pokerface": {
        "name": "PokerFace Backend",
        "description": "PokerFace game/analysis backend (FastAPI). Native port 8001.",
        "base_url": "/api/pokerface",
        "endpoints": [
            {
                "method": "GET",
                "path": "/api/system/health",
                "description": "Health check"
            }
        ]
    },
    "truthlens": {
        "name": "TruthLens Gateway",
        "description": "DeepFake detection gateway (NestJS)",
        "base_url": "/api/truthlens",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "jangforge": {
        "name": "WDLAB JangForge",
        "description": "Fermentation reasoning engine (FastAPI/LangGraph)",
        "base_url": "/api/jangforge",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "ascm": {
        "name": "ASCM Integration Gateway",
        "description": "SaaS subscription mgmt integration gateway (FastAPI)",
        "base_url": "/api/ascm",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "pi5_edge": {
        "name": "Pi5 Edge Device Gateway",
        "description": "Raspberry Pi5 edge device gateway (FastAPI)",
        "base_url": "/api/pi5_edge",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
    "pi5_aegis": {
        "name": "Pi5 AEGIS Gateway",
        "description": "Raspberry Pi5 AEGIS edge gateway (FastAPI)",
        "base_url": "/api/pi5_aegis",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            }
        ]
    },
}

SERVICE_CATEGORIES = {
    "AI Platforms": {
        "icon": "cube",
        "services": [
            "agentforge",
            "aegis",
            "nexusai",
            "aialbm",
            "expert100k",
            "jangforge"
        ]
    },
    "Documents & Files": {
        "icon": "file-text",
        "services": [
            "fileforge",
            "fileforge_py",
            "notebooklm",
            "slideeditor",
            "patentforge"
        ]
    },
    "Detection & Analysis": {
        "icon": "shield",
        "services": [
            "truthlens"
        ]
    },
    "Healthcare": {
        "icon": "heart",
        "services": [
            "carelink"
        ]
    },
    "Manufacturing (MES)": {
        "icon": "industry",
        "services": [
            "agriprocess",
            "aimes_agricultural_web",
            "aimes_automotive_web",
            "aimes_battery_web",
            "aimes_chemical_web",
            "aimes_cosmetics_web",
            "aimes_electronics_web",
            "aimes_food_web",
            "aimes_medical_web",
            "aimes_metal_web",
            "aimes_pharmaceutical_web",
            "aimes_textile_web"
        ]
    },
    "Automation & Agents": {
        "icon": "settings",
        "services": [
            "autoflow",
            "wdlab_cli",
            "crawling"
        ]
    },
    "Finance / Quant": {
        "icon": "trending-up",
        "services": [
            "alphaforge"
        ]
    },
    "LLMOps": {
        "icon": "activity",
        "services": [
            "llmops"
        ]
    },
    "Security": {
        "icon": "lock",
        "services": [
            "selfsec"
        ]
    },
    "Gaming": {
        "icon": "message-circle",
        "services": [
            "pokerface"
        ]
    },
    "SaaS Management": {
        "icon": "server",
        "services": [
            "ascm"
        ]
    },
    "Assistants": {
        "icon": "message-circle",
        "services": [
            "ainex"
        ]
    },
    "Edge / IoT": {
        "icon": "cpu",
        "services": [
            "pi5_edge",
            "pi5_aegis"
        ]
    },
    "Strategy / Games": {
        "icon": "cube",
        "services": [
            "janggi"
        ]
    },
}

_BASE = "/home/ubuntu-02/ai_project"

SERVICE_STARTUP_COMMANDS = {
    "notebooklm": {
        "workdir": "/home/ubuntu-02/ai_project/02_Design_NotebookLM/server",
        "cmd": "PORT=8013 node index.mjs"
    },
    "fileforge": {
        "workdir": "/home/ubuntu-02/ai_project/03_FileForge/backend",
        "cmd": "python main.py"
    },
    "fileforge_py": {
        "workdir": "/home/ubuntu-02/ai_project/03_FileForge-Python",
        "cmd": "python -m backend.main"
    },
    "autoflow": {
        "workdir": "/home/ubuntu-02/ai_project/04_AutoFlow/vllm-openclaw-webapp/backend",
        "cmd": "uvicorn main:app --port 8085"
    },
    "wdlab_cli": {
        "workdir": "/home/ubuntu-02/ai_project/06_wdlab-CLI/backend",
        "cmd": "python main.py"
    },
    "expert100k": {
        "workdir": "/home/ubuntu-02/ai_project/100K-Expert",
        "cmd": "python main.py"
    },
    "aegis": {
        "workdir": "/home/ubuntu-02/ai_project/AEGIS/apps/api",
        "cmd": "python main.py"
    },
    "aialbm": {
        "workdir": "/home/ubuntu-02/ai_project/AIALBM",
        "cmd": "python -m app.main"
    },
    "agriprocess": {
        "workdir": "/home/ubuntu-02/ai_project/AIMES-AgriProcess/services/api-gateway",
        "cmd": "node src/index.js"
    },
    "argus": {
        "workdir": "/home/ubuntu-02/ai_project/ARGUS/backend",
        "cmd": "uvicorn main:app --port 8002"
    },
    "agentforge": {
        "workdir": "/home/ubuntu-02/ai_project/AgentForge",
        "cmd": "python -m uvicorn api.main:app --port 8003"
    },
    "carelink": {
        "workdir": "/home/ubuntu-02/ai_project/AiCarelink/backend",
        "cmd": "uvicorn app.main:app --port 8004"
    },
    "ainex": {
        "workdir": "/home/ubuntu-02/ai_project/AiNex",
        "cmd": "python main.py"
    },
    "janggi": {
        "workdir": "/home/ubuntu-02/ai_project/JangGi/backend",
        "cmd": "uvicorn backend.main:app --port 8007"
    },
    "nexusai": {
        "workdir": "/home/ubuntu-02/ai_project/NexusAI/apps/api",
        "cmd": "uvicorn main:app --port 8008"
    },
    "patentforge": {
        "workdir": "/home/ubuntu-02/ai_project/PatentForge",
        "cmd": "python scripts/serve_api.py"
    },
    "crawling": {
        "workdir": "/home/ubuntu-02/ai_project/Project_Crawling",
        "cmd": "npm run server"
    },
    "selfsec": {
        "workdir": "/home/ubuntu-02/ai_project/Self_Security_Consulting/platform",
        "cmd": "python main.py serve"
    },
    "alphaforge": {
        "workdir": "/home/ubuntu-02/ai_project/WDLAB-AlphaForge",
        "cmd": "alphaforge-backend"
    },
    "llmops": {
        "workdir": "/home/ubuntu-02/ai_project/WDLAB-LLMOps/apps/backend",
        "cmd": "uvicorn wdlab_backend.main:app --port 18080"
    },
    "pokerface": {
        "workdir": "/home/ubuntu-02/ai_project/PokerFace",
        "cmd": "python main.py"
    },
    "truthlens": {
        "workdir": "/home/ubuntu-02/ai_project/TruthLens/services/gateway",
        "cmd": "node dist/main"
    },
    "jangforge": {
        "workdir": "/home/ubuntu-02/ai_project/WDLAB-JangForge/jangforge-core",
        "cmd": "python -m jangforge.main"
    },
    "ascm": {
        "workdir": "/home/ubuntu-02/ai_project/ASCM",
        "cmd": "python3 run_services.py"
    },
    "pi5_edge": {
        "workdir": "/home/ubuntu-02/ai_project/Pi5-Edge-Device/pi5-gateway",
        "cmd": "python -m src.main"
    },
    "pi5_aegis": {
        "workdir": "/home/ubuntu-02/ai_project/Pi5-AEGIS/gateway",
        "cmd": "python server.py"
    },
}

RECOVERY_CHECK_INTERVAL = 30   # seconds between health checks
RECOVERY_COOLDOWN = 120        # seconds between restart attempts per service
RECOVERY_MAX_RETRIES = 5       # max consecutive restart attempts before pausing

# Auto-recovery is OPT-IN. With ~60 downstream services registered, enabling it
# by default would spawn dozens of dev servers (npm/uvicorn) that mostly fail to
# bind, generating noise and stray processes. Set GATEWAY_AUTO_RECOVERY=1 to arm.
RECOVERY_ENABLED = os.environ.get("GATEWAY_AUTO_RECOVERY", "0") == "1"

_recovery_state = {
    "enabled": RECOVERY_ENABLED,
    "last_check": None,
    "previous_status": {},
    "restart_cooldown": {},
    "restart_counts": {},
    "recovery_log": [],
    "task": None,
    "total_restarts": 0,
}


async def restart_service(service_key: str) -> bool:
    """Restart a single service using its configured startup command."""
    if service_key not in SERVICE_STARTUP_COMMANDS:
        logger.warning("[Auto-Recovery] No startup command configured for '%s'", service_key)
        return False

    cmd_info = SERVICE_STARTUP_COMMANDS[service_key]
    workdir = cmd_info["workdir"]
    cmd = cmd_info["cmd"]

    if not os.path.isdir(workdir):
        logger.error("[Auto-Recovery] Directory not found for '%s': %s", service_key, workdir)
        return False

    try:
        log_file = f"/tmp/{service_key}_recovery.log"
        if cmd_info.get("docker"):
            full_cmd = f"cd '{workdir}' && docker compose down --remove-orphans > /dev/null 2>&1; docker compose up -d > '{log_file}' 2>&1"
        else:
            full_cmd = f"cd '{workdir}' && nohup {cmd} > '{log_file}' 2>&1 &"

        subprocess.Popen(full_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info("[Auto-Recovery] Restart command sent for '%s'", service_key)

        # Verify the service actually came up instead of blindly reporting
        # success: poll its health for a few seconds. A command that dies
        # immediately (missing deps, bad cwd) now correctly returns False so the
        # retry counter is not consumed by a phantom "successful" restart.
        svc = BACKEND_SERVICES.get(service_key) or FRONTEND_SERVICES.get(service_key) or {}
        port = svc.get("port")
        if not port:
            return True  # no port to verify against; assume best-effort success
        for _ in range(6):
            await asyncio.sleep(2)
            probe = await check_service_health(
                port, timeout=2.0,
                base_path=svc.get("basePath", ""),
                scheme=svc.get("scheme", "http"),
                health_path=svc.get("health", ""),
            )
            if probe.get("status") == "healthy":
                logger.info("[Auto-Recovery] '%s' verified Online after restart", service_key)
                return True
        logger.warning("[Auto-Recovery] '%s' did not come Online within timeout", service_key)
        return False
    except Exception as e:
        logger.error("[Auto-Recovery] Failed to restart '%s': %s", service_key, e)
        return False


async def auto_recovery_loop():
    """Background loop: detect Offline transitions and auto-restart services."""
    logger.info("[Auto-Recovery] Monitor started (interval=%ds, cooldown=%ds, max_retries=%d)",
                RECOVERY_CHECK_INTERVAL, RECOVERY_COOLDOWN, RECOVERY_MAX_RETRIES)

    # Initial delay to let services stabilize
    await asyncio.sleep(15)

    # First pass: record baseline status without restarting anything
    try:
        results = await check_all_services()
        for stype in ("backend", "frontend"):
            for skey, sinfo in results.get(stype, {}).items():
                _recovery_state["previous_status"][skey] = sinfo.get("status", "unhealthy")
        _recovery_state["last_check"] = datetime.now().isoformat()
        healthy_count = sum(1 for s in _recovery_state["previous_status"].values() if s == "healthy")
        total_count = len(_recovery_state["previous_status"])
        logger.info("[Auto-Recovery] Baseline recorded: %d/%d services Online", healthy_count, total_count)
    except Exception as e:
        logger.error("[Auto-Recovery] Baseline check failed: %s", e)

    # Main monitoring loop
    while _recovery_state["enabled"]:
        await asyncio.sleep(RECOVERY_CHECK_INTERVAL)
        try:
            results = await check_all_services()
            now = datetime.now()
            _recovery_state["last_check"] = now.isoformat()

            for stype in ("backend", "frontend"):
                for skey, sinfo in results.get(stype, {}).items():
                    current = sinfo.get("status", "unhealthy")
                    prev = _recovery_state["previous_status"].get(skey)
                    sname = sinfo.get("name", skey)

                    if current == "healthy" and prev == "unhealthy":
                        # Service recovered — reset retry counter
                        _recovery_state["restart_counts"][skey] = 0
                        logger.info("[Auto-Recovery] %s recovered -> Online", sname)
                        _recovery_state["recovery_log"].append({
                            "timestamp": now.isoformat(), "service": skey,
                            "name": sname, "event": "recovered",
                        })

                    elif current == "unhealthy" and prev == "healthy":
                        # Online -> Offline transition detected
                        await _attempt_restart(skey, sname, now, "offline_detected")

                    elif current == "unhealthy" and prev == "unhealthy":
                        # Still offline — retry if cooldown passed and retries remain
                        last_restart = _recovery_state["restart_cooldown"].get(skey, 0)
                        if last_restart > 0 and (now.timestamp() - last_restart) >= RECOVERY_COOLDOWN:
                            await _attempt_restart(skey, sname, now, "retry")

                    _recovery_state["previous_status"][skey] = current

            # Trim log to last 200 entries
            if len(_recovery_state["recovery_log"]) > 200:
                _recovery_state["recovery_log"] = _recovery_state["recovery_log"][-200:]

        except Exception as e:
            logger.error("[Auto-Recovery] Check cycle error: %s", e)


async def _attempt_restart(skey: str, sname: str, now: datetime, reason: str):
    """Check cooldown/retry limits and attempt a service restart."""
    # Check cooldown
    last_restart = _recovery_state["restart_cooldown"].get(skey, 0)
    if (now.timestamp() - last_restart) < RECOVERY_COOLDOWN:
        return

    # Check retry limit
    retries = _recovery_state["restart_counts"].get(skey, 0)
    if retries >= RECOVERY_MAX_RETRIES:
        if retries == RECOVERY_MAX_RETRIES:
            logger.warning("[Auto-Recovery] %s hit max retries (%d) — pausing auto-restart",
                           sname, RECOVERY_MAX_RETRIES)
            _recovery_state["restart_counts"][skey] = retries + 1
            _recovery_state["recovery_log"].append({
                "timestamp": now.isoformat(), "service": skey,
                "name": sname, "event": "max_retries_reached",
            })
        return

    event_label = "restart" if reason == "offline_detected" else "retry_restart"
    logger.info("[Auto-Recovery] %s — %s (attempt %d/%d)",
                sname, event_label, retries + 1, RECOVERY_MAX_RETRIES)

    success = await restart_service(skey)

    _recovery_state["restart_cooldown"][skey] = now.timestamp()
    _recovery_state["restart_counts"][skey] = retries + 1
    if success:
        _recovery_state["total_restarts"] += 1

    _recovery_state["recovery_log"].append({
        "timestamp": now.isoformat(), "service": skey, "name": sname,
        "event": event_label, "attempt": retries + 1, "success": success,
    })


# ============================================================
# FastAPI Application
# ============================================================

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan: arm/disarm the auto-recovery monitor."""
    if RECOVERY_ENABLED:
        _recovery_state["task"] = asyncio.create_task(auto_recovery_loop())
        logger.info("[API Gateway] Auto-Recovery monitor started")
    else:
        logger.info("[API Gateway] Auto-Recovery disabled (set GATEWAY_AUTO_RECOVERY=1 to enable)")
    try:
        yield
    finally:
        _recovery_state["enabled"] = False
        if _recovery_state["task"]:
            _recovery_state["task"].cancel()
        logger.info("[API Gateway] Auto-Recovery monitor stopped")


app = FastAPI(
    title="AI Project API Gateway",
    description="Unified API Gateway for all AI Projects with Web UI Dashboard",
    version="2.2.0",
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=GATEWAY_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Helper Functions
# ============================================================

async def check_service_health(port: int, timeout: float = 2.0, base_path: str = "",
                               scheme: str = "http", health_path: str = "") -> dict:
    """Check service health status.

    A response is considered healthy only when the upstream actually answers with
    a non-error status (2xx) or an auth challenge (401/403 — service is up but
    gated). 503 (Service Unavailable) is treated as UNHEALTHY so that a service
    failing its dependencies is not silently reported green (and stays eligible
    for auto-recovery). Redirects are followed rather than counted as healthy.
    """
    # Probe the service's declared health path first, then common fallbacks.
    endpoints_to_try = [health_path] if health_path else []
    endpoints_to_try += ["/health", "/api/health", "/", "/api/"]
    if base_path:
        endpoints_to_try = [base_path, f"{base_path}/health"] + endpoints_to_try
    # De-dup while preserving order
    seen = set()
    endpoints_to_try = [e for e in endpoints_to_try if e and not (e in seen or seen.add(e))]

    for endpoint in endpoints_to_try:
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False, follow_redirects=True) as client:
                response = await client.get(f"{scheme}://localhost:{port}{endpoint}")
                if response.status_code < 400 or response.status_code in (401, 403):
                    return {
                        "status": "healthy",
                        "response_time": response.elapsed.total_seconds() * 1000,
                        "endpoint": endpoint,
                        "http_status": response.status_code,
                    }
        except Exception:
            continue

    return {"status": "unhealthy", "response_time": None, "endpoint": None}

async def check_all_services() -> dict:
    """Check all backend and frontend services"""
    results = {"backend": {}, "frontend": {}, "timestamp": datetime.now().isoformat()}

    # Check backend services
    backend_tasks = []
    for service_key, service_info in BACKEND_SERVICES.items():
        backend_tasks.append(check_service_health(service_info["port"], scheme=service_info.get("scheme", "http"), health_path=service_info.get("health", "")))

    backend_results = await asyncio.gather(*backend_tasks)
    for i, (service_key, service_info) in enumerate(BACKEND_SERVICES.items()):
        results["backend"][service_key] = {
            **service_info,
            **backend_results[i]
        }

    # Check frontend services
    frontend_tasks = []
    for service_key, service_info in FRONTEND_SERVICES.items():
        frontend_tasks.append(check_service_health(service_info["port"], base_path=service_info.get("basePath", ""), scheme=service_info.get("scheme", "http")))

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
        /* N/A badge (F11) */
        .na-badge {
            display: inline-block; font-size: 0.65rem; font-weight: 600;
            padding: 2px 8px; border-radius: 9999px;
            background: var(--bg-tertiary); color: var(--text-tertiary);
            border: 1px solid var(--border-color);
        }
        /* Sort arrows (F1) */
        .sort-arrow { font-size: 0.6rem; margin-left: 4px; color: var(--text-tertiary); }
        .sort-arrow.active { color: var(--accent); }
        .tbl th.sortable { cursor: pointer; user-select: none; }
        .tbl th.sortable:hover { color: var(--text-secondary); }
        /* Filter buttons (F2) */
        .filter-group { display: flex; gap: 2px; background: var(--bg-tertiary); border-radius: 8px; padding: 2px; border: 1px solid var(--border-color); }
        .filter-btn {
            padding: 4px 12px; border: none; border-radius: 6px; font-size: 0.75rem;
            font-weight: 500; cursor: pointer; transition: all 0.2s;
            background: transparent; color: var(--text-tertiary); font-family: 'Inter', sans-serif;
        }
        .filter-btn:hover { color: var(--text-secondary); }
        .filter-btn.active { background: var(--accent); color: #fff; }
        /* Toast (F4) */
        #toast-container {
            position: fixed; bottom: 24px; right: 24px; z-index: 100;
            display: flex; flex-direction: column; gap: 8px; pointer-events: none;
        }
        .toast {
            pointer-events: auto; padding: 12px 20px; border-radius: 10px;
            font-size: 0.85rem; font-weight: 500; color: #fff;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
            animation: toastIn 0.3s ease, toastOut 0.3s ease 4.7s forwards;
            display: flex; align-items: center; gap: 8px;
        }
        .toast-online { background: var(--success); }
        .toast-offline { background: var(--danger); }
        @keyframes toastIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes toastOut { from { opacity: 1; } to { opacity: 0; transform: translateX(100%); } }
        /* Detail panel (F3) */
        .detail-panel {
            background: var(--bg-tertiary); border-left: 3px solid var(--accent);
            padding: 16px 20px; animation: detailIn 0.2s ease;
        }
        .detail-panel .ep-badge {
            display: inline-block; padding: 2px 8px; border-radius: 4px;
            font-size: 0.7rem; font-weight: 600; font-family: 'JetBrains Mono', monospace;
            margin-right: 6px;
        }
        .ep-GET { background: rgba(34,197,94,0.15); color: var(--success); }
        .ep-POST { background: rgba(59,130,246,0.15); color: var(--accent); }
        .ep-PUT { background: rgba(245,158,11,0.15); color: var(--warning); }
        .ep-DELETE { background: rgba(239,68,68,0.15); color: var(--danger); }
        .ep-PATCH { background: rgba(167,139,250,0.15); color: #a78bfa; }
        @keyframes detailIn { from { opacity: 0; max-height: 0; } to { opacity: 1; max-height: 400px; } }
        .tbl tbody tr.clickable-row { cursor: pointer; }
        .tbl tbody tr.row-expanded { background: var(--bg-tertiary); }
        /* Open button */
        .open-btn {
            display: inline-block;
            padding: 4px 12px;
            font-size: 0.75rem;
            font-weight: 500;
            border-radius: 6px;
            background: var(--accent);
            color: #fff;
            text-decoration: none;
            transition: opacity 0.2s;
            font-family: 'Inter', sans-serif;
        }
        .open-btn:hover { opacity: 0.85; }
        /* Error banner (F10) */
        .error-banner {
            background: var(--danger); color: #fff; text-align: center;
            padding: 10px 24px; font-size: 0.85rem; font-weight: 500;
            display: none; align-items: center; justify-content: center; gap: 8px;
            animation: bannerIn 0.3s ease;
        }
        .error-banner.show { display: flex; }
        @keyframes bannerIn { from { opacity: 0; transform: translateY(-100%); } to { opacity: 1; transform: translateY(0); } }
        /* Keyboard shortcuts overlay (F8) */
        .shortcuts-overlay {
            position: fixed; inset: 0; z-index: 200;
            background: rgba(0,0,0,0.6); backdrop-filter: blur(4px);
            display: none; align-items: center; justify-content: center;
        }
        .shortcuts-overlay.show { display: flex; }
        .shortcuts-modal {
            background: var(--bg-secondary); border: 1px solid var(--border-color);
            border-radius: 16px; padding: 32px; max-width: 420px; width: 90%;
            box-shadow: 0 16px 48px rgba(0,0,0,0.3);
        }
        .shortcuts-modal h3 { margin: 0 0 20px; font-size: 1rem; font-weight: 600; }
        .shortcut-row {
            display: flex; justify-content: space-between; align-items: center;
            padding: 8px 0; border-bottom: 1px solid var(--border-color);
        }
        .shortcut-row:last-child { border-bottom: none; }
        .shortcut-key {
            display: inline-block; padding: 2px 10px; border-radius: 6px;
            background: var(--bg-tertiary); border: 1px solid var(--border-color);
            font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 500;
        }
        /* View toggle (F6) */
        .view-toggle {
            background: var(--bg-tertiary); border: 1px solid var(--border-color);
            border-radius: 8px; padding: 6px 10px; cursor: pointer;
            color: var(--text-secondary); font-size: 0.9rem; transition: all 0.2s;
        }
        .view-toggle:hover { border-color: var(--accent); color: var(--text-primary); }
        /* Category group header (F6) */
        .category-header {
            padding: 10px 16px; background: var(--bg-tertiary); border-bottom: 1px solid var(--border-color);
            display: flex; align-items: center; gap: 8px;
        }
        .category-header .cat-icon { color: var(--accent); font-size: 0.85rem; }
        .category-header .cat-name { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); }
        .category-header .cat-count { font-size: 0.7rem; color: var(--text-tertiary); }
        /* Sparkline (F5) */
        .sparkline-wrap { display: flex; align-items: center; gap: 6px; }
        .sparkline-svg { overflow: visible; }
        /* Mobile responsive (F7) */
        @media (max-width: 768px) {
            #stats-bar { grid-template-columns: repeat(3, 1fr) !important; }
            .qlink-grid { grid-template-columns: repeat(2, 1fr) !important; }
            .navbar {
                flex-wrap: wrap; height: auto; padding: 10px 16px; gap: 8px;
            }
            .search-box { width: 160px; }
            .filter-group { display: none; }
            .tbl th:first-child, .tbl td:first-child { position: sticky; left: 0; z-index: 2; background: var(--bg-secondary); }
            .tbl tbody tr:hover td:first-child { background: var(--bg-tertiary); }
        }
        @media (max-width: 480px) {
            #stats-bar { grid-template-columns: repeat(2, 1fr) !important; }
            .search-box { width: 120px; }
            .stat-value { font-size: 1.5rem; }
        }
    </style>
</head>
<body>
    <!-- Error Banner (F10) -->
    <div id="error-banner" class="error-banner">
        <i class="fas fa-exclamation-triangle"></i>
        <span>Failed to fetch health data. Retrying...</span>
    </div>

    <!-- Navbar -->
    <nav class="navbar">
        <div style="display:flex;align-items:center;gap:12px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            <span style="font-weight:600;font-size:0.95rem;">API Gateway</span>
            <span style="font-size:0.7rem;color:var(--text-tertiary);padding:2px 8px;border:1px solid var(--border-color);border-radius:9999px;">v2.0</span>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
            <input type="text" id="search-input" class="search-box" placeholder="Search services... ( / )">
            <!-- Status filter (F2) -->
            <div class="filter-group">
                <button class="filter-btn active" id="filter-all" onclick="setStatusFilter('all')">All</button>
                <button class="filter-btn" id="filter-online" onclick="setStatusFilter('online')">Online</button>
                <button class="filter-btn" id="filter-offline" onclick="setStatusFilter('offline')">Offline</button>
            </div>
            <!-- View toggle (F6) -->
            <button class="view-toggle" id="view-toggle" onclick="toggleViewMode()" title="Toggle grouped view">
                <i class="fas fa-list" id="view-icon"></i>
            </button>
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
            <!-- Keyboard hint (F8) -->
            <button class="theme-toggle" onclick="toggleShortcutsOverlay()" title="Keyboard shortcuts">
                <i class="fas fa-keyboard"></i>
            </button>
        </div>
    </nav>

    <!-- Toast container (F4) -->
    <div id="toast-container"></div>

    <!-- Keyboard shortcuts overlay (F8) -->
    <div id="shortcuts-overlay" class="shortcuts-overlay" onclick="if(event.target===this)toggleShortcutsOverlay()">
        <div class="shortcuts-modal">
            <h3><i class="fas fa-keyboard" style="margin-right:8px;color:var(--accent);"></i>Keyboard Shortcuts</h3>
            <div class="shortcut-row"><span>Focus search</span><span class="shortcut-key">/</span></div>
            <div class="shortcut-row"><span>Refresh data</span><span class="shortcut-key">R</span></div>
            <div class="shortcut-row"><span>Toggle theme</span><span class="shortcut-key">D</span></div>
            <div class="shortcut-row"><span>Show shortcuts</span><span class="shortcut-key">?</span></div>
            <div class="shortcut-row"><span>Close / Clear search</span><span class="shortcut-key">Esc</span></div>
        </div>
    </div>

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
        <div class="qlink-grid" style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:24px;">
            <a href="http://GATEWAY_HOST_PLACEHOLDER:4000/interface" target="_blank" class="qlink">
                <i class="fas fa-shield-halved" style="font-size:1.3rem;color:#10b981;margin-bottom:8px;"></i>
                <span style="font-size:0.85rem;font-weight:500;color:var(--text-primary);">AEGIS</span>
                <span style="font-size:0.7rem;color:var(--text-tertiary);margin-top:2px;">Desktop Interface</span>
            </a>
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
                        http://GATEWAY_HOST_PLACEHOLDER:8080/api/{service_name}/{endpoint}
                    </code>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                        <div style="background:var(--bg-tertiary);border-radius:8px;padding:10px 14px;">
                            <div style="font-size:0.7rem;color:var(--text-tertiary);margin-bottom:4px;">TruthLens (DeepFake)</div>
                            <code style="font-size:0.8rem;color:var(--accent);font-family:'JetBrains Mono',monospace;">GET /api/truthlens/health</code>
                        </div>
                        <div style="background:var(--bg-tertiary);border-radius:8px;padding:10px 14px;">
                            <div style="font-size:0.7rem;color:var(--text-tertiary);margin-bottom:4px;">AI CareLink</div>
                            <code style="font-size:0.8rem;color:var(--accent);font-family:'JetBrains Mono',monospace;">GET /api/carelink/health</code>
                        </div>
                        <div style="background:var(--bg-tertiary);border-radius:8px;padding:10px 14px;">
                            <div style="font-size:0.7rem;color:var(--text-tertiary);margin-bottom:4px;">ASCM</div>
                            <code style="font-size:0.8rem;color:var(--accent);font-family:'JetBrains Mono',monospace;">GET /api/ascm/health</code>
                        </div>
                        <div style="background:var(--bg-tertiary);border-radius:8px;padding:10px 14px;">
                            <div style="font-size:0.7rem;color:var(--text-tertiary);margin-bottom:4px;">AgentForge</div>
                            <code style="font-size:0.8rem;color:var(--accent);font-family:'JetBrains Mono',monospace;">GET /api/agentforge/api/health</code>
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
                    <table class="tbl" id="backend-tbl">
                        <thead>
                            <tr>
                                <th class="sortable" onclick="toggleSort('backend','name')">Service <span class="sort-arrow" id="sort-backend-name"></span></th>
                                <th class="sortable" onclick="toggleSort('backend','port')">Port <span class="sort-arrow" id="sort-backend-port"></span></th>
                                <th>Direct URL</th>
                                <th>Gateway</th>
                                <th class="sortable" onclick="toggleSort('backend','response_time')">Response Time <span class="sort-arrow" id="sort-backend-response_time"></span></th>
                                <th class="sortable" style="text-align:center;" onclick="toggleSort('backend','status')">Status <span class="sort-arrow" id="sort-backend-status"></span></th>
                                <th style="text-align:center;">Action</th>
                            </tr>
                        </thead>
                        <tbody id="backend-table">
                            <tr><td colspan="7" style="padding:24px;text-align:center;">
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
                    <table class="tbl" id="frontend-tbl">
                        <thead>
                            <tr>
                                <th class="sortable" onclick="toggleSort('frontend','name')">Service <span class="sort-arrow" id="sort-frontend-name"></span></th>
                                <th>Type</th>
                                <th class="sortable" onclick="toggleSort('frontend','port')">Port <span class="sort-arrow" id="sort-frontend-port"></span></th>
                                <th>URL</th>
                                <th class="sortable" onclick="toggleSort('frontend','response_time')">Response Time <span class="sort-arrow" id="sort-frontend-response_time"></span></th>
                                <th class="sortable" style="text-align:center;" onclick="toggleSort('frontend','status')">Status <span class="sort-arrow" id="sort-frontend-status"></span></th>
                                <th style="text-align:center;">Action</th>
                            </tr>
                        </thead>
                        <tbody id="frontend-table">
                            <tr><td colspan="7" style="padding:24px;text-align:center;">
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
    const apiDocs = API_DOCS_JSON;
    let healthData = null;
    let lastFetchTime = null;
    let countdownValue = 30;
    let countdownInterval = null;
    let searchTerm = '';
    let searchTimeout = null;
    // F1: Sort
    let sortConfig = { backend: { key: null, dir: 'asc' }, frontend: { key: null, dir: 'asc' } };
    // F2: Status filter
    let statusFilter = 'all';
    // F4: Toast - previous health data
    let prevHealthData = null;
    // F5: Sparkline history
    let rtHistory = {};
    // F6: View mode
    let viewMode = localStorage.getItem('gw-view') || 'flat';
    // F10: Fetch error
    let fetchError = false;
    // F3: Expanded detail row
    let expandedRow = null;

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

    // === F1: Sort functions ===
    function sortServices(entries, tableType) {
        const cfg = sortConfig[tableType];
        if (!cfg || !cfg.key) return entries;
        const k = cfg.key;
        const dir = cfg.dir === 'asc' ? 1 : -1;
        return entries.slice().sort((a, b) => {
            let va = a[1][k], vb = b[1][k];
            if (k === 'name') { va = (va || '').toLowerCase(); vb = (vb || '').toLowerCase(); }
            if (k === 'status') { va = va === 'healthy' ? 1 : 0; vb = vb === 'healthy' ? 1 : 0; }
            if (k === 'response_time') { va = va === null ? 99999 : va; vb = vb === null ? 99999 : vb; }
            if (k === 'port') { va = Number(va) || 0; vb = Number(vb) || 0; }
            if (va < vb) return -1 * dir;
            if (va > vb) return 1 * dir;
            return 0;
        });
    }
    function toggleSort(tableType, columnKey) {
        const cfg = sortConfig[tableType];
        if (cfg.key === columnKey) {
            cfg.dir = cfg.dir === 'asc' ? 'desc' : 'asc';
        } else {
            cfg.key = columnKey;
            cfg.dir = 'asc';
        }
        updateSortArrows();
        renderTables();
    }
    function updateSortArrows() {
        ['backend', 'frontend'].forEach(t => {
            ['name', 'port', 'response_time', 'status'].forEach(k => {
                const el = document.getElementById('sort-' + t + '-' + k);
                if (!el) return;
                const cfg = sortConfig[t];
                if (cfg.key === k) {
                    el.className = 'sort-arrow active';
                    el.textContent = cfg.dir === 'asc' ? ' ▲' : ' ▼';
                } else {
                    el.className = 'sort-arrow';
                    el.textContent = ' ▲▼';
                }
            });
        });
    }

    // === F2: Status filter ===
    function setStatusFilter(value) {
        statusFilter = value;
        document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
        document.getElementById('filter-' + value).classList.add('active');
        renderTables();
    }
    function matchesStatusFilter(svc) {
        if (statusFilter === 'all') return true;
        if (statusFilter === 'online') return svc.status === 'healthy';
        if (statusFilter === 'offline') return svc.status !== 'healthy';
        return true;
    }

    // === F4: Toast notifications ===
    function detectStatusChanges() {
        if (!prevHealthData || !healthData) return;
        ['backend', 'frontend'].forEach(type => {
            const prev = prevHealthData[type] || {};
            const curr = healthData[type] || {};
            Object.keys(curr).forEach(key => {
                const prevStatus = prev[key] ? prev[key].status : null;
                const currStatus = curr[key].status;
                if (prevStatus && prevStatus !== currStatus) {
                    const name = curr[key].name || key;
                    if (currStatus === 'healthy') {
                        showToast(name + ' is now Online', 'online');
                    } else {
                        showToast(name + ' went Offline', 'offline');
                    }
                }
            });
        });
    }
    function showToast(message, type) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        toast.innerHTML = '<i class="fas ' + (type === 'online' ? 'fa-check-circle' : 'fa-times-circle') + '"></i> ' + esc(message);
        container.appendChild(toast);
        setTimeout(() => { toast.remove(); }, 5000);
    }

    // === F5: Sparkline ===
    function updateRtHistory() {
        if (!healthData) return;
        ['backend', 'frontend'].forEach(type => {
            Object.entries(healthData[type] || {}).forEach(([key, svc]) => {
                const hKey = type + ':' + key;
                if (!rtHistory[hKey]) rtHistory[hKey] = [];
                rtHistory[hKey].push(svc.response_time);
                if (rtHistory[hKey].length > 10) rtHistory[hKey].shift();
            });
        });
    }
    function renderSparkline(historyKey) {
        const data = rtHistory[historyKey];
        if (!data || data.length < 2) return '';
        const valid = data.map(v => v === null ? 0 : v);
        const max = Math.max(...valid, 1);
        const w = 60, h = 20;
        const points = valid.map((v, i) => {
            const x = (i / (valid.length - 1)) * w;
            const y = h - (v / max) * h;
            return x.toFixed(1) + ',' + y.toFixed(1);
        }).join(' ');
        return '<svg class="sparkline-svg" width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h + '">' +
            '<polyline points="' + points + '" fill="none" stroke="var(--accent)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>' +
        '</svg>';
    }

    // === F10: Error banner ===
    function showErrorBanner() {
        document.getElementById('error-banner').classList.add('show');
    }
    function hideErrorBanner() {
        document.getElementById('error-banner').classList.remove('show');
    }

    // === F3: Detail panel ===
    function toggleDetail(type, key) {
        const id = type + ':' + key;
        expandedRow = (expandedRow === id) ? null : id;
        renderTables();
    }
    function renderDetailPanel(type, key, svc) {
        const docs = apiDocs[key];
        let html = '<tr class="detail-row"><td colspan="7" style="padding:0;"><div class="detail-panel">';
        html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">';
        // Left: info
        html += '<div>';
        html += '<div style="font-size:0.75rem;color:var(--text-tertiary);margin-bottom:4px;">Service Key</div>';
        html += '<div style="font-family:JetBrains Mono,monospace;font-size:0.85rem;margin-bottom:12px;">' + esc(key) + '</div>';
        if (svc.path) {
            html += '<div style="font-size:0.75rem;color:var(--text-tertiary);margin-bottom:4px;">Path</div>';
            html += '<div style="font-family:JetBrains Mono,monospace;font-size:0.8rem;word-break:break-all;margin-bottom:12px;">' + esc(svc.path) + '</div>';
        }
        if (svc.entry) {
            html += '<div style="font-size:0.75rem;color:var(--text-tertiary);margin-bottom:4px;">Entry File</div>';
            html += '<div style="font-family:JetBrains Mono,monospace;font-size:0.8rem;">' + esc(svc.entry) + '</div>';
        }
        if (svc.type) {
            html += '<div style="font-size:0.75rem;color:var(--text-tertiary);margin-bottom:4px;margin-top:12px;">Framework</div>';
            html += '<div style="font-size:0.85rem;">' + esc(svc.type) + '</div>';
        }
        html += '</div>';
        // Right: API docs
        html += '<div>';
        if (docs && docs.endpoints && docs.endpoints.length > 0) {
            html += '<div style="font-size:0.75rem;color:var(--text-tertiary);margin-bottom:8px;">API Endpoints</div>';
            docs.endpoints.forEach(ep => {
                html += '<div style="margin-bottom:6px;display:flex;align-items:center;gap:6px;">';
                html += '<span class="ep-badge ep-' + ep.method + '">' + ep.method + '</span>';
                html += '<span style="font-family:JetBrains Mono,monospace;font-size:0.8rem;">' + esc(ep.path) + '</span>';
                html += '<span style="font-size:0.75rem;color:var(--text-tertiary);margin-left:4px;">' + esc(ep.description) + '</span>';
                html += '</div>';
            });
        } else {
            html += '<div style="font-size:0.8rem;color:var(--text-tertiary);">No API documentation available</div>';
        }
        html += '</div>';
        html += '</div></div></td></tr>';
        return html;
    }

    // === F6: Grouped view ===
    function toggleViewMode() {
        viewMode = viewMode === 'flat' ? 'grouped' : 'flat';
        localStorage.setItem('gw-view', viewMode);
        updateViewIcon();
        renderTables();
    }
    function updateViewIcon() {
        const icon = document.getElementById('view-icon');
        icon.className = viewMode === 'flat' ? 'fas fa-list' : 'fas fa-layer-group';
    }
    function renderGroupedBackend(entries) {
        let html = '';
        const catEntries = {};
        // Map services to categories
        Object.entries(serviceCategories).forEach(([catName, cat]) => {
            catEntries[catName] = [];
            cat.services.forEach(sKey => {
                const entry = entries.find(e => e[0] === sKey);
                if (entry) catEntries[catName].push(entry);
            });
        });
        // Uncategorized
        const categorized = new Set();
        Object.values(serviceCategories).forEach(cat => cat.services.forEach(s => categorized.add(s)));
        const uncategorized = entries.filter(e => !categorized.has(e[0]));
        if (uncategorized.length > 0) catEntries['Other'] = uncategorized;

        Object.entries(catEntries).forEach(([catName, svcs]) => {
            if (svcs.length === 0) return;
            const cat = serviceCategories[catName];
            const iconMap = { cube: 'fa-cube', shield: 'fa-shield-halved', heart: 'fa-heart', server: 'fa-server', 'message-circle': 'fa-comment', database: 'fa-database', 'file-text': 'fa-file-lines', settings: 'fa-gear', industry: 'fa-industry' };
            const iconClass = cat ? (iconMap[cat.icon] || 'fa-folder') : 'fa-folder';
            html += '<tr><td colspan="7" style="padding:0;">' +
                '<div class="category-header"><i class="fas ' + iconClass + ' cat-icon"></i><span class="cat-name">' + esc(catName) + '</span><span class="cat-count">(' + svcs.length + ')</span></div>' +
                '</td></tr>';
            svcs.forEach(([key, svc]) => {
                html += renderBackendRow(key, svc);
                if (expandedRow === 'backend:' + key) {
                    html += renderDetailPanel('backend', key, svc);
                }
            });
        });
        return html;
    }

    // === F8: Keyboard shortcuts ===
    function toggleShortcutsOverlay() {
        const el = document.getElementById('shortcuts-overlay');
        el.classList.toggle('show');
    }
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                if (e.key === 'Escape') {
                    e.target.value = '';
                    searchTerm = '';
                    e.target.blur();
                    renderTables();
                }
                return;
            }
            if (e.key === '/') {
                e.preventDefault();
                document.getElementById('search-input').focus();
            } else if (e.key === 'r' || e.key === 'R') {
                refreshNow();
            } else if (e.key === 'd' || e.key === 'D') {
                toggleTheme();
            } else if (e.key === '?') {
                toggleShortcutsOverlay();
            } else if (e.key === 'Escape') {
                const overlay = document.getElementById('shortcuts-overlay');
                if (overlay.classList.contains('show')) {
                    overlay.classList.remove('show');
                }
            }
        });
    }

    // === Fetch health (modified: F4, F5, F10) ===
    async function fetchHealth() {
        try {
            prevHealthData = healthData ? JSON.parse(JSON.stringify(healthData)) : null;
            const res = await fetch('/health');
            healthData = await res.json();
            lastFetchTime = Date.now();
            countdownValue = 30;
            startCountdown();
            // F10: clear error
            if (fetchError) { fetchError = false; hideErrorBanner(); }
            // F5: update history
            updateRtHistory();
            // F4: detect changes
            detectStatusChanges();
            renderStats();
            renderTables();
        } catch (err) {
            console.error('Health fetch failed:', err);
            // F10: show error
            fetchError = true;
            showErrorBanner();
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

    // === Render single backend row (reusable) ===
    function renderBackendRow(key, svc) {
        const isH = svc.status === 'healthy';
        const rt = svc.response_time;
        const hKey = 'backend:' + key;
        const expanded = expandedRow === hKey;
        return '<tr class="clickable-row' + (expanded ? ' row-expanded' : '') + '" onclick="toggleDetail(\\'backend\\',\\'' + key + '\\')">' +
            '<td><div style="font-weight:500;">' + esc(svc.name) + '</div><div style="font-size:0.75rem;color:var(--text-tertiary);">' + esc(svc.description || '') + '</div></td>' +
            '<td><span style="font-family:JetBrains Mono,monospace;font-size:0.8rem;color:var(--warning);">' + svc.port + '</span></td>' +
            '<td><a href="http://GATEWAY_HOST_PLACEHOLDER:' + svc.port + '" target="_blank" onclick="event.stopPropagation()" style="color:var(--accent);text-decoration:none;font-family:JetBrains Mono,monospace;font-size:0.8rem;">GATEWAY_HOST_PLACEHOLDER:' + svc.port + '</a></td>' +
            '<td><code style="font-size:0.8rem;color:var(--success);font-family:JetBrains Mono,monospace;">/api/' + key + '/</code></td>' +
            '<td>' + renderRTCell(rt, hKey) + '</td>' +
            '<td style="text-align:center;"><span class="dot ' + (isH ? 'dot-healthy' : 'dot-unhealthy') + '"></span> <span style="font-size:0.8rem;color:' + (isH ? 'var(--success)' : 'var(--danger)') + ';">' + (isH ? 'Online' : 'Offline') + '</span></td>' +
            '<td style="text-align:center;"><a href="http://GATEWAY_HOST_PLACEHOLDER:' + svc.port + '" target="_blank" rel="noopener" onclick="event.stopPropagation()" class="open-btn">Open</a></td>' +
        '</tr>';
    }

    // === Render tables (modified: F1, F2, F3, F5, F6, F9) ===
    function renderTables() {
        if (!healthData) return;
        updateSortArrows();

        // Backend
        const bt = document.getElementById('backend-table');
        let bEntries = Object.entries(healthData.backend || {}).filter(([key, svc]) => matchesSearch(svc, key) && matchesStatusFilter(svc));
        bEntries = sortServices(bEntries, 'backend');
        const bTotal = Object.keys(healthData.backend || {}).length;
        let bRows = '';

        if (viewMode === 'grouped') {
            bRows = renderGroupedBackend(bEntries);
        } else {
            bEntries.forEach(([key, svc]) => {
                bRows += renderBackendRow(key, svc);
                if (expandedRow === 'backend:' + key) {
                    bRows += renderDetailPanel('backend', key, svc);
                }
            });
        }
        bt.innerHTML = bRows || '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-tertiary);">No matching services</td></tr>';
        document.getElementById('backend-count').textContent = '(' + bEntries.length + ' of ' + bTotal + ')';

        // Frontend
        const ft = document.getElementById('frontend-table');
        let fEntries = Object.entries(healthData.frontend || {}).filter(([key, svc]) => matchesSearch(svc, key) && matchesStatusFilter(svc));
        fEntries = sortServices(fEntries, 'frontend');
        const fTotal = Object.keys(healthData.frontend || {}).length;
        let fRows = '';
        fEntries.forEach(([key, svc]) => {
            const isH = svc.status === 'healthy';
            const rt = svc.response_time;
            const hKey = 'frontend:' + key;
            const expanded = expandedRow === hKey;
            const svcUrl = svc.url || ('http://GATEWAY_HOST_PLACEHOLDER:' + svc.port);
            const svcLabel = svc.url ? svc.url.replace(/^https?:\\/\\//, '') : ('GATEWAY_HOST_PLACEHOLDER:' + svc.port);
            fRows += '<tr class="clickable-row' + (expanded ? ' row-expanded' : '') + '" onclick="toggleDetail(\\'frontend\\',\\'' + key + '\\')">' +
                '<td><div style="font-weight:500;">' + esc(svc.name) + '</div><div style="font-size:0.75rem;color:var(--text-tertiary);">' + esc(svc.description || '') + '</div></td>' +
                '<td><span style="font-size:0.75rem;padding:2px 8px;border-radius:9999px;background:var(--bg-tertiary);border:1px solid var(--border-color);">' + esc(svc.type || 'Web') + '</span></td>' +
                '<td><span style="font-family:JetBrains Mono,monospace;font-size:0.8rem;color:var(--warning);">' + svc.port + '</span></td>' +
                '<td><a href="' + svcUrl + '" target="_blank" onclick="event.stopPropagation()" style="color:var(--accent);text-decoration:none;font-family:JetBrains Mono,monospace;font-size:0.8rem;">' + esc(svcLabel) + '</a></td>' +
                '<td>' + renderRTCell(rt, hKey) + '</td>' +
                '<td style="text-align:center;"><span class="dot ' + (isH ? 'dot-healthy' : 'dot-unhealthy') + '"></span> <span style="font-size:0.8rem;color:' + (isH ? 'var(--success)' : 'var(--danger)') + ';">' + (isH ? 'Online' : 'Offline') + '</span></td>' +
                '<td style="text-align:center;"><a href="' + svcUrl + '" target="_blank" rel="noopener" onclick="event.stopPropagation()" class="open-btn">Open</a></td>' +
            '</tr>';
            if (expanded) {
                fRows += renderDetailPanel('frontend', key, svc);
            }
        });
        ft.innerHTML = fRows || '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-tertiary);">No matching services</td></tr>';
        document.getElementById('frontend-count').textContent = '(' + fEntries.length + ' of ' + fTotal + ')';
    }

    // === Render RT cell (modified: F5 sparkline, F11 N/A badge) ===
    function renderRTCell(ms, historyKey) {
        if (ms === null || ms === undefined) {
            return '<span class="na-badge">N/A</span>';
        }
        const sparkline = historyKey ? renderSparkline(historyKey) : '';
        return '<div class="sparkline-wrap">' +
            '<div style="display:flex;align-items:center;gap:8px;flex:1;">' +
                '<div style="flex:1;background:var(--bg-tertiary);border-radius:3px;height:6px;max-width:80px;">' +
                    '<div class="rt-bar ' + rtClass(ms) + '" style="width:' + rtWidth(ms) + '%;"></div>' +
                '</div>' +
                '<span style="font-size:0.75rem;font-family:JetBrains Mono,monospace;color:var(--text-secondary);min-width:42px;">' + rtLabel(ms) + '</span>' +
            '</div>' +
            sparkline +
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
    updateViewIcon();
    initKeyboardShortcuts();
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
    ).replace(
        "API_DOCS_JSON",
        json.dumps(API_DOCS)
    ).replace(
        "GATEWAY_HOST_PLACEHOLDER",
        GATEWAY_HOST
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
        service_info = BACKEND_SERVICES[service_name]
        port = service_info["port"]
        scheme = service_info.get("scheme", "http")
    elif service_type == "frontend":
        if service_name not in FRONTEND_SERVICES:
            raise HTTPException(status_code=404, detail=f"Frontend service '{service_name}' not found")
        service_info = FRONTEND_SERVICES[service_name]
        port = service_info["port"]
        scheme = service_info.get("scheme", "http")
    else:
        raise HTTPException(status_code=400, detail="Invalid service type. Use 'backend' or 'frontend'")

    result = await check_service_health(
        port,
        base_path=service_info.get("basePath", ""),
        scheme=scheme,
        health_path=service_info.get("health", ""),
    )
    return {
        "service": service_name,
        "type": service_type,
        "port": port,
        **result
    }

@app.get("/auto-recovery/status")
async def auto_recovery_status():
    """Get auto-recovery system status and recent events"""
    return {
        "enabled": _recovery_state["enabled"],
        "check_interval_sec": RECOVERY_CHECK_INTERVAL,
        "cooldown_sec": RECOVERY_COOLDOWN,
        "max_retries": RECOVERY_MAX_RETRIES,
        "last_check": _recovery_state["last_check"],
        "total_restarts": _recovery_state["total_restarts"],
        "services_tracked": len(_recovery_state["previous_status"]),
        "services_at_max_retries": [
            k for k, v in _recovery_state["restart_counts"].items() if v > RECOVERY_MAX_RETRIES
        ],
        "recent_events": _recovery_state["recovery_log"][-30:],
    }

@app.post("/auto-recovery/reset/{service_key}", dependencies=[Depends(require_api_key)])
async def auto_recovery_reset(service_key: str):
    """Reset retry counter for a service (re-enable auto-recovery after max retries)"""
    if service_key not in _recovery_state["previous_status"]:
        raise HTTPException(status_code=404, detail=f"Service '{service_key}' not tracked")
    _recovery_state["restart_counts"][service_key] = 0
    _recovery_state["restart_cooldown"].pop(service_key, None)
    logger.info("[Auto-Recovery] Retry counter reset for '%s'", service_key)
    return {"message": f"Auto-recovery retry counter reset for '{service_key}'"}

@app.get("/docs/api")
async def api_documentation():
    """Get API documentation for all services"""
    return {
        "title": "AI Project API Documentation",
        "version": "2.0.0",
        "base_url": f"http://{GATEWAY_HOST}:8080",
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
        "direct_url": f"http://{GATEWAY_HOST}:{service_info.get('port', 'unknown')}",
        "endpoints": API_DOCS[service_name]["endpoints"]
    }

@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"], dependencies=[Depends(require_api_key)])
async def proxy_request(service: str, path: str, request: Request):
    """Proxy requests to backend services"""
    if service not in BACKEND_SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found. Available services: {list(BACKEND_SERVICES.keys())}")

    svc = BACKEND_SERVICES[service]
    port = svc["port"]
    scheme = svc.get("scheme", "http")
    target_url = f"{scheme}://localhost:{port}/{path}"

    # Handle query parameters
    if request.query_params:
        target_url += f"?{request.query_params}"

    # Read request body
    body = await request.body()

    # Copy headers (exclude host + hop-by-hop / length headers that httpx recomputes)
    headers = dict(request.headers)
    for h in ("host", "content-length", "connection", "transfer-encoding"):
        headers.pop(h, None)

    try:
        async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                content=body,
                headers=headers,
            )

        # Pass the upstream response through faithfully: preserve status,
        # content-type and raw bytes so JSON, HTML, binary (images/audio/files)
        # are not corrupted. Strip hop-by-hop headers before re-emitting.
        passthrough = {
            k: v for k, v in response.headers.items()
            if k.lower() not in (
                "content-length", "content-encoding", "transfer-encoding",
                "connection", "keep-alive",
            )
        }
        passthrough["X-Proxied-From"] = f"{scheme}://localhost:{port}"
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=passthrough,
            media_type=response.headers.get("content-type"),
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
        logger.exception("[Proxy] Error proxying to '%s': %s", service, e)
        raise HTTPException(status_code=502, detail=f"Proxy error contacting service '{service}'")

# ============================================================
# Main Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║           AI Project API Gateway v2.2.0                   ║
    ║═══════════════════════════════════════════════════════════║
    ║  Dashboard:      http://{GATEWAY_HOST}:8080                   ║
    ║  Health Check:   http://{GATEWAY_HOST}:8080/health            ║
    ║  Auto-Recovery:  http://{GATEWAY_HOST}:8080/auto-recovery/status║
    ║  OpenAPI Docs:   http://{GATEWAY_HOST}:8080/swagger           ║
    ║  API Docs:       http://{GATEWAY_HOST}:8080/docs/api          ║
    ║  Services:       http://{GATEWAY_HOST}:8080/services          ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Auto-Recovery: {'ON ' if RECOVERY_ENABLED else 'OFF'} (interval={RECOVERY_CHECK_INTERVAL}s, cooldown={RECOVERY_COOLDOWN}s)    ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    # NOTE: force the pure-Python asyncio loop + h11 HTTP implementation. Both
    # uvloop and httptools segfault on start in this environment; the pure-Python
    # stack is stable. Override via GATEWAY_LOOP / GATEWAY_HTTP if desired.
    _loop = os.environ.get("GATEWAY_LOOP", "asyncio")
    _http = os.environ.get("GATEWAY_HTTP", "h11")
    uvicorn.run(app, host=GATEWAY_BIND_HOST, port=8080, reload=False, loop=_loop, http=_http)
