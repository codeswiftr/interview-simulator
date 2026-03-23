---
title: "Advanced SQL Interview Guide: Window Functions, CTEs, and Query Optimization"
description: "Master advanced SQL for interviews — window functions, recursive CTEs, execution plans, index strategies, EXPLAIN ANALYZE, and the complex queries that appear in data engineering interviews."
date: "2026-03-20"
category: "Algorithms"
---

# Advanced SQL Interview Guide: Window Functions, CTEs, and Query Optimization

Basic SQL (SELECT, JOIN, GROUP BY) is table stakes. Senior engineering and data engineering interviews test advanced SQL: window functions, recursive queries, optimization, and the ability to write complex analytical queries correctly and efficiently. Here's what to master.

## Window Functions: The Most Tested Topic

Window functions compute values across rows related to the current row without collapsing rows (unlike GROUP BY). Every senior data/backend engineer should know these cold.

```sql
-- Rank users by revenue within each region, without collapsing rows
SELECT 
    user_id,
    region,
    revenue,
    RANK() OVER (PARTITION BY region ORDER BY revenue DESC) AS rank_in_region,
    SUM(revenue) OVER (PARTITION BY region) AS region_total,
    SUM(revenue) OVER (ORDER BY order_date ROWS UNBOUNDED PRECEDING) AS running_total,
    LAG(revenue, 1) OVER (PARTITION BY user_id ORDER BY order_date) AS prev_revenue
FROM orders;
```

Key window functions:
- `ROW_NUMBER()` — unique sequential number (no ties)
- `RANK()` — same value gets same rank, gaps in sequence after ties
- `DENSE_RANK()` — same value gets same rank, no gaps
- `LAG(col, n)` / `LEAD(col, n)` — access value n rows before/after current row
- `FIRST_VALUE(col)` / `LAST_VALUE(col)` — first/last value in window frame
- `SUM/AVG/COUNT() OVER (...)` — running aggregates

## Common Window Function Patterns

**Month-over-month growth:**
```sql
SELECT 
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
    (revenue - LAG(revenue) OVER (ORDER BY month)) / 
        NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100 AS growth_pct
FROM monthly_revenue;
```

**Top N per group:**
```sql
-- Top 3 products per category by revenue
SELECT *
FROM (
    SELECT 
        category, product_id, revenue,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC) AS rn
    FROM products
) ranked
WHERE rn <= 3;
```

**Session identification:** Group user events into sessions (gap of > 30 minutes = new session):
```sql
WITH gaps AS (
    SELECT 
        user_id, event_time,
        CASE WHEN event_time - LAG(event_time) OVER (PARTITION BY user_id ORDER BY event_time) 
             > INTERVAL '30 minutes' 
             THEN 1 ELSE 0 END AS session_start
    FROM events
)
SELECT user_id, event_time,
       SUM(session_start) OVER (PARTITION BY user_id ORDER BY event_time) AS session_id
FROM gaps;
```

## CTEs and Recursive CTEs

**CTEs (WITH clauses):** Break complex queries into named, readable steps.

```sql
WITH 
active_users AS (
    SELECT DISTINCT user_id 
    FROM events 
    WHERE event_date >= CURRENT_DATE - 30
),
user_revenue AS (
    SELECT user_id, SUM(amount) AS total_revenue
    FROM orders
    WHERE user_id IN (SELECT user_id FROM active_users)
    GROUP BY user_id
)
SELECT 
    au.user_id,
    COALESCE(ur.total_revenue, 0) AS revenue
FROM active_users au
LEFT JOIN user_revenue ur USING (user_id);
```

**Recursive CTEs:** Query hierarchical or graph data (org charts, category trees, network traversal).

```sql
-- Traverse org chart from CEO down
WITH RECURSIVE org_tree AS (
    -- Base case: CEO (no manager)
    SELECT employee_id, name, manager_id, 0 AS depth
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- Recursive case: employees with a manager in the result
    SELECT e.employee_id, e.name, e.manager_id, ot.depth + 1
    FROM employees e
    JOIN org_tree ot ON e.manager_id = ot.employee_id
)
SELECT * FROM org_tree ORDER BY depth, name;
```

## Query Optimization

**EXPLAIN ANALYZE:** The essential tool for diagnosing slow queries. Shows the actual execution plan with row counts and timing. Key things to look for:
- Sequential scans on large tables (may need an index)
- Nested loop joins on large datasets (may prefer hash join)
- High row estimate errors (inaccurate statistics — run ANALYZE)
- Sorts on large datasets without an index

**Index strategies:**
- B-tree indexes: equality, range, ORDER BY on low-cardinality columns
- Partial indexes: `CREATE INDEX ON orders (user_id) WHERE status = 'completed'` — only indexes completed orders
- Composite indexes: column order matters — most selective/most filtered column first
- Index-only scans: include all needed columns in the index (INCLUDE clause in PostgreSQL)

**Common optimization patterns:**
```sql
-- Slow: function on indexed column prevents index use
WHERE DATE_TRUNC('day', created_at) = '2024-01-01'

-- Fast: range condition uses index
WHERE created_at >= '2024-01-01' AND created_at < '2024-01-02'
```

**Avoid:** `SELECT *` (fetches unnecessary columns, prevents index-only scans), correlated subqueries (execute once per row — often replaceable with a JOIN or window function), large IN clauses (use JOIN instead for thousands of values).

## Interview Problem: Retention Analysis

"Write a query to compute monthly retention — the percentage of users who were active in month N and returned in month N+1."

```sql
WITH monthly_active AS (
    SELECT 
        user_id,
        DATE_TRUNC('month', event_date) AS month
    FROM events
    GROUP BY 1, 2
)
SELECT 
    m1.month,
    COUNT(m2.user_id)::FLOAT / COUNT(m1.user_id) AS retention_rate
FROM monthly_active m1
LEFT JOIN monthly_active m2 
    ON m1.user_id = m2.user_id 
    AND m2.month = m1.month + INTERVAL '1 month'
GROUP BY m1.month
ORDER BY m1.month;
```

This kind of query — joining a table to itself with an offset, computing a rate — is the bread and butter of data engineering SQL interviews. Practice until you can write it fluently without reference.
