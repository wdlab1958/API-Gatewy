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
        "path": "/home/ubuntu-02/ai_project/TruthLens",
        "entry": "src/main.py"
    },
    "a3de": {
        "port": 4004,
        "name": "A3-ADE Development Environment",
        "description": "WDLAB@2023-2026 development environment",
        "path": "/home/ubuntu-02/ai_project/a3de",
        "entry": "backend/main.py"
    },
    "carelink": {
        "port": 4005,
        "name": "AI CareLink Platform",
        "description": "Healthcare/caregiving AI platform",
        "path": "/home/ubuntu-02/ai_project/AiCarelink",
        "entry": "backend/app/main.py"
    },
    "consulting": {
        "port": 4007,
        "name": "AiNex (AI Consulting)",
        "description": "Multi-agent AI consulting assistant platform",
        "path": "/home/ubuntu-02/ai_project/AiNex",
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
        "path": "/home/ubuntu-02/ai_project/AgentForge",
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
        "path": "/home/ubuntu-02/ai_project/AIALBM",
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
    "aegis": {
        "port": 4015,
        "name": "AEGIS Platform",
        "description": "AI-Enhanced Guardian Intelligence System",
        "path": "/home/wdlab/ai_project/AEGIS",
        "entry": "apps/api/main.py"
    },
    "nexusai": {
        "port": 4016,
        "name": "NexusAI Platform",
        "description": "Multi-agent AI platform with conversations, documents, and workflows",
        "path": "/home/ubuntu-02/ai_project/NexusAI",
        "entry": "apps/api/main.py"
    },
    "ascm": {
        "port": 8006,
        "name": "ASCM Platform",
        "description": "AI SaaS Service Platform Control System - Unified management for AI platforms",
        "path": "/home/ubuntu-02/ai_project/ASCM",
        "entry": "ASCM-main/run_services.py"
    },
    "aimes_food": {
        "port": 18080,
        "name": "AIMES Food",
        "description": "AI MES for Food manufacturing - HACCP compliance & production management",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Food",
        "entry": "services/api-gateway/src/index.js"
    },
    "aimes_agricultural": {
        "port": 28080,
        "name": "AIMES Agricultural",
        "description": "AI MES for Agricultural manufacturing - crop processing & supply chain",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Agricultural",
        "entry": "services/api-gateway/src/index.js"
    },
    "aimes_automotive": {
        "port": 58080,
        "name": "AIMES Automotive",
        "description": "AI MES for Automotive manufacturing - vehicle assembly & quality control",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Automotive",
        "entry": "services/api-gateway/src/index.js"
    },
    "aimes_battery": {
        "port": 40080,
        "name": "AIMES Battery",
        "description": "AI MES for Battery manufacturing - cell production & safety testing",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Battery",
        "entry": "index.js"
    },
    "aimes_chemical": {
        "port": 39080,
        "name": "AIMES Chemical",
        "description": "AI MES for Chemical manufacturing - process control & safety management",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Chemical",
        "entry": "services/api-gateway/src/index.js"
    },
    "aimes_cosmetics": {
        "port": 20080,
        "name": "AIMES Cosmetics",
        "description": "AI MES for Cosmetics manufacturing - formulation & quality assurance",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Cosmetics",
        "entry": "services/api-gateway/src/index.js"
    },
    "aimes_electronics": {
        "port": 48080,
        "name": "AIMES Electronics",
        "description": "AI MES for Electronics manufacturing - PCB assembly & testing",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Electronics",
        "entry": "services/api-gateway/src/index.js"
    },
    "aimes_medical": {
        "port": 29080,
        "name": "AIMES Medical",
        "description": "AI MES for Medical device manufacturing - FDA compliance & sterilization",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Medical",
        "entry": "services/api-gateway/src/index.js"
    },
    "aimes_metal": {
        "port": 49080,
        "name": "AIMES Metal",
        "description": "AI MES for Metal manufacturing - smelting, casting & finishing",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Metal",
        "entry": "services/api-gateway/src/index.js"
    },
    "aimes_pharmaceutical": {
        "port": 38080,
        "name": "AIMES Pharmaceutical",
        "description": "AI MES for Pharmaceutical manufacturing - GMP compliance & batch tracking",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Pharmaceutical",
        "entry": "services/api-gateway/src/index.js"
    },
    "aimes_textile": {
        "port": 50080,
        "name": "AIMES Textile",
        "description": "AI MES for Textile manufacturing - weaving, dyeing & quality control",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Textile",
        "entry": "services/api-gateway/src/index.js"
    },
    "anti_deepfake": {
        "port": 4017,
        "name": "Anti-Deep-Fake",
        "description": "Advanced deepfake detection and prevention system",
        "path": "/home/ubuntu-02/ai_project/Anti-Deep-Fake",
        "entry": "api_server.py"
    },
    "autogit": {
        "port": 4018,
        "name": "AutoGit",
        "description": "AI-powered Git automation with LLM integration",
        "path": "/home/ubuntu-02/ai_project/AutoGit",
        "entry": "api_server.py"
    },
    "stt_tts": {
        "port": 4019,
        "name": "STT-to-TTS",
        "description": "Speech-to-Text and Text-to-Speech processing pipeline",
        "path": "/home/ubuntu-02/ai_project/STT-to-TTS",
        "entry": "api_server.py"
    },
    "truthlens_unified": {
        "port": 8000,
        "name": "TruthLens Unified API",
        "description": "TruthLens DeepFake Detection - Production REST API with multi-agent AI",
        "path": "/home/ubuntu-02/ai_project/TruthLens",
        "entry": "src/unified_server.py"
    },
}

