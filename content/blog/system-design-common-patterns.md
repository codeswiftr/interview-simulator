---
title: "8 System Design Patterns Every Engineer Should Know for Interviews"
description: "CQRS, event sourcing, saga, circuit breaker, sidecar, API gateway, strangler fig, and bulkhead — explained clearly for system design interviews."
date: "2026-03-19"
category: "System Design"
---

# 8 System Design Patterns Every Engineer Should Know for Interviews

System design interviews reward engineers who can name and apply architectural patterns — not because naming patterns is valuable in itself, but because it demonstrates that you have internalized solutions to recurring problems. These 8 patterns appear most frequently in senior engineering interviews. Knowing when to apply them, and being able to explain the trade-offs, is a significant differentiator.

## 1. CQRS (Command Query Responsibility Segregation)

**What it is**: Separate the models used for reading data from the models used for writing data.

**When to use it**: When your read patterns and write patterns are fundamentally different — for example, writes update a normalized relational model, but reads need denormalized projections optimized for specific queries.

**Interview context**: CQRS appears in system design when the interviewer asks "how would you scale this to handle 100x more reads?" A separate read model (often eventually consistent, backed by a read-optimized database like Elasticsearch or a Redis cache) handles read traffic without affecting write performance.

**Trade-off**: Eventual consistency between write and read models. Users may briefly see stale data. Acceptable for most systems; not acceptable for financial balances.

## 2. Event Sourcing

**What it is**: Instead of storing current state, store a log of events that led to the state. Current state is derived by replaying the event log.

**When to use it**: Audit requirements (financial systems, healthcare), need to replay history, complex domain logic where the history of decisions matters.

**Interview context**: "How would you build an audit trail?" or "How would you handle temporal queries (what was the account balance at time T)?" Event sourcing makes these trivial — replay events up to time T.

**Trade-off**: Query complexity (you must read the full event log, or maintain projections), eventual consistency of projections, and debugging complexity. Most systems do not need event sourcing; do not add it speculatively.

## 3. Saga Pattern

**What it is**: Manage distributed transactions across multiple services using a sequence of local transactions, where each step has a compensating transaction for rollback.

**When to use it**: Any time you need atomicity across service boundaries — ordering a product requires updating inventory (Order Service), charging the customer (Payment Service), and scheduling delivery (Fulfillment Service). If any step fails, previous steps must be reversed.

**Two flavors**: Choreography (services emit events and react to each other's events) vs Orchestration (a central saga orchestrator directs each step).

**Interview context**: "How do you handle distributed transactions in a microservices architecture?" The answer is Saga, not 2-Phase Commit (2PC is blocking and fragile at scale).

## 4. Circuit Breaker

**What it is**: Wrap calls to external services with a "circuit breaker" that opens when failures exceed a threshold, short-circuiting calls (and returning fallback responses) until the downstream service recovers.

**When to use it**: Whenever you call external services that may fail. The pattern prevents cascading failures — a slow downstream service should not exhaust your thread pool.

**States**: Closed (normal operation), Open (failures exceeded threshold — calls short-circuit immediately), Half-Open (trial calls to check if service has recovered).

**Interview context**: "How do you prevent a failure in one service from cascading across your system?" Circuit breakers, bulkheads, and timeouts are the answer. Tools: Resilience4j (Java), Hystrix (deprecated), any service mesh (Istio).

## 5. Sidecar

**What it is**: Deploy a helper container alongside the main application container, handling cross-cutting concerns (logging, service discovery, TLS, circuit breaking) without coupling them to the application code.

**When to use it**: In Kubernetes-based microservices architectures where you want to enforce consistent behavior (logging format, mTLS, rate limiting) across many services without modifying each service.

**Interview context**: "How would you implement consistent distributed tracing across all your services without requiring each team to instrument their code?" Sidecar proxies (Envoy, Linkerd) inject tracing headers automatically.

## 6. API Gateway

**What it is**: A single entry point for all client requests, handling cross-cutting concerns (authentication, rate limiting, request routing, protocol translation) before forwarding to backend services.

**When to use it**: Almost always, in any multi-service architecture. The gateway handles concerns that are common across all services (auth, TLS termination, compression) and provides a stable interface to clients even as internal service topology changes.

**Interview context**: System design interviews involving microservices — "how do mobile clients talk to your services?" The API gateway is the expected answer. Discuss: request routing, auth validation, rate limiting, and how you handle gateway failures.

## 7. Strangler Fig

**What it is**: A migration strategy where you incrementally replace a monolith by routing traffic for specific features to new microservices, with a facade layer that handles the routing. New features go to the new system; old features gradually migrate.

**When to use it**: When migrating a monolith to microservices without a big-bang rewrite. The strangler fig grows around the old tree until it can stand alone.

**Interview context**: "How would you migrate this monolith to a microservices architecture without a risky cutover?" The strangler fig pattern allows incremental migration with rollback at each step. LinkedIn, Shopify, and Amazon all used this approach.

## 8. Bulkhead

**What it is**: Isolate different parts of a system so that a failure in one does not cascade to others — like the watertight compartments (bulkheads) in a ship.

**When to use it**: When different workloads have different reliability requirements. For example, use separate thread pools for critical and non-critical operations so that slow non-critical requests cannot exhaust the pool needed for critical requests.

**Interview context**: "How would you ensure that your recommendation service being slow does not affect your checkout service?" Bulkheads (separate thread pools, separate connection pools, separate Kubernetes resource quotas) prevent resource exhaustion from spreading.

---

Naming patterns in system design interviews signals breadth of knowledge. But pattern-dropping without understanding the trade-offs signals the opposite. For each pattern: know what problem it solves, when you would use it, and what you give up. That combination — problem, solution, trade-off — is what senior interviewers are listening for.
