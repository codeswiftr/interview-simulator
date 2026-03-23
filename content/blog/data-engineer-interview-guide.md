# Data Engineer Interview Guide 2024: What's Actually Tested

Data engineering interviews have a distinct flavor from general SWE interviews. They test SQL depth, pipeline design, distributed processing frameworks, and data modeling — with less emphasis on classic DSA. Here's the complete breakdown of what to expect and how to prepare.

## Data Engineering vs. Data Science vs. Software Engineering

Data engineers sit at the intersection: they write production-quality code (like SWEs) but work primarily with data infrastructure (pipelines, warehouses, transformation layers). The confusion in job descriptions means you must read each JD carefully.

**Signs of a data-heavy role**: Spark, dbt, Airflow, Kafka, Snowflake/BigQuery/Redshift, data modeling, ETL/ELT
**Signs of an SWE-leaning role**: APIs for data access, Flink/real-time stream processing, custom storage systems

## Interview Format

Data engineering interviews vary more than SWE interviews by company tier:

**FAANG/tier-1:**
- 1-2 SQL/coding rounds
- 1 data modeling/warehouse design round
- 1 pipeline system design round
- 1 behavioral round

**Data-focused companies (Databricks, Snowflake, dbt Labs):**
- 1 hands-on SQL exercise (complex queries)
- 1 distributed systems / Spark design
- 1 product/data architecture discussion
- 1 behavioral

**Startups:**
- Often a take-home project (build a simple pipeline or transform a dataset)
- 1 technical deep-dive
- 1 culture/behavioral

## SQL: The Core Skill

SQL is to data engineers what algorithms are to SWEs. You must be fluent with complex queries, not just `SELECT * FROM table`.

### Window Functions (Asked in Almost Every Interview)

```sql
-- Running total of sales per region, ordered by date
SELECT
  region,
  sale_date,
  amount,
  SUM(amount) OVER (
    PARTITION BY region
    ORDER BY sale_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS running_total
FROM sales;

-- Rank customers by lifetime value within their cohort month
SELECT
  customer_id,
  DATE_TRUNC('month', signup_date) AS cohort,
  lifetime_value,
  RANK() OVER (
    PARTITION BY DATE_TRUNC('month', signup_date)
    ORDER BY lifetime_value DESC
  ) AS rank_in_cohort
FROM customers;
```

### CTEs and Recursive Queries

```sql
-- Find all employees and their full management chain
WITH RECURSIVE org_chart AS (
  -- Base case: top-level employees
  SELECT id, name, manager_id, 1 AS depth, ARRAY[id] AS path
  FROM employees
  WHERE manager_id IS NULL

  UNION ALL

  -- Recursive case: employees with managers
  SELECT e.id, e.name, e.manager_id, oc.depth + 1, oc.path || e.id
  FROM employees e
  JOIN org_chart oc ON e.manager_id = oc.id
)
SELECT * FROM org_chart ORDER BY path;
```

### Aggregation and Grouping (Common Interview Problems)

```sql
-- Month-over-month revenue growth
WITH monthly AS (
  SELECT
    DATE_TRUNC('month', order_date) AS month,
    SUM(revenue) AS revenue
  FROM orders
  GROUP BY 1
)
SELECT
  month,
  revenue,
  LAG(revenue) OVER (ORDER BY month) AS prev_month,
  ROUND(
    100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
    / NULLIF(LAG(revenue) OVER (ORDER BY month), 0),
    2
  ) AS growth_pct
FROM monthly;
```

### What Interviewers Look For in SQL

- **NULLIF for safe division** — avoid division-by-zero without defensive CASE statements
- **NULL handling** — `NULL` in aggregations (ignored), in JOINs (excluded from INNER, included in LEFT), in comparisons (`= NULL` is always false; use `IS NULL`)
- **Query optimization awareness** — can you spot when a window function would replace a correlated subquery?
- **Clarity** — readable CTEs vs. deeply nested subqueries; interviewers evaluate code style

## Data Modeling

Data modeling questions test your ability to design schemas for analytics workloads.

### Dimensional Modeling (Kimball)

The dominant paradigm for data warehouses:
- **Fact tables**: Metrics/measurements (orders, events, transactions) — wide, append-only, foreign keys to dimensions
- **Dimension tables**: Descriptive context (customers, products, time, geography) — slower-changing, surrogate keys
- **Star schema**: Fact table in center, dimension tables around it — optimized for read performance
- **Snowflake schema**: Normalized dimensions — less redundancy but more joins

**Type 2 Slowly Changing Dimensions (SCD2):** Track dimension history by adding `valid_from`, `valid_to` columns and a new row per change. Used when you need to report "what was this customer's segment at the time of the order?"

**Interview question:**
> "Design a data model for an e-commerce company that wants to analyze: total revenue by product category, cohort analysis of customer retention, and month-over-month growth by region."

Walk through: orders fact table, product/category dimension, customer dimension with SCD2 for cohort assignment, date dimension. Explain why each design decision supports the analytical queries.

### Data Vault (Emerging Pattern)

Used at companies with raw/enterprise data integration:
- **Hubs**: Business keys only
- **Links**: Relationships between hubs
- **Satellites**: Descriptive attributes + history

Not always tested, but knowing it exists and when it's appropriate (multi-source integration, auditability requirements) impresses interviewers at data-heavy companies.

## Pipeline Design: The System Design Equivalent

Data pipeline design is the system design round for data engineers.

**Common questions:**
- Design an ETL/ELT pipeline for ingesting data from 50 source systems into a data warehouse
- Design a real-time event pipeline for user activity tracking
- Design a data quality monitoring system
- Design a data lake architecture