FRONTEND_SERVICES = {
    "truthlens": {
        "port": 8001,
        "name": "TruthLens Web",
        "description": "DeepFake detection web interface",
        "path": "/home/ubuntu-02/ai_project/webpage_truthlens",
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
        "path": "/home/ubuntu-02/ai_project/webpage_ainex_forge",
        "type": "Next.js"
    },
    "cluster_master_web": {
        "port": 3002,
        "name": "Cluster Master Web",
        "description": "Cluster Master webpage",
        "path": "/home/ubuntu-02/ai_project/webpage_ai_cluster_master",
        "type": "Next.js",
        "basePath": "/Webpage-Cluster-Master"
    },
    "aialbm_web": {
        "port": 3003,
        "name": "AIALBM Web",
        "description": "AIALBM webpage",
        "path": "/home/ubuntu-02/ai_project/webpage_aialbm",
        "type": "Next.js",
        "basePath": "/Webpage_AIALBM"
    },
    "carelink_web": {
        "port": 3004,
        "name": "CareLink Web",
        "description": "CareLink webpage",
        "path": "/home/ubuntu-02/ai_project/webpage_carelink",
        "type": "Next.js",
        "basePath": "/Webpage_AI-Carelink"
    },
    "carelink_frontend": {
        "port": 5005,
        "name": "AI CareLink UI",
        "description": "AI CareLink frontend application",
        "path": "/home/ubuntu-02/ai_project/AiCarelink/frontend",
        "type": "Next.js"
    },
    "langgraph_frontend": {
        "port": 5010,
        "name": "AgentForge UI",
        "description": "AgentForge frontend application",
        "path": "/home/ubuntu-02/ai_project/AgentForge/frontend",
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
        "path": "/home/ubuntu-02/ai_project/Ai_Unified_Portal",
        "type": "React/Vite"
    },
    "a3de_frontend": {
        "port": 5004,
        "name": "A3-ADE UI",
        "description": "A3-ADE frontend application",
        "path": "/home/ubuntu-02/ai_project/a3de/frontend",
        "type": "React/Vite"
    },
    "aegis_frontend": {
        "port": 4000,
        "name": "AEGIS Web",
        "description": "AEGIS platform web interface (Desktop Dashboard)",
        "path": "/home/wdlab/ai_project/AEGIS/apps/web",
        "type": "Next.js",
        "scheme": "http",
        "url": f"http://{GATEWAY_HOST}:4000/interface"
    },
    "nexusai_frontend": {
        "port": 3007,
        "name": "NexusAI Web",
        "description": "NexusAI platform web interface",
        "path": "/home/ubuntu-02/ai_project/NexusAI/apps/web",
        "type": "Next.js"
    },
    "webpage_aegis": {
        "port": 8003,
        "name": "AEGIS Homepage",
        "description": "AEGIS marketing/documentation webpage",
        "path": "/home/ubuntu-02/ai_project/webpage_AEGIS",
        "type": "Static"
    },
    "ascm_dashboard": {
        "port": 3010,
        "name": "ASCM Admin Dashboard",
        "description": "ASCM platform administration and management dashboard",
        "path": "/home/ubuntu-02/ai_project/ASCM/ASCM-main/admin-dashboard",
        "type": "Next.js"
    },
    "webpage_aimes": {
        "port": 8004,
        "name": "AIMES Homepage",
        "description": "AIMES Manufacturing Execution System webpage",
        "path": "/home/ubuntu-02/ai_project/webpage_AIMES",
        "type": "Static"
    },
    "webpage_eleven_aimes": {
        "port": 8005,
        "name": "Eleven AIMES Homepage",
        "description": "AIMES Eleven smart factory portfolio webpage",
        "path": "/home/ubuntu-02/ai_project/webpage_Eleven_AIMES",
        "type": "Static"
    },
    "webpage_nexusai": {
        "port": 8009,
        "name": "NexusAI Homepage",
        "description": "NexusAI platform portfolio webpage",
        "path": "/home/ubuntu-02/ai_project/webpage_NexusAI",
        "type": "Static"
    },
    "webpage_all_project": {
        "port": 3008,
        "name": "All Projects Homepage",
        "description": "WDLab1958 all projects unified homepage",
        "path": "/home/ubuntu-02/ai_project/webpage_wdlab1958-all_project",
        "type": "Next.js"
    },
    "aimes_agricultural_web": {
        "port": 5173,
        "name": "AIMES Agricultural Web",
        "description": "AIMES Agricultural MES frontend",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Agricultural/frontend/web",
        "type": "React/Vite"
    },
    "aimes_automotive_web": {
        "port": 5174,
        "name": "AIMES Automotive Web",
        "description": "AIMES Automotive MES frontend",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Automotive/frontend/web",
        "type": "React/Vite"
    },
    "aimes_battery_web": {
        "port": 5175,
        "name": "AIMES Battery Web",
        "description": "AIMES Battery MES frontend",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Battery/frontend/web",
        "type": "React/Vite"
    },
    "aimes_chemical_web": {
        "port": 5176,
        "name": "AIMES Chemical Web",
        "description": "AIMES Chemical MES frontend",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Chemical/frontend/web",
        "type": "React/Vite"
    },
    "aimes_cosmetics_web": {
        "port": 5177,
        "name": "AIMES Cosmetics Web",
        "description": "AIMES Cosmetics MES frontend",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Cosmetics/frontend/web",
        "type": "React/Vite"
    },
    "aimes_electronics_web": {
        "port": 5178,
        "name": "AIMES Electronics Web",
        "description": "AIMES Electronics MES frontend",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Electronics/frontend/web",
        "type": "React/Vite"
    },
    "aimes_food_web": {
        "port": 5179,
        "name": "AIMES Food Web",
        "description": "AIMES Food MES frontend",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Food/frontend/web",
        "type": "React/Vite"
    },
    "aimes_medical_web": {
        "port": 5180,
        "name": "AIMES Medical Web",
        "description": "AIMES Medical MES frontend",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Medical/frontend/web",
        "type": "React/Vite"
    },
    "aimes_metal_web": {
        "port": 5181,
        "name": "AIMES Metal Web",
        "description": "AIMES Metal MES frontend",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Metal/frontend/web",
        "type": "React/Vite"
    },
    "aimes_pharmaceutical_web": {
        "port": 5182,
        "name": "AIMES Pharmaceutical Web",
        "description": "AIMES Pharmaceutical MES frontend",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Pharmaceutical/frontend/web",
        "type": "React/Vite"
    },
    "aimes_textile_web": {
        "port": 5183,
        "name": "AIMES Textile Web",
        "description": "AIMES Textile MES frontend",
        "path": "/home/ubuntu-02/ai_project/AIMES-Eleven/AIMES-Textile/frontend/web",
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
    "aegis": {
        "endpoints": [
            # Health & Info
            {"method": "GET", "path": "/api/v1/info", "description": "API information with architecture layers"},
            {"method": "GET", "path": "/api/v1/health", "description": "Basic health check"},
            {"method": "GET", "path": "/api/v1/health/detailed", "description": "Detailed health check with dependency status"},
            {"method": "GET", "path": "/api/v1/health/architecture", "description": "AEGIS 7-layer architecture information"},
            # LLM (HLE)
            {"method": "GET", "path": "/api/v1/llm/models", "description": "List available LLM models"},
            {"method": "POST", "path": "/api/v1/llm/chat", "description": "Chat completion using HLE"},
            {"method": "GET", "path": "/api/v1/llm/health", "description": "HLE health and provider availability"},
            # Memory (3LMS)
            {"method": "GET", "path": "/api/v1/memory/status", "description": "Memory system status (3-layer)"},
            {"method": "GET", "path": "/api/v1/memory/activity/recent", "description": "Recent activity across memory layers"},
            {"method": "GET", "path": "/api/v1/memory/working/sessions", "description": "List working memory sessions"},
            {"method": "POST", "path": "/api/v1/memory/working/sessions/{session_id}/messages", "description": "Add message to working memory"},
            {"method": "DELETE", "path": "/api/v1/memory/working/sessions/{session_id}", "description": "Clear working memory session"},
            {"method": "GET", "path": "/api/v1/memory/episodic/episodes", "description": "List episodic memory episodes"},
            {"method": "POST", "path": "/api/v1/memory/episodic/episodes", "description": "Create episodic memory episode"},
            {"method": "GET", "path": "/api/v1/memory/semantic/entities", "description": "List semantic memory entities"},
            {"method": "POST", "path": "/api/v1/memory/semantic/entities", "description": "Add semantic memory entity"},
            {"method": "GET", "path": "/api/v1/memory/semantic/relationships", "description": "List semantic relationships"},
            {"method": "POST", "path": "/api/v1/memory/semantic/relationships", "description": "Add semantic relationship"},
            {"method": "POST", "path": "/api/v1/memory/consolidation/run", "description": "Run memory consolidation"},
            {"method": "GET", "path": "/api/v1/memory/consolidation/log", "description": "Consolidation log entries"},
            {"method": "POST", "path": "/api/v1/memory/embeddings/generate", "description": "Generate text embedding"},
            # Agents
            {"method": "GET", "path": "/api/v1/agents/frameworks", "description": "List agent frameworks"},
            {"method": "GET", "path": "/api/v1/agents", "description": "List all agents"},
            {"method": "POST", "path": "/api/v1/agents", "description": "Create a new agent"},
            {"method": "GET", "path": "/api/v1/agents/{agent_id}", "description": "Get agent details"},
            {"method": "DELETE", "path": "/api/v1/agents/{agent_id}", "description": "Delete an agent"},
            {"method": "POST", "path": "/api/v1/agents/tasks", "description": "Submit task for execution"},
            {"method": "GET", "path": "/api/v1/agents/tasks/list", "description": "List all tasks"},
            # Orchestration (MAOL)
            {"method": "GET", "path": "/api/v1/orchestration/status", "description": "Orchestration layer status"},
            {"method": "GET", "path": "/api/v1/orchestration/workflows", "description": "List workflows"},
            {"method": "POST", "path": "/api/v1/orchestration/workflows", "description": "Create and execute workflow"},
            {"method": "GET", "path": "/api/v1/orchestration/workflows/{workflow_id}", "description": "Get workflow by ID"},
            {"method": "DELETE", "path": "/api/v1/orchestration/workflows/{workflow_id}", "description": "Delete workflow"},
            # Dashboard
            {"method": "GET", "path": "/api/v1/dashboard/overview", "description": "System dashboard overview"},
            {"method": "GET", "path": "/api/v1/dashboard/alerts", "description": "Active system alerts"},
            # Projects
            {"method": "GET", "path": "/api/v1/projects", "description": "List all projects"},
            {"method": "GET", "path": "/api/v1/projects/{project_id}", "description": "Get project by ID"},
            # Companion (PLCM)
            {"method": "GET", "path": "/api/v1/companion/status", "description": "Companion status and personality"},
            {"method": "POST", "path": "/api/v1/companion/dialogue", "description": "Companion dialogue"},
            {"method": "GET", "path": "/api/v1/companion/personality", "description": "Get personality profile"},
            {"method": "PUT", "path": "/api/v1/companion/personality", "description": "Update personality"},
            {"method": "GET", "path": "/api/v1/companion/preferences", "description": "Get user preferences"},
            {"method": "POST", "path": "/api/v1/companion/preferences", "description": "Update user preferences"},
            {"method": "GET", "path": "/api/v1/companion/routines", "description": "List user routines"},
            {"method": "POST", "path": "/api/v1/companion/routines", "description": "Create routine"},
            {"method": "GET", "path": "/api/v1/companion/goals", "description": "List user goals"},
            {"method": "POST", "path": "/api/v1/companion/goals", "description": "Create goal"},
            {"method": "GET", "path": "/api/v1/companion/reminders", "description": "List reminders"},
            {"method": "POST", "path": "/api/v1/companion/reminders", "description": "Create reminder"},
            {"method": "DELETE", "path": "/api/v1/companion/reminders/{reminder_id}", "description": "Delete reminder"},
            {"method": "GET", "path": "/api/v1/companion/diary/entries", "description": "List diary entries"},
            {"method": "POST", "path": "/api/v1/companion/diary/entries", "description": "Create diary entry"},
            # Automation (PSAE)
            {"method": "GET", "path": "/api/v1/automation/status", "description": "Automation layer status"},
            {"method": "GET", "path": "/api/v1/automation/list", "description": "List all automations"},
            {"method": "POST", "path": "/api/v1/automation", "description": "Create automation"},
            {"method": "POST", "path": "/api/v1/automation/{auto_id}/run", "description": "Execute automation"},
            {"method": "DELETE", "path": "/api/v1/automation/{auto_id}", "description": "Delete automation"},
            {"method": "GET", "path": "/api/v1/automation/dashboard/home", "description": "Home automation dashboard"},
            {"method": "GET", "path": "/api/v1/automation/devices", "description": "List all devices"},
            {"method": "POST", "path": "/api/v1/automation/devices", "description": "Register device"},
            {"method": "GET", "path": "/api/v1/automation/devices/stats", "description": "Device statistics"},
            {"method": "GET", "path": "/api/v1/automation/devices/{device_id}", "description": "Get device details"},
            {"method": "DELETE", "path": "/api/v1/automation/devices/{device_id}", "description": "Delete device"},
            {"method": "POST", "path": "/api/v1/automation/devices/{device_id}/command", "description": "Send device command"},
            {"method": "POST", "path": "/api/v1/automation/devices/voice-test", "description": "Test NLU voice command"},
            {"method": "GET", "path": "/api/v1/automation/scenes", "description": "List scenes"},
            {"method": "POST", "path": "/api/v1/automation/scenes", "description": "Create scene"},
            {"method": "POST", "path": "/api/v1/automation/scenes/presets", "description": "Create preset scenes"},
            {"method": "GET", "path": "/api/v1/automation/scenes/stats", "description": "Scene statistics"},
            {"method": "DELETE", "path": "/api/v1/automation/scenes/{scene_id}", "description": "Delete scene"},
            {"method": "POST", "path": "/api/v1/automation/scenes/{scene_id}/execute", "description": "Execute scene"},
            {"method": "POST", "path": "/api/v1/automation/scenes/{scene_id}/favorite", "description": "Toggle scene favorite"},
            {"method": "GET", "path": "/api/v1/automation/spaces/rooms", "description": "List rooms"},
            {"method": "POST", "path": "/api/v1/automation/spaces/rooms", "description": "Create room"},
            {"method": "DELETE", "path": "/api/v1/automation/spaces/rooms/{room_id}", "description": "Delete room"},
            {"method": "POST", "path": "/api/v1/automation/spaces/rooms/{room_id}/devices/{device_id}", "description": "Add device to room"},
            {"method": "DELETE", "path": "/api/v1/automation/spaces/rooms/{room_id}/devices/{device_id}", "description": "Remove device from room"},
            {"method": "POST", "path": "/api/v1/automation/mqtt/publish", "description": "Publish MQTT message"},
            {"method": "GET", "path": "/api/v1/automation/mqtt/status", "description": "MQTT bridge status"},
            {"method": "GET", "path": "/api/v1/automation/homeassistant/devices", "description": "Home Assistant devices"},
            {"method": "POST", "path": "/api/v1/automation/homeassistant/sync", "description": "Sync Home Assistant devices"},
            {"method": "GET", "path": "/api/v1/automation/homeassistant/status", "description": "Home Assistant status"},
            {"method": "POST", "path": "/api/v1/automation/homeassistant/service", "description": "Call Home Assistant service"},
            {"method": "GET", "path": "/api/v1/automation/email/digest", "description": "Daily email digest"},
            {"method": "GET", "path": "/api/v1/automation/email/rules", "description": "List email triage rules"},
            {"method": "POST", "path": "/api/v1/automation/email/rules", "description": "Add email triage rule"},
            {"method": "GET", "path": "/api/v1/automation/email/status", "description": "Email triage status"},
            {"method": "POST", "path": "/api/v1/automation/calendar/sync", "description": "Sync external calendar"},
            {"method": "GET", "path": "/api/v1/automation/calendar/external", "description": "List external calendars"},
            {"method": "GET", "path": "/api/v1/automation/routines", "description": "List routines"},
            {"method": "POST", "path": "/api/v1/automation/routines", "description": "Create routine"},
            {"method": "POST", "path": "/api/v1/automation/routines/{routine_id}/execute", "description": "Execute routine"},
            {"method": "POST", "path": "/api/v1/automation/routines/{routine_id}/toggle", "description": "Toggle routine"},
            {"method": "DELETE", "path": "/api/v1/automation/routines/{routine_id}", "description": "Delete routine"},
            {"method": "GET", "path": "/api/v1/automation/routines/stats", "description": "Routine statistics"},
            {"method": "GET", "path": "/api/v1/automation/devices/{device_id}/history", "description": "Device event history"},
            # Config
            {"method": "GET", "path": "/api/v1/config", "description": "Get all configuration"},
            {"method": "PUT", "path": "/api/v1/config", "description": "Update configuration"},
            # Auth
            {"method": "POST", "path": "/api/v1/auth/register", "description": "Register user"},
            {"method": "POST", "path": "/api/v1/auth/login", "description": "Login and get tokens"},
            {"method": "POST", "path": "/api/v1/auth/refresh", "description": "Refresh access token"},
            {"method": "GET", "path": "/api/v1/auth/me", "description": "Current user profile"},
            {"method": "POST", "path": "/api/v1/auth/test-user", "description": "Create test user (dev)"},
            {"method": "GET", "path": "/api/v1/auth/admin/users", "description": "List all users (admin)"},
            {"method": "PUT", "path": "/api/v1/auth/admin/users/{user_id}/role", "description": "Update user role (admin)"},
            # Voice
            {"method": "GET", "path": "/api/v1/voice/status", "description": "Voice engine status"},
            {"method": "GET", "path": "/api/v1/voice/stt/models", "description": "List STT models"},
            {"method": "POST", "path": "/api/v1/voice/stt/load", "description": "Load STT model"},
            {"method": "POST", "path": "/api/v1/voice/stt/unload", "description": "Unload STT model"},
            {"method": "POST", "path": "/api/v1/voice/transcribe", "description": "Transcribe audio to text"},
            {"method": "POST", "path": "/api/v1/voice/synthesize", "description": "Text-to-speech synthesis"},
            {"method": "POST", "path": "/api/v1/voice/synthesize/json", "description": "TTS metadata (no audio)"},
            {"method": "POST", "path": "/api/v1/voice/conversation", "description": "Full voice conversation turn"},
            {"method": "GET", "path": "/api/v1/voice/voices", "description": "List TTS voices"},
            {"method": "GET", "path": "/api/v1/voice/languages", "description": "Supported STT languages"},
            # Monitoring
            {"method": "GET", "path": "/api/v1/monitoring/events", "description": "Recent monitoring events"},
            {"method": "GET", "path": "/api/v1/monitoring/stats", "description": "Monitoring statistics"},
            # Docs
            {"method": "GET", "path": "/api/v1/docs/list", "description": "List documentation files"},
            {"method": "GET", "path": "/api/v1/docs/{filename}", "description": "Get documentation content"},
            # Files
            {"method": "GET", "path": "/api/v1/files/status", "description": "File manager status"},
            {"method": "POST", "path": "/api/v1/files/search", "description": "Search files"},
            {"method": "POST", "path": "/api/v1/files/copy", "description": "Copy files"},
            {"method": "POST", "path": "/api/v1/files/move", "description": "Move files"},
            {"method": "POST", "path": "/api/v1/files/rename", "description": "Rename file"},
            {"method": "POST", "path": "/api/v1/files/delete", "description": "Delete files"},
            {"method": "POST", "path": "/api/v1/files/organize", "description": "Auto-organize files"},
            # Desktop
            {"method": "GET", "path": "/api/v1/desktop/status", "description": "Desktop integration status"},
            {"method": "POST", "path": "/api/v1/desktop/clipboard/analyze", "description": "Analyze clipboard text"},
            # WebSocket
            {"method": "WS", "path": "/ws", "description": "Main WebSocket (real-time events)"},
            {"method": "WS", "path": "/ws/voice/realtime", "description": "Real-time voice WebSocket"},
            # Prometheus
            {"method": "GET", "path": "/metrics", "description": "Prometheus metrics"},
        ]
    },
    "nexusai": {
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Service health check"},
            {"method": "POST", "path": "/auth/login", "description": "User authentication"},
            {"method": "GET", "path": "/agents", "description": "List agents"},
            {"method": "POST", "path": "/conversations", "description": "Create conversation"},
            {"method": "GET", "path": "/documents", "description": "List documents"},
            {"method": "POST", "path": "/tasks", "description": "Create task"},
        ]
    },
    "ascm": {
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Gateway health check"},
            {"method": "GET", "path": "/health/services", "description": "All ASCM services health status"},
            {"method": "POST", "path": "/auth/login", "description": "Admin authentication"},
            {"method": "GET", "path": "/auth/me", "description": "Current authenticated user info"},
            {"method": "GET", "path": "/api/v1/platforms", "description": "List managed AI platforms"},
            {"method": "GET", "path": "/api/v1/customers/customers", "description": "List customers"},
            {"method": "GET", "path": "/api/v1/customers/customers/stats", "description": "Customer statistics"},
            {"method": "GET", "path": "/api/v1/subscriptions/subscriptions", "description": "List subscriptions"},
            {"method": "GET", "path": "/api/v1/subscriptions/subscriptions/stats", "description": "Subscription statistics"},
            {"method": "GET", "path": "/api/v1/billing/invoices", "description": "List invoices"},
            {"method": "GET", "path": "/api/v1/billing/invoices/stats", "description": "Invoice statistics"},
            {"method": "GET", "path": "/api/v1/monitoring/metrics", "description": "System metrics (CPU, memory, disk)"},
            {"method": "GET", "path": "/api/v1/monitoring/alerts", "description": "List alerts"},
            {"method": "GET", "path": "/api/v1/analytics/dashboard", "description": "Analytics dashboard summary"},
            {"method": "GET", "path": "/api/v1/analytics/revenue/mrr", "description": "Monthly Recurring Revenue"},
        ]
    },
    "aimes_food": {
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Gateway health check"},
            {"method": "GET", "path": "/api/production", "description": "Production line status"},
            {"method": "GET", "path": "/api/quality", "description": "Quality inspection data"},
            {"method": "GET", "path": "/api/inventory", "description": "Inventory management"},
            {"method": "GET", "path": "/api/traceability", "description": "Product traceability"},
            {"method": "POST", "path": "/api/haccp", "description": "HACCP compliance check"},
        ]
    },
    "aimes_agricultural": {
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Gateway health check"},
            {"method": "GET", "path": "/api/production", "description": "Production line status"},
            {"method": "GET", "path": "/api/quality", "description": "Quality inspection data"},
            {"method": "GET", "path": "/api/inventory", "description": "Inventory management"},
            {"method": "GET", "path": "/api/traceability", "description": "Product traceability"},
        ]
    },
    "aimes_automotive": {
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Gateway health check"},
            {"method": "GET", "path": "/api/production", "description": "Production line status"},
            {"method": "GET", "path": "/api/quality", "description": "Quality inspection data"},
            {"method": "GET", "path": "/api/inventory", "description": "Inventory management"},
            {"method": "GET", "path": "/api/traceability", "description": "Product traceability"},
        ]
    },
    "aimes_battery": {
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Gateway health check"},
            {"method": "GET", "path": "/api/production", "description": "Production line status"},
            {"method": "GET", "path": "/api/quality", "description": "Quality inspection data"},
            {"method": "GET", "path": "/api/inventory", "description": "Inventory management"},
            {"method": "GET", "path": "/api/traceability", "description": "Product traceability"},
        ]
    },
    "aimes_chemical": {
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Gateway health check"},
            {"method": "GET", "path": "/api/production", "description": "Production line status"},
            {"method": "GET", "path": "/api/quality", "description": "Quality inspection data"},
            {"method": "GET", "path": "/api/inventory", "description": "Inventory management"},
            {"method": "GET", "path": "/api/traceability", "description": "Product traceability"},
        ]
    },
    "aimes_cosmetics": {
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Gateway health check"},
            {"method": "GET", "path": "/api/production", "description": "Production line status"},
            {"method": "GET", "path": "/api/quality", "description": "Quality inspection data"},
            {"method": "GET", "path": "/api/inventory", "description": "Inventory management"},
            {"method": "GET", "path": "/api/traceability", "description": "Product traceability"},
        ]
    },
    "aimes_electronics": {
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Gateway health check"},
            {"method": "GET", "path": "/api/production", "description": "Production line status"},
            {"method": "GET", "path": "/api/quality", "description": "Quality inspection data"},
            {"method": "GET", "path": "/api/inventory", "description": "Inventory management"},
            {"method": "GET", "path": "/api/traceability", "description": "Product traceability"},
        ]
    },
    "aimes_medical": {
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Gateway health check"},
            {"method": "GET", "path": "/api/production", "description": "Production line status"},
            {"method": "GET", "path": "/api/quality", "description": "Quality inspection data"},
            {"method": "GET", "path": "/api/inventory", "description": "Inventory management"},
            {"method": "GET", "path": "/api/traceability", "description": "Product traceability"},
        ]
    },
    "aimes_metal": {
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Gateway health check"},
            {"method": "GET", "path": "/api/production", "description": "Production line status"},
            {"method": "GET", "path": "/api/quality", "description": "Quality inspection data"},
            {"method": "GET", "path": "/api/inventory", "description": "Inventory management"},
            {"method": "GET", "path": "/api/traceability", "description": "Product traceability"},
        ]
    },
    "aimes_pharmaceutical": {
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Gateway health check"},
            {"method": "GET", "path": "/api/production", "description": "Production line status"},
            {"method": "GET", "path": "/api/quality", "description": "Quality inspection data"},
            {"method": "GET", "path": "/api/inventory", "description": "Inventory management"},
            {"method": "GET", "path": "/api/traceability", "description": "Product traceability"},
        ]
    },
    "aimes_textile": {
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Gateway health check"},
            {"method": "GET", "path": "/api/production", "description": "Production line status"},
            {"method": "GET", "path": "/api/quality", "description": "Quality inspection data"},
            {"method": "GET", "path": "/api/inventory", "description": "Inventory management"},
            {"method": "GET", "path": "/api/traceability", "description": "Product traceability"},
        ]
    },
    "truthlens_unified": {
        "endpoints": [
            {"method": "GET", "path": "/health", "description": "Service health check"},
            {"method": "POST", "path": "/detect/upload", "description": "Upload and analyze file for deepfake detection"},
            {"method": "POST", "path": "/detect/async", "description": "Async deepfake detection (returns task ID)"},
            {"method": "GET", "path": "/detect/status/{task_id}", "description": "Get async detection task status"},
            {"method": "GET", "path": "/models", "description": "List available detection models"},
            {"method": "POST", "path": "/compliance/report", "description": "Generate AI Basic Law compliance report"},
            {"method": "GET", "path": "/queue/stats", "description": "Task queue statistics"},
        ]
    },
}

