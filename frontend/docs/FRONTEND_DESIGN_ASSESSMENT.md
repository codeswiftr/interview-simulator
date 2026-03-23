# Frontend Design Assessment

**Date**: December 18, 2025
**Status**: Strategic Review Complete

---

## Executive Summary

The Interview Simulator has **two parallel frontend implementations**:

| Implementation | Location | Design System | Status |
|----------------|----------|---------------|--------|
| Legacy Frontend | `/frontend/` | Custom RGB-based | Production (running on port 5173) |
| Modern v2 UI | `/src/` | Shadcn/HSL-based | Development (running on port 5176) |

**Key Finding**: The v2 UI (`/src/`) implements a cleaner, more modern design with mobile-first bottom navigation and simpler card components. The user prefers this Linear-inspired aesthetic. However, v2 is incomplete - many pages are stub implementations without full functionality.

---

## Architecture Comparison

### Design Token Systems

| Aspect | Legacy (`/frontend/`) | v2 UI (`/src/`) | Reference (`/vite-app/`) |
|--------|----------------------|-----------------|--------------------------|
| Color Format | HEX/RGB (`#38BDF8`) | HSL (`197 91% 60%`) | OKLCH (`oklch(0.60 0.13 163)`) |
| Dark Mode | CSS variables + `.dark` class | HSL variables | OKLCH with full support |
| Component Library | Custom | Shadcn-inspired Card | Full Shadcn UI |
| Variant System | Inline styles | CSS classes | CVA (class-variance-authority) |

### Navigation Patterns

| Pattern | Legacy | v2 UI |
|---------|--------|-------|
| Desktop | Header with dropdown menus | Minimal header |
| Mobile | Hamburger menu in Header | **Bottom navigation bar** (iOS/Android native pattern) |
| Routes | /dashboard, /questions, /settings, /interview/:id, /feedback/:id | + **/practice**, **/progress** |

### Component Quality

| Component | Legacy | v2 UI |
|-----------|--------|-------|
| Cards | Glass morphism, gradients, heavy shadows | Flat, minimal borders, clean |
| Buttons | Gradient backgrounds, glow effects | Solid colors, subtle hover states |
| Typography | Multiple custom heading classes | Simpler heading hierarchy |
| Animation | Heavy (slide-up, scale-in, float, pulse) | Minimal (transitions only) |

---

## Page-by-Page Analysis

### Dashboard Page
| Aspect | Legacy | v2 UI | Recommendation |
|--------|--------|-------|----------------|
| Stats Cards | 4 glass cards with icons | 4 simpler cards | v2 cleaner |
| Activity Heatmap | Present | Missing | Keep from legacy |
| Skills Radar | Present | Missing | Keep from legacy |
| Progress Chart | Present | Missing | Keep from legacy |
| Onboarding Panel | Present | Missing | Keep from legacy |

### Progress Page
| Aspect | Legacy | v2 UI | Recommendation |
|--------|--------|-------|----------------|
| Route | Not defined | `/progress` | Add to production |
| Design | N/A | Simple 2-card layout | Good foundation |
| Data | N/A | Static placeholder | Needs API integration |

### Practice Page (Question Bank)
| Aspect | Legacy | v2 UI | Recommendation |
|--------|--------|-------|----------------|
| Route | `/questions` | `/practice` | Both valid |
| Filters | Basic dropdowns | Modern dropdowns | Similar |
| Question Cards | Complex with company tags | Similar | Both acceptable |

### Settings Page
| Aspect | Legacy | v2 UI | Recommendation |
|--------|--------|-------|----------------|
| Voice Settings | Full panel | Missing | Port from legacy |
| Theme | Slider component | Missing | Port from legacy |
| Subscription | Full integration | Missing | Port from legacy |

---

## Identified Gaps

### Missing in v2 UI (need porting from legacy)
1. **StatsOverview component** with readiness score
2. **ActivityHeatmap** visualization
3. **SkillsRadar** chart
4. **ProgressChart** with score trends
5. **CategoryBreakdown** analysis
6. **VoiceSettingsPanel** for audio preferences
7. **SubscriptionCard** and **UpgradeModal**
8. **WelcomeModal** and **FirstSessionPrompt** for onboarding
9. **CoachOverlay** for interview hints
10. **ThemeSlider** for theme selection

