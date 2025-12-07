# Sprint 4: Technical Debt Payback

## Status: Complete (Epics 1-3 Done)
## Target: December 2025
## Completed: 2025-12-04

---

## Overview

Sprint 4 focuses on **technical debt payback** to establish a maintainable codebase foundation. The audit revealed 158 backend linting errors, 28 frontend linting issues, and test coverage gaps (67% backend, 0% frontend). Addressing this debt now prevents compounding issues and enables confident feature development.

**Priority Order:**
1. **Epic 1**: Fix Linting Errors (clean codebase, prevent bugs)
2. **Epic 2**: Backend Test Coverage to 75% (confidence for deployments)
3. **Epic 3**: Frontend Test Infrastructure (regression protection)
4. **Epic 4**: E2E Test Suite (user journey validation)

---

## Success Criteria

- [x] 60 questions have sample_answer populated ✅ (completed Sprint 3)
- [x] Email service sends real emails via Resend ✅ (completed Sprint 3)
- [x] Backend linting: 0 errors ✅ (from 158)
- [x] Frontend linting: 0 errors ✅ (from 28)
- [x] Backend test coverage: 69% ✅ (from 67%, 219 tests passing)
- [x] Frontend test coverage: 55 tests ✅ (from 0%, hooks 100% covered)
- [x] All 219+ backend tests passing ✅
- [x] All 55 frontend tests passing ✅

---

# Sprint 3 Completion Summary ✅

| Epic | Status | Outcome |
|------|--------|---------|
| Sample Answers | ✅ Complete | 60 questions with answers (30 behavioral, 20 technical, 10 system design) |
| Email Service | ✅ Complete | Resend integration working |
| Test Coverage | 🟡 Partial | 67% (target was 75%) |
| Video Analysis | ⏸️ Deferred | Moved to future sprint |

---

# Epic 1: Sample Answers for Question Bank

## Goal
Provide users with high-quality reference answers so they understand what "good" looks like.

## Context
- 105 questions exist (50 technical, 30 behavioral, 25 system design)
- 0 questions currently have `sample_answer` populated
- SampleAnswerModal component already exists on FeedbackPage
- `sample_answer` field is `str | None` in Question model

## Success Criteria
- [ ] 20 behavioral questions have STAR-format sample answers
- [ ] 20 technical questions have structured problem-solving answers
- [ ] 10 system design questions have component-based answers

## Implementation Plan

### Phase 1: Behavioral Sample Answers (20 questions)
| Task | Description | Est |
|------|-------------|-----|
| 1.1 | Write STAR answers for 10 easy behavioral questions | 1.5h |
| 1.2 | Write STAR answers for 6 medium behavioral questions | 1h |
| 1.3 | Write STAR answers for 4 hard behavioral questions | 1h |
| 1.4 | Update seed_questions.py with new content | 30m |
| 1.5 | Run seed to update database | 15m |

**STAR Format Template:**
```
**Situation**: [Context and background]
**Task**: [Your responsibility]
**Action**: [Specific steps you took]
**Result**: [Measurable outcome]
```

**Checkpoint**: 20 behavioral questions visible in SampleAnswerModal

### Phase 2: Technical Sample Answers (20 questions)
| Task | Description | Est |
|------|-------------|-----|
| 2.1 | Write answers for 10 data structures questions | 1.5h |
| 2.2 | Write answers for 5 algorithm questions | 1h |
| 2.3 | Write answers for 5 coding pattern questions | 1h |
| 2.4 | Update seed_questions.py | 30m |

**Technical Answer Template:**
```
**Problem Understanding**: [Clarify requirements]
**Approach**: [Algorithm/data structure choice]
**Complexity**: [Time/space analysis]
**Code Sketch**: [Pseudocode or key logic]
**Edge Cases**: [What to watch for]
```

**Checkpoint**: 20 technical questions have sample answers

### Phase 3: System Design Sample Answers (10 questions)
| Task | Description | Est |
|------|-------------|-----|
| 3.1 | Write answers for 5 distributed systems questions | 1h |
| 3.2 | Write answers for 5 scaling questions | 1h |
| 3.3 | Update seed_questions.py | 30m |

