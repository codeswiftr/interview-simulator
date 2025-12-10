# Milestone: Onboarding & Prepare/Mentor Mode Enhancement

## Status: In Progress
## Target: Sprint 8 (Post-Sprint 7)

---

## Overview

This milestone focuses on two key areas:
1. **Onboarding Journey Enhancement** - Transform minimal welcome modal into comprehensive guided onboarding
2. **Preparation/Mentor Mode Polish** - Complete Sprint 7 voice features, fix CoachOverlay props mismatch, and add mentor enhancements

**Current State**:
- Onboarding: Basic WelcomeModal only (4-step tour for new users)
- Preparation Mode: Comprehensive 4-stage flow, voice features 80% complete
- ✅ CoachOverlay props mismatch FIXED (was critical bug)

---

## Success Criteria

- [x] CoachOverlay props mismatch fixed (critical bug) ✅ COMPLETE
- [ ] Sprint 7 Phase 5-6 completed (Draft Voice Dictation + Polish)
- [ ] Enhanced onboarding with guided first-session flow
- [ ] Contextual tooltips for key features
- [ ] Mentor hint history panel
- [ ] All tests passing, no TypeScript errors

---

## Technical Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           User Journey                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Registration → WelcomeModal → FirstSessionPrompt → PreparationPage         │
│       │              │                │                    │                 │
│       v              v                v                    v                 │
│  ┌─────────┐   ┌──────────┐    ┌───────────┐      ┌──────────────┐          │
│  │ Auth    │   │ Tour     │    │ Create    │      │ 4-Stage Flow │          │
│  │ Flow    │   │ Carousel │    │ Session   │      │              │          │
│  └─────────┘   └──────────┘    │ Prompt    │      │ Detective    │          │
│                                 └───────────┘      │ Draft        │          │
│                                                    │ Practice     │          │
│                                                    │ Complete     │          │
│                                                    └──────────────┘          │
│                                                           │                  │
│                                                           v                  │
│                                                    ┌──────────────┐          │
│                                                    │ CoachOverlay │          │
│                                                    │ (AI Coaching)│          │
│                                                    └──────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Models

**OnboardingState** (localStorage):
```typescript
interface OnboardingState {
  hasSeenWelcome: boolean;
  completedSteps: string[];         // Track completed onboarding steps
  dismissedAt?: string;             // When user dismissed onboarding
  firstSessionCreated?: boolean;    // NEW: Track first session milestone
  preparationTourCompleted?: boolean; // NEW: Track preparation tour
}
```

### API Contracts

No new backend endpoints required. All enhancements are frontend-only.

### Dependencies

**Existing Components to Modify**:
| Component | Location | Changes |
|-----------|----------|---------|
| `CoachOverlay` | `components/interview/CoachOverlay.tsx` | Fix interface, add new props |
| `PreparationPage` | `pages/PreparationPage.tsx` | Fix CoachOverlay usage, add voice dictation |
| `WelcomeModal` | `components/onboarding/WelcomeModal.tsx` | Add first-session prompt |
| `useOnboarding` | `hooks/useOnboarding.ts` | Add new tracking methods |

**New Components to Create**:
| Component | Purpose |
|-----------|---------|
| `FirstSessionPrompt` | Modal prompting user to create first interview session |
| `ContextualTooltip` | Reusable tooltip component for feature hints |
| `HintHistoryPanel` | Collapsible panel showing coaching hint history |

---

## Implementation Plan

### Phase 1: Critical Bug Fix - CoachOverlay Props (2h)

**Priority: CRITICAL** - Blocking practice coaching feature

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 1.1 | Audit CoachOverlay interface vs all usages | frontend-builder | 0.5h |
| 1.2 | Update CoachOverlay interface to support both use cases | frontend-builder | 0.5h |
| 1.3 | Fix PreparationPage CoachOverlay props | frontend-builder | 0.5h |
| 1.4 | Add missing tests for CoachOverlay | qa-test-guardian | 0.5h |

**Current Interface (CoachOverlay.tsx:4-14)**:
```typescript
interface CoachOverlayProps {
  isVisible: boolean;          // Required - NOT passed in PreparationPage
  onClose: () => void;         // Required - Passed ✅
  questionType: string;        // Required - NOT passed in PreparationPage
  elapsedTime: number;         // Required - NOT passed in PreparationPage
  expectedDuration: number;    // Required - NOT passed in PreparationPage
  dynamicHint?: string | null; // Optional - Passed as "hint"
  isHintLoading?: boolean;     // Optional - Passed as "isLoading"
  isHintStreaming?: boolean;   // Optional - Passed as "isStreaming"
  hintError?: string | null;   // Optional - Passed as "error"
}
```

