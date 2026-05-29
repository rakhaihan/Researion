# Researion

Multi-Agent Research Assistant — an AI-powered platform that automates research workflows using specialized agents orchestrated with LangGraph.

## Features

- Multi-agent research pipeline: Planner, Search, Source Evaluator, Summarizer, Analyst, Critique, Report Writer
- **Background job queue** with Redis + Arq worker (non-blocking workflow execution)
- **Real-time progress tracking** per agent step with percentage
- Research types: Market, Stock/Crypto, Academic, Competitor Analysis, Technology Trend
- PostgreSQL persistence for topics, questions, sources, summaries, and final reports
- REST API with OpenAPI docs at `/docs`
- **Tavily live search** with mock fallback and URL deduplication
- **Citation-aware reports** with inline `[S1][S2]` references and Sources appendix
- Markdown and PDF export (preserves citations)
- Modern React + Tailwind dashboard with source credibility badges
- Docker Compose deployment

## Architecture

```
frontend/   React dashboard (polls /progress)
backend/    FastAPI API + job enqueue
worker/     Arq worker processing LangGraph workflow
postgres/   Research data + job progress storage
redis/      Background job queue
```

## Quick Start (Docker)

1. Copy environment file:

```bash
cp backend/.env.example backend/.env
```

2. Optionally set `OPENAI_API_KEY` in `backend/.env` for LLM-powered agents. Without it, agents use structured fallbacks and mock search still works.

3. Start all services (postgres, redis, backend, worker, frontend):

```bash
docker-compose up --build
```

4. Open:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

> **Note:** If upgrading from an older version, reset the database to apply new schema/enums:
> `docker-compose down -v && docker-compose up --build`

## Manual Development

### Backend API

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Ensure PostgreSQL and Redis are running. Set `DATABASE_URL` and `REDIS_URL` in `.env`.

### Background Worker

Run in a separate terminal:

```bash
cd backend
arq app.workers.settings.WorkerSettings
```

The worker consumes jobs from Redis and executes the multi-agent LangGraph workflow.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL=http://localhost:8000/api` if needed.

## Background Jobs & Progress

### Flow

1. Client calls `POST /api/research/{id}/run`
2. API validates research, creates a `ResearchJob`, enqueues to Redis, returns `job_id` immediately
3. Worker picks up the job and runs agents sequentially
4. Each agent step updates progress in PostgreSQL
5. Frontend polls `GET /api/research/{id}/progress` every ~2.5 seconds

### Progress Steps

| Step | Progress | Label |
|------|----------|-------|
| planning | 10% | Planning research questions |
| searching | 25% | Searching sources |
| evaluating_sources | 40% | Evaluating source credibility |
| summarizing | 55% | Summarizing sources |
| analyzing | 70% | Performing analysis |
| critiquing | 85% | Critiquing analysis |
| writing_report | 95% | Writing final report |
| completed | 100% | Completed |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/research` | Create research project |
| GET | `/api/research` | List research history |
| GET | `/api/research/{id}` | Get research detail |
| POST | `/api/research/{id}/run` | Queue background workflow (returns `job_id`) |
| GET | `/api/research/{id}/progress` | Get latest job progress |
| GET | `/api/jobs/{job_id}` | Get job status by job ID |
| GET | `/api/research/{id}/report` | Get final report |
| GET | `/api/research/{id}/export/markdown` | Export Markdown |
| GET | `/api/research/{id}/export/pdf` | Export PDF |
| GET | `/api/health` | Health check |

### Example: Queue Workflow

```bash
curl -X POST http://localhost:8000/api/research/{research_id}/run
```

Response:

```json
{
  "research_id": "...",
  "job_id": "...",
  "status": "queued",
  "message": "Research job queued successfully"
}
```

### Example: Poll Progress

```bash
curl http://localhost:8000/api/research/{research_id}/progress
```

Response:

```json
{
  "research_id": "...",
  "job_id": "...",
  "status": "running",
  "current_step": "summarizing",
  "current_step_label": "Summarizing sources",
  "progress_percentage": 55,
  "error_message": null,
  "updated_at": "..."
}
```

## Tavily Live Search (Phase 2)

### Configuration

```env
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=tvly-your-api-key
TAVILY_MAX_RESULTS=5
ALLOW_SEARCH_FALLBACK=true
```

| Variable | Description |
|----------|-------------|
| `SEARCH_PROVIDER` | `mock` (default), `tavily`, or `serpapi` |
| `TAVILY_API_KEY` | API key from [tavily.com](https://tavily.com) |
| `TAVILY_MAX_RESULTS` | Max results per research question query |
| `ALLOW_SEARCH_FALLBACK` | If `true`, use mock search when Tavily fails |

### Citation format example

Report body:

```text
NVIDIA remains a leader in AI accelerators due to CUDA ecosystem strength [S1][S3].
```

Sources appendix:

```text
## Sources

