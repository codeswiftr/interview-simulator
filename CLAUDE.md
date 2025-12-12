# Interview Simulator Project Rules

## Project Overview
AI-powered interview practice platform for software engineers. Practice behavioral
and technical interviews with real-time audio analysis, transcription via Whisper,
and Claude-generated feedback.

## Tech Stack
- **Backend**: FastAPI + SQLModel (async) + PostgreSQL + Redis
- **Frontend**: React 19 + TypeScript + Vite + TailwindCSS v4
- **AI**: OpenAI Whisper (transcription), Anthropic Claude (feedback)
- **Audio**: Librosa (analysis)
- **Payments**: Stripe
- **Auth**: Custom JWT

## Quick Start
```bash
# Start database
docker compose up -d

# Backend
cd backend && uv sync && uv run alembic upgrade head
uv run python -c "from app.data.seed_questions import seed_questions; import asyncio; asyncio.run(seed_questions())"
uv run uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Testing Commands
```bash
cd backend && uv run pytest                    # All tests (385 tests, 38% line coverage)
cd backend && uv run pytest --cov=app --cov-report=html  # With coverage
cd frontend && npm run build                   # Build check
```

**Note**: High test count (385) with moderate line coverage (38%). Focus areas for coverage improvement: `interview_service.py` (18%), `video_service.py` (46%).

## Project Structure
```
interview-simulator/
├── backend/
│   ├── app/api/         # API routes
│   ├── app/models/      # SQLModel database models
│   ├── app/services/    # Business logic
│   ├── app/ai/          # AI integration (Whisper, Claude)
│   └── uploads/         # Audio file storage
├── frontend/
│   ├── src/components/
│   ├── src/pages/
│   ├── src/hooks/
│   └── src/lib/         # API client, utilities
└── docs/
```

## Audio Processing Standards

### Recording Requirements
- Formats: webm, mp3, wav
- Max duration: 5 minutes per response
- Sample rate: 16kHz minimum
- File size limit: 25MB

### Transcription Pipeline
```python
# Standard flow
audio_file -> Whisper API -> text -> Claude analysis -> feedback
```

### Privacy Considerations
- Audio files: Deleted after 30 days
- Transcripts: User-deletable
- No audio shared with third parties beyond API providers
- Option to use local-only mode (no cloud transcription)

## AI Feedback Guidelines

### Claude Prompt Structure
- Evaluate: clarity, structure, STAR method usage
- Score: 1-10 on multiple dimensions
- Provide: actionable improvement suggestions
- Tone: Constructive, encouraging, professional

### Feedback Categories
1. **Communication**: Clarity, conciseness, confidence
2. **Structure**: STAR method, logical flow
3. **Content**: Relevance, specificity, examples
4. **Technical**: Accuracy, depth (for technical interviews)

## API Standards
- Base path: `/api/v1/`
- Authentication: JWT tokens
- Rate limiting: Configurable per subscription tier
- Error format: `{"detail": "message", "code": "ERROR_CODE"}`

## Quality Gates
- [ ] Test coverage: 70%+
- [ ] API response (p95): <200ms
- [ ] Transcription: <30s for 5min audio
- [ ] Feedback generation: <10s

## Environment Variables
See `backend/.env.example` and `frontend/.env.example`
Required: `DATABASE_URL`, `SECRET_KEY`
Optional: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `STRIPE_SECRET_KEY`

## Current Sprint
See `docs/PLAN.md` for active tasks and blockers.

---

## Production Deployment

### Infrastructure
- **Backend**: Railway (`interview-simulator-api-production.up.railway.app`)
- **Frontend**: Cloudflare Pages (`interview-simulator-4bo.pages.dev`)
- **Custom Domain**: `app.codeswiftr.com`

### Deploying Frontend

**CRITICAL**: Vite inlines env vars at build time. Always ensure `.env.production` exists:

```bash
# frontend/.env.production (already committed)
VITE_API_URL=https://interview-simulator-api-production.up.railway.app/api/v1
```

Deploy steps:
```bash
cd frontend
npm run build                    # Uses .env.production automatically
wrangler pages deploy dist --project-name=interview-simulator --branch=main
```

### Deploying Backend

```bash
cd backend
railway up                       # Deploys from current directory
```

After changing env vars:
```bash
railway variables --service interview-simulator-api --set 'KEY=value'
railway redeploy --service interview-simulator-api -y
```

### Common Deployment Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| CORS 302 errors | Frontend using `http://` | Check `.env.production` uses `https://` |
| API not responding | Railway deployment pending | `railway deployment list` to check status |
| Changes not live | CDN cache | Wait 2-3 min or clear Cloudflare cache |

See [Deployment Troubleshooting](../../docs/DEPLOYMENT_TROUBLESHOOTING.md) for detailed debugging.

---

## Human Gates (Required)
1. **AI Prompts**: Changes to feedback generation prompts
2. **Scoring Logic**: Changes to evaluation algorithms
3. **Audio Processing**: Changes to transcription pipeline
4. **Subscription**: Tier limits or pricing changes
