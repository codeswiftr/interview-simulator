---
title: "Observability Engineer Interview Guide"
description: "Technical interview preparation for observability and monitoring engineering roles: the three pillars (metrics, traces, logs), OpenTelemetry, distributed tracing, alerting design, and what companies like Datadog, Grafana Labs, Honeycomb, and large engineering organizations expect."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

# Observability Engineer Interview Guide

Observability engineering is the discipline of making distributed systems understandable from the outside — instrumenting them so that engineers can ask arbitrary questions about system behavior and get answers. The term is borrowed from control theory: a system is observable if you can infer its internal state from its outputs. As microservices architectures proliferated and monolithic logs became insufficient for debugging distributed systems, observability emerged as a distinct engineering specialty. Companies building observability products (Datadog, Grafana Labs, Honeycomb, New Relic) and large engineering organizations with dedicated platform teams hire specialized observability engineers.

## The Three Pillars — And Their Limitations

The "three pillars of observability" (metrics, logs, traces) is the standard framing, though practitioners sometimes argue it's incomplete:

**Metrics**: Numerical measurements over time. Counters (requests served, errors), gauges (current queue depth, memory used), histograms (request duration distribution). Metrics are cheap to store and query at scale because they're aggregated — you don't store every individual event, just counts and distributions. The limitation: metrics tell you something is wrong but not why. High error rate metric → something is failing, but which requests, for which users, on which code paths?

**Logs**: Structured or unstructured event records. Good logs enable debugging specific events: "what happened during this request at 14:32:07?" Structured logs (JSON with consistent field names) are queryable; unstructured text logs require regex parsing. The limitation: log volume is enormous in high-traffic systems; full-text search doesn't scale cheaply; correlation across services requires a common request ID.

**Traces**: Records of causally-related operations across services. A trace follows a request as it propagates through a microservice call graph. Each operation is a span (with start time, duration, service name, operation name, status). The trace graph shows where time was spent and where errors occurred. Distributed tracing solves the "which service caused this latency?" question that metrics and logs can't answer efficiently.

**The fourth pillar debate**: Honeycomb's Charity Majors argues for "events" as the primitive — high-cardinality structured events with arbitrary dimensions, from which metrics and traces are derived. This view underlies tools like Honeycomb and influences OpenTelemetry's design philosophy.

## OpenTelemetry

OpenTelemetry (OTel) is the CNCF standard for telemetry instrumentation — replacing proprietary agent formats with a vendor-neutral approach:

**What it standardizes**: APIs and SDKs for generating metrics, traces, and logs. The OTLP (OpenTelemetry Protocol) wire format for sending telemetry to any compatible backend. Semantic conventions (standardized attribute names — `http.method`, `db.system`, `service.name` — so data from different sources is consistently labeled).

**The OTel collector**: A standalone process that receives telemetry (OTLP, Prometheus, Zipkin, Jaeger, FluentBit), processes it (batching, filtering, transforming, enriching), and exports it to one or more backends. The collector enables switching backends without re-instrumenting applications — critical for large organizations.

**Auto-instrumentation vs. manual**: Auto-instrumentation agents (for Java, Python, Node.js) inject instrumentation without code changes — capturing HTTP requests, database queries, and framework calls automatically. Manual instrumentation adds custom spans and attributes for application-specific logic. Both are needed: auto-instrumentation for coverage, manual for semantic richness.

## Metrics Systems Architecture

**Prometheus pull model**: Prometheus scrapes metrics endpoints (`/metrics`) from services at configurable intervals. Service discovery (Kubernetes service discovery, file-based, DNS) finds targets. The pull model means Prometheus controls the scrape schedule, simplifying push coordination. Drawback: requires services to expose metrics endpoints; doesn't work for short-lived jobs (use Pushgateway).

**Remote write and long-term storage**: Prometheus' local storage isn't designed for years of data. Remote write (to Thanos, Cortex, VictoriaMetrics, Mimir) enables scalable long-term storage and multi-tenant separation.

**PromQL**: Prometheus Query Language. Instant vectors vs. range vectors, aggregation operators (`sum by`, `avg by`, `topk`), rate calculations (`rate(counter[5m])` for per-second rate), histogram quantile (`histogram_quantile(0.99, ...)`). Fluency with PromQL is expected for observability roles.

## Distributed Tracing Implementation

**Trace context propagation**: For tracing to work across services, trace context (trace ID, span ID, sampling decision) must propagate in HTTP headers (`traceparent` in W3C Trace Context spec, `X-B3-TraceId`/`X-B3-SpanId` in Zipkin B3). At service boundaries, the receiving service extracts context and creates a child span.

**Sampling strategies**: Full sampling (every request traced) is prohibitively expensive at high traffic. Head-based sampling (decide at trace start — simple but discards tails of interesting traces). Tail-based sampling (buffer traces, sample based on characteristics like error or high latency — captures interesting traces but requires buffering at the collector). Adaptive/dynamic sampling.

**Exemplars**: A bridge between metrics and traces. A histogram metric (request duration) can include exemplars — specific trace IDs of requests that contributed to the metric. Clicking on a high-latency percentile on a graph can jump directly to a trace representing that latency. Grafana + Prometheus + Tempo implements this flow.

## Alerting Design

Well-designed alerting is harder than it appears, and poor alerting (too noisy, too slow to fire, unclear response) is a common problem. Interviews probe alerting philosophy:

**Symptom-based vs. cause-based alerting**: Alert on what users experience (high error rate, high latency), not on infrastructure metrics (CPU usage, disk space) that may or may not affect users. Alert on the symptom; investigate the cause.

**Alert fatigue**: Noisy alerts that fire frequently train engineers to ignore them. Principles: every alert should be actionable; every alert should require a response; alerts should fire rarely. Alert accuracy over alert coverage.

**SLO-based alerting**: Alert based on SLO burn rate — how quickly are you consuming your error budget? Multi-window alerting (fast burn in the short window AND over the long window) reduces false positives while ensuring timely notification. Google's SRE book formalizes this approach.

## Who Hires Observability Engineers

**Observability vendors**: Datadog (large engineering organization across agent, backend, frontend, integrations), Grafana Labs (open-source-first, remote-first), Honeycomb (Charity Majors' company, high-cardinality event philosophy), New Relic, Dynatrace, Elastic (ELK stack).

**Large engineering organizations**: Uber, Netflix, LinkedIn, Slack — all have internal observability platform teams with significant headcount. These teams build instrumentation libraries, internal tracing backends, and developer tooling.

**Consulting and implementation**: Companies that help enterprises implement observability programs — Chronosphere (Prometheus-based), Sumo Logic.

Observability engineering rewards engineers who understand distributed systems deeply and have the patience to build infrastructure that their colleagues trust implicitly. The work is less visible than product engineering but disproportionately valuable when production incidents occur.
