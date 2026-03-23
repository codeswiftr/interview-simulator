---
title: "Redis Internals Interview Guide"
description: "What engineers need to know about Redis for technical interviews — data structures, persistence, clustering, and real-world patterns used at Twitter, GitHub, and Stack Overflow."
date: "2026-03-19"
tags: ["redis", "system-design", "databases", "interview-prep", "backend"]
---

## Data Structures and When to Use Them

Redis ships six core data structures. Interviewers test whether you know *which* to reach for and *why*.

**Strings** are the default. They hold any binary data up to 512 MB — JSON blobs, serialized objects, counters, feature flags. The `INCR`/`INCRBY` commands operate atomically, making strings the right call for counters (rate limiting, inventory) without a lock.

**Hashes** map field-value pairs under one key. Use them for objects where you read or update individual fields without fetching the full payload. A user profile stored as a hash lets you `HGET user:1001 email` instead of deserializing a full JSON string. The memory efficiency is real too — Redis compresses small hashes with a ziplist encoding automatically.

**Lists** are doubly-linked lists with O(1) push/pop at both ends. Use them for queues (`LPUSH` / `BRPOP`) and activity feeds (prepend, trim with `LTRIM`). The distinction interviewers probe: lists are ordered by insertion, not by value. If you need sorted order, you want a sorted set.

**Sets** hold unique, unordered members. They support O(1) membership checks (`SISMEMBER`) and set operations (`SUNION`, `SINTER`, `SDIFF`). Classic use case: tracking unique visitors per day — `SADD visitors:2026-03-19 user:42`, then `SCARD` for the count.

**Sorted Sets (ZSets)** pair each member with a float score and maintain sorted order. O(log N) for adds and range queries. They are the correct structure for leaderboards, priority queues, and sliding-window rate limiting. `ZADD`, `ZRANGE`, `ZRANGEBYSCORE`, and `ZREMRANGEBYSCORE` together handle nearly every ranking use case.

**Streams** (added in Redis 5.0) are append-only logs with consumer groups, message IDs, and acknowledgment semantics. They are the right answer when you need pub/sub with durability and replay. Use `XADD` to append, `XREAD` or `XREADGROUP` to consume.

**The interview question you will get:** *"When would you choose a sorted set over a list?"* — when insertion order is not enough and you need queries by score range. When would you choose a stream over pub/sub? When message delivery must survive consumer crashes.

---

## Persistence: RDB vs AOF

Redis is in-memory, but it supports two persistence modes. Knowing the tradeoff is table stakes for any senior backend interview.

**RDB (Redis Database Snapshots)** writes a point-in-time binary snapshot to disk. Configured via `save 900 1` (save if at least 1 key changed in 900 seconds). RDB is compact, fast to restore, and has minimal runtime overhead — a `fork()` child handles the write. The cost: you can lose up to the last `save` interval of writes on a crash.

**AOF (Append-Only File)** logs every write operation. Three fsync policies:
- `appendfsync always` — safest, highest latency
- `appendfsync everysec` — compromise: at most 1 second of loss (default)
- `appendfsync no` — OS decides when to flush

AOF files grow large; Redis compacts them via `BGREWRITEAOF`. Recovery is slower than RDB because every operation replays.

**Combined mode** (`aof-use-rdb-preamble yes`) is the production default since Redis 4.0. Redis writes an RDB snapshot into the AOF file header, then appends incremental AOF records. Fast restore, low data loss.

**Interview framing:** RDB is right when startup speed matters and you can tolerate some data loss (caches). AOF is right when you need durability close to a traditional database. Combined mode is the safe default.

---

## Pub/Sub vs Streams

Pub/sub (`PUBLISH` / `SUBSCRIBE`) is fire-and-forget. Messages are not stored. Subscribers that are offline miss them permanently. This is acceptable for real-time notifications where stale data is useless — live dashboards, presence indicators.

Streams provide durable, replayable logs with consumer groups. A consumer group distributes messages across multiple consumers and tracks acknowledgment with `XACK`. If a consumer crashes, unacknowledged messages are re-delivered via `XPENDING` / `XCLAIM`.

```redis
# Producer
XADD orders * product_id 99 quantity 2

# Consumer group setup
XGROUP CREATE orders order-workers $ MKSTREAM

# Consumer reads
XREADGROUP GROUP order-workers worker-1 COUNT 10 BLOCK 2000 STREAMS orders >

# Acknowledge
XACK orders order-workers 1711234567890-0
```

Use pub/sub for ephemeral real-time fan-out. Use streams when you need guaranteed delivery, replay, or multiple independent consumer groups on the same feed.

---

## Clustering and Replication

