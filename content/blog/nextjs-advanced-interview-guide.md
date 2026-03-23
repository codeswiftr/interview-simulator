---
title: "Next.js Advanced Interview Guide: App Router, RSC, and Production Patterns"
description: "Master Next.js advanced interview topics including App Router architecture, React Server Components, streaming, caching strategies, and production deployment patterns for 2026."
date: "2026-03-20"
category: "Technical Skills"
---

# Next.js Advanced Interview Guide: App Router, RSC, and Production Patterns

Next.js has evolved dramatically. The App Router introduced in Next.js 13 and stabilized in 14-15 represents a fundamental architectural shift, not just a routing API change. Advanced interviews now test deep understanding of React Server Components, the multi-layer caching model, and the performance implications of rendering strategy decisions. This guide covers what senior Next.js interviews actually test in 2026.

## App Router vs Pages Router: The Conceptual Shift

The Pages Router model is familiar: every file in `/pages` is a route, `getServerSideProps` or `getStaticProps` runs on the server, the component renders on the client. The mental model is simple but limiting — the server and client are separate concerns, data fetching is co-located at the page level, and the client receives a fully-rendered HTML shell followed by a JavaScript bundle.

The App Router model inverts this. By default, every component in the `/app` directory is a **React Server Component** (RSC). Server components never send their JavaScript to the client — they render to a serialized payload on the server and the client receives the output, not the component code. Client components are opt-in via the `"use client"` directive.

This means the mental model shifts from "page-level data fetching" to "component-level data fetching where the component itself doesn't ship to the client." A deeply nested component can fetch its own data directly, and that fetch happens entirely on the server with no client-side waterfall.

## React Server Components in Depth

Interviewers probe RSC understanding extensively because it's where most misconceptions live.

**What RSCs can and cannot do:** Server components can use `async/await` directly, access server-only resources (databases, file systems, environment variables), and import server-only modules. They cannot use React hooks, event handlers, or browser APIs. Attempting to use `useState` in a server component is a compile-time error.

**The composition model:** You can pass server components as children or props to client components — the server component renders to a serialized representation that the client component receives. You cannot import a client component into a server component and then re-import the server component's internals on the client. The boundary is one-directional: server components can render client components, but client components cannot render server components directly (they can accept them as children).

**Data fetching patterns:** In the App Router, `fetch()` is augmented with Next.js-specific caching options. Fetching in server components avoids API roundtrips — the component fetches directly from the data source. The recommended pattern is fetching as close to where data is used as possible, enabling parallel fetching across the component tree via `Promise.all()`.

## Streaming and Suspense

Streaming is a first-class feature in the App Router. Instead of waiting for the entire page to render before sending any HTML, Next.js can stream HTML chunks as they become ready, using React's Suspense as the boundary mechanism.

Practical application: wrap a slow data-fetching component in `<Suspense fallback={<Skeleton />}>`. Next.js streams the fallback immediately, then streams the resolved component when the fetch completes. This dramatically improves Time to First Byte (TTFB) perception for pages with heterogeneous fetch latencies.

**Loading states:** The `loading.tsx` convention creates an automatic Suspense boundary for a route segment. The loading UI displays immediately while the segment's data fetches, then replaces it when ready.

**Error boundaries:** `error.tsx` creates a client-side error boundary that catches rendering errors within a segment. Because it must be a client component, it can use `useEffect` to report errors to monitoring services.

## The Caching Model

The Next.js App Router caching is the most complex conceptual area and the most frequently misunderstood in interviews.

**Full Route Cache (server-side):** Static routes are rendered at build time and cached on the server. Dynamic routes bypass this. `export const dynamic = "force-static"` opts a dynamic route into static generation.

**Data Cache:** `fetch()` responses are cached by Next.js independent of HTTP cache headers. The default is `cache: "force-cache"` (cache indefinitely). `cache: "no-store"` disables caching. `next: { revalidate: 3600 }` sets a revalidation interval. This cache persists across deployments until explicitly invalidated.

**Router Cache (client-side):** The client maintains an in-memory cache of rendered server component payloads for navigated routes. Navigating back to a cached route is instant. This cache is session-scoped and doesn't persist across page reloads. Interviewers frequently ask why a navigation shows stale data — the answer is often the router cache, invalidated by calling `router.refresh()`.

**On-demand revalidation:** `revalidatePath()` and `revalidateTag()` allow server actions or route handlers to invalidate cached data on demand. This enables patterns like invalidating a product page's cache when inventory updates, without a full redeployment.

## Sample Interview Questions

**Q: A page shows stale data after a mutation despite the server returning fresh data. What are the likely causes?**
A: In priority order: the router cache is serving a cached payload from a previous navigation — fix with `router.refresh()` or ensure the mutation calls `revalidatePath()`. The data cache may be caching the upstream fetch — check the `cache` option on the relevant `fetch()` call. The full route cache may have a stale static render — check if the route is statically generated and if `revalidate` is set appropriately.

**Q: When would you choose Pages Router over App Router for a new project?**
A: App Router is the default choice for new projects. Pages Router is appropriate when the team has existing deep expertise and migration cost is prohibitive, when using libraries with fundamental RSC incompatibility (some animation libraries, older state management patterns), or when the team needs time to develop RSC mental models before adopting them in production. The performance and DX advantages of App Router are significant enough that defaulting to it for new projects is correct.

**Q: How do you share state between a server component and a client component?**
A: Pass data as props from the server component to the client component — this is the idiomatic pattern. For cross-cutting state that many client components need, use React Context wrapped in a client provider component that sits high in the tree. The provider itself is a client component, but server components can still be rendered as children of the provider (they pass through the provider's context rendering without becoming client components themselves).

## When to Use Next.js vs Alternatives

Next.js is the right choice when: you need a mix of static, server-rendered, and client-rendered content; SEO is important; you're building a full-stack application with API routes; or you want a batteries-included framework with strong Vercel deployment integration.

Consider alternatives when: you're building a pure SPA with no SEO requirements (Vite + React); you need maximum control over the server layer (Remix, or a separate API server); you're working in a non-React ecosystem; or you need edge-first rendering at extreme scale (Cloudflare Workers with Hono).

Senior engineers who can articulate these tradeoffs — rather than reflexively recommending Next.js — consistently perform better in final-round interviews.
