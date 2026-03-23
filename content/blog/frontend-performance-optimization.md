---
title: "Frontend Performance Optimization: Core Web Vitals, Bundle Analysis, and Runtime Performance"
description: "Practical guide to frontend performance optimization — Core Web Vitals improvement, JavaScript bundle optimization, rendering performance, image optimization, and measuring what matters."
date: "2026-03-20"
category: "Frontend Engineering"
---

# Frontend Performance Optimization: Core Web Vitals, Bundle Analysis, and Runtime Performance

Frontend performance directly impacts business outcomes: a 100ms improvement in load time has been shown to increase conversion rates by 1%, and a 1-second delay reduces page views by 11%. For senior engineers, understanding the full performance optimization toolkit — from bundle analysis to rendering optimization to monitoring — is a core competency.

## Core Web Vitals: The Business Metrics

Google's Core Web Vitals are the three metrics that directly impact search ranking and user experience:

**LCP (Largest Contentful Paint)**: Time for the largest visible element (hero image, headline) to render. Target: < 2.5 seconds. Poor if > 4 seconds.

Common LCP issues and fixes:
- **Slow server response (TTFB)**: Use CDN, optimize server response time, implement HTTP/2
- **Render-blocking resources**: Move non-critical CSS/JS to load asynchronously
- **Hero image not prioritized**: Add `<link rel="preload" as="image" href="hero.webp">` and `fetchpriority="high"` attribute
- **Large image files**: Use WebP format, appropriate dimensions, and responsive images with srcset

**INP (Interaction to Next Paint)**: Time from user interaction to visual response. Target: < 200ms. This replaced FID as of March 2024.

Common INP issues:
- **Long JavaScript tasks**: Tasks > 50ms block the main thread. Use `scheduler.yield()` or `setTimeout(0)` to yield between chunks of work.
- **Heavy event handlers**: Move expensive logic to Web Workers. Debounce/throttle input handlers.
- **Unnecessary re-renders**: Profile with React DevTools; add memoization where needed.

**CLS (Cumulative Layout Shift)**: Visual stability score. Target: < 0.1.

Common CLS issues:
- Images without width/height attributes (browser doesn't reserve space)
- Ads injected above content
- Web fonts causing FOUT (Flash of Unstyled Text) — use `font-display: optional` or preload fonts

## Bundle Analysis and Code Splitting

JavaScript bundle size is the single most impactful optimization for initial load time. Every KB of JavaScript must be parsed, compiled, and executed.

**Analysis tools**:
- `webpack-bundle-analyzer`: Visual treemap of what's in your bundle
- `vite-bundle-visualizer`: Equivalent for Vite projects
- `bundlephobia.com`: Check package sizes before installing

**Target sizes** (gzipped):
- Initial bundle: < 150KB JavaScript
- Individual route chunks: < 50KB
- Third-party dependencies: audit regularly

**Common bundle bloat sources**:
- `moment.js` (67KB) → replace with `date-fns` or `dayjs`
- Full `lodash` import → use `lodash-es` with tree shaking or native equivalents
- Large icon libraries (`@heroicons/react` full import) → cherry-pick specific icons
- Unoptimized images bundled as imports

**Code splitting strategies**:
```javascript
// Route-level splitting (React)
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Settings = React.lazy(() => import('./pages/Settings'));

// Component-level splitting for heavy components
const HeavyEditor = React.lazy(() => import('./components/HeavyEditor'));
// Only loads when rendered
```

**Prefetching**: After the initial page loads, prefetch the likely next routes during idle time:
```html
<link rel="prefetch" href="/dashboard.chunk.js">
```

This downloads the chunk in the background so navigation is instant.

## Rendering Performance

**Long animation frames**: Paint/composite frames should complete in < 16ms (60fps) or < 8ms (120fps). Anything longer causes jank.

**Avoid layout thrashing**: Reading then writing layout properties in a loop causes forced synchronous reflows:
```javascript
// Bad: causes layout thrash
for (const el of elements) {
    const height = el.offsetHeight; // read — forces layout
    el.style.height = height + 'px'; // write — invalidates layout
}

// Good: batch reads and writes
const heights = elements.map(el => el.offsetHeight); // all reads
elements.forEach((el, i) => el.style.height = heights[i] + 'px'); // all writes
```

**CSS animation performance**: Animate only `transform` and `opacity` — these run on the compositor thread and don't block the main thread. Animating `width`, `height`, `margin`, `padding`, or `top/left` triggers layout on every frame.

**Virtualization for long lists**: Rendering 10,000 DOM nodes is expensive. Use `@tanstack/virtual` or `react-window` to render only visible items. Memory usage stays constant and scroll performance is smooth regardless of list length.

## Image Optimization

Images often account for 60-80% of page weight. Modern formats reduce this dramatically.

**Format guide**:
- **WebP**: 25-30% smaller than JPEG/PNG with equivalent quality. Universal browser support.
- **AVIF**: 50% smaller than JPEG. Superior quality at low bitrates. Growing browser support.
- **SVG**: For logos and icons — scales perfectly, tiny file sizes.

**Responsive images**: Serve appropriately sized images for each device:
```html
<img
  src="hero-800.webp"
  srcset="hero-400.webp 400w, hero-800.webp 800w, hero-1600.webp 1600w"
  sizes="(max-width: 600px) 400px, (max-width: 1200px) 800px, 1600px"
  loading="lazy"
  decoding="async"
  width="800" height="450"
  alt="Hero image"
>
```

**Loading strategies**:
- `loading="lazy"`: Defer images below the fold. Reduces initial page weight significantly.
- `loading="eager"` + `fetchpriority="high"`: For the LCP image — load immediately and deprioritize nothing.
- `decoding="async"`: Decode image off main thread.

## Performance Monitoring in Production

**Real User Monitoring (RUM)**: Collect Core Web Vitals from actual users. Use `web-vitals` library:
```javascript
import { getCLS, getINP, getLCP } from 'web-vitals';

getCLS(metric => sendToAnalytics(metric));
getINP(metric => sendToAnalytics(metric));
getLCP(metric => sendToAnalytics(metric));
```

Send to a monitoring service (DataDog, New Relic, or custom endpoint). Segment by device type, geography, and connection speed — performance problems often affect specific segments.

**Performance budget**: Set alerts when metrics exceed targets. Integrate into CI/CD: a PR that increases the bundle by >10KB should fail a check or require approval. Lighthouse CI automates this.

**The optimization cycle**: Measure (RUM or Lighthouse) → identify the highest-impact issue → make a targeted fix → verify with measurement → repeat. Avoid optimizing by intuition — always let data guide which problems to solve.

Performance optimization at senior level is not about individual tricks — it's about building systems that stay fast as the product grows. A performance monitoring pipeline, bundle analysis in CI, and a culture of measuring before and after changes are the lasting contributions.
