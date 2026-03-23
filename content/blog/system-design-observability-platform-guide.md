---
title: "System Design: Building an Observability Platform at Scale"
description: "A technical guide to designing an observability platform covering metrics pipelines, logging at scale, distributed tracing, OpenTelemetry, storage trade-offs, and system design interview approaches."
date: "2026-03-20"
category: "System Design"
---

# System Design: Building an Observability Platform at Scale

Observability platform design is an increasingly common system design interview question at companies that operate large distributed systems. It tests your understanding of high-volume data pipelines, storage trade-offs, and the operational concerns that become critical at scale. More importantly, it tests whether you think in terms of the three pillars of observability—metrics, logs, and traces—as complementary systems rather than isolated tools.

## The Three Pillars and Their Design Requirements

Metrics, logs, and traces have fundamentally different data shapes and access patterns. Designing a unified observability platform requires understanding these differences before making architecture decisions.

**Metrics** are numeric measurements sampled at regular intervals: CPU utilization at 15.3%, request rate at 1,240 requests/second, cache hit rate at 87.2%. They're aggregatable, they're cheap to store in compressed form, and they're the right tool for alerting and dashboards. Access patterns are predominantly recent data with range queries (give me CPU utilization for this service over the last 4 hours, broken down by host).

**Logs** are discrete events: a request completed, an error occurred, a configuration was loaded. They contain arbitrary structured or unstructured text. They're expensive to store relative to metrics and have high variance in volume—a single error condition can trigger log avalanche from thousands of instances. Access patterns are typically full-text search, filtering by service/level/time range, and tail-reading recent logs.

**Traces** are directed graphs of causally related events across service boundaries. A single user request might create a trace spanning 15 microservices with 40 spans. Traces are how you answer "which service is responsible for this 2-second tail latency?" Access patterns are lookup by trace ID, search by service/operation/duration, and analysis of span distributions.

## OpenTelemetry as the Collection Layer

The collection layer is the first design decision. Building proprietary agents is a strategic mistake—the market has converged on OpenTelemetry (OTel) as the vendor-neutral standard for instrumentation and collection.

OpenTelemetry provides:
- **SDK libraries** for all major languages that applications use to emit telemetry
- **OpenTelemetry Collector** (otelcol) — a deployable agent/gateway that receives, processes, and exports telemetry

The collector is the pivotal component in your architecture. It runs as a sidecar alongside services (agent mode) or as a standalone gateway deployment, and it handles:

- Protocol translation (receiving Jaeger, Zipkin, Prometheus, OTLP formats)
- Batching and compression before sending to backend storage
- Sampling decisions for traces
- Attribute filtering to strip PII before data leaves the service boundary
- Fan-out to multiple backends (send traces to both your primary store and an archive)

In your system design interview, proposing OTel Collector as the collection tier demonstrates you understand that the collection problem is solved and the architecture decisions are about storage, querying, and reliability—not reinventing agents.

## Metrics Pipeline: The TSDB Trade-off

For metrics storage, you need a time-series database (TSDB). The canonical TSDB choices for large-scale deployments are:

**Prometheus + Thanos/Cortex/Mimir** — Prometheus handles local collection and short-term storage. Thanos (or its Grafana-built successor Mimir) adds horizontal scalability, long-term storage via object storage (S3/GCS), and global query federation across multiple Prometheus instances. This stack is extremely common in Kubernetes environments and well-understood.

**InfluxDB / TimescaleDB** — InfluxDB is purpose-built for time series with good write throughput. TimescaleDB extends PostgreSQL with time-series optimizations, which matters if your team already has Postgres expertise.

**Clickhouse for metrics analytics** — Clickhouse is a columnar OLAP database that handles time-series workloads extremely well, particularly when you need flexible aggregation across high-cardinality dimensions (by region, by user tier, by service version simultaneously). Its compression ratios on time-series data are excellent.

The Prometheus-to-object-storage pattern is the most common at scale: store recent data (15-30 days) in Thanos/Mimir with fast SSD-backed storage, and compact and downsample older data to object storage with slower retrieval paths. This matches the access pattern: recent metrics are queried constantly, historical metrics are queried infrequently.

## Logging at Scale: The Storage and Ingestion Problem

Logs are the most expensive observability pillar. A system processing 1 million requests/second with an average of 5 log lines per request generates 5 million log lines per second. At 200 bytes per line average, that's 1 GB/second of raw log data—86 TB/day before compression.

The storage tier for logs uses a different architecture from metrics: you need full-text indexing for search, but full indexing of all log data is prohibitively expensive. The effective approach is:

**Hot tier (0-7 days):** Full-text indexed in a system like Elasticsearch, OpenSearch, or Clickhouse. Fast queries, expensive storage. This covers the operational window where engineers actively investigate incidents.

**Warm tier (7-30 days):** Structured JSON stored in object storage (S3, GCS) with a query engine like Athena, BigQuery, or ClickHouse's external table support. Slower queries (seconds to tens of seconds), but vastly cheaper storage.

**Cold tier (30+ days):** Raw compressed logs in object storage, retrieved only for compliance or post-mortem investigations.

The ingestion pipeline—OTel Collector → Kafka → consumers that write to the appropriate tiers—provides backpressure handling and replay capability. Kafka is important here: without a buffer between collection and storage, a storage backend slowdown causes backpressure that can affect application performance.

## Distributed Tracing: Sampling Strategy

Storing 100% of traces is impractical at scale—the volume is similar to logs, but traces have complex structure that makes compression less effective. The sampling strategy is the critical design decision.

**Head-based sampling** (deciding at the trace root whether to sample) is simple but forces the decision before you know if the trace is interesting. A 10% head-based sampler will miss 90% of the slow requests you care most about.

**Tail-based sampling** (buffering spans, making the decision when the full trace is assembled) is more powerful: sample 100% of error traces, 100% of traces exceeding the 99th percentile latency, and 1% of successful fast traces. The OTel Collector supports tail-based sampling with configurable policies.

For the interview, designing a tail-based sampler that retains error traces and high-latency traces while downsampling normal traces demonstrates strong systems thinking about operational trade-offs.

## The Interview Q&A

**Q: How would you handle cardinality explosion in your metrics system?**

High cardinality happens when a metric has dimensions with unbounded values—user IDs, URLs, or trace IDs as metric labels. A single metric with a user ID label for a service with 10 million users creates 10 million distinct time series. Most TSDBs handle this poorly. The solution is enforcing cardinality limits at the collection layer (OTel Collector can drop or hash high-cardinality labels), using label aggregation (replace user ID with user tier), and monitoring the cardinality of each metric family.

**Q: How do you correlate a log entry with its trace?**

By propagating the trace ID as a structured field in all log entries. When a request enters your system, a trace ID is generated (or propagated from an upstream service via OTel's context propagation headers). Any log statement made within that request context includes the trace ID. Query your log store by trace ID to see all logs associated with a specific trace. This correlation is why structured logging matters—free-text logs can't be reliably joined to traces.

**Q: How would you design alerting on top of this platform?**

Alerting evaluates metric queries on a scheduled interval and triggers notifications when conditions are met. The alerting system needs to de-duplicate and route alerts, handle alert fatigue, and support multi-condition alerts. Prometheus Alertmanager is the reference implementation. Critical design considerations: alert on symptoms (high error rate, high latency) not causes (CPU utilization), use multi-window burn rate alerts for SLO-based alerting, and build an on-call routing system that escalates based on alert severity.

An observability platform is ultimately a bet on operational leverage: the investment in instrumentation and infrastructure pays off during incidents. The candidates who answer this question well are the ones who've felt the pain of debugging production issues without it.
