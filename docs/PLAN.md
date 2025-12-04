# CareerSwiftr Interview Simulator - Implementation Plan

## Current Status: Sprint 2 Planning
## Last Updated: 2025-12-04

---

## Completed Milestones

### ✅ Milestone: Test Suite Regressions (Dec 3)
- Fixed ContentAnalyzer tests (8 failures → 0)
- Fixed subscription webhook test (1 failure → 0)
- All 95 tests passing with 66% coverage

### ✅ Milestone: Stripe Subscription Flow (Dec 2-3)
- Checkout session creation
- Webhook handling for subscription events
- Cancel subscription with UI update
- Stripe API compatibility for 2025-11-17 version
- Subscription sync from Stripe on page load

### ✅ Milestone: Soft Launch Ready (Dec 2)
- All core features working
- Dark mode with system detection
- Mobile navigation
- Branded assets integrated
- 10 screens validated feature-complete

---

## ✅ Completed Sprint: "Feedback That Helps"

### Goal
Transform generic feedback into personalized, actionable guidance that accelerates interview improvement.

### Success Criteria (All Met)
- [x] Users can set their experience level (junior/mid/senior) ✅ Done
- [x] Feedback adjusts expectations based on level ✅ Done (Phase 3)
- [x] Dashboard shows score trend over last 10 sessions ✅ Already existed
- [x] FeedbackPage shows improvement % vs average ✅ Done (Phase 4)

---

## Implementation Tasks

### Phase 1: User Experience Level (Backend) ✅ COMPLETE
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 1.1 | Add `experience_level` enum to User model | 30m | ✅ Done |
| 1.2 | Create Alembic migration | 15m | ✅ Done |
| 1.3 | Add experience_level to registration endpoint | 30m | ✅ Done |
| 1.4 | Add PATCH endpoint to update experience level | 30m | ✅ Done |
| 1.5 | Add tests for new endpoints | 30m | ✅ Done |

**Commits:**
- `f2bbad6` - feat(user): add experience level for personalized feedback

### Phase 2: User Experience Level (Frontend) ✅ COMPLETE
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 2.1 | Add experience level select to RegisterPage | 30m | ✅ Done |
| 2.2 | Add experience level field to SettingsPage | 30m | ✅ Done |
| 2.3 | Update auth context with experience level | 15m | ✅ Done |

**Commits:**
- `5446f87` - feat(frontend): add experience level selection to register and settings

### Phase 3: Personalized Feedback ✅ COMPLETE
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 3.1 | Update ContentAnalyzer.analyze() to accept experience_level param | 30m | ✅ Done |
| 3.2 | Create experience-level-specific prompt templates | 1h | ✅ Done |
| 3.3 | Update FeedbackService to fetch user's experience_level | 45m | ✅ Done |
| 3.4 | Add unit tests for experience-level-aware feedback | 1h | ✅ Done |
| 3.5 | Add "Tailored for {level}" indicator to FeedbackPage | 30m | ✅ Done |

**Commits:**
- `7044b52` - feat(feedback): personalize AI feedback based on user experience level

**Implementation Summary:**
- Added `EXPERIENCE_CONTEXT` dict with junior/mid/senior prompts to `ContentAnalyzer`
- Updated `analyze()` method to accept and use `experience_level` parameter
- Updated `FeedbackService.generate_feedback()` to fetch user's experience_level from DB
- Added 4 new tests (103 total passing)
- Added "Feedback tailored for {level}" indicator to FeedbackPage

### Phase 4: Progress Tracking ✅ COMPLETE
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 4.1 | ~~Add score history endpoint (last 10 sessions)~~ | - | ✅ Already exists (`/users/me/progress`) |
| 4.2 | ~~Add score trend chart to DashboardPage~~ | - | ✅ Already exists (ProgressChart component) |
| 4.3 | Add session comparison endpoint | 30m | ✅ Done |
| 4.4 | Show improvement % on FeedbackPage | 1h | ✅ Done |

