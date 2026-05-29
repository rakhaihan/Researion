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
- Modern React + Tailwind dashboard with design system, workflow stepper, and polished report viewer (Phase 4)
- **SSE progress stream** with polling fallback (~2s) and tab-visibility aware updates
- Source credibility badges, filters, and citation navigation
- **JWT authentication** with per-user research isolation (Phase 3)
- **Alembic migrations** for production-ready schema management
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

3. Start all services (postgres, redis, **migrate**, backend, worker, frontend):

```bash
docker-compose up --build
```

The `migrate` service runs `alembic upgrade head` before backend/worker start.

4. Open http://localhost:5173 → **Register** a new account (Docker defaults to `AUTH_MODE=jwt`).

5. API:

- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health (public): http://localhost:8000/api/health

> **Note:** Upgrading from Phase 1–2 without Alembic? Reset DB is easiest:
> `docker-compose down -v && docker-compose up --build`

## Authentication (Phase 3)

### Environment

```env
AUTH_MODE=jwt          # jwt | api_key | disabled
SECRET_KEY=your-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256
AUTO_CREATE_TABLES=false
API_KEY=               # required when AUTH_MODE=api_key
```

| AUTH_MODE | Behavior |
|-----------|----------|
| `jwt` | Register/login required; Bearer token on research endpoints |
| `api_key` | `X-API-Key` header; uses dev user context |
| `disabled` | Local dev bypass with auto dev user (`dev@researion.local`) |

### Endpoints

| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/api/auth/register` | Public |
| POST | `/api/auth/login` | Public |
| GET | `/api/auth/me` | Bearer |
| GET | `/api/health` | Public |
| All `/api/research/*`, `/api/jobs/*` | Bearer (jwt mode) |

### Login example

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"password123"}'
```

Use token for research:

```bash
curl http://localhost:8000/api/research \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Database Migrations (Alembic)

From `backend/`:

```bash
# Apply migrations
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Migrations:

| Revision | Description |
|----------|-------------|
| `001_initial_complete` | Full schema from SQLAlchemy metadata (users + research + jobs) |
| `002_backfill_dev_user` | No-op on fresh DB; backfills legacy rows if needed |

Manual migration in Docker:

```bash
docker compose run --rm migrate
```

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
npm run dev      # http://localhost:5173
npm run build    # production bundle
npm test         # Vitest unit tests
```

Set `VITE_API_URL=http://localhost:8000/api` if needed.

## Background Jobs & Progress

### Flow

1. Client calls `POST /api/research/{id}/run`
2. API validates research, creates a `ResearchJob`, enqueues to Redis, returns `job_id` immediately
3. Worker picks up the job and runs agents sequentially
4. Each agent step updates progress in PostgreSQL
5. Frontend uses **SSE** `GET /api/research/{id}/progress/stream` when available, with **polling fallback** every ~2 seconds
6. Polling pauses when the browser tab is hidden (reduces request spam)

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
| GET | `/api/research/{id}/progress/stream` | Server-Sent Events progress stream (Bearer auth) |
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

- `AUTH_MODE`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES` — Authentication
- `AUTO_CREATE_TABLES` — Dev-only `create_all()` fallback (default: `false`)
- `OPENAI_API_KEY` — OpenAI API key
- `REDIS_URL` — Redis connection URL (default: `redis://localhost:6379/0`)
- `SEARCH_PROVIDER` — `mock`, `tavily`, or `serpapi`
- `TAVILY_API_KEY` / `TAVILY_MAX_RESULTS` — Tavily search settings
- `ALLOW_SEARCH_FALLBACK` — Fall back to mock on provider failure
- `SERPAPI_API_KEY` — SerpAPI key (optional)
- `DATABASE_URL` — PostgreSQL async connection string

## Phase 6 — Quality Evaluation & Anti-Hallucination

### Structured agent outputs

All LangGraph agents return **Pydantic-validated JSON** (`app/schemas/agent_outputs.py`):

- PlannerOutput, SearchAgentOutput, SourceEvaluationOutput, SourceSummaryOutput
- AnalystOutput, CritiqueOutput, ReportWriterOutput

The LLM service parses JSON with up to **2 repair retries**, then falls back to safe defaults without crashing the workflow.

### Citation validation

`CitationValidationService` checks:

- Inline `[S1]` keys exist in collected sources
- No fictitious citations
- Key finding citation coverage (target ≥70%)
- Single-source dependency warnings

### Quality score (0–100)

| Sub-score | Meaning |
|-----------|---------|
| citation_score | Validity & coverage of citations |
| source_diversity_score | Domain variety |
| source_credibility_score | Average source credibility |
| freshness_score | Dated / accessed sources |
| completeness_score | Required report sections present |

**Quality gate:**

| Overall | Status |
|---------|--------|
| ≥80 | `passed` |
| 60–79 | `warning` |
| <60 | `failed` |

Reports are **always saved**; warnings appear in the UI.

### API

| Method | Endpoint |
|--------|----------|
| GET | `/api/research/{id}/quality` |
| POST | `/api/research/{id}/regenerate-report` |

Regenerate re-runs **Report Writer + critique + quality only** (no new search).

### Example warnings

- `Fictitious or unknown citations detected: S99`
- `Only 50% of key findings include citations`
- `High-risk claim without citation: Revenue increased 25%...`
- `Conclusion contains no inline citations`

### Tests

```bash
cd backend && pytest tests/test_phase6_quality.py tests/test_regenerate_report.py -q
cd frontend && npm test
```

## Phase 5 — Production & CI/CD

See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for full production deployment.

Quick reference:

```bash
cp backend/.env.production.example backend/.env.production
# edit secrets, then:
export POSTGRES_PASSWORD=your-db-password
export VITE_API_URL=http://localhost:8000/api
docker compose -f docker-compose.prod.yml up --build
```

- Health: `/api/health`, `/api/health/live`, `/api/health/ready`
- Gunicorn backend, Nginx frontend, JSON logs in production
- Auth rate limiting, password policy (letter + number), CORS from env
- CI: `.github/workflows/ci.yml`

## Phase 4 UI (Dashboard Polish)

### Highlights

- **App shell**: Sidebar with Researion branding, topbar (user, auth status, logout), responsive mobile menu
- **Design system** (`frontend/src/components/ui/`): Button, Card, Input, Select, Badge, Alert, Skeleton, ProgressBar, PageHeader, SectionHeader, EmptyState
- **New Research**: Template cards by type, depth selector, dynamic placeholders, client validation (topic ≥ 10 chars)
- **Workflow stepper**: 8 steps with pending / running / completed / failed mapping from `current_step`
- **Report viewer**: Styled markdown, sticky export toolbar, copy markdown, clickable `[S1]` citations → sources panel
- **Sources panel**: Credibility tier filters, collapsible rationale, low-credibility warning
- **History**: Search + filter by type/status, sort by latest
- **Dashboard**: Hero, stats cards, recent research, pipeline overview

### Screenshots

> Placeholder: add screenshots of Dashboard, Research Detail (stepper), and Report viewer to `docs/screenshots/` when available.

### Run frontend tests

```bash
cd frontend
npm install
npm test
```

### Polling vs SSE

| Mode | When | Endpoint |
|------|------|----------|
| SSE (preferred) | After workflow starts, tab visible | `GET /api/research/{id}/progress/stream` |
| Polling (fallback) | SSE error or unsupported | `GET /api/research/{id}/progress` every 2s |

Both stop automatically when status is `completed` or `failed`.

### Auth / token troubleshooting

| Issue | Fix |
|-------|-----|
| Redirected to login unexpectedly | Token expired — sign in again; check `ACCESS_TOKEN_EXPIRE_MINUTES` |
| 401 on API calls | Ensure `Authorization: Bearer <token>`; clear `localStorage` key `researion_token` |
| SSE fails but polling works | Normal fallback; verify backend exposes stream route and CORS allows streaming |

## Testing

```bash
cd backend
pytest

cd frontend
npm test
```

Tests cover agents, services, background job enqueue/progress, SSE stream, auth, duplicate job prevention, workflow step mapping, and UI validation.

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
