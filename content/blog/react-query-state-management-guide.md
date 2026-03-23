---
title: "React Query and Server State Management: A Complete Interview Guide"
description: "Deep dive into TanStack Query (React Query) for interviews — server vs client state, caching, background refetching, optimistic updates, and when to use React Query vs Redux vs Zustand."
date: "2026-03-20"
category: "Technical Skills Guides"
---

# React Query and Server State Management: A Complete Interview Guide

TanStack Query (formerly React Query) has fundamentally changed how React applications handle server data. Senior frontend interviews increasingly test whether candidates understand the architectural distinction between client state and server state — and React Query is the leading tool for the latter. This guide covers what interviews test about server state management.

## The Core Insight: Server State Is Different

The key mental model shift that React Query represents: **server state is not the same as client state**.

**Client state:** What's in your UI — which tab is selected, form input values, modal open/closed. You own this data completely. It lives in memory, never becomes stale, and changes only when the user does something.

**Server state:** Data that lives on a server — user profiles, posts, products, orders. You only have a cached copy. It can become stale (someone else changed it). It can be loading or have errors. It can be shared across multiple components.

Before React Query, teams managed server state in Redux or Zustand — treating it like client state. This created enormous boilerplate: loading flags, error states, cache invalidation logic, background refetch triggers. React Query handles all of this automatically.

## Core Concepts Interviewers Test

**Queries and mutations:**
`useQuery` for reading data; `useMutation` for writing. The separation is fundamental — queries are automatically deduplicated (if 5 components call `useQuery(['user', id])`, React Query makes one request), retried on failure, and cached. Mutations are one-time operations that typically invalidate related queries on success.

**Query keys:**
The cache key system. `['user', userId]` is a key. React Query serializes these and uses them to identify cached data. Keys should fully describe the query — if the same data is fetched with different parameters, use different keys: `['user', userId]` and `['users', { page: 2, filter: 'active' }]`.

**Stale time and cache time:**
- `staleTime`: How long until data is considered stale. During this period, React Query returns cached data without refetching (even on component mount). Default: 0 (always stale).
- `gcTime` (formerly `cacheTime`): How long to keep unused/inactive queries in cache. Default: 5 minutes.

Setting `staleTime: Infinity` for reference data that never changes (country list, product categories) eliminates unnecessary network requests.

**Background refetching:**
By default, React Query refetches stale data when: window regains focus, network reconnects, component mounts. This "stale-while-revalidate" pattern means users see cached data instantly, then fresh data arrives without a loading spinner.

## Optimistic Updates

Optimistic updates are a common senior interview topic:

```tsx
const mutation = useMutation({
  mutationFn: (newTodo) => api.createTodo(newTodo),
  onMutate: async (newTodo) => {
    // Cancel in-flight queries to prevent overwriting optimistic update
    await queryClient.cancelQueries({ queryKey: ['todos'] });
    // Snapshot for rollback
    const previousTodos = queryClient.getQueryData(['todos']);
    // Optimistically update cache
    queryClient.setQueryData(['todos'], (old) => [...old, newTodo]);
    return { previousTodos }; // Context for onError
  },
  onError: (err, newTodo, context) => {
    // Roll back to snapshot on error
    queryClient.setQueryData(['todos'], context.previousTodos);
  },
  onSettled: () => {
    // Refetch regardless of success or error
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
});
```

The pattern: optimistically apply the change, rollback if mutation fails, always invalidate to sync with server.

## When to Use React Query vs Other State Solutions

**Use React Query (server state) when:** Data comes from an API, can become stale, is shared across components, or needs caching/deduplication.

**Use Zustand/Redux (client state) when:** State is purely UI (modal state, form drafts, user preferences, shopping cart before checkout), never needs to sync with a server, or has complex client-side state transitions.

**Don't combine them unnecessarily:** A common antipattern is fetching data with React Query, then storing it in Redux for "global access." React Query's cache is already global — components anywhere in the tree can call `useQuery` with the same key and get the cached value without a new network request.

**The right mental model:** React Query is a cache layer. It lives between your components and the server. It answers: "What's the current state of this server resource from the client's perspective?"

## Prefetching and Infinite Queries

**Prefetching:** Load data before it's needed. On hover over a link, prefetch the destination page's data. `queryClient.prefetchQuery()` loads data into cache so the next page renders instantly.

**Infinite queries:** Pagination with `useInfiniteQuery`. Automatically manages page state, next page cursors, and combining pages into a flat list. Common for feeds and search results:

```tsx
const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = 
  useInfiniteQuery({
    queryKey: ['posts'],
    queryFn: ({ pageParam = 0 }) => api.getPosts({ cursor: pageParam }),
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  });
```

`data.pages` is an array of page results; `data.pages.flat()` gives all items. Hook into scroll events or an intersection observer to trigger `fetchNextPage`.

React Query represents a maturation of the React ecosystem's approach to server data. Senior frontend interviews increasingly assume familiarity with these patterns — knowing when to use server vs client state, how caching works, and how to implement optimistic updates demonstrates production-level frontend architecture experience.