### Missing in Legacy (need from v2)
1. **BottomNav** component for mobile
2. **ProgressPage** dedicated route
3. Simplified card design patterns

---

## Recommended Epics

### Epic 5: Design System Unification (Priority: HIGH)
**Goal**: Establish a single source of truth for design tokens

**Tasks**:
1. [ ] Adopt HSL color system from v2 (better for programmatic manipulation)
2. [ ] Create shared design tokens file importable by both implementations
3. [ ] Standardize on Shadcn-style Card component API
4. [ ] Unify button variants (primary, secondary, ghost, destructive)
5. [ ] Create shared typography scale

**Estimated Complexity**: Medium (3-5 days)

---

### Epic 6: Navigation Modernization (Priority: HIGH)
**Goal**: Implement mobile-first navigation pattern across the app

**Tasks**:
1. [ ] Port BottomNav from v2 to legacy frontend
2. [ ] Add /progress route to App.tsx
3. [ ] Create ProgressPage with proper API integration
4. [ ] Update Header to be responsive (hide on mobile when BottomNav visible)
5. [ ] Update App.tsx routes to include all v2 routes

**Estimated Complexity**: Medium (2-3 days)

---

### Epic 7: Component Migration (Priority: MEDIUM)
**Goal**: Consolidate components from both implementations

**Tasks**:
1. [ ] Migrate Card component to Shadcn-style API with `CardHeader`, `CardContent`, etc.
2. [ ] Update StatsOverview to use new Card API
3. [ ] Simplify glass morphism effects (reduce blur, remove gradients)
4. [ ] Port ScoreRing from v2 (if improved)
5. [ ] Unify Badge components

**Estimated Complexity**: Medium (3-4 days)

---

### Epic 8: Dashboard Simplification (Priority: MEDIUM)
**Goal**: Reduce visual complexity while preserving functionality

**Tasks**:
1. [ ] Remove or reduce background gradient decorations
2. [ ] Flatten card designs (remove `card-glass` in favor of `card`)
3. [ ] Simplify animation usage (remove float, reduce slide-up delays)
4. [ ] Make charts more compact
5. [ ] Improve empty state designs

**Estimated Complexity**: Low (2 days)

---

### Epic 9: Settings & Subscription Polish (Priority: LOW)
**Goal**: Complete settings page with all features

**Tasks**:
1. [ ] Ensure VoiceSettingsPanel works in v2 context
2. [ ] Port SubscriptionCard with proper Stripe integration
3. [ ] Add theme toggle to v2 Settings
4. [ ] Create account management section

**Estimated Complexity**: Medium (2-3 days)

---

## Recommended Strategy

### Option A: Evolve Legacy (Recommended)
- Keep `/frontend/` as primary codebase
- Incrementally adopt v2 patterns (BottomNav, simplified cards)
- Preserve rich functionality (charts, heatmaps, onboarding)
- Total effort: ~2 weeks

### Option B: Complete v2
- Port all legacy components to `/src/`
- Risk of regression (many features to reimplement)
- Cleaner codebase but higher effort
- Total effort: ~4 weeks

### Option C: Merge
- Create new unified `/app/` directory
- Cherry-pick best from both implementations
- Highest quality but most effort
- Total effort: ~3-4 weeks

---

## Immediate Next Steps

1. **Decision Required**: Choose between Option A, B, or C
2. **If Option A**: Start with Epic 6 (Navigation) - port BottomNav
3. **Create Issue Tickets**: Break epics into trackable issues
4. **Design Review**: Get stakeholder sign-off on target aesthetic

---

## Screenshots Reference

| Page | Legacy | v2 UI |
|------|--------|-------|
| Dashboard | Complex with charts | Simple stats cards |
| Progress | N/A | Clean 2-column |
| Practice | Full question bank | Full question bank |
| Settings | Full settings | Basic stub |

*Screenshots saved to: `/.playwright-mcp/`*
- `dashboard-with-bottom-nav.png`
- `progress-page.png`
- `practice-page.png`
