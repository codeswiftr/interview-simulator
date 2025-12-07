# Sprint 5: Quality & Feature Completion

## Status: Planning → Ready
## Target: December 2025
## Context: Post-Sprint 4 (Technical Debt Payback Complete)

---

## Overview

Sprint 5 focuses on two parallel tracks:
1. **Quality Track**: Increase test coverage on critical paths to enable confident deployments
2. **Feature Track**: Complete the AI Ghostwriter feature (Epic 6 Phases 2-4) to deliver full user value

The codebase audit (2025-12-07) identified 223+ backend tests (69% coverage), 55 frontend tests, and 4 E2E suites. Key gaps remain in the `useAudioRecording` hook (0% coverage) and API endpoints for interviews/feedback/auth (40-44% coverage).

**Priority Order:**
1. **Epic 1**: Test Coverage Sprint (foundation for confident deployments)
2. **Epic 2**: Epic 6 Phase 2 - Delivery Practice (high user value)
3. **Epic 3**: Epic 6 Phase 3 - Rating & Comparison (complete feature loop)
4. **Epic 4**: Epic 6 Phase 4 - Polish & Optimization (production readiness)

---

## Success Criteria

- [x] Production health checks implemented ✅ (already complete in main.py)
- [ ] `useAudioRecording` hook tested to 80%+ coverage
- [ ] Backend API coverage to 75% overall (from 69%)
- [ ] Epic 6 Phase 2: Users can practice delivering drafts
- [ ] Epic 6 Phase 3: Delivery rated and compared to draft
- [ ] Epic 6 Phase 4: Draft editing and iteration flow

---

# Epic 1: Test Coverage Sprint ⭐ Highest Priority

## Goal
Increase test coverage on critical paths to enable confident deployments and prevent regressions.

## Context
From codebase audit (2025-12-07):
- `useAudioRecording` hook: 0% coverage (core recording functionality)
- `api/feedback.py`: 44% → target 75%
- `api/interviews.py`: 40% → target 75%
- `api/auth.py`: 40% → target 75%
- `api/transcription.py`: 41% → target 75%

## Success Criteria
- [ ] `useAudioRecording` hook: 80%+ coverage (30+ tests)
- [ ] `api/feedback.py`: 75%+ coverage
- [ ] `api/interviews.py`: 75%+ coverage
- [ ] `api/auth.py`: 75%+ coverage
- [ ] Overall backend: 73%+ (from 69%)

## Implementation Plan

### Phase 1: useAudioRecording Hook Tests (4h)

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 1.1 | Create mock factories for MediaRecorder, MediaStream, Audio | qa-test-guardian | 1h |
| 1.2 | Test initial state and state transitions | qa-test-guardian | 1h |
| 1.3 | Test recording flow (start, pause, resume, stop) | qa-test-guardian | 1h |
| 1.4 | Test preview flow and cleanup on unmount | qa-test-guardian | 1h |

**Mocks Required:**
```typescript
// Mock MediaRecorder
class MockMediaRecorder {
  state = 'inactive';
  start = vi.fn(() => { this.state = 'recording'; });
  stop = vi.fn(() => { this.state = 'inactive'; this.onstop?.(); });
  pause = vi.fn(() => { this.state = 'paused'; });
  resume = vi.fn(() => { this.state = 'recording'; });
  ondataavailable: ((e: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
}

// Mock navigator.mediaDevices
const mockMediaStream = {
  getTracks: () => [{ stop: vi.fn() }],
};

// Mock Audio element
const mockAudio = {
  play: vi.fn().mockResolvedValue(undefined),
  pause: vi.fn(),
  currentTime: 0,
  duration: 60,
  onloadedmetadata: null,
  ontimeupdate: null,
  onended: null,
};
```

**Test Cases:**
1. Initial state is 'idle' with null values
2. `startRecording()` requests microphone permission
3. `startRecording()` handles permission denied error
4. `startRecording()` creates MediaRecorder and starts timer
5. `stopRecording()` creates blob and enters preview mode
6. `pauseRecording()` pauses recorder and timer
7. `resumeRecording()` resumes recorder and timer
8. `resetRecording()` clears all state and resources
9. Preview mode creates Audio element
10. `playPreview()` plays audio
11. `pausePreview()` pauses audio
12. `clearPreview()` returns to idle state
13. `confirmRecording()` returns audioBlob
14. Cleanup on unmount revokes object URLs
15. Error handling for unsupported browsers

**Checkpoint**: `useAudioRecording` hook fully tested

### Phase 2: API Endpoint Tests (6h)

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 2.1 | Add feedback.py tests (generate, get, list) | qa-test-guardian | 2h |
| 2.2 | Add interviews.py tests (lifecycle, responses) | qa-test-guardian | 2h |
| 2.3 | Add auth.py tests (refresh, password reset edge cases) | qa-test-guardian | 1.5h |
| 2.4 | Run coverage report and fill gaps | qa-test-guardian | 30m |

