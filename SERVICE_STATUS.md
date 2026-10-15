# API Gateway — Service Status & Registry

> Live snapshot 2026-06-06 from the running gateway. **Backend 26 + Frontend 34 + Gateway 1 = 61.**
> **Currently Online: 61/61  (Backend 26/26, Frontend 34/34, Gateway 1/1)** — all services booted on their registry ports.

## Backend Services

| Key | Port | Status | Name |
|-----|------|--------|------|
| `notebooklm` | 8013 | 🟢 | Design NotebookLM (Server) |
| `fileforge` | 8090 | 🟢 | FileForge Backend |
| `fileforge_py` | 8091 | 🟢 | FileForge-Python Backend |
| `autoflow` | 8085 | 🟢 | AutoFlow Backend |
| `wdlab_cli` | 8877 | 🟢 | WDLab CLI Backend |
| `expert100k` | 8001 | 🟢 | 100K-Expert |
| `aegis` | 4015 | 🟢 | AEGIS API |
| `aialbm` | 8000 | 🟢 | AIALBM Memory Platform |
| `agriprocess` | 28080 | 🟢 | AIMES AgriProcess Gateway |
| `argus` | 8002 | 🟢 | ARGUS Backend |
| `agentforge` | 8003 | 🟢 | AgentForge (LangGraph) |
| `carelink` | 8004 | 🟢 | AI CareLink Backend |
| `ainex` | 8005 | 🟢 | AiNex Consulting |
| `janggi` | 8007 | 🟢 | JangGi Backend |
| `nexusai` | 8008 | 🟢 | NexusAI API |
| `patentforge` | 9700 | 🟢 | PatentForge API |
| `crawling` | 3014 | 🟢 | Project Crawling Server |
| `selfsec` | 8019 | 🟢 | Self Security Consulting API |
| `alphaforge` | 8021 | 🟢 | WDLAB AlphaForge Backend |
| `llmops` | 18080 | 🟢 | WDLAB LLMOps Backend |
| `pokerface` | 8012 | 🟢 | PokerFace Backend |
| `truthlens` | 7000 | 🟢 | TruthLens Gateway |
| `jangforge` | 8014 | 🟢 | WDLAB JangForge |
| `ascm` | 8006 | 🟢 | ASCM Integration Gateway |
| `pi5_edge` | 18899 | 🟢 | Pi5 Edge Device Gateway |
| `pi5_aegis` | 8088 | 🟢 | Pi5 AEGIS Gateway |

## Frontend Services

| Key | Port | Status | Type | Name |
|-----|------|--------|------|------|
| `notebooklm_web` | 3017 | 🟢 | Vite | Design NotebookLM Web |
| `fileforge_web` | 5185 | 🟢 | Vite | FileForge Web |
| `autoflow_web` | 5174 | 🟢 | Vite | AutoFlow Web |
| `wdlab_cli_web` | 5188 | 🟢 | Vite | WDLab CLI Web |
| `aegis_web` | 4000 | 🟢 | Next.js | AEGIS Web |
| `agriprocess_web` | 5273 | 🟢 | Vite | AIMES AgriProcess Web |
| `argus_web` | 3030 | 🟢 | Vite | ARGUS Web |
| `agentforge_web` | 5175 | 🟢 | Vite | AgentForge UI |
| `carelink_web` | 3000 | 🟢 | Next.js | AI CareLink UI |
| `janggi_web` | 3021 | 🟢 | Next.js | JangGi Web |
| `nexusai_web` | 3022 | 🟢 | Next.js | NexusAI Web |
| `patentforge_web` | 3023 | 🟢 | Next.js | PatentForge Web |
| `crawling_web` | 3013 | 🟢 | Vite | Project Crawling Web |
| `selfsec_dashboard` | 8501 | 🟢 | Streamlit | Self Security Dashboard |
| `alphaforge_web` | 3024 | 🟢 | Next.js | WDLAB AlphaForge Web |
| `llmops_web` | 18090 | 🟢 | Vite | WDLAB LLMOps Web |
| `pokerface_web` | 5176 | 🟢 | Vite | PokerFace Web |
| `slideeditor` | 3025 | 🟢 | Vite | SlideEditor |
| `truthlens_web` | 7001 | 🟢 | Vite | TruthLens Dashboard |
| `ascm_web` | 3010 | 🟢 | Next.js | ASCM Admin Dashboard |
| `aimes_agricultural_web` | 5301 | 🟢 | Vite | AIMES Agricultural Web |
| `aimes_automotive_web` | 5302 | 🟢 | Vite | AIMES Automotive Web |
| `aimes_battery_web` | 5303 | 🟢 | Vite | AIMES Battery Web |
| `aimes_chemical_web` | 5304 | 🟢 | Vite | AIMES Chemical Web |
| `aimes_cosmetics_web` | 5305 | 🟢 | Vite | AIMES Cosmetics Web |
| `aimes_electronics_web` | 5306 | 🟢 | Vite | AIMES Electronics Web |
| `aimes_food_web` | 5307 | 🟢 | Vite | AIMES Food Web |
| `aimes_medical_web` | 5308 | 🟢 | Vite | AIMES Medical Web |
| `aimes_metal_web` | 5309 | 🟢 | Vite | AIMES Metal Web |
| `aimes_pharmaceutical_web` | 5310 | 🟢 | Vite | AIMES Pharmaceutical Web |
| `aimes_textile_web` | 5311 | 🟢 | Vite | AIMES Textile Web |
| `patentforge_webpage` | 8201 | 🟢 | Static | PatentForge Homepage |
| `alphaforge_webpage` | 8202 | 🟢 | Static | AlphaForge Homepage |
| `llmops_webpage` | 8203 | 🟢 | Static | LLMOps Homepage |

## Notes
- Run `./status_services.sh` for a live colored table.
- Several services were booted by serving their production build (Vite `dist/`) on the registry port; Next.js via `next start`/`next dev`; Python APIs via uvicorn on the registry port; truthlens & ascm with dedicated provisioned PostgreSQL (docker).