# Service Categories for grouped view
SERVICE_CATEGORIES = {
    "AI Platforms": {
        "icon": "cube",
        "services": ["a3de", "langgraph", "aialbm", "enterprise", "aegis", "nexusai"]
    },
    "Detection & Analysis": {
        "icon": "shield",
        "services": ["deepfake", "anti_deepfake", "truthlens_unified"]
    },
    "Healthcare": {
        "icon": "heart",
        "services": ["carelink"]
    },
    "Infrastructure": {
        "icon": "server",
        "services": ["cluster_master", "factory", "autogit"]
    },
    "Assistants & Bots": {
        "icon": "message-circle",
        "services": ["consulting", "panda"]
    },
    "Data & ML": {
        "icon": "database",
        "services": ["dataset_gen", "multimodals", "stt_tts"]
    },
    "Compliance": {
        "icon": "file-text",
        "services": ["labor"]
    },
    "SaaS Management": {
        "icon": "settings",
        "services": ["ascm"]
    },
    "Manufacturing": {
        "icon": "industry",
        "services": ["aimes_food", "aimes_agricultural", "aimes_automotive", "aimes_battery", "aimes_chemical", "aimes_cosmetics", "aimes_electronics", "aimes_medical", "aimes_metal", "aimes_pharmaceutical", "aimes_textile"]
    },
}

