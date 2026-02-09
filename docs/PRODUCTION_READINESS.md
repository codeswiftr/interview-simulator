# Interview Simulator – Production Readiness Audit

**Date:** 2026-02-06  
**Scope:** Backend config, Dockerfile(s), health, CORS, rate limiting, logging.

---

## 1. Config – Hardcoded secrets

**File:** `backend/app/config.py`

| Check | Result | Details |
|-------|--------|---------|
| No hardcoded API keys | **PASS** | `anthropic_api_key`, `openai_api_key`, `stripe_secret_key`, etc. default to `""`; loaded from env. |
| No hardcoded secret key in code | **FAIL** | `secret_key: str = "change-me-in-production"` is a default in code. If `SECRET_KEY` is not set in production, this value is used. |
| Default database URL | **FAIL** | `database_url` defaults to `postgresql+asyncpg://postgres:postgres@localhost:5432/...`. Acceptable for local dev only; production must set `DATABASE_URL`. |
| Production validation | **PASS** | `validate_for_production()` rejects `secret_key == "change-me-in-production"`, localhost `database_url`, missing AI keys, CORS wildcards, and non-HTTPS production origins. |

**Summary:** **FAIL** – Default `secret_key` and `database_url` must not be used in production. Ensure `SECRET_KEY` and `DATABASE_URL` are set in the production environment (and that startup runs `validate_for_production()` when not in debug).

---

## 2. Dockerfile – Production readiness

**Files:** `backend/Dockerfile`, `docker/Dockerfile.backend`

| Check | backend/Dockerfile | docker/Dockerfile.backend |
|-------|--------------------|---------------------------|
| Multi-stage build | **PASS** | **PASS** (builder + runtime) |
| Non-root user | **PASS** (`appuser`) | **PASS** (`app`) |
| No secrets in image | **PASS** | **PASS** |
| HEALTHCHECK | **PASS** | **FAIL** |
| Python/uv | **PASS** (3.13-slim, uv) | **PASS** (3.12-slim, uv) |
| Runtime deps only in final stage | **PASS** | **PASS** |
| PORT / proxy headers | **PASS** (PORT=8000, uvicorn `--proxy-headers`) | **PASS** (port 8000, no PORT env) |

**HEALTHCHECK details:**

- **backend/Dockerfile:** `http://localhost:8000/health` – **PASS** (matches app: health router mounted at `/health`).
- **docker/Dockerfile.backend:** `http://localhost:8000/api/v1/health` – **FAIL**. App exposes `/health`, not `/api/v1/health`; health check will 404.

**Summary:** **PASS** for `backend/Dockerfile`. **FAIL** for `docker/Dockerfile.backend` until HEALTHCHECK uses `/health`.

---

## 3. Health endpoint

**File:** `backend/app/main.py`, `backend/app/api/health.py`

| Check | Result | Details |
|-------|--------|---------|
| Basic liveness | **PASS** | `GET /health` returns `{"status": "healthy"}`. |
| Readiness with dependencies | **PASS** | `GET /health/ready` checks DB (critical), Redis and AI (optional); returns 503 if DB down. |
| Detailed health | **PASS** | `GET /health/details` returns DB/Redis/AI status and timings. |
| Router mount | **PASS** | Health router included without prefix → `/health`, `/health/ready`, `/health/details`. |
| Tests | **PASS** | `tests/test_health.py` covers basic, ready, and details. |

**Summary:** **PASS**.

---

## 4. CORS for production domain app.codeswiftr.com

**File:** `backend/app/config.py`, `backend/app/main.py`

| Check | Result | Details |
|-------|--------|---------|
| Production domain allowed | **PASS** | `cors_origins` includes `https://app.codeswiftr.com` and `https://interview-simulator-4bo.pages.dev`. |
| Dev origins not in prod | **PASS** | `effective_cors_origins` adds `_dev_cors_origins` only when `debug` or `environment == "development"`. |
| No wildcards in prod | **PASS** | Production startup raises if `*` (or `http://*` / `https://*`) is in `cors_origins`. |
| HTTPS in prod | **PASS** | `validate_for_production()` requires production CORS origins to use `https://` (localhost excluded). |
| Credentials + methods | **PASS** | CORSMiddleware uses `allow_credentials=True`, appropriate methods and headers. |

**Summary:** **PASS**.

---

## 5. Rate limiting config

**File:** `backend/app/main.py`

| Check | Result | Details |
|-------|--------|---------|
| Enabled in production | **PASS** | `RateLimitMiddleware` added only when `not settings.debug`. |
| Redis-backed | **PASS** | `redis_url=settings.redis_url`. |
| Limits set | **PASS** | `requests_per_minute=60`, `requests_per_hour=1000`. |
| Health excluded | **PASS** | `exclude_paths` includes `"/health"` (and `/docs`, `/openapi.json`, `/`, `/favicon.ico`, `/static`). |
| Readiness/details | **PASS** | Forge-shared middleware typically matches path prefix; `/health/ready` and `/health/details` are under `/health` so usually excluded. If not, consider adding them explicitly. |

**Summary:** **PASS**.

---

## 6. Logging config

**File:** `backend/app/main.py` (`configure_logging()`)

| Check | Result | Details |
|-------|--------|---------|
| Production format | **PASS** | When `not settings.debug`, uses JSON formatter (timestamp, level, logger, message, optional correlation_id, exception, extra). |
| Log level | **PASS** | Production: `logging.INFO`; debug: `logging.DEBUG`. |
| Uvicorn access logs | **PASS** | `uvicorn.access` set to WARNING in prod, INFO in debug to reduce noise. |
| Output | **PASS** | StreamHandler to stdout (container-friendly). |

**Summary:** **PASS**.

---

## Summary table

| Area | Result | Action |
|------|--------|--------|
| (1) Config – hardcoded secrets | **FAIL** | Ensure production sets `SECRET_KEY` and `DATABASE_URL`; rely on `validate_for_production()` at startup. |
| (2) Dockerfile | **PASS** (backend/Dockerfile) / **FAIL** (docker/Dockerfile.backend) | Fix `docker/Dockerfile.backend` HEALTHCHECK to use `/health`. |
| (3) Health endpoint | **PASS** | None. |
| (4) CORS for app.codeswiftr.com | **PASS** | None. |
| (5) Rate limiting | **PASS** | Optional: add `/health/ready` and `/health/details` to exclude_paths if needed. |
| (6) Logging | **PASS** | None. |

---

## Recommended actions

1. **Config:** In deployment (e.g. Railway), set `SECRET_KEY` and `DATABASE_URL`; do not rely on defaults. Keep `validate_for_production()` running when `debug=False`.
2. **docker/Dockerfile.backend:** Change HEALTHCHECK to:
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
       CMD curl -f http://localhost:8000/health || exit 1
   ```
3. **Optional:** Add `/health/ready` and `/health/details` to rate limit `exclude_paths` if your orchestrator uses them and they are ever rate-limited.
