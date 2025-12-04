# Agent Continuation Prompt

## Project Overview
**Project**: CareerSwiftr Interview Simulator
**Purpose**: AI-powered interview practice platform for software engineers with multimodal feedback analysis
**Tech Stack**: FastAPI + SQLModel + PostgreSQL (backend), React 19 + Vite + TailwindCSS v4 (frontend), OpenAI Whisper + Claude/OpenRouter + Librosa (AI)
**Repository**: `/Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator`

---

## Current State

### Branch
`main` - Production-ready code with Sprint 2 epics complete

### Recent Progress (Sprint 2 Complete)
- Epic 1: Company targeting + readiness scoring
- Epic 2: Expanded question bank (50 technical, 25 system design, 30 behavioral = 105 total)
- Epic 3: JWT refresh token system with token rotation
- Epic 4: Backend test coverage improved (140 tests, 66% coverage)
- Personalized feedback based on experience level
- Sample answer modal on FeedbackPage
- Improvement comparison vs user average

### Current Focus
**Codebase Audit & Quality Strategy** - Identify remaining gaps and create bottom-up testing strategy to achieve 75% coverage target.

### Blockers/Issues
- None - all tests passing, application working

---

## Codebase Audit Report

### Executive Summary
**Overall Health**: Good
**Test Coverage**: 66% (target: 75%)
**Documentation**: Complete
**Technical Debt**: Low-Medium

---

### Capabilities Inventory

#### Core Features
| Feature | Status | Test Coverage | Notes |
|---------|--------|---------------|-------|
| User Authentication | Working | 86% | JWT access + refresh tokens |
| Interview Sessions | Working | 40% | Create, start, end workflow |
| Audio Recording | Working | 63% | WebM format, upload to backend |
| AI Transcription | Working | 93% | OpenAI Whisper / Groq |
| AI Content Analysis | Working | 94% | Claude via Anthropic/OpenRouter |
| Audio Analysis | Working | 78% | Librosa-based quality metrics |
| Feedback Generation | Working | 39% | Async background tasks |
| Experience-Level Personalization | Working | 94% | Junior/mid/senior context |
| Company Targeting | Working | 58% | Filter by company tags |
| Readiness Score | Working | N/A | Calculated from last 5 sessions |
| Stripe Subscriptions | Working | 40% | Checkout, portal, webhooks |
| Sample Answers | Working | N/A | Modal display on feedback page |
| Progress Tracking | Working | N/A | Score trend, improvement % |

#### APIs
| Endpoint Category | Methods | Status | Tests |
|-------------------|---------|--------|-------|
| `/users/*` | POST, GET, PATCH, DELETE | Working | Partial |
| `/auth/*` | POST (refresh, forgot, reset) | Working | Partial |
| `/interviews/*` | CRUD + start/end | Working | Partial |
| `/questions/*` | GET, random | Working | 74% |
| `/feedback/*` | GET, generate | Working | 39% |
| `/subscriptions/*` | GET, POST, webhooks | Working | 40% |
| `/upload/*` | POST audio | Working | 63% |
| `/transcription/*` | POST | Working | 93% |
| `/health/*` | GET | Working | 79% |

#### Integrations
| Integration | Status | Notes |
|-------------|--------|-------|
| PostgreSQL | Working | Async SQLModel |
| Redis | Working | Rate limiting, caching |
| Stripe | Working | Subscriptions, webhooks |
| OpenAI Whisper | Working | Primary transcription |
| Groq Whisper | Working | Fallback transcription |
| Claude (Anthropic) | Working | Content analysis |
| OpenRouter | Working | Fallback content analysis |

---

### Architecture Assessment

#### Backend Module Structure
```
backend/app/
├── api/              # 9 route files - Mixed coverage (33-93%)
│   ├── auth.py       # 40% - Password reset flows untested
│   ├── feedback.py   # 39% - Multiple endpoints untested
│   ├── health.py     # 79% - Good coverage
│   ├── interviews.py # 40% - CRUD operations partially tested
│   ├── questions.py  # 74% - Good coverage
│   ├── subscriptions.py # 40% - Stripe flows need more tests
│   ├── transcription.py # 41% - API endpoint needs tests
│   ├── upload.py     # 63% - Decent coverage
│   └── users.py      # 52% - Profile updates need tests
├── ai/               # 3 modules - Good coverage (78-94%)
│   ├── audio_analyzer.py  # 78%
│   ├── content_analyzer.py # 94%
│   └── transcriber.py     # 93%
├── models/           # 6 models - 100% coverage
├── services/         # 5 services - Mixed (58-97%)
│   ├── audio_service.py      # 97%
│   ├── background_tasks.py   # 69%
│   ├── email_service.py      # 89%
│   ├── feedback_service.py   # 63%
│   └── interview_service.py  # 58%
├── middleware/       # 33% - Rate limiting untested
└── main.py           # 46% - App setup partially tested
```

