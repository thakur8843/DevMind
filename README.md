# DevMind — Phase 1: Core Backend + RAG + Middleware

Agentic code review platform — FastAPI · Qdrant · PostgreSQL · Groq · Docker

## Stack

| Layer | Tech | Cost |
|---|---|---|
| Backend | FastAPI + Uvicorn | Free |
| LLM | Groq (Llama 3.1 8B) | Free tier |
| Embeddings | HuggingFace all-MiniLM-L6-v2 | Free (local CPU) |
| Vector DB | Qdrant (Cloud free 1GB or local Docker) | Free |
| Database | PostgreSQL 16 | Free |
| Container | Docker Compose | Free |

## Middleware Stack

| Middleware | What it does |
|---|---|
| `LoggingMiddleware` | Attaches `X-Request-ID` to every request, logs method/path/status/time |
| `CORSMiddleware` | Cross-origin headers for frontend access |
| Rate Limiter (`slowapi`) | 30 req/min global, 10/min on `/review`, 20/min on `/chat` |
| API Key Auth | Protects all `/api/v1/*` routes via `X-API-Key` header |
| Error Handlers | Clean JSON errors for 4xx/5xx + validation failures |

## Quickstart

```bash
# 1. Setup environment
cp .env.example .env
# Fill in: GROQ_API_KEY, POSTGRES_PASSWORD, and optionally QDRANT_URL + QDRANT_API_KEY

# 2. Start with Docker (PostgreSQL + Qdrant included)
docker-compose up --build

# 3. Or run locally (needs postgres + qdrant running)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | /health | ❌ | Health check |
| POST | /api/v1/review/ | ✅ | Submit code for AI review |
| POST | /api/v1/review/chat | ✅ | RAG chat over your code |
| GET | /api/v1/review/history/{session_id} | ✅ | Get session history |
| DELETE | /api/v1/review/session/{session_id} | ✅ | Delete session data |

## Calling the API

```bash
# All requests need the API key header
curl -X POST http://localhost:8000/api/v1/review/ \
  -H "X-API-Key: devmind-local-api-key" \
  -H "Content-Type: application/json" \
  -d '{"code": "def fib(n):\n  return fib(n-1)+fib(n-2)", "language": "python"}'
```

## Qdrant Options

**Cloud (recommended for deployment):**
```
QDRANT_URL=https://YOUR-CLUSTER.qdrant.io
QDRANT_API_KEY=your_key
```

```

## Phase 2 Preview
- LangGraph agent orchestration
- Human-in-the-loop approval gates  
- Redis caching layer
- Celery + RabbitMQ async jobs
