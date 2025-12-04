# Sprint 3: Quality & Content Foundation

## Status: ✅ In Progress (Audit Complete)
## Target: December 2025
## Audit Date: 2025-01-02

---

## Overview

Sprint 3 focuses on two pillars: **content quality** (sample answers for user learning) and **code quality** (test coverage to prevent regressions). These epics maximize value delivery while building a solid foundation for future features like email verification and video analysis.

**Priority Order:**
1. **Epic 1**: Sample Answers (highest user value, zero technical risk)
2. **Epic 2**: Test Coverage to 75% (enables confident deployments)
3. **Epic 3**: Email Verification (production readiness)
4. **Epic 4**: Video Analysis (future stretch goal)

---

## Success Criteria

- [ ] 50 questions have sample_answer populated (20 behavioral, 20 technical, 10 system design)
- [ ] Backend test coverage reaches 75% (from 66%)
- [ ] All 140+ tests continue passing
- [ ] Password reset flow sends actual emails (production)
- [ ] Email verification for registration (optional stretch)

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

## Execution Order

**Recommended sequence:**

1. **Epic 1** (Sample Answers) - Immediate user value, no risk
2. **Epic 2** (Test Coverage) - Enables confident changes
3. **Epic 3, Phase 1** (Email Production) - Production readiness
4. **Epic 3, Phase 2** (Email Verification) - Nice to have
5. **Epic 4** (Video Analysis) - Future enhancement

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

- **Codebase Audit**: docs/PROMPT.md
- **Design System**: docs/DESIGN_SYSTEM.md
- **UI Flow**: docs/UI_SCREEN_FLOW.md
- **Deployment**: docs/DEPLOYMENT.md
- **Project Brief**: docs/project-brief.md
