# CareerSwiftr Interview Simulator - Implementation Plan

## Current Status: Post-Launch Value Optimization
## Last Updated: 2025-12-03

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

## Active Sprint: "Feedback That Helps"

### Goal
Transform generic feedback into personalized, actionable guidance that accelerates interview improvement.

### Problem Statement
Current feedback is one-size-fits-all. A junior engineer gets the same advice as a senior. Users can't see if they're improving. This reduces perceived value and retention.

### Success Criteria
- [ ] Users can set their experience level (junior/mid/senior)
- [ ] Feedback adjusts expectations based on level
- [ ] Dashboard shows score trend over last 10 sessions
- [ ] FeedbackPage shows improvement % vs average

---

## Implementation Tasks

### Phase 1: User Experience Level (Backend)
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 1.1 | Add `experience_level` enum to User model | 30m | Pending |
| 1.2 | Create Alembic migration | 15m | Pending |
| 1.3 | Add experience_level to registration endpoint | 30m | Pending |
| 1.4 | Add PATCH endpoint to update experience level | 30m | Pending |
| 1.5 | Add tests for new endpoints | 30m | Pending |

**Files to modify:**
- `backend/app/models/user.py` - Add ExperienceLevel enum
- `backend/app/api/users.py` - Update register and add endpoint
- `backend/tests/test_users.py` - Add tests

### Phase 2: User Experience Level (Frontend)
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 2.1 | Add experience level select to RegisterPage | 30m | Pending |
| 2.2 | Add experience level field to SettingsPage | 30m | Pending |
| 2.3 | Update auth context with experience level | 15m | Pending |

**Files to modify:**
- `frontend/src/pages/RegisterPage.tsx`
- `frontend/src/pages/SettingsPage.tsx`
- `frontend/src/types/index.ts`

### Phase 3: Personalized Feedback
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 3.1 | Update content analyzer prompt by experience level | 1h | Pending |
| 3.2 | Add level-specific scoring adjustments | 30m | Pending |
| 3.3 | Test feedback quality at each level | 30m | Pending |

**Files to modify:**
- `backend/app/ai/content_analyzer.py` - Adjust prompts
- `backend/app/services/feedback_service.py` - Pass level through

### Phase 4: Progress Tracking
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 4.1 | Add score history endpoint (last 10 sessions) | 1h | Pending |
| 4.2 | Calculate improvement % vs user's average | 30m | Pending |
| 4.3 | Add score trend chart to DashboardPage | 2h | Pending |
| 4.4 | Show improvement % on FeedbackPage | 1h | Pending |

**Files to modify:**
- `backend/app/api/users.py` - New endpoint
- `frontend/src/pages/DashboardPage.tsx` - Trend chart
- `frontend/src/pages/FeedbackPage.tsx` - Improvement indicator

---

## Future Sprints

### Sprint 2: "Practice Like the Real Thing"
- Target company customization
- Interview readiness score
- Add sample answers to 75 questions

### Sprint 3: "More Questions, Better Quality"
- Expand question bank to 150+
- Improve filler word detection with NLP
- Add pause/pacing analysis

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
