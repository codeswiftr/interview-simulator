---
title: "Drizzle ORM Migration Guide"
description: "Drizzle ORM for TypeScript applications—schema definition, migrations with drizzle-kit, query builder patterns, relations, transactions, and why Drizzle is gaining adoption as the lightweight Prisma alternative."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Drizzle ORM Migration Guide

Drizzle ORM has emerged as the lightweight, SQL-first alternative to Prisma in the TypeScript ecosystem. Where Prisma abstracts away SQL behind a schema language and generates a heavy runtime client, Drizzle keeps you close to SQL with TypeScript-first schema definitions and zero-overhead query building. For performance-sensitive applications and edge runtimes, Drizzle's minimal footprint is a significant advantage.

## Drizzle vs Prisma: The Key Differences

| Aspect | Drizzle | Prisma |
|--------|---------|--------|
| Schema definition | TypeScript | Prisma Schema Language |
| Bundle size | ~35KB | ~5MB+ |
| Query builder | SQL-like chainable API | Object-based |
| Runtime overhead | Near-zero | Heavier (separate binary) |
| Edge runtime | Native support | Limited (Accelerate add-on) |
| Migrations | SQL files (drizzle-kit) | Migration history |
| Learning curve | Lower (familiar SQL) | Higher (Prisma abstractions) |

## Schema Definition

Drizzle schemas are TypeScript—no separate schema language:

```typescript
// schema/users.ts
import { pgTable, text, timestamp, boolean, varchar, index } from 'drizzle-orm/pg-core';
import { createId } from '@paralleldrive/cuid2';

export const users = pgTable('users', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  email: varchar('email', { length: 255 }).notNull().unique(),
  username: varchar('username', { length: 50 }).notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  role: text('role', { enum: ['user', 'admin', 'moderator'] }).notNull().default('user'),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().$onUpdate(() => new Date()),
}, (table) => ({
  emailIdx: index('users_email_idx').on(table.email),
  createdAtIdx: index('users_created_at_idx').on(table.createdAt),
}));

// schema/posts.ts
export const posts = pgTable('posts', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  title: varchar('title', { length: 255 }).notNull(),
  content: text('content').notNull(),
  published: boolean('published').notNull().default(false),
  publishedAt: timestamp('published_at'),
  authorId: text('author_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  createdAt: timestamp('created_at').notNull().defaultNow(),
}, (table) => ({
  authorPublishedIdx: index('posts_author_published_idx').on(table.authorId, table.published),
}));

// Define relations
export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));

export const postsRelations = relations(posts, ({ one }) => ({
  author: one(users, { fields: [posts.authorId], references: [users.id] }),
}));
```

## Database Connection

```typescript
// db/index.ts
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from '../schema';

const connectionString = process.env.DATABASE_URL!;

// For regular server usage
const client = postgres(connectionString, { max: 20 });
export const db = drizzle(client, { schema });

// For edge/serverless — use HTTP-based driver
import { drizzle as drizzleHttp } from 'drizzle-orm/neon-http';
import { neon } from '@neondatabase/serverless';

const sql = neon(connectionString);
export const db = drizzleHttp(sql, { schema });
```

## Query Patterns

Drizzle's query API is intentionally SQL-like:

```typescript
import { eq, and, desc, ilike, sql, count } from 'drizzle-orm';

// Simple select
const user = await db.select().from(users).where(eq(users.id, userId)).limit(1);

// Select specific columns
const usernames = await db
  .select({ id: users.id, username: users.username })
  .from(users)
  .orderBy(users.username);

// Join
const postsWithAuthors = await db
  .select({
    postId: posts.id,
    title: posts.title,
    authorUsername: users.username,
  })
  .from(posts)
  .leftJoin(users, eq(posts.authorId, users.id))
  .where(eq(posts.published, true))
  .orderBy(desc(posts.publishedAt))
  .limit(20);

// Aggregation
const stats = await db
  .select({
    userId: posts.authorId,
    postCount: count(posts.id),
  })
  .from(posts)
  .where(eq(posts.published, true))
  .groupBy(posts.authorId);

// Insert and return
const [newUser] = await db.insert(users).values({
  email,
  username,
  passwordHash,
}).returning();

// Update
await db.update(users)
  .set({ updatedAt: new Date() })
  .where(eq(users.id, userId));
```

## Relational Queries

For nested data fetching (replaces JOINs with multiple queries):

```typescript
// Uses the relations defined in schema
const usersWithPosts = await db.query.users.findMany({
  with: {
    posts: {
      where: eq(posts.published, true),
      orderBy: desc(posts.createdAt),
      limit: 5,
    },
  },
  where: eq(users.role, 'user'),
  limit: 20,
});
// Returns: { id, email, ..., posts: [{ id, title, ... }] }[]
```

## Transactions

```typescript
// Transaction with rollback on error
const result = await db.transaction(async (tx) => {
  const [user] = await tx.select()
    .from(users)
    .where(eq(users.id, fromUserId))
    .for('update');  // SELECT FOR UPDATE — row-level lock

  if (user.credits < amount) {
    tx.rollback();  // Explicit rollback
  }

  await tx.update(users)
    .set({ credits: sql`${users.credits} - ${amount}` })
    .where(eq(users.id, fromUserId));

  await tx.update(users)
    .set({ credits: sql`${users.credits} + ${amount}` })
    .where(eq(users.id, toUserId));

  return { success: true };
});
```

## Migrations with drizzle-kit

```bash
# Generate migration from schema changes
npx drizzle-kit generate --name add_user_profile

# Apply migrations
npx drizzle-kit migrate

# Push schema directly (development only — no migration files)
npx drizzle-kit push

# View schema
npx drizzle-kit studio
```

```typescript
// drizzle.config.ts
import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  schema: './src/schema/*.ts',
  out: './drizzle',
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
  verbose: true,
  strict: true,  // Requires explicit confirmation for destructive changes
});
```

Generated migrations are plain SQL files—reviewable, version-controlled, and understandable without ORM knowledge.

## Interview Tips

Drizzle ORM interview questions:

1. **Drizzle vs Prisma** — schema language vs TypeScript-first; bundle size for edge; SQL proximity
2. **`select` vs `query` API** — `select` for SQL-like queries, `query` for relational (nested) data with defined relations
3. **Edge runtime support** — why Drizzle works in Cloudflare Workers/Vercel Edge (no native binaries, tree-shakeable)
4. **Migration safety** — `drizzle-kit push` vs `generate` + `migrate`; why production always uses `migrate`
5. **Raw SQL escape hatch** — `sql` template literal for expressions Drizzle can't express natively

The core Drizzle insight: Drizzle is "ORM that isn't." It generates type-safe SQL without hiding SQL—you still need to understand joins, indexes, and query plans. This is a feature: Drizzle users write better queries because the abstraction leaks intentionally. The tradeoff is that Drizzle's API is more verbose for complex relational queries than Prisma's `include` pattern.
