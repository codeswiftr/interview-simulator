---
title: "Caching Strategies in System Design Interviews"
description: "Master caching architecture for system design interviews. Covers cache-aside, write-through, write-behind, eviction policies, cache invalidation strategies, and CDN caching at scale."
date: "2025-10-27"
category: "Technical Skills Guides"
---

# Caching Strategies in System Design Interviews

Caching is one of the most frequently discussed topics in system design interviews. Almost every large-scale system uses caching at multiple layers, and interviewers expect you to understand not just what caching does, but which strategy to use in which context, and what problems each approach introduces.

## Why Caching Matters

A database query might take 5–50ms. A Redis lookup takes 0.1–1ms. For high-traffic systems, this difference is the gap between serving 10,000 requests/second and 500,000 requests/second — on the same hardware.

**The fundamental trade-off**: Caching introduces stale data risk. The right caching strategy depends on how much staleness your use case can tolerate.

## Cache-Aside (Lazy Loading)

The most common pattern. The application manages the cache explicitly.

```
Read:
1. Check cache for key
2. If miss: read from DB, populate cache, return
3. If hit: return cached value

Write:
1. Write to DB
2. Invalidate or update cache key
```

**Pros**: Cache only contains data that's actually requested. Cache failures degrade gracefully (fall through to DB).

**Cons**: Cache miss on cold start or after invalidation. Risk of thundering herd (many requests hitting DB simultaneously on cache miss for popular data).

**Best for**: Read-heavy workloads with occasional cache misses being acceptable.

## Write-Through

Write to cache and DB simultaneously. Cache is always up-to-date.

```
Write:
1. Write to cache
2. Write to DB (synchronously)
```

**Pros**: Cache always has fresh data; eliminates stale reads.

**Cons**: Write latency increases (both cache and DB must succeed). Cache fills with data that may never be read (write amplification).

**Best for**: Systems that read shortly after writing the same data (write → immediate read pattern).

## Write-Behind (Write-Back)

Write to cache immediately; async write to DB later.

```
Write:
1. Write to cache
2. Mark as dirty
3. [Async] Flush dirty entries to DB in batches
```

**Pros**: Lowest write latency. DB write throughput can be dramatically reduced (batch coalescing).

**Cons**: Data loss if cache fails before async flush. More complex failure handling.

**Best for**: Write-heavy workloads where some data loss is acceptable (gaming scores, counters, analytics events).

## Read-Through

Cache sits in front of the database and handles cache misses automatically (rather than the application managing it).

Similar to cache-aside, but the cache itself fetches from DB on miss. Application always talks to cache.

**Best for**: When you want a single abstraction layer and can configure the cache (e.g., using a cache provider that supports this like ElastiCache with DAX for DynamoDB).

## Eviction Policies

When the cache is full, which entries get removed?

**LRU (Least Recently Used)**: Evict the entry that was accessed furthest in the past. Most common default. Good for temporal locality workloads.

**LFU (Least Frequently Used)**: Evict the least often accessed entry. Better for workloads where some items are perennially popular.

**TTL (Time-to-Live)**: Expire entries after a fixed duration, regardless of access frequency. Simple, predictable, but can cause simultaneous mass expiration ("cache stampede").

**FIFO**: First in, first out. Simple but rarely optimal.

**Interview guidance**: "I'd use LRU for most use cases because it naturally keeps recently popular data in cache. For content with known freshness requirements, I'd combine LRU with a TTL."

## Cache Invalidation Strategies

Cache invalidation is famously one of the hardest problems in computer science. Your interview answer should show you've thought through the trade-offs.

**TTL-based expiration**: Simple and predictable. The question is what TTL to use — short TTL = more DB load; long TTL = stale data for longer. Common TTLs: 5–60 minutes for non-critical data, seconds for high-frequency changing data.

**Event-driven invalidation**: When the underlying data changes, publish an event to a message bus. Cache consumers listen for events and invalidate relevant keys. Consistent but adds architectural complexity.

**Versioned keys**: Instead of invalidating `user:{id}`, use `user:{id}:v{version}`. When data changes, increment the version — old keys become "orphaned" and expire naturally via TTL. Simple, avoids race conditions, at the cost of key proliferation.

**Write-around (for append-heavy data)**: Don't cache writes at all; cache only reads. Works when write-to-read ratio is low and data rarely re-read.

## CDN Caching

For serving static assets and cacheable HTTP responses globally:

**What belongs in CDN**: Static assets (JS, CSS, images), public API responses that don't change per-user, video/audio content.

**Cache-Control headers**:
```
Cache-Control: public, max-age=31536000, immutable  # Static assets (1 year)
Cache-Control: public, max-age=300, stale-while-revalidate=60  # API responses
Cache-Control: private, no-store  # Authenticated/user-specific content
```

**Cache busting**: When you deploy new assets, change the filename/URL (e.g., `app.abc123.js`). The CDN sees a new URL and fetches the updated version.

**Edge functions**: Modern CDNs (Cloudflare Workers, Vercel Edge Functions) let you run code at the CDN edge, enabling per-request logic without a round-trip to the origin.

## System Design: Where to Add Caches

In a typical web application interview:

1. **Browser cache**: HTTP cache-control headers for public assets
2. **CDN**: Static content, cacheable API responses
3. **API gateway cache**: Common query results
4. **Application-level cache**: In-process (Caffeine, Guava) for ultra-hot data
5. **Distributed cache**: Redis/Memcached for shared state across service instances
6. **Database query cache**: Most databases have built-in caching; usually less predictable than explicit caching

Describing this multi-tier architecture and reasoning about which data belongs at which tier is what distinguishes a strong system design answer on caching.
