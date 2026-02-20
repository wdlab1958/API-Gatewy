#!/usr/bin/env python3
"""
AI Project API Gateway
모든 프로젝트의 API를 단일 엔드포인트로 라우팅하는 게이트웨이
Port: 8080
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import asyncio
from typing import Dict, Any

app = FastAPI(
    title="AI Project API Gateway",
    description="통합 API 게이트웨이 - 모든 프로젝트 API 라우팅",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Backend 서비스 매핑
BACKEND_SERVICES = {
    "dataset_gen": {"port": 4001, "name": "Dataset Generator", "status": "pending"},
    "deepfake": {"port": 4002, "name": "DeepFake Detection (TruthLens)", "status": "running"},
    "a3de": {"port": 4004, "name": "A3-ADE Development Environment", "status": "running"},
    "carelink": {"port": 4005, "name": "AI CareLink Platform", "status": "running"},
    "cluster": {"port": 4006, "name": "AI Cluster Master", "status": "running"},
    "consulting": {"port": 4007, "name": "AI Consulting Assistant", "status": "running"},
    "factory": {"port": 4008, "name": "AI Factory", "status": "running"},
    "labor": {"port": 4009, "name": "AI Labor Compliance", "status": "pending"},
    "langgraph": {"port": 4010, "name": "AgentForge (LangGraph)", "status": "running"},
    "multimodals": {"port": 4011, "name": "AI Multimodals", "status": "pending"},
    "aialbm": {"port": 4012, "name": "AIALBM Memory Platform", "status": "pending"},
    "enterprise": {"port": 4013, "name": "Enterprise Factory", "status": "pending"},
    "panda": {"port": 4014, "name": "Panda Chatbot", "status": "pending"},
}

# Frontend 서비스 매핑
FRONTEND_SERVICES = {
    "dataset_gen": {"port": 4000, "name": "Dataset Generator UI"},
    "deepfake": {"port": 5000, "name": "TruthLens UI"},
    "a3de": {"port": 5004, "name": "A3-ADE UI"},
    "carelink": {"port": 5005, "name": "AI CareLink UI"},
    "cluster": {"port": 5006, "name": "AI Cluster UI"},
    "consulting": {"port": 5007, "name": "AI Consulting UI (Backend Integrated)"},
    "factory": {"port": 5008, "name": "AI Factory UI (Backend Integrated)"},
    "labor": {"port": 5009, "name": "AI Labor UI"},
    "langgraph": {"port": 5010, "name": "AgentForge UI"},
    "multimodals": {"port": 5020, "name": "AI Multimodals UI"},
    "aialbm": {"port": 5030, "name": "AIALBM UI"},
    "enterprise": {"port": 5013, "name": "Enterprise Factory UI"},
    "panda": {"port": 5014, "name": "Panda Chatbot UI"},
    "unified_portal": {"port": 5015, "name": "Unified Portal"},
}

async def check_service_health(port: int) -> bool:
    """서비스 상태 확인"""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"http://localhost:{port}/health")
            return response.status_code == 200
    except:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"http://localhost:{port}/")
                return response.status_code in [200, 307, 404]
        except:
            return False

@app.get("/")
async def root():
    """API 게이트웨이 홈"""
    return {
        "message": "AI Project API Gateway",
        "version": "1.0.0",
        "endpoints": {
            "/services": "서비스 목록 조회",
            "/health": "전체 서비스 상태 확인",
            "/api/{service}/{path}": "서비스별 API 프록시"
        }
    }

@app.get("/services")
async def list_services():
    """모든 서비스 목록"""
    return {
        "backend_services": BACKEND_SERVICES,
        "frontend_services": FRONTEND_SERVICES
    }

@app.get("/health")
async def health_check():
    """전체 서비스 상태 확인"""
    health_status = {"backend": {}, "frontend": {}}

    # 백엔드 서비스 상태 확인
    for service, info in BACKEND_SERVICES.items():
        is_healthy = await check_service_health(info["port"])
        health_status["backend"][service] = {
            "name": info["name"],
            "port": info["port"],
            "status": "healthy" if is_healthy else "unhealthy",
            "url": f"http://localhost:{info['port']}"
        }

    # 프론트엔드 서비스 상태 확인
    for service, info in FRONTEND_SERVICES.items():
        is_healthy = await check_service_health(info["port"])
        health_status["frontend"][service] = {
            "name": info["name"],
            "port": info["port"],
            "status": "healthy" if is_healthy else "unhealthy",
            "url": f"http://localhost:{info['port']}"
        }

    return health_status

@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(service: str, path: str, request: Request):
    """API 프록시 - 서비스별 요청 전달"""
    if service not in BACKEND_SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")

    port = BACKEND_SERVICES[service]["port"]
    target_url = f"http://localhost:{port}/{path}"

    # 요청 본문 읽기
    body = await request.body()

    # 헤더 복사
    headers = dict(request.headers)
    headers.pop("host", None)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                content=body,
                headers=headers,
                params=request.query_params,
            )

            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else {"data": response.text},
                status_code=response.status_code,
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"Service '{service}' is not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API 엔드포인트 문서 - 각 서비스별 주요 엔드포인트
API_DOCS = {
    "deepfake": {
        "base_url": "/api/deepfake",
        "endpoints": [
            {"method": "POST", "path": "/detect", "description": "딥페이크 탐지 분석"},
            {"method": "GET", "path": "/health", "description": "서비스 상태 확인"},
            {"method": "GET", "path": "/models", "description": "사용 가능한 모델 목록"},
        ]
    },
    "carelink": {
        "base_url": "/api/carelink",
        "endpoints": [
            {"method": "POST", "path": "/auth/login", "description": "로그인"},
            {"method": "GET", "path": "/patients", "description": "환자 목록"},
            {"method": "GET", "path": "/caregivers", "description": "간병인 목록"},
        ]
    },
    "cluster": {
        "base_url": "/api/cluster",
        "endpoints": [
            {"method": "GET", "path": "/workers", "description": "워커 노드 목록"},
            {"method": "POST", "path": "/tasks", "description": "작업 생성"},
            {"method": "GET", "path": "/status", "description": "클러스터 상태"},
        ]
    },
    "consulting": {
        "base_url": "/api/consulting",
        "endpoints": [
            {"method": "POST", "path": "/diagnose", "description": "AI 성숙도 진단"},
            {"method": "GET", "path": "/reports", "description": "보고서 목록"},
            {"method": "POST", "path": "/analyze", "description": "시나리오 분석"},
        ]
    },
    "langgraph": {
        "base_url": "/api/langgraph",
        "endpoints": [
            {"method": "POST", "path": "/chat", "description": "AI 채팅"},
            {"method": "POST", "path": "/rag/query", "description": "RAG 쿼리"},
            {"method": "GET", "path": "/agents", "description": "에이전트 목록"},
        ]
    },
    "a3de": {
        "base_url": "/api/a3de",
        "endpoints": [
            {"method": "POST", "path": "/projects", "description": "프로젝트 생성"},
            {"method": "GET", "path": "/agents", "description": "에이전트 목록"},
            {"method": "POST", "path": "/code/generate", "description": "코드 생성"},
        ]
    },
}

@app.get("/docs/api")
async def api_documentation():
    """API 문서"""
    return {
        "title": "AI Project API Documentation",
        "services": API_DOCS,
        "note": "각 서비스의 상세 API 문서는 해당 서비스의 /docs 엔드포인트에서 확인 가능합니다."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
