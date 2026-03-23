---
title: "Software Architecture Patterns: Microservices, Monoliths, and Event-Driven Systems"
description: "Architecture patterns for senior engineering interviews — monolith vs. microservices, CQRS, event sourcing, saga pattern, strangler fig, and when to use each."
date: "2026-03-20"
category: "System Design"
---

# Software Architecture Patterns: Microservices, Monoliths, and Event-Driven Systems

Architecture pattern questions appear in senior and staff engineer interviews to test whether you can reason about system design at a strategic level. The questions aren't "what is microservices" — they're "given these constraints, what architecture would you choose, and why?" Here's the framework and the key patterns.

## Monolith vs. Microservices

The most common architecture question. The honest answer: most systems should start as a monolith and extract services when there's a clear reason to.

**When to start with a monolith:** Team is small (< 10 engineers), system requirements are evolving, domain boundaries aren't well understood yet. A well-structured monolith with clear module boundaries is easier to build, deploy, and debug than distributed microservices.

**When to extract a service:** A component has significantly different scaling requirements, a team boundary wants independent deployment velocity, or a component needs a different technology stack. Extract along natural seams — user-facing APIs and background jobs are natural candidates.

**The microservices trap:** Teams prematurely decompose, creating distributed systems complexity without the business justification. Now you have network failures, distributed transactions, and operational overhead without the velocity gains. Netflix and Uber have hundreds of services because they have hundreds of teams. A 20-person startup does not.

## CQRS (Command Query Responsibility Segregation)

Separate the models for writing data (commands) and reading data (queries). The write model accepts commands and validates business rules; the read model is optimized for the specific queries the application needs.

**Why:** The same data model that's optimized for writes (normalized, enforces invariants) is often terrible for reads (lots of joins, missing denormalized aggregates). CQRS lets you optimize each side independently.

**Implementation:** Write commands update a canonical data store (relational DB). A projection process subscribes to change events and maintains denormalized read models (potentially in different databases — Elasticsearch for search, Redis for hot data, PostgreSQL view for reporting).

**Trade-off:** Eventual consistency between write and read models. After a command, the read model may lag by milliseconds to seconds. This is acceptable for most features but requires careful handling for cases where users expect to see their just-submitted change immediately.

## Event Sourcing

Instead of storing current state, store the sequence of events that led to the current state. Current state is derived by replaying events.

**Advantages:** Complete audit log, ability to replay and reconstruct state at any point in time, decoupling (downstream systems subscribe to events rather than polling).

**Disadvantages:** Query complexity (no simple SELECT * for current state), schema evolution (old events must remain replayable as the schema evolves), eventual consistency for projections. Event sourcing adds complexity — only use it when the benefits are clear (audit requirements, temporal queries, event-driven integration).

## Saga Pattern (Distributed Transactions)

In a microservices architecture, a business transaction often spans multiple services. Traditional database transactions don't work across services. The Saga pattern breaks the transaction into local transactions, each publishing events or triggering the next step.

**Choreography-based saga:** Each service listens for events and publishes events when its local transaction completes. Loose coupling, but hard to track overall transaction state.

**Orchestration-based saga:** A central coordinator (saga orchestrator) sends commands to services and receives replies. Easier to track and debug, but introduces a coordinator as a central dependency.

**Compensating transactions:** If a saga step fails, previously completed steps are rolled back via compensating transactions (explicit undo operations). These must be idempotent and designed upfront.

## Strangler Fig Pattern

When migrating a legacy monolith to a new architecture, the strangler fig approach: build new functionality in the new system, gradually intercept calls to the legacy system and route them to the new system, eventually decommission the legacy system.

The key: you never have a big-bang rewrite. The old system continues to serve traffic while you strangle it one feature at a time. A reverse proxy (nginx, API gateway) sits in front of both systems and routes based on path or header.

## Event-Driven Architecture

Services communicate via events rather than synchronous API calls. Producers publish events to a message broker (Kafka, SNS/SQS); consumers subscribe and react.

**Benefits:** Temporal decoupling (producer doesn't wait for consumer), fan-out (one event consumed by multiple services), resilience (consumer processes at its own pace, buffers traffic spikes).

**Challenges:** No immediate feedback on whether the event was processed successfully, harder to debug than synchronous calls, requires idempotent consumers.

**When to use event-driven vs. synchronous:** Synchronous for operations where the caller needs the result immediately (API responses, user-facing reads). Event-driven for background operations, fan-out notifications, audit logging, and decoupling services with different scaling characteristics.

## Architecture Decision Records (ADRs)

A practical addition that signals maturity: mention that architectural decisions should be documented in Architecture Decision Records. An ADR captures the context, the decision, and the tradeoffs considered. This creates institutional memory and prevents revisiting the same decisions repeatedly.

For senior/staff interviews, proposing ADRs as part of your architecture process demonstrates that you think about long-term maintainability, not just the current design.
