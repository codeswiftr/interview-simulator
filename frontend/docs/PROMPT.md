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
- 🔄 Ready to start Epic 5: Design Token Unification

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
**Current Phase**: Phase 2: Design Token Unification (Epic 5)
**Current Task**: Task 5.1: Create design-tokens.css
**Status**: Ready to start

### Immediate Next Steps
1. Create `design-tokens.css` with HSL variables from v2 styles.css
2. Update globals.css to import and use HSL tokens
3. Update button classes (.btn-primary, etc) to use HSL
4. Update card classes (.card, .card-glass) to use HSL
5. Update input/form classes to use HSL
6. Run visual regression check on all pages
7. Commit: `feat(frontend): migrate to HSL design tokens`

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
| Epic 6: Navigation | **NEXT** | 8 | 10.5h |
| Epic 5: Design Tokens | Pending | 7 | 7.5h |
| Epic 7: Component API | Pending | 9 | 10.5h |
| Epic 8: Dashboard | Pending | 7 | 5.5h |
| Epic 9: Settings | Pending | 7 | 7.5h |

---

## Resume Command

To continue work, start with:
```
Read docs/PROMPT.md and docs/PLAN.md, verify build passes with `npm run build`, then start Epic 6 Phase 1.

Launch parallel subagents:
- Group A: Create BottomNav component (tasks 6.1-6.3)
- Group B: Create ProgressPage (tasks 6.4-6.6)

After both complete, run tests and commit:
`feat(frontend): add mobile bottom navigation and progress page`

DO NOT STOP! Continue with the plan like an empowered, pragmatic senior engineer.
```
