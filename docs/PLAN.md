# Milestone: Sprint 10 - Code Quality & Feature Expansion

## Status: Ready
## Target: Sprint 10 (Dec 2025)

---

## Overview

Sprint 10 focuses on addressing accumulated technical debt before expanding features. With Sprint 9 (Conversational Voice Mentor) complete, we have 337 lint errors (206 backend + 131 frontend) and 38% test coverage that need attention before building new capabilities.

The sprint is organized into four epics:
1. **Epic 1**: Lint Cleanup & Code Quality (P0 - blocking)
2. **Epic 2**: Test Coverage Improvement (P1 - important)
3. **Epic 3**: Video Analysis MVP (P2 - feature expansion)
4. **Epic 4**: B2B Team Features (P2 - revenue expansion)

**Why This Order?**
- Epic 1 unblocks CI/CD and enables clean commits
- Epic 2 prevents regressions as we add features
- Epic 3 delivers the "multimodal feedback" promise from project brief
- Epic 4 opens higher-ARPU B2B revenue stream

---

## Success Criteria

- [x] Zero lint errors (backend + frontend) ✅ **COMPLETE**
- [ ] Backend test coverage ≥ 60% (currently 38%)
- [ ] API endpoint coverage ≥ 65% (currently 41.2%)
- [ ] Video analysis integrated into feedback pipeline
- [ ] Team subscription tier functional with admin dashboard

---

## Epic 1: Lint Cleanup & Code Quality ⭐ P0

**ICE Score**: 9.0/10 (Impact: 9, Confidence: 10, Ease: 9)
**Priority**: CRITICAL - Blocking CI/CD and clean commits
**Rationale**: 337 lint errors create tech debt, block CI, and make code review harder. Most are auto-fixable.

### Current State
- Backend: 206 errors (169 auto-fixable with `--fix`)
- Frontend: 131 errors (129 errors, 2 warnings)
- Categories: whitespace, unused vars, missing hook deps, any types

### Technical Design

No architecture changes needed. This is pure cleanup work.

**Backend (Ruff):**
- W293: Blank line contains whitespace (auto-fix)
- B007: Unused loop control variables (rename to `_`)
- F541: F-string without placeholders (auto-fix)
- F401: Unused imports (auto-fix)

**Frontend (ESLint):**
- `@typescript-eslint/no-unused-vars`: Unused variables in tests
- `react-hooks/exhaustive-deps`: Missing hook dependencies
- `@typescript-eslint/no-explicit-any`: Replace `any` with proper types

### Implementation Plan

#### Phase 1.1: Backend Auto-Fix ✅ COMPLETE

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 1.1.1 | Run `uv run ruff check --fix .` | - | 5m | ✅ Done |
| 1.1.2 | Run `uv run ruff check --fix --unsafe-fixes .` for remaining | - | 5m | ✅ Done |
| 1.1.3 | Manually fix remaining errors (loop vars, etc.) | - | 30m | ✅ Done (auto-fixed) |
| 1.1.4 | Verify with `uv run ruff check .` shows 0 errors | - | 5m | ✅ Done |
| 1.1.5 | Run `uv run pytest` to ensure no regressions | - | 5m | ✅ Done |

**Checkpoint**: ✅ `uv run ruff check .` shows 0 errors, all tests pass

---

#### Phase 1.2: Frontend Test File Cleanup ✅ COMPLETE

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 1.2.1 | Fix unused vars in `DashboardPage.test.tsx` | - | 15m | ✅ Done (already fixed) |
| 1.2.2 | Fix unused vars in `FeedbackPage.test.tsx` | - | 10m | ✅ Done (already fixed) |
| 1.2.3 | Fix unused vars in `InterviewPage.test.tsx` | - | 10m | ✅ Done (already fixed) |
| 1.2.4 | Fix unused vars in `PreparationPage.test.tsx` + any type | - | 15m | ✅ Done |
| 1.2.5 | Fix unused vars in `pageTestUtils.tsx` + any types | - | 15m | ✅ Done |
| 1.2.6 | Fix unused vars in `accessibility.test.tsx` | - | 5m | ✅ Done (already fixed) |

**Checkpoint**: ✅ Test file lint errors resolved

---

