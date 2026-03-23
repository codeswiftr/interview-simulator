---
title: "Advanced API Design Patterns: Versioning, Pagination, and Rate Limiting Best Practices"
description: "A deep-dive into production-ready API design patterns every senior engineer should know, covering versioning strategies, cursor-based pagination, and rate limiting architectures."
date: "2026-03-20"
category: "System Design"
---

# Advanced API Design Patterns: Versioning, Pagination, and Rate Limiting Best Practices

System design interviews at senior levels increasingly focus on API design — not just "what endpoints do you need" but "how do you evolve them safely, handle scale, and protect your infrastructure." This guide covers three critical pillars: versioning, pagination, and rate limiting.

## API Versioning Strategies

### URI Path Versioning

The most common approach: embed the version in the URL path.

```
GET /api/v1/users
GET /api/v2/users
```

**Pros:** Explicit, easy to cache, simple to route at the load balancer level.

**Cons:** Breaks REST's principle that a resource should have one canonical URI. You often end up duplicating large swaths of code across versions.

**When to use:** Public APIs consumed by third parties where discoverability matters and you expect long-lived versions.

### Header Versioning

Version negotiated via request headers:

```
GET /api/users
Accept: application/vnd.myapp.v2+json
```

**Pros:** Keeps URLs clean, aligns with HTTP content negotiation semantics.

**Cons:** Less visible in browser address bars, harder to test without tooling, caching becomes complex (Vary header required).

**When to use:** Internal service-to-service APIs or when you have strong API gateway control.

### Query Parameter Versioning

```
GET /api/users?version=2
```

Rarely the right choice for production systems — it pollutes your query string and makes routing awkward — but useful for quick experimentation.

### Sunset and Deprecation Headers

Regardless of strategy, use standard headers to signal deprecation:

```
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Deprecation: true
Link: <https://developer.example.com/migration>; rel="deprecation"
```

This gives clients machine-readable signals to trigger alerts before versions go offline.

## Pagination Patterns

### Offset Pagination

```
GET /api/posts?limit=20&offset=40
```

Simple to implement and supports random access ("jump to page 5"), but performance degrades at large offsets — the database must count and skip rows every time.

**The deep pagination problem:** At offset 10,000 with limit 20, the DB scans 10,020 rows to return 20. On write-heavy tables, you also get duplicate or missing results when records are inserted or deleted between page fetches.

### Cursor-Based Pagination

Instead of an offset, use an opaque cursor pointing to a position in the dataset:

```
GET /api/posts?limit=20&after=eyJpZCI6MTAwfQ==
```

The cursor encodes the last-seen record's stable identifier (often a timestamp + ID combo). The query becomes:

```sql
WHERE (created_at, id) < (:cursor_ts, :cursor_id)
ORDER BY created_at DESC, id DESC
LIMIT 20
```

**Pros:** Consistent results regardless of concurrent writes, O(1) complexity with proper indexing, no duplicate/missing records.

**Cons:** No random access (can't jump to page 7), cursors expire if underlying data changes drastically.

**Use for:** Social feeds, activity streams, any real-time or high-write-volume dataset.

### Keyset Pagination

A subset of cursor-based pagination where the cursor is a compound key. Particularly powerful with composite indexes:

```sql
-- Index: (status, created_at DESC, id DESC)
WHERE status = 'published'
  AND (created_at, id) < ($last_ts, $last_id)
```

This is what high-scale systems like Slack and Stripe use internally.

## Rate Limiting Architectures

### Token Bucket

Each client starts with a "bucket" of tokens. Each request consumes a token; tokens refill at a fixed rate. Allows bursting up to bucket capacity.

**Implementation:** Redis with atomic Lua scripts or the `INCR` + TTL pattern.

```
tokens = GET user:{id}:tokens
if tokens > 0:
    DECR user:{id}:tokens
    serve request
else:
    return 429 Too Many Requests
```

### Sliding Window Log

Maintain a log of request timestamps per client. On each request, count entries within the window:

```
ZADD user:{id}:requests {timestamp} {request_id}
ZREMRANGEBYSCORE user:{id}:requests 0 {window_start}
count = ZCARD user:{id}:requests
```

Precise but memory-intensive at scale — each request is stored.

### Fixed Window Counter

Simplest approach: count requests in discrete time windows (per minute, per hour). Reset counter at window boundary.

**The boundary burst problem:** A client can make 100 requests at 11:59:59 and another 100 at 12:00:01, effectively getting 200 requests in two seconds.

### Sliding Window Counter

Approximates the sliding log using two fixed window counters:

```
rate = previous_window_count * ((window_size - elapsed) / window_size) + current_window_count
```

Good accuracy at a fraction of the memory cost of the log approach. This is what Cloudflare uses.

### Response Headers

Always communicate rate limit state to clients:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1711929600
Retry-After: 42
```

## Interview Takeaways

In a system design interview, demonstrate that you understand the tradeoffs, not just the patterns. When asked "how would you paginate a feed?" — don't just say "use cursors." Explain why offset breaks at scale and why cursors need stable sort keys. When asked about rate limiting, address both local (in-process) and distributed (Redis) approaches and the tradeoffs in consistency versus latency.

The strongest signal you can send in an API design question is that you've thought about **what happens when things go wrong**: clients that ignore rate limits, cursors that reference deleted records, and API versions that need emergency retirement. That's the difference between a junior answer and a senior one.

Practice designing these systems end-to-end with Interview Simulator's system design mode — you'll get structured feedback on exactly these patterns.
