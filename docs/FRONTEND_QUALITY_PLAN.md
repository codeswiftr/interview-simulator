# Milestone: Frontend Quality & Polish Sprint

## Status: Ready
## Target: Sprint 11 (Dec 2025)

---

## Overview

This sprint addresses the findings from the comprehensive frontend audit. The Interview Simulator frontend is production-ready (~21,300 LOC, 44+ components) but has accumulated technical debt in accessibility, performance, and testing. This sprint focuses on:

1. **Epic 1**: Accessibility Compliance (P0 - legal/ethical requirement)
2. **Epic 2**: Request Caching & Performance (P1 - UX improvement)
3. **Epic 3**: Component Refactoring (P1 - maintainability)
4. **Epic 4**: Test Coverage Expansion (P2 - confidence)
5. **Epic 5**: UX Polish & Keyboard Support (P2 - power user experience)

**Why This Order?**
- Epic 1 addresses legal risk (WCAG compliance) and affects all users
- Epic 2 provides immediate UX improvement (faster loads, fewer API calls)
- Epic 3 reduces regression risk for future changes
- Epic 4/5 improve developer confidence and power user experience

---

## Success Criteria

- [ ] All modals have focus traps (WCAG 2.1 AA)
- [ ] ARIA live regions on async content (transcription, hints)
- [ ] Request deduplication reduces API calls by 30%+
- [ ] PreparationPage split into 3 stage components (<20KB each)
- [ ] Frontend test coverage reaches 50%+ (from ~35%)
- [ ] Keyboard shortcuts for interview flow (Space, Esc, arrows)

---

## Epic 1: Accessibility Compliance (P0)

**ICE Score**: 9.5/10 (Impact: 10, Confidence: 9, Ease: 9)
**Priority**: CRITICAL - WCAG 2.1 AA compliance required
**Rationale**: Screen reader users can't use async features, keyboard users trapped in modals

### Current State
- No ARIA live regions for transcription/hints
- No focus trap in modals (keyboard users tab out)
- No focus restoration on modal close
- Limited keyboard navigation in interview flow

### Target State
- `aria-live="polite"` on TranscriptionDisplay, CoachOverlay
- Focus trapped in all modals
- Focus restored to trigger element on close
- Keyboard shortcuts documented

### Implementation Plan

#### Phase 1.1: ARIA Live Regions

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 1.1.1 | Add `aria-live="polite"` to TranscriptionDisplay | - | 15m | Pending |
| 1.1.2 | Add `aria-live="polite"` to CoachOverlay hint section | - | 15m | Pending |
| 1.1.3 | Add `aria-live="assertive"` to error messages | - | 15m | Pending |
| 1.1.4 | Add `aria-busy` during loading states | - | 15m | Pending |
| 1.1.5 | Test with NVDA/VoiceOver screen readers | - | 30m | Pending |

**Checkpoint**: Screen readers announce transcription and hint updates

---

#### Phase 1.2: Modal Focus Management

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 1.2.1 | Install `focus-trap-react` library | - | 10m | Pending |
| 1.2.2 | Create `useFocusTrap` hook wrapper | frontend-builder | 30m | Pending |
| 1.2.3 | Add focus trap to NewInterviewModal | - | 20m | Pending |
| 1.2.4 | Add focus trap to UpgradeModal | - | 15m | Pending |
| 1.2.5 | Add focus trap to WelcomeModal | - | 15m | Pending |
| 1.2.6 | Add focus trap to SampleAnswerModal | - | 15m | Pending |
| 1.2.7 | Add focus trap to InterviewPage exit modal | - | 15m | Pending |
| 1.2.8 | Implement focus restoration to trigger element | frontend-builder | 30m | Pending |
| 1.2.9 | Test keyboard navigation in all modals | - | 30m | Pending |

**Checkpoint**: All modals trap focus and restore focus on close

---

#### Phase 1.3: Form Accessibility

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 1.3.1 | Audit form labels in LoginPage, RegisterPage | - | 20m | Pending |
| 1.3.2 | Add `aria-describedby` for error messages | - | 20m | Pending |
| 1.3.3 | Add `aria-invalid` to invalid form fields | - | 15m | Pending |
| 1.3.4 | Ensure select elements have proper labels | - | 15m | Pending |

**Checkpoint**: Forms are fully accessible with proper labels and error associations

---

### Testing Strategy
- Manual testing with VoiceOver (macOS) and NVDA (Windows)
- Keyboard-only navigation testing
- axe-core automated accessibility tests

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Focus trap breaks component behavior | Medium | Test each modal individually |
| Screen reader announcements too verbose | Low | Use `aria-live="polite"` not "assertive" |

---

## Epic 2: Request Caching & Performance (P1)