#### Frontend Structure
```
frontend/src/
├── pages/            # 10 pages
├── components/       # 50+ components (6 categories)
├── hooks/            # 4 custom hooks
├── lib/              # API client, utilities
├── contexts/         # Theme management
└── types/            # TypeScript definitions
```

#### Dependency Concerns
- None critical identified

#### Entry Points
| Entry Point | Type | Health |
|-------------|------|--------|
| `main.py` | FastAPI | Working |
| `App.tsx` | React | Working |

---

### Quality Metrics

#### Test Coverage by Module (Backend)
| Module | Stmts | Miss | Cover | Target | Gap |
|--------|-------|------|-------|--------|-----|
| app/models/* | 323 | 0 | 100% | 100% | - |
| app/ai/content_analyzer.py | 65 | 4 | 94% | 90% | - |
| app/ai/transcriber.py | 57 | 4 | 93% | 90% | - |
| app/services/audio_service.py | 70 | 2 | 97% | 80% | - |
| app/ai/audio_analyzer.py | 108 | 24 | 78% | 80% | +2% |
| app/api/questions.py | 53 | 14 | 74% | 75% | +1% |
| app/services/background_tasks.py | 127 | 40 | 69% | 75% | +6% |
| app/api/upload.py | 43 | 16 | 63% | 75% | +12% |
| app/services/feedback_service.py | 158 | 59 | 63% | 75% | +12% |
| app/services/interview_service.py | 67 | 28 | 58% | 75% | +17% |
| app/api/users.py | 110 | 53 | 52% | 75% | +23% |
| app/main.py | 116 | 63 | 46% | 60% | +14% |
| app/api/transcription.py | 56 | 33 | 41% | 75% | +34% |
| app/api/interviews.py | 148 | 89 | 40% | 75% | +35% |
| app/api/auth.py | 70 | 42 | 40% | 75% | +35% |
| app/api/subscriptions.py | 202 | 121 | 40% | 75% | +35% |
| app/api/feedback.py | 85 | 52 | 39% | 75% | +36% |
| app/middleware/rate_limit.py | 60 | 40 | 33% | 50% | +17% |
| app/data/seed_questions.py | 9 | 6 | 33% | N/A | - |

**Overall**: 2162 stmts, 727 miss, **66%** (target: 75%)

#### Frontend Test Coverage
| Suite | Tests | Status |
|-------|-------|--------|
| Button.test.tsx | 3 | Passing |
| msw-integration.test.tsx | 3 | Passing |
| **Total** | 6 | Passing |

#### Technical Debt Items
| Item | Impact | Effort to Fix |
|------|--------|---------------|
| Low API test coverage (39-52%) | Medium | High |
| Middleware untested | Low | Low |
| Rate limiter not integration tested | Medium | Medium |
| Frontend minimal test coverage | Medium | High |

---

### Gap Analysis

#### Critical Gaps (Priority 1)
1. **API endpoint coverage < 50%**: auth.py, feedback.py, interviews.py, subscriptions.py
   - Impact: Regressions undetected
   - Recommendation: Add integration tests for all CRUD operations

2. **Rate limiter untested (33%)**:
   - Impact: Could allow abuse or break valid requests
   - Recommendation: Add unit tests for rate limiting logic

#### Important Gaps (Priority 2)
1. **Interview service coverage (58%)**:
   - Impact: Question assignment bugs undetected
   - Recommendation: Test company filtering, difficulty balancing

2. **Feedback service coverage (63%)**:
   - Impact: AI feedback generation issues undetected
   - Recommendation: Test async flow, error handling

3. **Upload API coverage (63%)**:
   - Impact: File handling issues undetected
   - Recommendation: Test file validation, storage

#### Minor Gaps (Priority 3)
1. **Frontend test coverage minimal**:
   - Impact: UI bugs undetected
   - Recommendation: Add component tests for critical flows

2. **main.py coverage (46%)**:
   - Impact: App startup issues undetected
   - Recommendation: Test lifespan events, middleware setup

---

### Question Bank Status
| Category | Count | Sample Answers | With Tags |
|----------|-------|----------------|-----------|
| Behavioral | 30 | 0 | 30 |
| Technical | 50 | 0 | 50 |
| System Design | 25 | 0 | 25 |
| **Total** | **105** | **0** | **105** |

---

### Testing Strategy (Bottom-Up)

```
┌─────────────────────────────────────────┐
│            Testing Pyramid              │
├─────────────────────────────────────────┤
│              /\      E2E Tests         │
│             /  \     (Full flow)        │
│            /────\                       │
│           /      \   API Tests          │
│          /────────\  (Endpoints)        │
│         /          \ Integration        │
│        /────────────\(Services)         │
│       /              \ Unit Tests       │
│      /────────────────\(Core logic)     │
│     (Foundation - Most coverage here)   │
└─────────────────────────────────────────┘
```

#### Phase 1: Foundation (Unit Tests) - Target +5%
| Component | Current | Target | Priority | Est. Effort |
|-----------|---------|--------|----------|-------------|
| middleware/rate_limit.py | 33% | 60% | P0 | 1h |
| services/interview_service.py | 58% | 75% | P1 | 2h |
| services/feedback_service.py | 63% | 75% | P1 | 1.5h |

#### Phase 2: API Integration Tests - Target +6%
| Endpoint | Current | Target | Priority | Est. Effort |
|----------|---------|--------|----------|-------------|
| api/feedback.py | 39% | 75% | P0 | 2h |
| api/interviews.py | 40% | 75% | P0 | 2h |
| api/auth.py | 40% | 75% | P1 | 1.5h |
| api/subscriptions.py | 40% | 60% | P2 | 2h |
| api/users.py | 52% | 75% | P1 | 1h |

#### Phase 3: E2E Integration Tests
| Journey | Tested | Priority |
|---------|--------|----------|
| Register → Interview → Feedback | Partial | P0 |
| Subscription checkout → upgrade | Partial | P1 |
| Token refresh flow | Minimal | P1 |

---

### Opportunities

#### Quick Wins (High Impact, Low Effort)
1. **Add rate_limit.py tests** - 1 hour, reduces risk of abuse
2. **Add missing auth endpoint tests** - 1.5 hours, password reset coverage
3. **Add sample answers to top 20 questions** - Content improvement

#### Strategic Improvements
1. **Standardize test fixtures** - Create reusable factories for users, interviews, responses
2. **Add MSW handlers for all API endpoints** - Enable frontend testing
3. **Add GitHub Actions CI** - Automated test runs on PR

---

### Recommended Action Plan

#### Immediate (This Session)
1. Add tests for `api/feedback.py` endpoints (39% → 60%)
2. Add tests for `api/interviews.py` endpoints (40% → 60%)
3. Add tests for `middleware/rate_limit.py` (33% → 60%)

#### Short-term (Next Sprint)
1. Complete API coverage to 75% across all modules
2. Add sample answers to behavioral questions
3. Implement proper fixtures/factories for tests

#### Long-term (Roadmap)
1. Frontend component testing with Vitest + RTL
2. E2E tests with Playwright
3. Performance benchmarking suite

---

### Documentation Status

| Document | Status | Action Needed |
|----------|--------|---------------|
| README.md | Up to date | - |
| PLAN.md | Up to date | Mark completed epics |
| PROMPT.md | Updated | This document |
| DEPLOYMENT.md | Up to date | - |
| DESIGN_SYSTEM.md | Up to date | - |

---

## Commands to Run

### Verify Environment
```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend
uv run pytest -q --tb=no  # Should show 140 passed
```

### Run Backend
```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
```

### Run Frontend
```bash
cd frontend && npm run dev
```

### Run Tests with Coverage
```bash
cd backend && uv run pytest --cov=app --cov-report=term-missing
```

---

## Resume Command

To continue work, start with:
```
Read docs/PROMPT.md and docs/PLAN.md. Run tests with `uv run pytest -q --tb=no` (expect 140 passed).
Focus on increasing test coverage to 75%. Start with api/feedback.py and api/interviews.py.
DO NOT STOP! Continue with the plan like an empowered, pragmatic senior engineer.
```
