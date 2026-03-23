---
title: "Database Concepts for Software Engineering Interviews"
description: "Master database fundamentals for technical interviews. Covers SQL vs NoSQL trade-offs, indexing strategies, ACID transactions, normalization, sharding, and replication patterns."
date: "2025-10-25"
category: "Technical Skills Guides"
---

# Database Concepts for Software Engineering Interviews

Database knowledge is tested in almost every backend or system design interview. You don't need to be a DBA, but you need a solid mental model of how databases work, what trade-offs different choices involve, and how to design schemas that scale.

## SQL vs. NoSQL: The Core Trade-off

The most common database question in interviews is "when would you use SQL vs. NoSQL?" The answer depends on what you're optimizing for.

**SQL (Relational) Databases** (PostgreSQL, MySQL, SQLite):
- Strong ACID guarantees
- Complex queries with JOINs
- Well-understood schema enforcement
- Excellent for transactional workloads with structured data
- Scales vertically well; horizontal scaling is more complex

**NoSQL Databases** (MongoDB, DynamoDB, Cassandra, Redis):
- Flexible schema (document, key-value, column-family, graph)
- Horizontal scaling built-in
- Trade ACID for performance and scale
- Better for specific access patterns (high-volume key-value lookups, wide-column time series)

**Interview guidance**: "I default to PostgreSQL for most use cases — it's incredibly capable at scale, and the ACID guarantees simplify application logic. I'd reach for NoSQL when I have a specific access pattern that SQL doesn't serve well — like Cassandra for time-series data with high write throughput, or Redis for caching and session storage."

## Indexing: The Most Important Performance Tool

Indexes speed up reads at the cost of write performance and storage.

**B-Tree index** (default): Ordered tree structure. Supports range queries, exact match, prefix match. Most common index type.

**Hash index**: Extremely fast for exact equality lookups. Doesn't support range queries.

**Composite index**: Index on multiple columns. Column order matters: `(last_name, first_name)` speeds up queries filtering on `last_name` or `(last_name, first_name)`, but not just `first_name`.

**Covering index**: An index that contains all columns needed by a query — the query can be satisfied from the index alone without touching the main table.

**When to add an index**: When a query is slow, run `EXPLAIN` to see if it's doing a sequential scan. Add an index on the column(s) being filtered or sorted. Don't over-index — every index slows down writes.

**Index pitfalls**:
- `SELECT *` with joins — often doesn't use indexes effectively
- Functions on indexed columns: `WHERE YEAR(created_at) = 2024` won't use an index on `created_at`; use `WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31'`
- Low-cardinality columns (like a boolean `is_active`) — indexes are less useful

## ACID Transactions

**Atomicity**: A transaction is all-or-nothing. If any part fails, the entire transaction is rolled back.

**Consistency**: A transaction brings the database from one valid state to another. Foreign key constraints, unique constraints, and check constraints are all consistency mechanisms.

**Isolation**: Concurrent transactions don't interfere with each other. Isolation levels:
- **READ UNCOMMITTED**: Can see dirty reads (uncommitted data from other transactions) — almost never used
- **READ COMMITTED**: No dirty reads; but non-repeatable reads possible (same query returns different results within a transaction)
- **REPEATABLE READ**: No dirty or non-repeatable reads; phantom reads possible (new rows appear in a re-run query)
- **SERIALIZABLE**: Full isolation — transactions execute as if serial; highest performance cost

**Durability**: Once a transaction is committed, it persists even if the system crashes. Implemented via write-ahead logging (WAL).

**Interview answer**: "For most transactional applications, READ COMMITTED is the right isolation level — it prevents dirty reads without the overhead of SERIALIZABLE. For financial transactions where we need strict consistency, SERIALIZABLE."

## Schema Design and Normalization

**Normalization** removes data redundancy:
- **1NF**: Each column contains atomic values; no repeating groups
- **2NF**: No partial dependencies on composite primary key
- **3NF**: No transitive dependencies (non-key columns don't depend on other non-key columns)

**When to denormalize**: In high-read workloads, denormalization (adding redundant data) reduces JOIN operations at the cost of write complexity. Read-heavy reporting tables often store aggregated data rather than normalizing everything.

## Sharding and Replication

**Replication** copies data across multiple nodes:
- **Primary-Replica**: Writes go to primary; reads distributed across replicas. Good for read-heavy workloads. Data eventually consistent on replicas.
- **Multi-Primary**: Writes go to multiple nodes. Conflict resolution required. Used for geographic distribution.

**Sharding** partitions data across multiple database nodes:
- **Horizontal sharding**: Distribute rows across nodes. Each node stores a subset of rows for a given table.
- **Shard key selection is critical**: A poor shard key creates hotspots. User ID is common. Time-based keys cause hotspots (all writes to the latest shard).
- **Cross-shard queries**: Joins across shards are expensive and often impossible — design your access patterns to avoid them.

## Caching Patterns

**Cache-aside**: Application checks cache first; on miss, reads from DB and populates cache. Most flexible pattern.

**Write-through**: Write to cache and DB simultaneously. Cache always consistent; write latency higher.

**Write-behind (write-back)**: Write to cache; async write to DB. Lowest latency; risk of data loss on cache failure.

**Eviction policies**: LRU (Least Recently Used) — evict the item least recently accessed. LFU — evict the least frequently accessed. TTL — expire based on time.

Database design questions in system design interviews are less about memorizing SQL syntax and more about demonstrating you understand trade-offs. The best answers explain why you'd make specific choices given the system's requirements — not just which tools exist.
