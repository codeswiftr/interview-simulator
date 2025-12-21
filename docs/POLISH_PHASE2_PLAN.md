# Interview Simulator Polish Phase 2

## Status: Ready
## Target: Sprint 7 (Current)

---

## Overview

This plan addresses critical bugs discovered during testing, plus completes the deferred UI polish items from Phase 1. The issues include:

1. **Critical Bug**: Registration error crashes React (rendering object as child)
2. **Critical Bug**: Black screen after interview submission (route mismatch)
3. **Deferred**: Modal pattern standardization
4. **Deferred**: Chart theme integration

## Success Criteria

- [ ] Registration works with proper validation error display
- [ ] Interview → Feedback flow navigates correctly
- [ ] All modals use consistent Dialog component
- [ ] Charts respect dark/light theme
- [ ] No React rendering errors in console

---

## Technical Design

### Issue 1: Registration Error Rendering Objects

**Root Cause**: FastAPI validation errors return `detail` as an array of objects:
```json
{
  "detail": [
    {"type": "string_type", "loc": ["body", "password"], "msg": "Password too short", "input": "...", "ctx": {...}}
  ]
}
```

The code directly renders `{error}` in a `<p>` tag, but when `detail` is an array of objects, React crashes with "Objects are not valid as a React child".

**Fix**: Parse validation errors properly:
```tsx
// Helper to extract error message
function parseAPIError(err: AxiosError<{ detail?: string | ValidationError[] }>): string {
  const detail = err.response?.data?.detail;
  if (!detail) return 'An error occurred';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map(e => e.msg).join('. ');
  }
  return 'An error occurred';
}
```

**Files**:
- `src/views/RegisterPage.tsx`
- `src/views/LoginPage.tsx`
- `src/lib/api.ts` (add helper)

### Issue 2: Route Mismatch After Interview

**Root Cause**: InterviewPage navigates to `/interview/${id}/feedback` but router has `/feedback/:id`

**Fix**: Change navigation in InterviewPage:
```tsx
// Before
navigate(`/interview/${id}/feedback`);
// After
navigate(`/feedback/${id}`);
```

**Files**:
- `src/views/InterviewPage.tsx` (line 430)

### Issue 3: Modal Standardization

**Current State**: 5 modal implementations with inconsistent patterns:
- `WelcomeModal` - Custom implementation, blue gradient header
- `NewInterviewModal` - Uses custom card
- `UpgradeModal` - Uses Dialog component
- `SampleAnswerModal` - Uses Dialog component
- `InterviewPage` exit modal - Inline implementation

**Target**: All modals use `Dialog` component from `src/components/ui/dialog.tsx`

**Dialog Variants to Add**:
```tsx
// Add to dialog.tsx
variant?: 'default' | 'branded' | 'destructive' | 'fullscreen'
```

### Issue 4: Chart Theme Integration

**Current State**: ProgressChart uses CSS variables correctly (`var(--color-electric-blue)`), but other chart components may use hardcoded colors.

**Files to audit**:
- `src/components/dashboard/ProgressChart.tsx` - Already themed
- `src/components/dashboard/SkillsRadar.tsx` - Check theming
- `src/components/dashboard/CategoryBreakdown.tsx` - Check theming
- `src/components/dashboard/ActivityHeatmap.tsx` - Check theming

---

## Implementation Plan

### Phase 1: Critical Bug Fixes (P0)
| Task | Description | Agent | Est | Status |
|------|-------------|-------|-----|--------|
| 1.1 | Fix validation error parsing in RegisterPage | - | 30m | ✅ Done |
| 1.2 | Fix validation error parsing in LoginPage | - | 15m | ✅ Done |
| 1.3 | Create parseAPIError helper in api.ts | - | 15m | ✅ Done |
| 1.4 | Fix feedback route navigation | - | 10m | ✅ Done |
| 1.5 | Add `/interview/:id/feedback` route as alias | - | 10m | ✅ Done |

**Checkpoint**: Registration and interview flow work without crashes ✅

### Phase 2: Modal Standardization (P2)
| Task | Description | Agent | Est | Status |
|------|-------------|-------|-----|--------|
| 2.1 | Add Dialog variants (branded, destructive) | frontend-builder | 1h | ⏸️ Deferred |
| 2.2 | Migrate WelcomeModal to Dialog | - | 30m | ⏸️ Deferred |
| 2.3 | Migrate NewInterviewModal to Dialog | - | 30m | ⏸️ Deferred |
| 2.4 | Migrate InterviewPage exit modal to Dialog | - | 20m | ⏸️ Deferred |
| 2.5 | Document modal patterns in DESIGN_SYSTEM.md | - | 20m | ⏸️ Deferred |

**Note**: Existing modals (WelcomeModal, NewInterviewModal) are already well-styled and functional.
Full migration deferred - would require significant refactoring with low incremental value.

**Checkpoint**: ⏸️ Deferred - existing modals are production-ready

### Phase 3: Chart Theme Integration (P3)
| Task | Description | Agent | Est | Status |
|------|-------------|-------|-----|--------|
| 3.1 | Audit SkillsRadar for hardcoded colors | - | 15m | ✅ Done - uses CSS vars |
| 3.2 | Audit CategoryBreakdown for hardcoded colors | - | 15m | ✅ Done - uses Tailwind |
| 3.3 | Audit ActivityHeatmap for hardcoded colors | - | 15m | ✅ Done - uses Tailwind |
| 3.4 | Add chart color tokens to styles.css | - | 20m | ⏸️ Not needed |
| 3.5 | Update charts to use CSS variables | - | 1h | ⏸️ Not needed |

**Audit Results**:
- ProgressChart: Already uses `var(--color-electric-blue)`, `var(--color-border-light)` ✅
- SkillsRadar: Uses CSS variables throughout ✅
- CategoryBreakdown: Uses Tailwind classes (dark mode compatible) ✅
- ActivityHeatmap: Uses Tailwind classes with `dark:` variants ✅

**Checkpoint**: Charts already theme-aware ✅

---

## Testing Strategy

- **Manual Testing**: Registration flow, interview completion, modal interactions
- **Visual Testing**: Light/dark mode switching for all affected components
- **Error Scenarios**: Test with invalid passwords, network errors

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dialog migration breaks existing modals | High | Test each modal individually |
| CSS variable changes affect other components | Medium | Audit before changing tokens |

## Open Questions

- [x] Should we add route alias or fix navigation? → Do both for safety
- [ ] Should WelcomeModal retain its gradient header? → Keep branding

## References

- Previous plan: `docs/UI_POLISH_PLAN.md`
- Design system: `docs/DESIGN_SYSTEM.md`
- Dialog component: `src/components/ui/dialog.tsx`
