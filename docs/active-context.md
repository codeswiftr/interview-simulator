# Active Context - CareerSwiftr Interview Simulator

## Current Status

**Phase**: Soft Launch Ready + Sprint 8 Complete
**Last Updated**: 2025-12-10

## What We're Working On

### Completed (All Sprints)
- [x] Project structure created
- [x] Living documentation initialized
- [x] Backend scaffolding with FastAPI + UV
- [x] Question bank data model + API (filtering, random selection)
- [x] Interview session API (create, start, end, cancel)
- [x] User authentication (JWT, PBKDF2 hashing, protected routes)
- [x] Alembic migrations (10+ versions applied)
- [x] Docker Compose for Postgres + Redis
- [x] Pre-commit hooks (ruff, mypy)
- [x] Test infrastructure with pytest-asyncio
- [x] Seed questions auto-load (105 questions with 60 sample answers)
- [x] Design System document created (CodeSwiftr branding)
- [x] React + Vite + TailwindCSS frontend
- [x] WebRTC audio capture with Safari compatibility
- [x] Interview room with recording
- [x] Feedback dashboard with AI analysis
- [x] Auth pages (login, register, password reset)
- [x] Dashboard with interview history and stats
- [x] Stripe payment integration
- [x] Dark mode with system detection
- [x] Mobile navigation (hamburger menu)
- [x] Custom branded assets (logo, hero, favicons)
- [x] OpenGraph meta tags
- [x] Complete UI screen flow documentation
- [x] Epic 4: Real-Time AI Coaching Hints (Complete)
- [x] Epic 5: E2E Testing (4 Playwright suites)
- [x] Epic 6: AI Ghostwriter MVP (Detective Q&A + Draft Generation)
- [x] Sprint 7: Voice-Enabled Practice Mode
- [x] Sprint 8: Onboarding & Mentor Mode Enhancement (Complete 2025-12-10)

### Active Tasks
- None - Ready for soft launch!
- Sprint 8 complete: Onboarding flow, contextual tooltips, mentor hint history

## Recent Decisions

### 2025-12-10: Sprint 8 - Onboarding & Mentor Mode Enhancement
- Fixed CoachOverlay dual-interface props (canonical + alias for PreparationPage)
- Added Draft Voice Dictation with replace/append modes
- Created FirstSessionPrompt modal for new user onboarding
- Built ContextualTooltip component with hover/click/always triggers
- Implemented HintHistoryPanel for coaching hint history
- Extended useOnboarding hook with session tracking
- All 6 phases complete, build passing

### 2025-12-02: Soft Launch Readiness
- Completed comprehensive UI screen flow validation
- All 10 screens validated feature-complete
- Generated branded image assets (logo, hero, empty state, OG)
- Fixed dark mode CSS variable issues
- Verdict: **GO for Soft Launch**

### AI Provider Selection
- **Primary**: Claude API (content analysis via OpenRouter/Groq)
- **Transcription**: OpenAI Whisper
- **Audio Analysis**: Librosa (local processing)
- **Real-Time Coaching**: Gemini 2.5 Flash (via Google AI)

## Current Blockers

None - application is launch-ready.

## Post-Launch Priorities

### Week 1 (Monitoring)
1. Monitor auth token expiry (no refresh mechanism yet)
2. Collect user feedback
3. Fix any critical issues

### Month 1 (Polish)
1. Implement refresh token mechanism
2. Add email verification for profile changes
3. Improve microphone permission UX
4. Add frontend test coverage (target 60%)

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API Response Time | < 200ms | ✅ Met |
| Transcription Time | < 30s | ✅ Met |
| Feedback Generation | < 60s | ✅ Met |
| Audio Analysis | < 10s | ✅ Met |

## Files to Watch

- `frontend/src/pages/` - All 11 UI screens
- `backend/app/main.py` - FastAPI application entry
- `backend/app/ai/` - AI pipeline implementations
- `backend/app/api/coaching.py` - Real-time coaching hints (Epic 4)
- `backend/app/api/preparation.py` - Ghostwriter + practice APIs (Epic 6)
- `frontend/src/hooks/useCoachingHint.ts` - Coaching hint hook (Epic 4)
- `frontend/src/hooks/useSpeechRecognition.ts` - Voice input hook (Sprint 7)
- `frontend/src/components/common/ContextualTooltip.tsx` - Tooltip component (Sprint 8)
- `frontend/src/components/onboarding/FirstSessionPrompt.tsx` - Onboarding modal (Sprint 8)
- `frontend/src/components/interview/HintHistoryPanel.tsx` - Hint history (Sprint 8)
- `docs/UI_SCREEN_FLOW.md` - Complete screen validation
- `docs/PLAN.md` - Current milestone planning

## Launch Checklist

- [x] All routes accessible
- [x] Auth flow working (register, login, logout)
- [x] Interview recording and submission working
- [x] Feedback display working
- [x] Settings updates persisting
- [x] Error boundaries in place
- [x] Loading states on all pages
- [x] Dark mode functional
- [x] Mobile responsive (hamburger menu)
- [x] Branded assets integrated
- [x] OG meta tags for social sharing
