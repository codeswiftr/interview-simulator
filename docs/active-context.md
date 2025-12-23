# Active Context - CareerSwiftr Interview Simulator

**Last Updated**: 2025-12-16  
**Status**: Launch-ready (v2 UI complete)

## Current Focus

**Phase**: Post-v2 UI Implementation  
**Next**: Frontend testing, production deployment

## In Progress

- [ ] Frontend test coverage (target: 60%)
- [ ] Production deployment preparation
- [ ] Beta user onboarding

## Recent Decisions

### 2025-12-16: v2 UI Complete
- Stack: React 19 + Vite + TailwindCSS v4 + shadcn/ui
- Components: 12 UI primitives + layout components
- Mobile-first with bottom nav, FAB, drawer patterns
- HSL color space (OKLCH deferred)

### 2025-12-10: Sprint 9 Complete
- Conversational voice mentor implemented
- Free tier prepare access enabled (3/month)
- Voice quality assessment with premium badges

### AI Provider Selection
| Provider | Use Case |
|----------|----------|
| Claude API | Content analysis (via OpenRouter/Groq) |
| OpenAI Whisper | Transcription |
| Librosa | Audio analysis (local) |
| Gemini 2.5 Flash | Real-time coaching (Google AI) |

## Current Blockers

None - application is launch-ready.

## Post-Launch Priorities

### Week 1 (Monitoring)
1. Monitor auth token expiry (no refresh mechanism yet)
2. Collect user feedback
3. Fix critical issues

### Month 1 (Polish)
1. Refresh token mechanism
2. Email verification for profile changes
3. Microphone permission UX improvements
4. Frontend test coverage (target 60%)

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API Response Time | < 200ms | Met |
| Transcription Time | < 30s | Met |
| Feedback Generation | < 60s | Met |
| Audio Analysis | < 10s | Met |

## Key Files

**Backend**:
- backend/app/main.py - FastAPI app
- backend/app/ai/ - AI pipeline
- backend/app/api/coaching.py - Real-time coaching hints
- backend/app/api/preparation.py - Ghostwriter + practice APIs

**Frontend**:
- src/ - v2 UI implementation (React 19 + Vite)
- src/components/ui/ - UI primitives (12 components)
- src/views/ - Page components (7 pages)
- src/hooks/useInterviewStateMachine.ts - Interview state management

**Documentation**:
- docs/DESIGN_SYSTEM.md - v2 design system
- docs/PLAN.md - Current milestone planning

## Launch Checklist

- [x] All routes accessible
- [x] Auth flow working
- [x] Interview recording working
- [x] Feedback display working
- [x] Settings updates persisting
- [x] Error boundaries in place
- [x] Loading states on all pages
- [x] Mobile responsive
- [x] Branded assets integrated
