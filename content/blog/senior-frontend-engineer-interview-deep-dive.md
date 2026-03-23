---
title: "Senior Frontend Engineer Interview Deep Dive: Performance, Architecture, and Build Tools"
description: "What senior frontend interviews expect beyond React basics — Core Web Vitals optimization, rendering patterns, build tool internals, accessibility at scale, and advanced Q&A for senior-level loops."
date: "2026-03-20"
category: "Technical Skills"
---

# Senior Frontend Engineer Interview Deep Dive: Performance, Architecture, and Build Tools

Senior frontend interviews test a fundamentally different level than mid-level. Interviewers at companies like Vercel, Stripe, Airbnb, Shopify, and Linear expect you to reason about performance budgets, rendering trade-offs, and large-scale frontend architecture — not just React patterns. This guide covers the level of depth expected.

## Core Web Vitals: The Performance Framework

Google's Core Web Vitals are the industry-standard performance metrics. Senior frontend engineers should know them cold:

**Largest Contentful Paint (LCP):** Time for the largest visible element to render. Target: <2.5s. Common causes of poor LCP: render-blocking resources, slow server response, unoptimized images, client-side rendering without SSR.

**Interaction to Next Paint (INP, replaced FID):** Responsiveness — time from user interaction to visual feedback. Target: <200ms. Common causes: long JavaScript tasks blocking the main thread, synchronous state updates on user events.

**Cumulative Layout Shift (CLS):** Visual stability — unexpected content movement. Target: <0.1. Common causes: images without dimensions, ads that shift content, web fonts causing reflow.

**Optimization strategies interviewers expect:**

For LCP:
- Server-side rendering to send HTML immediately
- `<link rel="preload">` for critical resources
- Image optimization (WebP, AVIF, proper sizing, `loading="lazy"` for below-fold)
- Reduce render-blocking CSS/JS (`defer`, `async`, critical CSS inlining)

For INP:
- Yield to the browser between tasks (`scheduler.yield()`, `setTimeout(0)` for non-critical work)
- Virtualize long lists (react-virtual, TanStack Virtual)
- Move heavy computation off the main thread with Web Workers

For CLS:
- Reserve space for images and ads with aspect-ratio or explicit dimensions
- Font display swap settings (`font-display: optional` or use `font-display: swap` carefully)
- Avoid inserting content above existing content

## Rendering Patterns

Senior frontend engineers are expected to evaluate rendering patterns based on requirements, not just know them:

**CSR (Client-Side Rendering):** React app with no SSR. Full page load in JS bundle. Good for highly interactive, personalized apps (SPAs, dashboards). Bad for SEO and initial LCP.

**SSR (Server-Side Rendering):** HTML rendered on server per request. Good for SEO, fast initial paint. Server cost per request, harder caching.

**SSG (Static Site Generation):** HTML pre-built at deploy time. Excellent caching, minimal server cost. Bad for highly dynamic data or personalized content.

**ISR (Incremental Static Regeneration, Next.js):** Regenerate static pages on a schedule or on-demand. Combines SSG caching benefits with reasonable data freshness.

**Streaming SSR:** Send HTML in chunks as data resolves. React 18 Suspense model. Improves Time to First Byte and enables progressive rendering — faster perceived performance even when total load time is similar.

**Island Architecture (Astro):** HTML is static; interactive "islands" hydrate independently. Good for content-heavy sites with sparse interactivity. Minimal JS shipped.

**Interview framing:** "For a product page that's mostly static but has a dynamic price, I'd use ISR with a 60-second revalidation for the product data and client-side data fetching for the real-time price component. This gives us the caching benefits of SSG while keeping price data fresh."

## Build Tool Internals

Senior engineers are expected to reason about build tools, not just use them:

**Vite:** Uses esbuild (Go-based, 10-100x faster than JS bundlers) for development dependency pre-bundling and transpilation, Rollup for production bundling. Hot Module Replacement (HMR) is fast because it operates at the ES module level rather than rebuilding the full bundle.

**webpack:** Module bundler that builds a dependency graph and produces a bundle. Key concepts: loaders (transform files), plugins (post-processing), code splitting, dynamic imports, tree shaking via ES module static analysis.

**esbuild:** Written in Go, parallelized, no AST transformations on the hot path. Extremely fast but less flexible than webpack for complex transformations.

**Common interview Q: Why is Vite faster than webpack in dev?**
Vite serves ES modules directly to the browser during development — no bundling step. The browser does module resolution. Only the changed module is re-sent on HMR, not a full bundle rebuild. webpack bundles everything before serving, which becomes slow as project size grows.

## State Management Architecture

Senior engineers should evaluate state management needs rather than defaulting to a solution:

**Local state:** `useState` for component-local state. Default choice for UI state that doesn't need to be shared.

**Server state:** TanStack Query (React Query) for data fetched from APIs. Handles caching, background refetching, loading/error states. Much better than manual `useEffect + useState` for server data.

**Global client state:** Zustand for lightweight global state, Jotai for atomic state, Redux Toolkit for complex state with time-travel debugging. Many applications don't need global client state at all if server state is managed well.

**URL state:** Navigation state, filters, and pagination belong in the URL. Bookmarkable, shareable, survives page reload.

**Senior-level insight:** "I'd default to component state + React Query for server data, and avoid global state until there's a clear need. The most common mistake is reaching for a global state manager too early, which creates coupling and makes the component tree harder to reason about."

## Accessibility at Scale

Senior frontend engineers are expected to treat accessibility as a first-class engineering concern:

- **WCAG 2.1 AA** is the standard compliance target (not just guidelines)
- Color contrast ratios (4.5:1 for normal text, 3:1 for large text)
- Keyboard navigation: all interactive elements focusable, logical tab order, visible focus indicators
- Screen reader semantics: correct ARIA roles, labels for interactive elements, live regions for dynamic content
- Testing: axe DevTools, Lighthouse, manual screen reader testing (NVDA/VoiceOver)

**Common interview scenario:** "How would you add an accessible combobox for a search-with-autocomplete?" Expected answer references `role="combobox"`, `aria-expanded`, `aria-controls`, `aria-activedescendant`, keyboard handling (arrow keys for navigation, Enter to select, Escape to close).

## Common Senior Frontend Interview Questions

**Q: Your app's Lighthouse score is 45. Walk me through your debugging approach.**
Check the Lighthouse report for which categories are failing. For performance: TTFB (check server response time), LCP element (optimize that specific asset), render-blocking resources, JavaScript execution time. For accessibility: run axe. For best practices: check console errors, HTTPS, etc. Profile with Chrome DevTools Performance tab for JS bottlenecks.

**Q: How do you handle code splitting in a large React app?**
Route-level splitting via React.lazy + Suspense (automatic with Next.js App Router). Component-level splitting for large, rarely-used components. Dynamic imports for heavy libraries (charting, rich text editors). Bundle analysis tools (webpack-bundle-analyzer, Vite's rollup-plugin-visualizer) to identify what to split.

**Q: When would you NOT use React for a new project?**
Static content sites (Astro or vanilla HTML). Performance-critical interactive visualizations (WebGL, canvas-heavy). Simple forms or landing pages (vanilla JS, Lit). When the team is already expert in Vue or Svelte. React's complexity is worth it for large SPAs with complex state — not for everything.