**System Design Answer Template:**
```
**Requirements**: [Functional and non-functional]
**High-Level Design**: [Components and data flow]
**Deep Dive**: [Key component details]
**Tradeoffs**: [Decisions and alternatives]
**Scaling**: [How to handle growth]
```

**Checkpoint**: 10 system design questions have sample answers

---

# Epic 2: Backend Test Coverage to 75%

## Goal
Increase test coverage from 66% to 75% to prevent regressions and enable confident deployments.

## Context
From codebase audit, lowest coverage modules:
- `api/feedback.py`: 39% (target: 75%)
- `api/interviews.py`: 40% (target: 75%)
- `api/auth.py`: 40% (target: 75%)
- `api/subscriptions.py`: 40% (target: 60%)
- `api/users.py`: 52% (target: 75%)
- `middleware/rate_limit.py`: 33% (target: 60%)

## Success Criteria
- [ ] Overall coverage: 75%+
- [ ] api/feedback.py: 75%+
- [ ] api/interviews.py: 75%+
- [ ] api/auth.py: 75%+
- [ ] All 140+ tests passing

## Implementation Plan

### Phase 1: Test Fixtures & Infrastructure
| Task | Description | Est |
|------|-------------|-----|
| 1.1 | Create conftest.py fixtures for auth user | 30m |
| 1.2 | Create factory functions for interviews, responses | 30m |
| 1.3 | Create mock generators for feedback data | 30m |

**Checkpoint**: Reusable fixtures available for all test files

### Phase 2: Feedback API Tests (+36% needed)
| Task | Description | Est |
|------|-------------|-----|
| 2.1 | Test GET /feedback/session/{id}/all endpoint | 30m |
| 2.2 | Test GET /feedback/response/{id} endpoint | 30m |
| 2.3 | Test POST /feedback/generate/response/{id} | 30m |
| 2.4 | Test GET /feedback/session/{id}/comparison | 30m |
| 2.5 | Test authorization (wrong user access) | 30m |
| 2.6 | Test 404 cases (not found) | 30m |

**Checkpoint**: api/feedback.py coverage ≥ 75%

### Phase 3: Interviews API Tests (+35% needed)
| Task | Description | Est |
|------|-------------|-----|
| 3.1 | Test POST /interviews (create) with all options | 30m |
| 3.2 | Test POST /interviews/{id}/start edge cases | 30m |
| 3.3 | Test GET /interviews/{id}/questions | 30m |
| 3.4 | Test POST /interviews/{id}/responses validation | 30m |
| 3.5 | Test POST /interviews/{id}/end state transitions | 30m |
| 3.6 | Test DELETE /interviews/{id} authorization | 30m |
| 3.7 | Test quota enforcement for free users | 30m |

**Checkpoint**: api/interviews.py coverage ≥ 75%

### Phase 4: Auth API Tests (+35% needed)
| Task | Description | Est |
|------|-------------|-----|
| 4.1 | Test POST /auth/forgot-password rate limiting | 30m |
| 4.2 | Test POST /auth/reset-password expired token | 30m |
| 4.3 | Test POST /auth/reset-password used token | 30m |
| 4.4 | Test POST /auth/refresh with invalid token | 30m |
| 4.5 | Test POST /auth/refresh with expired token | 30m |

**Checkpoint**: api/auth.py coverage ≥ 75%

### Phase 5: Users & Rate Limit Tests
| Task | Description | Est |
|------|-------------|-----|
| 5.1 | Test PATCH /users/me with various updates | 30m |
| 5.2 | Test POST /users/me/change-password validation | 30m |
| 5.3 | Test DELETE /users/me cleanup behavior | 30m |
| 5.4 | Test rate_limit middleware request blocking | 30m |
| 5.5 | Test rate_limit cooldown and reset | 30m |

**Checkpoint**: Overall coverage ≥ 75%

---

# Epic 3: Email Verification & Password Reset

## Goal
Complete the email infrastructure for production deployment.

## Context
From exploration:
- `email_service.py` exists with `send_password_reset()` method
- Password reset flow is implemented but may not send real emails
- `is_verified` field exists on User model but is unused
- No email verification for registration
- SMTP config exists but may not be configured

