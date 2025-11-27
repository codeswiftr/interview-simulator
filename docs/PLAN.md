# PLAN - CareerSwiftr Interview Simulator

## Sprint Overview

| Sprint | Focus | Duration | Status |
|--------|-------|----------|--------|
| Sprint 0 | Project Setup | 2 days | ✅ Complete |
| Sprint 1 | Core Interview Flow | 1 week | ✅ Complete |
| Sprint 2 | AI Integration | 1 week | 🟡 30% (stubs) |
| Sprint 3 | Audio Analysis + Frontend | 1 week | ✅ Frontend Complete |
| Sprint 4 | Launch Prep | 1 week | Not Started |

---

## Sprint 0: Project Setup ✅ COMPLETE

### Goals
- Complete project scaffolding
- Set up development environment
- Initialize database schema

### Tasks

#### Backend Setup
- [x] Create directory structure
- [x] Initialize documentation
- [x] Create `pyproject.toml` with UV
- [x] Set up FastAPI application skeleton
- [x] Configure Alembic for migrations
- [x] Create SQLModel base models
- [x] Set up pytest infrastructure
- [x] Configure pre-commit hooks

#### Development Environment
- [x] Docker Compose for PostgreSQL + Redis
- [x] Environment variables setup
- [x] VS Code settings for project

### Deliverables ✅
- Working FastAPI server with health endpoint
- Database connection established
- Test suite running

---

## Sprint 1: Core Interview Flow ✅ COMPLETE

### Goals
- Implement question bank
- Build interview session management
- Basic user authentication

### Tasks

#### Question Bank
- [x] Question model with categories
- [x] Seed data: 50 questions
  - 10 behavioral (STAR format)
  - 20 technical (algorithms, data structures)
  - 20 system design (scalability, architecture)
- [x] Question retrieval API with filters
- [x] Random question selection logic

#### Interview Sessions
- [x] InterviewSession model
- [x] Session state machine (SCHEDULED → IN_PROGRESS → COMPLETED → ANALYZED)
- [x] CRUD endpoints for sessions
- [x] Question assignment logic
- [x] Time tracking

#### Authentication
- [x] User model with subscription tiers
- [x] JWT token generation
- [x] Login/register endpoints
- [x] Protected route middleware (get_current_user)
- [x] Password hashing with PBKDF2

#### Response Handling
- [x] Response submission endpoint (POST /interviews/{id}/responses)
- [x] Response retrieval endpoint (GET /interviews/{id}/responses)
- [x] Validation (session status, ownership, question linking)

### Deliverables ✅
- [x] API: Create interview, get questions
- [x] API: Submit responses
- [x] Auth: Register, login, protected routes
- [x] 50 seed questions in database

---

## Sprint 2: AI Integration

### Goals
- Integrate Whisper for transcription
- Implement Claude content analysis
- Build feedback generation pipeline

### Tasks

#### Transcription (Whisper)
- [ ] OpenAI Whisper API client
- [ ] Audio file processing service
- [ ] Timestamped transcript extraction
- [ ] Async processing with status updates

#### Content Analysis (Claude)
- [ ] Anthropic client setup
- [ ] Content analysis prompt engineering
- [ ] Structured feedback extraction
- [ ] Error handling and retries

#### Feedback Pipeline
- [ ] ContentFeedback model
- [ ] Feedback generation service
- [ ] Technical accuracy scoring
- [ ] STAR method evaluation (behavioral)
- [ ] Improvement suggestions

### Deliverables
- Audio upload → transcript endpoint
- Transcript → feedback endpoint
- Feedback stored in database

---

## Sprint 3: Audio Analysis + Frontend

### Goals
- Add Librosa audio analysis
- Build React frontend
- Implement WebRTC capture

### Tasks

#### Audio Analysis (Librosa)
- [ ] Librosa service setup
- [ ] Speech rate calculation
- [ ] Filler word detection from transcript
- [ ] Volume/pitch analysis
- [ ] Confidence scoring algorithm
- [ ] AudioFeedback model and storage

#### React Frontend
- [ ] Vite + React setup
- [ ] Tailwind CSS styling
- [ ] Interview room component
- [ ] WebRTC MediaRecorder integration
- [ ] Audio upload on response complete
- [ ] Loading states for AI processing

#### Feedback Dashboard
- [ ] Session feedback view
- [ ] Audio metrics visualization
- [ ] Content feedback display
- [ ] Progress tracking charts

### Deliverables
- Working interview room UI
- Real-time audio capture
- Feedback dashboard with scores

---

## Sprint 4: Launch Prep

### Goals
- Payment integration
- Landing page
- Production deployment
- Beta launch

### Tasks

#### Payments (Stripe)
- [ ] Stripe account setup
- [ ] Subscription plans creation
- [ ] Checkout flow
- [ ] Webhook handlers
- [ ] Usage metering (interviews/month)

#### Landing Page
- [ ] Use FORGE marketing template
- [ ] Custom copy for CareerSwiftr
- [ ] Lead capture form
- [ ] Demo video/screenshots

#### Production
- [ ] Production database (Neon/Supabase)
- [ ] Redis hosting (Upstash)
- [ ] Backend deployment (Railway/Render)
- [ ] Frontend deployment (Cloudflare Pages)
- [ ] Environment secrets

#### Beta Launch
- [ ] 20 beta users recruited
- [ ] Feedback collection form
- [ ] Bug tracking setup
- [ ] Usage analytics

### Deliverables
- Live production site
- 20 beta users onboarded
- Payment flow working

---

## Backlog (Post-MVP)

### v1.1: Video Analysis
- [ ] EmotiEffLib integration
- [ ] Eye contact tracking
- [ ] Body language analysis
- [ ] Video recording and playback

### v1.2: Company-Specific Prep
- [ ] Company question sets (FAANG, startups)
- [ ] Interview style customization
- [ ] Company research integration

### v1.3: Practice Modes
- [ ] Timed coding challenges
- [ ] System design whiteboard
- [ ] Behavioral story builder

### v1.4: Social Features
- [ ] Mock interview matching
- [ ] Community question contributions
- [ ] Leaderboards

---

## Definition of Done

For each sprint, all items must meet:
- [ ] Code reviewed and merged
- [ ] Tests passing (>80% coverage)
- [ ] Documentation updated
- [ ] No critical bugs
- [ ] Performance targets met
