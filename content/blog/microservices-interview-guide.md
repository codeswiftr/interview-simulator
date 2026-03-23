---
title: "Microservices Architecture in System Design Interviews"
description: "Master microservices concepts for system design interviews. Covers service decomposition, inter-service communication, data consistency, observability, and when NOT to use microservices."
date: "2025-10-23"
category: "Technical Skills Guides"
---

# Microservices Architecture in System Design Interviews

Microservices is one of the most frequently discussed architectural patterns in system design interviews. Understanding not just how microservices work, but when to use them and what problems they introduce, is what separates strong system design candidates from average ones.

## What Microservices Actually Solve

Before discussing microservices in an interview, be clear on the problem they solve — and the problems they create.

**What they solve:**
- **Independent deployability**: Each service can be deployed, scaled, and updated without redeploying the entire system
- **Team autonomy**: Different teams own different services with clear API contracts
- **Technology heterogeneity**: Services can use different languages and databases
- **Fault isolation**: A bug in one service doesn't take down the entire system

**What they create:**
- **Distributed system complexity**: Network latency, partial failures, eventual consistency
- **Operational overhead**: Each service needs deployment, monitoring, logging, and alerting
- **Data consistency challenges**: No ACID transactions across services
- **Developer experience cost**: Local development with many services is painful

**The interview answer**: "I'd start with a modular monolith unless we have a clear need for independent scaling or team boundaries that justify the operational overhead."

## Service Decomposition Strategies

When breaking a system into services, use these strategies:

**Domain-Driven Design (DDD)**: Decompose by bounded contexts — areas of the domain with clear ownership and minimal coupling. E.g., an e-commerce system might have: Catalog, Orders, Payments, Inventory, Shipping, Users.

**Strangler Fig Pattern**: When migrating a monolith, don't rewrite all at once. Gradually extract services while the monolith continues to run. Each new service "strangles" part of the monolith.

**Single Responsibility Principle**: Each service owns one business capability end-to-end. A service owns its data model, business logic, and API.

**Red flags in decomposition**:
- Services that must always be deployed together (not actually independent)
- Services with circular dependencies
- Services that share a database (defeats isolation)

## Inter-Service Communication

Services communicate in two ways:

### Synchronous (Request/Response)
- **REST/HTTP**: Most common, easy to debug, coupling between services
- **gRPC**: More efficient than REST, strongly typed, good for internal services with high throughput requirements

**Problems**: Cascading failures (Service A calls B calls C — if C is slow, A is slow), temporal coupling (both services must be up)

**Solutions**: Circuit breakers (Hystrix, Resilience4j), timeouts, retries with exponential backoff

### Asynchronous (Event-Driven)
- **Message queues**: SQS, RabbitMQ — point-to-point
- **Event streaming**: Kafka — publish/subscribe, event replay, high throughput

**Benefits**: Decoupled services, better resilience, natural audit log

**Problems**: Eventual consistency, harder to debug, need for idempotent consumers

**Interview guidance**: Use async for operations where you don't need an immediate response (notifications, inventory updates after order placement). Use sync for operations that need a real-time response (payment authorization).

## Data Consistency Patterns

The hardest part of microservices. Each service should own its database (Database per Service pattern). But this breaks ACID transactions.

**Saga Pattern**: Distribute a transaction across services using a sequence of local transactions with compensating transactions for rollback.

```
Order Service: Create order → 
Payment Service: Reserve payment → 
Inventory Service: Reserve stock → 
Shipping Service: Schedule delivery

If Inventory fails:
← Payment Service: Release reservation
← Order Service: Cancel order
```

Two saga coordination approaches:
- **Choreography**: Services react to events (simpler, harder to track)
- **Orchestration**: A central coordinator tells services what to do (clearer, coupling to coordinator)

**Outbox Pattern**: Write an event to an "outbox" table in the same local transaction as your database update. A separate process publishes these events to the message broker. Solves the dual-write problem.

## Observability: The Non-Negotiable

In a microservices system, you can't debug by looking at one log file. You need:

**Distributed Tracing**: Every request gets a trace ID that propagates across services. Tools: Jaeger, Zipkin, OpenTelemetry + Datadog/Honeycomb.

**Centralized Logging**: All service logs aggregated with trace IDs. Tools: ELK stack, Datadog, Loki.

**Metrics**: Each service emits key metrics (request rate, error rate, latency — the RED metrics). Dashboards and alerts for anomalies. Tools: Prometheus + Grafana.

**Health checks**: Each service exposes `/health` and `/ready` endpoints for load balancers and orchestrators.

## API Gateway Pattern

Services shouldn't be directly accessible to clients. An API Gateway provides:
- Single entry point for all clients
- Authentication/authorization
- Rate limiting
- Request routing
- Response aggregation (Backend for Frontend pattern)
- SSL termination

Tools: AWS API Gateway, Kong, Nginx, Envoy.

## When to Say "Not Microservices" in an Interview

Strong candidates can recognize when microservices are wrong. Say "I'd use a modular monolith" when:
- The team is small (< 10 engineers)
- The domain is not well-understood yet (premature decomposition is expensive)
- The operational maturity isn't there (no good CI/CD, monitoring, or container orchestration)
- The system is not at a scale where independent scaling matters

The best system design answers don't reflexively recommend microservices — they reason about what the system actually needs.
