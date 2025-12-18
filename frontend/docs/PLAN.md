# Milestone: Frontend Design System Unification

## Status: Ready
## Target: Sprint 7 (Dec 18 - Jan 3)

---

## Execution Strategy

### Agent & Skill Usage
| Tool | Purpose |
|------|---------|
| **frontend-design** skill | UI/UX decisions, component styling, responsive patterns |
| **frontend-builder** agent | Component implementation, React code |
| **qa-test-guardian** agent | Test creation and coverage |
| **Explore** agent | Codebase research for complex tasks |

### Subagent Strategy
- Launch **parallel subagents** for independent tasks within each phase
- Use **sequential execution** for dependent tasks (e.g., Card component before Card usage)
- Each phase should complete with a **conventional commit**

### Commit Checkpoints
```
feat(frontend): add mobile bottom navigation (Epic 6)
feat(frontend): migrate to HSL design tokens (Epic 5)
refactor(frontend): adopt Shadcn-style Card API (Epic 7)
style(frontend): simplify dashboard visual design (Epic 8)
feat(frontend): complete settings page polish (Epic 9)
```

---

## Overview

The Interview Simulator has two parallel frontend implementations that need to be unified. The legacy frontend (`/frontend/`) has rich functionality (charts, heatmaps, onboarding) but uses older design patterns. The v2 UI (`/src/`) has a cleaner, Linear-inspired aesthetic with mobile-first bottom navigation but is missing many features.

**Strategy**: Evolve the legacy frontend by incrementally adopting v2 patterns (BottomNav, simplified cards, HSL color system) while preserving all existing functionality. This approach minimizes risk while achieving design consistency.

## Success Criteria
- [ ] Mobile users see bottom navigation bar on all authenticated pages
- [ ] `/progress` route exists with API-integrated data display
- [ ] Design tokens unified to HSL format across all components
- [ ] Card components use consistent Shadcn-style API
- [ ] Dashboard visual complexity reduced (no floating gradients)
- [ ] All 255 existing tests continue to pass
- [ ] Lighthouse accessibility score remains >90

## Technical Design

### Architecture
```
/frontend/src/
├── components/
│   ├── layout/
│   │   ├── Header.tsx          # Desktop navigation (unchanged)
│   │   ├── BottomNav.tsx       # NEW: Mobile navigation
│   │   └── ProtectedRoute.tsx  # Auth wrapper (unchanged)
│   └── ui/
│       ├── Card.tsx            # UPDATED: Shadcn-style API
│       ├── Button.tsx          # UPDATED: CVA variants
│       └── ...
├── pages/
│   ├── ProgressPage.tsx        # NEW: Dedicated progress view
│   └── ...
├── styles/
│   └── globals.css             # UPDATED: HSL variables
└── App.tsx                     # UPDATED: New routes + layout
```

### Design Token Migration
```css
/* FROM (HEX) */
--color-electric-blue: #38BDF8;

/* TO (HSL) */
--electric-blue: 197 91% 60%;
--primary: var(--electric-blue);
```

### Component API Changes
```tsx
/* FROM */
<div className="card-glass p-6">
  <h3 className="heading-card">Title</h3>
  <p>Content</p>
</div>

/* TO */
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
</Card>
```

### Dependencies
- **Internal**: ThemeContext, useAuth, API client (unchanged)
- **New packages**: None required (use existing Tailwind + React)
- **Optional future**: `class-variance-authority` for component variants

---

## Implementation Plan

### Phase 1: Navigation Modernization (Epic 6)
**Goal**: Add mobile-first bottom navigation and /progress route

| Task | Description | Agent/Skill | Est | Parallel |
|------|-------------|-------------|-----|----------|
| 6.1 | Create BottomNav component in `/frontend/src/components/layout/` | frontend-builder | 2h | A |
| 6.2 | Add responsive logic to show BottomNav on mobile only (< md breakpoint) | frontend-builder | 1h | A (after 6.1) |
| 6.3 | Update Header to hide mobile menu when BottomNav is visible | frontend-builder | 1h | A (after 6.1) |
| 6.4 | Create ProgressPage with stats cards and session history | frontend-builder | 3h | B |
| 6.5 | Add `/progress` and `/practice` routes to App.tsx | - | 30m | B (after 6.4) |
| 6.6 | Wire ProgressPage to userAPI.getProgress() and userAPI.getStats() | frontend-builder | 1h | B (after 6.4) |
| 6.7 | Add tests for BottomNav active states and navigation | qa-test-guardian | 1h | C (after A) |
| 6.8 | Test keyboard navigation and screen reader accessibility | - | 1h | C (after A,B) |

