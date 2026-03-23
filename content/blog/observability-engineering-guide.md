---
title: "Observability Engineering Guide: Metrics, Logs, Traces, and SLOs"
description: "Build and improve observability for engineering interviews — the three pillars, OpenTelemetry, SLIs/SLOs/error budgets, alerting strategy, and production debugging techniques."
date: "2026-03-20"
category: "DevOps & SRE"
---

# Observability Engineering Guide: Metrics, Logs, Traces, and SLOs

Observability questions appear in SRE, platform engineering, and senior backend interviews. The distinction from monitoring: monitoring tells you something is wrong; observability lets you understand *why* it's wrong. This guide covers the concepts and practices that make systems observable in production.

## The Three Pillars

**Metrics:** Numeric measurements over time. Low cardinality (a few dimensions). Efficient for dashboards and alerts. Best for: request rates, error rates, latency percentiles, resource utilization. Tool stack: Prometheus (collection), Grafana (visualization), Alertmanager (alerting).

**Logs:** Timestamped records of discrete events. High cardinality (can contain any value). Best for: detailed debugging, audit trails, capturing context around errors. Tool stack: structured JSON logs → Fluentd/Fluent Bit → Elasticsearch/Loki → Kibana/Grafana.

**Traces:** Records of a request's path through a distributed system. Each span represents work in one service. Correlated by trace ID. Best for: diagnosing latency issues across services, understanding request flow in microservices. Tool stack: OpenTelemetry instrumentation → Jaeger/Tempo → Grafana.

The three pillars are complementary: an alert fires on a metric, logs provide context around the failure time, traces show exactly where latency spiked.

## OpenTelemetry

OpenTelemetry (OTel) is the open standard for instrumentation — collect metrics, logs, and traces with a single SDK that exports to any backend. This prevents vendor lock-in and standardizes instrumentation across languages.

**Auto-instrumentation:** For common frameworks (Flask, Django, Express, Spring), OTel agents automatically instrument HTTP requests, database queries, and outbound calls without code changes.

**Manual instrumentation:** Add spans for custom business operations:
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def process_order(order_id):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        # ... processing
```

**Correlation:** Propagate trace context across service boundaries via HTTP headers (W3C TraceContext standard: `traceparent` header). This enables end-to-end traces across microservices.

## SLIs, SLOs, and Error Budgets

**SLI (Service Level Indicator):** A specific metric that measures service health from the user's perspective. Good SLIs: request success rate, latency (P99), data freshness. Bad SLIs: CPU usage (implementation detail, not user-visible).

**SLO (Service Level Objective):** A target for an SLI over a time window. "99.9% of requests succeed over 30 days." "P99 latency < 200ms over 30 days." SLOs define what "good enough" means.

**Error budget:** The allowed amount of "bad" before the SLO is violated. 99.9% SLO over 30 days = 43.8 minutes of downtime allowed. The error budget frames reliability conversations: if the error budget is nearly depleted, stop new feature work and focus on reliability.

**Common interview question:** "How would you set SLOs for a new service?" Answer: start with user expectations (what latency or reliability do users need?), look at historical data if available, set initially conservative targets and adjust based on operational experience. Involve product stakeholders — an SLO is a business decision, not just a technical one.

## Alerting Strategy

Good alerts are: actionable (a human can do something about it), important (it affects users), accurate (low false positive rate — alert fatigue leads to ignored pages), and durable (they fire for real problems, not transient blips).

**Alert on SLI signals, not symptoms:**
- ❌ Alert when CPU > 80% (symptom — might not affect users)
- ✅ Alert when error rate > 1% for 5 minutes (SLI — user-visible)

**Multi-window alerting (Alertmanager / Google SRE):** Alert when the error rate over a short window (5m) is high AND the error rate over a longer window (1h) is also elevated. Short window catches fast-burning incidents; long window catches slow burns. Avoids both false positives (transient spikes) and false negatives (gradual degradation).

**Runbooks:** Every alert should link to a runbook — documented investigation steps. The responder shouldn't have to remember what to do at 3 AM.

## Production Debugging Patterns

When an incident fires, the investigation follows a structured flow:

1. **Establish blast radius:** How many users are affected? Which services? Check error rates and latency across all dependencies.

2. **Look for changes:** Recent deployments, config changes, dependency changes. "What changed?" is often the fastest path to root cause.

3. **Correlate across pillars:** Check metrics for the anomaly, check logs around the failure time for error messages, check traces for slow or failing operations.

4. **Hypothesis-driven investigation:** Form a hypothesis, look for evidence that confirms or refutes it, don't chase random dashboards.

5. **Document the timeline:** As you investigate, keep a running log of what you're seeing and your current hypothesis. This helps the post-mortem and prevents revisiting the same evidence.

**Structured logging:** Every log entry should include: timestamp, service name, trace ID (for correlation with traces), request ID, log level, message, and relevant context fields (user ID, order ID, etc.) as structured fields. This enables filtering and aggregation that unstructured log lines can't support.

**Exemplars:** Prometheus metrics can include exemplars — sample trace IDs for requests that contributed to a metric data point. Click a high-latency spike on a Grafana dashboard → jump directly to a trace from that moment. This bridges metrics and traces.

Observability is a competitive advantage. Services with good observability ship faster (faster debugging), have fewer incidents (better alerting), and recover faster when incidents occur (faster diagnosis). Making the case for observability investment is itself a signal of engineering maturity.