**ICE Score**: 8.0/10 (Impact: 9, Confidence: 8, Ease: 7)
**Priority**: HIGH - Reduces API calls, improves perceived performance
**Rationale**: Each component fetches independently; DashboardPage makes 5 parallel API calls

### Current State
- No request caching (each component calls API independently)
- No request deduplication (concurrent calls not merged)
- Manual loading/error state management
- DashboardPage: 5 parallel API calls on mount

### Target State
- React Query for data fetching
- 5-10 min stale time for user data
- Request deduplication automatic
- Loading/error states handled declaratively

### Technical Design

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    React Query Integration                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Component          useQuery Hook         API Client            │
│  ┌──────────┐      ┌──────────────┐      ┌──────────┐          │
│  │Dashboard │──────│ useUserStats │──────│ userAPI  │          │
│  │          │      │ staleTime:5m │      │.getStats │          │
│  └──────────┘      └──────────────┘      └──────────┘          │
│                                                                  │
│  Benefits:                                                       │
│  - Automatic caching + deduplication                            │
│  - Background refetching                                         │
│  - Loading/error states built-in                                │
│  - DevTools for debugging                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Plan

#### Phase 2.1: React Query Setup

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 2.1.1 | Install `@tanstack/react-query` | - | 5m | Pending |
| 2.1.2 | Create QueryClient with default config | frontend-builder | 30m | Pending |
| 2.1.3 | Wrap App with QueryClientProvider | - | 10m | Pending |
| 2.1.4 | Add React Query DevTools (dev only) | - | 10m | Pending |

**Checkpoint**: React Query initialized and working

---

#### Phase 2.2: Query Hooks - User Data

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 2.2.1 | Create `useUserStats` query hook | frontend-builder | 30m | Pending |
| 2.2.2 | Create `useUserProgress` query hook | frontend-builder | 30m | Pending |
| 2.2.3 | Create `useReadinessScore` query hook | frontend-builder | 20m | Pending |
| 2.2.4 | Migrate DashboardPage to use query hooks | frontend-builder | 1h | Pending |
| 2.2.5 | Test caching behavior (refresh, stale) | - | 30m | Pending |

**Checkpoint**: Dashboard uses cached user data

---

#### Phase 2.3: Query Hooks - Interviews & Questions

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 2.3.1 | Create `useInterviews` query hook | frontend-builder | 30m | Pending |
| 2.3.2 | Create `useQuestions` query hook with filters | frontend-builder | 45m | Pending |
| 2.3.3 | Migrate QuestionsPage to use query hook | frontend-builder | 45m | Pending |
| 2.3.4 | Add prefetching for common navigation paths | frontend-builder | 30m | Pending |

**Checkpoint**: Questions and interviews cached with filters

---

#### Phase 2.4: Mutation Hooks

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 2.4.1 | Create `useCreateInterview` mutation | frontend-builder | 30m | Pending |
| 2.4.2 | Create `useSubmitResponse` mutation with optimistic updates | frontend-builder | 45m | Pending |
| 2.4.3 | Invalidate caches on mutations | - | 20m | Pending |
| 2.4.4 | Test mutation + cache invalidation flow | - | 30m | Pending |

**Checkpoint**: Mutations invalidate relevant caches

---

#### Phase 2.5: Performance Optimizations

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 2.5.1 | Memoize InterviewCard with React.memo | - | 15m | Pending |
| 2.5.2 | Memoize ResponseReview with React.memo | - | 15m | Pending |
| 2.5.3 | Memoize QuestionCard with React.memo | - | 15m | Pending |
| 2.5.4 | Add useCallback to list item handlers | - | 30m | Pending |
| 2.5.5 | Profile with React DevTools, verify improvements | - | 30m | Pending |

**Checkpoint**: List rendering optimized, no unnecessary re-renders

---

### Dependencies
- `@tanstack/react-query` ^5.x

### Testing Strategy
- Verify request deduplication with Network tab
- Test stale-while-revalidate behavior
- Measure API call reduction (target: 30%+)

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Complex migration | Medium | Migrate one component at a time |
| Cache invalidation bugs | Medium | Clear invalidation rules per mutation |

---

## Epic 3: Component Refactoring (P1)

**ICE Score**: 7.5/10 (Impact: 8, Confidence: 8, Ease: 6)
**Priority**: HIGH - Reduces regression risk, improves maintainability
**Rationale**: PreparationPage (56KB), InterviewPage (26KB), DashboardPage (27KB) are too large

### Current State
- PreparationPage: 56KB, 15+ useState, 8+ useEffect - Very High complexity
- InterviewPage: 26KB, 10+ useState, 5+ useEffect - High complexity
- DashboardPage: 27KB, 4 modals, complex orchestration

### Target State
- PreparationPage split into: DetectiveStage, DraftStage, PracticeStage, ComparisonStage
- InterviewPage upload logic extracted to service
- DashboardPage modal state centralized

