---
title: "Caching Strategies Interview: Cache Patterns, Invalidation, and Distributed Caching"
description: "Deep dive on caching for system design interviews — cache-aside vs write-through vs write-behind, cache invalidation, Redis cluster, cache stampede/avalanche/penetration prevention, and practical interview Q&A."
date: "2026-03-20"
category: "System Design"
---

# Caching Strategies Interview: Cache Patterns, Invalidation, and Distributed Caching

Caching comes up in virtually every system design interview, but most candidates cover it superficially ("add a cache layer, use Redis"). Interviewers at senior and staff levels want depth: which patterns apply when, what invalidation strategy to use, and how to handle the failure modes that make caching hard in production.

## Cache Patterns

**Cache-Aside (Lazy Loading)**

The application manages cache population. On cache miss: fetch from database, write to cache, return result. On cache hit: return cached value directly.

```
get(key):
  value = cache.get(key)
  if value is None:
    value = db.fetch(key)
    cache.set(key, value, ttl=300)
  return value
```

**Pros:** Only caches what's actually accessed. Resilient to cache failure (app falls back to DB). Cache schema can differ from DB schema.

**Cons:** Cache miss penalty (3 round trips). Cache stampede risk on cold start or expiry. Data can be stale up to TTL.

**Best for:** Read-heavy workloads, when cache failure tolerance is important, when not all data needs caching.

---

**Write-Through**

Every write goes to both cache and database synchronously. Cache always reflects current state.

```
set(key, value):
  db.write(key, value)
  cache.set(key, value)
```

**Pros:** Cache always fresh. No read penalty for recently-written data.

**Cons:** Write latency increases (both cache and DB). Caches data that may never be read ("cache pollution").

**Best for:** When data is frequently read after being written. User profiles, settings, frequently accessed records.

---

**Write-Behind (Write-Back)**

Application writes to cache immediately; cache asynchronously flushes to database.

**Pros:** Very low write latency for the application. Absorbs write spikes.

**Cons:** Risk of data loss if cache crashes before flush. Complex consistency guarantees. Harder to implement correctly.

**Best for:** High-write-volume systems where durability can tolerate brief async lag. Gaming leaderboards, IoT sensor data aggregation.

---

**Read-Through**

Cache sits in front of DB; on miss, cache itself fetches from DB (not the application). Application only talks to cache.

Conceptually similar to cache-aside but the cache library handles the DB fallback transparently.

## Cache Invalidation

Phil Karlton's famous observation: "There are only two hard things in Computer Science: cache invalidation and naming things."

**TTL-based expiry:** The simplest strategy — set a TTL on every cache entry. Stale data is guaranteed fresh within TTL seconds. Simple but blunt: you can't surgically invalidate specific entries.

**Write-through invalidation:** On every write, update or delete the corresponding cache entry. Guarantees consistency but adds coupling between write path and cache.

**Event-based invalidation:** Write events trigger cache invalidation through a message queue or pub/sub system. Decouples the write path. Adds complexity and potential for lag.

**Cache versioning:** Instead of invalidating, change the cache key when the underlying data changes. Old keys expire naturally. Works well for bulk invalidations ("invalidate all product listings after a price update") but requires key management.

**The invalidation trilemma:** Strong consistency, high availability, and partition tolerance — pick two. In practice, most caches accept eventual consistency (stale data within TTL) in exchange for availability.

## Distributed Cache Failure Modes

**Cache Stampede (Thundering Herd)**

When a popular cache key expires, many requests miss simultaneously and all hit the database at once.

Solutions:
- **Probabilistic early expiry:** Before TTL expires, randomly extend it. Some requests will proactively refresh the cache.
- **Mutex/lock on miss:** First request to miss acquires a lock, others wait for it to populate the cache.
- **Jitter in TTL:** Add randomness to expiry times so entries expire spread out, not in synchronized bursts.

**Cache Penetration**

Requests for keys that don't exist in cache OR database — typically null values or invalid IDs. Every request passes through to the database.

Solutions:
- Cache null results with short TTL ("this key doesn't exist")
- Bloom filter at the cache layer to reject provably-invalid keys before querying the database

**Cache Avalanche**

Many cache keys expire at the same time (e.g., all set with the same TTL after a service restart), causing mass database load.

Solutions:
- TTL jitter: randomize expiry times
- Gradual warming: don't expire everything at once on restart

## Redis in Production

**Redis Cluster:** Shards data across multiple nodes. Data is partitioned by key hash into 16384 hash slots. Each shard has replicas for failure tolerance. Clients know which shard holds which slots.

**Sentinel:** High availability for a single Redis instance — monitors the primary, promotes a replica on failure, notifies clients of the new primary address.

**Persistence options:**
- **RDB (Snapshot):** Point-in-time snapshots to disk. Fast restart, but potential for data loss since last snapshot.
- **AOF (Append-Only File):** Logs every write command. More durable (configurable to fsync on every write) but slower and larger.
- **No persistence:** Fastest. Valid for cache-only workloads where the source of truth is elsewhere.

## Common Interview Questions

**Q: When would you NOT use a cache?**
When data changes very frequently (cache provides little benefit and adds invalidation complexity). When consistency requirements are strict (financial transactions). When the data set is too small to benefit from caching overhead. When writes heavily outnumber reads.

**Q: How do you design a cache for a social media feed?**
Feed data is expensive to compute (join across followees' posts). Cache at the user level with write-on-follow (fan-out to followers' cache on post). Use Redis sorted sets with post timestamp as score for ordered retrieval. TTL for inactive users, always-warm for power users. Handle cache miss by computing feed from scratch.

**Q: How do you handle cache consistency in a distributed system?**
Accept eventual consistency for most cache use cases (TTL bounds staleness). For critical consistency (inventory counts, financial balances), use write-through and shorter TTLs, or skip caching entirely and rely on DB with read replicas.
