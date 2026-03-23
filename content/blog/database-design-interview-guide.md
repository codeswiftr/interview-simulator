# Database Design and SQL Interview Guide 2024: Schema Design, Query Optimization, Indexes

Database questions appear in nearly every software engineering interview — and they're one of the most reliable ways to differentiate candidates. A strong SQL foundation, understanding of index internals, and the ability to design a normalized schema under time pressure signal engineering maturity that pure algorithmic prep doesn't. This guide covers everything from normalization theory to query plan reading to NoSQL trade-offs.

## What Database Interviews Actually Test

Database questions in interviews target three distinct skill sets. Know which one is being assessed at any moment:

**SQL fluency**: Can you write correct, efficient queries? Window functions, CTEs, aggregations, self-joins. This is tested with "write a query to..." problems.

**Schema design**: Can you model a domain? Normalize appropriately, choose the right relationships, handle edge cases like many-to-many or polymorphic associations. This is tested with "design the schema for..." problems.

**Systems understanding**: Do you understand why performance degrades and how to fix it? Index internals, query execution plans, transaction isolation, distributed trade-offs. This is tested with "how would you optimize..." or "what's wrong with..." problems.

Most interview rounds test all three. The candidates who struggle usually have SQL fluency but weak schema design, or can design schemas but can't reason about performance.

## Relational Schema Design

### Normalization: The Theory You Need in Practice

Normalization reduces data redundancy and update anomalies. Interviewers expect you to know the normal forms and — critically — when to violate them.

**First Normal Form (1NF)**: Atomic values in each column; no repeating groups.

Violation:
```
orders: id | items
        1  | "laptop, mouse, keyboard"
```

Fixed: a separate `order_items` table with one row per item.

**Second Normal Form (2NF)**: 1NF + no partial dependencies. Every non-key attribute must depend on the entire primary key, not just part of it.

Violation (composite key: `order_id, product_id`):
```
order_items: order_id | product_id | quantity | product_name | product_price
```
`product_name` and `product_price` depend only on `product_id`, not the full composite key.

Fixed: extract a `products` table with `(product_id, product_name, product_price)`.

**Third Normal Form (3NF)**: 2NF + no transitive dependencies. Non-key attributes must not depend on other non-key attributes.

Violation:
```
employees: employee_id | department_id | department_name | manager_id
```
`department_name` depends on `department_id`, not on `employee_id`.

Fixed: extract a `departments` table.

**Boyce-Codd Normal Form (BCNF)**: Stricter than 3NF. Every determinant must be a candidate key. BCNF violations are rare in practice but appear in interview edge cases involving composite candidate keys.

### When to Denormalize

3NF is the default target. Denormalize when you have a performance problem and have evidence (EXPLAIN output, slow query logs) that normalization is causing it — not preemptively.

**Legitimate reasons to denormalize:**
- Read-heavy analytical workloads where join cost dominates (data warehouses use star schema intentionally)
- Materialized aggregates that are expensive to compute on demand (e.g., denormalize `order_count` onto the `users` table if you always need it)
- Reporting schemas where 5-way joins make query maintenance impractical

**What interviewers want to hear:** "I'd start normalized and denormalize only when profiling shows the join is a bottleneck. I'd add application-level cache invalidation logic or a materialized view to keep the denormalized data consistent."

### Foreign Key Design and Referential Integrity

Foreign keys enforce referential integrity — a row in the child table cannot reference a non-existent row in the parent table. The database enforces this at the storage level, which is reliable in a way application-layer enforcement never fully is.

