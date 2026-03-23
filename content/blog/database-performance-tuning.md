---
title: "Database Performance Tuning: Query Optimization, Index Strategy, and Schema Design"
description: "A hands-on guide to database performance tuning for backend engineers — covering query optimization with EXPLAIN, index design principles, schema patterns that scale, and common performance anti-patterns to avoid."
date: "2026-03-20"
category: "Backend Engineering"
---

# Database Performance Tuning: Query Optimization, Index Strategy, and Schema Design

Database performance problems are a rite of passage for backend engineers. A query that runs fine at 10,000 rows becomes unacceptably slow at 10 million. An index strategy that seemed sensible in development causes write contention in production. A schema that felt clean during design requires painful migrations once traffic is real.

This guide covers the mental models and practical techniques that let you diagnose and fix these problems systematically.

## Start With EXPLAIN

Before optimizing anything, understand what the database is actually doing. Every major database — PostgreSQL, MySQL, SQLite — has an EXPLAIN command that shows the query execution plan.

In PostgreSQL, `EXPLAIN ANALYZE` gives you the plan *and* actual execution statistics:

```sql
EXPLAIN ANALYZE
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2025-01-01'
GROUP BY u.id, u.name;
```

The output shows each operation (Seq Scan, Index Scan, Hash Join, etc.) with estimated versus actual row counts and time spent. Key things to look for:

- **Seq Scan on large tables**: A sequential scan on a table with millions of rows is almost always a problem. It means no index is being used.
- **Estimate vs. actual row count divergence**: If PostgreSQL estimates 100 rows but sees 100,000, its query planning decisions will be wrong. Run `ANALYZE tablename` to update statistics.
- **Nested Loop on large result sets**: Nested loop joins work well for small inner tables but become O(n²) with large datasets. Hash joins and merge joins scale better.

## Index Design Principles

### Selectivity

An index is valuable when it eliminates most rows early. A boolean column with 50% true/false is low-selectivity — the database may decide a seq scan is faster than using the index. A UUID primary key is high-selectivity — almost every lookup eliminates all but one row.

**Rule of thumb**: Columns with fewer than 10-20 distinct values are poor candidates for standalone B-tree indexes. Consider partial indexes or composite indexes instead.

### Composite Index Column Order

The order of columns in a composite index matters. An index on `(a, b, c)` can be used for:
- Queries filtering on `a`
- Queries filtering on `a, b`
- Queries filtering on `a, b, c`

It cannot be efficiently used for queries filtering only on `b` or `c`. The leftmost prefix rule applies.

For `ORDER BY` optimization, the index column order should match the sort order. An index on `(user_id, created_at DESC)` perfectly serves queries like `WHERE user_id = ? ORDER BY created_at DESC LIMIT 10`.

### Covering Indexes

A covering index includes all columns referenced by a query, allowing the database to satisfy the query entirely from the index without touching the main table (heap). In PostgreSQL, add `INCLUDE` columns:

```sql
CREATE INDEX idx_orders_user_status 
ON orders (user_id, status) 
INCLUDE (total_amount, created_at);
```

Now a query selecting `total_amount` and `created_at` where filtering on `user_id` and `status` never touches the heap — often a 2-5x speedup for common queries.

### Partial Indexes

Index only the rows you actually query:

```sql
-- Only index active subscriptions
CREATE INDEX idx_subscriptions_active 
ON subscriptions (user_id) 
WHERE status = 'active';
```

This index is much smaller and faster to update than an index on all subscriptions. Particularly valuable when most rows will never match the common query predicate.

## Schema Design for Performance

### Avoid EAV (Entity-Attribute-Value) at Scale

The EAV pattern — a `properties` table with `entity_id`, `key`, `value` columns — is flexible but queries against it are expensive and hard to optimize. For dynamic attributes, prefer JSONB columns (PostgreSQL) which can be indexed, or separate tables for each attribute category.

### Denormalization as a Deliberate Choice

Strict normalization minimizes storage and update anomalies but requires joins for most queries. At scale, precomputed denormalized values (e.g., storing `order_count` directly on the `users` table) can eliminate expensive aggregation queries.

The tradeoff: every write must maintain both the source data and the denormalized copy. Use triggers, application-level writes, or background jobs — with explicit documentation that the value is derived.

### Timestamp Patterns

Store timestamps in UTC always. Use `timestamptz` (timezone-aware) in PostgreSQL rather than `timestamp`. For range queries on `created_at`, ensure the index and query types match — casting in the WHERE clause can prevent index use:

```sql
-- Bad: cast prevents index use
WHERE EXTRACT(year FROM created_at) = 2025

-- Good: range query uses index
WHERE created_at >= '2025-01-01' AND created_at < '2026-01-01'
```

## Common Performance Anti-Patterns

**N+1 queries**: Fetching a list of users, then querying orders for each user individually. Fix with a JOIN or a batched `WHERE user_id IN (...)` query.

**SELECT ***: Fetches every column, including large text fields you don't need, and prevents covering index optimization. Always specify columns explicitly.

**OFFSET for pagination**: `OFFSET 10000 LIMIT 20` requires scanning and discarding 10,000 rows. Use keyset/cursor pagination instead: `WHERE id > last_seen_id LIMIT 20`.

**Missing indexes on foreign keys**: PostgreSQL doesn't automatically index foreign key columns (unlike MySQL). Every foreign key column that you JOIN on or filter by should have an index.

**Transactions too large**: Long-running transactions hold locks and cause contention. Break batch operations into smaller chunks.

## Index Maintenance

Indexes aren't free. Every write (INSERT, UPDATE, DELETE) must update every index on the table. Tables with 10+ indexes on high-write paths can spend more time maintaining indexes than writing data.

Regularly review index usage:

```sql
SELECT indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC;
```

Indexes with zero scans in production are candidates for removal. Use `CONCURRENTLY` for index creation and removal on live tables to avoid locking.

Performance tuning is iterative. Measure before and after every change, and always verify against production-representative data volumes.