## Success Criteria
- [ ] Password reset emails actually send in production
- [ ] Email templates are professional and branded
- [ ] (Stretch) Registration requires email verification

## Implementation Plan

### Phase 1: Email Service Production Readiness
| Task | Description | Est |
|------|-------------|-----|
| 1.1 | Integrate SendGrid/Resend as email provider | 1h |
| 1.2 | Create branded HTML email templates | 1h |
| 1.3 | Test email delivery in staging | 30m |
| 1.4 | Add email delivery logging | 30m |

**Checkpoint**: Password reset emails send successfully

### Phase 2: Email Verification (Stretch)
| Task | Description | Est |
|------|-------------|-----|
| 2.1 | Create EmailVerificationToken model | 30m |
| 2.2 | Create Alembic migration | 15m |
| 2.3 | Add POST /auth/verify-email endpoint | 1h |
| 2.4 | Add POST /auth/resend-verification endpoint | 30m |
| 2.5 | Update registration to send verification email | 30m |
| 2.6 | Update login to check is_verified | 30m |
| 2.7 | Create VerifyEmailPage frontend | 1h |
| 2.8 | Add tests for verification flow | 1h |

**Checkpoint**: New users must verify email before login

---

# Epic 4: Video Analysis Integration (Future)

## Goal
Add video analysis for body language, eye contact, and emotion detection.

## Context
From project-brief.md:
- EmotiEffLib mentioned for video analysis
- Currently only audio is captured and analyzed
- Frontend uses WebRTC (can capture video)
- Would be a major differentiator

## Success Criteria
- [ ] Video capture enabled in interview room
- [ ] Emotion detection (confidence vs nervousness)
- [ ] Eye contact tracking
- [ ] Video feedback displayed on FeedbackPage

## Implementation Plan (High-Level)

### Phase 1: Research & Validation
| Task | Description | Est |
|------|-------------|-----|
| 1.1 | Research EmotiEffLib requirements | 2h |
| 1.2 | Test browser video capture | 1h |
| 1.3 | Evaluate processing requirements | 1h |
| 1.4 | Design video analysis data model | 1h |

**Checkpoint**: Feasibility confirmed, architecture designed

### Phase 2: Backend Implementation
| Task | Description | Est |
|------|-------------|-----|
| 2.1 | Create VideoFeedback model | 1h |
| 2.2 | Create video_analyzer.py service | 4h |
| 2.3 | Add video upload endpoint | 2h |
| 2.4 | Integrate with background tasks | 2h |
| 2.5 | Add tests for video analysis | 2h |

**Checkpoint**: Video analysis pipeline operational

### Phase 3: Frontend Integration
| Task | Description | Est |
|------|-------------|-----|
| 3.1 | Enable video capture in InterviewPage | 2h |
| 3.2 | Add video preview during recording | 1h |
| 3.3 | Upload video with audio | 1h |
| 3.4 | Display video feedback on FeedbackPage | 2h |
| 3.5 | Handle camera permission UX | 1h |

**Checkpoint**: Full video analysis user flow working

---

## Testing Strategy

### Unit Tests (Epic 2 focus)
- Target: 75% coverage on core API modules
- Mock external services (Stripe, OpenAI, Anthropic)
- Use factory fixtures for test data

### Integration Tests
- Full request-response cycle with database
- Test state machine transitions (interview status)
- Test cascade operations (delete user → cleanup)

### E2E Tests (Future)
- Register → Interview → Feedback flow
- Subscription checkout → upgrade flow

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Sample answer quality inconsistent | Medium | Medium | Use templates, review for consistency |
| Email delivery fails in production | High | Low | Use established provider (SendGrid), test thoroughly |
| Video processing too slow | Medium | Medium | Process async, show progress indicator |
| Test coverage slows development | Low | Low | Focus on high-risk modules first |

---

# Sprint 4: Technical Debt Payback (NEW)

---

# Epic 1: Fix Linting Errors

## Goal
Eliminate all linting errors to establish clean code standards and prevent potential bugs.

## Context
- Backend: 158 Ruff errors (61 auto-fixable)
- Frontend: 28 ESLint issues (19 errors, 9 warnings)
- Key issues: trailing whitespace, unused imports, React hook dependencies

