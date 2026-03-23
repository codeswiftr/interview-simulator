---
title: "Python for Data Engineering: Pandas, Spark, Airflow, and Production Data Pipelines"
description: "Data engineering interview prep with Python — pandas best practices, PySpark, Airflow DAG design, dbt, data quality, and the system design questions data engineers face."
date: "2026-03-20"
category: "Programming Languages"
---

# Python for Data Engineering: Pandas, Spark, Airflow, and Production Data Pipelines

Data engineering interviews test both Python proficiency and understanding of data systems at scale. Unlike software engineering interviews which focus on algorithms, data engineering interviews emphasize pipeline design, data quality, processing at scale, and orchestration. Here's what to prepare.

## Pandas: Interview Essentials

Pandas is the standard tool for data manipulation in Python. Interviewers expect fluency in:

**GroupBy and aggregation:**
```python
# Sales by region, with multiple aggregations
df.groupby('region').agg(
    total_revenue=('revenue', 'sum'),
    order_count=('order_id', 'count'),
    avg_order=('revenue', 'mean')
).reset_index()
```

**Window functions:**
```python
# Running total using expanding window
df['running_total'] = df.groupby('customer_id')['amount'].transform('cumsum')

# Rank within group
df['rank'] = df.groupby('region')['revenue'].rank(ascending=False, method='dense')
```

**Merge patterns:**
```python
# Left join + indicator to find missing records
merged = df1.merge(df2, on='key', how='left', indicator=True)
missing = merged[merged['_merge'] == 'left_only']
```

**Performance patterns:** Know when to use vectorized operations vs. apply (apply is slow — use it as last resort). Use `query()` for filtering (can be faster for large DataFrames). For truly large data, know when pandas isn't the right tool.

## PySpark: Distributed Processing

For large-scale data engineering, Spark is essential. Key concepts:

**RDDs vs DataFrames vs Datasets:** Use DataFrames (or Spark SQL) for data engineering — they benefit from the Catalyst optimizer and are significantly faster than RDDs for structured data.

**Transformations vs. Actions:** Transformations (map, filter, groupBy) are lazy — they build a DAG. Actions (collect, count, write) trigger execution. This is a common interview question: "Why is my Spark job slow?" Often because of too many small actions or collecting large DataFrames to the driver.

**Partitioning:** Spark processes data in partitions. `repartition()` reshuffles data across partitions (expensive — full shuffle). `coalesce()` reduces partitions without full shuffle (use for reducing partition count before writing). For joins and aggregations, ensure the join keys are well-distributed to avoid skew.

```python
from pyspark.sql import functions as F

# Broadcast join for small table
from pyspark.sql.functions import broadcast
result = large_df.join(broadcast(small_df), on='key')

# Window function in Spark
from pyspark.sql.window import Window
window = Window.partitionBy('user_id').orderBy('timestamp')
df.withColumn('prev_event', F.lag('event_type').over(window))
```

**Skew handling:** If one partition has far more data (e.g., one user_id has millions of rows), joins and aggregations become bottlenecked. Solutions: salting (add random prefix to key, join with exploded keys), skew hints, or broadcast joins.

## Airflow: Pipeline Orchestration

Airflow is the dominant workflow orchestration tool. Interview topics:

**DAG design:** DAGs define dependencies between tasks. Key principles: tasks should be idempotent (re-running produces the same result), atomic (succeed or fail completely), and catch up correctly if run after a delay.

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

dag = DAG(
    'etl_pipeline',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,  # Don't backfill historical runs
    default_args={'retries': 2, 'retry_delay': timedelta(minutes=5)}
)

extract = PythonOperator(task_id='extract', python_callable=extract_fn, dag=dag)
transform = PythonOperator(task_id='transform', python_callable=transform_fn, dag=dag)
load = PythonOperator(task_id='load', python_callable=load_fn, dag=dag)

extract >> transform >> load
```

**XCom:** Cross-task communication. Use sparingly — for passing small values (IDs, counts), not large data. Large data should go through storage (S3, database).

**Sensors:** Wait for external conditions (file arrival, API availability). Use with timeout and poke_interval configured appropriately.

**Common interview question:** "How do you handle failures in Airflow?" Answer: task-level retries with exponential backoff, failure callbacks for alerting, circuit breaker patterns using task state checks, dead letter queues for unprocessable records.

## Data Quality

Data quality is a common interview topic. Know the frameworks:

**Great Expectations:** Define expectations (column must be non-null, values must be in a set, distribution must match a baseline). Run as a step in the pipeline; fail or alert on violations.

**Data validation patterns:**
- Schema validation: check column names and types match expected schema
- Null checks: critical columns must meet null rate thresholds
- Range checks: numerical values within expected bounds
- Referential integrity: foreign keys exist in reference tables
- Freshness checks: data arrived within expected time window
- Row count reconciliation: downstream count ≈ upstream count

## SQL for Data Engineering

Data engineers are expected to write complex SQL fluently. Know window functions thoroughly:

```sql
-- Retention cohort analysis
WITH first_purchase AS (
    SELECT user_id, DATE_TRUNC('month', MIN(order_date)) AS cohort_month
    FROM orders
    GROUP BY user_id
),
monthly_activity AS (
    SELECT 
        f.cohort_month,
        DATE_TRUNC('month', o.order_date) AS activity_month,
        COUNT(DISTINCT o.user_id) AS active_users
    FROM orders o
    JOIN first_purchase f USING (user_id)
    GROUP BY 1, 2
)
SELECT 
    cohort_month,
    DATEDIFF('month', cohort_month, activity_month) AS months_since_cohort,
    active_users
FROM monthly_activity
ORDER BY 1, 2
```

For data engineering interviews at analytics-heavy companies (Databricks, Snowflake, dbt Labs), SQL fluency with window functions, CTEs, and analytical patterns is tested as rigorously as Python.
