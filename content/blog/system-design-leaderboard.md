---
title: "System Design: Real-Time Leaderboard"
description: "Design a real-time leaderboard system — Redis sorted sets, score ingestion at scale, global vs. friend leaderboards, pagination, and consistency tradeoffs for gaming and competitive platforms."
date: "2026-03-20"
category: "System Design"
---

# System Design: Real-Time Leaderboard

Leaderboard design is a common system design question for gaming, competitive platforms, and any application with rankings. It looks simple — keep a sorted list of scores — but the constraints at scale force interesting architectural decisions. This guide covers the components, the tradeoffs, and the design choices interviewers expect you to articulate.

## Requirements Clarification

Before designing, clarify:
- **Scale:** How many users? How many score updates per second? (1M users and 10K updates/second are very different from 100M users and 100K updates/second)
- **Leaderboard types:** Global (all users), friend (social graph subset), regional?
- **Update frequency:** Real-time, near-real-time (seconds delay), or batched?
- **Read pattern:** Top-N, user's rank + neighbors, paginated?
- **Consistency:** Is it acceptable to show a rank that's 5 seconds stale?

A reasonable baseline: 100M users, 50K score updates/second, global leaderboard with top 1000 visible, user's rank within ±10 neighbors, near-real-time (5s lag acceptable).

## Core Data Structure: Redis Sorted Sets

The canonical building block for leaderboards is Redis sorted sets (`ZSET`). Operations:
- `ZADD leaderboard <score> <user_id>` — add/update score: O(log n)
- `ZREVRANK leaderboard <user_id>` — get rank (0-indexed): O(log n)
- `ZREVRANGE leaderboard 0 9` — get top 10: O(log n + k)
- `ZREVRANGEBYSCORE leaderboard +inf -inf LIMIT offset count` — paginate: O(log n + k)

Redis sorted sets store members sorted by score in a skip list. Operations are O(log n) for rank queries, which is excellent for typical leaderboard sizes (millions of entries).

For 100M users: a Redis sorted set with 100M entries uses roughly 2-4GB RAM depending on user ID size. Feasible on a single high-memory Redis instance.

## Write Path: Score Ingestion

Score updates come from game servers or event processors. The write path:

1. **Game server** sends score event to a message queue (Kafka) rather than directly to Redis — decouples the leaderboard from game latency
2. **Score processor** consumes Kafka events, applies business rules (anti-cheat, score validation), writes to Redis with `ZADD`
3. **Redis** updates the sorted set atomically

Why Kafka? Game events burst — a battle royale match ending produces thousands of simultaneous score updates. Kafka buffers this burst; the processor handles it at sustainable throughput.

For 50K updates/second: a single Redis instance handles well over 100K `ZADD` operations/second. The bottleneck is typically the processor's throughput and network, not Redis.

## Read Path: Leaderboard Queries

Two main read patterns:

**Top-N leaderboard:** `ZREVRANGE leaderboard 0 999 WITHSCORES` returns top 1000 with scores. Cache this in a CDN or application cache for 1-5 seconds — the top leaderboard rarely changes dramatically second-to-second and is read very frequently.

**User's rank:** `ZREVRANK leaderboard <user_id>` gives rank. To show ±10 neighbors:
```
rank = ZREVRANK leaderboard user_id
start = max(0, rank - 10)
ZREVRANGE leaderboard start (rank + 10) WITHSCORES
```
This is two Redis calls — fast enough for real-time display.

## Friend Leaderboard

Global leaderboards are technically simpler but socially less engaging. Friend leaderboards (your rank among friends) are more interesting but harder to build at scale.

**Option 1: Query-time filter.** Get all friend IDs from social graph service, call `ZSCORE leaderboard <friend_id>` for each, sort in application layer. Works for small friend counts (<500), doesn't scale.

**Option 2: Per-user friend leaderboard.** Maintain a separate sorted set per user containing only their friends' scores. Updated when any friend's score changes — fanout problem. If a user has 5000 followers, a score update triggers 5000 sorted set writes. Acceptable for most users; use async fanout for celebrities.

**Option 3: Hybrid.** Compute friend leaderboards in batch (every 5 minutes) for users with many followers, real-time for users with few. Store precomputed results in a cache.

## Sharding for Extreme Scale

For truly global scale (1B users), a single Redis instance won't hold the full sorted set. Sharding options:

**Score-range sharding:** Shard 0 holds scores 0-1000, Shard 1 holds 1001-2000, etc. Top-N queries read only the top shards. Problem: score distribution is skewed — most users cluster near the bottom.

**Consistent hashing by user:** Distribute users across shards by user ID. Top-N becomes an N-way merge across shards. Rank requires counting entries in all higher-scoring shards.

**Hierarchical aggregation:** Shards maintain local counts by score bucket. A coordinator aggregates to compute global rank. Approximate but fast.

For most interview discussions, a single Redis instance with replication handles the stated scale. Present sharding as the path to 1B+ users.

## Persistence and Durability

Redis by default is an in-memory store with RDB snapshots and AOF logging. For a leaderboard:
- Use AOF with `everysec` sync — at most 1 second of data loss
- Keep an authoritative score record in PostgreSQL
- On Redis failure, rebuild the leaderboard by replaying scores from PostgreSQL

The database is the source of truth; Redis is the serving layer. This separation enables cache rebuilds and handles Redis failures gracefully.

## Consistency Tradeoffs

**Strong consistency:** Every score update immediately visible. Achieved by synchronous Redis write in the request path. Problem: Redis write latency (≈1ms) adds to every score update.

**Eventual consistency:** Score updates processed asynchronously via Kafka. Rank is stale by seconds. For most leaderboards, this is acceptable and preferable — users don't need millisecond-accurate rank updates.

The interview answer: choose eventual consistency for high-write scenarios, clearly state the lag bound, and explain how to monitor lag (Kafka consumer group lag).

## Monitoring

Key metrics: Redis memory usage, sorted set cardinality, `ZADD` latency, Kafka consumer lag, top-N cache hit rate. Alert on Kafka lag growth (processor not keeping up) and Redis memory approaching 80% of available RAM.
