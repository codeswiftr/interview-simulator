# Agent Continuation Prompt

## Project Overview
**Project**: Interview Simulator Frontend
**Purpose**: AI-powered interview practice platform for software engineers with real-time audio analysis and Claude-generated feedback
**Tech Stack**: React 19 + TypeScript + Vite + TailwindCSS v4 + Axios
**Repository**: `/Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/frontend`

---

## Current State

### Branch
`main` - Primary development branch (feature branches not required for this project)

### Recent Progress
- ✅ Completed Epic 3: Component Refactoring (InterviewContext, InterviewHeader, RecordingSection, etc.)
- ✅ Completed Epic 4: Fixed broken tests after refactoring (useOnboarding, page tests)
- ✅ Created comprehensive Frontend Design Assessment (`docs/FRONTEND_DESIGN_ASSESSMENT.md`)
- ✅ Created detailed implementation plan for Epics 5-9 (`docs/PLAN.md`)
- ✅ **Completed Epic 6: Navigation Modernization** (BottomNav, ProgressPage, /practice & /progress routes)
- ✅ **Completed Epic 5: Design Token Unification** (HSL color system, design-tokens.css)
- ✅ **Completed Epic 7: Component API Migration** (Shadcn-style Card components)
- ✅ **Completed Epic 8: Dashboard Simplification** (cleaner cards, compact heatmap, improved empty state)
- 🔄 Ready to start Epic 9: Settings & Polish

### Current Focus
**Frontend Design System Unification** - Merging best practices from two parallel frontend implementations:
- Legacy frontend (`/frontend/`) - Full-featured but older design patterns
- V2 UI (`/src/` at parent level) - Cleaner Linear-inspired design with bottom nav

### Blockers/Issues
- 7 pre-existing test failures in `useAudioRecording.test.tsx` (timing issues, not blocking)
- 263 tests passing, build succeeds

---

## Active Plan
**Plan File**: `docs/PLAN.md`
**Current Phase**: Phase 4: Dashboard Simplification (Epic 8)
**Current Task**: Task 8.1: Simplify DashboardPage layout
**Status**: Ready to start

### Immediate Next Steps
1. Review docs/PLAN.md for Epic 8 tasks
2. Simplify DashboardPage layout structure
3. Reduce visual complexity while maintaining functionality
4. Optimize mobile responsiveness
5. Add appropriate loading states and error handling
6. Commit: `refactor(frontend): simplify dashboard layout`

---

## Key Context

### Important Files
| File | Purpose |
|------|---------|
| `src/App.tsx` | Route definitions - needs /progress, /practice routes |
| `src/components/layout/Header.tsx` | Desktop navigation - needs mobile menu hiding |
| `src/styles/globals.css` | Design tokens - will migrate to HSL in Epic 5 |
| `docs/PLAN.md` | Implementation plan with 38 tasks across 5 epics |
| `docs/FRONTEND_DESIGN_ASSESSMENT.md` | Design gap analysis between frontends |

### Reference Files (V2 UI to port from)
| File | Purpose |
|------|---------|
| `../src/components/navigation/BottomNav.tsx` | Mobile navigation to port |
| `../src/views/ProgressPage.tsx` | Progress page template |
| `../src/shell/AppShell.tsx` | Route structure reference |
| `../src/styles.css` | HSL design tokens reference |

### Recent Decisions
- **Strategy: Evolve Legacy** - Keep `/frontend/` as primary, incrementally adopt v2 patterns
- **HSL Colors** - Will migrate from HEX to HSL for better theming flexibility
- **Shadcn-style Cards** - Will adopt Card/CardHeader/CardContent API pattern
- **Keep /questions route** - Maintain as alias for /practice for backwards compat

### Gotchas Discovered
- ⚠️ Two parallel frontends exist: `/frontend/` (port 5173) and `/src/` (port 5176)
- ⚠️ V2 UI uses React Query; legacy uses direct Axios - don't mix for now
- ⚠️ useAudioRecording tests have pre-existing timing issues - ignore for now
- ⚠️ Bottom nav needs `pb-16` on main content to avoid overlap