**Feedback API Tests to Add:**
- `test_get_session_feedback_returns_all_responses`
- `test_get_session_feedback_not_found`
- `test_get_response_feedback_not_found`
- `test_generate_feedback_requires_transcript`
- `test_feedback_unauthorized_access`

**Interviews API Tests to Add:**
- `test_create_interview_with_target_company`
- `test_start_interview_already_started`
- `test_end_interview_already_ended`
- `test_submit_response_interview_not_started`
- `test_quota_enforcement_free_tier`
- `test_quota_reset_monthly`

**Auth API Tests to Add:**
- `test_refresh_token_expired`
- `test_refresh_token_reused`
- `test_password_reset_token_expired`
- `test_password_reset_token_already_used`
- `test_login_user_not_found`

**Checkpoint**: Backend coverage at 73%+

---

# Epic 2: Delivery Practice (Epic 6 Phase 2)

## Goal
Enable users to practice delivering their AI-generated drafts with audio recording.

## Context
- PreparationPage already has draft generation (Phase 1 complete)
- RecordingDeck component exists for audio recording
- Need to integrate practice session with preparation flow

## Success Criteria
- [ ] Users can start practice from PreparationPage
- [ ] Recording integrates with existing RecordingDeck
- [ ] Practice attempts saved to database
- [ ] Multiple attempts allowed with history

## Technical Design

### Data Models

```python
# Already exists in models/preparation.py
class DeliveryAttempt(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    preparation_id: UUID = Field(foreign_key="answerpreparation.id")
    audio_url: str | None = None
    transcript: str | None = None
    delivery_score: float | None = None
    comparison_feedback: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

### API Contracts

```
POST /api/v1/preparation/{id}/practice/start
  Response: { attempt_id: UUID, stage: "practice" }

POST /api/v1/preparation/{id}/practice/submit
  Body: { audio_url: str }
  Response: { attempt_id: UUID, transcript: str, stage: "rating" }

GET /api/v1/preparation/{id}/attempts
  Response: { attempts: DeliveryAttempt[] }
```

## Implementation Plan

### Phase 1: Backend Practice API (4h)

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 1.1 | Create Alembic migration for DeliveryAttempt (if needed) | backend-engineer | 30m |
| 1.2 | Add POST /preparation/{id}/practice/start endpoint | backend-engineer | 1h |
| 1.3 | Add POST /preparation/{id}/practice/submit endpoint | backend-engineer | 1.5h |
| 1.4 | Add GET /preparation/{id}/attempts endpoint | backend-engineer | 30m |
| 1.5 | Add tests for practice endpoints | qa-test-guardian | 30m |

**Checkpoint**: Practice API endpoints available

### Phase 2: Frontend Integration (6h)

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 2.1 | Add practice stage UI to PreparationPage | frontend-builder | 2h |
| 2.2 | Integrate RecordingDeck for practice recording | frontend-builder | 2h |
| 2.3 | Add attempt history display | frontend-builder | 1h |
| 2.4 | Wire submit to transcription and storage | frontend-builder | 1h |

**Checkpoint**: Users can practice delivering drafts

---

# Epic 3: Rating & Comparison (Epic 6 Phase 3)

## Goal
Rate user delivery against their draft and provide improvement feedback.

## Context
- After practice, user has: draft (AI-generated) + delivery (transcribed)
- Need to compare and provide actionable feedback
- Track improvement over multiple attempts

## Success Criteria
- [ ] Delivery rated on STAR adherence, completeness
- [ ] Side-by-side comparison UI (draft vs delivery)
- [ ] Improvement suggestions provided
- [ ] Progress tracked across attempts

## Technical Design

### Rating Logic

```python
async def rate_delivery(
    preparation_id: UUID,
    attempt_id: UUID,
    draft: str,
    delivery_transcript: str,
) -> dict:
    """Compare delivery to draft and rate."""
    prompt = f"""
    Compare this interview answer delivery to the prepared draft.

    DRAFT (what they planned to say):
    {draft}

    DELIVERY (what they actually said):
    {delivery_transcript}

    Rate on:
    1. Content Coverage (0-100): Did they hit all STAR components?
    2. Key Points (0-100): Did they include the main points from draft?
    3. Flow & Structure (0-100): Was the delivery logical and clear?

    Provide:
    - Overall score (0-100)
    - 3 strengths of delivery
    - 3 improvements needed
    - Specific suggestions
    """
    # Use Claude Haiku for analysis
```

### API Contracts

```
POST /api/v1/preparation/{id}/rate-delivery
  Body: { attempt_id: UUID }
  Response: {
    delivery_score: float,
    comparison_feedback: str,
    strengths: str[],
    improvements: str[],
    stage: "complete"
  }

GET /api/v1/preparation/{id}/comparison
  Body: { attempt_id: UUID }
  Response: {
    draft: str,
    delivery: str,
    score: float,
    feedback: str
  }
