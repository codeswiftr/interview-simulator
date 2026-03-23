---
title: "Databricks and Apache Spark Engineering: What the Interview Actually Tests"
description: "A technical deep dive into Databricks engineering interviews — covering Apache Spark internals, Delta Lake, MLflow, and the performance optimization problems that show up in every round."
date: "2026-03-19"
category: "Company Deep Dives"
---

Databricks engineering interviews are heavy on distributed systems fundamentals, but the lens is always Apache Spark. You will not get abstract graph theory questions. You will get "why is this Spark job slow, and how do you fix it?" If you understand how Spark executes queries — DAGs, shuffle, memory management, the catalyst optimizer — you can handle most of what they throw at you.

This guide covers the technical depth you need: Spark internals, Delta Lake, MLflow, and the behavioral patterns that matter at Databricks specifically.

## Apache Spark Execution Model: What You Must Know Cold

Spark builds a Directed Acyclic Graph (DAG) of transformations before executing anything. This is lazy evaluation — calling `filter()`, `select()`, or `join()` does nothing until you trigger an action (`count()`, `collect()`, `write()`). Databricks interviewers will ask you to trace through a job and identify where stages break, where shuffles happen, and why.

**DAG to stages:** Spark breaks the DAG at shuffle boundaries. Each stage is a set of tasks that can run without moving data across the network. A `groupBy` or `join` on a non-broadcast table always creates a shuffle — data with the same key must land on the same partition.

**Tasks and partitions:** One task per partition per stage. Default is 200 partitions after a shuffle (`spark.sql.shuffle.partitions`). For large datasets this is too low; for small ones it creates overhead. Tune this based on data volume.

**RDDs vs DataFrames vs Datasets:** Know the evolution and why it matters.

- **RDD**: Low-level, no schema, no optimizer. You write what Spark does.
- **DataFrame**: Schema-aware, goes through Catalyst optimizer and Tungsten execution engine. This is what you should use.
- **Dataset**: Type-safe DataFrames (JVM only). Combines optimizer benefits with compile-time type checking. Python has no Dataset API — only DataFrames.

In interviews: if asked to compare them, anchor on the Catalyst optimizer. DataFrames and Datasets get query planning and code generation for free. RDDs do not.

## Shuffle Operations: The Root of Most Performance Problems

Shuffles are expensive because they write intermediate data to disk, serialize/deserialize it, and transfer it over the network. They are unavoidable for certain operations, but they can be minimized.

Operations that trigger shuffles: `groupBy`, `join` (non-broadcast), `distinct`, `repartition`, `orderBy`.

The most common interview scenario is diagnosing a slow join. Here is the difference between a bad pattern and a good one:

```python
# BAD: joining two large tables — triggers full shuffle on both sides
result = large_table.join(medium_table, on="user_id", how="inner")

# GOOD: if medium_table fits in memory (~10MB default threshold),
# use a broadcast join — no shuffle on the small side
from pyspark.sql.functions import broadcast

result = large_table.join(broadcast(medium_table), on="user_id", how="inner")
```

Spark can auto-broadcast tables below `spark.sql.autoBroadcastJoinThreshold` (default 10MB). For tables just above this threshold, manually set the hint or increase the threshold.

**Avoiding unnecessary shuffles:**

```python
# BAD: two separate groupBy operations = two shuffles
step1 = df.groupBy("region").agg({"revenue": "sum"})
step2 = df.groupBy("region").agg({"orders": "count"})
result = step1.join(step2, on="region")

# GOOD: combine into one groupBy = one shuffle
from pyspark.sql import functions as F

result = df.groupBy("region").agg(
    F.sum("revenue").alias("total_revenue"),
    F.count("orders").alias("order_count")
)
```

## Partitioning Strategy

Data skew is the second most common interview topic after joins. If one partition has 10x the data of others, that task becomes the bottleneck — all other tasks finish, and the job stalls waiting on the skewed partition.

```python
# Diagnosing skew: check partition sizes
df.rdd.mapPartitions(lambda it: [sum(1 for _ in it)]).collect()

# Fixing skew with salting: add a random prefix to distribute hot keys
import pyspark.sql.functions as F

salted = df.withColumn("salt", (F.rand() * 10).cast("int")) \
           .withColumn("salted_key", F.concat(F.col("user_id"), F.lit("_"), F.col("salt")))
```

**Partitioning on write:** When writing Parquet, partition by high-cardinality filter columns (date, region). This enables partition pruning at read time — Spark skips files entirely rather than reading and filtering.

