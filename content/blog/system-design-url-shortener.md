---
title: "System Design: URL Shortener (Bit.ly/TinyURL)"
description: "Design a URL shortener handling 100B URLs — hash generation strategies, collision handling, custom aliases, redirect performance, analytics pipeline, and database design for this classic system design interview question."
date: "2026-03-20"
category: "System Design"
---

# System Design: URL Shortener (Bit.ly/TinyURL)

URL shortener is one of the most common system design interview questions. It appears deceptively simple but surfaces important tradeoffs in ID generation, database design, caching, and redirect performance. Here's the full breakdown.

## Requirements

Functional: shorten a long URL to a short code (e.g., `bit.ly/abc123`), redirect short code to original URL, optional custom aliases, optional link expiration, click analytics (count, referrer, geography).

Non-functional: 100B total URLs stored, 10K URL creation requests/second, 100K redirect requests/second (10:1 read/write), redirect latency < 50ms (P99), 99.99% availability.

## Short Code Generation

A short code needs to be: compact (6-8 characters), unique, and URL-safe. With 6 characters from [a-zA-Z0-9] (62 chars): 62^6 ≈ 56 billion combinations. Enough for 100B if we reclaim codes for expired URLs, borderline otherwise. 7 characters = 3.5 trillion — use 7 to be safe.

**Approach 1 — Hash-based:** MD5 or SHA-256 the long URL, take the first 7 characters. Deterministic — same URL always gets the same code. Problem: hash collisions require checking the database, and multiple users shortening the same URL get the same code (usually desirable).

**Approach 2 — Counter-based:** Maintain a global auto-incrementing counter. Convert counter to base62. Problems: single point of failure for the counter, predictable/enumerable codes (sequential: abc123, abc124...).

**Approach 3 — Random generation:** Generate random 7-character string, check if it exists, retry on collision. Simple but requires a DB roundtrip for every creation. Collision probability is low (70B / 3.5T ≈ 2%) but retry logic adds complexity.

**Recommendation:** Counter-based with multiple counter servers using pre-allocated ranges. Assign each creation server a range of 1M IDs from a central "ticket server" (or ZooKeeper). Server uses its range sequentially, requests a new range when exhausted. Distributed, fast, no DB roundtrip for each creation.

## Database Design

Two entities: URL mappings and click analytics.

```sql
CREATE TABLE url_mappings (
    short_code VARCHAR(10) PRIMARY KEY,
    long_url TEXT NOT NULL,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    user_id BIGINT,
    custom_alias BOOLEAN DEFAULT FALSE
);

CREATE TABLE clicks (
    id BIGINT PRIMARY KEY,
    short_code VARCHAR(10),
    clicked_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    referrer TEXT
);
```

For 100B URL mappings, a single PostgreSQL table won't work. Shard by `short_code` (consistent hashing or range sharding). Each shard handles ~10B rows.

Click analytics is write-heavy and rarely queried in real-time. Use a separate database (Cassandra or Redshift) and write clicks asynchronously via a message queue.

## Redirect Performance

The redirect is the most latency-sensitive operation. A user clicks a link — they expect instant redirect.

**Cache the hot path:** 80% of clicks go to 20% of URLs (Zipf's law). Cache URL mappings in Redis with a 24-hour TTL. Cache hit rate will be ~90%+ for high-traffic URLs.

**Read flow:**
1. Request hits load balancer → creation/redirect server
2. Server checks Redis cache for short code
3. Cache hit: return 301/302 redirect immediately (sub-millisecond)
4. Cache miss: query database, populate cache, return redirect

**301 vs 302:** Use 302 (temporary redirect) for analytics. Browsers cache 301 permanently — future clicks go directly to the destination, bypassing your servers and breaking click counting. Use 301 only if you want CDN/browser caching and don't need analytics.

## Analytics Pipeline

Synchronous click recording would add latency to the redirect. Use an async pipeline:

1. Redirect server emits click event to Kafka
2. Click consumer service reads from Kafka, enriches with geographic data (IP → country lookup), writes to analytics DB (Cassandra or Redshift)
3. Dashboard queries analytics DB for per-URL statistics

This decouples click recording from redirect latency. If Kafka is temporarily slow, redirects are unaffected.

## Custom Aliases

Allow users to specify `bit.ly/mycompany-promo`. Constraints: only alphanumeric + hyphens, 3-50 characters, case-insensitive, no collision with auto-generated codes.

Implementation: custom aliases go into the same `url_mappings` table. Validate uniqueness before insertion. Mark with `custom_alias = TRUE` for reporting. Enforce uniqueness at DB level with the primary key constraint.

Rate limit custom alias creation to prevent enumeration attacks (someone claiming all common words).

## Handling Scale

For 100K redirects/second, a single server tier can't keep up. Scale horizontally:

**Redirect servers:** Stateless — any server can handle any request. Scale to 50+ servers behind a load balancer.

**Redis cluster:** Partition URL cache across a Redis cluster. Consistent hashing ensures short codes map to the same shard (cache hit rates stay high after shard expansion).

**Database shards:** Redirect servers route queries to the correct shard based on short code prefix.

## Edge Cases

**Expired links:** Background worker periodically scans `url_mappings` for `expires_at < NOW()` and deletes. Or lazy deletion: on redirect, check expiration and return 410 Gone if expired.

**Malicious URLs:** Before storing, check URL against Google Safe Browsing API. Async check to not slow down creation.

**URL normalization:** `http://example.com` and `http://example.com/` are the same URL. Normalize before checking for duplicates.

**Rate limiting:** Limit URL creation per API key to prevent abuse. Sliding window rate limiter in Redis.


## Related Articles

- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Distributed Cache](/blog/system-design-distributed-cache)
- [System Design: Rate Limiter (Advanced)](/blog/system-design-rate-limiter-advanced)
- [System Design Interview Framework](/blog/interview-system-design-framework)
- [Cracking the System Design Interview](/blog/cracking-the-system-design-interview)
