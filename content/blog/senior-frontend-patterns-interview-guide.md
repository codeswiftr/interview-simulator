---
title: "Senior Frontend Engineer Interview Guide: Architecture, Performance, and Accessibility"
description: "Interview preparation for senior frontend roles — component architecture, rendering strategies, accessibility requirements, frontend testing strategies, and state management at scale."
date: "2026-03-20"
category: "Frontend"
---

# Senior Frontend Engineer Interview Guide: Architecture, Performance, and Accessibility

Senior frontend engineer interviews go well beyond JavaScript fundamentals and React component patterns. They probe architectural judgment, performance reasoning, accessibility expertise, and the ability to make principled tradeoffs at scale. This guide covers the technical depth expected at senior levels across system design, performance, testing, and accessibility.

## What Senior Frontend Interviews Actually Test

The gap between mid and senior frontend interview expectations is significant. Mid-level interviews verify you can build components, handle state, and write clean code. Senior interviews test:

- **Architectural decisions:** When to use CSR vs SSR vs SSG vs ISR, and why
- **Scale thinking:** How does your approach change with 100 components vs 10,000?
- **Performance reasoning:** Not just "use a memo" but when memoization helps, when it hurts, and how to measure
- **Accessibility by default:** Not an afterthought — built into your architectural choices
- **Testing philosophy:** What to test, at what level, and how to balance coverage with maintenance cost
- **Framework agnosticism:** Understanding underlying browser and JavaScript mechanics, not just framework APIs

## Component Architecture

Senior frontend engineers are expected to think about component design as an architecture problem, not just a code organization preference.

**Key concepts to master:**

**Compound components:** A pattern where a parent component shares state with children through context, allowing flexible composition. React Select, Radix UI, and Headless UI use this pattern extensively.

```tsx
// The pattern allows flexible composition
<Select>
  <Select.Trigger />
  <Select.Content>
    <Select.Item value="a">Option A</Select.Item>
  </Select.Content>
</Select>
```

**Render props vs hooks:** Understand when each is appropriate. Hooks have replaced render props for most state-sharing cases, but render props still win for cases requiring components to control rendering structure.

**Component boundaries:** Where to split components isn't obvious. Key signals: independent re-render concerns (performance), independent reuse needs (design system), and independent ownership (team boundaries).

**Controlled vs uncontrolled:** Know when to build controlled components (parent owns state, full control) vs uncontrolled (internal state, simpler API). Form libraries like react-hook-form lean uncontrolled for performance reasons.

## Rendering Strategies

One of the most common senior frontend interview topics is the rendering model decision:

| Strategy | When to Use | Tradeoffs |
|----------|------------|-----------|
| **CSR (Client-Side Rendering)** | Authenticated apps, dashboards, real-time data | Poor SEO, slow initial paint, great interactivity |
| **SSR (Server-Side Rendering)** | Public content needing SEO, personalized pages | Server cost, higher TTFB, session complexity |
| **SSG (Static Site Generation)** | Marketing sites, documentation, blogs | Fast, cacheable, requires rebuild for updates |
| **ISR (Incremental Static Regeneration)** | High-traffic content with semi-frequent updates | Stale content window, complex cache invalidation |
| **Streaming SSR** | Large pages where parts are ready before others | React 18+, requires streaming-compatible infra |

Know the tradeoffs well enough to recommend a strategy for a given product requirement. "It depends" is the right instinct — but you need to know what it depends on.

## Performance Engineering

Performance questions at the senior level require you to go beyond "avoid unnecessary renders":

**Core Web Vitals as a framework:**
- **LCP (Largest Contentful Paint):** <2.5s. Optimize with preloading critical resources, efficient image delivery (next/image, srcset, WebP), and reducing render-blocking resources.
- **INP (Interaction to Next Paint):** <200ms. Minimize long tasks, use web workers for CPU-intensive work, defer non-critical JavaScript.
- **CLS (Cumulative Layout Shift):** <0.1. Reserve space for images and ads, avoid inserting content above existing content.

