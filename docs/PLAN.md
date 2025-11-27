# PLAN - CareerSwiftr Interview Simulator

## Sprint Overview

| Sprint | Focus | Duration | Status |
|--------|-------|----------|--------|
| Sprint 0 | Project Setup | 2 days | ✅ Complete |
| Sprint 1 | Core Interview Flow | 1 week | ✅ Complete |
| Sprint 2 | AI Integration | 1 week | ✅ Complete |
| Sprint 3 | Audio Analysis + Frontend | 1 week | ✅ Frontend Complete |
| Sprint 4 | Launch Prep | 1 week | 🟡 In Progress |

---

## Critical Gap Analysis (2025-11-27)

### Identified Issues

1. **Missing Question Assignment API** - No endpoint to assign questions to interviews
   - `InterviewQuestion` model exists but isn't populated
   - Frontend fetches random questions client-side as workaround
   - Response submission will fail validation (checks `InterviewQuestion` link)

2. **Missing Audio Upload API** - Frontend calls `POST /upload/audio` which doesn't exist
   - Transcription endpoint exists but doesn't store files
   - No audio URL returned for response submission

3. **Missing GET /interviews/{id}/questions** - Frontend expects this endpoint

4. **Audio Analyzer is Stub** - Returns mock values for speech_rate, volume, confidence

5. **Feedback Page Falls Back to Mock Data** - Uses `generateMockFeedback()` when API fails

---

## Sprint 4: Launch Prep (Detailed Implementation)

### Epic 4.1: End-to-End Interview Flow
**Priority: CRITICAL** - Without this, the app doesn't work

#### Task 4.1.1: Question Assignment on Interview Start
**Files to change:**
- `backend/app/api/interviews.py`
- `backend/app/services/interview_service.py` (new)
- `backend/tests/test_interviews.py`

**Functions to implement:**

```python
# backend/app/services/interview_service.py
class InterviewService:
    async def assign_questions(session: AsyncSession, interview: InterviewSession) -> list[InterviewQuestion]:
        """Selects random questions matching interview type and creates InterviewQuestion records.
        Uses weighted selection to avoid repeating recently-seen questions for user."""

    async def get_interview_questions(session: AsyncSession, interview_id: UUID) -> list[Question]:
        """Returns questions assigned to interview via InterviewQuestion join."""
```

```python
# backend/app/api/interviews.py
@router.post("/{interview_id}/start")
async def start_interview(...):
    """MODIFY: Call InterviewService.assign_questions() when starting interview."""

@router.get("/{interview_id}/questions", response_model=list[QuestionRead])
async def get_interview_questions(interview_id: UUID, ...):
    """NEW: Return questions assigned to this interview session."""
```

**Tests to add:**
- `test_start_interview_assigns_questions` - Verifies InterviewQuestion records created
- `test_get_interview_questions_returns_assigned` - Verifies correct questions returned
- `test_start_interview_respects_question_count` - Assigns exactly N questions
- `test_questions_match_interview_type` - All assigned questions match category

---

#### Task 4.1.2: Audio Upload Endpoint
**Files to change:**
- `backend/app/api/upload.py` (new)
- `backend/app/main.py`
- `backend/tests/test_upload.py` (new)

**Functions to implement:**

```python
# backend/app/api/upload.py
UPLOAD_DIR = Path("uploads")  # Local storage for MVP, S3 later

@router.post("/audio", response_model=AudioUploadResponse)
async def upload_audio(
    file: UploadFile,
    session_id: UUID,
    question_id: UUID,
    current_user: User = Depends(get_current_user),
) -> AudioUploadResponse:
    """Stores audio file and returns URL. Validates session ownership."""

class AudioUploadResponse(BaseModel):
    audio_url: str
    file_size_bytes: int
    duration_estimate_seconds: float | None
```

**Tests to add:**
- `test_upload_audio_creates_file` - File saved to uploads dir
- `test_upload_audio_validates_session` - Returns 404 for non-existent session
- `test_upload_audio_validates_ownership` - Returns 403 for other user's session
- `test_upload_audio_returns_url` - Response contains valid audio_url

---

#### Task 4.1.3: Fix Response Submission Validation
**Files to change:**
- `backend/app/api/interviews.py`

**Changes:**
```python
# backend/app/api/interviews.py:167-179
# CURRENT: Validates question belongs to interview via InterviewQuestion
# AFTER: Same logic works because Task 4.1.1 creates InterviewQuestion records
```

**Tests to add:**
- `test_submit_response_with_assigned_question` - Works after start assigns questions
- `test_submit_response_full_flow` - Create → Start → Submit → Verify

---

### Epic 4.2: Audio Pipeline Integration
**Priority: HIGH** - Core value proposition is audio analysis

#### Task 4.2.1: Integrated Audio Processing
**Files to change:**
- `backend/app/api/upload.py`
- `backend/app/services/audio_service.py` (new)

**Functions to implement:**