**Discovery Notes:**
The exploration revealed existing infrastructure:
- `GET /users/me/stats` - Returns total_sessions, completed_sessions, average_score, total_practice_time_seconds
- `GET /users/me/progress` - Returns score_trend (last 20 sessions with scores and dates)
- `ProgressChart` component - SVG-based line chart with trend direction indicator
- `StatsOverview` component - Displays overall stats on Dashboard

**Implementation Summary:**
- Added `GET /feedback/session/{id}/comparison` endpoint to return session score vs user average
- Added ImprovementBanner to FeedbackPage showing "+X% vs your average" with trend icons
- Frontend API updated with `feedbackAPI.getComparison()` method
- All 103 tests passing

---

# Sprint 2: Four Epics

## Overview

This sprint combines four high-priority epics to maximize user value and technical foundation:

1. **Epic 1**: "Practice Like the Real Thing" - Company targeting and readiness scoring
2. **Epic 2**: Expand Question Bank Quality - More questions and sample answers
3. **Epic 3**: JWT Refresh Token System - Session persistence and security
4. **Epic 4**: Backend Test Coverage - Improve coverage to 75%

**Target**: Complete all 4 epics
**Tests**: Maintain 103+ passing, target 75% coverage on core API modules

---

## Epic 1: "Practice Like the Real Thing"

### Goal
Help users prepare for specific companies with tailored practice and readiness tracking.

### Success Criteria
- [ ] Users can select target company when creating interview
- [ ] Questions are filtered by company_tags matching selection
- [ ] Interview Readiness Score calculated from last 5 sessions
- [ ] Readiness displayed on Dashboard
- [ ] Sample answers visible after response submission

### Technical Design

**Data Model Changes:**
- Add `target_company: str | None` field to InterviewSession model
- Existing: `company_style` for interview style (faang/startup/enterprise)
- Existing: `company_tags` array on Question model for filtering
- Existing: `sample_answer` field on Question model (already present)

**API Changes:**
- Update `InterviewSessionCreate` schema to accept `target_company`
- Add `GET /users/me/readiness-score` endpoint
- Update question assignment logic in InterviewService

**Frontend Changes:**
- Add company selector dropdown to NewInterviewModal
- Add ReadinessScore component to Dashboard
- Add SampleAnswerModal to FeedbackPage

### Implementation Tasks

#### Phase 1: Backend - Company Targeting ✅ COMPLETE
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 1.1 | Add `target_company` field to InterviewSession model | 30m | ✅ Done |
| 1.2 | Create Alembic migration | 15m | ✅ Done |
| 1.3 | Update InterviewSessionCreate schema | 15m | ✅ Done |
| 1.4 | Update InterviewService.assign_questions() to filter by company_tags | 1h | ✅ Done |
| 1.5 | Add tests for company-filtered question assignment | 45m | ✅ Done |

**Commits:**
- `174942b` - feat(backend): add target_company field for company-targeted interviews

**Checkpoint**: ✅ Creating interview with target_company filters questions correctly

#### Phase 2: Frontend - Company Selection ✅ COMPLETE
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 2.1 | Add company dropdown to NewInterviewModal | 45m | ✅ Done |
| 2.2 | Update interviewsAPI.create() to send target_company | 15m | ✅ Done |
| 2.3 | Update types/index.ts with new fields | 15m | ✅ Done |
| 2.4 | Display target company on InterviewCard | 30m | ✅ Done |

**Commits:**
- `cf5d09d` - feat(frontend): add company targeting UI for interviews

**Checkpoint**: ✅ Users can select company when starting interview

#### Phase 3: Backend - Readiness Score
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 3.1 | Add `GET /users/me/readiness-score` endpoint | 1h | ✅ Complete |
| 3.2 | Calculate readiness from last 5 sessions' scores | 30m | ✅ Complete |
| 3.3 | Add tests for readiness endpoint | 30m | ✅ Complete |

