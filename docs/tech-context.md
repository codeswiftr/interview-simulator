# Tech Context - CareerSwiftr Interview Simulator

## Architecture Decision Records (ADRs)

### ADR-001: FastAPI + SQLModel Backend

**Status**: Accepted
**Date**: 2025-11-24

**Context**: Need to choose a backend framework for the interview simulator API.

**Decision**: Use FastAPI with SQLModel for the backend.

**Rationale**:
- Consistent with other FORGE projects
- Native async support for AI API calls
- SQLModel provides Pydantic + SQLAlchemy integration
- Excellent OpenAPI documentation generation
- Strong typing support

**Consequences**:
- Team familiarity (positive)
- Need to manage async complexity for AI pipelines
- SQLModel migrations require Alembic setup

---

### ADR-002: Whisper for Transcription

**Status**: Accepted
**Date**: 2025-11-24

**Context**: Need speech-to-text for interview responses.

**Decision**: Use OpenAI Whisper API for transcription.

**Alternatives Considered**:
- Google Speech-to-Text: Good accuracy, higher cost
- AWS Transcribe: Good, but more complex setup
- Local Whisper: Lower cost, higher latency, infrastructure overhead

**Rationale**:
- Best-in-class accuracy for technical terminology
- Timestamped word output supports filler detection
- Simple API integration
- Reasonable cost at scale (~$0.006/minute)

**Consequences**:
- External dependency on OpenAI
- Network latency for transcription
- Cost scales with usage

---

### ADR-003: Claude for Content Analysis

**Status**: Accepted
**Date**: 2025-11-24

**Context**: Need LLM for analyzing interview answer quality.

**Decision**: Use Claude (Sonnet) for content analysis and feedback generation.

**Alternatives Considered**:
- GPT-4o: Comparable quality, slightly higher cost
- Local LLM: Not feasible for required quality
- GPT-3.5: Insufficient for nuanced technical feedback

**Rationale**:
- Excellent at structured analysis tasks
- Strong technical knowledge for coding questions
- Good at providing constructive feedback
- Consistent with FORGE AI strategy

**Consequences**:
- API costs (~$0.003 per analysis)
- Need prompt engineering for consistent output
- Response time 2-5 seconds

---

### ADR-004: Librosa for Audio Analysis

**Status**: Accepted
**Date**: 2025-11-24

**Context**: Need audio analysis for speech patterns (pace, filler words, confidence).

**Decision**: Use Librosa for local audio processing.

**Alternatives Considered**:
- Cloud audio analysis (Google, AWS): Higher cost, external dependency
- Custom ML model: Development overhead
- Skip audio analysis: Missing key feedback dimension

**Rationale**:
- Open source, no API costs
- Well-documented for speech analysis
- Can run locally or on backend server
- Sufficient for speech rate, pitch, volume analysis

**Consequences**:
- CPU-intensive processing
- Need to handle audio format conversion
- Requires librosa + numpy dependencies

---

### ADR-005: Defer Video Analysis to v1.1

**Status**: Accepted
**Date**: 2025-11-24

**Context**: Original spec included video analysis (eye contact, body language).

**Decision**: Defer video analysis to v1.1, focus on audio + content for MVP.

**Rationale**:
- Reduces MVP complexity significantly
- Audio + content provides 80% of feedback value
- Video processing is resource-intensive
- Can validate product-market fit without video

**Consequences**:
- Limited feedback on body language
- Faster time to market
- Lower infrastructure costs
- Clear upgrade path for v1.1

---

### ADR-006: WebRTC for Media Capture

**Status**: Accepted
**Date**: 2025-11-24

**Context**: Need to capture audio (and future video) from user's browser.

**Decision**: Use WebRTC MediaRecorder API for client-side capture.

**Alternatives Considered**:
- Server-side recording: Higher latency, complex infrastructure
- Third-party recording service: Cost, privacy concerns
- Native app: Platform-specific development

**Rationale**:
- Works in all modern browsers
- Client-side processing reduces server load
- Good audio quality with opus codec
- Privacy-friendly (user controls recording)

**Consequences**:
- Browser compatibility considerations
- Need to handle different audio codecs
- Client responsible for upload on completion

---

### ADR-007: PostgreSQL + Redis Data Layer

**Status**: Accepted
**Date**: 2025-11-24

**Context**: Need database and caching layer.

**Decision**: Use PostgreSQL for persistence, Redis for caching.

**Rationale**:
- PostgreSQL: FORGE standard, excellent JSON support, reliable
- Redis: Fast caching, session storage, rate limiting
- Both well-supported by SQLModel and FastAPI

**Consequences**:
- Two services to manage
- Need connection pooling for PostgreSQL
- Redis requires memory planning

---

## Technology Stack Summary

| Layer | Technology | Version |
|-------|------------|---------|
| Runtime | Python | 3.12+ |
| Framework | FastAPI | 0.115+ |
| ORM | SQLModel | 0.0.22+ |
| Database | PostgreSQL | 16+ |
| Cache | Redis | 7+ |
| Package Manager | UV | Latest |
| Transcription | OpenAI Whisper | API |
| Content Analysis | Claude Sonnet | API |
| Audio Analysis | Librosa | 0.10+ |
| Frontend | React | 18+ |
| Media Capture | WebRTC | Native |

## API Dependencies

```toml
[project]
dependencies = [
    "fastapi>=0.115.0",
    "sqlmodel>=0.0.22",
    "uvicorn[standard]>=0.32.0",
    "asyncpg>=0.30.0",
    "redis>=5.0.0",
    "anthropic>=0.37.0",
    "openai>=1.50.0",
    "librosa>=0.10.0",
    "pydantic-settings>=2.5.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.12",
    "httpx>=0.27.0",
]
```

## Infrastructure Requirements

### Development
- Local PostgreSQL (Docker)
- Local Redis (Docker)
- Python 3.12+ with UV
- Node.js 20+ (frontend)

### Production
- Cloudflare Workers / Railway / Render
- Managed PostgreSQL (Neon, Supabase, Railway)
- Managed Redis (Upstash, Railway)
- Cloudflare R2 (audio storage)

## Security Requirements

- HTTPS only
- JWT authentication with refresh tokens
- API rate limiting (100 req/min)
- Audio files encrypted at rest
- 30-day automatic data deletion
- GDPR compliance (data export, deletion)