**PreparationPage Usage (lines 823-831)**:
```typescript
<CoachOverlay
  hint={coachingHint}            // ❌ Wrong prop name
  isLoading={isHintLoading}      // ❌ Wrong prop name
  isStreaming={isHintStreaming}  // ❌ Wrong prop name
  error={hintError}              // ❌ Wrong prop name
  onClose={() => setShowCoach(false)}  // ✅ Correct
  onToggle={() => setShowCoach(!showCoach)}  // ❌ Not in interface
  isCollapsed={!showCoach}       // ❌ Not in interface
/>
```

**Solution**: Update CoachOverlay to accept alias props for backward compatibility:
```typescript
interface CoachOverlayProps {
  // For InterviewPage usage (existing)
  isVisible?: boolean;
  questionType?: string;
  elapsedTime?: number;
  expectedDuration?: number;

  // For PreparationPage usage (simplified)
  hint?: string | null;          // Alias for dynamicHint
  isLoading?: boolean;           // Alias for isHintLoading
  isStreaming?: boolean;         // Alias for isHintStreaming
  error?: string | null;         // Alias for hintError
  onToggle?: () => void;         // NEW: Toggle expanded/collapsed
  isCollapsed?: boolean;         // NEW: Controlled collapse state

  // Common
  onClose: () => void;
  dynamicHint?: string | null;
  isHintLoading?: boolean;
  isHintStreaming?: boolean;
  hintError?: string | null;
}
```

**Checkpoint**: Practice coaching displays correctly in PreparationPage

---

### Phase 2: Sprint 7 Completion - Draft Voice Dictation (2.5h)

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 2.1 | Add VoiceInputButton to draft editing textarea | frontend-builder | 0.5h |
| 2.2 | Implement append mode (add to end of draft) | frontend-builder | 0.5h |
| 2.3 | Add "replace selection" mode for editing | frontend-builder | 1h |
| 2.4 | Test draft dictation flow | qa-test-guardian | 0.5h |

**Files Modified**:
- `frontend/src/pages/PreparationPage.tsx` (draft stage section)

**Checkpoint**: Users can dictate draft edits by voice

---

### Phase 3: Sprint 7 Completion - Polish & Testing (2h)

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 3.1 | Test on Chrome, Firefox, Safari, Edge | qa-test-guardian | 1h |
| 3.2 | Add graceful degradation for unsupported browsers | frontend-builder | 0.5h |
| 3.3 | Update PreparationPage tests with voice integration | qa-test-guardian | 0.5h |

**Checkpoint**: Voice features work across all major browsers

---

### Phase 4: Enhanced Onboarding - First Session Flow (4h)

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 4.1 | Create FirstSessionPrompt modal component | frontend-builder | 1h |
| 4.2 | Update useOnboarding hook with new tracking | frontend-builder | 0.5h |
| 4.3 | Add first-session prompt after WelcomeModal | frontend-builder | 0.5h |
| 4.4 | Add "create session" shortcut in DashboardPage | frontend-builder | 1h |
| 4.5 | Test new onboarding flow | qa-test-guardian | 1h |

**New Component: FirstSessionPrompt**
```typescript
interface FirstSessionPromptProps {
  isOpen: boolean;
  onCreateSession: () => void;
  onSkip: () => void;
}
```

**Flow**:
```
New User → WelcomeModal → "Start Practicing" → FirstSessionPrompt
                                                      │
                              ┌───────────────────────┴────────────────────────┐
                              │                                                │
                              v                                                v
                       [Create Session]                                  [Maybe Later]
                              │                                                │
                              v                                                v
                    CreateSessionPage                                    DashboardPage
                                                                    (with "Getting Started" card)
```

**Checkpoint**: New users guided to create first session

---

### Phase 5: Contextual Tooltips (3h)

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 5.1 | Create ContextualTooltip component | frontend-builder | 1h |
| 5.2 | Add tooltips to PreparationPage stages | frontend-builder | 1h |
| 5.3 | Add tooltips to Dashboard key features | frontend-builder | 0.5h |
| 5.4 | Test tooltip accessibility and mobile behavior | qa-test-guardian | 0.5h |

**Tooltip Locations**:
- Dashboard: Interview sessions list, preparation mode entry
- PreparationPage: Detective stage (how Q&A works), Draft stage (AI generation), Practice stage (recording tips)

**Checkpoint**: Users have in-context help throughout app

---

### Phase 6: Mentor Enhancements (4h)

