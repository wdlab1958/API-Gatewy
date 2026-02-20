# AI Project Service Status

**Update: Feb. 01, 2026**
**Editor: Brian Lee**

---

## API Gateway v2.0

| Item | Value |
|------|-------|
| **Dashboard** | http://localhost:8080 |
| **Health Check** | http://localhost:8080/health |
| **OpenAPI Docs** | http://localhost:8080/swagger |
| **API Reference** | http://localhost:8080/redoc |
| **Services JSON** | http://localhost:8080/services |
| **API Docs** | http://localhost:8080/docs/api |

### Quick Start
```bash
cd ~/ai_project
./start_gateway.sh
```

---

## Backend Services

| Service Key | Name | Port | Direct URL | Gateway URL | Status |
|-------------|------|------|------------|-------------|--------|
| dataset_gen | Dataset Generator | 4001 | localhost:4001 | /api/dataset_gen/ | Pending |
| deepfake | TruthLens (DeepFake) | 4002 | localhost:4002 | /api/deepfake/ | Ready |
| a3de | A3-ADE Dev Environment | 4004 | localhost:4004 | /api/a3de/ | Ready |
| carelink | AI CareLink Platform | 4005 | localhost:4005 | /api/carelink/ | Ready |
| cluster | AI Cluster PC | 4006 | localhost:4006 | /api/cluster/ | Ready |
| consulting | AI Consulting Assistant | 4007 | localhost:4007 | /api/consulting/ | Ready |
| factory | AI Factory | 4008 | localhost:4008 | /api/factory/ | Ready |
| labor | AI Labor Compliance | 4009 | localhost:4009 | /api/labor/ | Pending (xgboost) |
| langgraph | AgentForge (LangGraph) | 4010 | localhost:4010 | /api/langgraph/ | Ready |
| multimodals | AI Multimodals | 4011 | localhost:4011 | /api/multimodals/ | Pending (flask) |
| aialbm | AIALBM Memory Platform | 4012 | localhost:4012 | /api/aialbm/ | Pending (chromadb) |
| enterprise | Enterprise Factory | 4013 | localhost:4013 | /api/enterprise/ | Pending |
| panda | Panda Chatbot | 4014 | localhost:4014 | /api/panda/ | Pending (redis) |
| cluster_master | Cluster Master | 8200 | localhost:8200 | /api/cluster_master/ | Ready |

---

## Frontend Applications

| Service Key | Name | Type | Port | URL |
|-------------|------|------|------|-----|
| truthlens | TruthLens Web | Next.js | 8001 | http://localhost:8001 |
| webpage_ainex | AiNex Web | Static | 8002 | http://localhost:8002 |
| ainex_home | AiNex Home | Next.js | 3001 | http://localhost:3001 |
| cluster_master_web | Cluster Master Web | Next.js | 3002 | http://localhost:3002 |
| aialbm_web | AIALBM Web | Next.js | 3003 | http://localhost:3003 |
| carelink_web | CareLink Web | Next.js | 3004 | http://localhost:3004 |
| ai_homepage | AI Homepage | Next.js | 3005 | http://localhost:3005 |
| carelink_frontend | AI CareLink UI | Next.js | 5005 | http://localhost:5005 |
| langgraph_frontend | AgentForge UI | React/Vite | 5010 | http://localhost:5010 |
| enterprise_frontend | Enterprise Factory UI | React/Vite | 5013 | http://localhost:5013 |
| unified_portal | Unified Portal | React/Vite | 5015 | http://localhost:5015 |
| a3de_frontend | A3-ADE UI | React/Vite | 5004 | http://localhost:5004 |

---

## API Routing Examples

```bash
# DeepFake Detection API
curl http://localhost:8080/api/deepfake/health

# AI CareLink API
curl http://localhost:8080/api/carelink/health

# Cluster Master API
curl http://localhost:8080/api/cluster_master/api/status

# AgentForge API
curl http://localhost:8080/api/langgraph/health

# A3-ADE API
curl http://localhost:8080/api/a3de/health
```

---

## Scripts

| Script | Description |
|--------|-------------|
| `./start_gateway.sh` | Start API Gateway only |
| `./start_all_services.sh` | Start all backend/frontend services |
| `./stop_all_services.sh` | Stop all services |

---

## Log Files

All log files are stored in `/tmp/`:
- API Gateway: `/tmp/api_gateway.log`
- Backend: `/tmp/{project}_backend.log`
- Frontend: `/tmp/{project}_frontend.log`

---

## Troubleshooting

### Missing Dependencies
```bash
pip3 install --user redis flask xgboost PyPDF2 chromadb
```

### Port Conflicts
```bash
# Check which process is using a port
lsof -i :8080

# Kill process on specific port
fuser -k 8080/tcp
```

### Service Not Starting
```bash
# Check service logs
tail -f /tmp/{service_name}_backend.log

# Check if port is available
netstat -tlnp | grep {port}
```
