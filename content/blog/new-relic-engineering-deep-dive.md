# New Relic Engineering Deep Dive: Building the Observability Platform at Petabyte Scale

Every minute, New Relic's platform ingests roughly 25 billion data points — metrics, traces, logs, and events — from millions of instrumented applications running across every major cloud and on-premise environment on earth. The engineering challenge is not just scale. It is heterogeneity: data arriving in dozens of formats, from agents embedded in PHP applications running on bare metal to OpenTelemetry collectors deployed in Kubernetes sidecars on AWS GovCloud. New Relic's engineering culture is built around a single hard constraint — every customer must be able to query any of their telemetry data, in any combination, in under a second. Understanding how they achieve this tells you nearly everything you need to know to succeed in their engineering interviews.

---

## NRDB: A Purpose-Built Telemetry Database

The core of New Relic's platform is NRDB — the New Relic Database — a proprietary distributed data store purpose-built for telemetry workloads. NRDB is not a general-purpose database. It does not support updates or deletes. It does not offer transaction isolation. What it does offer is write throughput and query speed at a scale that off-the-shelf solutions could not provide when New Relic built the first version.

NRDB's storage layer sits on top of Apache Druid, a columnar, append-only OLAP engine designed for high-cardinality time-series data. Druid stores data in segments — immutable compressed columnar files organized by time range. Each segment is typically 300–700 MB and covers a configurable time window (often one hour of data). Druid's segment model enables two critical optimizations: segment pruning (skipping segments outside the queried time range entirely) and column projection (reading only the columns referenced in the query, not entire rows).

But Druid alone does not get you sub-second query latency at New Relic's scale. New Relic built a distributed query layer on top of Druid that handles query routing, fan-out, and result merging across hundreds of Druid historical nodes. When a query arrives, the query layer determines which segments hold the relevant data, dispatches parallel sub-queries to each Druid node holding those segments, and merges partial results — applying final aggregations, sorting, and LIMIT enforcement — before returning the result to the caller. The query coordinator is aware of segment locality and routes sub-queries to minimize cross-rack data movement.

The unified data model is NRDB's most important architectural decision. Metrics, events, logs, and traces all land in the same queryable surface under a shared schema. Every record has a timestamp, an entity GUID (a globally unique identifier for the thing being monitored), and a set of attributes. A database query that joins trace span data with infrastructure CPU metrics for the same entity — something that would require federated queries across three separate storage systems in a traditional observability stack — executes as a single NRDB query.

---

## NRQL: A Distributed Query Engine for Mixed Telemetry

NRQL (New Relic Query Language) is New Relic's SQL-like query language for NRDB. Surface-level, it looks like standard SQL:

```sql
SELECT average(duration), count(*)
FROM Transaction
WHERE appName = 'checkout-service'
FACET httpResponseCode
SINCE 1 hour ago
TIMESERIES 5 minutes
```

Under the surface, executing this query requires solving problems that traditional SQL databases were not designed for. The `TIMESERIES` clause generates a time-bucketed aggregation across potentially billions of rows. The `FACET` clause groups results by a dimension that may have thousands of cardinality values. The `SINCE 1 hour ago` clause resolves to a wall-clock time range and drives segment selection across a distributed Druid cluster.

New Relic's distributed query engine handles approximate query processing for high-cardinality workloads. When a `FACET` query would return millions of distinct groups, the engine uses sketch algorithms — specifically HyperLogLog for cardinality estimation and t-digest for percentile approximation — to reduce memory pressure and query latency. The tradeoff is configurable: queries over large time ranges default to approximate results, while queries over short windows (where cardinality is bounded) execute exactly. Engineers at New Relic are expected to understand where approximation is acceptable and where it is not, which is a recurring theme in their system design interviews.

NRQL also supports correlated subqueries and `JOIN`-like operations between event types using `RELATED TO` syntax, which the query layer resolves by pushing predicate evaluation into each Druid sub-query to minimize data movement before the merge step. The query parser compiles NRQL to an internal plan representation, applies rule-based and cost-based optimizations, and hands off to the distributed execution layer.

---

## Adaptive Sampling: The Distributed Tracing Problem

Distributed tracing is the hardest observability problem at scale. A single user request touching twenty microservices generates twenty or more trace spans. A system processing two million requests per second produces forty million spans per second. Storing every span is economically infeasible. Dropping spans at random destroys trace completeness — a trace missing its slowest or most error-prone span is useless for debugging.

**Head-based sampling** — the traditional approach — makes the keep-or-drop decision at trace initiation, before any spans are collected. A sampling rate of 1% means 99% of traces are silently discarded before they are ever seen. This is computationally cheap but operationally blind: the 1% of traces you keep are not the 1% most likely to contain errors or performance anomalies. They are a random sample, and rare failure modes that occur in 0.01% of requests will never appear in your trace store.

