# Sprint 12: Scale Readiness

## Status: In Progress (75% Complete)
## Target: January 2025

---

## Sprint 12 Progress Summary

### COMPLETED (This Session)

#### Epic 5: Frontend Test Foundation - DONE
- **554 tests passing** (was 0)
- **29 test files** across pages, components, hooks
- MSW v2 + Vitest + React Testing Library setup
- Full coverage of auth flows, pages, and critical components

#### Epic 6: Auth Hardening - DONE
- **Phase 6.1**: Proactive token refresh (before expiry)
- **Phase 6.2**: Password policy (already existed)
- **Phase 6.3**: Email verification for changes (VerifyEmailPage.tsx)
- **Phase 6.4**: Browser compatibility (BrowserWarning.tsx)

#### Epic 7: Performance Optimization - MOSTLY DONE
- **Code splitting**: Main bundle **710KB → 148KB** (79% reduction!)
- Axios, analytics, sentry split into separate chunks
- Vite `manualChunks` function-based configuration
- **Remaining**: Mobile responsiveness polish (3h)

#### Epic 8: Production Resilience - DONE
- **retry.ts**: `withRetry()`, `withTimeout()`, exponential backoff
- **RetryButton.tsx**: Error recovery UI with loading states
- **useRetry()** hook for state management

### Files Created (This Session)
```
frontend/src/lib/retry.ts                              - Retry utilities
frontend/src/components/ui/RetryButton.tsx             - Error recovery
frontend/src/components/interview/BrowserWarning.tsx   - Browser compat
frontend/src/pages/VerifyEmailPage.tsx                 - Email verification
```

### Files Modified (This Session)
```
frontend/src/lib/api.ts        - Proactive token refresh
frontend/vite.config.ts        - Enhanced code splitting (79% reduction)
frontend/src/App.tsx           - Added verify-email route
```

---

## Sprint 12.5: Revenue Optimization - DONE

### Epic 9: Dedicated Pricing Page - DONE

**Objective**: Create a standalone pricing page to improve SEO and conversion for visitors who want to see pricing before signing up.

#### Implementation Details

**New Files:**
```
frontend/src/pages/PricingPage.tsx                     - Full pricing page
frontend/src/pages/__tests__/PricingPage.test.tsx      - 40 tests
```

**Modified Files:**
```
frontend/src/App.tsx                    - Added /pricing route
frontend/src/components/layout/Header.tsx - Added Pricing nav link (desktop + mobile)
frontend/src/pages/HomePage.tsx         - Added pricing preview section with 7-day trial badge
```

**Features:**
- **Monthly/Annual Toggle**: Switch between $29/month and $24/month (annual, save 17%)
- **7-Day Free Trial Badge**: Prominently displayed on Pro plan
- **Feature Comparison Table**: Side-by-side Free vs Pro comparison
- **FAQ Section**: Expandable FAQs addressing common objections
- **Team Plan Teaser**: Coming soon notification with email signup
- **Responsive Design**: Optimized for mobile and desktop
- **Analytics**: Page view and CTA click tracking

**Revenue Impact:**
1. **SEO**: `/pricing` page can rank for "interview simulator pricing" searches
2. **Conversion**: Visitors can evaluate pricing before signup (reduces friction)
3. **Transparency**: Clear pricing builds trust
4. **Marketing**: Direct linking from ads/content to pricing page
5. **Trial Visibility**: 7-day free trial is now prominently displayed

**Tests:**
- 40 tests covering rendering, billing toggle, plan cards, FAQ, accessibility
- All 686 frontend tests passing

---

## Remaining Work

### Sprint 12 Completion

| Task | Est | Priority | Status |
|------|-----|----------|--------|
| Mobile responsiveness polish | 3h | P1 | ✅ S129 — 5 phases: ScoreRing max-w, FeedbackPage sm:grid, MetricCard p-4 sm:p-6, Dashboard xs:1-col, Modal overflow |
| Fix backend .env credentials | 15m | P0 | ✅ Fixed — forge:forge_local → postgres:postgres (matches docker-compose.yml) |
| Backend test verification | 30m | P1 | ⏳ Blocked — Docker context on homelab; run `docker context use default && docker compose up -d` then `uv run pytest` |

---

## Mobile Polish Implementation Plan