```sql
CREATE TABLE orders (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status      TEXT NOT NULL CHECK (status IN ('pending', 'confirmed', 'shipped', 'cancelled')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

`ON DELETE RESTRICT` prevents deleting a user who has orders. Other options:
- `ON DELETE CASCADE`: delete all orders when user is deleted (appropriate for audit logs, not for financial records)
- `ON DELETE SET NULL`: set `user_id` to NULL when user is deleted (appropriate when the child can exist without the parent)

**Gotcha**: Foreign keys add overhead to inserts and updates (the parent row must be checked). At very high insert rates, some teams disable foreign key enforcement and enforce integrity at the application layer — this is a trade-off, not a best practice. Know that it exists and explain the risk.

**Many-to-many relationships**: Always model with a junction table.

```sql
CREATE TABLE user_roles (
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    granted_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    granted_by  BIGINT REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);
```

The composite primary key on `(user_id, role_id)` prevents duplicate role assignments and creates an implicit index on `user_id`, which is usually the access pattern.

## SQL Window Functions

Window functions are tested in almost every data-heavy interview. You need to be able to write them from memory and explain what each clause does.

### Core Syntax

```sql
function_name() OVER (
    PARTITION BY column1, column2  -- grouping (like GROUP BY, but doesn't collapse rows)
    ORDER BY column3 DESC          -- ordering within each partition
    ROWS/RANGE BETWEEN ...         -- frame specification
)
```

`PARTITION BY` divides the result into groups. The window function runs independently for each partition. Without `PARTITION BY`, the entire result set is one partition.

### ROW_NUMBER, RANK, DENSE_RANK

These are frequently confused. The difference only matters when there are ties.

```sql
-- Given: sales amounts 100, 100, 80, 70
SELECT
    salesperson_id,
    amount,
    ROW_NUMBER() OVER (ORDER BY amount DESC) AS row_num,   -- 1, 2, 3, 4 (arbitrary tiebreak)
    RANK()       OVER (ORDER BY amount DESC) AS rank_val,  -- 1, 1, 3, 4 (gap after ties)
    DENSE_RANK() OVER (ORDER BY amount DESC) AS dense_rank -- 1, 1, 2, 3 (no gap)
FROM sales;
```

Common interview use: "Find the top-performing salesperson per region."

```sql
WITH ranked AS (
    SELECT
        salesperson_id,
        region,
        total_sales,
        RANK() OVER (PARTITION BY region ORDER BY total_sales DESC) AS rank_in_region
    FROM salesperson_totals
)
SELECT salesperson_id, region, total_sales
FROM ranked
WHERE rank_in_region = 1;
```

Using `RANK()` here returns multiple rows per region if there's a tie for first. Use `ROW_NUMBER()` if you want exactly one row per region.

### LAG and LEAD

Access a value from a previous or subsequent row without a self-join.

```sql
-- Month-over-month revenue change
SELECT
    month,
    revenue,
    LAG(revenue, 1) OVER (ORDER BY month) AS prev_month_revenue,
    revenue - LAG(revenue, 1) OVER (ORDER BY month) AS absolute_change,
    ROUND(
        100.0 * (revenue - LAG(revenue, 1) OVER (ORDER BY month))
        / NULLIF(LAG(revenue, 1) OVER (ORDER BY month), 0),
        2
    ) AS pct_change
FROM monthly_revenue
ORDER BY month;
```

`LAG(expr, offset, default)` — the third argument provides a default when there's no previous row (first month has no prior month). Without a default, `LAG()` returns NULL for the first row.

```sql
-- Identify users who churned: active in month N but not in month N+1
SELECT
    user_id,
    month,
    LEAD(month, 1) OVER (PARTITION BY user_id ORDER BY month) AS next_active_month
FROM monthly_active_users
```

If `next_active_month` is NULL or is more than one month after `month`, the user churned after that month.

### Frame Specifications

The frame clause defines which rows are included in the window relative to the current row.

```sql
-- 7-day moving average (current row + 6 preceding rows)
SELECT
    date,
    daily_revenue,
    AVG(daily_revenue) OVER (
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS moving_avg_7d
FROM daily_revenue;

-- Running total
SELECT
    date,
    daily_revenue,
    SUM(daily_revenue) OVER (
        ORDER BY date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_revenue
FROM daily_revenue;

-- Percentage of total (no ORDER BY, no frame — entire partition is the window)
SELECT
    product_id,
    category,
    revenue,
    revenue / SUM(revenue) OVER (PARTITION BY category) AS pct_of_category
FROM product_revenue;
```

`ROWS` vs. `RANGE`: `ROWS` is physical row count. `RANGE` is logical — all rows with the same ORDER BY value are included. For time-series data with potential duplicate dates, `RANGE` may produce unexpected results if multiple rows share the same date.

### NTILE and PERCENT_RANK

```sql
-- Divide customers into 4 revenue quartiles
SELECT
    customer_id,
    annual_revenue,
    NTILE(4) OVER (ORDER BY annual_revenue) AS quartile
FROM customers;

-- Percentile rank (0 to 1)
SELECT
    employee_id,
    salary,
    PERCENT_RANK() OVER (ORDER BY salary) AS percentile_rank
FROM employees;
```

`NTILE(n)` divides rows into n groups of approximately equal size. If rows don't divide evenly, earlier buckets get the extra rows.

## Query Optimization

### EXPLAIN and EXPLAIN ANALYZE

`EXPLAIN` shows the query plan without executing. `EXPLAIN ANALYZE` executes and shows actual timing and row counts alongside the plan.

```sql
EXPLAIN ANALYZE
SELECT u.name, COUNT(o.id) AS order_count
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE u.created_at > '2024-01-01'
GROUP BY u.id, u.name
ORDER BY order_count DESC
LIMIT 10;
```

What to look for in the output:

**Seq Scan**: Full table scan. Expected for small tables or when selecting most of the table. Unexpected on a large table with a WHERE clause means the index isn't being used.

**Index Scan**: Used when the query selects a small fraction of rows. Follows the index B-tree to find row locations, then fetches rows.

**Index Only Scan**: All needed columns are in the index (covering index). Never touches the heap. Most efficient.

**Hash Join vs. Nested Loop vs. Merge Join**:
- Nested Loop: for small outer tables or when one side has an index. O(n * m) worst case.
- Hash Join: build a hash table on the smaller side, probe with the larger side. Efficient for large unsorted joins but requires memory.
- Merge Join: both sides are sorted on the join key. Efficient when sorted order is already available.

**Actual rows vs. estimated rows**: Large discrepancy means stale statistics. Run `ANALYZE table_name` to update them. Stale statistics cause the planner to choose wrong plans (e.g., Nested Loop when Hash Join would be better).

**Rows Removed by Filter**: High values here mean the filter is applied after a full scan — you need an index on that column.

### Index Types

**B-tree** (default): Balanced tree. Supports equality (`=`), range (`<`, `>`, `BETWEEN`), prefix LIKE (`name LIKE 'John%'`), and IS NULL. Maintains sorted order, so ORDER BY on an indexed column can be served without a sort step.

**Hash**: Only supports equality. Faster than B-tree for pure equality lookups but cannot support range queries or sorting. Not persisted before PostgreSQL 10 (crash recovery required a rebuild). Rarely preferred over B-tree in practice.

**GIN (Generalized Inverted Index)**: For values that contain multiple components — full-text search (tsvector), JSONB, arrays, hstore. GIN is write-heavy (slower inserts/updates) but read-fast. Use for any column where you need `@>` (contains), `<@` (contained by), or `@@` (full-text match) operators.

```sql
-- Index for JSONB contains queries
CREATE INDEX idx_user_metadata ON users USING GIN (metadata);
-- Query: SELECT * FROM users WHERE metadata @> '{"plan": "enterprise"}'
```

**GiST (Generalized Search Tree)**: For geometric types, geographic data (PostGIS), range types, full-text search (tsquery). Unlike GIN, GiST supports nearest-neighbor searches (`<->` operator for distance). Use PostGIS geometry columns with GiST.

**BRIN (Block Range Index)**: Extremely small index for very large tables where the data has natural physical ordering (time-series data inserted chronologically, log tables). Stores min/max values per block range rather than per row. Size is O(table size / pages_per_range) rather than O(rows). Effective for `WHERE created_at > '2024-01-01'` on a table where rows are inserted in time order.

```sql
-- For a 500M row events table, BRIN on created_at is megabytes vs. gigabytes for B-tree
CREATE INDEX idx_events_created_brin ON events USING BRIN (created_at);
```

### Index Selectivity and Partial Indexes

**Selectivity**: Fraction of rows that match a condition. Low selectivity = many matching rows = less useful index (full scan may be cheaper than index scan + heap fetch for each row).

A column with 3 distinct values (e.g., `status: 'active', 'inactive', 'pending'`) has low selectivity for equality queries — the index may not be used. A column like `user_id` or `email` has high selectivity.

**Partial indexes**: Index only a subset of rows. Dramatically reduces index size when you mostly query a small fraction of the table.

```sql
-- Only active users are queried by email in the login flow
CREATE INDEX idx_users_email_active ON users(email)
WHERE status = 'active';

-- Only unprocessed jobs are queried in the job queue
CREATE INDEX idx_jobs_pending ON jobs(created_at, priority)
WHERE status = 'pending';
```

The query must include the WHERE clause condition for the partial index to be used.

**Covering indexes** (index includes all needed columns):

```sql
-- Query: SELECT name, email FROM users WHERE company_id = 123
-- Without covering index: index scan on company_id + heap fetch for name, email
-- With covering index: index-only scan
CREATE INDEX idx_users_company_covering ON users(company_id) INCLUDE (name, email);
```

### Multi-Column Index Column Order

The leftmost prefix rule: a composite index on `(a, b, c)` can serve queries filtering on `a`, `a AND b`, or `a AND b AND c`. It cannot efficiently serve queries filtering only on `b` or only on `c`.

```sql
CREATE INDEX idx_orders_user_status_date ON orders(user_id, status, created_at);
-- Efficient: WHERE user_id = 123
-- Efficient: WHERE user_id = 123 AND status = 'pending'
-- Efficient: WHERE user_id = 123 AND status = 'pending' AND created_at > '2024-01-01'
-- NOT efficient: WHERE status = 'pending'  (no user_id filter)
```

Column order rule: most selective column first, unless you need to support range queries on a middle column (range queries on `b` prevent the index from using `c`).

## Common SQL Interview Questions with Solutions

### Find the Nth Highest Salary

```sql
-- Using window function (cleaner, handles ties properly)
SELECT DISTINCT salary
FROM (
    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
    FROM employees
) ranked
WHERE rnk = 3;  -- Change to N

-- Alternative with OFFSET (works but doesn't handle ties)
SELECT DISTINCT salary
FROM employees
ORDER BY salary DESC
LIMIT 1 OFFSET 2;  -- OFFSET N-1
```

`DENSE_RANK()` is usually what the interviewer means — return a salary even if two people share rank 2, making the third distinct salary rank 3.

### Identify Duplicates

```sql
-- Find all rows with duplicate email addresses
SELECT email, COUNT(*) AS occurrences
FROM users
GROUP BY email
HAVING COUNT(*) > 1;

-- Find the actual duplicate rows (all of them, not just counts)
SELECT *
FROM users
WHERE email IN (
    SELECT email FROM users GROUP BY email HAVING COUNT(*) > 1
)
ORDER BY email;

-- Find duplicates using window function (useful when deleting — keep one)
SELECT id, email, row_num
FROM (
    SELECT
        id,
        email,
        ROW_NUMBER() OVER (PARTITION BY email ORDER BY created_at) AS row_num
    FROM users
) ranked
WHERE row_num > 1;
-- These are the IDs to delete (keep row_num = 1, delete the rest)
```

### Running Totals and Cumulative Metrics

```sql
-- Cumulative revenue by day, with daily and running total
SELECT
    order_date,
    SUM(amount) AS daily_revenue,
    SUM(SUM(amount)) OVER (ORDER BY order_date) AS cumulative_revenue,
    SUM(SUM(amount)) OVER (
        ORDER BY order_date
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS rolling_30d_revenue
FROM orders
GROUP BY order_date
ORDER BY order_date;
```

Note `SUM(SUM(amount))` — the inner SUM is the group aggregate; the outer SUM is the window function over those aggregated values.

### Consecutive Dates / Gaps and Islands

Find users with 7 or more consecutive days of login activity:

```sql
WITH daily_logins AS (
    SELECT DISTINCT user_id, login_date::date AS login_date
    FROM user_sessions
),
with_groups AS (
    SELECT
        user_id,
        login_date,
        -- Rows with the same (login_date - row_number) are consecutive
        login_date - CAST(ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS INT) AS grp
    FROM daily_logins
),
streaks AS (
    SELECT
        user_id,
        MIN(login_date) AS streak_start,
        MAX(login_date) AS streak_end,
        COUNT(*) AS streak_length
    FROM with_groups
    GROUP BY user_id, grp
)
SELECT user_id, streak_start, streak_end, streak_length
FROM streaks
WHERE streak_length >= 7
ORDER BY streak_length DESC;
```

The trick: if you subtract the row number from the date, consecutive dates produce the same constant value (the "group key"). Rows in the same group are a consecutive sequence.

### Self-Join for Hierarchical Data

```sql
-- Find all employees who earn more than their manager
SELECT
    e.name AS employee,
    e.salary AS employee_salary,
    m.name AS manager,
    m.salary AS manager_salary
FROM employees e
JOIN employees m ON e.manager_id = m.id
WHERE e.salary > m.salary;
```

### Pivot / Cross-Tab Without CROSSTAB Extension

```sql
-- Monthly sales by product category (columns: Jan, Feb, Mar)
SELECT
    product_category,
    SUM(CASE WHEN EXTRACT(MONTH FROM order_date) = 1 THEN revenue ELSE 0 END) AS jan,
    SUM(CASE WHEN EXTRACT(MONTH FROM order_date) = 2 THEN revenue ELSE 0 END) AS feb,
    SUM(CASE WHEN EXTRACT(MONTH FROM order_date) = 3 THEN revenue ELSE 0 END) AS mar
FROM orders
JOIN products ON orders.product_id = products.id
WHERE EXTRACT(YEAR FROM order_date) = 2024
GROUP BY product_category;
```

## ACID vs. BASE and When to Choose

### ACID (Relational Databases)

**Atomicity**: A transaction either fully completes or fully rolls back. No partial updates.

**Consistency**: Transactions take the database from one valid state to another. Constraints (foreign keys, CHECK constraints, NOT NULL) are enforced transactionally.

**Isolation**: Concurrent transactions behave as if they ran serially. Isolation levels (READ COMMITTED, REPEATABLE READ, SERIALIZABLE) trade consistency for performance.

**Durability**: Committed transactions survive crashes. Achieved via write-ahead logging (WAL) — changes are written to the log before the data pages, so the log can replay uncommitted changes after a crash.

**Isolation level trade-offs:**

| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read |
|----------------|------------|---------------------|--------------|
| READ UNCOMMITTED | Possible | Possible | Possible |
| READ COMMITTED | Prevented | Possible | Possible |
| REPEATABLE READ | Prevented | Prevented | Possible |
| SERIALIZABLE | Prevented | Prevented | Prevented |

Most production databases use READ COMMITTED (PostgreSQL default). SERIALIZABLE prevents all anomalies but at significant performance cost. Use SERIALIZABLE only for financial operations where correctness is non-negotiable and you've tested the performance impact.

### BASE (NoSQL Systems)

**Basically Available**: The system remains available even during partial failures, though it may serve stale data.

**Soft state**: The system state may change over time even without input, as consistency is reached eventually.

**Eventually consistent**: All replicas will converge to the same value given enough time without further writes.

**When to choose ACID:**
- Financial transactions, inventory management, bookings — any domain where double-spending or lost updates are catastrophic
- Complex relational data with integrity constraints
- When you need cross-table consistency in a single operation

**When to choose BASE/eventual consistency:**
- Social media feeds, like counts, view counters — stale data for seconds is acceptable
- User preferences, session state — availability matters more than strong consistency
- Globally distributed writes where cross-region synchronous replication latency is unacceptable
- Analytic workloads where approximate results are acceptable

## NoSQL Data Modeling Patterns

### Document Model: Embed vs. Reference

The core document modeling question is whether to embed related data within a document or store it as a separate document and reference it.

**Embed when:**
- The nested data is always accessed together with the parent (a blog post and its tags)
- The nested data has a bounded size (a user profile and their 3-5 addresses)
- The nested data doesn't need to be queried or updated independently
- Strong consistency between parent and nested data is required

```json
// Embedded: post with comments (reads always need both)
{
  "_id": "post-123",
  "title": "Introduction to Kubernetes",
  "body": "...",
  "comments": [
    {"author": "alice", "text": "Great post", "created_at": "2024-01-15"},
    {"author": "bob", "text": "Very helpful", "created_at": "2024-01-16"}
  ]
}
```

**Reference when:**
- The nested data grows without bound (a post can have thousands of comments)
- The nested data is accessed independently (user profile read separately from their orders)
- The same entity is shared across multiple parents (an author referenced by many posts)
- You need to query or aggregate across the nested entities

```json
// Referenced: order references customer and product IDs
{
  "_id": "order-456",
  "customer_id": "customer-789",
  "items": [
    {"product_id": "product-101", "quantity": 2, "unit_price": 29.99}
  ]
}
```

Reference trades read simplicity (no join in the query result — you do application-level joins) for write simplicity and data consistency.

### Key-Value Patterns

Key-value stores (Redis, DynamoDB single-table, Memcached) require upfront knowledge of access patterns — you design the key to serve the query directly.

**Compound keys for range queries** (DynamoDB pattern):
- Partition key distributes data across shards. Same partition key = same shard = can range-query.
- Sort key provides ordering within a partition and enables range queries.

```
Table: UserActivity
PK: user#alice
SK: 2024-01-15T00:00:00  (ISO timestamp for range queries)

Query: all activity for user alice in January 2024
→ PK = "user#alice", SK BETWEEN "2024-01-01" AND "2024-01-31"
```

**Single-table design** (DynamoDB): store multiple entity types in one table, using overloaded PK/SK to serve different access patterns. Requires knowing all access patterns before designing.

### Wide-Column Time-Series (Cassandra/ScyllaDB)

Time-series data maps well to wide-column stores. The partition key determines which node holds the data; the clustering key determines row ordering within the partition.

```sql
-- Cassandra CQL
CREATE TABLE sensor_readings (
    sensor_id   UUID,
    reading_at  TIMESTAMP,
    value       DOUBLE,
    PRIMARY KEY (sensor_id, reading_at)
) WITH CLUSTERING ORDER BY (reading_at DESC);

-- Query: last 100 readings for a sensor (no full partition scan)
SELECT * FROM sensor_readings
WHERE sensor_id = ?
ORDER BY reading_at DESC
LIMIT 100;
```

Design concern: unbounded partition growth. If a sensor writes every second for years, the partition grows indefinitely. Solution: bucket partitions by time period.

```sql
CREATE TABLE sensor_readings (
    sensor_id   UUID,
    bucket      DATE,          -- partition key includes date bucket
    reading_at  TIMESTAMP,
    value       DOUBLE,
    PRIMARY KEY ((sensor_id, bucket), reading_at)
) WITH CLUSTERING ORDER BY (reading_at DESC);
```

Now each partition holds at most one day of readings.

## Database Design for Specific Domains

### E-Commerce: Products, Orders, Inventory

```sql
CREATE TABLE products (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT,
    base_price      NUMERIC(10, 2) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Variants handle size/color combinations
CREATE TABLE product_variants (
    id          BIGSERIAL PRIMARY KEY,
    product_id  BIGINT NOT NULL REFERENCES products(id),
    sku         TEXT NOT NULL UNIQUE,
    price       NUMERIC(10, 2),          -- NULL = use product base_price
    attributes  JSONB NOT NULL DEFAULT '{}'  -- {"size": "M", "color": "blue"}
);

CREATE TABLE inventory (
    variant_id          BIGINT NOT NULL REFERENCES product_variants(id),
    warehouse_id        BIGINT NOT NULL REFERENCES warehouses(id),
    quantity_on_hand    INT NOT NULL DEFAULT 0 CHECK (quantity_on_hand >= 0),
    quantity_reserved   INT NOT NULL DEFAULT 0 CHECK (quantity_reserved >= 0),
    PRIMARY KEY (variant_id, warehouse_id)
);

-- Inventory reservation for cart items uses SELECT FOR UPDATE
-- to prevent overselling
BEGIN;
SELECT quantity_on_hand, quantity_reserved
FROM inventory
WHERE variant_id = 42 AND warehouse_id = 1
FOR UPDATE;  -- Lock the row

UPDATE inventory
SET quantity_reserved = quantity_reserved + 1
WHERE variant_id = 42 AND warehouse_id = 1
  AND (quantity_on_hand - quantity_reserved) >= 1;  -- Check availability in same statement

COMMIT;
```

**Interview point**: explain the `SELECT FOR UPDATE` pattern and why it prevents the TOCTOU (time-of-check to time-of-use) race condition that would allow overselling.

```sql
CREATE TABLE orders (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id),
    status      TEXT NOT NULL DEFAULT 'pending',
    total       NUMERIC(10, 2) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE order_items (
    order_id    BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    variant_id  BIGINT NOT NULL REFERENCES product_variants(id),
    quantity    INT NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(10, 2) NOT NULL,  -- Denormalized: price at time of order
    PRIMARY KEY (order_id, variant_id)
);
```

`unit_price` is intentionally denormalized — if the product price changes, historical orders should reflect what was paid, not the current price.

### Social Network: Users, Follows, Feed

The follow graph is the hardest part to model. Two approaches:

**Adjacency list** (works for small-medium scale):
```sql
CREATE TABLE follows (
    follower_id BIGINT NOT NULL REFERENCES users(id),
    followee_id BIGINT NOT NULL REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (follower_id, followee_id),
    CHECK (follower_id != followee_id)
);

CREATE INDEX idx_follows_followee ON follows(followee_id);
-- Needed for "who follows this user?" query (reverse lookup)
```

**Feed generation**: two patterns with different trade-offs:

*Pull (fan-out on read)*: When a user opens their feed, query the most recent posts from everyone they follow.
```sql
SELECT p.*
FROM posts p
WHERE p.user_id IN (
    SELECT followee_id FROM follows WHERE follower_id = :current_user_id
)
ORDER BY p.created_at DESC
LIMIT 20;
```
Simple to implement. Degrades when a user follows thousands of accounts or when a single account has millions of followers (celebrity problem).

*Push (fan-out on write)*: When a user posts, insert a row into each follower's feed table.
```sql
-- When user 5 posts something, insert into feeds of all followers
INSERT INTO user_feeds (user_id, post_id, created_at)
SELECT follower_id, :post_id, NOW()
FROM follows
WHERE followee_id = 5;
```
Reads are O(1) — just read from the user's pre-computed feed. Writes are expensive for users with millions of followers (Twitter used this; had to skip fan-out for Beyoncé posts and inject them at read time — a hybrid approach).

### Messaging: Threads and Messages

```sql
CREATE TABLE conversations (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE conversation_participants (
    conversation_id BIGINT NOT NULL REFERENCES conversations(id),
    user_id         BIGINT NOT NULL REFERENCES users(id),
    joined_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_read_at    TIMESTAMPTZ,   -- Tracks unread message count
    PRIMARY KEY (conversation_id, user_id)
);

CREATE TABLE messages (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES conversations(id),
    sender_id       BIGINT NOT NULL REFERENCES users(id),
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at DESC);
```

**Unread count query** (efficient with `last_read_at`):
```sql
SELECT COUNT(*) AS unread_count
FROM messages m
JOIN conversation_participants cp
    ON cp.conversation_id = m.conversation_id AND cp.user_id = :user_id
WHERE m.conversation_id = :conversation_id
  AND m.created_at > COALESCE(cp.last_read_at, '1970-01-01')
  AND m.sender_id != :user_id;
```

## Common Candidate Mistakes in DB Design Interviews

**Using VARCHAR with an enormous limit instead of TEXT.** In PostgreSQL, `VARCHAR(255)` and `TEXT` have identical storage characteristics — there's no performance difference. The `255` limit is a holdover from MySQL days. Use `TEXT` with a CHECK constraint if you actually need to enforce a length.

**Forgetting to normalize junction tables.** Many candidates design a user-post relationship as `user_liked_posts TEXT[]` (storing post IDs in an array). This violates 1NF, prevents efficient queries ("find all users who liked post X"), and makes foreign key enforcement impossible.

**Not discussing locking when designing inventory or financial schemas.** Saying "check if stock > 0, then decrement" without mentioning `SELECT FOR UPDATE` or optimistic locking demonstrates lack of production experience. Race conditions on inventory and balance are the most common data integrity bugs in e-commerce systems.

**Putting indexes on every column preemptively.** Indexes have write overhead — each index on a table adds cost to every INSERT, UPDATE, and DELETE. Candidates who say "I'd index all the foreign keys and all the WHERE clause columns" without discussing trade-offs reveal they haven't operated a write-heavy table.

**Not asking about access patterns before designing a NoSQL schema.** With relational databases you can add indexes after the fact. With key-value and wide-column stores, the primary key design determines which access patterns are efficient — you must know the queries upfront. Always ask "what queries will this schema serve?" before designing in a NoSQL context.

**Treating NULL incorrectly in queries.** `NULL = NULL` is NULL (not TRUE) in SQL. Use `IS NULL` and `IS NOT NULL`. A LEFT JOIN that filters on the right table's column in the WHERE clause becomes an implicit INNER JOIN — move that filter into the ON clause instead.

```sql
-- WRONG: this is effectively an INNER JOIN
SELECT u.*, o.id
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE o.created_at > '2024-01-01';  -- Filters out NULLs (users with no orders)

-- CORRECT: filter in ON clause to keep users with no orders
SELECT u.*, o.id
FROM users u
LEFT JOIN orders o ON o.user_id = u.id AND o.created_at > '2024-01-01';
```

**Designing for the happy path only.** Strong database design candidates explicitly discuss: what happens when a transaction fails mid-way, what cascades when a parent is deleted, how the schema handles timezone-aware timestamps (always use TIMESTAMPTZ, not TIMESTAMP), and how it handles concurrent updates to the same row.

## Preparation Timeline

**Week 1: SQL fluency**
- Write all window function variants from memory: ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, NTILE, running totals, moving averages
- Solve the classic questions: Nth salary, duplicates, consecutive dates, hierarchical queries
- Practice on a real database — set up PostgreSQL locally, load a public dataset (Stack Overflow data dump, NYC taxi trips)

**Week 2: Schema design and normalization**
- Design 3 complete schemas from scratch: e-commerce with inventory, social network, multi-tenant SaaS billing
- For each: walk through normalization, explain denormalization decisions, write the critical queries, discuss index strategy
- Study ACID isolation levels, practice explaining the anomalies each level prevents

**Week 3: Performance and systems depth**
- Run EXPLAIN ANALYZE on slow queries, learn to read every node type
- Implement a partial index, covering index, and GIN index; measure the difference
- Study the embed vs. reference decision in MongoDB; practice designing a document schema for a blog and a messaging app
- Review the ACID vs. BASE trade-off with concrete examples from systems you know

## The Database Design Mindset

The database engineers who perform best in design interviews share one habit: they design for the mutation, not just the query. It's easy to design a schema that makes reads elegant. The hard part is designing a schema where writes remain correct under concurrency, constraints enforce business rules without application-layer workarounds, and schema migrations 18 months later don't require a full rewrite.

When you present a schema in an interview, walk through what happens when: a row is deleted (what cascades?), two users try to modify the same row at the same time (what locking prevents corruption?), a transaction fails halfway through (what's left in an inconsistent state?). That line of thinking — designing for failure, not just the happy path — is what tells an interviewer you've shipped production database code.
