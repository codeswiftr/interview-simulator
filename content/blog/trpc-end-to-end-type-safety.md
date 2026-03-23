---
title: "tRPC End-to-End Type Safety Guide"
description: "tRPC for full-stack TypeScript applications—routers, procedures, middleware, subscriptions, React Query integration, and the patterns that make tRPC the most productive API layer for TypeScript monorepos."
date: "2026-03-21"
category: "Language Deep Dives"
---

# tRPC End-to-End Type Safety Guide

tRPC enables end-to-end type safety between your TypeScript backend and frontend without code generation or a schema language. Call server functions from the client with full autocomplete, type inference, and compile-time error checking. For TypeScript monorepos building full-stack applications, tRPC eliminates an entire category of API contract bugs.

## Core Concept

tRPC works by sharing TypeScript types directly from server to client:

```typescript
// server/router.ts — defines the API
const appRouter = router({
  user: router({
    getById: publicProcedure
      .input(z.object({ id: z.string() }))
      .query(async ({ input }) => {
        return db.users.findById(input.id);
      }),
    create: protectedProcedure
      .input(z.object({ username: z.string(), email: z.string().email() }))
      .mutation(async ({ input, ctx }) => {
        return db.users.create({ ...input, createdBy: ctx.userId });
      }),
  }),
});

export type AppRouter = typeof appRouter;  // Export the TYPE, not the implementation

// client/api.ts — uses the type
import { createTRPCReact } from '@trpc/react-query';
import type { AppRouter } from '../server/router';

export const trpc = createTRPCReact<AppRouter>();

// Component — full type inference, no code generation
function UserProfile({ userId }: { userId: string }) {
  const { data, isLoading } = trpc.user.getById.useQuery({ id: userId });
  // data is typed as: { id: string; username: string; email: string; ... }

  const createUser = trpc.user.create.useMutation({
    onSuccess: () => utils.user.getById.invalidate(),
  });
}
```

## Router Structure

Organize procedures into nested routers that mirror your domain:

```typescript
// server/routers/users.ts
import { router, publicProcedure, protectedProcedure } from '../trpc';
import { z } from 'zod';
import { TRPCError } from '@trpc/server';

const userSchema = z.object({
  id: z.string().cuid(),
  username: z.string(),
  email: z.string().email(),
  createdAt: z.date(),
});

export const usersRouter = router({
  getById: publicProcedure
    .input(z.object({ id: z.string() }))
    .output(userSchema.nullable())  // Validated response type
    .query(async ({ input }) => {
      const user = await db.users.findById(input.id);
      return user ?? null;
    }),

  list: protectedProcedure
    .input(z.object({
      limit: z.number().min(1).max(100).default(20),
      cursor: z.string().nullish(),
    }))
    .query(async ({ input }) => {
      const users = await db.users.findMany({
        take: input.limit + 1,
        cursor: input.cursor ? { id: input.cursor } : undefined,
      });

      const hasMore = users.length > input.limit;
      return {
        users: users.slice(0, input.limit),
        nextCursor: hasMore ? users[input.limit - 1].id : null,
      };
    }),

  update: protectedProcedure
    .input(z.object({
      id: z.string(),
      data: z.object({ username: z.string().optional() }),
    }))
    .mutation(async ({ input, ctx }) => {
      const user = await db.users.findById(input.id);
      if (!user) throw new TRPCError({ code: 'NOT_FOUND', message: 'User not found' });
      if (user.id !== ctx.userId) throw new TRPCError({ code: 'FORBIDDEN' });
      return db.users.update(input.id, input.data);
    }),
});
```

## Middleware and Context

tRPC middleware provides authentication, authorization, and request context:

