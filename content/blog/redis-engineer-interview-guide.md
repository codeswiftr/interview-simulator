---
title: "Redis Interview Guide: Caching, Data Structures, and Distributed Systems Patterns"
description: "A technical deep-dive into Redis interview topics: data structures, cluster architecture, persistence options, and common patterns interviewers expect you to know."
date: "2026-03-20"
category: "Technical Skills"
---

# Redis Interview Guide: Caching, Data Structures, and Distributed Systems Patterns

Redis interviews span a wider range than most engineers expect. A strong candidate knows not just that Redis is fast, but *why* it is fast, when to use each data structure, and how Redis handles the distributed systems problems that matter at scale. Here is the structured preparation you need.

## Core Data Structures and When to Use Them

Understanding Redis data structures is table stakes. Interviewers expect you to know not just the API but the operational complexity and appropriate use case for each.

**Strings** are the simplest and most misused. They are appropriate for atomic values, counters (`INCR`, `DECR`), and short-lived serialized objects. The `SETNX` pattern (set if not exists) underlies basic distributed locking. Strings store up to 512MB but using them as a general-purpose object store defeats the purpose.

**Lists** are linked lists supporting O(1) push/pop at both ends. `LPUSH`/`RPOP` gives you a queue. `LPUSH`/`LPOP` gives you a stack. `BRPOP` and `BLPOP` block until an element is available — useful for lightweight job queues. At high cardinality, consider Streams instead.

**Sets** provide unordered collections of unique strings with O(1) average-case membership testing. Set operations (`SUNION`, `SINTER`, `SDIFF`) are extremely efficient and underlie patterns like "users who have visited both pages A and B."

**Sorted Sets (ZSets)** are the most powerful structure. Each member has an associated floating-point score; members are ordered by score. `ZADD`, `ZRANGE`, `ZRANGEBYSCORE`, `ZRANK` are the core operations. ZSets power leaderboards, priority queues, and any system where you need ordered retrieval. Time-series windows (expire old entries by score = timestamp) and rate limiting are natural fits.

**Hashes** are maps of field-to-value, optimal for representing objects. A user record as a Hash costs significantly less memory than a JSON string and allows field-level updates. `HGET`, `HSET`, `HMGET` are the workhorses.

**Streams** (added in Redis 5.0) are append-only logs with consumer group semantics — essentially Kafka-lite. Streams support message acknowledgment, consumer groups, and at-least-once delivery. Use Streams when Lists start feeling inadequate for your job queue patterns.

**HyperLogLog** enables probabilistic cardinality estimation with ~1% error and O(1) memory regardless of the actual set size. `PFADD`, `PFCOUNT`, and `PFMERGE` are the entire API. Use it for "how many unique visitors today" where approximate answers are acceptable.

## Critical Use Cases

**Rate limiting** is one of the most common Redis interview topics. The sliding window pattern uses a ZSet where the score is the timestamp and members are request IDs. On each request: remove entries outside the window (`ZREMRANGEBYSCORE`), count remaining entries, add the new request, check against limit. This executes atomically via Lua script or pipeline.

**Session storage**: Redis TTL (`EXPIRE`, `EXPIREAT`) makes session expiration automatic. Storing sessions as Hashes rather than serialized JSON allows partial updates without fetching and re-serializing the entire object.

**Pub/Sub vs Streams**: Pub/Sub in Redis is fire-and-forget with no persistence — subscribers that miss a message cannot retrieve it. Streams persist messages and support consumer groups with acknowledgment. Know when to recommend each.

**Distributed locking**: The `SET key value NX EX seconds` pattern is the correct atomic implementation. Redlock (the multi-node distributed lock algorithm) is contentious — understand that it exists, what problem it solves, and why Martin Kleppmann criticized it.

## Redis Cluster and Persistence

**Redis Cluster** shards data across nodes using 16,384 hash slots. Every key maps to a slot via CRC16. Multi-key commands (`MGET`, `MSET`, `SUNION` across keys) only work when all keys hash to the same slot — hash tags (`{user}.session` and `{user}.profile`) force co-location. The cluster requires a minimum of 3 primary nodes for quorum.

**Persistence options**: RDB (snapshotting) writes point-in-time dumps at configured intervals — lower overhead, less durability. AOF (Append Only File) logs every write command — higher durability, larger files, slower restarts. `appendfsync everysec` is the standard production setting, accepting up to 1 second of data loss. Many production deployments combine RDB + AOF for balance.

## Sample Interview Questions

**"How would you implement a leaderboard for 10 million users?"**
Use a Sorted Set. Score = user's points. `ZADD leaderboard score user_id`, `ZREVRANK leaderboard user_id` for rank, `ZREVRANGE leaderboard 0 99 WITHSCORES` for top 100. This is O(log N) for updates and O(log N + M) for range queries regardless of total user count.

**"What happens when a Redis node runs out of memory?"**
Behavior depends on `maxmemory-policy`. `noeviction` returns errors. `allkeys-lru` evicts least recently used keys. `volatile-lru` evicts only keys with TTL. Know the eviction policies and when each is appropriate.

**"How would you ensure your Lua script runs atomically?"**
Redis executes Lua scripts atomically — no other command runs while the script executes. This is stronger than `MULTI`/`EXEC` transactions which can still see interleaving from other clients between commands in a pipeline. Use `EVAL` for operations that must be atomic across multiple keys.

**"When would you NOT use Redis?"**
When you need durable, queryable storage of large objects; when your dataset far exceeds available RAM; when you need complex relational queries. Redis is not a database replacement — it is a complement.

Strong Redis interviews reward candidates who can reason through trade-offs rather than recite API documentation.

---
