# Interview Simulator – Frontend Production Readiness Audit

**Date:** 2026-02-06  
**Stack:** React 19, TypeScript, Vite 7, TailwindCSS v4  
**Scope:** `codeswiftr-com/interview-simulator/frontend/`

---

## Executive Summary

| Area | Overall | Critical | High | Medium | Low |
|------|---------|----------|------|--------|-----|
| Build | ⚠️ Pass with warnings | 0 | 1 | 1 | 0 |
| Console / React warnings | ✅ | 0 | 0 | 0 | 0 |
| Accessibility | ✅ | 0 | 0 | 2 | 2 |
| Mobile responsiveness | ✅ | 0 | 0 | 1 | 0 |
| Error boundaries | ⚠️ | 0 | 1 | 0 | 0 |
| Loading / skeletons | ✅ | 0 | 0 | 1 | 0 |
| SEO meta tags | ✅ | 0 | 0 | 0 | 1 |
| Performance | ✅ | 0 | 0 | 1 | 1 |
| Environment config | ⚠️ | 0 | 1 | 0 | 0 |

The app is in good shape for production. Address the **HIGH** items (build env placeholder, error boundary coverage) and the **MEDIUM** items for a stronger launch.

---

## 1. Build (succeeds with warnings)

**Result:** Build succeeds; two non-blocking warnings.

| Finding | Severity | Details |
|---------|----------|---------|
| `%VITE_REWARDFUL_API_KEY%` not defined | **HIGH** | `index.html` line 34: `<script ... data-rewardful='%VITE_REWARDFUL_API_KEY%'></script>`. Vite replaces only `import.meta.env.VITE_*` in JS; HTML is not processed by default, so the literal string appears in the built HTML. In production this can load Rewardful with an invalid key or break the script. |
| baseline-browser-mapping data outdated | **MEDIUM** | Build log: "The data in this module is over two months old". Affects accuracy of baseline/browser targeting, not runtime. |

**Fix recommendations**

1. **Rewardful in HTML (HIGH):**  
   - **Option A:** Inject the key at build time: use a Vite plugin (e.g. `vite-plugin-html`) to replace a placeholder in `index.html` with `import.meta.env.VITE_REWARDFUL_API_KEY`.  
   - **Option B:** Load Rewardful from JS only when the key exists (e.g. in `main.tsx` or a small bootstrap script): `if (import.meta.env.VITE_REWARDFUL_API_KEY) { loadRewardful(import.meta.env.VITE_REWARDFUL_API_KEY); }` and remove the script from `index.html`.  
   - **Option C:** If Rewardful is optional, keep the script out of the default template and add it only in a build variant that defines the key.

2. **baseline-browser-mapping (MEDIUM):** Run `npm i baseline-browser-mapping@latest -D` and re-build.

---

## 2. Console errors and React warnings

**Result:** No console or React warnings identified in the codebase.

- No `useEffect` dependency-array issues that would obviously cause runtime warnings.
- No invalid or missing `key` in critical list paths (some lists use `key={idx}`; see Performance).
- Error boundary uses `componentDidCatch` and `getDerivedStateFromError` correctly.

**Recommendation:** Run the app and full E2E suite in dev, and in production build, and fix any warnings that appear (e.g. from React 19 strict mode or router).

---

## 3. Accessibility (a11y)

**Result:** Good coverage; a few targeted improvements.