**Commits:**
- `e0f86e1` - feat(backend): add interview readiness score endpoint

**Checkpoint**: ✅ Readiness score returns valid percentage based on practice history

#### Phase 4: Frontend - Readiness Display
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 4.1 | Create ReadinessScore component | 1h | ✅ Complete |
| 4.2 | Add to DashboardPage layout | 30m | ✅ Complete |
| 4.3 | Add userAPI.getReadinessScore() method | 15m | ✅ Complete |

**Commits:**
- `c7ec79e` - feat(frontend): add interview readiness score display to dashboard

**Checkpoint**: ✅ Dashboard shows interview readiness percentage

#### Phase 5: Sample Answers
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 5.1 | Create SampleAnswerModal component | 1h | ✅ Complete |
| 5.2 | Add "View Sample Answer" button to ResponseAccordion | 30m | ✅ Complete |
| 5.3 | Style sample answer with highlighting | 30m | ✅ Complete |

**Commits:**
- `fbe728e` - feat(frontend): add sample answer modal for interview feedback

**Checkpoint**: ✅ Users can view model answer after submitting response

---

### Epic 1 Progress Summary
- Phase 1 (Backend - Company Targeting): ✅ Complete
- Phase 2 (Frontend - Company Selection): ✅ Complete
- Phase 3 (Backend - Readiness Score): ✅ Complete
- Phase 4 (Frontend - Readiness Display): ✅ Complete
- Phase 5 (Sample Answers): ✅ Complete

**Epic 1 Complete!** All phases implemented and tested.

---

## Epic 2: Expand Question Bank Quality

### Goal
Provide more diverse practice material and reference answers for self-evaluation.

### Success Criteria
- [ ] Question bank expanded from 75 to 150+ questions
- [ ] 50 new technical questions added
- [ ] 25 new system design questions added
- [ ] Sample answers written for top 50 most-used questions

### Technical Design

**Question Categories:**
- BEHAVIORAL: 25+ questions (existing)
- TECHNICAL: 70+ questions (add 50)
- SYSTEM_DESIGN: 55+ questions (add 25)

**Difficulty Distribution:**
- EASY: 30%
- MEDIUM: 50%
- HARD: 20%

**Company Tags:**
- google, amazon, meta, apple, microsoft, netflix
- stripe, airbnb, uber, lyft, doordash
- startup, enterprise, remote

### Implementation Tasks

#### Phase 1: Technical Questions
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 1.1 | Add 20 algorithm questions (arrays, trees, graphs) | 2h | Pending |
| 1.2 | Add 15 data structure questions | 1.5h | Pending |
| 1.3 | Add 15 coding pattern questions (DP, backtracking) | 1.5h | Pending |

**Checkpoint**: 50 new technical questions seeded to database

#### Phase 2: System Design Questions
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 2.1 | Add 10 distributed systems questions | 1h | Pending |
| 2.2 | Add 10 scaling/performance questions | 1h | Pending |
| 2.3 | Add 5 real-world scenario questions | 45m | Pending |

**Checkpoint**: 25 new system design questions seeded to database

#### Phase 3: Sample Answers
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 3.1 | Write sample answers for 20 behavioral questions | 2h | Pending |
| 3.2 | Write sample answers for 20 technical questions | 2h | Pending |
| 3.3 | Write sample answers for 10 system design questions | 1.5h | Pending |

**Checkpoint**: 50 questions have sample_answer populated

---

## Epic 3: JWT Refresh Token System

### Goal
Improve session persistence so users don't need to re-login frequently.

### Success Criteria
- [ ] Refresh tokens stored securely in database
- [ ] Automatic token refresh on 401 errors
- [ ] Token rotation on each refresh (security)
- [ ] Access token: 15 minutes, Refresh token: 7 days

### Technical Design

**User Model Changes:**
```python
refresh_token: str | None = Field(default=None, max_length=512)
refresh_token_expires_at: datetime | None = Field(default=None)
```

