---
title: "Database Design in System Design Interviews: Choosing and Scaling Data Stores"
description: "How to answer database design questions in system design interviews — SQL vs NoSQL decision framework, sharding strategies, replication patterns, ACID vs BASE, indexing decisions, and when to use specialized stores (Redis, Elasticsearch, Cassandra)."
date: "2026-03-20"
category: "System Design"
---

# Database Design in System Design Interviews: Choosing and Scaling Data Stores

Database selection and design is a core skill in system design interviews. Interviewers probe whether you can match data characteristics to the right storage technology, design schemas that scale, and reason about consistency tradeoffs. Here's the framework.

## The SQL vs NoSQL Decision

This question comes up constantly. The honest answer: start with SQL (PostgreSQL), move to NoSQL only when you have a specific reason.

**Choose SQL when:**
- Data has relationships (users have orders have items)
- You need ACID transactions across multiple records
- Your schema is relatively stable
- Your scale is under ~10M rows per table on a single server
- You need ad-hoc queries and joins

**Choose NoSQL when:**
- Horizontal scaling is required and your access patterns are simple (key lookups)
- Schema-less data (user-generated JSON, event data with varying fields)
- Extremely high write throughput (time-series, IoT, click streams)
- Specific data models (documents, graphs, wide-column, key-value)

The most common mistake: choosing NoSQL because it "scales better" without a specific reason. PostgreSQL handles millions of users and billions of rows with proper indexing and read replicas.

## Sharding Strategies

When a single database node can't handle the load, shard.

**Horizontal sharding (range-based):** Partition by value range (user IDs 0-10M on shard 1, 10M-20M on shard 2). Simple but creates hotspots if data distribution is uneven or if access patterns favor recent data (e.g., time-series range sharding will make the latest shard a hotspot).

**Hash sharding:** Hash the partition key, modulo number of shards. Distributes evenly. Drawback: resharding requires moving all data (mitigated by consistent hashing).

**Consistent hashing:** Arrange shard ranges on a ring. Adding a shard only requires moving 1/N of data, not all data. Used by Cassandra, DynamoDB, and many distributed systems.

**Geographic sharding:** Data lives in the shard closest to the user. EU user data on EU shards. Useful for data residency compliance and latency.

**Shard key selection is critical:** A bad shard key creates hotspots. User ID is a good shard key (distributes evenly). Timestamp is a bad shard key for append-heavy workloads (all recent writes hit the latest shard).

## Replication Patterns

**Primary-replica (master-slave):** Writes go to primary, replicated to replicas (async or sync). Reads distributed across replicas. Good for read-heavy workloads. Failover: promote a replica to primary (may lose some data if async replication lags).

**Synchronous vs asynchronous replication:** Synchronous = write isn't acknowledged until replicas confirm. No data loss but higher write latency. Asynchronous = primary acknowledges immediately, replicas catch up. Low latency but risk of data loss on failure.

**Multi-primary:** All nodes accept writes. Requires conflict resolution when two primaries accept conflicting writes. Complex but enables higher write throughput and availability.

**Read-your-writes consistency:** After writing, a user should see their write when they read. Hard with async replication — you might read from a replica that hasn't received the write yet. Solutions: route reads for the same user to the same replica, read from primary for a brief window after write, use synchronous replication for critical data.

## ACID vs BASE

**ACID (SQL databases):** Atomicity, Consistency, Isolation, Durability. All-or-nothing transactions, strong consistency, safe concurrent access.

**BASE (many NoSQL databases):** Basically Available, Soft state, Eventual consistency. Prioritizes availability over consistency. Writes accepted and propagated asynchronously — briefly you may see stale data.

The CAP theorem: in a distributed system, you can only guarantee two of: Consistency, Availability, Partition tolerance. Since network partitions happen, you choose CA (traditional RDBMS, in practice), CP (Zookeeper, HBase), or AP (Cassandra, DynamoDB, Riak).

Interview nuance: CAP is often oversimplified. Most systems are "tunable" — Cassandra lets you choose consistency level per operation (ONE → QUORUM → ALL). Design for the right tradeoff given your requirements, not a fixed CAP choice.

## Indexing Design

Indexes speed reads at the cost of write overhead. Common interview discussion:

**Composite indexes:** An index on (user_id, created_at DESC) serves "get a user's recent items" queries efficiently. The order of columns matters — the index is useful for queries that filter on the leading column(s).

**Covering indexes:** Include all columns needed for a query in the index. The query can be satisfied from the index alone without accessing the main table ("index-only scan"). Faster at the cost of larger index size.

**When NOT to index:** Low-cardinality columns (boolean, status with 3 values) where index scans aren't selective. Tables with very high write rates where index maintenance is a bottleneck. Rarely-queried columns.

**Index types:** B-tree (default, for equality and range queries), Hash (equality only, faster), GIN (full-text search, JSON), BRIN (time-series data on append-only tables, very small).

## Specialized Data Stores

**Redis:** In-memory key-value store. Use for: caching frequently-read data, session storage, leaderboards (sorted sets), rate limiting counters, pub-sub messaging, distributed locks. Not for: primary data storage (data fits in RAM limitation), complex queries.

**Elasticsearch:** Full-text search and analytics. Use for: search (inverted index), log aggregation and analysis, faceted search with aggregations. Not for: primary data storage, transactional updates (eventual consistency, no ACID).

**Cassandra:** Wide-column, AP system. Use for: time-series data, IoT sensor data, user activity logs, any append-heavy high-throughput workload. Queries must match your data model (designed around access patterns, not normalization).

**ClickHouse/BigQuery:** Columnar analytics databases. Use for: analytical queries over large datasets, data warehousing, reporting. Not for: OLTP (transactional workloads).

## Database Design Checklist for Interviews

When asked to design a database for a system:
1. Identify the read/write access patterns — what queries will run most often?
2. Model the data — what are the entities and relationships?
3. Choose the right store — SQL for relational OLTP, specialized for specific needs
4. Design the schema — normalize appropriately, choose data types carefully (BIGINT for IDs, DECIMAL for money, TIMESTAMPTZ for time)
5. Design indexes — cover the common query patterns
6. Plan for scale — sharding strategy, read replicas
7. Address consistency requirements — what can be eventually consistent vs must be strongly consistent?