#### Phase 1.3: Frontend Source File Cleanup ✅ COMPLETE

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 1.3.1 | Fix unused `err` vars in `PreparationPage.tsx` (lines 188, 223) | - | 10m | ✅ Done (already correct) |
| 1.3.2 | Fix missing `loadComparison` dependency in useCallback | - | 15m | ✅ Done |
| 1.3.3 | Fix remaining unused vars across components | - | 30m | ✅ Done |
| 1.3.4 | Verify with `npm run lint` shows 0 errors | - | 5m | ✅ Done |
| 1.3.5 | Run `npm run build` to ensure no TypeScript errors | - | 2m | ✅ Done |

**Checkpoint**: ✅ `npm run lint` shows 0 errors, build passes

---

### Testing Strategy
- Run full test suite after backend fixes
- Run frontend build after lint fixes
- No new tests needed (cleanup only)

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Auto-fix breaks tests | Medium | Run tests immediately after fix |
| Hook dependency change affects behavior | Medium | Test affected components manually |

---

## Epic 2: Test Coverage Improvement (P1)

**ICE Score**: 7.5/10 (Impact: 9, Confidence: 8, Ease: 6)
**Priority**: HIGH - Prevents regressions, enables confident feature work
**Rationale**: 38% coverage is too low. API endpoints at 41.2% average is the biggest gap.

### Current State
- Overall: 38% coverage (2980 lines, 1845 uncovered)
- API modules: 40-44% average
- Critical gaps: `feedback_service.py` (12%), `interview_service.py` (18%)

### Target State
- Overall: ≥ 60% coverage
- API modules: ≥ 65% average
- Services: ≥ 50% coverage

### Technical Design

No new code - just tests for existing functionality.

**Priority Modules** (by uncovered lines):
1. `api/interviews.py` - 148 lines, 40% → target 70%
2. `api/feedback.py` - 148 lines, 44% → target 70%
3. `api/auth.py` - 148 lines, 40% → target 70%
4. `services/feedback_service.py` - 158 lines, 12% → target 50%
5. `services/interview_service.py` - 67 lines, 18% → target 50%

### Implementation Plan

#### Phase 2.1: API Endpoint Tests 🔄 IN PROGRESS

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 2.1.1 | Add tests for `api/interviews.py` error paths | qa-test-guardian | 2h | ✅ Done (9 tests added) |
| 2.1.2 | Add tests for `api/interviews.py` edge cases (cancel, duplicate) | qa-test-guardian | 1h | ✅ Done (covered in 2.1.1) |
| 2.1.3 | Add tests for `api/feedback.py` missing feedback scenarios | qa-test-guardian | 1.5h | ✅ Already covered |
| 2.1.4 | Add tests for `api/auth.py` refresh token edge cases | qa-test-guardian | 1h | ✅ Already covered |
| 2.1.5 | Add tests for `api/auth.py` password reset flow | qa-test-guardian | 1h | ✅ Already covered |

**Checkpoint**: ⏳ API coverage currently ~40-44%, target ≥ 65%

---

#### Phase 2.2: Service Layer Tests

| Task | Description | Agent/Skill | Est |
|------|-------------|-------------|-----|
| 2.2.1 | Add tests for `feedback_service.py` error handling | qa-test-guardian | 2h |
| 2.2.2 | Add tests for `feedback_service.py` async processing | qa-test-guardian | 1.5h |
| 2.2.3 | Add tests for `interview_service.py` session management | qa-test-guardian | 1.5h |
| 2.2.4 | Add tests for `background_tasks.py` failure scenarios | qa-test-guardian | 1h |

**Checkpoint**: Service coverage ≥ 50%

---

#### Phase 2.3: Coverage Verification

| Task | Description | Agent/Skill | Est |
|------|-------------|-------------|-----|
| 2.3.1 | Run full coverage report | - | 10m |
| 2.3.2 | Identify remaining gaps | - | 20m |
| 2.3.3 | Document coverage in CODEBASE_AUDIT.md | - | 15m |

**Checkpoint**: Overall coverage ≥ 60%