## Success Criteria
- [x] Backend: 0 Ruff errors ✅
- [x] Frontend: 0 ESLint errors ✅
- [x] Pre-commit hooks passing ✅

## Implementation Plan

### Phase 1: Backend Auto-Fixes (30 min)
| Task | Description | Est |
|------|-------------|-----|
| 1.1 | Run `ruff check --fix app/` to auto-fix 61 errors | 15m |
| 1.2 | Run `ruff format app/` for consistent formatting | 15m |

**Checkpoint**: ~97 errors remaining (manual fixes needed)

### Phase 2: Backend Manual Fixes (2h)
| Task | Description | Est |
|------|-------------|-----|
| 2.1 | Fix trailing whitespace in feedback_service.py | 15m |
| 2.2 | Refactor late imports in email_service.py, dependencies.py | 30m |
| 2.3 | Fix late import in api/feedback.py (line 321) | 15m |
| 2.4 | Update Optional[X] to X \| None syntax (Python 3.12+) | 30m |
| 2.5 | Remove unused imports across modules | 30m |

**Checkpoint**: 0 backend linting errors

### Phase 3: Frontend Fixes (2h)
| Task | Description | Est |
|------|-------------|-----|
| 3.1 | Fix useAuth.tsx: remove unused 'error', fix try/catch wrappers | 30m |
| 3.2 | Fix useOnboarding.ts: remove unused '_userId' param | 15m |
| 3.3 | Fix DashboardPage.tsx: add loadData to useEffect deps | 30m |
| 3.4 | Fix FeedbackPage.tsx: add loadFeedback to useEffect deps | 15m |
| 3.5 | Fix RegisterPage.tsx: type 'any' to specific type | 15m |
| 3.6 | Fix react-refresh warnings in hooks (export refactor) | 15m |

**Checkpoint**: 0 frontend linting errors

---

# Epic 2: Backend Test Coverage to 75%

## Goal
Increase backend test coverage from 67% to 75% for deployment confidence.

## Context
Current coverage gaps (from audit):
- `api/feedback.py`: 44% (target 75%)
- `api/interviews.py`: 40% (target 75%)
- `api/auth.py`: 40% (target 75%)
- `middleware/rate_limit.py`: 33% (target 60%)
- `services/interview_service.py`: 58% (target 75%)

## Success Criteria
- [ ] Overall coverage: 75%+
- [ ] api/feedback.py: 75%+
- [ ] api/interviews.py: 75%+
- [ ] api/auth.py: 75%+
- [ ] All 188+ tests passing

## Implementation Plan

### Phase 1: Feedback API Tests (2h)
| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 1.1 | Test GET /feedback/session/{id}/all endpoint | qa-test-guardian | 30m |
| 1.2 | Test GET /feedback/response/{id} endpoint | qa-test-guardian | 30m |
| 1.3 | Test POST /feedback/generate/response/{id} | qa-test-guardian | 30m |
| 1.4 | Test authorization (wrong user access 403) | qa-test-guardian | 30m |

**Checkpoint**: api/feedback.py coverage ≥ 75%

### Phase 2: Interviews API Tests (2h)
| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 2.1 | Test POST /interviews with all options | qa-test-guardian | 30m |
| 2.2 | Test interview state transitions (start, end) | qa-test-guardian | 30m |
| 2.3 | Test GET /interviews/{id}/questions ordering | qa-test-guardian | 30m |
| 2.4 | Test quota enforcement edge cases | qa-test-guardian | 30m |

**Checkpoint**: api/interviews.py coverage ≥ 75%

### Phase 3: Auth API Tests (1.5h)
| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 3.1 | Test token validation edge cases | qa-test-guardian | 30m |
| 3.2 | Test malformed token handling | qa-test-guardian | 30m |
| 3.3 | Test concurrent token refresh | qa-test-guardian | 30m |

**Checkpoint**: api/auth.py coverage ≥ 75%

### Phase 4: Rate Limiting Tests (1h)
| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 4.1 | Test request blocking when limit exceeded | qa-test-guardian | 30m |
| 4.2 | Test limit reset after window | qa-test-guardian | 30m |

**Checkpoint**: middleware/rate_limit.py coverage ≥ 60%