| Task | Description | Agent | Est |
|------|-------------|-------|-----|
| 6.1 | Create HintHistoryPanel component | frontend-builder | 1.5h |
| 6.2 | Add hint tracking state to PreparationPage | frontend-builder | 0.5h |
| 6.3 | Integrate history panel with CoachOverlay | frontend-builder | 1h |
| 6.4 | Add hint pagination/scrolling for long sessions | frontend-builder | 0.5h |
| 6.5 | Test mentor history functionality | qa-test-guardian | 0.5h |

**HintHistoryPanel Component**:
```typescript
interface HintHistoryPanelProps {
  hints: Array<{
    timestamp: Date;
    hint: string;
    stage: 'detective' | 'practice';
  }>;
  isExpanded: boolean;
  onToggle: () => void;
}
```

**Checkpoint**: Users can review all coaching hints received during session

---

## Testing Strategy

### Unit Tests
- **CoachOverlay**: Props validation, both usage patterns
- **FirstSessionPrompt**: Render, actions, state management
- **ContextualTooltip**: Visibility, positioning, accessibility
- **HintHistoryPanel**: Hint list rendering, expansion toggle

### Integration Tests
- Onboarding flow: Register → Welcome → First Session
- Preparation flow with voice: Detective → Draft (dictation) → Practice (coaching)
- Mentor hints accumulation and history display

### E2E Tests (Optional)
- Full new user onboarding journey
- Complete preparation session with voice input

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| CoachOverlay fix breaks InterviewPage | High | Test both usages before/after |
| Voice dictation cursor placement issues | Medium | Start with append-only mode |
| Tooltip positioning on mobile | Low | Use responsive positioning library |
| Hint history memory usage | Low | Limit to last 20 hints per session |

---

## Open Questions

- [ ] Should hint history persist across sessions? (localStorage)
- [ ] Tooltip dismiss behavior: click-outside vs explicit close?
- [ ] Voice dictation: Show waveform visualization?

---

## Files Summary

### New Files (4)
1. `frontend/src/components/onboarding/FirstSessionPrompt.tsx`
2. `frontend/src/components/common/ContextualTooltip.tsx`
3. `frontend/src/components/interview/HintHistoryPanel.tsx`
4. `frontend/src/components/common/__tests__/ContextualTooltip.test.tsx`

### Modified Files (5)
1. `frontend/src/components/interview/CoachOverlay.tsx` - Fix interface
2. `frontend/src/pages/PreparationPage.tsx` - Fix props, add voice dictation
3. `frontend/src/hooks/useOnboarding.ts` - Add new tracking
4. `frontend/src/pages/DashboardPage.tsx` - Add first-session prompt
5. `frontend/src/components/onboarding/WelcomeModal.tsx` - Chain to first-session

---

## Estimated Timeline

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 1: CoachOverlay Fix | 2h | None (CRITICAL) |
| Phase 2: Draft Voice Dictation | 2.5h | Phase 1 |
| Phase 3: Polish & Testing | 2h | Phase 2 |
| Phase 4: First Session Flow | 4h | None |
| Phase 5: Contextual Tooltips | 3h | Phase 4 |
| Phase 6: Mentor Enhancements | 4h | Phase 1 |

**Total Estimated Effort**: 17.5 hours

**Parallel Execution**:
- Phase 1 is critical and must be done first
- Phase 4-5 (Onboarding) can run in parallel with Phase 6 (Mentor)
- Phase 2-3 (Sprint 7 completion) depends on Phase 1

---

## Previous Sprints Reference

### Sprint 7: Voice-Enabled Practice Mode (80% Complete)
- Phase 1-4: ✅ Complete (Speech hook, VoiceInput, Detective integration, Practice coaching)
- Phase 5: ⏳ Draft Voice Dictation (this milestone)
- Phase 6: ⏳ Polish & Cross-Browser Testing (this milestone)

### Sprint 6: Production Readiness ✅ COMPLETE
- Epic 1: Test Coverage ✅
- Epic 2: Frontend Component Testing ✅
- Epic 3: Production Security & Observability ✅
- Epic 4: Performance & Polish ✅

---

## Appendix: ICE-Scored Epic Priorities

| Epic | Impact | Confidence | Ease | ICE Score |
|------|--------|------------|------|-----------|
| CoachOverlay Fix | 10 | 10 | 9 | **900** |
| Sprint 7 Phase 5-6 | 8 | 9 | 7 | **504** |
| First Session Flow | 8 | 8 | 7 | **448** |
| Contextual Tooltips | 7 | 8 | 7 | **392** |
| Mentor History Panel | 7 | 7 | 6 | **294** |
