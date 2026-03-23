# Agent Continuation Prompt

## Project Overview
**Project**: Interview Simulator
**Purpose**: AI-powered interview practice platform for software engineers with real-time audio analysis, transcription, and Claude-generated feedback
**Tech Stack**: FastAPI + SQLModel + PostgreSQL (backend), React 19 + TypeScript + Vite + TailwindCSS v4 (frontend), OpenAI Whisper, Anthropic Claude
**Repository**: `/Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator`

---

## Current State

### Branch
`main` - Up to date with origin

### Recent Progress
- ✅ **Skills Gap Analysis COMPLETE (2025-12-20)**: Full-stack implementation with real API data
  - Backend: GET /users/me/skills-gap endpoint with 6 dimensions
  - Frontend: SkillsRadar with loading/empty states, no mock data
  - Removed "Preview" badge - feature production-ready
- ✅ UI Polish & Error Handling (toast colors, filter colors, mobile responsiveness)
- ✅ Improvements by Criteria feature with real data
- ✅ Sprint 10 Code Quality (337 lint errors fixed, 69% backend coverage)
- ✅ Deployed to production (app.codeswiftr.com)

### Current Focus
Skills Gap Analysis fully implemented and deployed. System is launch-ready.

### Blockers/Issues
- Frontend test coverage at 0% (Sprint 11 priority)
- One pre-existing test failure: `test_get_session_feedback_no_feedback_generated` (unrelated to recent work)

---

## Active Plan
**Plan File**: `docs/SKILLS_GAP_PLAN.md`
**Status**: ✅ COMPLETE

### Completed Milestones
- ✅ Skills Gap Analysis with real API data (6 dimensions)
- ✅ UI Polish & Error Handling
- ✅ Improvements by Criteria feature
- ✅ v2 UI Overhaul (React 19 + TailwindCSS v4)

### Next Priority Items
1. Frontend test coverage (currently 0%, target 60%)
2. Video Analysis MVP (scaffolded, needs completion)
3. B2B features (deferred)

---

## Key Context

### Important Files
| File | Purpose |
|------|---------|
| `backend/app/services/feedback_service.py` | Skills gap computation, improvements aggregation |
| `backend/app/api/users.py` | User endpoints including /skills-gap, /improvements |
| `backend/app/models/feedback.py` | SkillDimension, SkillsGapResponse schemas |
| `frontend/src/pages/DashboardPage.tsx` | Main dashboard with skills radar |
| `frontend/src/components/dashboard/SkillsRadar.tsx` | Radar chart component |
| `frontend/src/lib/api.ts` | API client with userAPI.getSkillsGap() |
| `docs/progress.md` | Project progress tracking |
| `docs/SKILLS_GAP_PLAN.md` | Completed implementation plan |

### Recent Decisions
- **6 skill dimensions**: Content, Delivery, Behavioral, Technical, System Design, Communication
- **Trend calculation**: Compare recent 5 vs previous 5 sessions (improving/declining/stable)
- **Target scores**: Content 90, Delivery 85, Behavioral 90, Technical 85, System Design 80, Communication 90
- **Empty state**: Show message when <2 sessions available

### Gotchas Discovered
- ⚠️ Backend tests need `uv sync --all-extras` before running
- ⚠️ AudioFeedback is often null - delivery dimension needs graceful null handling
- ⚠️ Question.category determines which feedback dimensions to aggregate
- ⚠️ Frontend build uses .env.production for API URL (must be https://)

### Patterns to Follow
- **Skills dimensions**: Use weighted score computation per category
- **API endpoints**: Follow pattern in `users.py` (get_my_stats, get_my_progress, get_skills_gap)
- **Frontend data fetching**: Add state + load function + useMemo transformation
- **Component states**: Always handle loading, empty, and data states

### Things to Avoid
- ❌ Don't commit to main directly (use feature branches for major work)
- ❌ Don't use pip (use `uv` for Python dependencies)
- ❌ Don't add mock data fallbacks - compute from real data or show empty state
- ❌ Don't skip the build verification before deploying

---

## Commands to Run

### Verify Environment
```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/frontend
npm run build  # Should pass with no errors
```

### Run Backend Tests
```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend
uv run pytest tests/test_feedback.py tests/test_api.py -v  # Core tests
```

### Run Frontend Tests
```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/frontend
npm run test -- --run
```

### Start Development
```bash
# Backend
cd backend && uv run uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev
```

### Deploy
```bash
# Frontend to Cloudflare Pages
cd frontend && npm run build && npx wrangler pages deploy dist --project-name=interview-simulator --branch=main

# Backend to Railway
cd backend && railway up
```

---

## Instructions for New Agent

### Mindset
You are a pragmatic senior engineer. The system is launch-ready and deployed. Focus on:
- Quality improvements (test coverage)
- Bug fixes as they arise
- Feature enhancements based on user feedback

### Workflow
1. Read this context and check `docs/progress.md` for current status
2. Run build to verify everything compiles
3. Address any specific task requested
4. Commit with conventional messages
5. Deploy if changes are ready

### Quality Gates
After each change:
1. `npm run build` passes (frontend)
2. `uv run pytest tests/test_feedback.py tests/test_api.py` passes (backend)
3. Commit with conventional message
4. Push and deploy if ready

### Production URLs
- Frontend: https://app.codeswiftr.com
- Backend: https://interview-simulator-api-production.up.railway.app

---

## API Reference

### Skills Gap Endpoint
```
GET /api/v1/users/me/skills-gap

Response (success):
{
  "dimensions": [
    {
      "name": "Content",
      "current_score": 72.5,
      "target_score": 90,
      "sessions_with_data": 8,
      "trend": "improving"
    },
    // ... 5 more dimensions
  ],
  "sessions_analyzed": 10,
  "data_available": true,
  "last_updated": "2025-12-20T12:00:00Z"
}

Response (insufficient data):
{
  "dimensions": [],
  "sessions_analyzed": 1,
  "data_available": false,
  "last_updated": null
}
```

---

## Key Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Backend Test Coverage | 69% | 70%+ |
| Frontend Test Coverage | 0% | 60% |
| Backend Tests | 637 collected | - |
| API Endpoints | 25+ | - |

---

## Resume Command

To continue work, start with:
```
Read docs/PROMPT.md and docs/progress.md. The system is deployed and launch-ready.
Check for any specific tasks or continue with frontend test coverage improvements.
```
