---
title: "System Design: Analytics Platform — Building Mixpanel or Amplitude at Scale"
description: "A deep-dive system design walkthrough for building a product analytics platform at scale — covering event ingestion, time-series storage, query engines, and the architectural trade-offs that separate toy systems from production-grade analytics."
date: "2026-03-20"
category: "System Design"
---

# System Design: Analytics Platform — Building Mixpanel or Amplitude at Scale

Product analytics platforms like Mixpanel, Amplitude, and PostHog have to solve a specific and genuinely hard systems problem: ingest billions of events per day, store them durably, and answer arbitrary analytical queries in under a second. This is a system design question that tests your understanding of data modeling, distributed systems, and the fundamental trade-off between write throughput and query flexibility.

Let's design it properly.

## Clarifying the Requirements

Before diving into architecture, establish scope:

**Functional requirements:**
- Track user events (page views, clicks, custom events) with arbitrary properties
- Answer queries: "How many users did X in the last 30 days, broken down by Y?"
- Support funnel analysis: "What % of users who did A then did B within 7 days?"
- Retention cohorts: "Of users who signed up in week 1, how many came back in week 4?"
- Real-time dashboards (delay < 30 seconds acceptable)

**Non-functional requirements:**
- Ingest: 1M events/second at peak (a large customer like Spotify or Uber)
- Query latency: p95 < 1 second for dashboard queries
- Retention: 2 years of event history
- Availability: 99.9%+ for ingestion; queries can tolerate brief degradation

## The Core Challenge: Write-Heavy, Query-Flexible

The fundamental tension is this: events arrive in a stream (time-ordered by arrival), but queries are arbitrary (by user, by event type, by time range, by property values). No single storage layout serves both optimally.

## High-Level Architecture

```
Client SDKs → Load Balancer → Ingestion API → Message Queue (Kafka) → 
Stream Processor → OLAP Storage → Query Engine → API → Dashboard
                 ↓
          Cold Storage (S3) for archival
```

## Ingestion Layer

**Client SDKs** batch events locally (100 events or 5 seconds, whichever comes first) and POST to the ingestion API. Batching is critical — it transforms thousands of tiny HTTP calls into manageable payloads.

**Ingestion API** servers are stateless, horizontally scalable. Their job is minimal: validate the payload, attach a server-side timestamp (don't trust client timestamps for deduplication), and push to Kafka. Target: sub-5ms p99 response time.

**Kafka** is the backbone. Partition by `project_id` (ensures events for one customer stay ordered) or by `user_id` (ensures per-user event ordering for funnel analysis). Topic retention: 7 days (enough for reprocessing).

**Critical decision: server-side vs client-side timestamps.** Client timestamps drift, can be manipulated, and arrive out-of-order. Use server receipt time for ordering; store client timestamp as a property for display.

## Event Schema

Events should be schema-less at ingestion but typed in storage:

```json
{
  "event_id": "uuid-v4",           // deduplication key
  "project_id": "proj_abc",        // customer identifier
  "user_id": "user_123",           // for user-level analytics
  "anonymous_id": "anon_xyz",      // pre-login tracking
  "event_name": "checkout_completed",
  "timestamp": 1710000000000,      // client time (ms)
  "received_at": 1710000000150,    // server time
  "properties": {                  // arbitrary key-value
    "amount": 49.99,
    "currency": "USD",
    "plan": "pro"
  }
}
```

## Stream Processing

**Stream processors** (Flink or Spark Streaming) consume from Kafka and:
1. Deduplicate by `event_id` within a 1-hour window (bloom filter per partition)
2. Resolve identity: merge `anonymous_id` → `user_id` when user authenticates
3. Compute real-time aggregations: event counts per 5-minute buckets
4. Write to both OLAP storage and cold storage (S3) in parallel

**Identity resolution** is subtle. When user `anon_xyz` logs in as `user_123`, all prior anonymous events should be attributed to that user. This requires a lookup table and retroactive attribution, which is expensive. Mixpanel and Amplitude handle this differently — it's a legitimate design discussion point.

## Storage: The Key Decision

This is where the system design gets interesting.

**Option A: ClickHouse**
Column-oriented OLAP database. Compresses extremely well for event data (10:1 ratios). Supports vectorized query execution. Can answer most analytics queries in milliseconds. Widely used in this space (PostHog, Contentsquare use it). Trade-off: limited JOIN support; schema changes require planning.

**Option B: Apache Druid**
Time-series OLAP database purpose-built for analytics. Pre-aggregates data into segments during ingestion. Handles real-time and historical queries from the same interface. Trade-off: operationally complex; Zookeeper dependency is a pain point.

**Option C: BigQuery / Snowflake (cloud OLAP)**
Managed, scales infinitely, SQL-compatible. Trade-off: query costs are variable and can be high; latency is higher than self-hosted ClickHouse for sub-second queries.

**Recommended:** ClickHouse for the hot tier (last 90 days), BigQuery/Snowflake for cold tier (90 days to 2 years). Most queries hit the hot tier; historical analysis goes to cold.

## Query Engine

**Pre-aggregation:** For common queries (DAU, WAU, event counts by hour), pre-compute and store results in Redis. Cache hit rate for dashboard queries should be >80%.

**Query planner:** For ad-hoc queries, translate the analytics query (funnels, retention, segmentation) into SQL against ClickHouse. Funnel queries are set intersection problems; retention queries are cohort intersection problems. Both require careful SQL generation to avoid N+1 patterns.

**Query timeouts and sampling:** For queries touching >30 days of data, sample at 10% and extrapolate. Surface this to the user. Amplitude does this; it's the right trade-off for interactive dashboards.

## Funnel Analysis: The Hard Part

A funnel query ("of users who did A, what % did B within 7 days?") is deceptively complex:

1. Find all users who did event A in the time range
2. For each such user, check if they did event B within the 7-day window
3. Count and compute conversion rates

In ClickHouse this uses window functions over user-partitioned data. The data must be sorted by `(user_id, timestamp)` — this is why your ClickHouse table should have that as its sort key.

## Capacity Estimation

- 1M events/second × 500 bytes avg = 500 MB/s raw ingestion
- After compression in ClickHouse: ~50 MB/s on-disk write
- 90 days hot storage: 50 MB/s × 90 × 86400 ≈ 388 TB
- With ClickHouse compression (10:1): ~39 TB for hot tier

This is manageable on a 10-node ClickHouse cluster with 4TB SSDs each.

## Key Interview Talking Points

1. **Idempotency in ingestion:** How do you handle duplicate events from SDK retries? Event ID + time-window deduplication.
2. **Late-arriving data:** Events arrive out-of-order. Use received_at for partitioning; allow writes to recent partitions for 24 hours.
3. **Multi-tenancy:** How do you prevent one customer's heavy query from impacting others? Query quotas, separate ClickHouse clusters for Enterprise customers, or logical resource pools.
4. **Schema evolution:** New event properties are additive. Use schema-on-read (store JSON, index specific columns). Never block ingestion on schema changes.

This architecture handles the scale of Mixpanel or Amplitude, and the design decisions here — column store vs row store, pre-aggregation strategy, funnel query implementation — are exactly what interviewers at data-infrastructure-heavy companies want to discuss.
