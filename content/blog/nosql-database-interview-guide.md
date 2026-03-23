---
title: "NoSQL Database Interview Guide: MongoDB vs Cassandra vs DynamoDB vs Redis"
description: "A practical guide to NoSQL database interview questions — when to choose MongoDB, Cassandra, DynamoDB, or Redis, and how to explain your reasoning to interviewers."
category: "Backend Engineering"
date: "2026-03-19"
tags: ["NoSQL", "MongoDB", "Cassandra", "DynamoDB", "Redis", "databases", "system design"]
---

# NoSQL Database Interview Guide: MongoDB vs Cassandra vs DynamoDB vs Redis

One of the most common system design interview pitfalls is reaching for "a database" without articulating which database and why. For NoSQL systems specifically, the choice between MongoDB, Cassandra, DynamoDB, and Redis isn't arbitrary — each is optimized for fundamentally different access patterns. Getting this right in interviews signals genuine backend depth.

## Why NoSQL Exists: The Motivation Matters

Before discussing specific databases, interviewers want to know you understand *why* NoSQL databases emerged. Relational databases excel at structured data with complex relationships and strong consistency requirements. But they struggle with:

- **Horizontal scaling** — sharding a relational database is difficult and operationally expensive
- **Schema flexibility** — evolving a schema on a large table can require expensive migrations
- **High write throughput** — traditional RDBMS architectures weren't built for millions of writes per second
- **Specific access patterns** — sometimes you just need fast key-value lookups, not full SQL

NoSQL databases trade some of SQL's guarantees (ACID transactions, rich query language) for gains in scale, flexibility, or performance. The right database depends entirely on your access patterns and consistency requirements.

## MongoDB: Document Store for Flexible Schema Workloads

**What it is:** MongoDB stores JSON-like documents in collections. Documents can have nested structures and don't require a fixed schema. It supports rich queries including range queries, full-text search, and aggregation pipelines.

**Best for:**
- Applications with flexible, evolving schemas (product catalogs where each product has different attributes)
- Hierarchical data that maps naturally to documents (a user with an embedded array of addresses)
- Applications that need rich queries without committing to a relational model
- Rapid iteration where the data model changes frequently

**Weaknesses:**
- Not ideal for highly relational data that requires joins across many collections
- Write consistency at scale requires careful configuration of write concerns and replica sets
- Not built for extremely high write throughput (Cassandra beats it here)

**Interview framing:** Propose MongoDB when the data model is hierarchical and the query patterns are moderately complex. "I'd use MongoDB for the product catalog because each product category has different attributes — a TV has resolution and refresh rate, while a shirt has size and color. A document model handles this without a complex EAV schema."

## Apache Cassandra: Distributed Column Store for High Write Throughput

**What it is:** Cassandra is a wide-column store optimized for write-heavy workloads at massive scale. It uses consistent hashing for data distribution, has no single point of failure, and is designed to run across multiple datacenters natively.

**Best for:**
- Time-series data (IoT sensor readings, application logs, metrics)
- High write throughput with eventual consistency tolerance
- Geographically distributed data with multi-datacenter replication
- Workloads where you can define query patterns upfront (Cassandra data modeling is query-driven)

**Key constraint:** Cassandra data modeling requires knowing your queries before designing your tables. Unlike MongoDB or SQL, you can't easily query data in ad hoc ways. This is a fundamental difference that interviewers probe.

**Weaknesses:**
- No joins, no ACID transactions across partitions
- Secondary indexes are limited and often discouraged
- Schema changes require careful planning to avoid performance degradation

**Interview framing:** "For storing IoT sensor readings from a million devices, I'd use Cassandra. The write throughput is massive, queries are always time-windowed by device ID, and we can tolerate eventual consistency. The access pattern fits Cassandra's design perfectly — we know at schema design time that we'll always query by `(device_id, time_range)`."

## DynamoDB: Managed Key-Value and Document Store on AWS

**What it is:** DynamoDB is AWS's fully managed NoSQL database. It offers single-digit millisecond performance at any scale, with automatic scaling and no operational overhead. Data is accessed via partition key (and optional sort key).

**Best for:**
- Applications already on AWS that need low-latency key-value access
- Workloads with unpredictable scale that need auto-scaling without operations burden
- Simple access patterns: get by primary key, range query on sort key
- Gaming leaderboards, session stores, e-commerce shopping carts

**Key concept — access patterns drive design:** Like Cassandra, DynamoDB forces query-first data modeling. The choice of partition key is critical: a bad partition key creates hot partitions that degrade performance for everyone.

**DynamoDB-specific features worth knowing:**
- **GSI (Global Secondary Index):** Allows queries on non-primary-key attributes, with eventual consistency
- **DAX:** In-memory cache for DynamoDB with microsecond response times
- **Streams:** Change data capture for triggering Lambda functions on item changes
- **Single-table design:** Advanced pattern where all entity types live in one table, differentiated by key structure

**Interview framing:** "For a session store at scale, DynamoDB is the natural choice on AWS. We get sub-millisecond reads, automatic scaling for traffic spikes, and no servers to manage. The access pattern — get session by token, update TTL — maps directly to DynamoDB's key-value model."

## Redis: In-Memory Data Structure Store for Cache and Real-Time Use Cases

**What it is:** Redis stores data in memory, making it extremely fast (sub-millisecond latency). It supports rich data structures: strings, hashes, lists, sets, sorted sets, and more. Data can be persisted to disk, but Redis is primarily used as a cache or for workloads that require real-time performance.

**Best for:**
- Caching (session data, computed results, API responses)
- Real-time leaderboards (sorted sets with O(log n) range queries)
- Rate limiting (atomic increment operations)
- Pub/sub messaging (low-latency message fanout)
- Distributed locks (with SETNX and expiry)

**Key limitation:** Memory is expensive. Redis is not suitable as a primary database for large datasets. It shines as a complementary layer to a persistent database.

**Interview framing:** "I'd put Redis in front of the database for the user profile service. Profiles are read far more than they're written, and they fit easily in memory. We cache on read, invalidate on write, and the database becomes the source of truth. Cache hit rates of 90%+ dramatically reduce database load."

## Choosing the Right Database: A Decision Framework

Interviewers love asking: "Which database would you use and why?" Here's a concise decision framework:

| Need | Database |
|------|----------|
| Flexible schema, rich queries | MongoDB |
| Extreme write throughput, time-series | Cassandra |
| Managed, AWS-native, auto-scaling | DynamoDB |
| Sub-millisecond latency, caching | Redis |
| Complex relationships, ACID transactions | PostgreSQL (not NoSQL) |

The key to answering these questions well is never saying "I'd use MongoDB" without following up with "because the access patterns are X and the consistency requirements are Y."

## Common Interview Questions and Strong Answers

**"How would you design a leaderboard for a multiplayer game?"**
Redis sorted sets. Each player is a member with their score. `ZADD`, `ZRANK`, and `ZRANGE` give you real-time rankings in O(log n). For persistence, sync periodically to a relational DB.

**"How would you store and query time-series metrics from 10,000 servers?"**
Cassandra, with a table partitioned by `(server_id, date)` and a sort key on timestamp. Write throughput is handled natively, and queries by server and time range map directly to the data model.

**"How would you cache database query results?"**
Redis with a TTL. Compute the cache key from the query parameters. On cache miss, query the database and populate cache. On writes, invalidate affected cache keys. Discuss cache stampede protection (probabilistic early expiration) for high-traffic keys.

Understanding these databases as tools — each with specific strengths and failure modes — is what separates engineers who pass system design interviews from those who don't.
