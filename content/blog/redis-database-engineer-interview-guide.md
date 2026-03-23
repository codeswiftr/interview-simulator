---
title: "Redis and In-Memory Data Store Interview Guide"
description: "Technical interview preparation for Redis: data structures, persistence options, clustering and replication, Pub/Sub, use cases (caching, session store, rate limiting, leaderboards), and how Redis knowledge shows up in system design interviews."
date: "2026-03-19"
category: "Technical Skills Guides"
---

# Redis and In-Memory Data Store Interview Guide

Redis knowledge shows up in two interview contexts: backend engineer roles where you've used Redis in production, and system design interviews where Redis is the right tool for a specific component. In both cases, interviewers probe beyond "it's a fast cache" — they want to understand which data structures you'd use, what persistence you'd configure, and what the failure modes are.

## Redis Data Structures: The Fundamental Differentiator

Redis is not just a key-value store. Its data structures are what make it useful for a wide range of problems:

**String**: Basic key-value. INCR/DECR are atomic — the foundation of counters and rate limiters. SET with NX (only set if not exists) + EX (expiry) is the pattern for distributed locks.

**Hash**: Map of field-value pairs within a key. Efficient for storing objects with many fields — better than JSON strings when you need to update individual fields without reading the whole object. Use case: user profile data, session attributes.

**List**: Doubly linked list. LPUSH/RPUSH and LPOP/RPOP for queue semantics. LRANGE for pagination. Use case: activity feeds (LPUSH event, LTRIM to cap list length), job queues (though dedicated systems like Celery/Sidekiq use Redis lists under the hood).

**Set**: Unordered unique values. SADD, SMEMBERS, SUNION, SINTER, SDIFF. Use case: unique visitors, friend lists, tagging systems. SRANDMEMBER for random selection.

**Sorted Set (ZSet)**: Values with associated scores, kept sorted by score. ZADD, ZRANGE, ZRANGEBYSCORE, ZRANK. Use case: leaderboards (score = game score), rate limiting (score = timestamp), priority queues. Sorted sets are one of the most useful structures in Redis for engineering problems.

**HyperLogLog**: Probabilistic cardinality estimation with very low memory (~12KB regardless of set size). ~1% error rate. Use case: counting unique users at scale when exact counts aren't required.

**Pub/Sub**: Message broadcasting. Publishers send to a channel; all subscribers receive. Not persistent — messages sent to a channel with no subscribers are lost. For persistent messaging, use Redis Streams.

**Streams**: Append-only log, consumer groups, message acknowledgment. Redis's answer to Kafka for simpler use cases. Consumer groups allow multiple consumers to process different messages (unlike Pub/Sub where all consumers get all messages).

## Interview Pattern Questions

**Design a rate limiter**: The canonical Redis interview question. Options:
- Fixed window: INCR key (reset on window boundary), SET expiry on first increment. Problem: burst at window boundary.
- Sliding window with sorted set: ZADD with timestamp as score, ZREMRANGEBYSCORE to remove old entries, ZCARD to count. Accurate but more expensive.
- Token bucket: Lua script to atomically check and update token count. Smooth rate limiting.

**Design a leaderboard**: Sorted set. ZADD leaderboard score userid. ZRANK for rank. ZRANGE with WITHSCORES for top N. ZINCRBY to add points atomically. Scales to millions of entries.

**Design a distributed lock**: SET key value NX EX seconds. NX ensures only one lock holder; EX ensures automatic expiry on crash. Redlock algorithm for distributed multi-node locks (controversial — Redlock is debated for correctness under network partitions).

**Design a session store**: HSET session:{token} field value with TTL (EXPIRE). HGET for individual fields. HDEL to log out. Scales well because sessions are small, independent objects.

## Persistence: RDB vs AOF

Redis can be purely in-memory (no persistence) or persist data with two mechanisms:

**RDB (Redis Database)**: periodic snapshots. Low overhead during normal operation. Risk: data loss between snapshots (if Redis crashes at 14:59, you lose data since the 14:50 snapshot).

**AOF (Append-Only File)**: log of write commands. Can be configured to fsync every second (up to 1s of data loss) or on every write (no data loss, significant performance cost). AOF files are larger than RDB but more durable.

**For most production use cases**: AOF with `appendfsync everysec` — 1 second of potential data loss with manageable performance cost. For data that can be rebuilt (cache), no persistence needed.

## Clustering and Replication

**Replication**: One primary, multiple replicas. Replicas are read-only and asynchronously replicate from the primary. Read scaling (route read traffic to replicas). Failover requires Sentinel or Cluster.

**Redis Sentinel**: High availability without clustering. Monitors the primary, promotes a replica on primary failure. Simple but limited to one primary shard.

**Redis Cluster**: Horizontal scaling. Keyspace split into 16,384 hash slots distributed across multiple primary nodes, each with replicas. Keys with the same hash tag (`{user}:123` and `{user}:456`) go to the same slot. Multi-key commands require all keys to be in the same slot.

## What Not to Use Redis For

Redis is an in-memory store — data that exceeds memory is evicted or causes OOM. It's not appropriate for: primary persistent storage of large datasets, complex relational queries, durable event logs (use Kafka), full-text search (use Elasticsearch).

The system design answer: "I'd use Redis for the session cache and rate limiting layer, backed by PostgreSQL as the source of truth for persistent data." That framing — Redis as the fast layer, relational DB as the durable layer — demonstrates production system thinking.
