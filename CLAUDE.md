# Interview Simulator — Agent Instructions

## Project Context

- **Domain:** codeswiftr-com
- **Status:** LIVE — #1 Revenue Product ($1,200 MRR at app.codeswiftr.com)
- **Stack:** FastAPI + SQLModel + PostgreSQL + Redis + React 19 + Stripe
- **Deploy:** Railway (backend) + Cloudflare Pages (frontend)
- **Last Updated:** 2026-03-21

## Entry Points

| Purpose | Location |
|---------|----------|
| Backend Entry | `backend/app/main.py` |
| Frontend Entry | `frontend/src/main.tsx` |
| Backend Config | `backend/.env.example` |
| Frontend Config | `frontend/.env.example` |
| Docker Compose | `docker-compose.yml` |
| Makefile | `Makefile` |

## Development Commands

```bash
# Setup
docker compose up -d                                  # Start PostgreSQL + Redis
cd backend && uv sync && uv run alembic upgrade head  # Migrate DB
uv run python -c "from app.data.seed_questions import seed_questions; import asyncio; asyncio.run(seed_questions())"

# Dev
cd backend && uv run uvicorn app.main:app --reload    # Backend :8000
cd frontend && npm install && npm run dev             # Frontend :5173

# Test
cd backend && uv run pytest                           # All backend tests (2,022 passing, 34 pre-existing edge failures)
cd backend && uv run pytest --cov=app --cov-report=html  # Coverage (64.2%)
cd frontend && npm test                               # Frontend unit tests
cd frontend && npm run build                          # Build check

# Quality
cd backend && ruff check .
cd backend && ruff format .
cd backend && mypy app/
```

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app factory, middleware, startup |
| `backend/app/api/` | Route handlers organized by resource |
| `backend/app/models/` | SQLModel database models (async) |
| `backend/app/services/` | Business logic layer |
| `backend/app/ai/` | OpenAI Whisper transcription + Claude feedback |
| `frontend/src/main.tsx` | React 19 app entry point |
| `frontend/src/components/` | Reusable UI components |
| `frontend/src/pages/` | Route-level page components |
| `frontend/src/hooks/` | Custom React hooks |
| `frontend/src/lib/` | API client, utilities |
| `frontend/content/blog/` | Markdown blog posts (1,219+ posts) |
| `frontend/src/pages/BlogList.tsx` | Blog engine — auto-indexes via import.meta.glob |
| `backend/app/services/stripe_service.py` | Stripe billing integration |
| `backend/.env.example` | Required env vars reference |
| `docs/PLAN.md` | Active sprint tasks and blockers |

## Architecture

```
interview-simulator/
├── backend/
│   ├── app/
│   │   ├── api/          # REST endpoints (/api/v1/interviews, /subscriptions, /teams)
│   │   ├── ai/           # Whisper transcription + Claude feedback generation
│   │   ├── models/       # SQLModel async models
│   │   ├── services/     # Business logic (interview, video, stripe, posthog)
│   │   ├── middleware/   # Rate limiting, request ID
│   │   └── main.py       # App entry point
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/   # VideoFeedbackCard, VideoRecordingDeck (feature-flagged)
│   │   ├── pages/        # Route components + BlogList.tsx
│   │   ├── hooks/
│   │   └── lib/          # API client
│   ├── content/blog/     # 1,219+ Markdown blog posts (auto-indexed)
│   └── package.json
└── docker-compose.yml
```

**Key APIs:**
- `GET/POST /api/v1/interviews` — Interview session management
- `GET/POST /api/v1/subscriptions` — Stripe billing (free/pro/team tiers)
- `GET/POST /api/v1/teams` — Team account management
- `POST /api/v1/interviews/{id}/feedback` — Claude AI feedback generation

**Billing tiers:** Free / Pro / Team (GATE-STRIPE-TEAM blocks team billing)

**Blog engine:** Markdown files in `frontend/content/blog/` are auto-indexed by `BlogList.tsx` using `import.meta.glob`. 1,219+ posts, sitemap 1,225+ URLs.

**Video features:** `VideoFeedbackCard` and `VideoRecordingDeck` are behind a feature flag — do not enable without human approval.

**Audio pipeline:** webm/mp3/wav → Whisper API → text → Claude analysis → structured feedback (5-minute max, 25MB limit).

**Analytics:** PostHog (event tracking, funnel analysis)

**Auth:** Custom JWT tokens (access + refresh), Stripe webhook signature validation.

## Quality Gates

| Gate | Tool | Threshold |
|------|------|-----------|
| Backend Tests | pytest | 2,022 passing (64.2% coverage) |
| Frontend Build | Vite | Zero build errors |
| Lint | Ruff | Zero errors |
| Type Check | mypy | Strict mode |
| Security | Bandit | High severity zero |
| API Response (p95) | — | <200ms target |
| Transcription | Whisper | <30s for 5min audio |
| Feedback Generation | Claude | <10s target |

## Human Gates

The following changes require human approval before implementation:

1. **GATE-STRIPE-TEAM** — Team billing activation (Stripe team tier keys not configured in Railway)
2. **Cloudflare Pages token** — Required for `wrangler pages deploy` frontend deployments
3. **AI Prompts** — Changes to Claude feedback generation prompts or scoring logic
4. **Audio Processing** — Changes to Whisper transcription pipeline or audio format support
5. **Subscription Tiers** — Pricing, tier limits, or feature flag changes
6. **Auth/Security** — Changes to JWT configuration or authentication flow
7. **Video Features** — Enabling VideoFeedbackCard / VideoRecordingDeck (behind feature flag)
8. **Production Deploy** — Any deployment to Railway backend or Cloudflare Pages

## Production Infrastructure

| Component | Location |
|-----------|----------|
| Backend | `interview-simulator-api-production.up.railway.app` |
| Frontend | `app.codeswiftr.com` (Cloudflare Pages) |
| Database | PostgreSQL on Railway |
| Cache | Redis on Railway |

**Deploy backend:**
```bash
cd backend && railway up
```

**Deploy frontend:**
```bash
cd frontend
npm run build   # Uses frontend/.env.production (VITE_API_URL must be https://)
wrangler pages deploy dist --project-name=interview-simulator --branch=main
```

**CRITICAL:** Vite inlines env vars at build time. Always verify `frontend/.env.production` exists with `VITE_API_URL=https://...` before building.

## Environment Variables

Required: `DATABASE_URL`, `SECRET_KEY`, `REDIS_URL`
Optional: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `STRIPE_SECRET_KEY`, `POSTHOG_API_KEY`

See `backend/.env.example` and `frontend/.env.example` for full reference.
