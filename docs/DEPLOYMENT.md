# Researion Production Deployment

This guide covers deploying Researion with Docker Compose for a single-host or small production setup.

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- Domain names for frontend and API (recommended)
- TLS termination via reverse proxy (Caddy, Nginx, Traefik, or cloud load balancer)

## 1. Configure environment

```bash
cp backend/.env.production.example backend/.env.production
cp frontend/.env.production.example frontend/.env.production
```

Edit `backend/.env.production`:

| Variable | Notes |
|----------|--------|
| `SECRET_KEY` | At least 32 random characters |
| `DATABASE_URL` | Use Docker service host `db` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `AUTH_MODE` | Must be `jwt` in production |
| `BACKEND_CORS_ORIGINS` | Your public frontend URL(s), comma-separated |
| `FRONTEND_URL` | Public app URL |
| `TAVILY_API_KEY` | Required when `SEARCH_PROVIDER=tavily` |
| `ADMIN_API_KEY` | Optional, for job cleanup endpoint |

Edit root `.env` for Compose (or export):

```bash
POSTGRES_PASSWORD=strong-db-password
VITE_API_URL=https://api.yourdomain.com/api
FRONTEND_PORT=80
GUNICORN_WORKERS=2
```

Build-time frontend API URL:

```bash
export VITE_API_URL=https://api.yourdomain.com/api
```

## 2. Run production stack

```bash
docker compose -f docker-compose.prod.yml --env-file backend/.env.production up --build -d
```

Services:

| Service | Role |
|---------|------|
| `db` | PostgreSQL |
| `redis` | Job queue |
| `migrate` | Alembic `upgrade head` (one-shot) |
| `backend` | Gunicorn + Uvicorn workers |
| `worker` | Arq background jobs |
| `frontend` | Nginx serving static React build |

## 3. Migrations

Migrations run automatically via the `migrate` service before backend/worker start.

Manual run:

```bash
docker compose -f docker-compose.prod.yml run --rm migrate alembic upgrade head
```

## 4. Health checks

| Endpoint | Purpose |
|----------|---------|
| `GET /api/health` | Basic public health |
| `GET /api/health/live` | Liveness (process up) |
| `GET /api/health/ready` | Readiness (DB + Redis + queue) |

```bash
curl -s http://localhost:8000/api/health/ready | jq
```

Docker healthchecks use `scripts/docker_healthcheck.py` for backend and worker.

## 5. Reverse proxy & SSL

Expose only the reverse proxy on ports 80/443.

Example layout:

- `https://app.example.com` → `frontend:80`
- `https://api.example.com` → `backend:8000`

Use Let's Encrypt (Caddy automatic HTTPS or certbot with Nginx).

Do not expose PostgreSQL or Redis publicly.

## 6. Job monitoring & cleanup

List jobs (authenticated user):

```bash
curl -H "Authorization: Bearer $TOKEN" https://api.example.com/api/jobs
```

Cleanup old completed/failed jobs (requires `ADMIN_API_KEY`):

```bash
curl -X POST "https://api.example.com/api/jobs/admin/cleanup?older_than_days=30" \
  -H "X-Admin-Key: $ADMIN_API_KEY"
```

**Manual cleanup** (SQL example):

```sql
DELETE FROM research_jobs
WHERE status IN ('completed', 'failed')
  AND updated_at < NOW() - INTERVAL '30 days';
```

Document retention policy for your team and schedule cleanup via cron + admin endpoint or SQL.

## 7. Observability

Production enables JSON structured logs (`LOG_JSON=true`).

Each HTTP request logs: `request_id`, `method`, `path`, `status_code`, `duration_ms`, optional `user_id`.

Correlate client issues using the `X-Request-ID` response header.

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|----------------|-----|
| `migrate` fails: no `alembic.ini` | Old image | Rebuild: `docker compose build --no-cache migrate` |
| `ready` returns 503 database | Wrong `DATABASE_URL` / DB not up | Check `db` health, credentials |
| Redis connection errors | `REDIS_URL` typo | Use `redis://redis:6379/0` inside Compose network |
| CORS errors in browser | Origin not whitelisted | Add frontend URL to `BACKEND_CORS_ORIGINS` |
| Tavily 401 | Invalid key | Rotate `TAVILY_API_KEY`, restart backend + worker |
| App refuses to start | Weak/missing `SECRET_KEY` | Set 32+ char secret; `ENVIRONMENT=production` |
| `AUTH_MODE=disabled` error | Production guard | Set `AUTH_MODE=jwt` |
| Rate limit on login | Brute-force protection | Wait or tune `AUTH_RATE_LIMIT` |

## 9. Development vs production

| | Development | Production |
|---|-------------|------------|
| Compose file | `docker-compose.yml` | `docker-compose.prod.yml` |
| Backend server | Uvicorn (reload optional) | Gunicorn + Uvicorn workers |
| Auth | `jwt` (dev example) | `jwt` only |
| Docs | `/docs` enabled | Disabled |
| Logs | Text | JSON |

Development:

```bash
docker compose up --build
```