### Testing Strategy
- Use existing test infrastructure (pytest-asyncio, AsyncClient)
- Mock AI services (ContentAnalyzer, Transcriber)
- Database cleanup between tests (TRUNCATE CASCADE)
- Test error paths and edge cases, not just happy paths

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tests take longer than estimated | Medium | Focus on highest-impact modules first |
| Mock complexity increases | Low | Reuse existing mock patterns |

---

## Epic 3: Video Analysis MVP (P2)

**ICE Score**: 7.2/10 (Impact: 8, Confidence: 7, Ease: 7)
**Priority**: MEDIUM - Differentiating feature from project brief
**Rationale**: Project promises "multimodal feedback (audio + video + content)". Video is the missing piece.

### Current State
- Audio analysis: ✅ Librosa for speech rate, filler words, confidence
- Content analysis: ✅ Claude for technical accuracy, structure
- Video analysis: ❌ Not implemented

### Target State
- Basic emotion detection (nervousness, confidence)
- Eye contact tracking (looking at camera vs. away)
- Video metrics integrated into overall feedback score

### Technical Design

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Video Analysis Pipeline                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Frontend (WebRTC)          Backend (FastAPI)                   │
│  ┌──────────────┐           ┌──────────────┐                   │
│  │ Video        │  POST     │ /upload/     │                   │
│  │ Capture      │ ───────── │ video        │                   │
│  └──────────────┘           └──────┬───────┘                   │
│                                    │                            │
│                                    v                            │
│                             ┌──────────────┐                   │
│                             │ VideoAnalyzer│                   │
│                             │ (EmotiEffLib)│                   │
│                             └──────┬───────┘                   │
│                                    │                            │
│                                    v                            │
│                             ┌──────────────┐                   │
│                             │ VideoFeedback│                   │
│                             │ Model        │                   │
│                             └──────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Data Models

```python
# backend/app/models/video_feedback.py
class VideoFeedback(SQLModel, table=True):
    __tablename__ = "video_feedback"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    response_id: UUID = Field(foreign_key="interview_responses.id", unique=True)

    # Emotion metrics (0-1 scale)
    confidence_score: float = Field(default=0.0)
    nervousness_score: float = Field(default=0.0)
    engagement_score: float = Field(default=0.0)

    # Eye contact metrics
    eye_contact_percentage: float = Field(default=0.0)
    looking_away_count: int = Field(default=0)

    # Gesture metrics (future)
    fidget_count: Optional[int] = None
    hand_gesture_frequency: Optional[float] = None

    # Processing
    processing_duration_ms: int = Field(default=0)
    frame_count: int = Field(default=0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

#### API Contracts

```
POST /api/v1/upload/video
Content-Type: multipart/form-data
Body: { file: <video_file>, response_id: UUID }
Response: { video_id: UUID, status: "processing" }

