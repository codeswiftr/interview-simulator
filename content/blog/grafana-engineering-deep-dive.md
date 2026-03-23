# Grafana Labs Engineering Deep Dive: Architecture, Culture, and What They're Really Testing in Interviews

Grafana Labs has quietly become one of the most technically ambitious companies in infrastructure software. What started as a dashboarding layer over Prometheus has evolved into a complete observability stack — metrics, logs, and traces — all designed around a shared architectural insight: **treat every signal type like a time-series problem**. If you're interviewing at Grafana Labs, you're entering a shop where engineers debate storage compaction strategies, argue about label cardinality, and take backward compatibility as seriously as most companies take uptime. This post covers the technical depth you need to walk in prepared.

---

## The Plugin Architecture: 150+ Data Sources and Backward Compatibility at Scale

Grafana's core product is a visualization layer, which means the plugin system is load-bearing infrastructure, not a nice-to-have. The data source plugin API works through a gRPC-based backend plugin protocol (the `grafana-plugin-sdk-go`). Each data source plugin implements a `QueryData` handler that receives a `QueryDataRequest` — a batch of `DataQuery` objects with a time range and interval — and returns a `DataResponse` containing `Frames` (Apache Arrow-compatible tables).

The critical design decision is that frames carry their own schema. Each `Frame` has typed `Fields` with metadata, so the frontend never needs to know the underlying data source structure ahead of time. A plugin for Postgres and a plugin for CloudWatch both emit the same frame format, and the panel plugins (time series, bar chart, table) consume frames without caring about origin.

Backward compatibility across major versions is maintained through a plugin versioning contract enforced at the API surface level, not implementation level. The `pluginID` + `type` tuple is immutable once published. The team runs a plugin compatibility matrix in CI — any change to the SDK triggers a test sweep across all first-party plugins. Third-party plugins that break get flagged before releases go out. This is the same approach Google uses for proto3 evolution: add fields, never remove or repurpose them.

For panel plugins, the data flow is: raw frames from backend → field overrides and transformations in the frontend pipeline → panel renderer. Transformations (join, filter, group-by) are composable pure functions over frames, which makes them testable without a live data source.

---

## Loki: The "Logs Are Like Metrics" Insight

Elasticsearch indexes every word in every log line. At high ingest rates, that index overhead dominates your cost and your operational burden. Loki's founding insight was that **you don't need to search log content at write time — you need to search it at read time, and only when you already know roughly where to look**.

Loki indexes only labels (structured key-value pairs attached at ship time), not log content. Log lines are compressed and stored as chunks in object storage (S3, GCS, Azure Blob). The label index — implemented with a custom inverted index in BoltDB, now moved to a distributed index using Cassandra or BigTable for scale — maps label sets to chunk locations. When you query `{app="api", env="prod"}`, Loki resolves the label set to a list of chunks, fetches them in parallel, decompresses, and applies your filter regex or pipeline in-memory at query time.

The chunk model is the performance lever. Chunks are snappy-compressed streams of log lines, typically 256KB uncompressed. Because log data compresses extremely well (repetitive structure, common substrings), real-world compression ratios of 10:1 to 20:1 are common. Combined with S3-class storage prices, Loki regularly achieves 5-10x lower storage cost than Elasticsearch for equivalent retention.

The query language, LogQL, is deliberately Prometheus-compatible in its label selector syntax. Metric queries derive from log streams:

```logql
# Count HTTP 5xx errors per minute, by service
sum by (service) (
  rate(
    {cluster="prod", namespace="api"} |= "status=5" [1m]
  )
)

# Parse structured fields from log lines and filter
{app="payment-service"}
  | json
  | status_code >= 500
  | line_format "{{.method}} {{.path}} → {{.status_code}}"
```

The `| json` stage parses the log line as JSON and promotes fields to labels for filtering and aggregation — without indexing them. This is the key architectural difference from Elasticsearch: field extraction is a query-time operation, not an index-time one.

---

## Tempo: Trace Storage Without a Trace Index

Distributed tracing backends like Jaeger and Zipkin built general-purpose search indexes: you can query by service, operation, tags, duration, and error status. That flexibility is expensive. Elasticsearch-backed Jaeger at scale can cost as much as your production infrastructure.

