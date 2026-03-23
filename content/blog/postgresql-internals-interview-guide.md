---
title: "PostgreSQL Internals Interview Guide"
description: "Database internals questions that appear in senior engineering interviews — MVCC, index types, query planning, connection pooling, and WAL."
date: "2026-03-19"
tags: ["postgresql", "databases", "interview-prep", "backend", "internals"]
---

## PostgreSQL Internals Interview Guide

Senior backend roles at fintech companies, SaaS platforms, and data-heavy startups consistently include PostgreSQL internals questions. These aren't trivia — interviewers use them to distinguish engineers who tune production systems from those who only write queries. This guide covers the five areas that appear most frequently, with the depth interviewers expect.

---

## MVCC: How PostgreSQL Handles Concurrent Reads and Writes

Multi-Version Concurrency Control is PostgreSQL's answer to the classic readers-writers problem. Instead of locking rows during writes, Postgres keeps multiple versions of each row simultaneously.

Every row has two hidden system columns: `xmin` (the transaction ID that inserted it) and `xmax` (the transaction ID that deleted or updated it). When a transaction reads a row, it checks whether the row's version is visible based on its snapshot — a consistent view of which transactions were committed at query start.

```sql
-- See the hidden MVCC columns
SELECT xmin, xmax, ctid, id, name FROM users WHERE id = 1;
```

**What this means in practice:**

- A `SELECT` never blocks a concurrent `UPDATE` on the same row.
- An `UPDATE` actually inserts a new row version and marks the old one with `xmax`.
- Dead row versions accumulate until `VACUUM` reclaims them.

The interview follow-up is almost always: *"What happens if VACUUM doesn't run?"* The answer is table bloat and transaction ID wraparound — a hard limit at ~2 billion transactions that can take down a database if ignored. Autovacuum handles this automatically, but high-write tables need tuned autovacuum settings.

```sql
-- Check for table bloat and dead tuples
SELECT relname, n_dead_tup, n_live_tup, last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

Fintech companies ask MVCC questions because they run high-concurrency transactional workloads. Understanding isolation levels — `READ COMMITTED` vs `REPEATABLE READ` vs `SERIALIZABLE` — follows directly from MVCC knowledge.

---

## Index Types: B-tree, GIN, GiST, and BRIN

The default `CREATE INDEX` creates a B-tree. Knowing when not to use B-tree separates mid-level from senior engineers.

**B-tree** works for equality, range queries, and sorting on scalar types. It is the right choice for 90% of cases.

```sql
CREATE INDEX idx_orders_created_at ON orders (created_at);
-- Supports: WHERE created_at > '2026-01-01', ORDER BY created_at
```

**GIN (Generalized Inverted Index)** indexes composite values where you search for elements within them — arrays, JSONB, full-text search. Each element in the value gets its own entry pointing back to the row.

```sql
CREATE INDEX idx_products_tags ON products USING GIN (tags);
-- Supports: WHERE tags @> ARRAY['electronics', 'sale']

CREATE INDEX idx_docs_search ON documents USING GIN (to_tsvector('english', body));
-- Supports: WHERE to_tsvector('english', body) @@ to_tsquery('postgresql')
```

GIN writes are slower than B-tree because every element in an array or JSONB document creates index entries. Use `fastupdate = on` (the default) to buffer writes.

**GiST (Generalized Search Tree)** handles geometric data, ranges, and nearest-neighbor queries. It trades some precision for flexibility — it can produce false positives, requiring a recheck.

```sql
CREATE INDEX idx_locations_point ON locations USING GIST (coordinates);
-- Supports: WHERE coordinates <-> point(40.7, -74.0) < 10  (within 10 units)

CREATE INDEX idx_reservations_range ON reservations USING GIST (daterange(start_date, end_date));
-- Supports: WHERE daterange(start_date, end_date) && '[2026-03-01, 2026-03-31)'
```

**BRIN (Block Range Index)** stores min/max values for contiguous blocks of disk pages. It is tiny — sometimes 1000x smaller than B-tree — but only works when column values correlate with physical storage order.

```sql
CREATE INDEX idx_events_timestamp ON events USING BRIN (created_at);
-- Works well when rows are inserted in timestamp order (append-only tables)
-- Useless if rows are inserted out of order
```

The BRIN question in interviews: *"Why would you pick BRIN over B-tree for a 500GB events table?"* Answer: if the table is append-only and `created_at` correlates with insertion order, BRIN occupies kilobytes vs gigabytes for B-tree, with acceptable query performance for range scans.

---

## Query Planning: Reading EXPLAIN ANALYZE

`EXPLAIN ANALYZE` executes the query and returns actual vs estimated row counts, execution time, and the plan tree.

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT u.email, COUNT(o.id)
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE u.created_at > '2026-01-01'
GROUP BY u.email;
```

