---
title: "Data Engineer Deep Dive Interview Guide"
description: "Advanced data engineering interview preparation: batch vs. streaming architecture, data modeling (Kimball vs. Vault), dbt for transformation, Apache Spark internals, and what companies like Databricks, Snowflake, dbt Labs, and data-mature tech companies expect from senior data engineers."
date: "2026-03-19"
category: "Technical Skills Guides"
---

Senior data engineering interviews have shifted. It is no longer enough to know SQL and how to run an ETL job. Interviewers at Databricks, Snowflake, dbt Labs, and data-mature product companies expect you to reason about trade-offs — between modeling paradigms, processing architectures, and toolchain decisions — and to explain your choices under real constraints. This guide covers the technical depth those conversations require.

## Data Warehouse Design: Kimball vs. Data Vault

### Kimball Star Schema

The Kimball approach centers on fact tables (measurements, transactions) surrounded by denormalized dimension tables (who, what, where, when). A `fact_orders` table holds foreign keys to `dim_customer`, `dim_product`, and `dim_date`, plus numeric measures like `revenue` and `quantity`.

Key concepts interviewers probe:

- **Slowly Changing Dimensions (SCDs):** How do you handle a customer changing their address? SCD Type 1 overwrites in place (no history). SCD Type 2 adds a new row with `valid_from`/`valid_to` dates and a surrogate key (preserves history). SCD Type 3 adds a `previous_value` column (limited history). Know when each is appropriate — Type 2 is the default for anything that requires point-in-time accuracy.
- **Grain:** Every fact table must have a declared grain. "One row per order line item" is precise. "One row per order" is different. Mixing grains in a single table is a common bug that breaks aggregations.
- **Conformed dimensions:** `dim_date` and `dim_customer` should be reusable across multiple fact tables so metrics are consistent across subject areas.

Kimball is optimized for query performance and analyst usability. It is the right choice when your primary consumer is BI tooling and ad hoc SQL.

### Data Vault

Data Vault structures data into three object types: **Hubs** (unique business keys, e.g., customer ID), **Links** (relationships between hubs, e.g., order-to-customer), and **Satellites** (descriptive attributes with full history attached to a hub or link). Every record carries a load timestamp and a source system identifier.

This approach is designed for auditability and change resilience. Because attributes live in satellites and relationships live in links, adding a new source system or changing a business rule requires adding rows rather than restructuring existing tables. The trade-off is query complexity — analysts rarely query Data Vault directly. It is typically used as a raw vault layer that feeds a downstream Kimball or wide-table presentation layer.

Choose Data Vault when you have multiple source systems with conflicting keys, strict regulatory requirements for data lineage, or frequent structural changes from upstream.

## dbt: Transformation as Software Engineering

dbt treats SQL transformations as software. Each model is a single `SELECT` statement saved as a `.sql` file. dbt wraps it in `CREATE TABLE AS` or `CREATE VIEW AS` depending on the materialization strategy. This simplicity is the point — analysts write SQL, dbt handles the rest.

**Core concepts:**

- **`ref()` function:** Calling `ref('dim_customer')` instead of hardcoding a schema and table name lets dbt build a dependency graph and execute models in the correct order. It also handles environment-specific schema resolution.
- **Tests:** Schema tests (`not_null`, `unique`, `accepted_values`, `relationships`) run as generated SQL queries. Custom data tests are standalone `.sql` files that return rows on failure. Tests are your first line of defense against silent data quality regressions.
- **Macros:** Jinja-based reusable logic. Use macros for things like generating SCD Type 2 logic, dynamically pivoting columns, or standardizing date spine generation. Do not use macros to hide business logic that belongs in models.
- **Incremental models:** Instead of rebuilding a full table on every run, incremental models append or merge only new or changed rows using a filter like `where updated_at > (select max(updated_at) from {{ this }})`. This is critical for large fact tables. The risk is that late-arriving data or upstream restatements require a full refresh — always document when and why full refreshes are needed.

In interviews, be ready to explain how you structure a dbt project (staging, intermediate, marts layers), how you enforce contracts between teams (model contracts, meta fields), and how you handle environments (dev profiles, CI schema isolation).

## Apache Spark Internals

**RDD vs. DataFrame/Dataset:** RDDs are the low-level abstraction — distributed collections of JVM objects with no schema. DataFrames add a schema and route execution through the Catalyst optimizer, which generates an optimized physical plan. Use DataFrames unless you need custom serialization or are working in a context where the optimizer cannot help (rare).

