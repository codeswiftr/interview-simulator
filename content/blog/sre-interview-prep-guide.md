# Site Reliability Engineering Interview Guide 2024: SRE-Specific Prep Beyond DevOps

Most engineers preparing for SRE roles study the same DevOps material they would for a platform engineering or infrastructure position. That is a mistake. SRE interviews test a specific body of knowledge rooted in Google's original SRE model, and interviewers at companies like Google, Spotify, Cloudflare, and LinkedIn can tell within the first ten minutes whether a candidate genuinely understands reliability engineering or is just an ops engineer who learned to write Python.

This guide covers what SRE interviews actually test, what distinguishes SRE candidates from DevOps generalists, and how to prepare for the specific technical domains that come up repeatedly.

## What SREs Actually Do vs. What DevOps Engineers Do

The distinction matters because interview questions are designed to surface it. DevOps engineers optimize for deployment velocity and infrastructure automation. SREs optimize for reliability at scale, and they do it by applying software engineering principles to operations problems.

The defining characteristic of SRE is the error budget. An SRE team defines service level objectives — the target reliability for a given service — and the difference between 100% and that target is the error budget. If your SLO is 99.9% availability, you have 43.8 minutes per month of allowed downtime. When the error budget is healthy, the team can move fast and accept more deployment risk. When the budget is exhausted, reliability work takes priority over feature development. This creates a mathematically grounded negotiation between SRE and product teams, which is fundamentally different from a DevOps team's relationship with engineering.

SLIs (Service Level Indicators) are the measurements. For a web service, common SLIs are request success rate, latency at the 99th percentile, and throughput. SLOs are the targets set on those measurements. SLAs are contractual commitments to customers, usually set more conservatively than internal SLOs. The difference between SLA and SLO is a buffer that gives you room to recover before you breach customer commitments.

Interviewers will ask you to define these for a hypothetical service. Practice defining SLIs for different service types: for a batch processing job, availability and latency are less relevant than freshness and correctness. For a payment API, a 200 response that processes the wrong amount is worse than an error. Knowing how to choose meaningful SLIs for a given system is a senior SRE skill.

Toil is another concept that separates SRE from DevOps. Google defines toil as manual, repetitive, automatable work that scales linearly with service growth and provides no enduring value. Handling on-call alerts manually, running the same deployment runbook every week, manually provisioning capacity — these are toil. SRE teams track their toil load, and the Google SRE model sets an upper bound of 50% operational work, with the remaining time dedicated to engineering. Interviewers ask about toil to understand whether you have thought about the economics of operations work and have experience reducing it through automation.

## The Google SRE Book in Interview Context

The Site Reliability Engineering book from Google is not optional reading for SRE candidates. Most interviewers have read it, and many interview questions are derived directly from its content. You do not need to memorize it, but you need to understand its core frameworks.

The chapters on SLOs, error budgets, and eliminating toil form the conceptual backbone. The chapters on on-call practices and postmortem culture will come up in behavioral interviews. The chapters on load balancing, managing load, and handling overload inform system design questions.

Pay particular attention to the concept of graceful degradation and the difference between a service being unavailable and a service being slow. An SRE frames these differently from a developer. A developer might fix a timeout bug. An SRE asks: what should the system do when downstream dependencies are slow? What is the right behavior under partial failure? These questions lead to design patterns like circuit breakers and load shedding.

The monitoring chapter's framework — white-box versus black-box monitoring — still comes up. White-box monitoring uses internal signals (memory usage, garbage collection pressure, queue depth). Black-box monitoring tests external behavior from the user's perspective. Neither is sufficient alone. An interviewer might ask you to design a monitoring system and expect you to distinguish between the two.

## Incident Management and On-Call Culture

Incident management questions appear in almost every SRE interview. They test your operational maturity and your understanding of how reliability teams function under pressure.

The incident command structure matters. Large-scale incidents require an incident commander who coordinates response, a communications lead who manages stakeholder updates, and technical responders who do the actual debugging. You should be able to describe this structure and explain why it exists: coordination overhead during incidents is a real problem, and having clear roles prevents the situation where ten engineers are all debugging the same thing while nobody is communicating status to customers.

Blameless postmortems are central to SRE culture. The principle is that people do not cause incidents — systems do. When something fails, the right question is not who made the mistake but what system properties allowed the mistake to have catastrophic consequences. A configuration error that takes down production is a symptom of missing safeguards: no automated validation, no staged rollout, no automated rollback. The postmortem documents the timeline, the contributing factors, the impact, and the action items. Interviewers want to hear that you have led postmortems and that your action items address systemic causes rather than blaming individuals.

