---
title: "Data Warehouse Engineer Interview Guide: Dimensional Modeling, dbt, and Modern Data Stack"
description: "Data warehouse engineer interview preparation — Kimball dimensional modeling, dbt best practices, slowly changing dimensions, modern data stack (Snowflake/BigQuery + dbt + Airflow), and data quality testing."
date: "2026-03-20"
category: "Data Engineering"
---

# Data Warehouse Engineer Interview Guide: Dimensional Modeling, dbt, and Modern Data Stack

Data warehouse engineering has undergone a transformation with the modern data stack. Engineers who once built ETL pipelines in custom Python scripts now work with cloud-native warehouses, dbt for SQL transformations, and orchestration tools like Airflow or Dagster. Interviews test both the classic data modeling fundamentals and modern tooling fluency.

## Dimensional Modeling: The Foundation

Ralph Kimball's dimensional modeling methodology remains the standard for analytical data warehouse design. Understanding it deeply is a prerequisite for senior data warehouse roles.

**Fact tables**: Contain measurements (metrics) of a business process. Each row represents an event or snapshot. Columns are numeric metrics (revenue, quantity, duration) and foreign keys to dimension tables.

**Dimension tables**: Contain descriptive attributes of the entities involved in the business process. Date dimensions, customer dimensions, product dimensions. Typically have surrogate keys (not natural keys).

**Star schema**: One fact table at the center, multiple dimension tables radiating outward. Optimized for query performance — queries join fact to 1-3 dimensions without complex multi-hop joins.

**Snowflake schema**: Dimensions are normalized into sub-dimensions. More normalized but more complex to query. Generally avoid in modern analytical warehouses — storage is cheap, query performance matters more than normalization.

**Example — e-commerce orders**:
- Fact: `orders_fact` (order_id, customer_key, product_key, date_key, quantity, revenue, cost)
- Dimensions: `customer_dim` (customer_key, name, email, city, country), `product_dim` (product_key, name, category, brand), `date_dim` (date_key, date, year, quarter, month, day_of_week, is_holiday)

**Interview question**: "Why use a surrogate key instead of the natural key in dimension tables?"

Surrogate keys (generated integers) are stable — they don't change when the source system changes the natural key. They enable Slowly Changing Dimension handling. They're more efficient for joins than string natural keys. The source system key is preserved as `natural_key` in the dimension for traceability.

## Slowly Changing Dimensions (SCD)

SCD is one of the most commonly tested concepts in data warehouse interviews.

**SCD Type 1 (Overwrite)**: Simply update the dimension record. No history preserved. Use when history doesn't matter (fix a data entry error) or is not needed for analysis.

**SCD Type 2 (Add row)**: Add a new row with the changed values; mark the old row as expired. Use effective_date, expiry_date, and is_current flag. Preserves full history. Most common for slowly changing attributes like customer address, employee department.

```sql
-- SCD Type 2 example
SELECT customer_key, name, city, effective_date, expiry_date, is_current
FROM customer_dim
WHERE customer_id = 'C001'
ORDER BY effective_date;
-- Shows history of city changes with date ranges
```

**SCD Type 3 (Add column)**: Add a "previous_value" column. Only preserves one level of history. Use when you only care about the previous vs. current value.

**SCD Type 6 (Hybrid 1+2+3)**: Combines approaches for complex requirements. Rarely used but shows up in senior interviews.

## Modern Data Stack

The modern data stack is the standard architecture for data teams building analytical infrastructure in 2024-2026:

**Ingestion**: Fivetran, Airbyte, or Stitch for managed source connectors. Move data from 100+ source systems (Salesforce, Stripe, PostgreSQL) into the raw layer of your warehouse with minimal custom code.

**Storage and compute**: Snowflake, BigQuery, or Databricks. Cloud-native, separated storage and compute, pay-per-query. Optimized for analytical workloads — columnar storage, MPP execution.

**Transformation (dbt)**: Define transformations as SQL SELECT statements. dbt handles dependency management, documentation, testing, and lineage. Each model is a SQL file that compiles to a CREATE TABLE/VIEW statement.

**Orchestration**: Airflow, Prefect, or Dagster for scheduling and dependency management across pipelines.

**Semantic layer**: dbt Semantic Layer, Looker (LookML), or Cube.js for defining business metrics once and serving them consistently to all consumers.

## dbt Best Practices

dbt (data build tool) is now nearly universal in modern data teams. Senior interviews test fluency with its patterns.

**Folder structure convention**:
```
models/
  staging/     # Clean raw source data, 1:1 with source tables
  marts/       # Business-facing dimensional models
    core/      # Core entities (customers, products)
    finance/   # Finance-specific analytics
  intermediate/ # Complex transformations shared between marts
```

**Testing**: dbt tests are assertions about your data.
- `not_null`: Column should have no null values
- `unique`: Column should have no duplicate values
- `accepted_values`: Column should only contain specific values
- `relationships`: Foreign key integrity

```yaml
# models/marts/core/schema.yml
models:
  - name: orders_fact
    columns:
      - name: order_id
        tests:
          - not_null
          - unique
      - name: customer_key
        tests:
          - not_null
          - relationships:
              to: ref('customer_dim')
              field: customer_key
```

**Materializations**: Table (computed and stored on every run), view (computed on every query — no storage cost but slower), incremental (only process new/updated records — efficient for large tables), ephemeral (CTE, no storage).

Use incremental for fact tables that grow continuously. Add a filter: `WHERE event_time > '{{ this.max_event_time }}'` (conceptually — use dbt's `is_incremental()` macro in practice).

**Sources**: Define upstream sources in `sources.yml`. Use `{{ source('database', 'table') }}` rather than raw SQL references. This enables lineage tracking and freshness tests.

## Data Quality and Monitoring

Data quality problems silently corrupt analytics. Senior engineers build quality checks into the pipeline:

- **Freshness checks**: Alert when source data hasn't updated in expected time windows
- **Volume checks**: Alert when row counts deviate more than X% from the rolling average
- **Statistical checks**: Alert when metric distributions shift significantly (using Great Expectations or dbt's custom test capabilities)
- **Referential integrity**: Test that foreign key relationships hold

**Handling late-arriving data**: Batch pipelines often miss events that arrive after the batch window closes. Use a lookback window (always reprocess the last 3 days) or event time-based processing with watermarks.

Data warehouse engineering at senior level is about reliable, maintainable data products — not just working SQL. The combination of dimensional modeling fundamentals, modern tooling fluency, and data quality rigor is what separates the candidates who get offers.