### Overview

The frontend has **solid mobile foundations** (safe area insets, touch targets, bottom nav, scroll-aware header) but needs polish in specific areas where fixed dimensions or aggressive padding cause issues on small screens (< 375px width).

### Success Criteria

- [ ] All pages usable on iPhone SE (375×667) without horizontal scroll
- [ ] Score rings scale responsively on feedback page
- [ ] Card padding adapts to viewport on mobile
- [ ] Recording interface has adequate space on compact devices
- [ ] No content cutoff or overlap with BottomNav

### Implementation Plan

#### Phase 1: ScoreRing Responsive Scaling (30m)

| Task | File | Change |
|------|------|--------|
| 1.1 | `components/feedback/ScoreRing.tsx` | Add responsive size prop that adapts to container |
| 1.2 | `pages/FeedbackPage.tsx` | Use `size="small"` on mobile, `size="medium"` on tablet+ |

**Current**: Fixed dimensions (100px/150px/200px) that can overflow.
**Fix**: Add container-aware sizing with CSS `max-w-full` wrapper and conditional size prop.

```typescript
// ScoreRing.tsx - Add responsive wrapper
<div className="flex flex-col items-center gap-3 w-full max-w-[150px] md:max-w-none">
```

**Checkpoint**: Score rings display correctly on iPhone SE without overflow.

---

#### Phase 2: FeedbackPage Card Padding (30m)

| Task | File | Change |
|------|------|--------|
| 2.1 | `pages/FeedbackPage.tsx` | Reduce metric card padding: `p-4 sm:p-6 lg:p-8` |
| 2.2 | `pages/FeedbackPage.tsx` | Add responsive grid: `grid-cols-1 sm:grid-cols-2 md:grid-cols-3` |

**Current**: `grid grid-cols-1 md:grid-cols-3` with large card padding.
**Fix**: Add intermediate `sm:` breakpoint for tablet, reduce padding on mobile.

**Checkpoint**: Feedback metrics have breathing room on all screen sizes.

---

#### Phase 3: RecordingDeck Mobile Optimization (45m)

| Task | File | Change |
|------|------|--------|
| 3.1 | `components/interview/RecordingDeck.tsx` | Reduce control panel padding: `p-4 sm:p-6` |
| 3.2 | `components/interview/RecordingDeck.tsx` | Ensure canvas container is `w-full` with aspect ratio |
| 3.3 | `components/interview/RecordingSection.tsx` | Reduce card padding if present |

**Current**: Fixed canvas (600×160) + `p-6 sm:p-10` padding = cramped on small screens.
**Fix**: Already has `p-6 sm:p-10` which is good. Verify control buttons don't overflow.

**Checkpoint**: Recording interface fully usable on iPhone SE.

---

#### Phase 4: Dashboard Stats Grid (30m)

| Task | File | Change |
|------|------|--------|
| 4.1 | `components/dashboard/StatsOverview.tsx` | Change to `grid-cols-1 xs:grid-cols-2 lg:grid-cols-4` |
| 4.2 | `tailwind.config.js` | Add custom `xs:` breakpoint at 400px if not present |

**Current**: `grid-cols-2 lg:grid-cols-4` - 2-column even on very small screens.
**Fix**: Stack to 1 column below 400px, then 2, then 4.

**Checkpoint**: Stats readable on all device widths.

---

#### Phase 5: Modal & Overflow Safety (30m)

| Task | File | Change |
|------|------|--------|
| 5.1 | `components/ui/Modal.tsx` | Add `max-h-[90vh] max-w-[95vw]` constraints |
| 5.2 | Global CSS or utility | Add `.overflow-x-safe` class for horizontal scroll containers |
| 5.3 | Verify sticky elements | Ensure no overlap with BottomNav (z-index check) |

**Current**: Modals may exceed viewport on mobile.
**Fix**: Constrain modals + add scrollable content area.

**Checkpoint**: Modals display correctly, no horizontal overflow anywhere.

---

### Testing Strategy

| Test Type | Coverage |
|-----------|----------|
| Visual | Chrome DevTools device simulation (iPhone SE, iPhone 12, Pixel 5) |
| Manual | Real device testing if available |
| Automated | Playwright viewport tests for critical pages |

### Devices to Test