Key numbers to interpret:

| Field | What it means |
|-------|---------------|
| `rows=X` (estimated) | Planner's guess based on statistics |
| `actual rows=Y` | What actually came back |
| `Buffers: hit=N` | Pages served from shared_buffers (cache) |
| `Buffers: read=N` | Pages read from disk |

A large gap between estimated and actual rows signals stale statistics. Fix with `ANALYZE tablename` or by reducing `default_statistics_target`.

**Seq scan vs index scan:** A sequential scan reads every page. The planner chooses it when fetching a large percentage of rows — typically over 5-10% — because random I/O for index lookups becomes more expensive than sequential I/O. If you see a seq scan on a column you indexed, the planner may be right. Force the issue only after confirming with `EXPLAIN (ANALYZE, BUFFERS)`.

```sql
-- Common planner hint for testing (not production tuning)
SET enable_seqscan = off;
EXPLAIN ANALYZE SELECT * FROM orders WHERE status = 'pending';
SET enable_seqscan = on;
```

Data-heavy companies — analytics platforms, reporting tools — ask about nested loop vs hash join vs merge join. Hash joins win for large unsorted inputs with enough `work_mem`. Nested loops win when the outer side is small and the inner side has a good index.

---

## Connection Pooling with PgBouncer

PostgreSQL processes are heavy — each connection forks a backend process consuming ~5-10 MB. A 500-connection application can exhaust memory before query load becomes a concern.

PgBouncer sits between the application and Postgres, maintaining a small pool of actual database connections.

Three pooling modes:

| Mode | Connection reuse | Use case |
|------|-----------------|----------|
| `session` | One server connection per client session | Requires persistent session state |
| `transaction` | Server connection returned after each transaction | Most common — works for stateless apps |
| `statement` | Returned after each statement | Rarely safe — breaks multi-statement transactions |

The interview gotcha: *"What breaks in transaction pooling mode?"* Prepared statements (unless you use `server_reset_query`), `SET` session parameters, advisory locks, and `LISTEN/NOTIFY`. Any session-level state gets lost when the connection is recycled.

```ini
# pgbouncer.ini
[databases]
myapp = host=127.0.0.1 port=5432 dbname=myapp

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```

A pool of 20 server connections handles 1000 client connections comfortably for transaction-pooling workloads. The right `default_pool_size` is roughly `(number of CPU cores) * 2` for CPU-bound queries.

---

## WAL and Replication Concepts

The Write-Ahead Log is a sequential append-only file that records every change before it touches the actual data pages. This guarantees durability: if Postgres crashes mid-write, WAL replay restores consistency.

**Streaming replication** ships WAL records from primary to standby in near real-time. The standby replays them, maintaining a read-only replica.

```sql
-- On primary: check replication lag
SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn,
       (sent_lsn - replay_lsn) AS replication_lag_bytes
FROM pg_stat_replication;
```

**Synchronous vs asynchronous replication:** Async means the primary commits without waiting for standby acknowledgment — zero performance overhead, but potential data loss on primary failure. Sync replication (`synchronous_commit = on`) waits for standby confirmation, eliminating data loss at a latency cost.

Logical replication (Postgres 10+) replicates at the row level rather than WAL byte level. It enables replicating individual tables, replicating to different Postgres major versions, and feeding change data capture (CDC) pipelines.

```sql
-- Set up logical replication (publisher side)
CREATE PUBLICATION my_pub FOR TABLE orders, users;

-- Subscriber side
CREATE SUBSCRIPTION my_sub
  CONNECTION 'host=primary dbname=myapp'
  PUBLICATION my_pub;
```

Fintech interviewers care about WAL because audit trails, point-in-time recovery (PITR), and zero-downtime major version upgrades all depend on it. Knowing that `wal_level = logical` is required for CDC pipelines, and that WAL archiving enables PITR, signals operational maturity.

---

## What Companies Ask These Questions

**Fintech:** MVCC, isolation levels, and WAL/replication. They need engineers who understand transaction guarantees and can reason about what happens during a failover.

**SaaS:** Connection pooling and index selection. Multi-tenant databases under variable load need engineers who can tune PgBouncer and avoid full table scans as data grows.

**Data-heavy:** Query planning and BRIN/GIN indexes. Analytical workloads on large tables require reading EXPLAIN output and choosing index types that don't consume half your disk.

The common thread: these questions filter engineers who have debugged production Postgres from those who have only used it as a query target.
