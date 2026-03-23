---
title: "Prisma ORM Advanced Patterns"
description: "Advanced Prisma ORM patterns for production—schema design, relations, migrations, query optimization, middleware, transactions, raw queries, and the patterns that make Prisma databases maintainable at scale."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Prisma ORM Advanced Patterns

Prisma has become the dominant ORM for TypeScript/Node.js applications. Its combination of type-safe queries, schema-first migrations, and excellent DX makes database work significantly less error-prone. This guide covers the advanced patterns that distinguish production Prisma usage from tutorial-level applications.

## Schema Design Patterns

```prisma
// schema.prisma
generator client {
  provider = "prisma-client-js"
  previewFeatures = ["fullTextSearch", "fullTextIndex"]
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
  directUrl = env("DIRECT_URL")  // For connection poolers like PgBouncer
}

model User {
  id        String   @id @default(cuid())
  email     String   @unique
  username  String   @unique
  password  String
  role      UserRole @default(USER)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  profile   UserProfile?
  posts     Post[]
  comments  Comment[]
  sessions  Session[]

  @@index([email])
  @@index([createdAt])
  @@map("users")  // Explicit table name
}

model Post {
  id          String    @id @default(cuid())
  title       String
  content     String    @db.Text
  published   Boolean   @default(false)
  publishedAt DateTime?
  authorId    String

  author    User      @relation(fields: [authorId], references: [id], onDelete: Cascade)
  tags      PostTag[]
  comments  Comment[]

  @@index([authorId, published])
  @@index([publishedAt])
  @@fulltext([title, content])
  @@map("posts")
}

// Many-to-many through explicit join table
model PostTag {
  postId    String
  tagId     String
  createdAt DateTime @default(now())

  post Post @relation(fields: [postId], references: [id], onDelete: Cascade)
  tag  Tag  @relation(fields: [tagId], references: [id], onDelete: Cascade)

  @@id([postId, tagId])
  @@map("post_tags")
}

enum UserRole {
  USER
  ADMIN
  MODERATOR
}
```

## Query Optimization

**Selecting only needed fields** reduces data transfer:

```typescript
// BAD: fetches everything including password
const user = await prisma.user.findUnique({ where: { id } });

// GOOD: select only needed fields
const user = await prisma.user.findUnique({
  where: { id },
  select: {
    id: true,
    username: true,
    email: true,
    profile: {
      select: { bio: true, avatarUrl: true },
    },
  },
});
```

**Avoiding N+1 with include**:

```typescript
// One query with JOIN instead of N+1
const posts = await prisma.post.findMany({
  where: { published: true },
  include: {
    author: { select: { username: true } },
    tags: { include: { tag: true } },
    _count: { select: { comments: true } },
  },
  orderBy: { publishedAt: 'desc' },
  take: 20,
});
```

**Cursor-based pagination** for large datasets:

```typescript
async function getPaginatedPosts(cursor?: string, limit = 20) {
  const posts = await prisma.post.findMany({
    where: { published: true },
    take: limit + 1,
    cursor: cursor ? { id: cursor } : undefined,
    skip: cursor ? 1 : 0,  // Skip the cursor item itself
    orderBy: { publishedAt: 'desc' },
    select: { id: true, title: true, publishedAt: true },
  });

  const hasNextPage = posts.length > limit;
  return {
    posts: posts.slice(0, limit),
    nextCursor: hasNextPage ? posts[limit - 1].id : null,
  };
}
```

## Transactions

```typescript
// Interactive transaction — use for complex business logic
async function transferCredits(fromUserId: string, toUserId: string, amount: number) {
  return prisma.$transaction(async (tx) => {
    const from = await tx.user.findUnique({
      where: { id: fromUserId },
      select: { id: true, credits: true },
    });

    if (!from || from.credits < amount) {
      throw new Error('Insufficient credits');
    }

    await tx.user.update({
      where: { id: fromUserId },
      data: { credits: { decrement: amount } },
    });

    await tx.user.update({
      where: { id: toUserId },
      data: { credits: { increment: amount } },
    });

    return tx.creditTransfer.create({
      data: { fromUserId, toUserId, amount },
    });
  });
}

// Sequential transaction — for batching independent writes (more performant)
const [user, post] = await prisma.$transaction([
  prisma.user.update({ where: { id }, data: { updatedAt: new Date() } }),
  prisma.post.create({ data: { ...postData, authorId: id } }),
]);
```

## Prisma Middleware

Middleware intercepts Prisma client calls—useful for logging, soft deletes, and audit trails:

```typescript
// Soft delete middleware
prisma.$use(async (params, next) => {
  // Redirect 'delete' operations to 'update' with deleted flag
  if (params.model === 'Post' && params.action === 'delete') {
    params.action = 'update';
    params.args.data = { deletedAt: new Date() };
  }

  // Exclude soft-deleted records from all find operations
  if (params.model === 'Post' && params.action === 'findMany') {
    params.args.where = {
      ...params.args.where,
      deletedAt: null,
    };
  }

  return next(params);
});

// Query logging middleware
prisma.$use(async (params, next) => {
  const start = Date.now();
  const result = await next(params);
  const duration = Date.now() - start;

  if (duration > 100) {
    logger.warn('Slow query', {
      model: params.model,
      action: params.action,
      durationMs: duration,
    });
  }

  return result;
});
```

## Raw Queries for Complex Cases

When Prisma's query builder isn't expressive enough:

```typescript
// Raw query with type safety via Prisma.sql
const results = await prisma.$queryRaw<{ id: string; rank: number }[]>`
  SELECT id, ts_rank(search_vector, to_tsquery('english', ${query})) as rank
  FROM posts
  WHERE search_vector @@ to_tsquery('english', ${query})
  ORDER BY rank DESC
  LIMIT ${limit}
`;

// $executeRaw for write operations
const deletedCount = await prisma.$executeRaw`
  DELETE FROM sessions
  WHERE expires_at < NOW() - INTERVAL '7 days'
`;
```

## Migration Workflow

```bash
# Development: generate and apply migration
npx prisma migrate dev --name add_user_profile

# Production: apply pending migrations
npx prisma migrate deploy

# Check migration status
npx prisma migrate status

# Baseline an existing database (for teams adding Prisma to existing projects)
npx prisma migrate resolve --applied "20240101_init"
```

Production migration safety: always run `prisma migrate deploy` (not `dev`) in production. `migrate dev` resets the database on migration conflicts—not acceptable for production data.

## Interview Tips

Prisma interview questions for senior roles:

1. **Cursor vs offset pagination** — why cursor-based is necessary for large tables (offset `SKIP N` scans N rows), when offset is acceptable
2. **N+1 detection** — Prisma logging in development (`log: ['query']`), why `include` beats multiple queries
3. **Transaction types** — interactive ($transaction with callback) vs sequential (array) and when each is appropriate
4. **Schema migrations in production** — `migrate deploy` vs `migrate dev`, why you never reset production, zero-downtime migration patterns (add column → deploy → backfill → make required)
5. **Connection pooling** — PgBouncer with `directUrl` for migrations, why serverless environments need external pooling

The core Prisma insight: Prisma trades query flexibility for safety and DX. For 95% of queries, the Prisma client API is sufficient and far safer than raw SQL. For the 5% requiring complex SQL (window functions, CTEs, full-text search), `$queryRaw` provides an escape hatch. The migration workflow is where Prisma provides the most value at scale—schema changes become explicit, reviewable, and reversible.