A common interview question: walk me through how you would handle a P1 incident where payments are failing. The expected answer covers immediate triage (what signals tell you something is wrong and what initial diagnosis looks like), mitigation (how you reduce customer impact quickly, even before root cause is identified), communication (who you notify and at what cadence), and the postmortem process afterward. Candidates who focus only on the technical debugging often miss the communication and coordination expectations.

On-call rotation design is another common question. How would you design an on-call rotation for a team of eight engineers covering a globally distributed service? You need to cover time zones, define escalation paths, specify what warrants a page versus a ticket, and explain how you would manage alert fatigue. Alert fatigue is a real problem in SRE — if alerts are noisy, engineers learn to ignore them, which is more dangerous than having no alerts at all. Alert quality (signal-to-noise ratio) is something interviewers probe specifically.

## Capacity Planning and Load Testing

SREs own capacity planning, which requires understanding both the demand forecast and the system's performance characteristics under load.

Capacity planning starts with growth projections. You need historical usage data, knowledge of upcoming product launches, and an understanding of how usage patterns change seasonally or with marketing campaigns. You then model how the system scales with load: is it compute-bound, memory-bound, I/O-bound, or network-bound? Each constraint has different scaling strategies.

Load testing validates your capacity models. You cannot plan capacity for traffic patterns you have never tested. A realistic load test simulates actual traffic distributions, including the long tail of slow or complex requests that often dominate actual resource consumption. Interviewers may ask you to design a load testing strategy for a service — they want to see that you understand the difference between load testing (how does the system perform under expected load), stress testing (where does it break), and chaos engineering (how does it behave under partial failure).

The important concept here is that load tests should be run continuously, not just before major events. If you only run load tests before Black Friday, you find problems too late to fix them. Progressive load testing integrated into the deployment pipeline catches performance regressions before they reach production.

## Distributed Systems Reliability Patterns

SRE candidates are expected to understand the standard reliability patterns for distributed systems. These come up in system design interviews and in questions about how you would improve an existing system's reliability.

Circuit breakers prevent cascading failures. When a downstream service starts failing, a circuit breaker tracks the failure rate and, once it crosses a threshold, stops sending requests to that service for a period. This gives the downstream service time to recover without being bombarded with requests. Interviewers expect you to know the three states (closed, open, half-open) and when each applies.

Bulkheads isolate failures. The pattern comes from ship design: if one compartment floods, bulkheads prevent the whole ship from sinking. In software, you achieve bulkheads by separating thread pools, connection pools, or resource limits by service or tenant. If one customer's traffic spikes and exhausts a shared resource, it should not degrade service for other customers.

Retry with jitter and exponential backoff is the correct pattern for handling transient failures. Retrying immediately after failure often makes things worse — if a service is overloaded and you retry instantly, you add to the load. Exponential backoff spreads out retries over time. Adding jitter (randomness to the retry interval) prevents all clients from retrying in synchronized bursts, which is the thundering herd problem. This is a question that comes up often: why add jitter to retries? The answer must include thundering herd.

Load shedding is what you do when the system cannot handle all incoming traffic. Shedding low-priority requests preserves capacity for high-priority ones. This requires defining request priority, which is often a product decision as much as an engineering one. A payment confirmation request is higher priority than a recommendation refresh.

## Observability: The Three Pillars

Observability is a core SRE domain. Interviewers expect deep familiarity with metrics, logs, and distributed traces, and increasingly with OpenTelemetry as the standard instrumentation framework.

Metrics answer quantitative questions: how many requests per second, what is the 99th percentile latency, how many errors in the last five minutes. Prometheus is the dominant metrics system in the Kubernetes ecosystem. It uses a pull model (Prometheus scrapes metrics from services), a dimensional data model (labels for filtering and aggregation), and PromQL for querying. Interviewers may ask you to write PromQL queries to calculate error rates or alert on SLO violations. The recording rules pattern — pre-computing expensive queries — is worth knowing.

Logs answer diagnostic questions: what happened in this specific request, what error message appeared before this failure. At scale, logs require structured formatting (JSON), sampling strategies for high-cardinality events, and a log aggregation system (Elasticsearch, Loki, Splunk). Raw logs are rarely useful without structured indexing.

Distributed traces answer flow questions: how did this request travel through the system, where was time spent, where did it fail? Tracing requires instrumentation at every service boundary, a trace collection system (Jaeger, Tempo, Zipkin), and a sampling strategy. Sampling is important because tracing every request at high volume is expensive; you need to capture enough traces to be useful while controlling cost.