**Lazy evaluation:** Transformations (`filter`, `groupBy`, `join`) build a logical plan but do not execute. An action (`collect`, `count`, `write`) triggers execution. This allows Catalyst to optimize the full plan before touching data — predicate pushdown, column pruning, and join reordering all happen here.

**Shuffle operations:** Any operation that requires redistributing data across partitions — `groupBy`, `join`, `repartition` — causes a shuffle. Shuffles write intermediate data to disk and transfer it over the network. They are the primary source of performance problems. Key mitigation strategies: broadcast joins for small tables (avoids shuffle on the larger side), partition pruning to reduce data volume before a shuffle, and salting keys to avoid data skew.

**Partitioning:** Default partition count after a shuffle is controlled by `spark.sql.shuffle.partitions` (default 200 — almost always wrong for your data size). Too few partitions means large tasks and OOM risk. Too many means scheduling overhead. A useful heuristic: target 100-200 MB per partition post-shuffle.

## Streaming vs. Batch

**Lambda architecture** runs parallel batch and streaming paths, merging results at query time. The batch layer reprocesses all data for correctness; the speed layer provides low-latency results. The problem is operational complexity — you maintain two codebases that must produce consistent results.

**Kappa architecture** eliminates the batch layer. Kafka retains the full event log with sufficient retention, and the streaming layer can reprocess historical data by replaying from the beginning. This works well when your streaming framework (Flink, Spark Structured Streaming) can handle reprocessing at batch speeds.

**Kafka** serves as the durable, ordered event log in both architectures. Producers write to topics, consumers read at their own offset. Partitioning enables parallelism; replication enables fault tolerance.

**Flink vs. Spark Streaming:** Flink is a true streaming system — it processes events one at a time with millisecond latency and has first-class support for event time, watermarks, and stateful operations. Spark Structured Streaming uses micro-batches (typically seconds). Flink has lower latency; Spark Structured Streaming integrates more naturally with the rest of a Spark-based batch stack.

**Exactly-once semantics** require coordination between the source (Kafka offset management), the processing layer (idempotent operations or transactional writes), and the sink (idempotent writes or transactional commits). It is harder than it sounds and is a frequent interview topic.

## The Modern Data Stack

The canonical stack: **Fivetran or Airbyte** for managed ingestion (source connectors, schema change handling), **dbt** for transformation, **Snowflake, BigQuery, or Databricks** for storage and compute, and **Looker or Metabase** for BI. Each layer has a clear responsibility. Interviewers want to see that you understand the boundaries — dbt does not move data, Fivetran does not transform it.

Databricks blurs the line between batch and streaming by unifying them on Delta Lake with ACID transactions, time travel, and schema enforcement.

## Data Quality and Observability

**Great Expectations** defines expectations (assertions about data) that can be run in a pipeline or as standalone checks. Results produce a Data Docs HTML report. It is code-first and integrates naturally with dbt and Airflow.

**Monte Carlo and Datafold** take a different approach — they monitor data automatically for anomalies (schema drift, null rate spikes, volume drops, distribution shifts) without requiring you to define every rule in advance. Monte Carlo positions itself as a "data observability" platform; Datafold specializes in diff-based testing when data changes between deploys.

Know the distinction: explicit contract testing (Great Expectations, dbt tests) catches known failure modes; observability platforms catch unknown regressions.

## Interview Patterns to Prepare For

**Pipeline design questions:** "Design a pipeline that ingests clickstream events and serves a dashboard of daily active users." Walk through ingestion, storage, transformation, and serving. State your assumptions about latency requirements, data volume, and existing infrastructure.

**Late-arriving data:** How do you handle events that arrive after their window has closed? Watermarks in Flink define how long to wait. In batch systems, reprocessing windows with `WHERE event_date >= cutoff` is standard. Be explicit about the trade-off between completeness and latency.

**Slow Spark job debugging:** Start with the Spark UI — check for data skew (one task taking 10x longer than others), excessive shuffle bytes, or a missing broadcast join. Look at partition counts and task sizes. Common fixes: broadcast hints, salting, repartitioning before a join, pushing predicates earlier in the plan.

**Modeling trade-offs:** Be ready to justify why you would choose a wide denormalized table over a normalized schema for a specific use case, or when you would accept duplication to improve query performance. There is no universal right answer — the correct answer is always tied to the query patterns and the team's ability to maintain the model.

The strongest candidates do not just describe what tools do. They explain what problem the tool solves, what it costs, and when they would choose something different.