**Framework for pipeline design:**

**1. Batch vs. streaming**
- Batch (daily/hourly): Airflow/dbt/Spark — most analytics workloads
- Streaming (real-time): Kafka/Flink — operational dashboards, fraud detection, real-time recommendations
- Micro-batch: Spark Structured Streaming — compromise; 1-5 minute latency

**2. ELT vs. ETL**
Modern pattern is ELT: Extract → Load raw → Transform in warehouse (dbt). Advantages: raw data always preserved, transformation logic versioned in SQL/dbt, compute runs on warehouse not separate Spark cluster.

Old pattern ETL: Transform before loading. Appropriate when transformations require business logic too complex for SQL, or when you can't store raw data (PII regulations).

**3. Data quality gates**
Every production pipeline needs:
- Row count checks (did we load expected volume?)
- Null checks on not-null fields
- Range/domain validation (order amounts > 0, dates in reasonable range)
- Freshness checks (last updated within expected window)
- Referential integrity checks (all order customer_ids exist in customers table)

Tools: dbt tests, Great Expectations, Soda Core.

**4. Idempotency and rerunnability**
Pipelines fail. Design for retry:
- Partitioned tables: `DELETE + INSERT` per partition instead of `APPEND` — safe to rerun
- `MERGE` statements for upserts: idempotent on natural key
- Checkpoint patterns for Spark streaming: exactly-once semantics via Kafka offsets + state store

**5. Orchestration patterns**
- Airflow: DAG-based, Python-native, battle-tested but complex
- Prefect/Dagster: Modern alternatives with better observability, dynamic DAGs
- Key features to discuss: dependency management, retry policies, alerting on failure, SLA monitoring

**Worked example: Real-time user activity pipeline**

*Source*: Mobile app → sends events (page views, clicks, purchases) → Kafka topic

*Pipeline*:
1. Kafka → Flink consumer: validate schema (Avro/Protobuf), enrich with user profile (Redis lookup), write to both Kafka (for downstream consumers) and data lake (Parquet on S3)
2. S3 → Spark batch job (hourly): aggregate sessions, compute funnel metrics, load to Snowflake
3. Snowflake → dbt: build `fct_sessions`, `fct_events`, `dim_users` models
4. Operational dashboard: Flink → Redis/Cassandra for real-time counters (active users, conversion rate)

*Data quality*: Schema registry in Kafka (Confluent) prevents malformed events; Great Expectations checks on Spark output before loading to warehouse; dbt tests on model output.

## Distributed Processing: Spark Fundamentals

Spark is tested at most companies with large-scale data engineering roles.

**Must-know concepts:**

**RDD vs. DataFrame vs. Dataset:**
- RDD: low-level, type-safe in Scala, no optimization
- DataFrame: SQL-like API, Catalyst optimizer, most performant for tabular data
- Dataset: typed DataFrame (Scala/Java only)

**Lazy evaluation and the DAG:**
Transformations are lazy — Spark builds a DAG of transformations, only executing when an action is called (`collect()`, `count()`, `save()`). Wide transformations (joins, groupBy) trigger shuffles.

**Shuffles and performance:**
Shuffles (groupBy, join, repartition) are expensive — data moves across the network. Optimize with:
- `broadcast()` for small tables in joins (avoids shuffle)
- Pre-partitioning on join keys
- Appropriate `spark.sql.shuffle.partitions` (default 200 is too many for small data)

**Partitioning:**
Partition by columns commonly used in filters (date, region). Balance partition size (~128MB each). Too few partitions → underutilization; too many → scheduler overhead.

**Common interview question:**
> "You have a Spark job that's running slowly. How do you diagnose and fix it?"

Walk through: Spark UI (stages with long duration, skewed partitions), check shuffle read/write size, look for data skew (one partition 10x larger than others — fix with salting or custom partitioner), check for unnecessary collect() calls, broadcast small tables.

## Behavioral: Data Engineering Edition

**"Tell me about a pipeline you built that had performance problems. How did you fix it?"**
Specific: what was slow (shuffle, query, I/O), how you diagnosed it, what you changed, measurable improvement.

**"How do you ensure data quality in your pipelines?"**
Walk through your quality framework: schema validation, freshness checks, anomaly detection, monitoring.

**"How do you handle schema changes from upstream sources?"**
Discuss: schema registry (Avro), backward/forward compatibility, alerting on breaking changes, migration strategies.

**"Tell me about a time you had to communicate a data issue to stakeholders."**
They want: ability to explain technical issues in business terms, proactive communication, clear remediation timeline.

## Preparation Timeline

**Week 1: SQL depth**
- Write 20 complex SQL queries: window functions, recursive CTEs, aggregations
- Practice explain/analyze on slow queries
- Study dimensional modeling patterns

**Week 2: Pipeline design**
- Design 3 pipelines: batch ETL, real-time streaming, data quality system
- Set up a local Airflow instance, build a simple DAG
- Learn dbt basics: models, tests, documentation

**Week 3: Spark + behavioral**
- Study Spark architecture, lazy evaluation, shuffle optimization
- Write 5 STAR behavioral stories covering data quality, pipeline failures, schema changes
- Practice explaining technical decisions to non-technical stakeholders

## The Data Engineer Mindset

The data engineers who excel in interviews think about their work as **enabling decisions**, not just moving data. Every pipeline serves an analyst, a product manager, or an ML model that makes a business decision. The best candidates understand that a buggy pipeline that silently produces wrong data is worse than a broken pipeline that fails loudly.

In every design question, ask: "What's the cost of bad data reaching this downstream consumer?" That question — and your answer — is what separates strong candidates from great ones.