```python
# Write with partition pruning in mind
df.write \
  .partitionBy("event_date", "region") \
  .mode("overwrite") \
  .parquet("/data/events/")

# Read benefits: only scans 2026-03-19/us-west/ instead of all partitions
spark.read.parquet("/data/events/").filter("event_date = '2026-03-19' AND region = 'us-west'")
```

## Delta Lake: ACID Transactions on Object Storage

Delta Lake is Databricks' core differentiator. It adds a transaction log (`_delta_log/`) on top of Parquet files, enabling ACID semantics, time travel, and schema enforcement. Interviews will ask how it works under the hood.

**Transaction log:** Every write appends a JSON entry to `_delta_log/`. This log records what files were added or removed. Reading a Delta table means reading the log to determine the current table state, then reading only the relevant Parquet files.

**Time travel:** Because the log is append-only and old Parquet files are retained until `VACUUM` runs, you can query any historical snapshot:

```python
# Read snapshot from 7 days ago
df = spark.read.format("delta").option("timestampAsOf", "2026-03-12").load("/delta/events")

# Read specific version
df = spark.read.format("delta").option("versionAsOf", 42).load("/delta/events")
```

**Merge (upsert):** Delta's `MERGE` is the correct answer for CDC (change data capture) pipelines. Interview question: "how do you handle late-arriving data or updates to existing records?"

```python
from delta.tables import DeltaTable

target = DeltaTable.forPath(spark, "/delta/customers")

target.alias("t").merge(
    updates.alias("u"),
    "t.customer_id = u.customer_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()
```

**Z-Ordering:** Co-locate related data within files to improve filter performance on columns not used for partitioning. Useful when you have multiple filter predicates on a large table.

## MLflow: The ML Platform Layer

Databricks built MLflow and integrates it deeply into the platform. If you are interviewing for an ML engineering or platform role, expect questions here.

The four components: **Tracking** (log parameters, metrics, artifacts per run), **Projects** (package code for reproducible runs), **Models** (standard format for model serialization), **Registry** (lifecycle management — staging, production, archived).

What interviewers want to know: how do you design an ML platform that handles experiment tracking at scale, model versioning, and A/B deployment? The answer usually involves MLflow Registry + Databricks Jobs + Feature Store, with a rollback story based on model version history.

## What Databricks Interviews Actually Test

**Round 1 — Coding:** Standard LC medium/hard, sometimes with a data-engineering flavor (streaming aggregations, implementing a simple task scheduler). Strong Python or Scala expected.

**Round 2 — System Design:** Design a large-scale data pipeline. Common prompts: real-time fraud detection, log ingestion at 1M events/sec, feature store for ML models. Expect to talk through Lambda vs Kappa architecture, exactly-once semantics, schema evolution.

**Round 3 — Spark Deep Dive:** Live debugging of a slow Spark job. You will be given a query plan or job timeline and asked to find the bottleneck. Study the Spark UI: stages tab, shuffle read/write metrics, task duration distribution.

**Round 4 — Behavioral:** Databricks values ownership and direct communication. Their behavioral themes center on "move fast without breaking things" — situations where you shipped something important quickly, handled production incidents, or disagreed with a technical decision and what you did about it.

## Databricks Tech Stack Snapshot

- **Compute:** Databricks Runtime (optimized Spark + Photon engine for SQL queries)
- **Storage:** Delta Lake on S3/ADLS/GCS
- **Orchestration:** Databricks Workflows (managed Jobs), also integrates with Airflow
- **ML:** MLflow, Feature Store, Model Serving (REST endpoints)
- **Languages:** Python (PySpark), Scala (core Spark), SQL, R (limited)
- **Infrastructure:** Kubernetes-based, multi-cloud (AWS/Azure/GCP)

## Preparation Checklist

Before your Databricks interview, you should be able to:

- Explain what happens when Spark executes a `groupBy` + `join` pipeline, from DAG construction through task scheduling
- Read a Spark execution plan (`df.explain(True)`) and identify broadcast joins, sort-merge joins, and exchange (shuffle) nodes
- Describe Delta Lake's transaction log format and how it provides ACID guarantees without a traditional database engine
- Design a CDC pipeline that handles late arrivals and deduplication
- Articulate the tradeoffs between streaming (Structured Streaming) and micro-batch architectures for a given SLA requirement

The core thesis of a Databricks interview is: can you reason about distributed data movement? Every performance question comes back to "where is data moving, why, and how do you reduce it?"
