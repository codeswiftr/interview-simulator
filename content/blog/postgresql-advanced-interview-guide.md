---
title: "PostgreSQL Advanced Interview Guide: Query Optimization, Indexes, and MVCC"
description: "Deep technical coverage of PostgreSQL internals for senior engineering interviews: EXPLAIN ANALYZE, index types, MVCC, VACUUM, partitioning, and query optimization patterns."
date: "2026-03-20"
category: "Technical Skills"
---

# PostgreSQL Advanced Interview Guide: Query Optimization, Indexes, and MVCC

Senior engineering interviews involving PostgreSQL go well beyond "write a JOIN." Companies using PostgreSQL at scale expect you to understand query planning, index internals, transaction behavior, and maintenance operations. Here is the depth that separates strong candidates from adequate ones.

## EXPLAIN ANALYZE: Reading the Query Plan

`EXPLAIN ANALYZE` executes the query and returns the actual execution plan with timing and row count data. The key metrics to examine:

**Seq Scan vs Index Scan**: A sequential scan reads every row in the table. Appropriate when the planner estimates it will touch a large fraction of rows (the crossover is typically around 5–10% of the table). An index scan is appropriate for selective predicates. An unexpected Seq Scan usually means a missing index, stale statistics, or a predicate that cannot use an index (e.g., applying a function to an indexed column: `WHERE LOWER(email) = 'foo'` cannot use an index on `email`).

**Actual vs Estimated Rows**: A large mismatch indicates stale statistics. Run `ANALYZE tablename` to refresh. If estimates are consistently wrong, examine your `default_statistics_target` — increasing it from the default 100 to 500 for high-cardinality columns often helps.

**Nested Loop vs Hash Join vs Merge Join**: Nested loops are efficient for small outer sets with indexed lookups. Hash joins work well for large unsorted sets. Merge joins require sorted inputs and are efficient when both sides can be sorted cheaply. Forcing a specific join type with `SET enable_hashjoin = off` is sometimes used for debugging but should not appear in production code.

**Buffers**: `EXPLAIN (ANALYZE, BUFFERS)` adds buffer hit/miss information. High read counts indicate missing caching or cold data. Shared hits mean data was in PostgreSQL's buffer cache.

## Index Types

**B-tree** is the default. Supports equality and range queries on orderable types. Covers `=`, `<`, `>`, `BETWEEN`, `LIKE 'prefix%'` (left-anchored patterns only).

**GIN (Generalized Inverted Index)** indexes multiple values per row. Required for full-text search (`tsvector` columns), JSONB containment queries (`@>`, `?`), and array containment operators. Build time is slow; updates are deferred via pending list — `fastupdate` is on by default.

**GiST (Generalized Search Tree)** is an extensible index type supporting nearest-neighbor searches, geometric types, and range types. PostGIS uses GiST for spatial queries.

**Hash indexes** are faster than B-tree for equality-only lookups but do not support range queries and were historically not WAL-logged (fixed in PG 10). Rarely the right choice in practice.

**BRIN (Block Range Index)** stores min/max values for ranges of heap blocks. Extremely small and fast to build. Highly effective for naturally ordered data (timestamps, auto-increment IDs). Useless for randomly distributed data.

**Partial indexes** index only rows matching a WHERE clause: `CREATE INDEX ON orders (customer_id) WHERE status = 'pending'`. Dramatically reduces index size and maintenance cost when queries consistently filter on the same condition.

**Expression indexes**: `CREATE INDEX ON users (LOWER(email))` enables case-insensitive lookups with `WHERE LOWER(email) = $1`.

## MVCC and Transaction Isolation

PostgreSQL uses Multi-Version Concurrency Control. Writers never block readers; each transaction sees a consistent snapshot of the database as of its start time. Each row version carries `xmin` (the transaction that created it) and `xmax` (the transaction that deleted/updated it).

**Isolation levels**: `READ COMMITTED` (default) sees committed data as of each statement start — susceptible to non-repeatable reads. `REPEATABLE READ` sees data as of transaction start — susceptible to phantom reads in most databases, but PostgreSQL's MVCC implementation prevents phantoms here. `SERIALIZABLE` (SSI in PG 9.1+) prevents all anomalies through serializable snapshot isolation.

**Common anomaly interview question**: "What is a phantom read and how does PostgreSQL handle it?" A phantom read occurs when a second read within a transaction returns rows that did not exist during the first read. PostgreSQL's Repeatable Read prevents this because the transaction snapshot is fixed.

## VACUUM and Table Bloat

Dead row versions are not immediately removed — they accumulate until VACUUM processes them. Autovacuum handles this automatically but can lag under heavy write workloads. Signs of VACUUM problems: table bloat (visible via `pg_stat_user_tables.n_dead_tup`), slow sequential scans, and wraparound risk.

**Transaction ID wraparound** is a critical failure mode. PostgreSQL's 32-bit transaction IDs wrap after ~2 billion transactions. Tables with `relfrozenxid` approaching the `autovacuum_freeze_max_age` threshold will be aggressively vacuumed. Monitor `age(datfrozenxid)` in `pg_database`.

**VACUUM FULL** rewrites the entire table, reclaiming space to the OS but requiring an exclusive lock. Use sparingly — it is disruptive. `pg_repack` is the standard production alternative.

## Partitioning

PostgreSQL declarative partitioning (PG 10+) supports range, list, and hash partitioning. Range partitioning on a timestamp column is the most common pattern for time-series data — each partition covers a time range, enabling partition pruning (the planner excludes irrelevant partitions from scans).

```sql
CREATE TABLE events (
  id BIGSERIAL,
  created_at TIMESTAMPTZ NOT NULL,
  payload JSONB
) PARTITION BY RANGE (created_at);

CREATE TABLE events_2026_q1
  PARTITION OF events
  FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
```

Partition pruning requires that your WHERE clause includes the partition key with a constant or stable expression.

## Key pg_stat Views

- `pg_stat_user_tables`: Row counts, sequential and index scan counts, dead tuples, last vacuum
- `pg_stat_user_indexes`: Index usage counts — identify unused indexes
- `pg_stat_activity`: Active queries, wait events, query duration
- `pg_locks`: Lock contention; join with `pg_stat_activity` to identify blocking queries
- `pg_stat_bgwriter`: Buffer writes, checkpoint frequency

**Interview question**: "How would you identify the top 5 slowest queries in a production PostgreSQL instance?" Enable `pg_stat_statements` extension, then query `SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 5`. This is the single most useful diagnostic view.

---
