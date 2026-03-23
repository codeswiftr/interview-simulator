---
title: "Microservices Architecture Interview Guide"
description: "Master microservices architecture interview questions: monolith vs microservices trade-offs, service communication patterns, circuit breakers, the saga pattern, and distributed observability — with real examples from Netflix, Uber, and Amazon."
date: "2026-03-19"
category: "System Design"
---

## What Interviewers Actually Want to Know

Microservices questions at senior-level interviews are not about whether you know the definition. They are about whether you understand the costs. Every interviewer who asks "monolith vs microservices" is really asking: "Have you felt the pain of both, and do you know when to choose which?"

If your answer starts with "microservices are better because they scale independently," you have already lost points. Scale is one dimension. Operational complexity, network latency, distributed transactions, and debugging across dozens of services are the other dimensions that get ignored until they cause production incidents.

## Monolith vs Microservices: The Trade-Off Question

The interview question is almost always framed as a design decision for a new system or a migration of an existing one. Your job is to name the specific costs on both sides.

**Monolith advantages that candidates undersell:**
- Single deployment unit. One binary, one CI pipeline, one rollback.
- In-process calls are orders of magnitude faster than network calls.
- Transactions are ACID by default — no saga choreography needed.
- Debugging is linear. One log stream, one stack trace.

**Microservices advantages:**
- Independent deployability. The payments team ships without waiting for the search team.
- Fault isolation. A recommendation service crash does not take down checkout.
- Technology heterogeneity. You can run your ML inference service in Python while everything else is Go.
- Independent scaling. You can scale your video transcoding service without scaling your user profile service.

**What actually happened at real companies:**

Amazon ran a monolith for years. By the early 2000s, it had become what Werner Vogels called a "spaghetti of dependencies" — a change to one module required rebuilding and redeploying the entire system. They decomposed into services team by team, eventually publishing the internal mandate that all teams expose functionality through service interfaces only.

Netflix started its streaming service as a monolith and hit scaling walls in 2008 when a database corruption event took down the entire service for three days. They spent the next seven years migrating to microservices on AWS, eventually running over 700 services. They also built most of the tooling that the industry now takes for granted: Hystrix for circuit breaking, Eureka for service discovery, Zuul for API gateway.

Stack Overflow went the other direction — they run one of the highest-traffic sites in the world on a near-monolith, with a handful of SQL Server instances and a carefully tuned caching layer. They are a counter-example worth knowing.

**The answer interviewers want to hear:** Start with a monolith if the domain is not yet well understood. Decompose along bounded contexts once team boundaries, scaling requirements, and deployment independence become real constraints, not hypothetical ones.

## Service Communication Patterns

This is where candidates get tripped up. There are two categories: synchronous and asynchronous. Each has specific use cases.

**Synchronous: REST and gRPC**

REST over HTTP is the default. It is human-readable, widely supported, and easy to debug with curl. The cost is verbosity and loose typing — a JSON field rename breaks clients silently.

gRPC uses HTTP/2 and Protocol Buffers. It is strongly typed, generates client/server stubs, supports streaming, and is typically 5-10x faster than REST for internal service calls. Uber, Netflix, and Google use gRPC extensively for internal service communication. The cost is tooling complexity and less debuggability — you cannot just curl a gRPC endpoint.

Choose synchronous when the caller needs a result before it can proceed. An API gateway authenticating a request must call the auth service synchronously.

**Asynchronous: Message Queues and Event Streaming**

Kafka, RabbitMQ, and AWS SQS are the common choices. Producers publish events without waiting for consumers. Consumers process at their own rate.

Benefits: decoupling, buffering during traffic spikes, natural audit log, fanout to multiple consumers.

Uber's dispatch system publishes a `trip_requested` event. Multiple services — driver matching, surge pricing, fraud detection — consume it independently. No synchronous chain of calls, no cascading failure if fraud detection is slow.

Choose asynchronous when the caller does not need an immediate result, when processing can be deferred, or when multiple services need to react to the same event.

**The question interviewers ask:** "How do you handle the case where Service A calls Service B synchronously and Service B is down?" This leads directly to circuit breakers.

## Service Discovery

When you have 50 services and each has multiple instances, how does Service A know where to find Service B?

Two patterns:

**Client-side discovery:** The client queries a service registry (Eureka, Consul) and picks an instance using a load-balancing algorithm. Netflix Ribbon does this. The client has more control but must implement discovery logic.

**Server-side discovery:** The client calls a load balancer (an AWS ALB, Nginx, or a service mesh like Envoy). The load balancer queries the registry. The client is dumb. Kubernetes uses this model — you call a Service DNS name and kube-proxy routes it.