| Finding | Severity | Details |
|---------|----------|---------|
| Modal has dialog semantics | ✅ | `Modal.tsx` uses `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, focus trap, Escape to close, and close button has `aria-label="Close modal"`. |
| Live regions for errors and status | ✅ | Login, Register, ResetPassword, InterviewPage, Toast, OfflineIndicator, TranscriptionDisplay, CoachOverlay, BrowserWarning use `role="alert"` and/or `aria-live` appropriately. |
| Record button | ✅ | RecordButton uses visible text ("Start Recording" / "Stop Recording") and `aria-hidden="true"` on decorative icons. |
| Skip link | ✅ | Header has a skip link with `sr-only focus:not-sr-only`. |
| Offline page retry button | **MEDIUM** | `public/offline.html`: retry button has no `aria-label`. Screen reader users only get "Try Again" and the icon. |
| Skeleton / loading semantics | **MEDIUM** | Skeleton UIs do not use `aria-busy` or `aria-live="polite"` on the loading container. Screen readers may not announce loading state. |
| List keys and semantics | **LOW** | Some lists use `key={idx}`; prefer stable IDs where possible for dynamic lists (also helps reconciliation). |
| Offline page SVG | **LOW** | `offline.html` SVG has no `aria-hidden="true"` or descriptive `aria-label` where the icon is decorative. |

**Fix recommendations**

1. **Offline retry button (MEDIUM):** Add `aria-label="Retry connection"` (or similar) to the retry button in `public/offline.html`.  
2. **Loading/skeleton (MEDIUM):** On data-heavy pages (Dashboard, Feedback, Progress, SharedInterview), wrap skeleton/content in a container with `aria-busy={isLoading}` and optionally `aria-live="polite"` so assistive tech can announce loading.  
3. **Offline SVG (LOW):** Add `aria-hidden="true"` to the decorative WiFi-off SVG in `offline.html`.

---

## 4. Mobile responsiveness

**Result:** Good use of breakpoints and mobile patterns.

- Tailwind breakpoints (`sm:`, `md:`, `lg:`) are used across pages and components (e.g. Header, HomePage, QuestionsPage, RecordingDeck, SettingsPage).
- Viewport meta: `width=device-width, initial-scale=1.0, viewport-fit=cover` in both `index.html` and `offline.html`.
- Bottom nav is present; Footer is `hidden md:block` so mobile uses the nav.
- Touch targets: Buttons and links generally use adequate padding (e.g. `px-8 py-4`, `p-3`).

| Finding | Severity | Details |
|---------|----------|---------|
| QuestionsPage loading | **MEDIUM** | Loading state is a centered spinner + text. Consider a skeleton that mirrors the question grid (e.g. card-shaped placeholders) for a more consistent mobile layout and perceived performance. |

**Fix recommendation:** Add a skeleton or card-placeholder loading state for the question list on QuestionsPage (aligned with Dashboard, Feedback, Progress).

---

## 5. Error boundary coverage

**Result:** One global boundary; some high-impact routes lack local boundaries.

| Location | Coverage |
|----------|----------|
| App root | ✅ Single `<ErrorBoundary>` wraps the whole app. |
| InterviewPage | ✅ Wraps interview content in its own `<ErrorBoundary>`. |
| FeedbackPage | ✅ Wraps feedback content in its own `<ErrorBoundary>`. |
| DashboardPage | ❌ No local boundary. A failure in charts, Recharts, or a heavy child can bring down the whole page. |
| QuestionsPage | ❌ No local boundary. |
| SettingsPage | ❌ No local boundary (complex form and API calls). |
| PreparationPage | ❌ No local boundary. |
| ProgressPage | ❌ No local boundary. |
| SharedInterviewPage | ❌ No local boundary. |

ErrorBoundary implementation is solid: fallback UI, Sentry reporting, reset and "Go Home" actions, dev-only error details.

| Finding | Severity | Details |
|---------|----------|---------|
| No local boundary on Dashboard | **HIGH** | Dashboard uses Recharts and multiple data sources. A single component error (e.g. chart, skills radar) could take down the entire page. Users lose the whole dashboard instead of a single section. |

**Fix recommendations**

1. **HIGH:** Wrap the main content (or at least the chart/analytics section) of `DashboardPage` in an `<ErrorBoundary>` with a section-level fallback (e.g. "This section failed to load" + retry).  
2. Optionally add section-level boundaries to SettingsPage, PreparationPage, and ProgressPage for consistent resilience.

---

## 6. Loading states and skeleton screens

**Result:** Good coverage; one page could be improved.

| Page / component | Loading / skeleton |
|------------------|--------------------|
| App (route lazy load) | ✅ `<Suspense>` with `PageLoadingFallback` (spinner + "Loading..."). |
| DashboardPage | ✅ Skeleton: `SkeletonStatsOverview`, `SkeletonInterviewList`, and text placeholders. |
| FeedbackPage | ✅ Skeleton: `Skeleton`, `SkeletonScoreRing`, `SkeletonText`, and card placeholders. |
| ProgressPage | ✅ Skeleton: multiple `Skeleton` blocks for charts/cards. |
| InterviewPage | ✅ `SkeletonQuestion` while loading. |
| SharedInterviewPage | ✅ Skeleton layout with score rings and text. |
| SettingsPage | ✅ Spinner + "Loading settings..." while fetching. |
| QuestionsPage | ⚠️ Spinner + "Loading questions..." only; no skeleton. |
| Login / Register / Pricing | ✅ Button `loading` state and/or inline spinners. |

| Finding | Severity | Details |
|---------|----------|---------|
| QuestionsPage | **MEDIUM** | Uses a single centered spinner. A skeleton that approximates the question grid (e.g. 6–8 card-shaped blocks) would improve perceived performance and align with other pages. |

**Fix recommendation:** Add a skeleton similar to Dashboard or Progress (card/grid placeholders) for the question list on QuestionsPage.

---

## 7. SEO meta tags

**Result:** Solid baseline and PWA meta.

- **Title:** "Interview Simulator - CareerSwiftr" in `index.html`.
- **Description:** `<meta name="description" content="AI-powered interview practice for software engineers...">`.
- **Viewport:** `width=device-width, initial-scale=1.0, viewport-fit=cover`.
- **PWA:** theme-color, mobile-web-app-capable, apple-mobile-web-app-*.
- **OG:** og:type, og:title, og:description, og:image.
- **Twitter:** twitter:card summary_large_image.
- **Favicons:** 32, 16, apple-touch 192.

| Finding | Severity | Details |
|---------|----------|---------|
| Per-route meta | **LOW** | Title/description are static. For deeper SEO (e.g. /pricing, /blog/:slug), consider React Helmet or similar to set title/description per route. |

**Fix recommendation (LOW):** Add per-route meta (e.g. `react-helmet-async` or Vite/SSR meta) for key marketing and content routes.

---

## 8. Performance (bundle size, lazy loading)

**Result:** Good code splitting and chunking; one large dependency.

**Lazy loading**

- Heavy routes are lazy-loaded: Dashboard, Questions, Interview, Feedback, Settings, Preparation, Progress, SharedInterview, BlogList, BlogPost, DevPreview.
- Core auth and marketing (Home, Login, Register, ForgotPassword, ResetPassword, VerifyEmail, Pricing, Affiliate) are eager-loaded.

**Manual chunks (vite.config.ts)**

- react-vendor, recharts, axios, query, ui-vendor, sentry, analytics are split.
- `chunkSizeWarningLimit: 600` suppresses warnings for large chunks.

**Reported bundle (gzip)**

- react-vendor ~132 KB; index main ~29 KB; recharts ~102 KB; DashboardPage ~32 KB; FeedbackPage ~11 KB; PreparationPage ~11 KB; BlogPostPage ~44 KB; analytics ~55 KB.
- Total precache (PWA) ~4 MB.

| Finding | Severity | Details |
|---------|----------|---------|
| Recharts size | **MEDIUM** | recharts chunk is ~335 KB (min), ~102 KB gzip. Only Dashboard (and possibly Progress) use it. It is already in its own chunk and lazy with the page; consider replacing or trimming chart types if further reduction is needed. |
| key={idx} in lists | **LOW** | PricingPage and a few others use `key={idx}` for list items. Prefer stable IDs (e.g. plan id, question id) to avoid unnecessary re-renders and reconciliation issues when list order or content changes. |

**Fix recommendations**

1. **MEDIUM:** If bundle size is a concern, profile which chart components are used and tree-shake or replace with a lighter chart lib for simple visualizations.  
2. **LOW:** Replace `key={idx}` with stable IDs where the list can change (e.g. PricingPage plan cards, AffiliatePage benefits).

---

## 9. Environment config correctness

**Result:** API and optional keys are documented; production build has one gap.

- **VITE_API_URL:** Used in `lib/api.ts`; fallback `http://localhost:8000/api/v1`. `.env.example` and `.env.production` document and set it.
- **VITE_FORGE_CORE_URL:** Documented in `.env.example`; not referenced in the audited `api.ts` (may be used elsewhere).
- **VITE_POSTHOG_KEY / VITE_POSTHOG_HOST:** Optional; documented.
- **VITE_SENTRY_DSN:** Optional; documented.
- **VITE_REWARDFUL_API_KEY:** Documented in `.env.example` but **not** in `.env.production`. It is referenced in `index.html` as a literal placeholder, and Vite does not substitute env in HTML by default.