[S1] NVIDIA Data Center Revenue Surges — https://example.com/nvidia-earnings
[S2] Analyst Downgrade on Valuation — https://example.com/downgrade
[S3] Industry Outlook 2026 — https://example.com/outlook
```

### Troubleshooting Tavily

| Issue | Fix |
|-------|-----|
| `Invalid API key (401)` | Check `TAVILY_API_KEY` in `backend/.env` |
| Workflow fails immediately | Set `ALLOW_SEARCH_FALLBACK=true` or switch to `SEARCH_PROVIDER=mock` |
| No live results | Verify worker container has same `.env` as backend |
| Duplicate sources | Normal — dedup runs on normalized URL; near-duplicates may differ |

### Test with mock (no API key)

```env
SEARCH_PROVIDER=mock
```

### Test with Tavily

1. Set `SEARCH_PROVIDER=tavily` and valid `TAVILY_API_KEY`
2. Restart `backend` and `worker`: `docker-compose up --build backend worker`
3. Run a research workflow and verify sources have real URLs and `citation_key` fields

## Environment Variables

See `backend/.env.example` for all options:

- `OPENAI_API_KEY` — OpenAI API key
- `REDIS_URL` — Redis connection URL (default: `redis://localhost:6379/0`)
- `SEARCH_PROVIDER` — `mock`, `tavily`, or `serpapi`
- `TAVILY_API_KEY` / `TAVILY_MAX_RESULTS` — Tavily search settings
- `ALLOW_SEARCH_FALLBACK` — Fall back to mock on provider failure
- `SERPAPI_API_KEY` — SerpAPI key (optional)
- `DATABASE_URL` — PostgreSQL async connection string

## Testing

```bash
cd backend
pytest
```

Tests cover agents, services, background job enqueue/progress, duplicate job prevention, and API endpoints.

## Manual Test Checklist

1. Start stack: `docker-compose up --build`
2. Create research from frontend or API
3. Open research detail → click **Run Multi-Agent Workflow**
4. Verify immediate response (no long blocking wait)
5. Watch progress bar update through agent steps
6. Confirm report appears when completed
7. Export Markdown/PDF
8. Click run again while running → should return existing active job (no duplicate)

## Project Structure

```
Researion/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── core/          # config, logging, redis
│   │   ├── db/
│   │   ├── schemas/
│   │   ├── services/      # research_service, job_service
│   │   ├── workers/       # Arq worker + settings
│   │   ├── workflows/
│   │   └── utils/
│   └── tests/
├── frontend/
│   └── src/
├── docker-compose.yml
└── README.md
```

## Notes

- Default search provider is `mock` for local development without external API keys.
- LangGraph orchestrates agents sequentially: plan → search → evaluate → summarize → analyze → critique → report.
- Duplicate run requests while a job is queued/running return the existing active job instead of creating a new one.
- Failed workflows set both job and research status to `failed` with `error_message`.

## License

MIT
