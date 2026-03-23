# Databricks Engineering Deep Dive: The Data Lakehouse, Photon, and What It Takes to Pass Their Bar

Databricks occupies a rare position in enterprise software: a $43B company built entirely on the thesis that unifying analytics and AI workloads on a single open platform beats the fragmented incumbents. They invented the data lakehouse pattern, open-sourced Apache Spark, Delta Lake, and MLflow, and have made those bets pay off at scale. If you're interviewing there, you're entering a company where nearly every senior engineer has published papers, shipped distributed systems used by thousands of enterprises, and has very specific opinions about query execution. This post breaks down the technical decisions that define Databricks' engineering culture — and what the interview process will probe.

---

## Apache Spark and the Photon Engine

Databricks was founded in 2013 by Matei Zaharia and the original Spark team from UC Berkeley's AMPLab. Spark's core insight was simple but revolutionary: instead of writing intermediate results to disk after every MapReduce step (Hadoop's approach), keep data in memory across transformations and only materialize when necessary. That shift from disk-bound to memory-bound computation unlocked 10-100x speedups for iterative algorithms.

But Spark's original execution engine had a fundamental ceiling: it compiled query plans down to JVM bytecode. JVM's JIT compiler is impressive, but it cannot match hand-tuned native code for tight inner loops. Columnar operations like filtering a billion-row parquet file, or aggregating with SIMD vectorization, hit a wall in Java.

**Photon** is Databricks' answer. Introduced in 2021, Photon is a C++ vectorized query engine that replaces the JVM-based execution layer for SQL and DataFrame operations. The key architectural decisions:

- **Columnar batch processing**: instead of processing one row at a time, Photon operates on batches of 1,000–10,000 rows per column vector. This allows SIMD (Single Instruction Multiple Data) CPU instructions to process 8–32 values per clock cycle.
- **Adaptive query execution**: Photon inherits Spark's AQE framework, which rewrites query plans at runtime based on actual partition statistics rather than estimates.
- **Transparent compatibility**: Photon is a drop-in replacement. The same DataFrame API compiles to Photon execution paths without changing application code.

The performance delta matters: Databricks benchmarks show Photon achieving 2-5x speedups over the standard Spark engine on TPC-DS workloads, primarily from eliminating JVM overhead in hot loops and leveraging CPU cache locality with columnar layouts.

For interviews, understand that Photon is architecturally similar to what DuckDB (OLAP), ClickHouse, and Velox (Meta's unified execution engine) do at the execution layer. The shift from row-oriented to columnar vectorized execution is one of the defining trends in modern query processing.

---

## Delta Lake: Solving the Data Swamp

Before Delta Lake, data lakes were often called "data swamps." The problem: object storage (S3, GCS, ADLS) is cheap and scalable, but it has no transaction semantics. If a Spark job writing 10,000 parquet files fails halfway through, you have a partially-written dataset with no rollback mechanism. Concurrent writers corrupt each other's output. Schema changes break downstream consumers silently.

Delta Lake, open-sourced by Databricks in 2019, adds a **transaction log** — a `_delta_log/` directory of JSON files — on top of standard parquet files. Every write operation appends a new commit entry describing the exact set of parquet files added or removed. This gives you:

- **ACID transactions** on object storage: optimistic concurrency control using conditional writes to the log. Writers read the current log version, compute their changes, and attempt to atomically append a new log entry. Conflicts are detected and retried.
- **Time travel**: because every version of the table is captured in the log, you can query any historical snapshot with `VERSION AS OF` or `TIMESTAMP AS OF`. This is invaluable for debugging data pipelines and regulatory compliance.
- **Schema evolution**: Delta Lake enforces schema on write by default (preventing silent schema drift) but supports explicit schema evolution — adding columns, widening types — with `mergeSchema` options.
- **Efficient upserts**: the `MERGE INTO` operation, a pain point in pure parquet lakes, is implemented efficiently via log-based file rewriting.

```python
from delta.tables import DeltaTable
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .getOrCreate()

# Write initial data
events_df.write.format("delta").save("/mnt/delta/events")

# Transactional upsert — atomic, no partial writes
delta_table = DeltaTable.forPath(spark, "/mnt/delta/events")

delta_table.alias("target").merge(
    updates_df.alias("source"),
    "target.event_id = source.event_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()

# Time travel — query yesterday's snapshot
spark.read.format("delta") \
    .option("timestampAsOf", "2024-01-01") \
    .load("/mnt/delta/events") \
    .show()
```

The transaction log is also the key to **Delta Live Tables** (Databricks' declarative ETL framework) and **Databricks SQL** — both rely on Delta Lake as the foundational storage layer. When interviewers at Databricks ask about storage engines or the reliability of streaming pipelines, Delta Lake's ACID model is the answer they're looking for.

---

## Unity Catalog: Governance Across the Lakehouse

As organizations adopted Delta Lake, they faced a new problem: data sprawl across multiple Databricks workspaces, cloud accounts, and storage buckets. Unity Catalog (GA in 2022) is Databricks' centralized data governance layer.

The core architectural decisions in Unity Catalog:

**Three-level namespace**: Unity Catalog introduces `catalog.schema.table` — a three-level hierarchy above the two-level `schema.table` that Hive Metastore used. This allows a single metastore to govern data across multiple business units and cloud environments while maintaining isolation through catalog-level permissions.

**Fine-grained access control**: Unity Catalog moves permissions down to the column and row level. Row-level security is implemented via dynamic views — Unity Catalog rewrites queries at the engine level to inject WHERE clauses based on the requester's identity. This happens transparently to the application.

**Automatic lineage tracking**: Unity Catalog captures column-level lineage automatically from query execution plans. When a Spark job reads `table_a.column_x` and writes to `table_b.column_y`, Unity Catalog records that relationship without requiring annotation. This is architecturally significant — lineage as a side effect of query execution rather than a separate instrumentation burden.

**Metastore architecture**: a single Unity Catalog metastore can be attached to multiple Databricks workspaces. The metastore itself is hosted by Databricks' control plane, separate from the customer's data plane (the compute clusters and storage buckets in the customer's cloud account). This separation of control and data planes is a deliberate security architecture.

---

## MLflow and the ML Lifecycle

Databricks' influence on the ML ecosystem extends beyond data engineering. MLflow, open-sourced in 2018, became the de facto standard for ML experiment tracking before most companies had a coherent answer to "how do we reproduce this model?"

MLflow's four components map directly to the ML lifecycle:

- **Tracking**: log parameters, metrics, and artifacts per run. Every `mlflow.log_metric("accuracy", 0.94)` call persists to a SQLite or remote backend, enabling comparison across experiments.
- **Projects**: packaging ML code as reproducible units with an `MLproject` file specifying the conda or docker environment and entry points.
- **Models**: a standard format for packaging models from any framework (scikit-learn, PyTorch, TensorFlow, XGBoost) with a consistent Python function interface.
- **Registry**: versioned model lifecycle management — `Staging`, `Production`, `Archived` stages with approval workflows.

Databricks has since extended MLflow with **Model Serving** (REST endpoints backed by autoscaling compute) and **Feature Store** (point-in-time correct feature retrieval to prevent training-serving skew). These additions reflect Databricks' strategic position: own the entire workflow from raw data in Delta Lake through feature engineering, model training, and production serving.

---

## What the Interview Actually Tests

Databricks runs one of the more rigorous technical bars in the industry. They recruit heavily from PhD programs (particularly systems, databases, and ML) but also hire strong generalist engineers who can operate in high-abstraction distributed systems.

**System design questions they favor**: "Design a distributed query engine" (tests your understanding of query parsing, logical/physical planning, execution, shuffle, and fault tolerance), "Design a data lakehouse" (tests your knowledge of storage layers, transaction semantics, and the compute/storage separation pattern), and "Design a feature store with point-in-time correctness" (tests ML platform thinking). Expect follow-ups about consistency models, failure modes, and performance at scale.

**Coding interview focus**: Databricks engineers write a lot of Scala and Python. Expect medium-to-hard algorithm questions, but also questions where distributed thinking matters — understanding when a naive in-memory approach fails at 100TB scale, or why sorting is central to shuffle-based joins. Data structure questions often involve trees and graphs because query plans are DAGs.

**Distributed systems depth**: questions about CAP theorem tradeoffs, how optimistic concurrency control works (Delta Lake's model), the semantics of exactly-once delivery in Spark Structured Streaming, and how Delta Lake's log compaction (OPTIMIZE and VACUUM operations) works are all fair game.

**"Data + AI" positioning**: Databricks is actively competing with Snowflake (analytics), Palantir (AI/ML platforms), and the hyperscalers. Engineers are expected to understand this competitive landscape and have opinions about where unified platforms win versus best-of-breed toolchains. Be prepared to discuss tradeoffs honestly — Unity Catalog versus open table formats like Apache Iceberg and Apache Hudi is a topic where showing nuanced understanding signals seniority.

The common thread across all of it: Databricks rewards engineers who have internalized the why behind architectural decisions, not just the what. Know why columnar execution beats row-oriented for analytics, why transaction logs beat in-place mutation for cloud storage, and why unified governance beats per-system ACLs. That reasoning instinct is what they're hiring for.
