---
title: "System Design Deep Dive: Designing Database Systems at Scale"
description: "Master database system design for technical interviews. Learn how to design URL shorteners, rate limiters, leaderboards, and time-series systems with the right database choices and scaling strategies."
date: "2025-10-26"
category: "Technical Skills Guides"
---

# System Design Deep Dive: Designing Database Systems at Scale

Database design is the backbone of almost every system design interview. The decisions you make about data models, storage engines, and consistency trade-offs determine whether your system can handle the required scale. This guide covers the patterns that appear most in interviews.

## The Database Selection Framework

Before picking a database, answer three questions:

1. **What is the read/write ratio?** High read → optimize for read performance (replication, caching, denormalization). High write → optimize for write throughput (LSM trees, partitioning, write-ahead logging).

2. **What are the access patterns?** Key-value lookups → Redis or DynamoDB. Complex queries with JOINs → PostgreSQL. Time-series → InfluxDB or Cassandra with time-based partitioning. Graph traversals → Neo4j or specialized graph DB.

3. **What are the consistency requirements?** Financial transactions → strong consistency, ACID. Social feeds → eventual consistency is fine. Gaming leaderboards → somewhere in between.

## System Design Problem: URL Shortener

**Scale target**: 100 million URLs created/day, 10 billion reads/day (100:1 read ratio)

**Schema**:
```sql
CREATE TABLE urls (
    id         BIGINT PRIMARY KEY,
    short_code VARCHAR(8) UNIQUE NOT NULL,
    long_url   TEXT NOT NULL,
    user_id    BIGINT,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    click_count BIGINT DEFAULT 0
);
```

**Short code generation**: Use a counter + base62 encoding (a-z, A-Z, 0-9). A 7-character base62 code supports 3.5 trillion unique URLs. Alternative: MD5 hash of long URL + truncation (risk of collisions, but manageable).

**Scaling reads**: 
- Cache short_code → long_url in Redis (99% of reads from hot cache)
- Multi-region replicas for geographic distribution
- CDN layer for the redirect response itself

**Scaling writes**:
- Distributed counter (using Redis INCR or a snowflake ID) to avoid counter hotspot on single DB
- Write to primary; async replicate

**Analytics**: Append click events to Kafka → batch process into analytics DB (ClickHouse). Don't update `click_count` synchronously on each click — that's a hotspot.

## System Design Problem: Rate Limiter

A rate limiter is a classic "design a system that stores and reads state at very high throughput."

**Algorithms**:
- **Fixed window**: Simple, but allows burst at window boundaries
- **Sliding window log**: Accurate, but high memory usage (stores every request timestamp)
- **Sliding window counter**: Best balance — `current_count = prev_window_count * (1 - elapsed/window) + current_window_count`
- **Token bucket**: Allows bursting up to bucket size; good for most API rate limiting

**Storage**: Redis with atomic operations (INCR + EXPIRE) or Lua scripts for sliding window counter. At extreme scale: local Redis cluster with consistent hashing, one node per API key range.

**Data structure**:
```
Key: rate_limit:{user_id}:{endpoint}:{window_start}
Value: request count (INCR)
TTL: window duration
```

**Multi-region**: Distributed rate limiting across regions requires a consensus mechanism or accepting slight over-admission at region boundaries.

## System Design Problem: Leaderboard

**Scale**: Gaming leaderboard, 10 million users, real-time top 100.

**Redis Sorted Sets** are purpose-built for this:
```redis
ZADD leaderboard 1250 "user:123"  # Set score
ZREVRANK leaderboard "user:123"    # Get rank
ZREVRANGE leaderboard 0 99 WITHSCORES  # Top 100
ZSCORE leaderboard "user:123"      # Get score
```

All operations O(log n). Redis can handle millions of operations/second.

**Sharding**: For billions of users, shard the sorted set across multiple Redis instances. For global top 100, run a periodic aggregation job that merges top-K from each shard.

**Persistence**: Redis AOF or RDB snapshots for durability, or write scores to PostgreSQL for long-term storage and compute from there.

## System Design Problem: Time-Series Data

**Use case**: IoT sensor data, application metrics, financial tick data.

**Access patterns**: 
- Write-heavy with high throughput (millions of events/second)
- Reads are typically range queries: "all values for sensor X between T1 and T2"
- Recent data queried most; old data often aggregated or deleted

**Why standard relational databases struggle**: 
- Constant inserts create index fragmentation
- Time-range queries without proper partitioning do full table scans
- Old data cleanup is expensive

**Purpose-built time-series databases**:
- **InfluxDB**: Schema-on-write, built-in downsampling and retention policies
- **TimescaleDB**: PostgreSQL extension with hypertables (automatic time-based partitioning)
- **Cassandra**: Wide-column model, excellent for time-series when partitioned by (device_id, time_bucket)

**Retention tiers**: Store raw data for 7 days → 1-minute aggregates for 90 days → 1-hour aggregates for 2 years → discard. Implemented via TTL or data lifecycle policies.

## Caching at Scale

**Multi-tier caching**:
- L1: In-process cache (e.g., Caffeine in Java) — sub-millisecond, limited size
- L2: Shared Redis cluster — 1-2ms, large size, shared across instances
- L3: CDN edge cache — for cacheable HTTP responses

**Cache invalidation strategies**:
- **TTL-based**: Simple, eventually consistent, occasional stale reads
- **Event-based invalidation**: Publish events when data changes; consumers invalidate relevant cache keys. Consistent but complex.
- **Cache-aside + versioned keys**: When you update data, write to a new cache key with an incremented version. Old keys expire naturally.

The engineers who do well on database system design questions are those who can reason about trade-offs explicitly: "I'm choosing eventual consistency here because the cost of strict consistency doesn't justify the added complexity for this use case." That kind of explicit reasoning is what separates a good answer from an excellent one.
