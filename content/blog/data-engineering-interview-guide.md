---
title: "Data Engineering Interview Guide"
description: "Technical interview preparation for data engineering roles: pipeline design with Spark and Airflow, data modeling (dimensional vs. data vault), streaming with Kafka and Flink, and what companies at every scale expect from data engineers."
date: "2026-03-19"
category: "Technical Skills Guides"
---

Data engineering interviews trip up a lot of strong engineers because the role sits in a weird middle ground. You need the SQL depth of an analyst, the systems thinking of a backend engineer, and the distributed computing knowledge of a platform engineer — but the job is none of those things. This guide covers what you actually need to know and what to expect in the loop.

## What Data Engineers Actually Build

Data engineers build and maintain the infrastructure that moves, transforms, and models data for analytics teams and ML systems. That means ingestion pipelines pulling from APIs, databases, and event streams; transformation jobs that clean and reshape raw data into analytics-ready tables; and data models that make it possible for a business analyst to write a SQL query without joining fifteen tables in their head.

The distinction that matters for interviews: data scientists consume clean data, backend engineers write to transactional systems optimized for reads and writes on individual records, data engineers build the pipelines that move data from those transactional systems into analytical stores. You own the plumbing, not the faucet or the sink.

## The Core Stack

Most data engineering interviews assume familiarity with this stack:

- **Python** for pipeline code, data manipulation (pandas for small data, PySpark for large)
- **SQL** at an advanced level (see below)
- **Apache Spark** for large-scale batch processing
- **Apache Airflow** for orchestration and scheduling
- **Kafka** for real-time event streaming
- **Cloud data warehouses**: Redshift (AWS), Snowflake, or BigQuery (GCP) — pick the one your target company uses and go deep
- **dbt** for SQL-based transformation layers
- **Cloud object storage**: S3 or GCS as the data lake layer

You do not need to be an expert in all of these before interviewing. Know Spark and Airflow well; have a working understanding of Kafka and a cloud warehouse.

## SQL Depth: Beyond Basic Queries

Data engineering SQL is not analytics SQL. You are expected to understand execution, not just syntax.

Window functions show up in almost every SQL challenge: `ROW_NUMBER`, `RANK`, `DENSE_RANK` for deduplication and ranking, `LAG`/`LEAD` for comparing a row to adjacent rows, and aggregate windows for running totals. Practice writing these against realistic schemas, not toy examples.

Beyond functions, you need to understand query execution: how the planner chooses between hash joins and merge joins, what partition pruning means and when it fires, why columnar storage (Parquet, ORC, the format underlying most warehouses) is fast for analytical reads and how that affects how you write queries. An interviewer asking "why is this query slow?" expects you to walk through the execution plan, not guess.

CTEs are table stakes. Know when to use them for readability versus when they create a performance problem by materializing an intermediate result in a system that does not optimize across CTE boundaries.

## Data Modeling: Schemas and Their Tradeoffs

The two modeling paradigms you will be asked about are dimensional modeling (star and snowflake schemas) and data vault.

**Star schema** puts a fact table at the center — orders, events, transactions — with dimension tables hanging off it: customers, products, time. Queries are simple, joins are predictable, and business users can navigate the model. The tradeoff is denormalization: you store redundant data in dimensions, and when dimensions change, you have to decide how to handle it.

**Slowly changing dimensions** (SCDs) are the mechanism for that decision. Type 1 overwrites old values, losing history. Type 2 adds a new row with effective dates, preserving full history at the cost of row count growth. Type 3 adds a column for the previous value, giving you one level of history without unbounded row growth. Most companies use Type 2 for customer and product data; you should be able to implement it in SQL or Spark.

**Snowflake schema** normalizes dimension tables further, reducing storage but adding join complexity. In practice, most teams start with star and tolerate some redundancy.

**Data vault** is an enterprise modeling approach that separates hubs (business keys), links (relationships between hubs), and satellites (attributes and history). It is more complex than dimensional modeling but handles schema evolution and auditability better. Know what it is and when to recommend it; do not expect to implement it from scratch in an interview.