**Replication** in Redis is primary/replica (formerly master/slave). The primary streams changes to replicas asynchronously. Replicas handle read traffic, reducing load on the primary. Failover is manual unless you add Sentinel.

**Redis Sentinel** monitors primaries, detects failures, and promotes a replica automatically. It also provides service discovery — clients query Sentinel for the current primary address.

**Redis Cluster** shards data across nodes using consistent hashing over 16,384 hash slots. Each primary owns a slot range; data is routed by `CRC16(key) % 16384`. Keys in the same hash tag (`{user:1001}:session`, `{user:1001}:cart`) land on the same slot, enabling multi-key operations.

Cluster topology requires a minimum of 3 primaries for quorum. Each primary should have at least one replica for fault tolerance.

**Interview question:** *"How does Redis Cluster handle a node failure?"* — the remaining primaries detect the failure via gossip protocol, promote the failed primary's replica after quorum agreement, and update the slot mapping. Clients with cluster-aware libraries reroute automatically.

---

## Common Patterns with Commands

### Rate Limiting (Sliding Window)

```redis
# Fixed window — simple but allows burst at boundary
INCR rate:user:1001:2026031914
EXPIRE rate:user:1001:2026031914 60

# Sorted set sliding window — precise
ZADD rate:user:1001 1711234567.123 1711234567.123
ZREMRANGEBYSCORE rate:user:1001 0 (NOW - 60)
ZCARD rate:user:1001  # if > limit, reject
```

### Distributed Locks (Redlock)

```redis
# Acquire: SET with NX (not exists) + PX (millisecond expiry)
SET lock:resource:42 <random-token> NX PX 5000

# Release: compare-and-delete via Lua (atomic)
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
else
    return 0
end
```

Always set a lock TTL. Always use a random token for release — prevents a slow process from releasing a lock it no longer holds.

### Caching Strategies

**Cache-aside (lazy loading):** Application checks Redis first, falls back to DB on miss, populates cache.
**Write-through:** Write to cache and DB synchronously on every update.
**Write-behind (write-back):** Write to cache immediately, flush to DB asynchronously.

Cache-aside is the most common. Write-through trades write latency for read consistency. Write-behind maximizes write throughput but risks data loss.

### Session Storage

```redis
HSET session:abc123 user_id 1001 role admin last_seen 1711234567
EXPIRE session:abc123 86400  # 24-hour TTL
```

Hashes let you update individual fields (`HSET session:abc123 last_seen NOW`) without rewriting the full session blob.

---

## Expiry and Eviction

Keys expire via TTL set with `EXPIRE`, `PEXPIRE`, `EXPIREAT`. Redis uses lazy expiration (checks on access) plus a periodic background sampler — it does not scan all keys continuously.

When memory is full, Redis enforces an eviction policy set via `maxmemory-policy`:

| Policy | Behavior |
|---|---|
| `noeviction` | Return error on write when full |
| `allkeys-lru` | Evict least-recently-used across all keys |
| `volatile-lru` | LRU eviction, only keys with TTL set |
| `allkeys-lfu` | Evict least-frequently-used (Redis 4.0+) |
| `volatile-ttl` | Evict keys with shortest remaining TTL |
| `allkeys-random` | Random eviction across all keys |

For a pure cache, `allkeys-lru` or `allkeys-lfu` is correct. For mixed workloads where some keys must not be evicted (application state), use `volatile-lru` and only set TTLs on expendable keys.

---

## How Companies Use Redis in Interviews

**Twitter** uses Redis for timeline caching. Each user's home timeline is a sorted set of tweet IDs scored by timestamp. Fan-out on write pushes new tweets into follower timelines. At scale, they hybrid this with fan-out on read for users with millions of followers.

**GitHub** uses Redis for rate limiting the API — exactly the fixed-window counter pattern above. They also use it for distributed job queuing (Resque, which was built on Redis lists).

**Stack Overflow** uses Redis for caching question and answer data, hot tag lists (sorted sets by question count), and real-time websocket fan-out via pub/sub.

These patterns appear in system design interviews as: *"Design a rate limiter," "Design a leaderboard," "Design a notification system."* Redis is the correct tool in most answers — the interview credit comes from knowing which structure and why.

---

## What Interviewers Actually Test

The surface-level question is always about Redis. The real question is whether you think about:

1. **Memory bounds** — Redis is in-memory. Every design decision has a memory cost. Know your data sizes.
2. **Atomicity** — Multi-step operations need Lua scripts or transactions (`MULTI`/`EXEC`) to avoid race conditions.
3. **Persistence tradeoffs** — Is this a cache or a source of truth? The answer changes the persistence config.
4. **Failure modes** — What happens when Redis goes down? Your application needs a fallback or a durability story.

Master these four concerns and you can answer virtually any Redis question in a system design or engineering interview.