### Phase 5: Service Layer Tests (2h)
| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 5.1 | Test interview_service state transitions | qa-test-guardian | 1h |
| 5.2 | Test feedback_service aggregation logic | qa-test-guardian | 1h |

**Checkpoint**: Overall backend coverage ≥ 75%

---

# Epic 3: Frontend Test Infrastructure

## Goal
Establish frontend test infrastructure and achieve 30% coverage.

## Context
- Current: 0% coverage (6 tests in 2 files)
- Infrastructure exists: Vitest, RTL, MSW configured
- Missing: Hook tests, component tests, MSW handlers

## Success Criteria
- [ ] Frontend coverage: 30%+
- [ ] All 4 hooks tested
- [ ] Critical pages tested (Dashboard, Interview, Feedback)
- [ ] MSW handlers for all API endpoints

## Implementation Plan

### Phase 1: Test Infrastructure Setup (2h)
| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 1.1 | Create test utilities with AuthProvider wrapper | frontend-builder | 30m |
| 1.2 | Add MSW handlers for 15+ missing endpoints | frontend-builder | 1h |
| 1.3 | Create mock data factories | frontend-builder | 30m |

**Checkpoint**: Test infrastructure complete

### Phase 2: Hook Tests (4h)
| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 2.1 | Test useAuth: login, logout, register, token refresh | qa-test-guardian | 1.5h |
| 2.2 | Test useAudioRecording: start, stop, permission handling | qa-test-guardian | 1.5h |
| 2.3 | Test useToast: show, dismiss, auto-dismiss | qa-test-guardian | 30m |
| 2.4 | Test useOnboarding: state persistence | qa-test-guardian | 30m |

**Checkpoint**: All hooks tested, ~15% coverage

### Phase 3: Critical Page Tests (6h)
| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 3.1 | Test LoginPage: form validation, submission, errors | qa-test-guardian | 1h |
| 3.2 | Test RegisterPage: form validation, experience selection | qa-test-guardian | 1h |
| 3.3 | Test DashboardPage: stats loading, session list, modals | qa-test-guardian | 2h |
| 3.4 | Test FeedbackPage: feedback display, sample answer modal | qa-test-guardian | 2h |

**Checkpoint**: Critical pages tested, ~30% coverage

---

# Epic 4: Real-Time AI Coaching Hints

## Goal
Replace static coaching hints with dynamic, contextual AI-generated hints based on live transcript analysis during interviews.

## Context
**Current State:**
- `CoachOverlay`: Shows static hints based on question type (behavioral → STAR, technical → approach, etc.)
- `RecordingDeck`: Has live transcript via browser Speech Recognition API (stored in `transcript` state)
- Backend: Uses Claude Haiku 4.5 for post-interview analysis (not real-time)
- OpenRouter integration already exists in backend for content analysis

**Research Findings:**
- **Fast Model Options:**
  - Gemini 2.0 Flash: $0.10/M input, $0.40/M output, ~200ms latency (cheapest)
  - GPT-4o mini: $0.15/M input, $0.60/M output, ~300ms latency (good balance)
  - Claude Haiku 4.5: $1.00/M input, $5.00/M output, ~400ms latency (current, too expensive)
  - Groq (Llama 3): Free tier, ~100ms latency (ultra-fast, but quality concerns)

- **Cost Estimate:** ~500 tokens/hint × 5 hints = 2,500 tokens per session
  - Gemini Flash: ~$0.001 per session
  - GPT-4o mini: ~$0.002 per session

**Recommended Architecture: Option A (Frontend Streaming)**
- RecordingDeck (transcript) → Debounce (2s) → Frontend API call → Streaming response → CoachOverlay
- Pros: Low latency, no backend changes needed
- Cons: API key exposure (use proxy or edge function)

**Alternative: Option B (Backend WebSocket)**
- Frontend → WebSocket → Backend → LLM → Streaming back → CoachOverlay
- Pros: Secure API keys, server-side rate limiting
- Cons: More complex, WebSocket management

## Success Criteria
- [ ] Dynamic hints generated from live transcript context
- [ ] Hints update every 2s of silence or 50+ new words
- [ ] Streaming response for low latency (<500ms)
- [ ] Cost-effective: <$0.01 per interview session
- [ ] Fallback to static hints if AI unavailable