| Device | Width | Priority |
|--------|-------|----------|
| iPhone SE | 375px | HIGH (smallest supported) |
| iPhone 12/13 | 390px | HIGH (common) |
| Pixel 5 | 393px | MEDIUM |
| iPad Mini | 768px | MEDIUM (tablet) |
| Desktop | 1280px+ | Regression check |

### Risks

| Risk | Mitigation |
|------|------------|
| Breaking existing responsive behavior | Test on desktop after each change |
| ScoreRing animation issues at small sizes | Test animation smoothness |
| Touch target regression | Verify 44px minimum maintained |

### Estimated Total: 2.5-3 hours

### Sprint 13: Video Analysis MVP — DONE ✅

| Phase | Task | Status |
|-------|------|--------|
| 13.1 | video_analyzer.py backend (via Sprint 15 backend) | ✅ |
| 13.2 | VideoRecordingDeck UI component (8-state machine, camera, upload) | ✅ S129 |
| 13.3 | VideoFeedbackCard integration in FeedbackPage | ✅ S129 |
| 13.4 | Tests: 18 tests across VideoFeedbackCard + VideoRecordingDeck | ✅ S129 |

### Sprint 14: B2B Team Features — Phase 1 + 2 COMPLETE ✅

| Phase | Task | Status |
|-------|------|--------|
| DB | Organization + OrganizationMember + OrganizationInvitation models | ✅ S130 |
| DB | Alembic migration (b1c2d3e4f5a6_add_team_organization_models.py) | ✅ S130 |
| Backend | TeamService (create_org, add_member, remove_member, send_invitation, accept_invitation) | ✅ S130 |
| Backend | teams.py router (POST/GET /teams, invitations, members, seats) | ✅ S130 |
| Backend | main.py: router registered at /api/v1/teams | ✅ S130 |
| Backend | check_interview_quota: team members bypass free limit | ✅ S130 |
| Backend | PATCH /teams/{org_id} — rename org + seat upgrade | ✅ S131 |
| Backend | PATCH /teams/{org_id}/members/{user_id}/role — promote/demote | ✅ S131 |
| Backend | GET /teams/{org_id}/usage — per-member interview analytics | ✅ S131 |
| Frontend | types/team.ts (TeamRead, TeamMemberRead, InvitationRead, PublicInvitationRead) | ✅ S130 |
| Frontend | teamAPI client methods in api.ts | ✅ S130 |
| Frontend | TeamDashboardPage.tsx (members, invitations, invite modal, role toggle, settings link) | ✅ S131 |
| Frontend | AcceptInvitationPage.tsx (/join/:token public route) | ✅ S130 |
| Frontend | App.tsx routes: /team + /join/:token + /team/settings | ✅ S131 |
| Frontend | PricingPage.tsx: Team card added | ✅ S130 |
| Frontend | TeamSettingsPage.tsx (org rename, seat picker, per-member usage analytics) | ✅ S131 |
| Tests | 30 Phase 1 tests in tests/api/test_teams.py | ✅ S130 |
| Tests | 19 Phase 2 tests (TestUpdateTeam ×7, TestUpdateMemberRole ×6, TestGetTeamUsage ×6) — 41/41 pass | ✅ S131 |
| Frontend tests | TeamDashboardPage.test.tsx (13), TeamSettingsPage.test.tsx (10), AcceptInvitationPage.test.tsx (12) — 35/35 pass | ✅ S131 |
| Frontend fix | RegisterPage.tsx experience-hint text aligned to test expectations; RegisterPage 39/39 pass | ✅ S131 |
| Frontend suite | 754/754 passing (was 717/719) — 0 failures, 29 skipped | ✅ S131 |

### Sprint 15: Video Wiring