### Implementation Plan

#### Phase 3.1: PreparationPage Decomposition

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 3.1.1 | Extract DetectiveStage component (Q&A flow) | frontend-builder | 2h | Pending |
| 3.1.2 | Extract DraftStage component (draft review/edit) | frontend-builder | 1.5h | Pending |
| 3.1.3 | Extract PracticeStage component (recording) | frontend-builder | 2h | Pending |
| 3.1.4 | Extract ComparisonStage component (feedback) | frontend-builder | 1.5h | Pending |
| 3.1.5 | Create PreparationContext for shared state | frontend-builder | 1h | Pending |
| 3.1.6 | Refactor PreparationPage to orchestrate stages | frontend-builder | 1h | Pending |
| 3.1.7 | Write tests for each stage component | qa-test-guardian | 2h | Pending |

**Checkpoint**: PreparationPage <20KB, stages testable independently

---

#### Phase 3.2: InterviewPage Service Extraction

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 3.2.1 | Create `useInterviewSession` hook for session state | frontend-builder | 1.5h | Pending |
| 3.2.2 | Create `useResponseSubmission` hook for upload + retry | frontend-builder | 1.5h | Pending |
| 3.2.3 | Extract transcription polling to hook | frontend-builder | 1h | Pending |
| 3.2.4 | Simplify InterviewPage to use extracted hooks | frontend-builder | 1h | Pending |
| 3.2.5 | Write tests for extracted hooks | qa-test-guardian | 1.5h | Pending |

**Checkpoint**: InterviewPage <15KB, hooks testable

---

#### Phase 3.3: DashboardPage Modal Centralization

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 3.3.1 | Create `useDashboardModals` hook for modal state | frontend-builder | 45m | Pending |
| 3.3.2 | Migrate 4 modal states to hook | - | 30m | Pending |
| 3.3.3 | Add modal orchestration logic (prevent overlaps) | - | 30m | Pending |
| 3.3.4 | Test modal state transitions | - | 30m | Pending |

**Checkpoint**: Dashboard modal logic centralized and testable

---

### Testing Strategy
- Unit tests for extracted components/hooks
- Integration tests for full flows
- Verify no regressions in existing behavior

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Refactoring breaks existing flows | High | Comprehensive tests before refactoring |
| Prop drilling after extraction | Medium | Use context for deeply shared state |

---

## Epic 4: Test Coverage Expansion (P2)

**ICE Score**: 7.0/10 (Impact: 8, Confidence: 8, Ease: 6)
**Priority**: MEDIUM - Prevents regressions, enables confident changes
**Rationale**: ~35% coverage, critical paths undertested

### Current State
- 14 test files, ~35% coverage
- Well-tested: Audio recording hooks, RecordingDeck, CoachOverlay
- Undertested: API interceptors, page integration, error recovery

### Target State
- 50%+ overall coverage
- API interceptor tests
- Error recovery path tests
- Page integration tests for critical flows

### Implementation Plan

#### Phase 4.1: API Client Tests

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 4.1.1 | Create `api.test.ts` for interceptor tests | qa-test-guardian | 1.5h | Pending |
| 4.1.2 | Test token refresh flow (401 → refresh → retry) | qa-test-guardian | 1h | Pending |
| 4.1.3 | Test concurrent 401 handling (queue behavior) | qa-test-guardian | 45m | Pending |
| 4.1.4 | Test network error handling | qa-test-guardian | 30m | Pending |
| 4.1.5 | Test 402 quota exceeded handling | qa-test-guardian | 30m | Pending |

**Checkpoint**: API interceptors fully tested

---

#### Phase 4.2: Error Recovery Tests

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 4.2.1 | Test upload retry behavior (InterviewPage) | qa-test-guardian | 1h | Pending |
| 4.2.2 | Test failed transcription handling | qa-test-guardian | 45m | Pending |
| 4.2.3 | Test feedback generation failure | qa-test-guardian | 45m | Pending |
| 4.2.4 | Test ErrorBoundary error reporting | qa-test-guardian | 30m | Pending |

**Checkpoint**: Error paths have test coverage

---

#### Phase 4.3: Integration Tests

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 4.3.1 | Expand InterviewPage tests (full flow) | qa-test-guardian | 2h | Pending |
| 4.3.2 | Expand PreparationPage tests (stage transitions) | qa-test-guardian | 2h | Pending |
| 4.3.3 | Test DashboardPage modal interactions | qa-test-guardian | 1h | Pending |
| 4.3.4 | Test QuestionsPage filter + pagination | qa-test-guardian | 1h | Pending |

**Checkpoint**: Critical page flows have integration tests

---

### Testing Strategy
- Use MSW for API mocking
- Test error states, not just happy paths
- Aim for 50%+ coverage on critical modules

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tests take longer than estimated | Medium | Prioritize highest-impact paths |
| Mock complexity | Low | Reuse existing MSW handlers |