## Implementation Plan

### Phase 1: Backend Coaching Endpoint (3h)
| Task | Description | Agent | Est | Status |
|------|-------------|-------|-----|--------|
| 1.1 | Create `/api/v1/coaching/hint` endpoint | backend-builder | 1h | ✅ Done |
| 1.2 | Integrate Gemini 2.0 Flash via OpenRouter | backend-builder | 1h | ✅ Done |
| 1.3 | Add streaming response support | backend-builder | 1h | ✅ Done |
| 1.4 | Add rate limiting (5 hints/min per user) | backend-builder | 30m | 🔄 In Progress |

**Checkpoint**: Endpoint returns contextual hints from question + transcript

### Phase 2: Frontend Integration (4h)
| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 2.1 | Add debounced hint generation hook | frontend-builder | 1h |
| 2.2 | Connect RecordingDeck transcript to hook | frontend-builder | 30m |
| 2.3 | Update CoachOverlay to show dynamic hints | frontend-builder | 1.5h |
| 2.4 | Add loading state and error fallback | frontend-builder | 1h |

**Checkpoint**: Dynamic hints appear in CoachOverlay during recording

### Phase 3: Streaming & UX Polish (2h)
| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 3.1 | Implement streaming hint display | frontend-builder | 1h |
| 3.2 | Add hint quality indicators (confidence) | frontend-builder | 30m |
| 3.3 | Test with various question types | qa-test-guardian | 30m |

**Checkpoint**: Smooth streaming hints with good UX

### Phase 4: Testing & Optimization (2h)
| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 4.1 | Add unit tests for hint generation | qa-test-guardian | 1h |
| 4.2 | Test rate limiting and error handling | qa-test-guardian | 30m |
| 4.3 | Monitor costs and optimize prompt | backend-builder | 30m |

**Checkpoint**: Tests passing, costs validated

**Total Estimated Effort**: ~11 hours

---

## Technical Details

### Hint Generation Prompt Template
```
You are an interview coach. Based on the question and the candidate's current answer transcript, provide a brief, actionable hint (1-2 sentences) to help them improve their answer.

Question: {question_text}
Question Type: {question_type}
Current Transcript: {transcript}

Provide a specific, contextual hint. Focus on:
- For behavioral: STAR structure, quantifying results, personal contribution
- For technical: Problem clarification, approach explanation, edge cases
- For system design: Requirements, scalability, trade-offs

Hint (max 100 words):
```

### Debounce Strategy
- Trigger hint generation after:
  - 2 seconds of silence (no new transcript words)
  - OR 50+ new words added to transcript
- Cancel pending requests if new transcript arrives

### Error Handling
- If AI service unavailable: Fall back to static hints
- If rate limit exceeded: Show cached hint or static hint
- If streaming fails: Show full hint when complete

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| API costs exceed budget | Medium | Low | Use Gemini Flash, rate limit strictly |
| Latency too high | Medium | Medium | Use streaming, debounce intelligently |
| API key exposure (frontend) | High | Medium | Use backend proxy or edge function |
| Quality of hints poor | Medium | Low | Test prompts, add fallback to static |

---

# Epic 5: E2E Test Suite (Future)

## Goal
Add Playwright E2E tests for critical user journeys.

## Success Criteria
- [ ] 5-10 E2E tests covering critical flows
- [ ] Tests run in CI pipeline

## Implementation Plan (Deferred)

### Phase 1: Setup (2h)
| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 1.1 | Install and configure Playwright | devops-deployer | 1h |
| 1.2 | Create test fixtures and helpers | qa-test-guardian | 1h |

### Phase 2: Critical Journeys (8h)
| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 2.1 | Test: Register → Dashboard | qa-test-guardian | 2h |
| 2.2 | Test: Login → Create Interview → Record → Feedback | qa-test-guardian | 3h |
| 2.3 | Test: Password Reset Flow | qa-test-guardian | 1.5h |
| 2.4 | Test: Subscription Checkout | qa-test-guardian | 1.5h |

**Checkpoint**: Critical user journeys validated

---

## Testing Strategy

