---
title: "System Design: URL Shortener (TinyURL/Bitly Architecture)"
description: "Classic system design interview problem — encoding strategies, database design, caching, redirect performance, analytics, and scaling a URL shortener to billions of URLs."
date: "2026-03-20"
category: "System Design"
---

# System Design: URL Shortener (TinyURL/Bitly Architecture)

The URL shortener is one of the most common system design interview questions, and for good reason: it appears simple but reveals how you think about encoding, caching, database design, and scale. A confident walkthrough of this problem signals solid foundational knowledge to your interviewer.

## Clarifying Requirements First

Before diving into architecture, nail down scope. Ask: How many URLs per day? Read-heavy or write-heavy? Do we need custom aliases? Analytics? Link expiration?

A typical back-of-envelope estimate: 100 million new URLs per day means roughly 1,150 writes per second. If reads are 100x writes (URL shorteners are extremely read-heavy), that's ~115,000 redirects per second. This shapes your entire design.

The core functional requirements are: generate a short code for a given long URL, redirect short URL → long URL (fast), and optionally support custom aliases, expiration, and analytics.

## Encoding Strategy: Base62 vs Hashing

This is where most candidates get asked follow-up questions, so know both approaches cold.

**Base62 encoding** uses characters `[a-zA-Z0-9]` — 62 possibilities per character. A 7-character code gives 62^7 ≈ 3.5 trillion combinations, more than enough for any real system. The typical approach: use an auto-incrementing ID from the database, then convert that integer to Base62. This guarantees no collisions and is deterministic.

**Hash-based approaches** (MD5, SHA-256, then truncate) are simpler to implement but introduce collision risk. If two URLs hash to the same 7-character prefix, you need a collision resolution strategy — usually checking the database and appending a counter. This adds latency and complexity. Prefer Base62 with a counter unless asked specifically about hash-based designs.

For collision handling in hash-based designs, the standard pattern is: generate hash → check DB → if collision exists, append `+1` to the original URL and re-hash. Loop until unique. In practice, collisions are rare but the logic must be correct.

## Database Schema and Storage

The core table is minimal:

```
short_codes(
  short_code   VARCHAR(8)  PRIMARY KEY,
  long_url     TEXT        NOT NULL,
  created_at   TIMESTAMP,
  expires_at   TIMESTAMP,
  user_id      BIGINT
)
```

For scale, a relational database (PostgreSQL, MySQL) works fine up to several billion rows with proper indexing. The primary key lookup on `short_code` is a single B-tree index scan. If you anticipate write throughput exceeding what a single primary can handle, discuss read replicas and eventual sharding.

NoSQL (Cassandra, DynamoDB) is worth mentioning for truly massive scale — the access pattern (key → value lookup) maps perfectly to key-value stores, and you get horizontal write scaling for free.

## Caching: The 80/20 Rule in Practice

URL shorteners exhibit strong Pareto distribution: roughly 20% of short URLs generate 80% of traffic. This makes caching extremely effective. A Redis cache in front of your database dramatically reduces read load.

Cache the mapping `short_code → long_url` with a TTL aligned to your expiration policy. On a cache hit, return immediately and skip the database entirely. Cache miss: query DB, populate cache, redirect.

At 115,000 reads/second, even a 90% cache hit rate means only 11,500 database reads/second — easily handled by a single read replica. Size your cache: 100 million entries × ~200 bytes per entry ≈ 20 GB, well within a single Redis instance.

## Redirect Performance: 301 vs 302

This is a favorite follow-up. **301 (Moved Permanently)** tells browsers to cache the redirect indefinitely — future requests for that short URL go directly to the destination, bypassing your servers entirely. This saves bandwidth and server load but breaks analytics (you never see the request).

**302 (Found / Temporary Redirect)** routes every request through your servers, enabling click tracking, A/B testing, and geo-targeting. Bitly and most analytics-heavy shorteners use 302. TinyURL historically used 301 for pure performance.

Choose 302 unless analytics are explicitly out of scope. It's the more interesting design choice.

## Analytics Pipeline

If analytics are in scope, discuss two approaches:

**Synchronous**: Log each redirect to a database before responding. Simple but adds latency to every redirect — bad at scale.

**Asynchronous**: Publish a click event to a message queue (Kafka, SQS) during the redirect, respond immediately with 302, and let a consumer process analytics in the background. This decouples analytics from the critical path. The consumer aggregates data and writes to a time-series store (ClickHouse, BigQuery) for dashboards.

## Sharding for Billion-Scale

At planetary scale, a single database node can't hold all URLs. Discuss two sharding strategies:

**Range-based sharding** on `short_code` (e.g., a-m on shard 1, n-z on shard 2) is simple but creates hot spots if certain prefixes are more popular.

**Hash-based sharding** distributes evenly by hashing the short code to a shard number. Most production systems use consistent hashing so adding shards doesn't require full resharding.

In practice, most interviewers are satisfied when you identify the need for sharding and describe one sound approach — you don't need to solve consistent hashing in full detail unless prompted.

## Custom Domains and Multi-Tenancy

Enterprise URL shorteners (Bitly Enterprise, Rebrandly) let customers use their own domains (`go.company.com/abc123`). Architecturally this adds a domain routing layer: incoming request → look up tenant by domain → resolve short code within tenant's namespace. Store tenant_id alongside each short code or use a separate namespace per tenant.

## Common Follow-Up Questions

- "What if a user submits the same long URL twice?" — Deduplicate with a reverse index (`long_url → short_code`) or just issue a new short code per request (simpler, costs more storage).
- "How do you handle expired URLs?" — Lazy deletion (check `expires_at` on read) vs. background TTL sweep job. Lazy deletion is simpler; a sweep job keeps the database clean.
- "How do you prevent abuse?" — Rate limiting per IP/user at the write endpoint, blocklist of malicious long URLs checked against a Safe Browsing API.

The URL shortener is deceptively rich. A strong answer moves through requirements, encoding, database design, caching strategy, and redirect semantics in about 35–40 minutes, leaving time for at least two of these follow-ups.
