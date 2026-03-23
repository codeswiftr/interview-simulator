---
title: "Next.js App Router Migration Guide"
description: "How to migrate from Next.js Pages Router to App Router—routing changes, data fetching migration, middleware updates, and common pitfalls when upgrading to the App Router architecture."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Next.js App Router Migration Guide

The Next.js App Router (introduced in Next.js 13, stable in 14) represents a fundamental architectural shift from the Pages Router. Most production Next.js applications built before 2023 use the Pages Router. This guide covers the migration path, key differences, and pitfalls.

## Key Architectural Differences

| Feature | Pages Router | App Router |
|---------|-------------|------------|
| Data fetching | getServerSideProps, getStaticProps | async Server Components |
| Routing | pages/ directory | app/ directory |
| Layouts | Custom _app.js | Nested layout.tsx files |
| Loading states | Manual | loading.tsx files |
| Error handling | Custom _error.js | error.tsx files |
| Components | All client by default | Server by default |

## Routing Migration

**Pages Router**:
```
pages/
  index.tsx          → /
  users/[id].tsx     → /users/:id
  api/users.ts       → /api/users
```

**App Router**:
```
app/
  page.tsx           → /
  users/[id]/
    page.tsx         → /users/:id
  api/
    users/
      route.ts       → /api/users (API Route Handler)
```

## Data Fetching Migration

**Before (Pages Router)**:
```tsx
// pages/users/[id].tsx
export async function getServerSideProps({ params }) {
    const user = await fetchUser(params.id);
    return { props: { user } };
}

export default function UserPage({ user }) {
    return <div>{user.name}</div>;
}
```

**After (App Router)**:
```tsx
// app/users/[id]/page.tsx
async function UserPage({ params }: { params: { id: string } }) {
    // Direct async/await — no getServerSideProps wrapper
    const user = await fetchUser(params.id);
    return <div>{user.name}</div>;
}

export default UserPage;
```

Static generation:
```tsx
// Before: getStaticPaths + getStaticProps
// After: generateStaticParams
export async function generateStaticParams() {
    const users = await fetchAllUsers();
    return users.map(u => ({ id: u.id }));
}
```

## Layouts

One of the App Router's biggest wins: nested layouts that persist across navigations without re-rendering.

```tsx
// app/layout.tsx — root layout
export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
            <body>
                <Navbar />  {/* Persists across all pages */}
                {children}
                <Footer />
            </body>
        </html>
    );
}

// app/dashboard/layout.tsx — nested layout
export default function DashboardLayout({ children }) {
    return (
        <div>
            <Sidebar />  {/* Persists within dashboard, doesn't re-render */}
            <main>{children}</main>
        </div>
    );
}
```

## Loading and Error UI

```tsx
// app/users/[id]/loading.tsx — automatic Suspense fallback
export default function Loading() {
    return <Skeleton />;
}

// app/users/[id]/error.tsx — automatic error boundary
'use client'
export default function Error({ error, reset }) {
    return (
        <div>
            <p>Something went wrong: {error.message}</p>
            <button onClick={reset}>Retry</button>
        </div>
    );
}
```

## API Routes Migration

**Before**:
```typescript
// pages/api/users.ts
export default function handler(req, res) {
    if (req.method === 'GET') {
        res.json({ users: [] });
    }
}
```

**After**:
```typescript
// app/api/users/route.ts
import { NextResponse } from 'next/server';

export async function GET() {
    return NextResponse.json({ users: [] });
}

export async function POST(request: Request) {
    const body = await request.json();
    return NextResponse.json({ created: true }, { status: 201 });
}
```

## Common Migration Pitfalls

**1. Forgetting 'use client' for interactive components**:
Every component using hooks, event listeners, or browser APIs needs `'use client'`. This is the most common migration error.

**2. Context providers must be Client Components**:
```tsx
'use client'
// Context providers need browser state
export function ThemeProvider({ children }) {
    const [theme, setTheme] = useState('light');
    return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>;
}
```

**3. Cookies and headers in Server Components**:
```tsx
import { cookies, headers } from 'next/headers';

async function AuthenticatedPage() {
    const cookieStore = cookies();
    const token = cookieStore.get('auth-token');
    // Use token for authentication
}
```

**4. Parallel routes and intercepting routes**: New App Router features with no Pages Router equivalent. Worth learning separately.

## Migration Strategy

Recommended approach:
1. Upgrade Next.js to 14+
2. Create `app/` directory alongside existing `pages/`
3. Migrate routes one at a time (both can coexist)
4. Start with leaf pages (no shared layouts)
5. Migrate layouts last (most complex)
6. Remove `pages/` when fully migrated

The `pages/` and `app/` directories can coexist indefinitely — incremental migration is the official recommended approach.

## Interview Tips

App Router knowledge is tested at most frontend/fullstack interviews in 2026:

1. Server Components vs Client Components — the most common question
2. Data fetching migration (async components vs getServerSideProps)
3. Nested layouts and when they re-render
4. Route Handlers vs API Routes
5. `generateStaticParams` for static generation

The most important concept: the mental model shift from "pages with attached data fetching" to "async components that fetch their own data." Once that clicks, the App Router's design becomes intuitive.