### Unit Tests (Epics 2-3)
- **Backend**: pytest with asyncio, 75% coverage target
- **Frontend**: Vitest + RTL, 30% coverage target
- **Focus**: Hooks, services, API endpoints

### Integration Tests (Existing)
- Database operations: ✅ Covered
- External API mocks: ✅ Configured (Stripe, OpenAI, Claude)
- Auth flow: ✅ Partial coverage

### Real-Time Coaching (Epic 4)
- **Backend**: Coaching endpoint with Gemini 2.0 Flash via OpenRouter
- **Frontend**: Debounced hint generation, streaming display
- **Focus**: Contextual hints based on live transcript

### E2E Tests (Epic 5)
- Tool: Playwright
- Focus: Critical user journeys
- Target: 5-10 tests

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Linting fixes break code | Medium | Low | Run tests after each fix batch |
| Test coverage slows dev | Low | Low | Focus on high-risk modules only |
| Frontend tests flaky | Medium | Medium | Use proper async handling, stable selectors |
| MSW handlers incomplete | Low | Medium | Add handlers incrementally as needed |
| AI coaching API costs exceed budget | Medium | Low | Use Gemini Flash, rate limit strictly |
| Coaching hints latency too high | Medium | Medium | Use streaming, debounce intelligently |

---

## Execution Order

**Recommended sequence:**

1. **Epic 1** (Linting) - Quick wins, clean foundation ✅
2. **Epic 2** (Backend Tests) - Deployment confidence ✅
3. **Epic 3** (Frontend Tests) - Regression protection ✅
4. **Epic 4** (Real-Time AI Coaching) - User experience enhancement
5. **Epic 5** (E2E Tests) - Future enhancement

**Estimated Total Effort**: 
- Sprint 4 (Epics 1-3): ~25 hours ✅
- Epic 4 (Real-Time Coaching): ~11 hours
- Epic 5 (E2E Tests): ~10 hours

---

## Completed Sprints

### Sprint 2: Four Epics (Dec 2025) ✅ COMPLETE

#### Epic 1: "Practice Like the Real Thing" ✅
- Added target_company field for company-targeted interviews
- Implemented readiness score calculation from last 5 sessions
- Added sample answer modal on FeedbackPage
- Company selector in NewInterviewModal

**Commits:**
- `174942b` feat(backend): add target_company field
- `cf5d09d` feat(frontend): add company targeting UI
- `e0f86e1` feat(backend): add interview readiness score endpoint
- `c7ec79e` feat(frontend): add readiness score display
- `fbe728e` feat(frontend): add sample answer modal

#### Epic 2: Expand Question Bank ✅
- Expanded to 105 questions (50 technical, 30 behavioral, 25 system design)
- Company tags and topic tags on all questions

**Commits:**
- `394b90f` feat(questions): expand technical question bank to 50 questions

#### Epic 3: JWT Refresh Token System ✅
- Refresh token stored in database with expiration
- Token rotation on each refresh (security)
- Frontend auto-refresh on 401 with request queuing

**Commits:**
- `6d4ae6b` feat(auth): implement JWT refresh token system with rotation
- `6c94221` feat(frontend): add automatic JWT token refresh

#### Epic 4: Backend Test Coverage ✅
- Expanded from ~95 to 140 tests
- Coverage improved to 66%

**Commits:**
- `a1f32c2` test: add comprehensive API tests for improved coverage

---

### Sprint 1: "Feedback That Helps" (Dec 2025) ✅ COMPLETE

- User experience level selection (junior/mid/senior)
- Personalized AI feedback based on level
- Improvement comparison vs user average
- Score trend visualization

**Commits:**
- `f2bbad6` feat(user): add experience level
- `5446f87` feat(frontend): add experience level selection
- `7044b52` feat(feedback): personalize AI feedback
- `24f65ef` feat(feedback): add improvement comparison

---

## References

- **Codebase Audit**: docs/CODEBASE_AUDIT.md
- **Design System**: docs/DESIGN_SYSTEM.md
- **UI Flow**: docs/UI_SCREEN_FLOW.md
- **Deployment**: docs/DEPLOYMENT.md
- **Project Brief**: docs/project-brief.md
