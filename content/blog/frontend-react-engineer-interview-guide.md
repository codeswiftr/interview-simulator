# Frontend / React Engineer Interview Guide 2024: What's Actually Tested

Frontend engineering interviews have evolved. Companies no longer just ask you to center a div — they test system design, TypeScript depth, performance optimization, and the internals of React you rarely think about day-to-day. Here's an honest breakdown of what to expect and how to prepare.

## What Separates Frontend From General SWE Interviews

Frontend interviews at top companies cover ground that general SWE interviews don't:

- **Browser fundamentals**: The event loop, rendering pipeline, critical rendering path
- **React internals**: Reconciliation, fiber architecture, hooks behavior under concurrent features
- **TypeScript**: Generics, conditional types, discriminated unions — not just "add types"
- **Performance**: Core Web Vitals, lazy loading, bundle optimization, memoization trade-offs
- **Accessibility**: ARIA, keyboard navigation, screen reader compatibility (asked more than you'd think)

**Typical big tech frontend interview format:**
- 1-2 coding rounds (DSA + DOM/HTML/CSS/JS problems)
- 1 React component design round
- 1 frontend system design round
- 1 behavioral round

Some companies (Airbnb, Shopify, Stripe) weight the UI component design round heavily. Others (Google, Meta) still prioritize DSA.

## JavaScript/TypeScript: The Foundation Layer

### Event Loop and Async (Always Asked)

Interviewers love event loop questions because they reveal whether you actually understand how JavaScript executes or just use it.

**Classic question:**
```javascript
console.log('1');
setTimeout(() => console.log('2'), 0);
Promise.resolve().then(() => console.log('3'));
console.log('4');
// Output: 1, 4, 3, 2
```

Know the difference between macrotasks (setTimeout, setInterval, I/O) and microtasks (Promise.then, queueMicrotask, MutationObserver). Microtasks drain completely before the next macrotask runs.

**`this` binding rules:**
Arrow functions inherit `this` from the enclosing scope. Regular functions get `this` from the call site. This distinction matters in class components and event handlers.

### Closure and Memory

```javascript
// What logs here?
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
// Logs: 3, 3, 3 (not 0, 1, 2)
// Fix: use let, or wrap in IIFE
```

Closures come up in debounce/throttle implementations, which are common coding questions:

```javascript
function debounce(fn, delay) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}
```

### TypeScript Depth

Entry-level: interfaces vs. types, basic generics.
Senior: conditional types, mapped types, template literal types, `infer`.

**Discriminated unions** (come up constantly):
```typescript
type ApiResult<T> =
  | { status: 'success'; data: T }
  | { status: 'error'; error: string }
  | { status: 'loading' };

// TypeScript narrows correctly in each branch
function handleResult<T>(result: ApiResult<T>) {
  if (result.status === 'success') {
    console.log(result.data); // T — TypeScript knows this exists
  }
}
```

**Utility types to know cold:** `Partial`, `Required`, `Pick`, `Omit`, `Record`, `ReturnType`, `Parameters`, `Awaited`.

## React: What Interviewers Actually Probe

### Reconciliation and the Virtual DOM

You don't need to explain fiber internals in detail, but you need to know:
- React diffing uses the **key** prop to identify list items — wrong keys cause unnecessary re-mounts
- Reconciliation is a tree diffing problem with O(n) heuristics (same-type, same-position assumptions)
- `key` changes force a full remount — useful for resetting state, but expensive if overused

### Hooks Internals

**`useEffect` gotchas** (asked constantly):
```javascript
useEffect(() => {
  // Runs after every render — missing deps
  fetchData(userId);
}, []); // Stale closure — userId from first render only
```

Know what causes stale closures, how to use the functional updater form of setState, and why `useCallback`/`useMemo` don't always improve performance (they have overhead too).

**The rules of hooks — and why:**
Hooks must be called unconditionally and at the top level because React relies on call order (an internal array) to associate hook state with component instances. This is why `if (condition) { useState(...) }` breaks.

### `useState` vs `useReducer`

Use `useReducer` when:
- Next state depends on previous state in complex ways
- Multiple sub-values change together
- You want to pass dispatch (stable reference) instead of callbacks

**When to avoid re-renders:**
- `React.memo` — shallow comparison of props
- `useMemo` — memoize expensive computed values
- `useCallback` — stable function reference for child component props
- Context splitting — separate `StateContext` from `DispatchContext` to prevent consumers from re-rendering on dispatch-only changes

### Concurrent Features (Senior Level)

`useTransition` marks state updates as non-urgent, keeping the UI responsive during heavy renders. `useDeferredValue` defers a value so expensive child trees don't block interaction.

Interviewers at Meta/Netflix ask about Suspense for data fetching and streaming SSR. You don't need to implement them, but understand the model: components suspend by throwing Promises, Suspense boundaries catch them and show fallbacks.

## Frontend System Design: The High-Signal Round

Frontend system design is underestimated. Companies like Airbnb, Stripe, and Figma weight this round heavily for senior roles.

### The Framework

**1. Clarify requirements**
- How many users? What devices/browsers? Offline support?
- Real-time or polling? What's the latency requirement?

**2. Component architecture**
- Break the UI into a component tree
- Identify what state goes where (local vs. context vs. external store)
- Talk about controlled vs. uncontrolled components

**3. Data flow and API design**
- REST vs. GraphQL? Pagination strategy (cursor vs. offset)?
- Optimistic updates — when to use them, how to handle rollbacks
- Caching strategy: React Query/SWR patterns, cache invalidation

**4. Performance**
- Code splitting (route-level, component-level with `React.lazy`)
- Image optimization (lazy loading, WebP, responsive images)
- Bundle analysis — what to defer, what to preload

**5. Accessibility and internationalization**
- Keyboard navigation, ARIA roles for dynamic content
- RTL support, number/date formatting

**Example question: "Design a real-time collaborative text editor (like Google Docs)"**

Approach:
- Operational Transforms or CRDT for conflict resolution
- WebSocket for real-time sync; fallback to SSE for read-heavy clients
- Presence indicators via separate lightweight channel
- Undo history: command pattern, bounded stack
- Offline: buffer local ops, sync on reconnect with OT merge

## Performance Optimization: Core Web Vitals

Interviewers at companies with public-facing products ask about Lighthouse scores and CWV.

**LCP (Largest Contentful Paint):** Optimize your hero image/text. Preload critical resources. Use `fetchpriority="high"` on above-the-fold images.

**CLS (Cumulative Layout Shift):** Always specify image dimensions. Avoid injecting content above existing content. Use CSS `content-visibility` for off-screen content.

**INP (Interaction to Next Paint, replaced FID):** Avoid long tasks on the main thread. Break up work with `scheduler.yield()` or `setTimeout` chunking. Move heavy computation to Web Workers.

**Bundle optimization:**
- Tree shaking (import only what you use, avoid side-effect imports)
- Dynamic imports for route-based code splitting
- Analyze your bundle: `source-map-explorer` or `rollup-plugin-visualizer`

## Browser APIs Worth Knowing

- **IntersectionObserver** — lazy loading, infinite scroll (better than scroll event listeners)
- **ResizeObserver** — responsive component behavior without media queries
- **MutationObserver** — watching DOM changes (use sparingly)
- **Web Workers** — offload CPU-intensive work from the main thread
- **Service Workers** — caching strategies for PWAs (cache-first, network-first, stale-while-revalidate)
- **requestAnimationFrame** — smooth animations tied to display refresh rate

## CSS and Layout (Still Asked)

Senior engineers sometimes underestimate CSS questions. Companies like Stripe and Linear care about CSS architecture.

**Specificity:** inline > ID > class > element. `!important` overrides all (and is almost never the right answer in production).

**Flexbox vs. Grid:**
- Flexbox: one-dimensional layout (row OR column), content-driven sizing
- Grid: two-dimensional (rows AND columns), layout-driven sizing
- Practical rule: Flexbox for component internals, Grid for page layout

**CSS-in-JS trade-offs:** Runtime CSS-in-JS (Emotion, styled-components) adds JS payload and runtime cost. Zero-runtime alternatives (Linaria, vanilla-extract) extract CSS at build time. CSS Modules are the minimal footprint option.

## The Preparation Plan

**Week 1-2: JavaScript/TypeScript depth**
- Review event loop, closures, prototype chain, async/await internals
- Practice TypeScript: write a type-safe API client, use discriminated unions
- Implement debounce, throttle, deep clone, EventEmitter from scratch

**Week 3-4: React**
- Reimplement a mini React (useState, useEffect) — best way to understand hooks
- Practice building real components: autocomplete, infinite scroll, drag-and-drop
- Learn React Query/SWR patterns for data fetching

**Week 5-6: System design + performance**
- Design 3 systems: autocomplete, collaborative editor, social media feed
- Run Lighthouse on a real site, fix the top 3 issues
- Practice explaining your design decisions out loud

## What Separates Strong Candidates

The engineers who pass senior frontend loops share one trait: they think in trade-offs. They don't just implement the thing — they explain why this approach over another, what breaks under scale, and what they'd monitor in production.

When you reach for `useMemo`, explain what problem you're solving. When you choose WebSockets over polling, articulate the operational cost. When you structure your component tree, justify where state lives.

Interviewers are evaluating whether they'd want to pair with you on a complex UI problem at 11pm before a launch. Make it obvious you've thought about how your code behaves in the real world.
