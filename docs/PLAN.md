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
- [x] Users can set their experience level (junior/mid/senior) ✅ Done
- [ ] Feedback adjusts expectations based on level (Phase 3 - IN PROGRESS)
- [ ] Dashboard shows score trend over last 10 sessions (Phase 4)
- [ ] FeedbackPage shows improvement % vs average (Phase 4)

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

### Phase 3: Personalized Feedback - 🔄 IN PROGRESS
| Task | Description | Est | Status |
|------|-------------|-----|--------|
| 3.1 | Update ContentAnalyzer.analyze() to accept experience_level param | 30m | Pending |
| 3.2 | Create experience-level-specific prompt templates | 1h | Pending |
| 3.3 | Update FeedbackService to fetch user's experience_level | 45m | Pending |
| 3.4 | Add unit tests for experience-level-aware feedback | 1h | Pending |
| 3.5 | Add "Tailored for {level}" indicator to FeedbackPage | 30m | Pending |

**Files to modify:**
- `backend/app/ai/content_analyzer.py` - Add experience_level param, personalized prompts
- `backend/app/services/feedback_service.py` - Fetch user.experience_level, pass to analyzer
- `backend/tests/test_api.py` - Add tests for personalized feedback
- `frontend/src/pages/FeedbackPage.tsx` - Show experience level indicator

**Detailed Implementation:**

#### Task 3.1-3.2: ContentAnalyzer Changes
Add experience-level context to ANALYSIS_PROMPT:
```python
EXPERIENCE_CONTEXT = {
    "junior": """
The candidate is a JUNIOR engineer (0-2 years experience). When providing feedback:
- Be encouraging and supportive in tone
- Acknowledge that they're still learning fundamentals
- Provide explicit, actionable tips they can apply immediately
- Focus on foundational skills rather than advanced concepts
- Score slightly more leniently on depth, but maintain standards for clarity
""",
    "mid": """
The candidate is a MID-LEVEL engineer (2-5 years experience). When providing feedback:
- Balance encouragement with constructive criticism
- Focus on growth areas and next-level skills
- Expect solid fundamentals but room for strategic thinking
- Provide actionable improvements for career advancement
""",
    "senior": """
The candidate is a SENIOR engineer (5+ years experience). When providing feedback:
- Be direct and concise - they can handle candid feedback
- Hold to higher standards for depth, leadership, and strategic thinking
- Focus on nuance, trade-offs, and system-wide implications
- Expect them to demonstrate mentorship and decision-making skills
- Point out areas where they could show more seniority
"""
}
```

#### Task 3.3: FeedbackService Changes
```python
# In generate_feedback(): fetch user.experience_level
user_result = await session.exec(select(User).where(User.id == interview.user_id))
user = user_result.first()
experience_level = user.experience_level if user else "mid"

# Pass to analyzer
feedback = await self.content_analyzer.analyze(
    transcript=response.transcript,
    question=question.content,
    question_type=question.category,
    experience_level=experience_level  # NEW
)
```

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