OpenTelemetry is the CNCF standard for instrumentation. It provides a single SDK for emitting metrics, logs, and traces, with pluggable exporters for different backends. Interviewers at companies using modern observability stacks will expect familiarity with OTel, even if they don't require deep implementation knowledge.

The practical question interviewers ask: how would you debug a latency regression in production? The expected answer uses all three pillars: start with metrics to identify when and where the latency increase appeared, use traces to identify which service or operation is slow, use logs to diagnose the root cause within that operation.

## Common SRE Interview Questions

These questions appear repeatedly. Each requires a structured answer that demonstrates SRE-specific knowledge.

Design an on-call rotation system for a global service. Cover escalation policies, time zone coverage, alert routing, on-call compensation, and metrics you would track to assess on-call health (mean time to acknowledge, mean time to resolve, alert volume, burnout signals).

Calculate the error budget for a service with a 99.95% monthly SLO. The math: 99.95% availability means 0.05% downtime allowed. In a 30-day month (43,200 minutes), that is 21.6 minutes. If the service has been down for 15 minutes this month, 6.6 minutes remain. Interviewers want to see that you can do this calculation and explain its implications for deployment decisions.

Design a health check system. A shallow health check (is the process alive?) is insufficient — a service can be alive but unable to process requests. A deep health check (can I connect to the database, is the cache responding, is the queue drained?) is more informative but can cause false positives if dependencies are flaky. The right design includes both, uses health checks to inform load balancer routing, and avoids using health checks as the primary alerting mechanism.

How would you reduce alert fatigue on a team with 50 alerts per day? This question tests whether you understand that alert quality is more important than alert quantity. The answer should cover: audit alerts to remove those that do not require human action, convert informational alerts to dashboards, aggregate related alerts, improve runbooks so alerts are actionable, and track alert-to-incident conversion rate as a quality metric.

## What Distinguishes SRE Candidates

SRE interviewers are specifically filtering for engineers who think about reliability as a product property, not a binary state. The question is not "is the service up" but "what reliability level is appropriate for this service, how do we measure it, and what trade-offs are we making."

Candidates from pure DevOps backgrounds often focus on tooling and automation without the reliability framework. They can tell you how to configure a CI/CD pipeline but struggle to define an SLO or explain why 100% availability is not the right goal (it removes the error budget, which removes the incentive to ship features, and it is never achievable anyway — you end up lying to yourselves about what the target means).

Candidates from pure software engineering backgrounds understand distributed systems but lack the operational context — they have not been on call, have not debugged production issues at 3 AM, and have not internalized the difference between what a system does under lab conditions and what it does under real load with real failure modes.

The strongest SRE candidates bridge both: they think in systems, they understand reliability mathematics, they have hands-on operational experience, and they write code to solve operational problems.

## Coding Expectations at SRE Interviews

SRE coding interviews are not LeetCode grinding sessions. Interviewers are not looking for optimal algorithmic complexity on contrived problems. They are looking for evidence that you can write reliable, maintainable scripts and tools.

Python and Go are the dominant languages. Python for scripting, automation, and data analysis. Go for production tooling and anything that runs in the critical path. You should be comfortable with both.

Common coding tasks: write a script to parse log files and compute p99 latency, implement a health check poller with retry logic, write a Prometheus exporter for a custom metric, implement a rate limiter, write a circuit breaker. These tasks test practical engineering skills rather than algorithmic knowledge.

The code quality bar is higher than candidates expect. SRE code runs in production. Interviewers will look at error handling (do you handle the case where the log file doesn't exist?), observability (does your tool emit metrics about its own operation?), and operational properties (does it handle signals gracefully, does it have a configurable timeout?).

## Preparation Strategy

Read the Google SRE Book chapters on SLOs, error budgets, toil, on-call practices, and postmortems. Read the Seeking SRE anthology for perspectives beyond Google. Practice calculating error budgets and defining SLIs for different service types.

For system design, practice designing systems with reliability as a first-class constraint. Every design should include: what are the failure modes, how does the system degrade gracefully, how would you monitor it, what are the SLIs.

For coding, implement a small observability tool in Python or Go — a log parser, a metric exporter, a health check poller. Write it to production quality: error handling, logging, tests.

For behavioral interviews, prepare three to five incident stories using the STAR format: what was the service, what went wrong, what did you do, what did you change afterward. Each story should include the postmortem process and the systemic improvements that resulted.

The SRE role is one of the highest-leverage positions in engineering. Candidates who demonstrate genuine understanding of reliability economics, operational practice, and software engineering discipline stand out immediately from the field.