```python
# backend/app/services/audio_service.py
class AudioService:
    async def process_audio(audio_path: str, response_id: UUID) -> ProcessingResult:
        """Orchestrates: upload → transcribe → analyze. Returns all results."""

    async def transcribe_and_update(audio_path: str, response_id: UUID) -> str:
        """Calls Whisper, updates InterviewResponse.transcript, returns text."""

    async def analyze_audio_metrics(audio_path: str, transcript: str) -> AudioMetrics:
        """Calls AudioAnalyzer with real Librosa analysis."""
```

**Tests to add:**
- `test_process_audio_updates_transcript` - Transcript saved to response
- `test_process_audio_returns_metrics` - AudioMetrics populated

---

#### Task 4.2.2: Implement Real Librosa Analysis
**Files to change:**
- `backend/app/ai/audio_analyzer.py`
- `backend/pyproject.toml` (add librosa dependency)
- `backend/tests/test_audio_analyzer.py` (new)

**Functions to implement:**

```python
# backend/app/ai/audio_analyzer.py
class AudioAnalyzer:
    async def analyze(self, audio_path: str, transcript: str | None = None) -> AudioMetrics:
        """MODIFY: Replace mock returns with real Librosa analysis."""

    def _calculate_speech_rate(self, audio_path: str, transcript: str) -> float:
        """Uses Librosa to get audio duration, divides word count by duration."""

    def _analyze_volume_consistency(self, audio_path: str) -> float:
        """Calculates RMS energy variance - lower variance = more consistent."""

    def _calculate_confidence_score(self, audio_path: str) -> float:
        """Analyzes pitch variation and stability as confidence proxy."""
```

**Tests to add:**
- `test_analyze_returns_real_speech_rate` - Not default 130.0
- `test_analyze_calculates_volume_consistency` - Returns 0-100 score
- `test_analyze_detects_filler_words` - Counts um/uh in transcript
- `test_analyze_handles_missing_transcript` - Works without transcript

---

#### Task 4.2.3: Create AudioFeedback Storage
**Files to change:**
- `backend/app/models/feedback.py`
- `backend/alembic/versions/0003_audio_feedback.py` (new)
- `backend/app/services/feedback_service.py`

**Functions to implement:**

```python
# backend/app/models/feedback.py
class AudioFeedback(SQLModel, table=True):
    """Stores audio analysis metrics per response."""
    id: UUID
    response_id: UUID  # FK to InterviewResponse
    speech_rate_wpm: float
    filler_word_count: int
    filler_words: dict[str, int]  # {"um": 5, "uh": 3}
    volume_consistency: float
    confidence_score: float
    overall_audio_score: float
```

```python
# backend/app/services/feedback_service.py
async def generate_audio_feedback(session: AsyncSession, response_id: UUID) -> AudioFeedback:
    """Analyzes audio for response and stores AudioFeedback record."""
```

**Tests to add:**
- `test_generate_audio_feedback_creates_record` - AudioFeedback saved
- `test_session_feedback_includes_audio_score` - SessionFeedback.audio_score populated

---

### Epic 4.3: Execution & Feedback Polish
**Priority: MEDIUM** - Makes the product feel complete

#### Task 4.3.1: Wire Frontend to Real Feedback API
**Files to change:**
- `frontend/src/pages/FeedbackPage.tsx`
- `frontend/src/lib/api.ts`

**Changes:**
```typescript
// frontend/src/pages/FeedbackPage.tsx
// REMOVE: generateMockFeedback() function (lines 29-168)
// MODIFY: loadFeedback() to throw error on API failure instead of using mock
// ADD: Loading state while feedback generates
// ADD: "Generate Feedback" button if feedback not yet created
```

```typescript
// frontend/src/lib/api.ts
export const feedbackAPI = {
    generateForSession: (sessionId: string) =>
        api.post(`/feedback/generate/session/${sessionId}`),
    // ... existing methods
};
```

**Tests to add (frontend):**
- Component test: renders loading state
- Component test: renders error state on API failure
- Component test: renders feedback data correctly

---

#### Task 4.3.2: Fix Interview Questions Endpoint in Frontend
**Files to change:**
- `frontend/src/pages/InterviewPage.tsx`
- `frontend/src/lib/api.ts`

**Changes:**
```typescript
// frontend/src/pages/InterviewPage.tsx:64-78
// REMOVE: Client-side random question fetching workaround
// REPLACE WITH: Call to interviewsAPI.getQuestions(id)

const loadInterview = async () => {
    const sessionResponse = await interviewsAPI.getById(id);
    if (sessionData.status === 'scheduled') {
        await interviewsAPI.start(id);  // This now assigns questions
    }
    const questionsResponse = await interviewsAPI.getQuestions(id);
    setQuestions(questionsResponse.data);
};
```

---

#### Task 4.3.3: Add Feedback Generation Trigger
**Files to change:**
- `backend/app/api/interviews.py`
- `backend/app/services/feedback_service.py`

**Functions to implement:**

```python
# backend/app/api/interviews.py
@router.post("/{interview_id}/end")
async def end_interview(...):
    """MODIFY: After ending, trigger async feedback generation for all responses."""
```

