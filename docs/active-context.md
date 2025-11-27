# Active Context - CareerSwiftr Interview Simulator

## Current Status

**Phase**: Sprint 1 Completion + Frontend Development
**Last Updated**: 2025-11-26

## What We're Working On

### Completed (Sprint 0-1)
- [x] Project structure created
- [x] Living documentation initialized
- [x] Backend scaffolding with FastAPI + UV
- [x] Question bank data model + API (filtering, random selection)
- [x] Interview session API (create, start, end, cancel)
- [x] User authentication (JWT, PBKDF2 hashing, protected routes)
- [x] Alembic migrations (2 versions applied)
- [x] Docker Compose for Postgres + Redis
- [x] Pre-commit hooks (ruff, mypy)
- [x] Test infrastructure with pytest-asyncio
- [x] Seed questions auto-load in debug mode (5 questions)
- [x] Design System document created (CodeSwiftr branding)

### Active Tasks
- [ ] Expand seed questions from 5 to 50
- [ ] Implement response submission endpoint
- [ ] Wire up real Claude API for content analysis
- [ ] Build React frontend with Vite + Tailwind
- [ ] Implement interview room with audio recording

## Recent Decisions

### 2025-11-24: Project Bootstrap
- Created project structure under `codeswiftr-com/interview-simulator`
- Adopted FastAPI + SQLModel + UV stack (FORGE standard)
- Positioned as "Simulator" not "Copilot" for ethical clarity

### AI Provider Selection
- **Primary**: Claude API (content analysis, interviewer agent)
- **Transcription**: OpenAI Whisper
- **Audio Analysis**: Librosa (local processing)
- **Rationale**: Claude for quality, Whisper for accuracy, Librosa for cost efficiency

## Current Blockers

None currently.

## Open Questions

1. **Video Analysis Scope**: Should we include EmotiEffLib for MVP or defer?
   - Recommendation: Defer to v1.1, focus on audio + content first

2. **Question Bank Size**: How many seed questions for launch?
   - Target: 50 questions (10 behavioral, 20 technical, 20 system design)

3. **Pricing Experiment**: Start with freemium or trial-based?
   - Leaning: 7-day free trial, then paid

## Dependencies

### External Services
- [ ] OpenAI API key (for Whisper)
- [ ] Anthropic API key (for Claude)
- [ ] Object storage (Cloudflare R2 or S3)
- [ ] PostgreSQL database
- [ ] Redis cache

### Internal Dependencies
- FORGE marketing template (for landing page)
- FORGE marketing-api (for lead capture)

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API Response Time | < 200ms | N/A |
| Transcription Time | < 30s | N/A |
| Feedback Generation | < 60s | N/A |
| Audio Analysis | < 10s | N/A |

## Files to Watch

- `backend/app/main.py` - FastAPI application entry
- `backend/app/ai/` - AI pipeline implementations
- `backend/app/services/interview_service.py` - Core business logic
- `docs/PLAN.md` - Sprint planning and roadmap

## Soft Launch Roadmap

### Phase A: Backend Completion (Sprint 1-2 finish)
1. Expand to 50 seed questions (10 behavioral, 20 technical, 20 system design)
2. Implement response submission with basic audio handling
3. Wire up real Claude API for content analysis
4. Basic feedback generation pipeline
5. Test coverage to 80%+

### Phase B: Frontend MVP
1. React + Vite + TailwindCSS setup with Design System
2. Auth flows (login/register/logout)
3. Dashboard with interview history
4. Interview room with WebRTC audio recording
5. Feedback dashboard with scores and improvement tips

### Phase C: Launch Prep
1. Stripe subscription integration
2. Landing page using FORGE marketing template
3. Production deployment (Railway/Cloudflare)
4. Beta user onboarding (20 users)

## Next Session Priorities

1. Expand seed questions from 5 to 50
2. Implement response submission endpoint
3. Initialize React frontend with Design System
4. Build auth pages and dashboard shell