**Token Schema:**
```python
class Token(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
```

**New Endpoint:**
```
POST /auth/refresh
Body: { "refresh_token": "..." }
Response: { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }
```

### Implementation Tasks

#### Phase 1: Backend - Token Storage
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 1.1 | Add refresh_token fields to User model | 30m | Pending |
| 1.2 | Create Alembic migration | 15m | Pending |
| 1.3 | Update Token schema to include refresh_token | 15m | Pending |

**Checkpoint**: User model can store refresh tokens

#### Phase 2: Backend - Token Generation
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 2.1 | Create create_refresh_token() in security.py | 30m | Pending |
| 2.2 | Update login endpoint to generate and store refresh token | 45m | Pending |
| 2.3 | Create POST /auth/refresh endpoint | 1h | Pending |
| 2.4 | Implement token rotation (invalidate old, issue new) | 30m | Pending |
| 2.5 | Add tests for refresh flow | 1h | Pending |

**Checkpoint**: /auth/refresh returns new access + refresh tokens

#### Phase 3: Frontend - Auto Refresh
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 3.1 | Store refresh_token in localStorage on login | 15m | Pending |
| 3.2 | Update axios interceptor to call refresh on 401 | 1h | Pending |
| 3.3 | Update AuthContext to handle token refresh | 30m | Pending |
| 3.4 | Add retry logic for original request after refresh | 30m | Pending |

**Checkpoint**: Expired token triggers automatic refresh and retry

---

## Epic 4: Backend Test Coverage

### Goal
Increase test coverage to 75% on core API modules to prevent regressions.

### Success Criteria
- [ ] feedback.py: 39% → 75%
- [ ] interviews.py: 39% → 75%
- [ ] subscriptions.py: 40% → 75%
- [ ] users.py: 43% → 75%

### Current Coverage Report
| Module | Stmts | Miss | Cover | Target |
|--------|-------|------|-------|--------|
| app/api/feedback.py | 85 | 52 | 39% | 75% |
| app/api/interviews.py | 148 | 90 | 39% | 75% |
| app/api/subscriptions.py | 202 | 121 | 40% | 75% |
| app/api/users.py | 90 | 51 | 43% | 75% |

### Implementation Tasks

#### Phase 1: Test Infrastructure
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 1.1 | Create reusable fixtures (user, interview, responses) | 1h | Pending |
| 1.2 | Create mock factory for feedback data | 30m | Pending |

**Checkpoint**: Shared fixtures available for all test files

#### Phase 2: Feedback API Tests
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 2.1 | Test GET /feedback/session/{id} endpoint | 30m | Pending |
| 2.2 | Test GET /feedback/session/{id}/all endpoint | 30m | Pending |
| 2.3 | Test GET /feedback/response/{id} endpoint | 30m | Pending |
| 2.4 | Test POST /feedback/generate/session/{id} | 45m | Pending |
| 2.5 | Test GET /feedback/session/{id}/comparison | 30m | Pending |
| 2.6 | Test authorization (wrong user) | 30m | Pending |
| 2.7 | Test not-found cases | 30m | Pending |

**Checkpoint**: feedback.py coverage ≥ 75%

#### Phase 3: Interviews API Tests
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 3.1 | Test POST /interviews (create) | 30m | Pending |
| 3.2 | Test POST /interviews/{id}/start | 30m | Pending |
| 3.3 | Test GET /interviews/{id}/questions | 30m | Pending |
| 3.4 | Test POST /interviews/{id}/responses | 45m | Pending |
| 3.5 | Test POST /interviews/{id}/end | 30m | Pending |
| 3.6 | Test DELETE /interviews/{id} | 30m | Pending |
| 3.7 | Test edge cases (invalid state transitions) | 45m | Pending |
| 3.8 | Test quota enforcement for free users | 30m | Pending |

**Checkpoint**: interviews.py coverage ≥ 75%