**JavaScript bundle strategy:**
- Code splitting at the route level (minimum) and component level for large features
- Tree shaking requires ES modules and careful library selection
- Third-party scripts are often the largest LCP and INP contributors — load them async, defer, or use facade patterns

**React-specific performance:**
- `useMemo` and `useCallback` add overhead when dependencies change frequently — profile before applying
- `React.memo` prevents re-renders when props are stable — profile to verify actual benefit
- Virtualization (react-window, TanStack Virtual) for lists with hundreds or thousands of items
- Concurrent features (Suspense, transitions) for deferring non-urgent updates

**The profiling-first principle:** Interviewers at senior level expect you to measure before optimizing. Know how to use React DevTools Profiler, Chrome Performance tab, and Lighthouse.

## Accessibility as Architecture

Accessibility at the senior level isn't a checklist — it's baked into design decisions. Key areas:

**ARIA correctly applied:**
- `role`, `aria-label`, `aria-labelledby`, `aria-describedby` — know when each is appropriate
- ARIA should augment HTML semantics, not replace them. `<button>` > `<div role="button">`
- Dynamic content changes: `aria-live`, `aria-atomic`, `aria-relevant` for regions that update

**Keyboard navigation:**
- Focus management in modals (focus trap on open, restore on close)
- Skip links for main content
- Custom components (comboboxes, date pickers) must implement full keyboard patterns from WAI-ARIA Authoring Practices

**Color and contrast:**
- WCAG 2.1 AA: 4.5:1 contrast ratio for text, 3:1 for large text and UI components
- Don't communicate with color alone — pair with icons, patterns, or text labels

**Testing accessibility:**
- Automated: axe-core, jest-axe catch 30–40% of issues
- Manual: keyboard-only navigation test, screen reader test (VoiceOver/NVDA)
- The 60% of accessibility issues that automation misses require human testing

Interviewers increasingly ask candidates to design a component accessibly from scratch — practice building a modal, dropdown, or tab interface while narrating your accessibility decisions.

## Frontend Testing Strategy

Senior engineers need a testing philosophy, not just the ability to write tests.

**The testing pyramid for frontend:**
- **Unit tests:** Pure functions, custom hooks, utility logic — fast, isolated, high value
- **Component tests (React Testing Library):** Test component behavior from the user's perspective, not implementation details
- **Integration tests:** Test user flows across multiple components or pages
- **E2E tests (Playwright, Cypress):** Critical paths only — slow, but catch integration failures that lower levels miss

**Key principles:**
- Test behavior, not implementation: prefer `getByRole` and `getByText` over `getByTestId`
- Avoid testing React internals (state values, component instances)
- Mock network calls at the network layer (MSW), not at the module level
- Accessibility and functionality overlap — testing with accessible queries reinforces accessible markup

## State Management at Scale

The state management landscape has clarified. The right answer depends on the problem:

- **Server state** (data from APIs): React Query / TanStack Query. Handles caching, revalidation, background updates, and optimistic updates. Eliminates most `useEffect` data-fetching code.
- **Client/UI state** (modals, selections, form state): Local component state + context. Global stores for UI state are often over-engineered.
- **Complex global state** (multi-step forms, undo/redo, real-time collaborative): Zustand or Jotai for simplicity, Redux Toolkit when you need devtools, time-travel debugging, or the ecosystem.

The common mistake is using a global store for everything. Senior candidates should be able to articulate when they'd reach for each tool and why.

## Approaching the Frontend System Design Interview

When given a frontend system design prompt ("Design Google Docs" or "Design a social media feed"), work through:

1. **Clarify requirements** — real-time collaboration? Offline support? Mobile?
2. **Data modeling** — what entities, what relationships, where does state live?
3. **Component architecture** — high-level component tree, key interfaces
4. **Data fetching strategy** — REST vs GraphQL, caching, optimistic updates
5. **Performance considerations** — virtualization, code splitting, image strategy
6. **Accessibility** — at least flag the key concerns
7. **Testing approach** — what you'd test and at what level

Frontend system design is less standardized than backend system design — interviewers want to see structured thinking and your ability to connect product requirements to architectural decisions.