| Finding | Severity | Details |
|---------|----------|---------|
| Rewardful in production | **HIGH** | `.env.production` does not define `VITE_REWARDFUL_API_KEY`. Even if defined, the value would not be injected into `index.html` unless the build pipeline is changed (see §1). Production builds will ship with the literal `%VITE_REWARDFUL_API_KEY%` in the script tag unless fixed. |

**Fix recommendations**

1. **HIGH:** Resolve Rewardful loading as in §1 (inject at build time or load from JS when key exists).  
2. Add `VITE_REWARDFUL_API_KEY` to `.env.production` (or deployment env) when using Rewardful in production, and ensure the chosen injection method is used so the script receives the key.

---

## 10. Additional notes

- **PWA:** Service worker, manifest, offline.html, InstallPrompt, OfflineIndicator are in place. `navigateFallback: '/offline.html'` is configured.
- **Security:** No secrets found in frontend code; API base URL and optional keys are env-driven.
- **Tests:** `vitest-axe` and an accessibility test (e.g. FeedbackPage) exist; expand a11y tests to other key flows.

---

## 11. Prioritized action list

| Priority | Severity | Action |
|----------|----------|--------|
| 1 | HIGH | Fix Rewardful: load from JS when `VITE_REWARDFUL_API_KEY` is set, or inject into HTML at build time; ensure production env sets the key if used. |
| 2 | HIGH | Add an ErrorBoundary around the main (or chart) section of DashboardPage. |
| 3 | MEDIUM | Add skeleton loading for QuestionsPage (card/grid placeholders). |
| 4 | MEDIUM | Add `aria-busy` (and optionally `aria-live`) to skeleton/loading containers on data-heavy pages. |
| 5 | MEDIUM | Add `aria-label` to the retry button in `public/offline.html`. |
| 6 | MEDIUM | Update baseline-browser-mapping: `npm i baseline-browser-mapping@latest -D`. |
| 7 | MEDIUM | Evaluate Recharts bundle size; consider lighter charts or tree-shaking if needed. |
| 8 | LOW | Prefer stable list keys (e.g. IDs) instead of `key={idx}` where lists are dynamic. |
| 9 | LOW | Per-route meta (title/description) for pricing and blog. |
| 10 | LOW | Add `aria-hidden="true"` to decorative SVG in `offline.html`. |

---

*Audit performed against the frontend at `codeswiftr-com/interview-simulator/frontend/` (React 19, TypeScript, Vite 7, TailwindCSS v4). Build command: `npm run build`.*