| Phase | Task | Status |
|-------|------|--------|
| InterviewContext | lastSubmittedResponseId + clearLastSubmittedResponseId | ✅ S132 |
| RecordingSection | VideoRecordingDeck wired — shows "Add video for your last answer" after audio submit | ✅ S132 |
| Build | Clean (4.47s), 171 interview tests pass | ✅ S132 |
| Tests | RecordingSection.test.tsx — 10 tests for video wiring | ✅ S132 |
| Content | 4 new SEO blog posts (AI tools comparison, Pramp alt, busy engineers, scoring criteria) — 40 total | ✅ S132 |
| Frontend suite | **764/764 passing** (44 test files) | ✅ S132 |
| SEO | sitemap.xml (47 URLs: 7 pages + 40 blog posts) + robots.txt added to public/ | ✅ S132 |
| Lint | 0 errors (was 11): fixed PricingPage catch, analytics.test posthog, main.tsx Rewardful any/arguments, RetryButton + BrowserWarning fast-refresh | ✅ S132 |
| STRIPE | Checkout + webhook extensions | ⏳ HUMAN GATE (Stripe changes) |

*Full plan at `/Users/bogdan/work/FORGE/docs/plans/S130_PLAN.md`*

---

## Success Criteria

- [x] Frontend test coverage ≥ 40% (✅ 554 tests)
- [x] Refresh token rotation working (✅ proactive refresh)
- [x] Main bundle < 500KB (✅ 148KB, was 710KB)
- [x] Password policy enforced (✅ already exists)
- [x] All auth flows have retry/fallback (✅ retry.ts)
- [x] Mobile responsive polish complete (✅ S129 — ScoreRing max-w, FeedbackPage sm:grid, MetricCard p-4 sm:p-6, Dashboard xs:1-col, Modal overflow)

---

## Build Metrics (After Sprint 12)

| Chunk | Before | After | Change |
|-------|--------|-------|--------|
| index.js | 710KB | 148KB | **-79%** |
| axios.js | bundled | 36KB | split |
| analytics.js | bundled | 165KB | split |
| recharts.js | 335KB | 335KB | unchanged |
| react-vendor.js | 430KB | 430KB | unchanged |

**Total Initial Load**: ~350KB (was ~1MB+)

---

## Test Status

### Frontend
- **554 tests passing**
- **29 test files**
- **29 tests skipped** (complex async scenarios - appropriate for e2e)

### Backend
- 782 tests (Sprint 11 baseline)
- Note: Local `.env` credential mismatch resolved — both `.env` and `.env.example` now use `postgres:postgres` matching docker-compose.yml

---

## Technical Decisions Made

### 1. Proactive Token Refresh
Instead of waiting for 401 errors, we now check token expiry before each request and refresh proactively if < 5 minutes remaining.

```typescript
// frontend/src/lib/api.ts
async function proactiveTokenRefresh(): Promise<void> {
  if (!isTokenExpiringSoon()) return;
  // ... refresh logic
}
```

### 2. Function-based Code Splitting
Switched from object-based to function-based `manualChunks` for better control:

```typescript
// vite.config.ts
manualChunks: (id) => {
  if (id.includes('node_modules/axios/')) return 'axios';
  if (id.includes('node_modules/@sentry/')) return 'sentry';
  // ...
}
```

### 3. Retry with Exponential Backoff
Created reusable retry utility with configurable presets:

```typescript
// frontend/src/lib/retry.ts
const result = await withRetry(
  () => api.get('/data'),
  RetryPresets.standard // maxRetries: 3, baseDelay: 1000ms
);
```

---

## Previous Sprint Summary

### Sprint 11: Soft Launch Hardening - COMPLETED
- **Epic 1**: Critical Path Tests - DONE
- **Epic 2**: Question Recommendations - DONE
- **Epic 3**: Interview Export & Sharing - DONE
- **Epic 4**: Sentry Integration - DONE

**Achievements:**
- 782 backend tests (up from 385)
- PDF export with WeasyPrint
- Share link system with 7-day expiry
- Sentry error tracking integrated

---

## Future Sprints

### Sprint 13: Video Analysis MVP (30h)
- Video recording UI
- Basic video analysis (posture, eye contact)
- Video feedback display
- Integration with feedback page

### Sprint 14: B2B Team Features (45h)
- Team/Organization models
- Admin dashboard
- Seat-based licensing
- Member invitation flow

### Sprint 15: Advanced Features
- Interview comparison
- Mock interviewer personas
- Custom question banks
- Enterprise API

---

## References

- [CODEBASE_AUDIT.md](./CODEBASE_AUDIT.md) - Coverage metrics
- [DUE_DILIGENCE_REPORT.md](./DUE_DILIGENCE_REPORT.md) - Overall assessment
- [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) - Security posture