Grafana Tempo makes an opinionated trade-off: **index only trace ID and service name. Find traces through metrics and logs, not through trace search**. The canonical workflow is: a Prometheus alert fires → you jump to the exemplar (a trace ID embedded in the metric) → Tempo fetches the full trace by ID in milliseconds. Or: a Loki query surfaces an error log with a `traceID` field → Tempo fetches the trace. This is the "correlate signals" model, not the "search traces directly" model.

Trace data is stored as Parquet files in object storage, partitioned by tenant and time window. The only index is a bloom filter per block for trace ID lookups, which is O(1) per block for ID-based retrieval. Full-text search over trace attributes is explicitly not supported in the base storage layer — if you need it, you use TraceQL with post-filtering, and you pay for the scan.

The result is trace storage at roughly 1/10th the cost of Elasticsearch-backed solutions. The operational model is also dramatically simpler: no Elasticsearch cluster to tune, no shard rebalancing, no hot/warm/cold tier management.

---

## Mimir: Horizontally Scalable Prometheus at Any Cardinality

Prometheus's single-node TSDB is exceptional for small-to-medium deployments, but it has hard limits: a single node, local disk only, no multi-tenancy. Cortex (now forked to Mimir, with Grafana Labs as primary maintainer) decomposed every Prometheus component into a horizontally scalable microservice.

The write path: `Distributor → Ingester → Object Storage`

- **Distributor**: Receives remote-write traffic. Uses consistent hashing (with virtual nodes for even distribution) to shard series across ingesters. Validates labels, enforces per-tenant limits.
- **Ingester**: Holds the recent in-memory TSDB for each shard. Flushes chunks to object storage (S3/GCS) on a configurable schedule (typically 2h blocks). Write-ahead log (WAL) provides durability across restarts.
- **Compactor**: Runs continuously, merging small blocks into larger ones (Prometheus's TSDB compaction model), deduplicating across replicated ingesters.
- **Ruler**: Evaluates recording rules and alerting rules at scale, sharded across ruler instances.
- **Querier + Query Frontend**: The query frontend splits PromQL range queries into sub-range shards and parallelizes them across queriers. A query over 30 days of data with a 1h step becomes 720 parallel fetches, each hitting the block cache (Memcached/Redis) before going to object storage.

The object storage model is the architectural unlock. Long-term retention is trivially cheap because S3-class storage is cents per GB-month. There's no custom time-series database to operate — just block files in a bucket. The Thanos project pioneered this pattern; Mimir extends it with multi-tenancy, rate limiting, and a production-grade query path.

---

## What Grafana Labs Looks for in Engineering Interviews

**Go expertise is non-negotiable.** The entire stack — Mimir, Loki, Tempo, the plugin SDK, the Grafana backend — is Go. They're not testing syntax; they're testing whether you understand goroutine scheduling, channel semantics, context propagation, and how to write Go that doesn't leak goroutines under load. Expect code reviews of concurrent code as part of the process.

**System design questions map directly to their stack.** Common prompts include:

- *Design a metrics storage system for 10M time series* — they want to see you independently arrive at ingestor/compactor/object storage decomposition, consistent hashing, and WAL-based durability.
- *Design a log aggregation system at 1TB/day* — they want to see the index-labels-not-content insight, chunk compression, and query-time filtering.
- *How would you handle a high-cardinality label that's killing your metrics backend?* — this is a real operational problem (a `user_id` label at millions of users) and they want to hear about cardinality limits, label normalization, and recording rules to pre-aggregate.

**Open source culture shapes the interview dynamic.** Grafana Labs contributes most of their core infrastructure publicly. Engineers are expected to engage with RFCs, write design docs that hold up to external scrutiny, and make decisions that won't trap future contributors. During behavioral rounds, they probe for evidence that you've navigated open source trade-offs: maintaining backward compatibility for external users, managing breaking changes with deprecation cycles, and writing public-facing documentation as a first-class artifact.

**Observability domain depth matters.** If you can't explain the difference between a counter and a gauge, or why histogram quantile estimation has inherent error bounds, you'll struggle in technical discussions. Understanding the RED method (Rate, Errors, Duration) and USE method (Utilization, Saturation, Errors) as frameworks for instrumentation design signals that you think about observability at the system level, not just the library integration level.

The strongest candidates arrive having run Grafana, Loki, and Mimir in a personal lab environment — even a small k3s cluster is enough. Reading the architecture docs is table stakes. Having opinions about chunk sizing trade-offs or bloom filter false positive rates from operational experience is what separates candidates who get offers.
