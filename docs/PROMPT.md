# Agent Continuation Prompt

## Project Overview
**Project**: CareerSwiftr Interview Simulator
**Purpose**: AI-powered interview practice platform with audio recording, transcription, and personalized feedback
**Tech Stack**: Python 3.13+/FastAPI/SQLModel/PostgreSQL (backend) | React 19/TypeScript/Vite 7/TailwindCSS (frontend)
**Repository**: /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator

---

## Current State

### Branch
`main` - Production branch, Sprint 4 complete

### Recent Progress
- `9b63833` docs: mark Sprint 4 complete with final metrics
- `f2b7a6a` test: add comprehensive hook tests and expand MSW mock infrastructure
- `b3db554` test: increase backend test coverage from 67% to 69%
- `867615a` fix(frontend): resolve all ESLint errors (28 to 0)
- `313c800` fix(backend): resolve all ruff linting errors (158 to 0)

### Current Focus
**Sprint 4: Technical Debt Payback** - COMPLETE (Epics 1-3 Done)

### Blockers/Issues
- None - codebase clean, tests passing

---

## Active Plan
**Plan File**: `docs/PLAN.md`
**Current Phase**: Sprint 4 Complete
**Status**: Ready for next sprint

### Completed (Sprint 4)
- [x] Epic 1: Fix Linting Errors (158 backend + 28 frontend to 0)
- [x] Epic 2: Backend Test Coverage (67% to 69%, 219 tests)
- [x] Epic 3: Frontend Test Infrastructure (55 tests, hooks 100%)
- [x] Epic 4: E2E Test Suite (Deferred to future sprint)

### Future Work
1. **Frontend Component Tests** - Add tests for pages and components
2. **API Endpoint Test Coverage** - Reach 75% on remaining modules
3. **E2E Test Suite** - Playwright for critical user journeys
4. **Performance Optimization** - Code splitting, bundle optimization

---

## Key Context

### Important Files
| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI application entry point |
| `backend/app/api/` | API routers (8 modules) |
| `backend/tests/` | Backend test suite (219 tests, 69% coverage) |
| `frontend/src/hooks/` | React hooks (4 hooks, 3 fully tested) |
| `frontend/src/hooks/__tests__/` | Hook tests (49 tests) |
| `frontend/src/test/mocks/handlers.ts` | MSW handlers (40+ endpoints) |
| `frontend/src/pages/` | Page components (10 pages) |
| `docs/PLAN.md` | Sprint implementation plans |
| `docs/CODEBASE_AUDIT.md` | Current codebase metrics |

### Current Coverage
| Module | Coverage | Status |
|--------|----------|--------|
| Backend Overall | 69% | Good |
| `middleware/rate_limit.py` | 100% | Excellent |
| `hooks/useAuth` | 100% | Excellent |
| `hooks/useToast` | 100% | Excellent |
| `hooks/useOnboarding` | 100% | Excellent |
| `api/interviews.py` | 41% | Needs work |
| `api/transcription.py` | 42% | Needs work |

### Recent Decisions
- **B008 ruff ignore**: Added to pyproject.toml for FastAPI Depends() pattern
- **ESLint disable comments**: Used for react-refresh/only-export-components in hook files
- **useCallback pattern**: Used for functions referenced in useEffect dependencies

### Gotchas Discovered
- Port 5432 may conflict with other PostgreSQL instances (postgres-db container)
- Frontend useEffect dependencies require useCallback for function stability
- Backend Depends() pattern triggers B008 linting rule - ignore is correct

### Patterns to Follow
- **Backend tests**: Use pytest-asyncio, mock external services
- **Frontend tests**: Vitest + RTL + MSW, wrap with providers
- **Commits**: Conventional format with scope (e.g., `fix(backend): ...`)
- **Coverage**: Focus on API endpoints and components

---

## Commands to Run

### Verify Environment
```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator
docker compose up -d  # Start PostgreSQL and Redis
cd backend && uv run alembic upgrade head  # Run migrations
```

### Run Tests
```bash
# Backend tests with coverage
cd backend && uv run pytest --cov=app --cov-report=term-missing -v

# Frontend tests
cd frontend && npm test

# Linting (should be clean)
cd backend && uv run ruff check app/
cd frontend && npm run lint
```

### Start Development
```bash
# Backend (port 8000)
cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (port 5173)
cd frontend && npm run dev
```

---

## Instructions for New Agent

### Mindset
You are a pragmatic senior engineer. Your approach:
- Apply Pareto principle - 20% effort for 80% value
- Test-driven development for business logic
- YAGNI - don't build what isn't needed
- Clean architecture with clear separation

### Workflow
1. Read this context and the plan file (`docs/PLAN.md`)
2. Run tests to verify current state: `cd backend && uv run pytest`
3. Identify next priority from remaining work
4. Commit after each completed task
5. Update docs as you progress

### Quality Gates
After each change:
1. Run affected tests: `uv run pytest tests/test_<module>.py -v`
2. Check coverage: `uv run pytest --cov=app/<module>.py`
3. Verify linting: `uv run ruff check app/`
4. Commit with conventional message
5. Continue to next task

---

## Current Metrics

| Metric | Value |
|--------|-------|
| Backend Tests | 219 (215 passed, 4 skipped) |
| Backend Coverage | 69% |
| Frontend Tests | 55 |
| Frontend Hook Coverage | 100% (3/4 hooks) |
| Linting Errors | 0 (backend + frontend) |
| MSW Handlers | 40+ |
| Questions with Sample Answers | 60 |

---

## Resume Command

To continue work, start with:
```
Read docs/PROMPT.md and docs/PLAN.md. Sprint 4 is complete.
Verify tests pass, then evaluate priorities for next sprint.
Consider: frontend component tests, API coverage to 75%, E2E tests, or new features.
DO NOT STOP! Continue like an empowered, pragmatic senior engineer.
```