**Parallel Groups**: A (BottomNav), B (ProgressPage), C (Testing) - A and B can run simultaneously

**Checkpoint**: Mobile users can navigate via bottom bar; /progress shows real data

**Commit**: `feat(frontend): add mobile bottom navigation and progress page`

---

### Phase 2: Design Token Unification (Epic 5)
**Goal**: Migrate to HSL color system for consistent theming

| Task | Description | Agent/Skill | Est | Parallel |
|------|-------------|-------------|-----|----------|
| 5.1 | Create `design-tokens.css` with HSL variables from v2 styles.css | frontend-design skill | 1h | A |
| 5.2 | Update globals.css to import and use HSL tokens | frontend-builder | 2h | A (after 5.1) |
| 5.3 | Update button classes (.btn-primary, etc) to use HSL | frontend-builder | 1h | B |
| 5.4 | Update card classes (.card, .card-glass) to use HSL | frontend-builder | 1h | B |
| 5.5 | Update input/form classes to use HSL | frontend-builder | 1h | B |
| 5.6 | Run visual regression check on all pages | - | 1h | C (after A,B) |
| 5.7 | Update Tailwind theme config if needed | - | 30m | C |

**Parallel Groups**: A (Token setup), B (Class updates - can run in parallel), C (Validation)

**Checkpoint**: All colors render correctly; dark mode works; no visual regressions

**Commit**: `feat(frontend): migrate to HSL design tokens`

---

### Phase 3: Component API Migration (Epic 7)
**Goal**: Adopt Shadcn-style Card component API

| Task | Description | Agent/Skill | Est | Parallel |
|------|-------------|-------------|-----|----------|
| 7.1 | Create Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter components | frontend-design skill + frontend-builder | 2h | A |
| 7.2 | Update StatsOverview to use new Card components | frontend-builder | 1h | B |
| 7.3 | Update StatsCard in dashboard to use new Card components | frontend-builder | 1h | B |
| 7.4 | Update InterviewCard to use new Card components | frontend-builder | 1h | B |
| 7.5 | Update QuestionCard to use new Card components | frontend-builder | 1h | C |
| 7.6 | Update MetricCard in feedback to use new Card components | frontend-builder | 1h | C |
| 7.7 | Update all remaining card usages (grep for "card-glass", "card-interactive") | frontend-builder | 2h | D (after B,C) |
| 7.8 | Remove deprecated card CSS classes from globals.css | - | 30m | D |
| 7.9 | Add tests for Card component variants | qa-test-guardian | 1h | E (after A) |

**Parallel Groups**: A (Foundation), B (Dashboard cards), C (Other cards), D (Cleanup), E (Tests)
- B and C can run in parallel after A completes
- Launch 2-3 frontend-builder subagents for B and C tasks

**Checkpoint**: All cards use consistent API; old card classes removed

**Commit**: `refactor(frontend): adopt Shadcn-style Card API`

---

### Phase 4: Dashboard Simplification (Epic 8)
**Goal**: Reduce visual complexity while preserving functionality

| Task | Description | Agent/Skill | Est | Parallel |
|------|-------------|-------------|-----|----------|
| 8.1 | Remove floating gradient background decorations from DashboardPage | frontend-builder | 30m | A |
| 8.2 | Replace card-glass with simpler card styling on dashboard | frontend-builder | 1h | A |
| 8.3 | Reduce animation delays and remove float animation | frontend-builder | 30m | A |
| 8.4 | Make ActivityHeatmap more compact (reduce cell size) | frontend-builder | 1h | B |
| 8.5 | Simplify SkillsRadar chart styling | frontend-builder | 1h | B |
| 8.6 | Improve empty state designs (new user, no sessions) | frontend-design skill | 1h | C |
| 8.7 | Test dashboard on mobile viewport sizes | - | 30m | D (after all) |

**Parallel Groups**: A (Page cleanup), B (Chart adjustments), C (Empty states), D (Testing)
- All of A, B, C can run in parallel

**Checkpoint**: Dashboard is visually cleaner; all features still work

**Commit**: `style(frontend): simplify dashboard visual design`

---

### Phase 5: Settings & Polish (Epic 9)
**Goal**: Complete settings page and final polish

