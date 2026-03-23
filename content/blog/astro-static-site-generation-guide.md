---
title: "Astro Static Site Generation Guide"
description: "How Astro works for static site generation and content-driven websites—island architecture, partial hydration, content collections, and when to choose Astro over Next.js or Gatsby."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Astro Static Site Generation Guide

Astro has emerged as the leading framework for content-driven websites in 2026. Its "zero JavaScript by default" philosophy and island architecture make it ideal for blogs, documentation sites, and marketing pages where performance is paramount. Understanding Astro is increasingly expected for frontend engineers working on content sites.

## The Core Philosophy

Astro's key insight: most content websites don't need JavaScript for most of their content. A blog post doesn't need React to render. A documentation page doesn't need Vue. By defaulting to zero JavaScript and "hydrating" only the components that need interactivity, Astro ships dramatically less JavaScript than traditional SPA frameworks.

## Astro Components

```astro
---
// Component Script (runs at build time, never in browser)
const title = "My Blog Post";
const posts = await fetch('/api/posts').then(r => r.json());
---

<!-- Component Template -->
<html>
<head>
    <title>{title}</title>
</head>
<body>
    <h1>{title}</h1>
    <ul>
        {posts.map(post => (
            <li><a href={`/posts/${post.slug}`}>{post.title}</a></li>
        ))}
    </ul>
</body>
</html>
```

The frontmatter (between `---`) runs on the server/at build time. It's regular JavaScript/TypeScript with access to Node.js APIs, environment variables, and the filesystem.

## Content Collections

Astro's content collections provide type-safe access to markdown/MDX content:

```typescript
// src/content/config.ts
import { z, defineCollection } from 'astro:content';

const blogCollection = defineCollection({
    type: 'content',
    schema: z.object({
        title: z.string(),
        date: z.date(),
        tags: z.array(z.string()).default([]),
        draft: z.boolean().default(false),
    }),
});

export const collections = { blog: blogCollection };
```

```astro
---
// src/pages/blog/[slug].astro
import { getCollection, getEntry } from 'astro:content';

const { slug } = Astro.params;
const post = await getEntry('blog', slug);
const { Content } = await post.render();
---

<h1>{post.data.title}</h1>
<Content />  <!-- Renders the markdown content -->
```

TypeScript validates your frontmatter against the schema at build time.

## Island Architecture

The "island" concept: interactive UI components are "islands" in a sea of static HTML. Only islands ship JavaScript.

```astro
---
import StaticHeader from './StaticHeader.astro'; // No JS
import InteractiveCounter from './Counter.tsx';   // Needs JS
import StaticFooter from './StaticFooter.astro'; // No JS
---

<StaticHeader />

<!-- This island hydrates only when visible -->
<InteractiveCounter client:visible />

<!-- This island hydrates immediately -->
<SearchBar client:load />

<!-- This island hydrates on idle -->
<Analytics client:idle />

<StaticFooter />
```

The `client:*` directives control when hydration happens:
- `client:load` — hydrate immediately
- `client:visible` — hydrate when the element enters viewport
- `client:idle` — hydrate when the browser is idle
- `client:media="(max-width: 768px)"` — hydrate on media query match

## Framework Integrations

Astro supports React, Vue, Svelte, Solid, and others simultaneously:

```astro
---
import ReactCounter from './Counter.react.tsx';
import VueModal from './Modal.vue';
import SvelteChart from './Chart.svelte';
---

<!-- All three frameworks on the same page -->
<ReactCounter client:load />
<VueModal client:visible />
<SvelteChart client:idle />
```

This is unique to Astro — no other framework lets you mix UI libraries this way.

## SSG vs SSR vs Hybrid

Astro supports all rendering modes:

```javascript
// astro.config.mjs
export default defineConfig({
    output: 'static',   // Pure static site (default)
    // output: 'server',   // SSR with Node.js adapter
    // output: 'hybrid',   // Per-page SSR/static decision
});

// Per-page SSR override in hybrid mode
// src/pages/dashboard.astro
---
export const prerender = false; // This page uses SSR
---
```

## View Transitions

Astro has built-in View Transitions API support for SPA-like transitions:

```astro
---
import { ViewTransitions } from 'astro:transitions';
---
<html>
<head>
    <ViewTransitions />  <!-- Enables page transitions -->
</head>
<body>
    <!-- Page content -->
</body>
</html>
```

With View Transitions enabled, clicking links triggers smooth animated transitions without a full page reload — while still having actual page navigations (not SPA routing).

## Performance Comparison

Typical Core Web Vitals comparison:

| Framework | LCP | TBT | CLS |
|-----------|-----|-----|-----|
| Astro | ~0.4s | ~0ms | 0 |
| Next.js (SSG) | ~0.8s | ~50ms | 0.01 |
| Gatsby | ~0.7s | ~40ms | 0 |
| CRA (SPA) | ~1.2s | ~200ms | 0.05 |

Astro's zero-JS default produces dramatically better performance metrics.

## When to Choose Astro

**Right for Astro**:
- Blogs, documentation sites
- Marketing/landing pages
- Portfolios
- E-commerce product pages (with island for cart)

**Wrong for Astro**:
- Highly interactive applications (dashboards, tools, editors)
- Real-time features (chat, collaboration)
- Apps with complex client-side state

## Interview Tips

Astro questions in senior frontend interviews:

1. Island architecture — explain the concept and why it improves performance
2. `client:*` directives — when to use each
3. Content collections — type-safe content management
4. When to choose Astro vs Next.js — content vs application distinction
5. View Transitions API for SPA-like navigation without JavaScript overhead

The core insight for interviews: Astro makes the correct default assumption that most content doesn't need JavaScript, and adds JavaScript only where explicitly needed. This inversion of Next.js/Gatsby's assumption is what drives Astro's performance advantage.
