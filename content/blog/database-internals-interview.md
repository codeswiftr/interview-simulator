---
title: "Database Internals: What Senior Engineers Know About How Databases Work"
description: "Database internals for senior engineer interviews — B-tree vs. LSM-tree storage engines, WAL, MVCC, query planning, index types, and why these details matter in system design discussions."
date: "2026-03-20"
category: "System Design"
---

# Database Internals: What Senior Engineers Know About How Databases Work

Senior engineer interviews often probe database internals — not to test trivia, but to verify that you can make informed decisions about indexes, storage engines, and query patterns. Understanding how a database physically stores and retrieves data changes how you design schemas, choose indexes, and debug performance problems.

## Storage Engines: B-Tree vs. LSM-Tree

**B-Tree (PostgreSQL, MySQL InnoDB, SQLite):**

Data is stored in a balanced tree of fixed-size pages (typically 4KB or 8KB). Leaf pages contain the actual data; internal pages contain keys and child pointers. All lookups traverse from root to leaf in O(log n).

Writes: update pages in-place. Each write touches potentially the leaf page and any parent pages that need updating. Good read performance (data is sorted, range scans are efficient), moderate write performance, high write amplification.

**LSM-Tree (LevelDB, RocksDB, Apache Cassandra, ScyllaDB):**

Writes go first to an in-memory structure (MemTable). When the MemTable fills, it's flushed to an immutable sorted file on disk (SSTable). Reads check the MemTable first, then SSTables in order. Background compaction merges SSTables to reclaim space and maintain read performance.

Writes: always sequential (append-only) — excellent write throughput. Reads: may require checking multiple SSTables — worse read performance than B-trees for point queries, offset by Bloom filters.

**Interview question:** "When would you choose a B-tree based database vs. an LSM-tree based one?"

B-tree: read-heavy workloads, OLTP, strong consistency requirements. LSM-tree: write-heavy workloads, time-series data, event logs, NoSQL use cases.

## WAL: Write-Ahead Logging

PostgreSQL and most ACID databases use a Write-Ahead Log. The principle: before modifying any data page, write the change to the WAL (an append-only log). On crash recovery, replay the WAL to reconstruct the committed state.

Why append-only? Sequential disk writes are much faster than random writes. Writing to the WAL first (fast sequential) then updating the data pages (slower random) separates the latency-sensitive commit path from the I/O-intensive data update.

**WAL and durability:** A transaction is durable once its WAL entry is flushed to disk (`fsync`). PostgreSQL's `synchronous_commit=on` flushes the WAL synchronously. `synchronous_commit=off` risks losing committed transactions on crash but improves throughput.

**WAL and replication:** Streaming replication works by shipping WAL records from primary to replica. The replica applies WAL records to maintain a synchronized copy. This is why logical vs. physical replication is a meaningful distinction — physical replication ships WAL bytes; logical replication ships logical change events.

## MVCC: Multi-Version Concurrency Control

PostgreSQL uses MVCC to allow readers and writers to operate without blocking each other. Each row has a `xmin` (transaction that created it) and `xmax` (transaction that deleted it, or 0 if still live).

When a transaction reads a row, it sees only rows where `xmin` is a committed transaction that started before the current transaction, and `xmax` is either 0 or an uncommitted transaction. This provides snapshot isolation — readers see a consistent snapshot of the database without holding any locks.

Writes don't overwrite rows in-place. An UPDATE creates a new row version and marks the old version as deleted (sets `xmax`). Old versions are cleaned up by VACUUM.

**Why this matters in interviews:** Understanding MVCC explains:
- Why `SELECT FOR UPDATE` is needed for pessimistic locking
- Why long-running transactions cause table bloat (old versions accumulate)
- Why `VACUUM` is critical for PostgreSQL performance
- Why read-heavy workloads on PostgreSQL are extremely efficient

## B-Tree Index Internals

When you `CREATE INDEX ON users (email)`, PostgreSQL creates a B-tree containing email values as keys and heap tuple locations (ctid) as values, sorted by email. A query `WHERE email = 'x'` traverses the B-tree to find the ctid, then fetches the actual row from the heap.

**Index-only scans:** If all queried columns are in the index, PostgreSQL can skip the heap fetch entirely. `CREATE INDEX ON users (email) INCLUDE (name)` makes `SELECT name WHERE email = 'x'` an index-only scan.

**Partial indexes:** `CREATE INDEX ON orders (user_id) WHERE status = 'pending'` — small index covering only pending orders. Fast queries on pending orders, doesn't waste space on completed ones.

**Covering index selection:** The most important decision in index design. Index should cover the query's WHERE clauses and ideally all SELECTed columns. Composite index column order matters: high-selectivity columns first, equality conditions before range conditions.

## Query Planning: EXPLAIN ANALYZE

Senior engineers use `EXPLAIN ANALYZE` to understand query execution. Key terms:

```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 42 AND created_at > '2025-01-01';
```

- **Seq Scan:** Full table scan. Red flag if table is large and this is a frequent query.
- **Index Scan:** Uses an index, then fetches heap pages. Good.
- **Index Only Scan:** Uses index, no heap fetch. Best.
- **Nested Loop:** Inner query executed once per outer row. Good for small outer loops.
- **Hash Join:** Builds hash table from smaller relation, probes with larger. Good for large equijoins.
- **Merge Join:** Both sides must be sorted. Good when both sides have matching indexes.
- **Actual Rows vs. Estimated Rows:** Large discrepancy indicates stale statistics. Run `ANALYZE`.

## Connection Pooling

Database connections are expensive to create (TCP handshake, authentication, process fork). Connection poolers (PgBouncer, pgpool-II) maintain a pool of connections to the database and reuse them across application requests.

**PgBouncer modes:**
- **Session pooling:** One DB connection per client session. Least restrictive.
- **Transaction pooling:** DB connection held only for the duration of a transaction. Most efficient. Incompatible with prepared statements and `SET` commands.
- **Statement pooling:** Connection returned after each statement. Most efficient but most restrictive.

In most web application deployments, PgBouncer in transaction mode between the application and PostgreSQL dramatically improves the database's effective connection capacity.

## What to Know for System Design Interviews

When discussing persistence in system design:
- Justify your database choice (PostgreSQL for transactional, Cassandra/DynamoDB for high-write, Redis for cache)
- Mention indexing strategy and what queries it supports
- Discuss connection pooling for high-concurrency services
- Know when to use read replicas (read-heavy) vs. sharding (write-heavy at scale)
- Understand that MVCC means readers don't block writers — relevant for high-concurrency design

These internals turn vague "use a database" answers into precise architectural reasoning.
