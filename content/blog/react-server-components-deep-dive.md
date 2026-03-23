---
title: "React Server Components: A Deep Dive"
description: "How React Server Components work, when to use them, how they interact with Client Components, and the patterns for building hybrid server/client React applications in 2026."
date: "2026-03-21"
category: "Language Deep Dives"
---

# React Server Components: A Deep Dive

React Server Components (RSC) represent the most significant architectural change to React since hooks. They allow components to run exclusively on the server, accessing databases and file systems directly without client-side JavaScript. Understanding RSC is essential for senior React engineers in 2026.

## The Mental Model

Traditional React: all components run on the client (or are SSR'd and then hydrated). Every component ships JavaScript to the browser.

RSC: components can be designated as "server only" — they run exclusively during rendering on the server, have zero client-side JavaScript, and can access server resources directly.

```tsx
// UserProfile.tsx — a Server Component
// This runs ONLY on the server

import { db } from '@/lib/db'; // Direct DB access — no API call needed

export default async function UserProfile({ userId }: { userId: string }) {
    // Direct database query — no fetch(), no useEffect()
    const user = await db.user.findUnique({ where: { id: userId } });

    if (!user) return <div>User not found</div>;

    return (
        <div>
            <h1>{user.name}</h1>
            <p>{user.email}</p>
            {/* No user.password here — it never left the server */}
        </div>
    );
}
```

## Server vs Client Components

**Server Components (default in Next.js App Router)**:
- Run on the server
- Can use `async/await` directly
- Can access server resources (DB, filesystem, environment variables)
- Cannot use browser APIs (window, document)
- Cannot use hooks (useState, useEffect)
- No JavaScript shipped to client

**Client Components** (marked with `'use client'`):
- Run on both server (for SSR) and client
- Can use hooks
- Can use browser APIs
- Ship JavaScript to client
- Cannot directly access server resources

```tsx
'use client'

import { useState } from 'react';

export function LikeButton({ postId }: { postId: string }) {
    const [liked, setLiked] = useState(false);

    return (
        <button onClick={() => setLiked(!liked)}>
            {liked ? '❤️' : '🤍'}
        </button>
    );
}
```

## Composition: The Key Pattern

Server Components can contain Client Components, but not vice versa (without serialization):

```tsx
// page.tsx — Server Component
import { db } from '@/lib/db';
import { LikeButton } from './LikeButton'; // Client Component

export default async function BlogPost({ params }: { params: { id: string } }) {
    const post = await db.post.findUnique({ where: { id: params.id } });

    return (
        <article>
            <h1>{post.title}</h1>
            <p>{post.content}</p>
            {/* Client Component receives serializable data from Server Component */}
            <LikeButton postId={post.id} />
        </article>
    );
}
```

The boundary between server and client is where `'use client'` appears. Data crossing this boundary must be serializable (JSON-safe).

## Server Actions

Server Actions let Client Components call server-side code without an explicit API route:

```tsx
'use server'

export async function createPost(formData: FormData) {
    const title = formData.get('title') as string;
    const content = formData.get('content') as string;

    await db.post.create({ data: { title, content } });
    revalidatePath('/posts');
}
```

```tsx
'use client'

import { createPost } from './actions';

export function CreatePostForm() {
    return (
        <form action={createPost}>
            <input name="title" />
            <textarea name="content" />
            <button type="submit">Create Post</button>
        </form>
    );
}
```

Server Actions eliminate the need for API routes for many common patterns.

## Data Fetching Patterns

**Before RSC** (Client-side fetching):
```tsx
function UserList() {
    const [users, setUsers] = useState([]);
    useEffect(() => {
        fetch('/api/users').then(r => r.json()).then(setUsers);
    }, []);
    return <div>{users.map(u => <div key={u.id}>{u.name}</div>)}</div>;
}
```

**With RSC** (Server-side direct access):
```tsx
async function UserList() {
    const users = await db.user.findMany(); // Direct DB query
    return <div>{users.map(u => <div key={u.id}>{u.name}</div>)}</div>;
}
```

RSC eliminates loading states, error handling for fetches, and the API route layer for internal data access.

## Streaming with Suspense

RSC integrates with Suspense for progressive rendering:

```tsx
import { Suspense } from 'react';
import { SlowComponent } from './SlowComponent';

export default function Page() {
    return (
        <div>
            <h1>Page Title</h1>
            <Suspense fallback={<div>Loading...</div>}>
                {/* SlowComponent can be an async Server Component */}
                <SlowComponent />
            </Suspense>
        </div>
    );
}
```

The page title renders immediately. SlowComponent streams in when its async data is ready.

## Interview Tips

RSC is a common interview topic in 2026 for React engineers:

1. Explain the server/client boundary and why it matters
2. Describe when to use `'use client'` (interactivity, browser APIs, hooks)
3. Server Actions pattern for forms and mutations
4. Streaming with Suspense for progressive loading
5. Limitations: no browser state in server components

The key insight: RSC is not about replacing client components — it's about moving the data-fetching and rendering work to the server where it's cheaper, faster, and more secure, while keeping interactivity client-side.