### Patterns to Follow
- **Component API**: Use Shadcn-style slots (CardHeader, CardContent, CardFooter)
- **Design Tokens**: HSL format `--color-name: H S% L%` without `hsl()` wrapper
- **Responsive**: Use `md:hidden` for mobile-only, `hidden md:flex` for desktop-only
- **Commit Messages**: Conventional format `feat(frontend): description`

### Things to Avoid
- ❌ Don't add React Query to legacy frontend (defer for later)
- ❌ Don't remove card-glass until Epic 7 (Card component migration)
- ❌ Don't modify useAudioRecording tests (pre-existing issues)
- ❌ Don't commit to a feature branch - work directly on main

---

## Commands to Run

### Verify Environment
```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/frontend
npm run build
```

### Run Tests
```bash
npm run test -- --run
# Expect 255 passed, 7 failed (pre-existing)
```

### Start Development
```bash
npm run dev
# Opens on http://localhost:5173
```

### View V2 UI for Reference
```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator
npm run dev
# Opens on http://localhost:5176
```

---

## Instructions for New Agent

### Mindset
You are a pragmatic senior engineer continuing frontend design system unification. Your approach:
- Apply Pareto principle - 20% effort for 80% value
- Port components from v2 UI, adapting to legacy patterns
- Preserve all existing functionality while modernizing design
- Clean commits after each phase completion

### Workflow
1. Read this context and `docs/PLAN.md`
2. Run `npm run build` to verify current state
3. Start with Task 6.1: Create BottomNav component
4. Use `frontend-design` skill for UI/UX decisions
5. Use `frontend-builder` agent for implementation
6. Commit after completing Phase 1 (Epic 6)

### Quality Gates
After each change:
1. Run `npm run build` - must succeed
2. Run `npm run test -- --run` - 255+ tests must pass
3. Visual check on localhost:5173
4. Commit with conventional message

### Parallel Execution
For Epic 6, launch two parallel subagents:
- **Group A**: BottomNav (tasks 6.1-6.3)
- **Group B**: ProgressPage (tasks 6.4-6.6)

### If Stuck
- Check v2 UI reference at `../src/components/navigation/BottomNav.tsx`
- Use `/debug` for complex issues
- Check `docs/FRONTEND_DESIGN_ASSESSMENT.md` for design decisions
- The 7 failing tests are pre-existing - don't try to fix them

---

## Epic Summary

| Epic | Status | Tasks | Est |
|------|--------|-------|-----|
| Epic 6: Navigation | ✅ Complete | 8 | 10.5h |
| Epic 5: Design Tokens | ✅ Complete | 7 | 7.5h |
| Epic 7: Component API | ✅ Complete | 9 | 10.5h |
| Epic 8: Dashboard | ✅ Complete | 7 | 5.5h |
| Epic 9: Settings | ✅ Complete | 7 | 7.5h |

---

## Milestone Complete

All 5 epics of the Frontend Design System Unification have been completed:

### Summary of Changes
- **Epic 6**: Added BottomNav mobile navigation, ProgressPage, /practice route
- **Epic 5**: Migrated to HSL design tokens in design-tokens.css
- **Epic 7**: Created Shadcn-style Card component API, migrated all pages
- **Epic 8**: Simplified dashboard visual design, compact charts, improved empty states
- **Epic 9**: Settings page polish, Account Overview section, accessibility improvements

### Quality Metrics
- Build: ✅ Passes
- Tests: 263 passing, 7 pre-existing failures (useAudioRecording timing)
- Bundle sizes optimized (Dashboard: 476KB)

### Ready for Next Steps
The frontend design system is now unified and ready for:
1. E2E testing and visual regression
2. Performance optimization (code splitting for DashboardPage)
3. Feature development on the new foundation
