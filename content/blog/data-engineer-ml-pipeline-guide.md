---
title: "Data Engineer Interview Guide: ETL Pipelines, dbt, and the Modern Data Stack"
description: "Ace data engineering interviews — batch vs. streaming ETL, dbt models and testing, Apache Spark architecture, data lakehouse patterns, data quality, and orchestration with Airflow."
date: "2026-03-20"
category: "Specialty Engineering Roles"
---

# Data Engineer Interview Guide: ETL Pipelines, dbt, and the Modern Data Stack

Data engineering interviews test a distinct set of skills: pipeline architecture, distributed systems for data workloads, SQL at scale, and the modern toolchain that has emerged around cloud data warehouses. Companies like Airbnb, Stripe, Databricks, dbt Labs, and every data-intensive startup are hiring data engineers who can design reliable, testable, production-grade data pipelines. Here's what they actually evaluate.

## Batch vs. Streaming ETL: The Foundational Question

Almost every data engineering interview opens with some version of this question. You need a crisp, accurate answer and the judgment to know which approach fits which problem.

**Batch processing:**
- Data is collected over a period and processed as a group (hourly, daily, weekly)
- Higher latency acceptable; throughput and cost efficiency are the optimization targets
- Tools: Apache Spark, dbt (transformations), Airflow (orchestration), Snowflake/BigQuery (compute)
- Right for: end-of-day financial reports, weekly user cohort analysis, nightly data warehouse loads

**Streaming processing:**
- Data is processed continuously as events arrive, targeting low latency (seconds or milliseconds)
- Tools: Apache Kafka (event bus), Apache Flink or Spark Structured Streaming (processing), Apache Iceberg or Delta Lake (storage)
- Right for: fraud detection (act before the transaction clears), real-time dashboards, event-driven microservices

*"How would you decide between batch and streaming for a new pipeline?"*
The honest answer is: start with batch unless you have a business requirement for sub-minute latency. Streaming systems are significantly harder to operate — exactly-once semantics, watermark handling for late-arriving data, stateful processing, and reprocessing on failure all add complexity. At most companies, a 15-minute batch job is indistinguishable from "real-time" for the end user.

**Lambda architecture — when it comes up:**
Lambda architecture runs both batch and streaming in parallel: the speed layer (streaming) provides low-latency approximate results; the batch layer periodically recomputes the ground truth and overwrites. The criticism is operational complexity (two code paths to maintain). Kappa architecture simplifies this by using a replayable event log (Kafka) as the source of truth and running only a streaming layer.

## dbt: Models, Testing, and the Analytics Engineering Model

dbt (data build tool) has become the standard for transformation in the modern data stack. If you're interviewing at a company that uses Snowflake, BigQuery, Redshift, or Databricks SQL, expect dbt questions.

**Core concepts:**

- **Models** are SELECT statements. dbt compiles them into DDL/DML and materializes them as tables or views in the warehouse. The lineage graph (DAG) is derived from `ref()` dependencies between models.
- **Materializations**: `view` (recomputed on query), `table` (full recompute each run), `incremental` (append or merge new rows only), `ephemeral` (CTEs inlined into dependent models, no warehouse object created)

*"When would you use an incremental model over a table model?"*
Incremental models are essential for large tables where full recompute is too slow or expensive. The trade-off: you need a reliable `updated_at` or event timestamp column, and you must decide what to do with late-arriving data (the `is_incremental()` filter only catches known-late rows if you expand the lookback window). Full table refreshes are simpler and less error-prone — use incremental only when the table size justifies the complexity.

**dbt testing:**
- **Schema tests** (now generic tests): `not_null`, `unique`, `accepted_values`, `relationships` — declare in YAML, dbt generates the SQL
- **Singular tests**: custom SQL assertions in `tests/` directory — any query that returns rows is a test failure
- **dbt-expectations** (community package): statistical tests, regex checks, `expect_column_values_to_be_between`

Interviewers will ask: *"How do you test a dbt model that aggregates daily revenue?"*
A strong answer: `unique` + `not_null` on the grain key (date + product_id), `not_null` on the revenue column, a singular test asserting revenue is never negative, and a relationship test back to the source orders model. For critical financial models, add a row-count threshold test comparing against yesterday's value.

## Apache Spark Architecture

Spark remains the dominant engine for large-scale data processing. Expect architecture questions, especially for roles involving data lakes or ML feature engineering.

**Execution model:**
- **Driver** program: defines the computation, builds the logical plan, negotiates with the cluster manager for executors
- **Executors**: JVM processes on worker nodes that run tasks and cache data
- **DAG Scheduler**: converts the logical plan into stages, splits at shuffle boundaries
- **Task Scheduler**: assigns tasks within a stage to executors