# ============================================================
# Service Startup Commands (for Auto-Recovery)
# ============================================================

_BASE = "/home/ubuntu-02/ai_project"

SERVICE_STARTUP_COMMANDS = {
    # --- Backend Services ---
    "dataset_gen": {
        "workdir": f"{_BASE}/Dataset_Gen",
        "cmd": "myenv/bin/streamlit run main.py --server.port 4001 --server.headless true",
    },
    "deepfake": {
        "workdir": f"{_BASE}/TruthLens/src",
        "cmd": "../venv/bin/python3 -m uvicorn api_server:app --host 0.0.0.0 --port 4002",
    },
    "a3de": {
        "workdir": f"{_BASE}/a3de/backend",
        "cmd": "../venv/bin/uvicorn main:app --host 0.0.0.0 --port 4004",
    },
    "carelink": {
        "workdir": f"{_BASE}/AiCarelink/backend",
        "cmd": "../venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 4005",
    },
    "consulting": {
        "workdir": f"{_BASE}/AiNex",
        "cmd": "venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 4007",
    },
    "factory": {
        "workdir": f"{_BASE}/ai_factory",
        "cmd": "venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 4008",
    },
    "labor": {
        "workdir": f"{_BASE}/ai_labor",
        "cmd": "venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 4009",
    },
    "langgraph": {
        "workdir": f"{_BASE}/AgentForge",
        "cmd": "venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 4010",
    },
    "multimodals": {
        "workdir": f"{_BASE}/ai_multimodals/web",
        "cmd": """../venv/bin/python -c "import app as a; a.socketio.run(a.app, host='0.0.0.0', port=4011, debug=False, allow_unsafe_werkzeug=True)" """,
    },
    "aialbm": {
        "workdir": f"{_BASE}/AIALBM",
        "cmd": "aialb_venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 4012",
    },
    "enterprise": {
        "workdir": f"{_BASE}/enterprise_factory/local-llm-os/backend",
        "cmd": "venv/bin/python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 4013",
    },
    "panda": {
        "workdir": f"{_BASE}/panda_chetbot/api",
        "cmd": "../venv/bin/uvicorn main:app --host 0.0.0.0 --port 4014",
    },
    "cluster_master": {
        "workdir": f"{_BASE}/Cluster-Master",
        "cmd": "venv/bin/python3 -m uvicorn src.server:app --host 0.0.0.0 --port 8200",
    },
    "aegis": {
        "workdir": f"{_BASE}/AEGIS/apps/api",
        "cmd": "venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 4015",
    },
    "nexusai": {
        "workdir": f"{_BASE}/NexusAI/apps/api",
        "cmd": ".venv/bin/uvicorn main:app --host 0.0.0.0 --port 4016",
    },
    "ascm": {
        "workdir": f"{_BASE}/ASCM/ASCM-main",
        "cmd": "venv_ascm/bin/python run_services.py",
    },
    "aimes_food": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Food",
        "cmd": "docker compose up -d",
        "docker": True,
    },
    "aimes_agricultural": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Agricultural/services/api-gateway",
        "cmd": "env API_GATEWAY_PORT=28080 node src/index.js",
    },
    "aimes_automotive": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Automotive/services/api-gateway",
        "cmd": "env PORT=58080 node src/index.js",
    },
    "aimes_battery": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Battery/services/api-gateway",
        "cmd": "env PORT=40080 node index.js",
    },
    "aimes_chemical": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Chemical/services/api-gateway",
        "cmd": "env API_GATEWAY_PORT=39080 node src/index.js",
    },
    "aimes_cosmetics": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Cosmetics/services/api-gateway",
        "cmd": "env PORT=20080 node src/index.js",
    },
    "aimes_electronics": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Electronics/services/api-gateway",
        "cmd": "env API_GATEWAY_PORT=48080 node src/index.js",
    },
    "aimes_medical": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Medical/services/api-gateway",
        "cmd": "env PORT=29080 node src/index.js",
    },
    "aimes_metal": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Metal/services/api-gateway",
        "cmd": "env PORT=49080 node src/index.js",
    },
    "aimes_pharmaceutical": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Pharmaceutical/services/api-gateway",
        "cmd": "env API_GATEWAY_PORT=38080 node src/index.js",
    },
    "aimes_textile": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Textile/services/api-gateway",
        "cmd": "env PORT=50080 node src/index.js",
    },
    "anti_deepfake": {
        "workdir": f"{_BASE}/Anti-Deep-Fake",
        "cmd": "venv/bin/python3 -m uvicorn api_server:app --host 0.0.0.0 --port 4017",
    },
    "autogit": {
        "workdir": f"{_BASE}/AutoGit",
        "cmd": ".venv/bin/python -m uvicorn api_server:app --host 0.0.0.0 --port 4018",
    },
    "stt_tts": {
        "workdir": f"{_BASE}/STT-to-TTS",
        "cmd": "venv/bin/python3 -m uvicorn api_server:app --host 0.0.0.0 --port 4019",
    },
    "truthlens_unified": {
        "workdir": f"{_BASE}/TruthLens",
        "cmd": "venv/bin/python3 src/unified_server.py",
    },
    # --- Frontend Services ---
    "truthlens": {
        "workdir": f"{_BASE}/webpage_truthlens",
        "cmd": "python3 -m http.server 8001",
    },
    "webpage_ainex": {
        "workdir": f"{_BASE}/webpage_AiNex",
        "cmd": "python3 -m http.server 8002",
    },
    "ainex_home": {
        "workdir": f"{_BASE}/webpage_ainex_forge",
        "cmd": "npx next dev -p 3001",
    },
    "cluster_master_web": {
        "workdir": f"{_BASE}/webpage_ai_cluster_master",
        "cmd": "npx next dev -p 3002",
    },
    "aialbm_web": {
        "workdir": f"{_BASE}/webpage_aialbm",
        "cmd": "npx next dev -p 3003",
    },
    "carelink_web": {
        "workdir": f"{_BASE}/webpage_carelink",
        "cmd": "npx next dev -p 3004",
    },
    "carelink_frontend": {
        "workdir": f"{_BASE}/AiCarelink/frontend",
        "cmd": "npx next dev -p 5005",
    },
    "langgraph_frontend": {
        "workdir": f"{_BASE}/AgentForge/frontend",
        "cmd": "npx vite --port 5010 --host",
    },
    "enterprise_frontend": {
        "workdir": f"{_BASE}/enterprise_factory/local-llm-os/frontend",
        "cmd": "npx vite --port 5013 --host",
    },
    "unified_portal": {
        "workdir": f"{_BASE}/Ai_Unified_Portal",
        "cmd": "npx vite --port 5015 --host",
    },
    "a3de_frontend": {
        "workdir": f"{_BASE}/a3de/frontend",
        "cmd": "node node_modules/vite/bin/vite.js --port 5004 --host",
    },
    "aegis_frontend": {
        "workdir": f"{_BASE}/AEGIS/apps/web",
        "cmd": "npx next dev -p 4000 --hostname 0.0.0.0",
    },
    "nexusai_frontend": {
        "workdir": f"{_BASE}/NexusAI/apps/web",
        "cmd": "npx next dev -p 3007",
    },
    "webpage_aegis": {
        "workdir": f"{_BASE}/webpage_AEGIS",
        "cmd": "python3 -m http.server 8003",
    },
    "ascm_dashboard": {
        "workdir": f"{_BASE}/ASCM/ASCM-main/admin-dashboard",
        "cmd": "npx next dev -p 3010",
    },
    "webpage_aimes": {
        "workdir": f"{_BASE}/webpage_AIMES",
        "cmd": "python3 -m http.server 8004",
    },
    "webpage_eleven_aimes": {
        "workdir": f"{_BASE}/webpage_Eleven_AIMES",
        "cmd": "python3 -m http.server 8005",
    },
    "webpage_nexusai": {
        "workdir": f"{_BASE}/webpage_NexusAI",
        "cmd": "python3 -m http.server 8009",
    },
    "webpage_all_project": {
        "workdir": f"{_BASE}/webpage_wdlab1958-all_project",
        "cmd": "npx next dev -p 3008",
    },
    "aimes_agricultural_web": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Agricultural/frontend/web",
        "cmd": "npx vite --port 5173 --host",
    },
    "aimes_automotive_web": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Automotive/frontend/web",
        "cmd": "npx vite --port 5174 --host",
    },
    "aimes_battery_web": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Battery/frontend/web",
        "cmd": "npx vite --port 5175 --host",
    },
    "aimes_chemical_web": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Chemical/frontend/web",
        "cmd": "npx vite --port 5176 --host",
    },
    "aimes_cosmetics_web": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Cosmetics/frontend/web",
        "cmd": "npx vite --port 5177 --host",
    },
    "aimes_electronics_web": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Electronics/frontend/web",
        "cmd": "npx vite --port 5178 --host",
    },
    "aimes_food_web": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Food/frontend/web",
        "cmd": "npx vite --port 5179 --host",
    },
    "aimes_medical_web": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Medical/frontend/web",
        "cmd": "npx vite --port 5180 --host",
    },
    "aimes_metal_web": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Metal/frontend/web",
        "cmd": "npx vite --port 5181 --host",
    },
    "aimes_pharmaceutical_web": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Pharmaceutical/frontend/web",
        "cmd": "npx vite --port 5182 --host",
    },
    "aimes_textile_web": {
        "workdir": f"{_BASE}/AIMES-Eleven/AIMES-Textile/frontend/web",
        "cmd": "npx vite --port 5183 --host",
    },
    # truthlens_gradio shares port 8000 with truthlens_unified — no separate restart needed
}

