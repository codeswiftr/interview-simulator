---
title: "PostgreSQL Deep Dive Interview Guide"
description: "Advanced PostgreSQL knowledge for backend engineer interviews: MVCC and transaction isolation, index types, query planning, partitioning, replication, and the PostgreSQL-specific features that separate expert users from average ones."
date: "2026-03-19"
category: "Technical Skills Guides"
---

# PostgreSQL Deep Dive Interview Guide

Basic SQL is table stakes for backend engineer interviews. What separates strong candidates is understanding how PostgreSQL actually works — its concurrency model, query planning, indexing internals, and operational characteristics. This guide covers the PostgreSQL depth that shows up in senior backend interviews.

## MVCC: How PostgreSQL Handles Concurrency

PostgreSQL uses Multi-Version Concurrency Control (MVCC) — the foundation of its concurrency model. Rather than locking rows for reads, PostgreSQL creates new versions of rows on update.

When a row is updated, PostgreSQL creates a new row version (tuple) with the new data and marks the old version as deleted (setting `xmax`). Each transaction sees a consistent snapshot of the database as of its start time — it reads only row versions that were committed before the transaction began.

**What this means for interviews**:
- Reads don't block writes, writes don't block reads (the key advantage over lock-based systems)
- Long-running transactions can see stale data (they're reading an old snapshot)
- Dead tuples accumulate (old versions of updated/deleted rows) and must be cleaned up by VACUUM
- VACUUM: PostgreSQL's background process that reclaims dead tuple space and updates visibility maps. AUTOVACUUM handles this automatically, but tuning autovacuum is important for high-write tables.

## Transaction Isolation Levels

PostgreSQL supports four isolation levels with distinct behaviors:

**Read Committed** (default): Each statement within a transaction sees data committed before that statement started. Two consecutive reads in the same transaction can return different results (non-repeatable read). Usually the right choice for OLTP workloads.

**Repeatable Read**: All statements in a transaction see data committed before the transaction started. Prevents non-repeatable reads. May still see phantom rows in other databases — PostgreSQL's implementation prevents phantoms too using snapshot isolation.

**Serializable**: Full serializable isolation using SSI (Serializable Snapshot Isolation). Transactions execute as if they ran sequentially. Higher overhead but necessary for financial accuracy (bank transfer correctness, inventory). PostgreSQL's SSI implementation is efficient enough to use in practice.

Interview question: "A bank transfer requires debiting one account and crediting another atomically. What isolation level do you use?" The answer involves wrapping both in a transaction (guaranteed atomicity at any isolation level), but Serializable is the right level when you need to prevent anomalies from concurrent transfers affecting the same accounts.

## Indexing: Beyond B-Trees

Most engineers know about B-tree indexes. PostgreSQL has several other index types worth knowing:

**B-tree** (default): Ordered data, supports equality and range queries, most operators. The right choice for most columns.

**GIN (Generalized Inverted Index)**: For composite values where you're searching for elements within the value. Full-text search (`tsvector`/`tsquery`), JSONB containment (`@>`), array containment. More expensive to update than B-tree, faster for containment searches.

**GiST (Generalized Search Tree)**: Extensible index supporting geometric operations, full-text search (alternative to GIN), range types. Used for PostGIS geographic queries.

**BRIN (Block Range Index)**: Stores min/max values per block range, not per row. Tiny size, fast to create, but only effective for naturally ordered columns (timestamp, sequential IDs). Excellent for time-series data where rows are physically ordered by time.

**Partial indexes**: Index only rows matching a condition. `CREATE INDEX ON orders (user_id) WHERE status = 'pending'` — only index pending orders. Smaller and faster than full-index when queries always include the condition.

**Expression indexes**: Index on an expression, not a column. `CREATE INDEX ON users (lower(email))` — enables case-insensitive lookups on email without full-table scans.

## Query Planning: Reading EXPLAIN

Every backend engineer working with PostgreSQL needs to read `EXPLAIN ANALYZE` output:

**Seq Scan**: Full table scan. Expected for small tables or when a large fraction of rows is returned. A sign of missing index when unexpected.

**Index Scan**: Uses an index to find rows, then fetches from heap. Good for selective queries.

**Index Only Scan**: Uses covering index (all needed columns in the index). Doesn't touch the heap.

**Bitmap Index Scan + Bitmap Heap Scan**: Used when multiple indexes can be combined (OR conditions) or when many rows match. Builds a bitmap of matching TIDs, then fetches from heap.

**Hash Join vs. Nested Loop vs. Merge Join**: Hash join materializes the smaller table, probes with rows from the larger — good for large joins on equality. Nested loop is efficient for small outer tables with index on inner. Merge join requires both sides sorted — good for large sorted inputs.

Key numbers: `rows=X` shows estimated rows (compare to `actual rows=Y` for planner accuracy). High discrepancy means stale statistics — run `ANALYZE`.

## JSONB and Semi-Structured Data

PostgreSQL's `jsonb` type stores JSON as binary (indexed, fast containment queries) vs. `json` (text, stored as-is, exact whitespace/key order preserved).

When to use JSONB: flexible schema fields (varying attributes per row), storing configuration objects, EAV (Entity-Attribute-Value) patterns. When not to: when you regularly query specific keys and know the schema — use typed columns instead.

GIN indexes on JSONB enable fast containment queries (`@>`) and key existence (`?`, `?|`, `?&`). Without an index, JSONB queries scan all rows.

## Partitioning

Table partitioning splits a large table into smaller physical tables (partitions) while presenting a unified logical table. PostgreSQL supports:

**Range partitioning**: by date range (`created_at`). Most common for time-series data. Older partitions can be dropped cleanly (no VACUUM needed for deleted data).

**List partitioning**: by discrete values (region, tenant_id for multi-tenancy).

**Hash partitioning**: by hash of a column — even distribution.

Partition pruning: the query planner eliminates irrelevant partitions when the WHERE clause includes the partition key. A query for `WHERE created_at > '2026-01-01'` only scans 2026 partitions, not the entire table.

## Replication

**Streaming replication** (physical): replicas receive WAL (Write-Ahead Log) stream and replay it. Near-real-time lag. Replica is byte-for-byte identical to primary. Used for read scaling and failover.

**Logical replication**: replicate individual tables or subsets. Can replicate between different PostgreSQL versions or architectures. Used for zero-downtime major version upgrades, cross-region data distribution, and read replicas with selective data.

The practical question: "How do you promote a replica to primary with minimal downtime?" With streaming replication and a tool like Patroni (or pg_auto_failover), this is automatic. Manually: stop writes to primary, wait for replica to catch up, promote replica (`pg_promote()`), update application connection string.

Understanding MVCC and VACUUM is what most engineers miss — that knowledge signals genuine PostgreSQL production experience.