New Relic's answer is **Infinite Tracing** — a tail-based sampling architecture. With Infinite Tracing, every span is collected from every trace agent and sent to New Relic's trace observers (dedicated edge nodes deployed in Google Cloud regions globally). The trace observer buffers spans in memory for a configurable window — typically 60 seconds — until the full trace is complete. Only then does the sampling decision execute, with access to the full span set. The sampling logic is priority-based: traces containing errors, traces with anomalous duration (above a configurable percentile), and traces matching user-defined attribute filters are kept at 100%. Low-priority routine success traces are downsampled aggressively.

The engineering challenge in tail-based sampling is the head affinity problem. For sampling to work correctly, all spans belonging to the same trace must reach the same trace observer. New Relic solves this with consistent hashing on the trace ID: the agent SDK hashes the trace ID (propagated via W3C TraceContext headers) and routes all spans for that trace to the same observer node. If an observer node fails, consistent hash ring rebalancing ensures minimal disruption with bounded trace incompleteness.

---

## The Agent Ecosystem: Zero-Config Instrumentation at Scale

New Relic ships and maintains eight production language agents: Java, Go, Python, Ruby, Node.js, .NET, PHP, and Browser (JavaScript). Each agent auto-instruments the target application — intercepting HTTP client calls, database queries, message queue operations, and external service calls — without requiring application code changes. The engineering discipline required to maintain eight agents with consistent behavior across wildly different language runtimes is one of New Relic's most underappreciated technical achievements.

The Java agent uses bytecode instrumentation via a Java agent JAR loaded at JVM startup with the `-javaagent` flag. The agent uses ASM to rewrite class bytecode at load time, injecting tracing logic into constructors and method calls for hundreds of known libraries (Spring, Hibernate, Apache HttpClient, Kafka, and dozens more). The instrumentation is declarative — agent engineers write YAML-based instrumentation rules that map to ASM transformations — which means adding support for a new library version does not require writing bytecode manipulation code directly.

The Go agent takes a different approach because Go does not support runtime bytecode modification. Go instrumentation requires explicit API calls (`txn.StartSegment()`, `nrpq.InstrumentConnector()`, etc.), but the agent ships "integration packages" that wrap popular libraries — `nrgin` for the Gin web framework, `nrmongo` for MongoDB, `nrredis` for Redis — so instrumentation often reduces to a one-line import and a wrapper call at initialization. The Go agent team runs the same integration test suite against every Go minor version and all supported library versions in CI, catching breaking changes in library APIs before they reach customers.

Consistent behavior across agents is enforced by a shared specification: a canonical document that defines exactly how transaction naming, segment timing, error classification, and attribute truncation must work in every language. Deviations from the spec are tracked as bugs, not as language-specific features. This matters for customers running polyglot architectures — a request traced from a Node.js frontend through a Python service to a Java backend should produce a coherent distributed trace with consistent timing semantics, regardless of which language agent generated each span.

---

## Interview Implications: What New Relic Actually Tests

New Relic's engineering interviews are heavily weighted toward system design and distributed systems fundamentals, with less emphasis on algorithmic puzzles than companies like Google or Meta. The interviewers are practitioners who work on the problems described above daily, and they probe for depth rather than breadth.

**System design questions you should be prepared for:** "Design a distributed tracing system that handles 10 million spans per second" (expect deep follow-up on head vs. tail-based sampling tradeoffs, head affinity, observer capacity planning). "Design a metrics alerting platform" (expect questions about time-series storage layout, alert evaluation at scale, flap detection, notification deduplication). "Design a log aggregation pipeline" (expect discussion of ingestion buffering, schema-on-read vs. schema-on-write, full-text indexing tradeoffs).

**What they look for beyond technical depth:** New Relic's observability engineering culture prizes engineers who reason carefully about data fidelity tradeoffs. In a metrics system, is it acceptable to lose 0.1% of data points during a broker failover? In a tracing system, is a 5-second delay in trace availability acceptable if it enables better sampling? Engineers who can articulate the product and operational consequences of these tradeoffs — not just the technical ones — perform well in New Relic's debrief process.

Come prepared to discuss cardinality as a first-class engineering concern. High-cardinality dimensions (user IDs, request IDs, IP addresses) in metric labels are the single most common cause of NRDB query degradation and storage cost blowout in customer deployments. Engineers at New Relic spend significant time helping customers restructure their telemetry schemas to move high-cardinality attributes from metric dimensions (where they explode index size) to trace attributes or log fields (where they are stored as columns and queried with filters, not aggregated as group-by keys). Demonstrating awareness of this distinction in your system design answers signals direct relevance to the work the team does every day.