## Spark: What You Actually Need to Know

Interviewers at data-heavy companies go deep on Spark internals.

Understand the API lineage: RDDs are the low-level abstraction (immutable distributed collections), DataFrames add schema and the Catalyst optimizer, Datasets add compile-time type safety (JVM only). In practice, write DataFrames; understand RDDs well enough to explain why DataFrames are usually faster.

**Narrow vs. wide transformations** is a core concept. Narrow transformations (map, filter, select) process each partition independently — no data movement across the cluster. Wide transformations (groupBy, join, distinct) require a shuffle, which is the expensive part of any Spark job. Every performance problem in Spark traces back to shuffle cost or partition imbalance.

For joins, know when to use a broadcast join (one side fits in memory — typically under a few hundred MB) versus a sort-merge join. Data skew — when one key has far more records than others — kills sort-merge join performance; the fix is salting or a skew hint if your Spark version supports it.

## Airflow: Pipelines That Actually Work in Production

DAG design questions come up in almost every data engineering interview.

Know the operator types: `PythonOperator` for arbitrary Python, `BashOperator` for shell commands, sensors for waiting on external conditions (S3 file sensor, external task sensor). Know that `XCom` passes small values between tasks but is not a mechanism for passing large datasets — large data should go through storage.

**Idempotency** is the most important concept in pipeline design. A pipeline is idempotent if running it multiple times produces the same result as running it once. In practice this means: use upserts rather than appends, partition output by date so reruns overwrite only the relevant partition, and never increment counters or timestamps in a way that changes on rerun. Interviewers will probe this directly: "what happens if this pipeline runs twice?"

Backfill strategy follows from idempotency: if your pipeline is idempotent, backfilling is just running historical dates in order. If it is not, backfilling is a production incident waiting to happen.

## Streaming: Kafka and Stream Processing

For Kafka, know: topics partition data for parallelism, consumer groups enable multiple applications to read the same topic independently, and offsets track where a consumer is in a partition. Understand at-least-once versus exactly-once delivery semantics and why exactly-once is expensive (it requires coordination between the producer, broker, and consumer).

For stream processing, the two main choices are Spark Structured Streaming and Apache Flink. Flink has lower latency and better support for stateful stream processing; Spark Streaming integrates well if you already have a Spark stack. For interviews, understand watermarks (how long to wait for late-arriving data before closing a window) and the distinction between event time and processing time.

## What the Interview Loop Looks Like

Expect three types of questions:

**SQL challenge**: a complex query involving window functions, multiple CTEs, or a deduplication problem. Practice on StrataScratch and LeetCode's SQL section.

**Pipeline design**: "design an ingestion pipeline for clickstream data from our web app to our data warehouse." Walk through source, ingestion mechanism, landing zone, transformation, data model, and observability. Cover failure modes and idempotency.

**System design**: "design a data warehouse for an e-commerce company." Cover the warehouse platform, table structure (facts and dimensions), transformation layer (dbt models), and how you would handle a late-arriving order that affects a metric from last month.

## How to Prepare

Complex SQL is the highest-leverage practice. Spend a week working through hard problems on StrataScratch (which uses realistic data schemas) before your loop.

Build a personal pipeline project: pick a public API, ingest it on a schedule with Airflow, transform it with dbt, and load it into a free-tier BigQuery or Snowflake instance. Having a project to walk through in a design question is worth more than memorizing documentation.

Read the dbt documentation on materializations (table, view, incremental, snapshot) and understand when to use each. Incremental models and snapshots map directly to SCD Type 2 and idempotency — two of the most common interview topics.

The gotchas that eliminate candidates are usually not technical knowledge gaps. They are shallow answers on idempotency ("we just rerun it"), no opinion on when to partition data, and system design answers that ignore cost. Cloud data warehouse queries scan data; partitioning reduces what gets scanned; this is not optional at scale. Have a point of view on it.