*"What is a shuffle in Spark and why is it expensive?"*
A shuffle happens when data must be redistributed across partitions — for example, during a `groupBy`, `join`, or `repartition`. Shuffle involves writing intermediate data to disk and transferring it over the network, which breaks pipelining and is usually the bottleneck in Spark jobs. Strategies to minimize shuffles: broadcast joins (for small tables), partition pruning, bucketing on join keys.

**Common interview gotcha — data skew:**
When one partition has dramatically more data than others (e.g., a `groupBy` where one key has 80% of the rows), the task processing that partition becomes the bottleneck. Fixes: salting (add a random prefix to the key, aggregate in two passes), AQE (Adaptive Query Execution in Spark 3+) which automatically handles skew splits.

## Data Lakehouse Patterns

The lakehouse pattern has largely replaced the two-tier lambda architecture at modern companies. Key concepts:

**Delta Lake / Apache Iceberg:**
These open table formats add ACID transactions, schema evolution, and time travel to data stored in object storage (S3, GCS). The core innovation: a transaction log (Delta) or metadata layer (Iceberg) that tracks which Parquet files belong to which version of a table.

*"What is time travel and when is it useful?"*
Time travel lets you query a table as it existed at a prior point in time or version number. Use cases: debugging pipeline failures (compare current vs. yesterday's state), regulatory compliance (reconstruct data as-of a reporting date), and safely rolling back a bad transformation run.

**The medallion architecture (Bronze / Silver / Gold):**
- **Bronze**: raw ingestion, exactly as received from source, no transformations, schema-on-read
- **Silver**: cleaned, validated, deduplicated, conformed data types — the "single source of truth" layer
- **Gold**: business-level aggregations and feature tables, optimized for consumption by analysts and ML models

This pattern comes up in system design rounds. Know the trade-offs: Bronze is cheap to write (no transformation failures) but expensive to query. Gold is fast to query but expensive to maintain (changes ripple forward from Bronze). Silver is the critical quality gate.

## Data Quality and Orchestration

Data quality is a first-class concern in mature data engineering organizations.

**Data quality dimensions:** completeness, uniqueness, timeliness, validity (conforms to business rules), consistency (agrees with other sources), accuracy (matches ground truth).

**Tooling:** Great Expectations and Soda for declarative quality checks; Monte Carlo and Bigeye for ML-driven anomaly detection (automated data observability). Know the difference: declarative checks enforce known rules; observability platforms catch unknown-unknown issues like sudden schema changes or volume drops.

**Airflow for orchestration:**

Airflow remains the dominant open-source orchestrator. Key concepts for interviews:
- **DAGs** are Python objects, not YAML — dynamic DAG generation from config is common
- **Operators**: `PythonOperator`, `BashOperator`, `BigQueryOperator`, `SparkSubmitOperator`; modern pattern is `@task` decorator with the TaskFlow API
- **XComs**: mechanism for passing small values between tasks (task outputs); not appropriate for large datasets — use intermediate storage (S3, GCS) instead
- **Sensors**: wait for external conditions (`FileSensor`, `S3KeySensor`, `ExternalTaskSensor`)

*"What happens when an Airflow DAG run fails halfway through?"*
Failed task turns orange/red. Downstream tasks are skipped (default) or can be configured to run anyway. Re-run options: `Clear` the failed task (resets it to scheduled, upstream still succeeded so they don't re-run) or `Clear` the entire DAG run. Interviewers probe whether you understand idempotency here — every task should produce the same output whether run once or ten times.

## Preparation Timeline

**Weeks 1-2:** SQL at scale — window functions, CTEs, query optimization (EXPLAIN plans, partition pruning, index selection). Write 20+ medium-hard SQL problems from scratch. Practice explaining your query plan aloud.

**Weeks 3-4:** dbt and the modern data stack. Build a dbt project from scratch: staging models from a raw source, intermediate models, a mart with business logic, schema tests throughout. Deploy it against a free-tier BigQuery or Snowflake account.

**Weeks 5-6:** Spark architecture and system design. Practice designing pipelines: "design an ML feature store," "design a data quality monitoring system," "design a real-time fraud detection pipeline." Use the medallion architecture as a starting framework and justify your choices.

The data engineers who stand out in interviews are not those who know every tool — they're the ones who reason clearly about trade-offs: batch vs. streaming, incremental vs. full refresh, declarative quality checks vs. observability. Build the judgment to make and defend those trade-offs, and the technical depth to back it up.