In practice, Kubernetes + Istio has replaced custom service discovery for most teams. But understanding the underlying mechanism is what distinguishes candidates who have operated distributed systems from those who have only read about them.

## Circuit Breakers

Named after the electrical component that stops current flow when a fault is detected.

In software: if Service A calls Service B and Service B starts returning errors or timing out, a circuit breaker opens after a failure threshold is crossed. While open, calls to Service B fail immediately without waiting for the timeout. After a cooldown period, the circuit enters half-open state and allows a test request through. If it succeeds, the circuit closes.

Without circuit breakers, a slow downstream service causes thread pool exhaustion in the caller. Threads pile up waiting for timeouts. The caller runs out of resources. Now you have a cascading failure.

Netflix built Hystrix specifically to prevent this. After seeing that a single slow dependency could take down the Netflix API, they wrapped all downstream calls in circuit breakers with fallbacks. The fallback for "cannot reach recommendation service" was "return the top 10 most popular titles." The user sees a degraded experience, not an error page.

Key parameters you should know: failure threshold percentage, minimum request volume before the breaker can open, sleep window duration, and request volume threshold.

**Interview signal:** Candidates who have actually operated services know that the hard part is tuning these parameters. Too sensitive and the breaker opens on normal traffic spikes. Too loose and it never opens when you actually need it.

## Saga Pattern for Distributed Transactions

The single hardest microservices problem: how do you maintain data consistency across multiple services when you cannot use a database transaction?

Example: an e-commerce order involves reserving inventory, charging the customer, and scheduling fulfillment. These span three services with three databases. If the charge succeeds but fulfillment scheduling fails, you have an inconsistent state.

The saga pattern breaks the transaction into a sequence of local transactions, each of which publishes an event or calls the next step. If a step fails, compensating transactions roll back the previous steps.

Two coordination styles:

**Choreography:** Each service listens for events and takes action. No central coordinator. Inventory hears `order_created`, reserves stock, publishes `inventory_reserved`. Payments hears `inventory_reserved`, charges the card, publishes `payment_completed`. If payment fails, payments publishes `payment_failed`. Inventory hears `payment_failed` and releases the reserved stock.

Pros: simple, decoupled. Cons: hard to trace, implicit logic distributed across services.

**Orchestration:** A central saga orchestrator tells each service what to do and handles compensations. Uber's order service orchestrates the saga explicitly.

Pros: easy to see the workflow, clear error handling. Cons: the orchestrator becomes a coupling point.

Amazon uses sagas extensively for order processing. The compensating transaction for a failed delivery is either a retry, a reroute, or a refund — each of which is its own saga.

**What to say in an interview:** Acknowledge that sagas only provide eventual consistency. You do not get isolation. Two sagas can see each other's intermediate states. The interview question is usually whether you understand this trade-off.

## Observability in Microservices

A request enters your system and touches 8 services before failing. Without observability, you are blind.

The three pillars:

**Distributed tracing:** Each request gets a trace ID at the entry point. Every service propagates the trace ID in outgoing calls (via HTTP headers: `X-Trace-ID`, or the W3C Traceparent header). A tracing system (Jaeger, Zipkin, AWS X-Ray, Datadog APM) collects spans from each service and reconstructs the full call graph.

Correlation IDs are the minimum viable version: a UUID injected at the edge, logged by every service, searchable across log aggregators like Splunk or Elastic.

**Metrics:** RED metrics per service — Rate (requests/sec), Errors (error rate), Duration (latency percentiles). Prometheus + Grafana is the standard open-source stack. Every service should expose a `/metrics` endpoint.

**Structured logging:** JSON logs with consistent fields — `trace_id`, `service`, `level`, `message`, `duration_ms`. Unstructured text logs across 50 services are unqueryable.

Netflix, Uber, and Amazon all invested heavily in internal observability platforms before their microservices architectures became manageable. Netflix built Atlas for metrics, Mantis for stream processing of operational data, and Edgar for distributed tracing. These were not afterthoughts — they were prerequisites for operating at scale.

**Interview signal:** Mention that observability must be built into service templates from day one. Retrofitting it into 50 services is painful. A candidate who has lived through "we added tracing six months after launch" will say this unprompted.

## The Question You Will Get

"Design a system like Uber's ride-sharing backend." The first question back should be: "What is the scale?" The second should be: "Where are the domain boundaries?" The answer to the second question determines where the service boundaries go. Domain-Driven Design's bounded contexts — not Conway's Law, not team size — are the correct decomposition principle. But the answer to the first question determines whether you even need microservices at all.

Most systems do not. Start with that.
