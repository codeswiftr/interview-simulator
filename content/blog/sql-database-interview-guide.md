---
title: "SQL and Relational Database Interview Guide"
description: "Master SQL interview questions with this deep-dive into query optimization, normalization, transaction isolation, window functions, CTEs, and PostgreSQL-specific features that interviewers actually ask about."
date: "2026-03-20"
category: "Technical Skills Guides"
---

# SQL and Relational Database Interview Guide

SQL remains one of the most consistently tested skills in software engineering interviews, yet candidates often underestimate its depth. An interviewer asking a "simple SQL question" may be probing your understanding of query planning, isolation levels, or index internals — not just syntax. This guide covers the topics that separate candidates who pass SQL rounds from those who stumble.

## Query Optimization: EXPLAIN Plans and Index Selection

The single most valuable habit you can demonstrate in a SQL interview is reaching for `EXPLAIN` (or `EXPLAIN ANALYZE` in PostgreSQL) before declaring a query "good enough." An EXPLAIN plan reveals the access method the query planner chose — sequential scan, index scan, index-only scan, bitmap heap scan — along with estimated and actual row counts, cost estimates, and join strategies.

Key things to discuss when an interviewer asks how you'd optimize a slow query:

**Index selection:** B-tree indexes (the default in PostgreSQL) work well for equality and range queries on high-cardinality columns. Partial indexes reduce size and maintenance overhead for filtered queries (`CREATE INDEX ON orders (user_id) WHERE status = 'active'`). Multi-column indexes serve queries that filter on multiple columns, but column order matters — the index `(a, b)` helps queries filtering on `a` alone or `(a, b)` together, but not `b` alone. Covering indexes (index-only scans) eliminate heap fetches entirely when all projected columns are in the index.

**Join strategies:** Hash joins are efficient for large unsorted datasets; nested-loop joins suit small inner tables; merge joins require sorted inputs. Demonstrating awareness of when the planner might choose incorrectly (stale statistics, skewed data distributions) and how to address it (`ANALYZE`, `pg_stats`, plan hints via `pg_hint_plan`) signals senior-level understanding.

**Common gotchas:** `LIKE '%prefix%'` prevents index use; implicit type casts in `WHERE` clauses defeat index scans; functions applied to indexed columns (`LOWER(email) = ...`) require expression indexes.

## Normalization vs. Denormalization

Normalization organizes data to minimize redundancy and enforce integrity. The canonical normal forms you should be able to explain:

- **1NF:** Atomic column values, no repeating groups
- **2NF:** 1NF plus no partial dependencies (every non-key attribute depends on the whole key)
- **3NF:** 2NF plus no transitive dependencies
- **BCNF:** Every determinant is a candidate key

In practice, most production schemas aim for 3NF or BCNF and then deliberately denormalize for read performance. Denormalization trades write complexity (maintaining derived columns, managing consistency) for read speed (fewer joins, better cache locality). Materialized views sit between these extremes — precomputed query results refreshed on demand or on schedule.

Interview tip: when asked "should we normalize or denormalize?", the correct answer is always "it depends on the read/write ratio, query patterns, and consistency requirements." Demonstrate that you understand the tradeoffs rather than defaulting to one approach.

## Transactions and Isolation Levels

Transactions provide the ACID guarantees that make relational databases trustworthy. The four isolation levels defined by SQL standard and their anomaly protections:

| Isolation Level | Dirty Reads | Non-Repeatable Reads | Phantom Reads |
|----------------|-------------|---------------------|---------------|
| Read Uncommitted | Possible | Possible | Possible |
| Read Committed | Prevented | Possible | Possible |
| Repeatable Read | Prevented | Prevented | Possible |
| Serializable | Prevented | Prevented | Prevented |

PostgreSQL's default is Read Committed. Its Repeatable Read implementation uses MVCC (Multi-Version Concurrency Control) rather than locks, which means it also prevents phantom reads in practice. Serializable uses predicate locking (SSI — Serializable Snapshot Isolation) to detect write-write and write-read conflicts.

Interviewers frequently ask about deadlocks — understand that they arise from circular lock dependencies and that PostgreSQL detects and resolves them by aborting one transaction. Good application design acquires locks in a consistent order to minimize deadlock probability.

## Window Functions and CTEs

Window functions are a frequent advanced SQL interview topic. Unlike aggregate functions, window functions compute results across a set of rows related to the current row without collapsing them into a single output row.

Essential window functions to know:
- `ROW_NUMBER()` — unique sequential rank, no ties
- `RANK()` / `DENSE_RANK()` — handle ties differently (RANK skips numbers, DENSE_RANK does not)
- `LAG()` / `LEAD()` — access preceding/following row values
- `SUM() OVER (PARTITION BY ... ORDER BY ... ROWS BETWEEN ...)` — running totals with frame clauses

Common interview question: "Find the top 3 salaries per department." The clean solution uses `DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC)` in a CTE, then filters on `rank <= 3`.

CTEs (Common Table Expressions) introduced with `WITH` improve readability and allow recursive queries. Recursive CTEs are useful for hierarchical data (org charts, bill-of-materials) — know the pattern: an anchor member unioned with a recursive member that terminates when no new rows are produced. PostgreSQL also supports materialized CTEs (`WITH ... AS MATERIALIZED`) which force the planner to execute the CTE as a fence, useful when you need its results computed exactly once.

## PostgreSQL-Specific Features Worth Knowing

If your target company uses PostgreSQL (increasingly common), these features come up in interviews:

- **JSONB:** Binary JSON storage with GIN indexing, enabling efficient querying of semi-structured data without sacrificing relational integrity elsewhere
- **Lateral joins:** `LATERAL` allows a subquery to reference columns from preceding `FROM` items, enabling per-row subqueries that replace expensive correlated subqueries
- **`pg_stat_statements`:** Query performance extension that aggregates execution statistics — useful for identifying slow queries in production
- **Table partitioning:** Range, list, and hash partitioning strategies for managing large tables; partition pruning means queries touching a specific date range scan only relevant partitions
- **`COPY`:** Bulk loading mechanism orders of magnitude faster than row-by-row `INSERT` for ingesting large datasets

A strong SQL interview performance comes from combining practical query-writing skill with the ability to reason about performance, consistency, and schema design tradeoffs. Practice writing queries on a running PostgreSQL instance, run `EXPLAIN ANALYZE`, and develop intuition for what the planner does and why.