#### Phase 4: Subscriptions API Tests
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 4.1 | Test GET /subscriptions/status | 30m | Pending |
| 4.2 | Test POST /subscriptions/checkout | 45m | Pending |
| 4.3 | Test POST /subscriptions/portal | 30m | Pending |
| 4.4 | Test POST /subscriptions/cancel | 30m | Pending |
| 4.5 | Test webhook events (invoice.paid, subscription.deleted) | 1h | Pending |
| 4.6 | Test Stripe error handling | 30m | Pending |

**Checkpoint**: subscriptions.py coverage ≥ 75%

#### Phase 5: Users API Tests
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 5.1 | Test POST /users/register validation | 30m | Pending |
| 5.2 | Test PATCH /users/me profile updates | 30m | Pending |
| 5.3 | Test POST /users/me/change-password | 30m | Pending |
| 5.4 | Test DELETE /users/me (soft delete) | 30m | Pending |
| 5.5 | Test GET /users/me/stats | 30m | Pending |
| 5.6 | Test GET /users/me/progress | 30m | Pending |

**Checkpoint**: users.py coverage ≥ 75%

---

## Testing Strategy

### Unit Tests
- Mock external services (Stripe, OpenAI, Anthropic)
- Test each endpoint with valid/invalid inputs
- Verify authorization checks

### Integration Tests
- Full request-response cycle with database
- Test cascade operations (delete user → cleanup data)
- Test state machine transitions (interview status)

### Coverage Target
- Overall: 75% (currently 66%)
- Core API modules: 75% each

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Token refresh race conditions | High | Medium | Use version field, proper async handling |
| Company tags don't match questions | Medium | Low | Audit existing questions, add missing tags |
| Sample answer quality inconsistent | Medium | Medium | Use evaluation_criteria as quality guide |
| Test coverage slows development | Low | Medium | Focus on critical paths first |

---

## Execution Order

**Recommended sequence** (can parallelize where noted):

1. **Epic 4, Phase 1**: Test infrastructure (enables all other testing)
2. **Epic 3, Phase 1-2**: Token storage + generation (backend complete)
3. **Epic 1, Phase 1-2**: Company targeting + readiness (backend complete)
4. **Epic 2, Phase 1-2**: Add new questions (parallel with backend work)
5. **Epic 3, Phase 3**: Frontend token handling
6. **Epic 1, Phase 3-5**: Frontend company + readiness + samples
7. **Epic 2, Phase 3**: Write sample answers
8. **Epic 4, Phase 2-5**: Test coverage (continuous throughout)

---

## Technical Notes

### Experience Level Enum
```python
class ExperienceLevel(str, Enum):
    JUNIOR = "junior"      # 0-2 years
    MID = "mid"            # 2-5 years
    SENIOR = "senior"      # 5+ years
```

### Claude Prompt Adjustments by Level
- **Junior**: Focus on fundamentals, be more encouraging, expect basic STAR usage
- **Mid**: Balanced expectations, look for depth and specificity
- **Senior**: High standards, expect leadership stories, strategic thinking

### Score History Query
```python
# Get last 10 completed sessions with scores
SELECT id, overall_score, created_at
FROM session_feedback sf
JOIN interview_session s ON sf.session_id = s.id
WHERE s.user_id = :user_id AND s.status = 'COMPLETED'
ORDER BY s.created_at DESC
LIMIT 10
```

---

## Quality Gates

Before marking sprint complete:
- [ ] All new endpoints have tests
- [ ] Full test suite passes (95+ tests)
- [ ] Frontend builds without errors
- [ ] Manual testing of registration → feedback flow
- [ ] Experience level visible in dashboard
- [ ] Score trend chart renders correctly

---

## References

- **Audit Report**: See docs/PROMPT.md for full codebase audit
- **Design System**: docs/DESIGN_SYSTEM.md
- **UI Flow**: docs/UI_SCREEN_FLOW.md
- **Deployment**: docs/DEPLOYMENT.md
