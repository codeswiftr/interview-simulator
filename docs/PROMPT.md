# Agent Continuation Prompt

## Project Overview
**Project**: CareerSwiftr Interview Simulator
**Purpose**: AI-powered interview practice platform with audio recording, transcription, and personalized feedback
**Tech Stack**: Python 3.13+/FastAPI/SQLModel/PostgreSQL (backend) | React 19/TypeScript/Vite 7/TailwindCSS (frontend)
**Repository**: /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator

---

## Current State

### Branch
`main` - Production branch, all Sprint 4 work committed

### Recent Progress
- `3560535` docs: update PLAN.md and CODEBASE_AUDIT.md - Epic 1 complete
- `867615a` fix(frontend): resolve all ESLint errors (28 to 0)
- `313c800` fix(backend): resolve all ruff linting errors (158 to 0)
- `9bcbad9` docs: add Sprint 4 technical debt payback plan
- `4a73002` docs: update codebase audit with December 2025 metrics

### Current Focus
**Sprint 4: Technical Debt Payback** - Epic 1 Complete, Epic 2 and 3 pending

### Blockers/Issues
- None currently - servers running, codebase clean

---

## Active Plan
**Plan File**: `docs/PLAN.md`
**Current Phase**: Sprint 4: Technical Debt Payback
**Current Task**: Epic 2: Backend Test Coverage to 75%
**Status**: Ready for next

### Completed
- [x] Epic 1: Fix Linting Errors (158 backend + 28 frontend to 0)

### Immediate Next Steps
1. **Epic 2: Backend Test Coverage to 75%** (~8.5h)
   - Phase 1: Feedback API Tests (2h) - target 44% to 75%
   - Phase 2: Interviews API Tests (2h) - target 40% to 75%
   - Phase 3: Auth API Tests (1.5h) - target 40% to 75%
   - Phase 4: Rate Limiting Tests (1h) - target 33% to 60%
   - Phase 5: Service Layer Tests (2h)

2. **Epic 3: Frontend Test Infrastructure** (~12h)
   - Phase 1: Test Infrastructure Setup (2h)
   - Phase 2: Hook Tests (4h) - useAuth, useAudioRecording, useToast, useOnboarding
   - Phase 3: Critical Page Tests (6h) - Login, Register, Dashboard, Feedback

3. **Epic 4: E2E Test Suite** (Deferred)

---

## Key Context

### Important Files
| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI application entry point |
| `backend/app/api/` | API routers (8 modules) |
| `backend/tests/` | Backend test suite (188 tests, 67% coverage) |
| `frontend/src/hooks/` | React hooks (4 hooks, 0% coverage) |
| `frontend/src/pages/` | Page components (10 pages) |
| `frontend/src/test/` | Frontend test infrastructure (Vitest + RTL + MSW) |
| `docs/PLAN.md` | Sprint 4 implementation plan |
| `docs/CODEBASE_AUDIT.md` | Current codebase metrics |

### Coverage Gaps (Priority Order)
| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| `api/feedback.py` | 44% | 75% | P0 |
| `api/interviews.py` | 40% | 75% | P0 |
| `api/auth.py` | 40% | 75% | P0 |
| `middleware/rate_limit.py` | 33% | 60% | P1 |
| `services/interview_service.py` | 58% | 75% | P1 |
| Frontend hooks | 0% | 80% | P0 |

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
- **Coverage**: Focus on API endpoints and hooks first

### Things to Avoid
- Don't run `ruff check` without `--fix` flag initially
- Don't forget to add `from None` on exception re-raises (B904)
- Don't skip useCallback for functions used in useEffect deps
- Don't create E2E tests yet (deferred to Epic 4)

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

### Check Coverage by Module
```bash
cd backend && uv run pytest --cov=app --cov-report=term-missing -v 2>&1 | grep -E "^app/"
```

---

## Instructions for New Agent

### Mindset
You are a pragmatic senior engineer continuing implementation. Your approach:
- Apply Pareto principle - 20% effort for 80% value
- Test-driven development for business logic
- YAGNI - don't build what isn't needed
- Clean architecture with clear separation

### Workflow
1. Read this context and the plan file (`docs/PLAN.md`)
2. Run tests to verify current state: `cd backend && uv run pytest`
3. Continue from Epic 2, Phase 1 (Feedback API Tests)
4. Commit after each completed phase
5. Update plan status as you progress

### Quality Gates
After each change:
1. Run affected tests: `uv run pytest tests/test_<module>.py -v`
2. Check coverage increased: `uv run pytest --cov=app/api/<module>.py`
3. Commit with conventional message
4. Continue to next task

### Test Writing Strategy
For backend API tests:
1. Read the endpoint code to understand paths
2. Create test cases for: happy path, validation errors, auth failures, 404s
3. Use existing fixtures from `conftest.py`
4. Mock external services (Stripe, OpenAI, Claude)

For frontend hook tests:
1. Create test wrappers with providers (AuthProvider, ToastProvider)
2. Use MSW for API mocking
3. Test state transitions and error handling

### If Stuck
- Use `/debug` for complex issues
- Use `/feedback` to review approach
- Check related tests for expected behavior
- Ask for clarification if requirements unclear

---

## Current Metrics

| Metric | Value |
|--------|-------|
| Backend Tests | 188 (184 passed, 4 skipped) |
| Backend Coverage | 67% |
| Frontend Tests | 6 |
| Frontend Coverage | 0% |
| Linting Errors | 0 (backend + frontend) |
| Questions with Sample Answers | 60 |

---

## Resume Command

To continue work, start with:
```
Read docs/PROMPT.md and docs/PLAN.md, verify tests pass, then continue with Epic 2: Backend Test Coverage to 75%.
Start with Phase 1: Feedback API Tests - increase api/feedback.py from 44% to 75%.
DO NOT STOP! Continue with the plan like an empowered, pragmatic senior engineer.
```