| Task | Description | Agent/Skill | Est | Parallel |
|------|-------------|-------------|-----|----------|
| 9.1 | Ensure SettingsPage uses new Card components | frontend-builder | 1h | A |
| 9.2 | Verify VoiceSettingsPanel works with new design tokens | frontend-builder | 30m | A |
| 9.3 | Verify SubscriptionCard and UpgradeModal use new styles | frontend-builder | 1h | A |
| 9.4 | Add account management section (name, email display) | frontend-design skill + frontend-builder | 1h | B |
| 9.5 | Final visual QA pass on all pages | - | 2h | C (after all) |
| 9.6 | Fix any accessibility issues found during testing | frontend-builder | 1h | C |
| 9.7 | Update component README documentation | - | 1h | D |

**Parallel Groups**: A (Settings updates), B (New features), C (QA), D (Docs)

**Checkpoint**: Settings fully styled; all pages pass visual QA

**Commit**: `feat(frontend): complete settings page and final polish`

---

## Testing Strategy

### Unit Tests
- **BottomNav**: Active state detection, route matching
- **Card components**: Render variants, slot composition
- **ProgressPage**: Data display, loading states, error states
- **Coverage target**: Maintain 60%+ frontend coverage

### Integration Tests
- Navigation flow: Login -> Dashboard -> Practice -> Progress -> Settings
- Theme persistence across routes
- API error handling in ProgressPage

### E2E Tests (Existing)
- Verify existing Playwright tests pass
- Add E2E for bottom navigation flow on mobile viewport

### Visual Regression
- Screenshot comparison before/after design token migration
- Mobile viewport checks for bottom nav

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing styles during HSL migration | High | Migrate incrementally; visual regression checks |
| Card API migration breaks layouts | Medium | Update one component at a time; test each |
| Bottom nav overlaps content on short pages | Low | Add `pb-16` padding to main content area |
| Dark mode inconsistencies | Medium | Test both themes after each phase |
| Performance regression from new components | Low | Bundle size check; no new heavy dependencies |

---

## Open Questions
- [x] Which strategy to use? **Answered: Option A - Evolve Legacy**
- [ ] Should we add React Query to legacy frontend now or defer? **Recommend: Defer**
- [ ] Keep /questions route as alias for /practice? **Recommend: Yes, for backwards compat**

---

## Task Summary by Epic

| Epic | Tasks | Total Est | Priority | Subagents |
|------|-------|-----------|----------|-----------|
| Epic 6: Navigation | 8 tasks | 10.5h | HIGH | 2 parallel (A+B) |
| Epic 5: Design Tokens | 7 tasks | 7.5h | HIGH | 2 parallel (A+B) |
| Epic 7: Component API | 9 tasks | 10.5h | MEDIUM | 3 parallel (B+C+E) |
| Epic 8: Dashboard | 7 tasks | 5.5h | MEDIUM | 3 parallel (A+B+C) |
| Epic 9: Settings | 7 tasks | 7.5h | LOW | 2 parallel (A+B) |
| **TOTAL** | **38 tasks** | **41.5h** | - | - |

**Estimated Duration**: 5-6 working days (with parallel subagent execution)

---

## Context Management Strategy

### Avoiding Context Rot
To prevent context loss during this multi-phase implementation:

1. **Phase Isolation**: Each phase is self-contained; complete one phase before starting next
2. **Subagent Delegation**: Use Task tool with specific, focused prompts for each parallel group
3. **Checkpoint Commits**: Commit after each phase to create restore points
4. **Handoff Files**: Update `docs/active-context.md` after each phase with current state

### Subagent Prompt Template
```
Implement [TASK_ID]: [DESCRIPTION]

Context:
- Working in /frontend/src/
- Using design tokens from styles/globals.css
- Following Shadcn-style component patterns
- Must maintain existing test coverage

Files to modify:
- [FILE_PATH_1]
- [FILE_PATH_2]

Expected outcome:
- [SPECIFIC_DELIVERABLE]

Run tests after changes: npm run test
```

### Recovery Points
After each commit checkpoint, the following should be true:
- `npm run build` succeeds
- `npm run test` passes (255+ tests)
- No TypeScript errors
- Visual appearance matches design intent

---

## References
- [Frontend Design Assessment](./FRONTEND_DESIGN_ASSESSMENT.md)
- [V2 UI BottomNav](../../../src/components/navigation/BottomNav.tsx)
- [V2 UI Card Component](../../../src/components/ui/card.tsx)
- [V2 UI Styles](../../../src/styles.css)
- [Legacy Globals CSS](../src/styles/globals.css)
- [Shadcn UI Card Docs](https://ui.shadcn.com/docs/components/card)
