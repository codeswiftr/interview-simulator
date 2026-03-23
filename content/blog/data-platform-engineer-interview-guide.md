---
title: "Data Platform Engineer Interview: Lakehouse, Spark, and Modern Data Stack"
description: "A complete guide to data platform engineer interviews: lakehouse architecture, Spark internals, Delta Lake, dbt, orchestration, and what companies expect from senior candidates."
date: "2026-03-20"
category: "Specialty Role Interviews"
---

# Data Platform Engineer Interview: Lakehouse, Spark, and Modern Data Stack

The data platform engineer role has crystallized around a specific set of technologies and architectural patterns. Unlike data engineers who primarily build pipelines, data platform engineers build and own the infrastructure that other data engineers and analysts run on. Interviews for this role probe both systems depth and the ability to make architectural trade-offs.

## What the Role Actually Owns

Data platform engineers typically own:

- The storage and compute infrastructure (Databricks/Spark clusters, Snowflake warehouses, S3/GCS/ADLS)
- Table formats and data lake management (Delta Lake, Apache Iceberg, Apache Hudi)
- Transformation layer infrastructure (dbt projects, model materialization strategy, warehouse cost management)
- Orchestration platform (Airflow, Prefect, Dagster — not just using it, owning its operation)
- Data quality and observability infrastructure (Great Expectations, Monte Carlo, custom frameworks)
- Ingestion infrastructure (Fivetran, Airbyte, Debezium, custom Kafka consumers)

This is distinguished from a data analyst or analytics engineer role by the emphasis on platform reliability, scalability, and cost management rather than business logic.

## Lakehouse Architecture

The lakehouse pattern stores data in open formats on object storage (S3/GCS) while adding ACID transaction semantics, schema enforcement, and optimized query performance on top.

**Delta Lake** (developed by Databricks, now open-source) uses a transaction log (`_delta_log`) stored alongside Parquet files to implement optimistic concurrency control. Every write appends a JSON log entry describing the operation. Reads reconstruct the table state by replaying the log. This enables:

- ACID transactions without a separate metadata store
- Time travel: `SELECT * FROM table TIMESTAMP AS OF '2026-01-01'`
- Schema evolution with `MERGE INTO` semantics
- Z-ordering: co-locating related data within files to reduce scanned bytes for common query patterns

**Apache Iceberg** is the other major table format, backed by Apple, Netflix, and the broader open-source community. Iceberg's metadata is organized differently — a snapshot tree rather than a linear log — and it has stronger partition evolution semantics. In interviews, demonstrate awareness of format trade-offs: Delta is tightly integrated with Databricks; Iceberg has broader multi-engine support (Trino, Spark, Flink all read Iceberg natively).

## Spark Internals You Need to Know

Senior interviews test whether you understand Spark beyond "it runs distributed compute."

**DAG and stage boundaries**: Spark builds a Directed Acyclic Graph of transformations. Stage boundaries occur at shuffle operations (`groupBy`, `join`, `distinct`). Data within a stage moves without network transfer; between stages it shuffles. Minimizing shuffle is the primary performance optimization lever.

**Catalyst optimizer**: Spark SQL and DataFrames go through Catalyst, which applies logical and physical plan optimizations — predicate pushdown, constant folding, broadcast hash join decisions. Understanding Catalyst explains why expressing operations as DataFrame transformations rather than RDD operations enables automatic optimization.

**Broadcast joins**: When one side of a join is small enough (`spark.sql.autoBroadcastJoinThreshold`, default 10MB), Spark broadcasts it to all executors, eliminating shuffle. Explicitly using `broadcast()` hint for dimension tables in fact-dimension joins is a standard pattern.

**Skew handling**: Data skew (some partition keys having disproportionately more data) causes some tasks to take 10-100x longer than others, stalling the stage. Solutions: salting (adding a random prefix to skewed keys, joining twice), Adaptive Query Execution (AQE) with `coalescePartitions` and skew join optimization (PySpark 3.0+), or repartitioning before the join.

**Delta Lake OPTIMIZE and VACUUM**: Small file problems are endemic in streaming and incremental batch workloads. `OPTIMIZE` compacts small files into larger ones (default 1GB target). `VACUUM` removes files no longer referenced by the transaction log, with a minimum 7-day retention for time travel.

## dbt at Platform Scale

Data platform engineers own dbt infrastructure, not just models. Interview topics:

**Materialization strategy**: Decide when to use `table` vs `view` vs `incremental` vs `ephemeral`. Incremental models require a reliable `unique_key` and `updated_at` predicate. Senior candidates can articulate when incremental models fail (late-arriving data, logic changes that require full refresh) and how to handle them.

**dbt testing**: `not_null`, `unique`, `accepted_values`, and `relationships` tests are standard. Custom generic tests via macros extend coverage. Source freshness checks (`dbt source freshness`) detect ingestion failures upstream of your models.

**dbt on Databricks/Snowflake**: Know the adapter-specific optimizations — `databricks_partitioned_by` for Delta tables, Snowflake clustering keys, query tag propagation for cost attribution.

## Orchestration: Airflow vs Prefect vs Dagster

The platform engineer owns orchestration infrastructure. Key interview differentiation:

**Airflow** is the established standard — broad ecosystem, DAG-centric model, scheduler reliability issues at scale (SQLite → Postgres, Celery/Kubernetes executor). The pain points (DAG parsing time, scheduler bottlenecks, complex dynamic DAG patterns) are well-known.

**Prefect** and **Dagster** take different approaches to the DAG model. Dagster's asset-based model (`@asset` decorator) makes data assets the first-class concept rather than tasks — this maps well to the dbt model where transformations produce assets. Dagster's software-defined assets allow lineage-aware scheduling.

**Platform engineer question**: "How would you handle a Airflow scheduler that is falling behind processing 5,000 DAGs?" Expect a discussion of parallelism config, DAG file processing interval, executor choice, and whether consolidating small DAGs makes sense.

## Compensation

Data platform engineers command premiums over general data engineering:

- **Mid-level**: $140,000–180,000 base (US) / 120–160K EUR (Western Europe)
- **Senior**: $180,000–240,000 base (US) / 150–200K EUR
- **Staff/Principal**: $240,000–320,000+ total comp (US, with equity)

Databricks-certified and Snowflake-certified candidates have measurable premium in the market, particularly at smaller companies that cannot hire specialists.

---