GET /api/v1/feedback/video/{response_id}
Response: {
    confidence_score: 0.72,
    nervousness_score: 0.35,
    eye_contact_percentage: 0.68,
    looking_away_count: 5,
    recommendations: [
        "Maintain more consistent eye contact",
        "Good confidence level detected"
    ]
}
```

### Implementation Plan

#### Phase 3.1: Research & Setup

| Task | Description | Agent/Skill | Est |
|------|-------------|-------------|-----|
| 3.1.1 | Research EmotiEffLib capabilities and requirements | - | 2h |
| 3.1.2 | Evaluate alternative: OpenCV + face detection | - | 1h |
| 3.1.3 | Set up video processing dependencies | - | 1h |
| 3.1.4 | Create VideoFeedback model + migration | backend-engineer | 1h |

**Checkpoint**: Video analysis dependencies installed, model created

---

#### Phase 3.2: Backend Video Analyzer

| Task | Description | Agent/Skill | Est |
|------|-------------|-------------|-----|
| 3.2.1 | Create `ai/video_analyzer.py` base service | backend-engineer | 3h |
| 3.2.2 | Implement emotion detection using EmotiEffLib | backend-engineer | 3h |
| 3.2.3 | Implement eye contact tracking | backend-engineer | 2h |
| 3.2.4 | Add error handling and fallback metrics | backend-engineer | 1h |
| 3.2.5 | Write unit tests for video analyzer | qa-test-guardian | 2h |

**Checkpoint**: Video analyzer service functional with tests

---

#### Phase 3.3: Backend API Integration

| Task | Description | Agent/Skill | Est |
|------|-------------|-------------|-----|
| 3.3.1 | Add video upload endpoint to `api/upload.py` | backend-engineer | 1.5h |
| 3.3.2 | Add video feedback endpoint to `api/feedback.py` | backend-engineer | 1h |
| 3.3.3 | Integrate video analysis into response processing | backend-engineer | 2h |
| 3.3.4 | Add video feedback to overall feedback aggregation | backend-engineer | 1h |
| 3.3.5 | Write API tests | qa-test-guardian | 1.5h |

**Checkpoint**: Video upload and feedback APIs functional

---

#### Phase 3.4: Frontend Integration

| Task | Description | Agent/Skill | Est |
|------|-------------|-------------|-----|
| 3.4.1 | Add video recording to InterviewPage | frontend-builder | 3h |
| 3.4.2 | Create VideoFeedbackCard component | frontend-builder | 2h |
| 3.4.3 | Integrate video metrics into FeedbackPage | frontend-builder | 1.5h |
| 3.4.4 | Add video toggle in interview settings | frontend-builder | 1h |
| 3.4.5 | Write component tests | qa-test-guardian | 1.5h |

**Checkpoint**: Video recording and feedback display working

---

### Dependencies

**External:**
- EmotiEffLib or OpenCV for video analysis
- FFmpeg for video processing (already available in Python ecosystem)

**Internal:**
- Existing upload endpoint pattern (`api/upload.py`)
- Existing feedback aggregation (`services/feedback_service.py`)
- WebRTC video capture (similar to audio)

### Testing Strategy

- **Unit Tests**: VideoAnalyzer service with sample video frames
- **Integration Tests**: Upload → analyze → retrieve feedback flow
- **E2E Tests**: Record interview with video → view video feedback

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| EmotiEffLib not suitable | High | Evaluate OpenCV + fer as fallback |
| Video processing too slow | Medium | Process async, show "processing" state |
| Large video files | Medium | Compress on client, limit duration |
| Privacy concerns | High | Document video usage, add opt-out |

---

## Epic 4: B2B Team Features (P2)

**ICE Score**: 6.5/10 (Impact: 8, Confidence: 7, Ease: 5)
**Priority**: MEDIUM - Higher ARPU revenue stream
**Rationale**: B2B tiers ($199-499/mo) are 3-7x higher than B2C ($29-79/mo). Opens enterprise market.

### Current State
- User model: Individual accounts only
- Subscription: FREE, PRO, PREMIUM tiers (B2C)
- No team/organization concept

### Target State
- Team model with admin/member roles
- Team subscription tier ($199/mo for 10 seats)
- Admin dashboard with team usage stats
- Member invitation flow

### Technical Design

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Team Subscription Model                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Organizations          Teams              Users                │
│  ┌──────────┐          ┌──────────┐       ┌──────────┐         │
│  │ Org      │ 1───────N│ Team     │N─────N│ User     │         │
│  │          │          │          │       │          │         │
│  │ - name   │          │ - name   │       │ - email  │         │
│  │ - plan   │          │ - seats  │       │ - role   │         │
│  └──────────┘          └──────────┘       └──────────┘         │
│                                                                  │
│  Team Roles: ADMIN, MEMBER                                      │
│  Org Plans: TEAM ($199), ENTERPRISE ($499)                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Data Models

```python
# backend/app/models/team.py
class Team(SQLModel, table=True):
    __tablename__ = "teams"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100)
    slug: str = Field(max_length=100, unique=True)

    # Subscription
    subscription_tier: str = Field(default="team")  # team, enterprise
    max_seats: int = Field(default=10)
    stripe_subscription_id: Optional[str] = None

    # Settings
    custom_questions_enabled: bool = Field(default=False)
    sso_enabled: bool = Field(default=False)

    created_at: datetime
    updated_at: Optional[datetime]

class TeamMembership(SQLModel, table=True):
    __tablename__ = "team_memberships"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    team_id: UUID = Field(foreign_key="teams.id")
    user_id: UUID = Field(foreign_key="users.id")
    role: str = Field(default="member")  # admin, member

    invited_by: Optional[UUID] = Field(foreign_key="users.id")
    invited_at: datetime
    accepted_at: Optional[datetime]

