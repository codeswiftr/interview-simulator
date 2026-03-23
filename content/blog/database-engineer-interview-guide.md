---
title: "Database Engineer Interview Guide: Internals, Query Optimization & Scaling"
description: "Master database engineering interviews — storage engine internals, query execution, indexing deep dive, ACID guarantees, replication patterns, and NewSQL vs. NoSQL tradeoffs."
date: "2026-03-20"
category: "Technical Skills Guides"
---

# Database Engineer Interview Guide: Internals, Query Optimization & Scaling

Database engineering roles at companies like SingleStore, PlanetScale, Neon, Cockroach Labs, or on internal data infrastructure teams require deep knowledge of database internals, query optimization, and distributed systems. Even generalist backend engineers are expected to understand databases deeply at senior levels. This guide covers what database engineering interviews test.

## Storage Engine Internals

Understanding how databases actually store and retrieve data is the foundation:

**B-Tree vs. LSM-Tree**: The two dominant storage engine architectures. B-Trees (PostgreSQL, MySQL InnoDB) are optimized for reads: balanced tree maintains sorted key order for O(log n) point lookups and efficient range scans. LSM-Trees (RocksDB, LevelDB, Cassandra, ScyllaDB) are optimized for writes: append-only memtable flushes to SSTable files, compaction merges periodically. Know the tradeoff: B-Trees have better read performance; LSM-Trees have better write throughput and are more durable (append-only by nature).

**Page layout**: Databases organize storage in fixed-size pages (typically 8KB in PostgreSQL, 16KB in MySQL). A page stores the header, tuple data, and a slot array pointing to tuples. Understanding heap pages vs. index pages matters for storage efficiency discussions.

**WAL (Write-Ahead Log)**: All changes are written to the WAL before being applied to data pages. This ensures durability (replay WAL on crash recovery) and enables replication (streaming WAL to replicas). PostgreSQL's WAL, MySQL's binary log, and SQLite's WAL mode all serve this function.

**MVCC (Multi-Version Concurrency Control)**: PostgreSQL and MySQL/InnoDB implement MVCC to allow readers and writers to proceed concurrently without blocking. Each row has version metadata — readers see a consistent snapshot, writers create new versions. Know how vacuum/garbage collection reclaims old versions and what happens when vacuum falls behind (table bloat).

## Query Planning and Optimization

Query optimizer internals are a senior-level interview topic:

**Query execution pipeline**: Parse → analyze → rewrite → plan → optimize → execute. The optimizer's job is choosing the cheapest execution plan from all equivalent plans. Cost is estimated based on table statistics (row counts, value distributions, index selectivity) stored in the catalog.

**Join algorithms**: Nested loop join (O(n×m), good for small inputs or index-backed inner loop), hash join (O(n+m), requires memory for hash table, good for large unsorted inputs), merge join (O(n log n + m log m), requires sorted inputs, reuses sort for multi-join queries). PostgreSQL's query planner chooses between these based on cost estimates.

**Index selection**: Covering indexes (all columns in the query, including WHERE, JOIN, and SELECT, are in the index — eliminating heap fetches), partial indexes (filter reduces index size), expression indexes (index on `lower(email)`), and composite index column ordering (leftmost prefix rule). Know why an index might not be used (low selectivity, type mismatch, function on indexed column).

**EXPLAIN and EXPLAIN ANALYZE**: Walk through a PostgreSQL EXPLAIN output — understand `Seq Scan` vs. `Index Scan` vs. `Index Only Scan`, `Hash Join` vs. `Nested Loop`, node cost and row estimates vs. actual rows. Knowing how to identify bad estimates (wrong statistics) and trigger re-analysis is a differentiating skill.

## ACID Guarantees and Isolation Levels

**Atomicity**: Transaction either fully commits or fully rolls back. Implemented via undo log/MVCC (PostgreSQL) or rollback segments (Oracle, MySQL).

**Consistency**: The database moves from one valid state to another. Enforced by constraints, triggers, and application-level invariants.

**Isolation levels** (know all four):
- Read Uncommitted: dirty reads allowed — almost never used
- Read Committed: no dirty reads; non-repeatable reads and phantom reads possible — PostgreSQL default
- Repeatable Read: consistent snapshot for transaction duration; phantom reads possible — MySQL InnoDB default
- Serializable: full isolation as if transactions ran serially — highest correctness, lowest throughput

**Real-world concurrency anomalies**: Dirty reads, non-repeatable reads, phantom reads, and write skew (two transactions read overlapping data and both write based on what they read, violating a constraint neither detected). Write skew requires Serializable isolation to prevent.

## Distributed Database Patterns

Modern databases must scale beyond a single node:

**Replication topologies**: Single-leader (primary/replica, PostgreSQL streaming replication), multi-leader (active-active, complex conflict resolution), and leaderless (Cassandra-style, tunable quorums for consistency). Know the failure modes of each.

**Sharding strategies**: Range sharding (contiguous key ranges, enables efficient range queries but causes hot spots), hash sharding (distributes evenly, breaks range queries), and directory sharding (explicit mapping, most flexible, maintenance overhead).

**Consensus protocols**: Raft (etcd, CockroachDB, TiKV) is the readable reference implementation for distributed consensus. Know leader election, log replication, and how Raft handles network partitions. PBFT and Paxos as precursors.

**NewSQL tradeoffs**: CockroachDB and Spanner achieve geo-distributed ACID transactions via 2-phase commit + Paxos consensus. The latency cost of cross-region consensus (50-150ms) is acceptable for write-rarely, read-often global tables. Know when this cost is worth it vs. eventual consistency alternatives.

## Interview Preparation

- Deploy PostgreSQL locally, run `EXPLAIN ANALYZE` on complex queries, and optimize them
- Study the PostgreSQL documentation on vacuuming, MVCC, and index types (GiST, GIN, BRIN)
- Read "Database Internals" by Alex Petrov — the definitive modern textbook
- Build a simple storage engine from scratch (B-Tree or LSM-Tree) to solidify internals
- Practice query optimization with realistic workloads using pgbench

Database engineering rewards the deepest understanding of any engineering discipline. Engineers who combine theoretical foundations with practical performance tuning skills are consistently among the most valuable engineers at data-intensive companies.
