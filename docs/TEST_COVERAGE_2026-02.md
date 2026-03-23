# Interview Simulator Test Coverage Report

**Date:** 2026-02-10  
**Last Verified:** 2026-02-10  
**Task:** T3.3 – Test Coverage Analysis  
**Reference:** `docs/interview-sim-repomix-2026-02.md`, `backend/TEST_COVERAGE_REPORT.md`, `backend/TEST_COVERAGE_SUMMARY.md`

---

## Executive Summary

Interview Simulator backend has **~67% total coverage** baseline (Jan 2026). Coverage varies by layer: high in services (interview, video, email), low in API routes and middleware. Main gaps are modules under 70% coverage and critical paths that lack tests.

---

## Coverage by Layer

| Layer | Status | Notes |
|-------|--------|------|
| **Services** | Good | interview_service 100%, video_service 70%+, others improved |
| **API Routes** | 23–40% | DB-dependent; many skipped when DB unavailable |
| **AI Modules** | 61–79% | content_analyzer blocked by LLMClient mock failures |
| **Middleware** | 0–35% | security_headers 0%, dependencies 35% |
| **Models** | Near 100% | Core schemas well covered |

---

## Modules Under 70% (Priority Gaps)

### Critical (Blocking / High Impact)

| Module | Est. Coverage | Statements | Priority |
|--------|---------------|------------|----------|
| `app/api/subscriptions.py` | 23% | Stripe integration | P0 |
| `app/api/users.py` | 25% | User management | P0 |
| `app/api/interviews.py` | 28% | Core interview flow | P0 |
| `app/api/coaching.py` | 28% | AI feedback | P0 |
| `app/api/feedback.py` | 30% | Session feedback | P0 |
| `app/middleware/security_headers.py` | ~80% | Unit tests in `tests/middleware/test_security_headers_unit.py` (prod + debug modes) | P2 |

### Medium (User-Facing)

| Module | Est. Coverage | Notes |
|--------|---------------|-------|
| `app/api/preparation.py` | 33% | Prep pipeline |
| `app/api/questions.py` | 34% | Question bank |
| `app/api/upload.py` | 37% | Media uploads |
| `app/api/auth.py` | 38% | Auth flows |
| `app/ai/content_analyzer.py` | 61% | Blocked by failing tests |

---

## Critical Paths Untested

1. **Stripe webhook flow** – signature verification, subscription lifecycle
2. **Auth** – refresh token rotation, password reset, token expiry
3. **Interview lifecycle** – create → assign questions → submit response → end
4. **Security headers** – CSP, HSTS, X-Frame-Options (tests exist in `test_security_headers_unit.py`)
5. **Content analyzer** – LLM integration (tests fail due to `LLMClient.messages` removal)

---

## Known Blockers

### 1. ContentAnalyzer Tests (12 failures)

```
AttributeError: 'LLMClient' object has no attribute 'messages'
```

**Fix:** Update mocks in `tests/test_content_analyzer.py` to match current LLM client interface.

### 2. DB-Dependent Tests Skipped

Many integration tests skip when `TEST_DATABASE_URL` / `DATABASE_URL` is not set. Use `scripts/run_coverage.sh` or ensure Postgres is running (e.g. `docker-compose up -d postgres`) before running coverage.

---

## Recommendations

### Immediate (P0)

1. **Fix ContentAnalyzer mocks** – Align with current LLM client API.
2. **SecurityHeadersMiddleware** – ✅ Unit tests exist (`test_security_headers_unit.py`).
3. **Run DB-backed tests** – Use `scripts/run_coverage.sh` for full coverage.

### Short Term (P1)

4. **Auth integration tests** – Login, refresh, password reset paths.
5. **Stripe webhook tests** – Signature verification, subscription events.
6. **Preparation pipeline** – Detective → draft → practice → completion.

### Long Term (P2)

7. **API route coverage** – Integrate tests for subscriptions, users, interviews.
8. **Audit logging** – Tests for sensitive operation logging.

---

## Run Commands

```bash
# Full coverage (requires PostgreSQL)
cd codeswiftr-com/interview-simulator/backend
./scripts/run_coverage.sh

# Or manually
docker-compose up -d postgres
uv run pytest --cov=app --cov-report=term-missing --cov-report=html

# Single module
uv run pytest tests/test_video_service_unit.py -v
```

---

## Coverage Artifacts

- **HTML:** `backend/htmlcov/index.html`
- **JSON:** `backend/coverage.json`
- **Terminal:** `uv run pytest --cov=app --cov-report=term-missing`

---

**Status:** Document complete.  
**Verification:** Run `./scripts/run_coverage.sh` (requires Postgres) for full coverage; `uv run pytest` passes when DB is available. Security headers middleware has unit tests (prod + debug modes).