```

## Implementation Plan

### Phase 1: Rating Backend (4h)

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 1.1 | Create rating service with Claude Haiku | backend-engineer | 2h |
| 1.2 | Add POST /preparation/{id}/rate-delivery endpoint | backend-engineer | 1h |
| 1.3 | Add GET /preparation/{id}/comparison endpoint | backend-engineer | 30m |
| 1.4 | Add tests for rating endpoints | qa-test-guardian | 30m |

**Checkpoint**: Rating API available

### Phase 2: Comparison UI (6h)

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 2.1 | Create ComparisonView component | frontend-builder | 2h |
| 2.2 | Add side-by-side diff view | frontend-builder | 2h |
| 2.3 | Display scores and feedback | frontend-builder | 1h |
| 2.4 | Add progress tracking across attempts | frontend-builder | 1h |

**Checkpoint**: Complete rating and comparison flow

---

# Epic 4: Polish & Optimization (Epic 6 Phase 4)

## Goal
Polish the Ghostwriter feature for production launch.

## Success Criteria
- [ ] Draft editing capability
- [ ] Iteration flow (refine draft, re-record)
- [ ] AI prompts optimized for cost/quality
- [ ] Caching for common questions
- [ ] Loading states and error handling polished

## Implementation Plan

### Phase 1: Draft Editing (3h)

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 1.1 | Add draft editing UI to PreparationPage | frontend-builder | 1.5h |
| 1.2 | Add PATCH /preparation/{id}/draft endpoint | backend-engineer | 1h |
| 1.3 | Add save/cancel functionality | frontend-builder | 30m |

**Checkpoint**: Users can edit drafts

### Phase 2: Iteration Flow (3h)

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 2.1 | Add "Try Again" button after rating | frontend-builder | 1h |
| 2.2 | Add "Refine Draft" button | frontend-builder | 1h |
| 2.3 | Track iteration count on attempts | backend-engineer | 1h |

**Checkpoint**: Users can iterate

### Phase 3: Optimization (4h)

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 3.1 | Optimize AI prompts for token efficiency | backend-engineer | 1h |
| 3.2 | Add caching for detective questions | backend-engineer | 1h |
| 3.3 | Polish loading states and transitions | frontend-builder | 1h |
| 3.4 | Add error recovery UX | frontend-builder | 1h |

**Checkpoint**: Feature production-ready

---

## Testing Strategy

### Unit Tests (Epic 1)
- **useAudioRecording**: 30+ tests for all states and transitions
- **Backend APIs**: Cover edge cases, error paths, authorization
- **Target**: 73% overall backend coverage

### Integration Tests
- Full preparation flow (detective → draft → practice → rating)
- Multi-attempt tracking and history
- Error recovery scenarios

### E2E Tests (Existing)
- 4 Playwright suites already cover core flows
- May add Ghostwriter-specific E2E if needed

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| MediaRecorder browser differences | Medium | Low | Test on Chrome, Firefox, Safari |
| AI rating quality inconsistent | Medium | Medium | Test prompts thoroughly, add fallback |
| Ghostwriter costs exceed budget | Low | Low | Tier limits, monitoring |
| Test flakiness on audio mocks | Low | Medium | Use robust mock factories |

---

## Execution Order

**Week 1:**
1. Epic 1: Test Coverage Sprint (foundation)

**Week 2-3:**
2. Epic 2: Delivery Practice

**Week 4:**
3. Epic 3: Rating & Comparison

**Week 5:**
4. Epic 4: Polish & Optimization

**Total Estimated Effort:**
- Epic 1: ~10 hours
- Epic 2: ~10 hours
- Epic 3: ~10 hours
- Epic 4: ~10 hours
- **Total: ~40 hours (1 week full-time or 2 weeks part-time)**

---

## References

- **Codebase Audit**: docs/CODEBASE_AUDIT.md (2025-12-07)
- **Epic 6 Design**: docs/GHOSTWRITER_FEATURE_EVALUATION.md
- **E2E Completion**: docs/EPIC5_EPIC6_COMPLETION_SUMMARY.md
- **Test Patterns**: frontend/src/hooks/__tests__/useAuth.test.tsx
- **RecordingDeck Tests**: frontend/src/components/interview/__tests__/RecordingDeck.test.tsx

---

## Previous Sprints

### Sprint 4: Technical Debt Payback ✅ COMPLETE
- Fixed 158 backend linting errors → 0 errors
- Fixed 28 frontend ESLint issues → 0 errors
- Increased backend tests: 188 → 219+
- Added 55 frontend tests (hooks 100% covered)
- Epic 4: Real-Time AI Coaching ✅
- Epic 5: E2E Test Suite ✅
- Epic 6 Phase 1: AI Ghostwriter MVP ✅

### Sprint 3: Sample Answers & Email ✅ COMPLETE
- 60 questions with sample answers
- Email service integrated with Resend

### Sprint 2: Four Epics ✅ COMPLETE
- Target company feature
- Expanded question bank to 105
- JWT refresh tokens
- Test coverage to 67%

### Sprint 1: Feedback That Helps ✅ COMPLETE
- Experience level selection
- Personalized AI feedback
- Score visualization