```typescript
// server/trpc.ts
import { initTRPC, TRPCError } from '@trpc/server';
import type { CreateNextContextOptions } from '@trpc/server/adapters/next';
import { verifyJWT } from './auth';

// Context created per request
export async function createContext({ req }: CreateNextContextOptions) {
  const token = req.headers.authorization?.slice(7);
  const user = token ? await verifyJWT(token) : null;
  return { req, user, db };
}

type Context = Awaited<ReturnType<typeof createContext>>;

const t = initTRPC.context<Context>().create({
  errorFormatter({ shape, error }) {
    return {
      ...shape,
      data: {
        ...shape.data,
        zodError: error.cause instanceof ZodError ? error.cause.flatten() : null,
      },
    };
  },
});

export const router = t.router;
export const publicProcedure = t.procedure;

// Protected middleware
const isAuthenticated = t.middleware(({ ctx, next }) => {
  if (!ctx.user) {
    throw new TRPCError({ code: 'UNAUTHORIZED', message: 'Must be logged in' });
  }
  return next({ ctx: { ...ctx, userId: ctx.user.id, user: ctx.user } });
});

export const protectedProcedure = t.procedure.use(isAuthenticated);

// Admin middleware chains on top of auth
const isAdmin = isAuthenticated.unstable_pipe(({ ctx, next }) => {
  if (!ctx.user.roles.includes('admin')) {
    throw new TRPCError({ code: 'FORBIDDEN', message: 'Admin required' });
  }
  return next({ ctx });
});

export const adminProcedure = t.procedure.use(isAdmin);
```

## Subscriptions with WebSockets

tRPC supports real-time subscriptions via WebSockets:

```typescript
// server/routers/notifications.ts
import { observable } from '@trpc/server/observable';
import { EventEmitter } from 'events';

const eventEmitter = new EventEmitter();

export const notificationsRouter = router({
  onNewNotification: protectedProcedure
    .subscription(({ ctx }) => {
      return observable<Notification>((observer) => {
        const handler = (notification: Notification) => {
          if (notification.userId === ctx.userId) {
            observer.next(notification);
          }
        };

        eventEmitter.on('notification', handler);
        return () => eventEmitter.off('notification', handler);
      });
    }),
});

// Client usage
function NotificationBell() {
  trpc.notifications.onNewNotification.useSubscription(undefined, {
    onData: (notification) => {
      toast.info(notification.message);
    },
  });
}
```

## React Query Integration

tRPC integrates with React Query for caching and mutation management:

```typescript
// Optimistic updates
function TodoItem({ todo }: { todo: Todo }) {
  const utils = trpc.useUtils();

  const toggleTodo = trpc.todos.toggle.useMutation({
    // Optimistic update
    onMutate: async ({ id }) => {
      await utils.todos.list.cancel();
      const prev = utils.todos.list.getData();
      utils.todos.list.setData(undefined, (old) =>
        old?.map(t => t.id === id ? { ...t, done: !t.done } : t)
      );
      return { prev };
    },
    onError: (_, __, ctx) => {
      // Rollback on error
      utils.todos.list.setData(undefined, ctx?.prev);
    },
    onSettled: () => {
      utils.todos.list.invalidate();
    },
  });
}

// Prefetching on server (Next.js App Router)
export async function generateStaticParams() {
  const helpers = createServerSideHelpers({
    router: appRouter,
    ctx: await createContext(),
  });

  const users = await helpers.users.list.fetch({ limit: 100 });
  return users.users.map(u => ({ userId: u.id }));
}
```

## Error Handling

```typescript
// Throw TRPCError on server
throw new TRPCError({
  code: 'BAD_REQUEST',
  message: 'Invalid input',
  cause: originalError,
});

// Handle on client
const createUser = trpc.users.create.useMutation({
  onError: (error) => {
    if (error.data?.code === 'CONFLICT') {
      setFieldError('email', 'Email already in use');
    } else if (error.data?.zodError) {
      // Structured Zod validation errors
      Object.entries(error.data.zodError.fieldErrors).forEach(([field, errors]) => {
        setFieldError(field, errors?.[0]);
      });
    } else {
      toast.error('Something went wrong');
    }
  },
});
```

## Interview Tips

tRPC interview questions:

1. **Type sharing mechanism** — how TypeScript module types traverse the monorepo boundary; why no code generation is needed
2. **vs REST/GraphQL** — tRPC is TypeScript-only; REST is language-agnostic; GraphQL has a schema for multi-language clients
3. **Input validation** — Zod schemas serve dual purpose: runtime validation AND TypeScript type inference
4. **Procedure types** — query (GET semantics, cacheable), mutation (POST semantics, non-cacheable), subscription (WebSocket)
5. **When NOT to use tRPC** — public APIs consumed by non-TypeScript clients, microservices with independent deployment, when you need OpenAPI spec for third parties

The core tRPC insight: it's not a replacement for REST or GraphQL in general. It's the right choice when your client and server are both TypeScript and deployed together. The DX wins (autocomplete, no code gen, type-safe errors) are significant for full-stack TypeScript teams—but disappear the moment you need to expose the API to external consumers.