**Tests to add:**
- `test_end_interview_triggers_feedback` - ContentFeedback created for each response
- `test_end_interview_creates_session_feedback` - SessionFeedback created

---

### Epic 4.4: Payment Integration
**Priority: HIGH** - Required for monetization

#### Task 4.4.1: Stripe Configuration
**Files to change:**
- `backend/app/config.py`
- `backend/.env.example`
- `backend/pyproject.toml` (add stripe dependency)

**Environment variables:**
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_PREMIUM=price_...
```

---

#### Task 4.4.2: Subscription Management
**Files to change:**
- `backend/app/api/subscriptions.py` (new)
- `backend/app/models/user.py`
- `backend/app/main.py`

**Functions to implement:**

```python
# backend/app/api/subscriptions.py
@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    price_id: str,
    current_user: User = Depends(get_current_user),
) -> CheckoutSessionResponse:
    """Creates Stripe Checkout session, returns URL for redirect."""

@router.post("/webhook")
async def stripe_webhook(request: Request) -> dict:
    """Handles checkout.session.completed, customer.subscription.updated/deleted."""

@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(current_user: User = Depends(get_current_user)):
    """Returns current subscription tier and usage limits."""
```

```python
# backend/app/models/user.py
class User(SQLModel, table=True):
    # ADD:
    stripe_customer_id: str | None = None
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    subscription_expires_at: datetime | None = None
    interviews_this_month: int = 0
```

**Tests to add:**
- `test_create_checkout_session_returns_url` - Valid Stripe URL returned
- `test_webhook_updates_subscription` - User tier updated on success
- `test_free_user_limited_interviews` - Enforces 3/month limit
- `test_pro_user_unlimited_interviews` - No limit for pro tier

---

#### Task 4.4.3: Usage Limits Enforcement
**Files to change:**
- `backend/app/api/interviews.py`
- `backend/app/dependencies.py`

**Functions to implement:**

```python
# backend/app/dependencies.py
async def check_interview_quota(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Raises 402 Payment Required if free user exceeds 3 interviews/month."""
```

```python
# backend/app/api/interviews.py
@router.post("/", response_model=InterviewSessionRead, dependencies=[Depends(check_interview_quota)])
async def create_interview(...):
    """MODIFY: Add quota check dependency."""
```

**Tests to add:**
- `test_free_user_fourth_interview_blocked` - Returns 402
- `test_pro_user_no_limit` - No 402 for pro users
- `test_quota_resets_monthly` - New month allows interviews

---

#### Task 4.4.4: Frontend Subscription UI
**Files to change:**
- `frontend/src/pages/SettingsPage.tsx` (new)
- `frontend/src/components/UpgradeModal.tsx` (new)
- `frontend/src/lib/api.ts`

**Components:**
- `SettingsPage` - Shows current plan, billing info, upgrade/cancel buttons
- `UpgradeModal` - Shown when user hits free limit, redirects to Stripe checkout

---

## Completed Sprints Reference

### Sprint 0: Project Setup ✅ COMPLETE

- [x] Create directory structure
- [x] Initialize documentation
- [x] Create `pyproject.toml` with UV
- [x] Set up FastAPI application skeleton
- [x] Configure Alembic for migrations
- [x] Create SQLModel base models
- [x] Set up pytest infrastructure
- [x] Configure pre-commit hooks
- [x] Docker Compose for PostgreSQL + Redis

### Sprint 1: Core Interview Flow ✅ COMPLETE

- [x] Question model with categories, seed 50 questions
- [x] Question retrieval API with filters
- [x] Random question selection logic
- [x] InterviewSession model and CRUD
- [x] Session state machine
- [x] User model with JWT auth
- [x] Response submission/retrieval endpoints

### Sprint 2: AI Integration ✅ COMPLETE

- [x] Whisper transcription service (`backend/app/ai/transcriber.py`)
- [x] Transcription API endpoint (`backend/app/api/transcription.py`)
- [x] Claude content analyzer (`backend/app/ai/content_analyzer.py`)
- [x] Feedback generation service (`backend/app/services/feedback_service.py`)
- [x] Feedback API endpoints (`backend/app/api/feedback.py`)

### Sprint 3: Frontend MVP ✅ COMPLETE

- [x] React + Vite + TailwindCSS setup
- [x] Auth pages (login, register)
- [x] Dashboard with interview history
- [x] Interview room with WebRTC audio
- [x] Feedback page with score visualization
- [x] Design system components

---

## Backlog (Post-MVP)

### v1.1: Video Analysis
- [ ] EmotiEffLib integration
- [ ] Eye contact tracking
- [ ] Body language analysis

### v1.2: Company-Specific Prep
- [ ] Company question sets (FAANG, startups)
- [ ] Interview style customization

### v1.3: Social Features
- [ ] Mock interview matching
- [ ] Community question contributions

---

## Definition of Done

For each task:
- [ ] Code implemented and linted
- [ ] Tests passing (>80% coverage)
- [ ] Documentation updated
- [ ] No critical bugs
- [ ] Committed to feature branch
