# Agent Continuation Prompt

## Project Overview
**Project**: CareerSwiftr Interview Simulator
**Purpose**: AI-powered interview practice platform for software engineers with multimodal feedback analysis
**Tech Stack**: FastAPI + SQLModel + PostgreSQL (backend), React 19 + Vite + TailwindCSS v4 (frontend), OpenAI Whisper + Claude/OpenRouter + Librosa (AI)
**Repository**: `/Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator`

---

## Current State

### Branch
`main` - Production-ready soft launch code

### Recent Progress
- ✅ Stripe subscription flow working (checkout, cancel, sync, resubscribe)
- ✅ New Stripe API compatibility fixed (current_period_end on subscription item)
- ✅ Cancel subscription UI properly detects scheduled cancellation
- ✅ Test suite fully passing (95/95 tests, 66% coverage)
- ✅ Dark mode with system detection
- ✅ Mobile navigation (hamburger menu)
- ✅ Branded assets integrated (logo, hero, OG images)
- ✅ Comprehensive codebase audit completed

### Current Focus
**Post-Launch Value Optimization** - The platform is feature-complete but under-delivering on core value. The audit identified that feedback is too generic and lacks personalization/progress tracking.

### Blockers/Issues
- None - all tests passing, application working

---

## Active Plan
**Plan File**: `docs/PLAN.md`
**Current Phase**: Post-Launch Optimization
**Current Task**: Implement "Feedback That Helps" sprint
**Status**: Ready to start

### Immediate Next Steps (High Value, Low Effort)
1. Add `experience_level` field to User model (junior/mid/senior)
2. Update registration form to collect experience level
3. Update Claude prompt to adjust expectations by level
4. Add score history endpoint (last 10 sessions)
5. Add score trend chart to DashboardPage
6. Show "improvement %" on FeedbackPage

---

## Key Context

### Important Files
| File | Purpose |
|------|---------|
| `backend/app/models/user.py` | User model - add experience_level here |
| `backend/app/ai/content_analyzer.py` | Claude prompts - personalize by level |
| `backend/app/api/users.py` | User endpoints - add stats history |
| `frontend/src/pages/DashboardPage.tsx` | Dashboard - add trend chart |
| `frontend/src/pages/FeedbackPage.tsx` | Feedback - add improvement % |
| `backend/app/data/seed_questions.py` | Question bank - needs sample answers |
| `docs/PLAN.md` | Implementation plan |

### Recent Decisions
- **OpenRouter for content analysis**: Using claude-haiku-4.5 via OpenRouter for cost efficiency
- **Stripe subscription item access**: New Stripe API (2025-11-17) moved current_period_end to subscription item
- **Anthropic provider for tests**: Tests use mock_settings fixture to force anthropic provider

### Gotchas Discovered
- ⚠️ Stripe API changed: `subscription["items"]["data"][0]["current_period_end"]` not `subscription.current_period_end`
- ⚠️ Stripe cancel sets `cancel_at_period_end=true` but keeps `status="active"` - must check both
- ⚠️ ContentAnalyzer uses `anthropic_client` or `openrouter_client` based on provider setting
- ⚠️ Frontend dark mode uses hex CSS variables, not @theme references

### Patterns to Follow
- **Conventional commits**: `feat(scope):`, `fix(scope):`, `chore(scope):`
- **Alembic migrations**: `uv run alembic revision --autogenerate -m "description"`
- **Test async**: Use `pytest.mark.asyncio` and AsyncMock
- **API response models**: Use Pydantic BaseModel for all endpoints

### Things to Avoid
- ❌ Don't use `analyzer.client` - use `analyzer.anthropic_client` or `analyzer.openrouter_client`
- ❌ Don't access Stripe subscription object as dict directly - check Stripe library version
- ❌ Don't commit without running tests first
- ❌ Don't add features - focus on making existing feedback more valuable

---

## Codebase Audit Summary

### Value Delivery Gaps (Priority Order)
1. **No sample answers** - Users can't see what good looks like (0/75 questions have samples)
2. **Generic feedback** - Same advice for junior and senior engineers
3. **No progress tracking** - Users don't know if they're improving
4. **Filler detection too simple** - Context-free string matching
5. **No company customization** - Generic vs "FAANG-ready" feedback

### Question Bank Status
| Category | Count | Sample Answers |
|----------|-------|----------------|
| Behavioral | 30 | 0 |
| Technical | 20 | 0 |
| System Design | 25 | 0 |

### Test Coverage
- 95 tests passing
- 66% line coverage
- Key modules: content_analyzer (90%), subscriptions (80%), interviews (70%)

---

## Commands to Run

### Verify Environment
```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend
uv run pytest -q --tb=no  # Should show 95 passed
```

### Run Backend
```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
```

### Run Frontend
```bash
cd frontend && npm run dev
```

### Create Migration
```bash
cd backend && uv run alembic revision --autogenerate -m "add experience level"
```

---

## Instructions for New Agent

### Mindset
You are a pragmatic senior engineer optimizing for **user outcomes**, not features. The platform works - now make it genuinely helpful for interview prep.

Focus on:
- **Personalization** - Feedback adjusted to user's experience level
- **Progress visibility** - Show users they're improving
- **Actionable guidance** - Specific examples, not generic advice

### Workflow
1. Read this context and `docs/PLAN.md`
2. Run tests to verify current state: `uv run pytest -q --tb=no`
3. Start with Task 1: Add `experience_level` to User model
4. Commit after each completed task
5. Update plan status as you progress

### Quality Gates
After each change:
1. Run affected tests
2. Ensure no regressions
3. Commit with conventional message
4. Continue to next task

### If Stuck
- Check `backend/tests/` for expected behavior patterns
- Use Stripe docs for subscription questions
- Check `app/ai/content_analyzer.py` for Claude prompt structure
- Review recent commits for similar changes

---

## Resume Command

To continue work, start with:
```
Read docs/PROMPT.md and docs/PLAN.md, verify tests pass with `uv run pytest -q --tb=no`, then begin Sprint: "Feedback That Helps" - Task 1: Add experience_level field to User model.
DO NOT STOP! Continue with the plan like an empowered, pragmatic senior engineer.
```
