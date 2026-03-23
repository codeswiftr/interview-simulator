---
title: "Observability Engineering Interview Guide"
description: "Metrics, logs, and traces in technical interviews: OpenTelemetry, distributed tracing, SLOs/SLIs, cardinality problems, and how observability thinking signals senior engineering maturity."
date: "2026-03-19"
category: "Technical Skills"
---

# Observability Engineering Interview Guide

Observability has evolved from a DevOps operational concern to a first-class engineering discipline. Senior engineers at companies with serious production systems are expected to think about how systems are observable from the design phase, not as an afterthought. This guide covers how observability topics appear in technical interviews and what interviewers are actually evaluating.

## The Three Pillars: What Interviewers Test

The "three pillars" framework (metrics, logs, traces) appears in interviews as a starting point, but interviewers at companies with mature observability cultures push beyond it. The question isn't just "do you know what these are?" but "do you understand when to use each, where they overlap, and what their limitations are?"

### Metrics

Metrics are aggregated numeric measurements over time. They answer "what is happening to the system right now and over time." Key interview concepts:

**Counter, gauge, histogram**: The three metric types. Counters increase monotonically (requests handled, errors). Gauges measure current state (memory usage, active connections). Histograms bucket observations for percentile calculation — essential for latency because averages mislead.

**Why averages are wrong for latency**: A p50 of 50ms with a p99 of 5000ms looks fine as an average (~100ms) but represents severe tail latency. Interviewers ask: "Your p50 API latency is 30ms. How do you know if there's a problem?" The answer requires histograms and percentiles, not averages.

**Cardinality problems**: High-cardinality labels (user ID, request ID, IP address) in metrics explode storage and query cost. A metric with 1 million unique values × 1000 metric series = 1 billion time series. Prometheus and Datadog both become unusable at high cardinality. Interviewers ask how to handle this — the answer involves choosing low-cardinality dimensions and using traces for high-cardinality event data.

### Logs

Logs are discrete events with structured context. They answer "what happened during a specific request or at a specific time."

**Structured logging**: Logs as JSON objects (or key=value) rather than free text strings. Enables query, aggregation, and correlation. `log.info("Request failed", {"user_id": "123", "error_code": "TIMEOUT", "duration_ms": 5000})` is useful; `log.info("Request from user 123 failed with TIMEOUT after 5000ms")` is not queryable.

**Log levels and sampling**: Debug logs at full rate in production are expensive. Production systems need sampling strategies: error logs at 100%, info logs at 10%, debug logs at 1% unless a debug flag is set. This shows operational maturity.

**Correlation IDs**: A trace ID or request ID passed through every log line in a request's lifecycle allows reconstructing what happened across service boundaries. "Did the logs have correlation IDs?" is a common post-incident question at companies that didn't implement this.

### Distributed Tracing

Traces answer "what path did this specific request take through the system and where did time go?"

**Trace, span, context propagation**: A trace is a single request's journey. It consists of spans — individual units of work with start time, duration, and metadata. Context propagation passes the trace ID through service calls via HTTP headers (`traceparent` in W3C Trace Context format) or message queue metadata.

**OpenTelemetry**: The emerging standard for instrumentation. Language-specific SDKs emit traces, metrics, and logs in a vendor-neutral format, which backends (Jaeger, Zipkin, Honeycomb, Datadog) ingest. Interviewers at companies migrating from vendor-specific agents ask why they'd switch to OTel.

**Sampling strategy**: Full-rate tracing is expensive for high-traffic systems. Head-based sampling (decide at trace start, random 10%) is simple but loses long-tail traces. Tail-based sampling (collect all spans, decide after the trace is complete, keep errors and slow traces) is expensive to implement but captures exactly what you care about.

## SLOs, SLIs, and Error Budgets

This is the senior interview territory. SRE/platform roles and senior backend roles at reliability-focused companies (Stripe, PagerDuty, Datadog) expect fluency here.

**SLI (Service Level Indicator)**: A specific metric that measures service health. "99th percentile request latency" or "error rate" are SLIs. The choice of SLI matters — it needs to measure what users actually experience.

**SLO (Service Level Objective)**: A target for an SLI. "p99 latency < 200ms for 99.9% of the last 28 days." SLOs are internal targets — not customer promises, but engineering targets that, if met, make the customer promise viable.

**Error budget**: The acceptable amount of unreliability derived from the SLO. If your SLO is 99.9% availability over 28 days, you have about 40 minutes of allowed downtime. This budget governs release velocity — when the error budget is consumed, you stop shipping features and focus on reliability.

Interview question: "How do you decide when to prioritize reliability work vs. feature work?" The SLO/error budget framework is the expected answer at companies that have adopted it.

## Designing Observable Systems

The most senior observability interview question: "Walk me through how you'd design this service to be observable."

A strong answer naturally incorporates:
- Metrics at the application layer (request rate, error rate, latency histograms) not just infrastructure (CPU, memory)
- Structured logs with correlation IDs and relevant business context
- Traces for any cross-service calls or workflows
- Health check endpoints that test actual dependencies (not just "the process is running")
- SLI/SLO definition for the service before launch
- Runbook links in alert notifications

Engineers who think about observability during design ship systems that are dramatically easier to debug in production. Interviewers who run production systems know this and hire for it.

## What to Study

- **The SRE Book** (Google): Chapter on Service Level Objectives is the canonical reference
- **OpenTelemetry documentation**: Hands-on instrumentation of a service with OTel is the best preparation
- **Honeycomb blog**: Charity Majors and team have written extensively on observability — observability-driven development, wide events, why the three pillars framing is limiting
- **Prometheus documentation**: Understanding metric types, labels, and the cardinality problem
- **Datadog / Grafana**: Using one of these tools in a real production context — even a small side project — is more valuable than reading about them