# ============================================================
# Auto-Recovery System
# ============================================================

RECOVERY_CHECK_INTERVAL = 30   # seconds between health checks
RECOVERY_COOLDOWN = 120        # seconds between restart attempts per service
RECOVERY_MAX_RETRIES = 5       # max consecutive restart attempts before pausing

_recovery_state = {
    "enabled": True,
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
        return True
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
    allow_origins=GATEWAY_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Start the auto-recovery background monitor."""
    _recovery_state["task"] = asyncio.create_task(auto_recovery_loop())
    logger.info("[API Gateway] Auto-Recovery monitor started")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop the auto-recovery background monitor."""
    _recovery_state["enabled"] = False
    if _recovery_state["task"]:
        _recovery_state["task"].cancel()
    logger.info("[API Gateway] Auto-Recovery monitor stopped")


# ============================================================
# Helper Functions
# ============================================================

async def check_service_health(port: int, timeout: float = 2.0, base_path: str = "", scheme: str = "http") -> dict:
    """Check service health status"""
    endpoints_to_try = ["/health", "/api/health", "/", "/api/"]
    if base_path:
        endpoints_to_try = [base_path, f"{base_path}/health"] + endpoints_to_try

    for endpoint in endpoints_to_try:
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
                response = await client.get(f"{scheme}://localhost:{port}{endpoint}")
                if response.status_code in [200, 207, 307, 503]:
                    return {
                        "status": "healthy",
                        "response_time": response.elapsed.total_seconds() * 1000,
                        "endpoint": endpoint
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
        backend_tasks.append(check_service_health(service_info["port"], scheme=service_info.get("scheme", "http")))

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

    result = await check_service_health(port, scheme=scheme)
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
                except Exception:
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
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║           AI Project API Gateway v2.1.0                   ║
    ║═══════════════════════════════════════════════════════════║
    ║  Dashboard:      http://{GATEWAY_HOST}:8080                   ║
    ║  Health Check:   http://{GATEWAY_HOST}:8080/health            ║
    ║  Auto-Recovery:  http://{GATEWAY_HOST}:8080/auto-recovery/status║
    ║  OpenAPI Docs:   http://{GATEWAY_HOST}:8080/swagger           ║
    ║  API Docs:       http://{GATEWAY_HOST}:8080/docs/api          ║
    ║  Services:       http://{GATEWAY_HOST}:8080/services          ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Auto-Recovery: ON (interval={RECOVERY_CHECK_INTERVAL}s, cooldown={RECOVERY_COOLDOWN}s)     ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host=GATEWAY_BIND_HOST, port=8080, reload=False)