---

## Epic 5: UX Polish & Keyboard Support (P2)

**ICE Score**: 6.5/10 (Impact: 7, Confidence: 8, Ease: 7)
**Priority**: MEDIUM - Power user experience, professional polish
**Rationale**: No keyboard shortcuts, minor UX friction points

### Current State
- No keyboard shortcuts in interview flow
- No virtual scrolling (QuestionsPage may lag with 100+ items)
- No submission confirmation (accidental skips possible)

### Target State
- Space to start/stop recording
- Esc to exit interview (with confirmation)
- Arrow keys for question navigation
- Submission confirmation modal

### Implementation Plan

#### Phase 5.1: Keyboard Shortcuts

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 5.1.1 | Create `useKeyboardShortcuts` hook | frontend-builder | 1h | Pending |
| 5.1.2 | Add Space to start/stop recording | - | 30m | Pending |
| 5.1.3 | Add Esc to trigger exit confirmation | - | 20m | Pending |
| 5.1.4 | Add arrow keys for hint navigation | - | 30m | Pending |
| 5.1.5 | Show keyboard shortcut hints in UI | frontend-builder | 30m | Pending |
| 5.1.6 | Document shortcuts in help section | - | 20m | Pending |

**Checkpoint**: Interview controllable via keyboard

---

#### Phase 5.2: UX Improvements

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 5.2.1 | Add submission confirmation dialog | frontend-builder | 45m | Pending |
| 5.2.2 | Add loading skeleton for RecordingDeck | frontend-builder | 30m | Pending |
| 5.2.3 | Add hint relevance rating (thumbs up/down) | frontend-builder | 45m | Pending |
| 5.2.4 | Add question bookmarking feature | frontend-builder | 1.5h | Pending |
| 5.2.5 | Improve empty states with helpful CTAs | frontend-builder | 30m | Pending |

**Checkpoint**: UX polish items complete

---

#### Phase 5.3: Virtual Scrolling (Optional)

| Task | Description | Agent/Skill | Est | Status |
|------|-------------|-------------|-----|--------|
| 5.3.1 | Install `react-window` | - | 10m | Pending |
| 5.3.2 | Create VirtualizedQuestionList component | frontend-builder | 1.5h | Pending |
| 5.3.3 | Migrate QuestionsPage to virtualized list | frontend-builder | 1h | Pending |
| 5.3.4 | Test scroll performance with 200+ questions | - | 30m | Pending |

**Checkpoint**: QuestionsPage handles 200+ items smoothly

---

### Testing Strategy
- Manual testing of keyboard navigation
- Performance profiling for virtual scrolling
- User feedback on shortcut discoverability

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Shortcuts conflict with browser | Low | Use unassigned keys, test in multiple browsers |
| Virtual scroll breaks existing behavior | Medium | Thorough testing, keep non-virtualized fallback |

---

## Sprint Summary

### Total Estimated Effort

| Epic | Effort | Priority | Dependencies |
|------|--------|----------|--------------|
| Epic 1: Accessibility | ~6 hours | P0 - Critical | None |
| Epic 2: Request Caching | ~10 hours | P1 - High | None |
| Epic 3: Refactoring | ~18 hours | P1 - High | Epic 2 (React Query) |
| Epic 4: Test Coverage | ~12 hours | P2 - Medium | Epic 3 (testable components) |
| Epic 5: UX Polish | ~10 hours | P2 - Medium | None |

**Total**: ~56 hours (2 sprints)

### Recommended Execution Order

**Sprint 11A (Week 1-2):**
1. Epic 1: Accessibility (P0) - ~6h
2. Epic 2: Request Caching (P1) - ~10h

**Sprint 11B (Week 3-4):**
3. Epic 3: Refactoring (P1) - ~18h
4. Epic 4: Test Coverage (select phases) - ~8h

**Deferred to Sprint 12:**
5. Epic 5: UX Polish - ~10h
6. Epic 4: Remaining tests - ~4h

---

## Open Questions

- [ ] Should we use `react-aria` instead of `focus-trap-react` for more comprehensive accessibility?
- [ ] For virtual scrolling: `react-window` vs `react-virtualized` vs `@tanstack/react-virtual`?
- [ ] Should keyboard shortcuts be customizable (user preferences)?

---

## References

- [Frontend Audit Results](#) - Comprehensive codebase analysis
- [WCAG 2.1 AA Guidelines](https://www.w3.org/WAI/WCAG21/quickref/?currentsidebar=%23702) - Accessibility requirements
- [React Query Documentation](https://tanstack.com/query/latest) - Data fetching library
- [Testing Library Best Practices](https://testing-library.com/docs/react-testing-library/intro/) - Testing patterns
