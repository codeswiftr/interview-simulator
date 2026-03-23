---
title: "System Design: Building a Distributed Cache"
description: "How to design a distributed cache in system design interviews — cache eviction policies, consistent hashing, replication, partitioning, and Redis vs Memcached tradeoffs."
date: "2026-03-20"
category: "System Design"
---

# System Design: Building a Distributed Cache

Designing a distributed cache is one of the most common system design questions. It appears in interviews at every major tech company because it tests multiple skills simultaneously: data structures, distributed systems theory, failure handling, and performance reasoning. This guide walks through the full design, from eviction policies to production-grade decisions.

## Clarify Requirements First

Before drawing anything, establish constraints. A cache for a social media feed has very different requirements from a session store or a rate limiter. Key questions:

- What data is being cached? (objects, HTML fragments, database query results, sessions)
- What are the read/write ratios? (caches are typically read-heavy — 100:1 is common)
- What consistency is required? (can reads see slightly stale data?)
- What is the expected throughput and latency target? (millions of QPS, sub-millisecond?)
- What is the eviction policy when the cache is full?
- How large is the dataset, and what is the expected hit rate?

Stating these assumptions up front shows structured thinking and prevents designing for the wrong problem.

## Cache Eviction Policies

When the cache is full and a new item arrives, something must be evicted. The policy choice depends on the access pattern:

**LRU (Least Recently Used)**: Evicts the item not accessed for the longest time. Assumes recent access predicts future access. Implemented with a doubly-linked list plus a hash map for O(1) get and put. The standard choice for general-purpose caches.

**LFU (Least Frequently Used)**: Evicts the item accessed least often. Better for skewed access patterns where some items are permanently popular. Harder to implement efficiently (requires frequency buckets); also suffers from cache pollution where old frequently-used items crowd out new ones.

**TTL (Time-To-Live)**: Items expire after a fixed duration regardless of access. Used when data freshness matters (API responses, session tokens). Can be combined with LRU or LFU.

**ARC (Adaptive Replacement Cache)**: Dynamically balances between recency and frequency by maintaining two LRU lists. Used in ZFS and some CDNs. More complex but self-tuning.

In interviews, start with LRU, explain the implementation, then mention TTL as a composable extension. Only introduce LFU if the access pattern clearly warrants it.

## Consistent Hashing and Partitioning

A single cache node cannot serve millions of QPS or store terabytes of data. Partitioning distributes the keyspace across multiple nodes.

**Naive modular hashing** (`key_hash % N`) is simple but catastrophic when N changes — nearly all keys must be remapped, causing a thundering herd of cache misses (cache stampede) that overwhelms the origin.

**Consistent hashing** maps both keys and nodes to a ring (circular hash space of 0 to 2^32). Each key is assigned to the next node clockwise on the ring. Adding or removing a node only remaps keys in one segment, not the entire keyspace. On average, only `K/N` keys need to move when a node is added (K = total keys, N = node count).

**Virtual nodes** solve uneven distribution: each physical node is represented by multiple points on the ring (e.g., 150 virtual nodes). This distributes load more evenly and smooths out the impact of hotspots. When a node is removed, its virtual node slots are reassigned across the remaining nodes.

Most production systems (Redis Cluster, Cassandra, Amazon's Dynamo) use consistent hashing with virtual nodes. In Redis Cluster, the keyspace is divided into 16,384 hash slots, and nodes own ranges of slots — a variant of consistent hashing with explicit slot assignment.

## Replication Strategies

Partitioning alone provides no fault tolerance. If a node dies, all keys owned by that node are lost (cache miss storm). Replication distributes copies.

**Primary-replica replication**: Each primary node has one or more replicas. Writes go to primary, replicated asynchronously (or synchronously for stronger consistency). If the primary dies, a replica is promoted. Redis Sentinel automates this failover. Asynchronous replication means replicas may lag — reads from replicas can return stale data.

**Multi-primary (active-active) replication**: All nodes accept writes. Conflicts resolved with last-write-wins (LWW) using timestamps, or more complex CRDTs. Used when write availability trumps strict consistency.

**Leaderless replication**: No designated primary. Writes are sent to a quorum of nodes (W out of N). Reads are sent to R nodes. Consistency guaranteed when W + R > N. Used in Amazon's Dynamo-style systems.

For caches, primary-replica is the most common choice — the simplicity tradeoff is acceptable because cache data is inherently derived (can be reconstructed from the source of truth).

## Write Policies

How writes interact with the cache and backing store determines consistency and performance:

**Write-through**: Write to cache and backing store synchronously. Every cache entry is consistent with the database. Higher write latency; cache always warm. Good when read-after-write consistency is required.

**Write-back (write-behind)**: Write to cache only, flush to backing store asynchronously. Lower write latency; risk of data loss if cache node fails before flush. Used in scenarios where write throughput is the bottleneck.

**Write-around**: Bypass the cache on writes, write directly to backing store. Cache is populated on reads. Good for write-once, read-many data. Prevents cache pollution from write-heavy, read-rare data.

## Cache Stampede and Solutions

When a popular cache entry expires, many concurrent requests find a cache miss and simultaneously query the database. This **thundering herd** (cache stampede) can overwhelm the origin.

**Probabilistic early expiration**: Before TTL expires, each read has a small probability of refreshing the cache. The probability increases as TTL approaches. This distributes refresh load over time with no coordination.

**Mutex/lock-based coalescing**: The first request to find a miss acquires a lock and fetches from origin. Other requests wait. Only one origin query per cache miss. Risk: lock contention at high QPS.

**Background refresh**: Cache entries are refreshed asynchronously before expiry. Stale values are served until the refresh completes. Eliminates thundering herd entirely at the cost of briefly serving stale data.

**Lease mechanism**: Cache grants a lease (token) to the first requester. Others wait or receive a "try again" signal. When the leaseholder writes the value back, it includes the token to validate freshness. Facebook's Memcache uses this pattern.

## Redis vs. Memcached Tradeoffs

Both are in-memory caches, but they serve different needs:

| Dimension | Redis | Memcached |
|---|---|---|
| Data structures | Strings, lists, sets, hashes, sorted sets, streams, bitmaps | Strings only |
| Persistence | RDB snapshots, AOF log | None |
| Replication | Built-in primary-replica + Sentinel + Cluster | External (mcrouter) |
| Lua scripting | Yes (atomic multi-step operations) | No |
| Multi-threading | Single-threaded command processing (I/O threads in Redis 6+) | Multi-threaded |
| Memory efficiency | Slightly higher overhead per key | Slightly leaner |

Choose **Memcached** when: pure string caching, maximum memory efficiency, multi-threaded architecture matters. Choose **Redis** when: complex data structures (leaderboards with sorted sets, pub/sub, rate limiting with atomic increments), persistence, or built-in clustering is needed.

## How to Answer This in an Interview

Structure your answer in four phases:

1. **Clarify**: read/write ratio, consistency requirements, scale, data type.
2. **Single node design**: LRU + hash map, TTL, API (`get`, `set`, `delete`).
3. **Scale out**: consistent hashing with virtual nodes, primary-replica replication.
4. **Production hardening**: cache stampede prevention (probabilistic expiry or lease), monitoring (hit rate, eviction rate, latency percentiles), graceful degradation when cache is unavailable.

End with tradeoffs: stronger consistency costs latency, higher replication increases durability but adds write overhead. Showing you understand these tradeoffs — not just the happy path — is what earns senior-level marks.
