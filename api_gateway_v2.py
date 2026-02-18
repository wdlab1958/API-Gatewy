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

Update: Feb. 15, 2026
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
        "path": "/home/ubuntu-02/ai_project/TruthLens",
        "entry": "src/main.py"
    },
    "a3_adep": {
        "port": 4003,
        "name": "A3-ADEP Agent Platform",
        "description": "Agent-based AI system with task orchestration",
        "path": "/home/ubuntu-02/ai_project/A3-ADEP",
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
        "path": "/home/ubuntu-02/ai_project/AEGIS",
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
        "port": 3006,
        "name": "AEGIS Web",
        "description": "AEGIS platform web interface",
        "path": "/home/ubuntu-02/ai_project/AEGIS/apps/web",
        "type": "Next.js"
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
            {"method": "GET", "path": "/health", "description": "Service health check"},
            {"method": "POST", "path": "/llm/chat", "description": "LLM chat conversation"},
            {"method": "GET", "path": "/agents", "description": "List available agents"},
            {"method": "GET", "path": "/projects", "description": "List projects"},
            {"method": "GET", "path": "/dashboard", "description": "Dashboard data"},
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
}

# Service Categories for grouped view
SERVICE_CATEGORIES = {
    "AI Platforms": {
        "icon": "cube",
        "services": ["a3_adep", "a3de", "langgraph", "aialbm", "enterprise", "aegis", "nexusai"]
    },
    "Detection & Analysis": {
        "icon": "shield",
        "services": ["deepfake", "anti_deepfake"]
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

async def check_service_health(port: int, timeout: float = 2.0, base_path: str = "") -> dict:
    """Check service health status"""
    endpoints_to_try = ["/health", "/api/health", "/", "/api/"]
    if base_path:
        endpoints_to_try = [base_path, f"{base_path}/health"] + endpoints_to_try

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
        frontend_tasks.append(check_service_health(service_info["port"], base_path=service_info.get("basePath", "")))

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
        <div class="qlink-grid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px;">
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
            '<td><a href="http://localhost:' + svc.port + '" target="_blank" onclick="event.stopPropagation()" style="color:var(--accent);text-decoration:none;font-family:JetBrains Mono,monospace;font-size:0.8rem;">localhost:' + svc.port + '</a></td>' +
            '<td><code style="font-size:0.8rem;color:var(--success);font-family:JetBrains Mono,monospace;">/api/' + key + '/</code></td>' +
            '<td>' + renderRTCell(rt, hKey) + '</td>' +
            '<td style="text-align:center;"><span class="dot ' + (isH ? 'dot-healthy' : 'dot-unhealthy') + '"></span> <span style="font-size:0.8rem;color:' + (isH ? 'var(--success)' : 'var(--danger)') + ';">' + (isH ? 'Online' : 'Offline') + '</span></td>' +
            '<td style="text-align:center;"><a href="http://localhost:' + svc.port + '" target="_blank" rel="noopener" onclick="event.stopPropagation()" class="open-btn">Open</a></td>' +
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
            fRows += '<tr class="clickable-row' + (expanded ? ' row-expanded' : '') + '" onclick="toggleDetail(\\'frontend\\',\\'' + key + '\\')">' +
                '<td><div style="font-weight:500;">' + esc(svc.name) + '</div><div style="font-size:0.75rem;color:var(--text-tertiary);">' + esc(svc.description || '') + '</div></td>' +
                '<td><span style="font-size:0.75rem;padding:2px 8px;border-radius:9999px;background:var(--bg-tertiary);border:1px solid var(--border-color);">' + esc(svc.type || 'Web') + '</span></td>' +
                '<td><span style="font-family:JetBrains Mono,monospace;font-size:0.8rem;color:var(--warning);">' + svc.port + '</span></td>' +
                '<td><a href="http://localhost:' + svc.port + '" target="_blank" onclick="event.stopPropagation()" style="color:var(--accent);text-decoration:none;font-family:JetBrains Mono,monospace;font-size:0.8rem;">localhost:' + svc.port + '</a></td>' +
                '<td>' + renderRTCell(rt, hKey) + '</td>' +
                '<td style="text-align:center;"><span class="dot ' + (isH ? 'dot-healthy' : 'dot-unhealthy') + '"></span> <span style="font-size:0.8rem;color:' + (isH ? 'var(--success)' : 'var(--danger)') + ';">' + (isH ? 'Online' : 'Offline') + '</span></td>' +
                '<td style="text-align:center;"><a href="http://localhost:' + svc.port + '" target="_blank" rel="noopener" onclick="event.stopPropagation()" class="open-btn">Open</a></td>' +
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