class TeamInvitation(SQLModel, table=True):
    __tablename__ = "team_invitations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    team_id: UUID = Field(foreign_key="teams.id")
    email: str
    role: str = Field(default="member")
    token: str = Field(unique=True)

    invited_by: UUID = Field(foreign_key="users.id")
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime]
```

#### API Contracts

```
# Team Management
POST /api/v1/teams
Body: { name: string }
Response: { id: UUID, name: string, slug: string }

GET /api/v1/teams/{team_id}
Response: { id, name, members: [...], usage: {...} }

# Member Management
POST /api/v1/teams/{team_id}/invitations
Body: { email: string, role: "admin" | "member" }
Response: { invitation_id: UUID, token: string }

POST /api/v1/teams/invitations/{token}/accept
Response: { team_id: UUID, role: string }

DELETE /api/v1/teams/{team_id}/members/{user_id}
Response: { success: true }

# Admin Dashboard
GET /api/v1/teams/{team_id}/usage
Response: {
    total_interviews: 150,
    interviews_this_month: 45,
    active_members: 8,
    member_usage: [{ user_id, name, interviews: 12 }, ...]
}
```

### Implementation Plan

#### Phase 4.1: Data Models & Migration

| Task | Description | Agent/Skill | Est |
|------|-------------|-------------|-----|
| 4.1.1 | Create Team model in `models/team.py` | backend-engineer | 1h |
| 4.1.2 | Create TeamMembership model | backend-engineer | 30m |
| 4.1.3 | Create TeamInvitation model | backend-engineer | 30m |
| 4.1.4 | Update User model with team relationship | backend-engineer | 30m |
| 4.1.5 | Create Alembic migration | backend-engineer | 30m |
| 4.1.6 | Write model tests | qa-test-guardian | 1h |

**Checkpoint**: Team models created and migrated

---

#### Phase 4.2: Backend Team API

| Task | Description | Agent/Skill | Est |
|------|-------------|-------------|-----|
| 4.2.1 | Create `api/teams.py` router | backend-engineer | 2h |
| 4.2.2 | Implement team CRUD endpoints | backend-engineer | 2h |
| 4.2.3 | Implement invitation flow (create, accept, revoke) | backend-engineer | 3h |
| 4.2.4 | Implement member management (add, remove, role change) | backend-engineer | 2h |
| 4.2.5 | Add team permission decorators | backend-engineer | 1h |
| 4.2.6 | Write API tests | qa-test-guardian | 2h |

**Checkpoint**: Team API functional with tests

---

#### Phase 4.3: Team Subscription Integration

| Task | Description | Agent/Skill | Est |
|------|-------------|-------------|-----|
| 4.3.1 | Add team tier to Stripe products | - | 30m |
| 4.3.2 | Create team checkout endpoint | backend-engineer | 2h |
| 4.3.3 | Update webhook handler for team subscriptions | backend-engineer | 1.5h |
| 4.3.4 | Implement seat-based quota enforcement | backend-engineer | 1.5h |
| 4.3.5 | Write subscription tests | qa-test-guardian | 1h |

**Checkpoint**: Team subscriptions working with Stripe

---

#### Phase 4.4: Admin Dashboard API

| Task | Description | Agent/Skill | Est |
|------|-------------|-------------|-----|
| 4.4.1 | Create `api/teams.py` usage endpoint | backend-engineer | 1.5h |
| 4.4.2 | Implement team usage aggregation service | backend-engineer | 2h |
| 4.4.3 | Add member activity tracking | backend-engineer | 1h |
| 4.4.4 | Write usage API tests | qa-test-guardian | 1h |

**Checkpoint**: Admin usage API functional

---

#### Phase 4.5: Frontend Team Management

| Task | Description | Agent/Skill | Est |
|------|-------------|-------------|-----|
| 4.5.1 | Create TeamDashboardPage | frontend-builder | 3h |
| 4.5.2 | Create MemberList component | frontend-builder | 2h |
| 4.5.3 | Create InviteMemberModal | frontend-builder | 1.5h |
| 4.5.4 | Create TeamUsageChart component | frontend-builder | 2h |
| 4.5.5 | Add team routes and navigation | frontend-builder | 1h |
| 4.5.6 | Write component tests | qa-test-guardian | 1.5h |

**Checkpoint**: Team dashboard functional

---

#### Phase 4.6: Invitation Flow UI

| Task | Description | Agent/Skill | Est |
|------|-------------|-------------|-----|
| 4.6.1 | Create AcceptInvitationPage | frontend-builder | 2h |
| 4.6.2 | Add invitation email templates | backend-engineer | 1h |
| 4.6.3 | Integrate with email service (Resend) | backend-engineer | 1h |
| 4.6.4 | Write E2E tests for invitation flow | qa-test-guardian | 1.5h |

**Checkpoint**: Full invitation flow working

---

### Dependencies

**External:**
- Stripe Team product/price configuration
- Resend email templates for invitations

**Internal:**
- Existing auth system
- Existing subscription infrastructure
- Existing email service

### Testing Strategy

- **Unit Tests**: Team model validation, permission checks
- **Integration Tests**: Team creation → invite → accept → usage flow
- **E2E Tests**: Full team admin journey

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Complex permission model | High | Start simple (admin/member), expand later |
| Seat counting edge cases | Medium | Clear rules: pending invites don't count |
| SSO requirement for enterprise | Low | Defer SSO to later sprint |

---

## Sprint 10 Summary

### Total Estimated Effort

| Epic | Effort | Priority |
|------|--------|----------|
| Epic 1: Lint Cleanup | ~4 hours | P0 - Critical |
| Epic 2: Test Coverage | ~15 hours | P1 - High |
| Epic 3: Video Analysis | ~35 hours | P2 - Medium |
| Epic 4: B2B Features | ~45 hours | P2 - Medium |

**Recommended Sprint Scope:**
- Epic 1 + Epic 2 = ~19 hours (1 sprint)
- Epic 3 or Epic 4 = ~35-45 hours (separate sprint)

### Execution Order

1. **Week 1**: Epic 1 (Lint) + Epic 2 Phase 2.1 (API tests)
2. **Week 2**: Epic 2 Phase 2.2-2.3 (Service tests, verification)
3. **Week 3-4**: Epic 3 OR Epic 4 (choose based on business priority)

### Open Questions

- [ ] Video analysis: EmotiEffLib vs OpenCV + fer - which is more suitable?
- [ ] B2B: Should enterprise tier include SSO from day 1?
- [ ] B2B: Do we need team-specific question banks?

---

## Previous Sprint Reference

### Sprint 9: Conversational Voice Mentor ✅ COMPLETE (Dec 2025)

#### Epic 1: Voice Mentor TTS Integration ✅
- Phase 1.1: useSpeechSynthesis hook ✅
- Phase 1.2: TTS integrated into Detective Stage ✅
- Phase 1.3: VoiceSettingsPanel with voice selection ✅

#### Epic 2: Conversational Mode ✅
- Phase 2.1: useConversationMode state machine ✅
- Phase 2.2: ConversationIndicator UI component ✅
- Phase 2.3: Auto-listen mode after mentor speaks ✅
- Phase 2.4: Interrupt handling (stop TTS when user speaks) ✅

#### Epic 3: Premium Voice Quality ✅
- Phase 3.1: Voice quality assessment (premium badges) ✅
- voice-quality.ts with ranking utilities ✅
- VoiceSettingsPanel shows premium indicators ✅

#### Epic 4: Free Tier Prepare Access ✅
- Phase 4.1: Updated subscription gating ✅
- Phase 4.2: usePrepUsage hook (3/month limit, localStorage) ✅
- QuestionCard shows remaining preparations ✅

#### Post-Sprint Fixes:
- **Conversation Mode STT Conflict** (d5fc412): Fixed dual speech recognition issue
- **TTS Canceled Error** (37cfd24): Fixed error handling for intentional cancellation
- **Transcript Persistence** (37cfd24): Transcript now persists until answer submitted

---

## References

- [CODEBASE_AUDIT.md](./CODEBASE_AUDIT.md) - Current code quality metrics
- [project-brief.md](./project-brief.md) - Product vision and features
- [progress.md](./progress.md) - Sprint history and milestones
- [active-context.md](./active-context.md) - Current focus areas
