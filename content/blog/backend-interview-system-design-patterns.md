---
title: "Backend Engineer System Design Patterns: Beyond the Basics"
description: "Advanced system design patterns for backend engineers — CQRS, event sourcing, saga patterns, outbox pattern, and how to discuss these in system design interviews."
date: "2026-03-20"
category: "System Design"
---

# Backend Engineer System Design Patterns: Beyond the Basics

Entry-level system design interviews cover databases, caching, and load balancing. Senior and staff-level interviews go deeper: distributed transactions, event-driven consistency, and the operational tradeoffs of complex patterns. This guide covers the patterns that separate senior backend engineers from intermediate ones — and how to discuss them without sounding like you read a Wikipedia article.

## CQRS: Command Query Responsibility Segregation

CQRS splits your application into two models: one for writes (commands) and one for reads (queries). Instead of a single service and database handling both, you have separate paths optimized for each concern.

**When it's worth the complexity**: CQRS earns its overhead when read and write loads differ significantly, when read models need to be shaped very differently from the write model, or when you need multiple read projections of the same data (e.g., an e-commerce order viewed differently by the customer, warehouse, and billing team).

**What it looks like in practice**: The command side receives `PlaceOrder`, `CancelOrder`, `UpdateShipping` commands. It validates, applies business logic, persists to the write store (often a normalized relational DB), and emits domain events. The query side maintains denormalized read models optimized for specific query patterns — perhaps a Redis hash for real-time order status, and a Postgres materialized view for order history dashboards. The read models are updated asynchronously by consuming domain events.

**The tradeoff to articulate**: Read models are eventually consistent with the write model. A user who places an order may not see it in their order history for 100-500ms while the event propagates. For most use cases this is acceptable. For anything requiring read-your-writes consistency, you either need synchronous read model updates (defeating part of the benefit) or you return the write response directly and trust the client to display optimistically.

In an interview, describe CQRS by leading with the problem it solves ("complex domains where read and write models diverge"), then the pattern, then the operational cost. Interviewers are testing whether you know when NOT to use a pattern as much as when to use it.

## Event Sourcing

Event sourcing stores the history of state changes (events) as the source of truth, rather than current state. Instead of `UPDATE orders SET status='shipped'`, you append `OrderShipped{orderId, timestamp, carrier, trackingNumber}` to an immutable event log.

**The key insight**: Current state is derived by replaying events. Want to know an order's current status? Fold (reduce) over its event log. Want state as of last Tuesday? Replay only events up to that timestamp.

**Strengths**: Complete audit trail for free, ability to replay and rebuild projections (invaluable for debugging production issues), natural fit with CQRS (events are the mechanism that updates read models), and temporal queries without special tooling.

**Challenges to address in interviews**:

*Schema evolution*: Events are immutable, but your understanding of them changes. If `OrderPlaced` in 2022 didn't include `customerId` but now it must, you need a migration strategy. Common approaches: event versioning (store `OrderPlacedV2`), upcasting (convert old events to new format during replay), or "gentle" schema changes that add optional fields only.

*Storage growth*: An append-only log grows indefinitely. Use snapshotting: periodically capture current aggregate state as a snapshot, then only replay events after the latest snapshot. Dramatically reduces replay time for long-lived aggregates.

*Event sourcing is not a universal pattern*. Don't event-source a simple CRUD service for user profile management. The complexity is justified for business domains where audit history, temporal queries, and event-driven integrations provide clear value.

## Saga Pattern for Distributed Transactions

When a business transaction spans multiple services, you can't use a single database transaction. The saga pattern coordinates multi-service workflows through a sequence of local transactions, each of which publishes events or messages to trigger the next step.

**Two implementation styles**:

**Choreography-based sagas**: Each service listens for events and reacts. `OrderService` emits `OrderCreated` → `InventoryService` listens, reserves stock, emits `StockReserved` → `PaymentService` listens, charges the card, emits `PaymentCompleted` → `OrderService` listens, marks order confirmed. No central coordinator. Simple and decoupled, but the saga flow is implicit and hard to trace.

**Orchestration-based sagas**: A central saga orchestrator (a dedicated service or a workflow engine like Temporal) explicitly coordinates steps. The orchestrator sends `ReserveStock` command to InventoryService, waits for response, sends `ChargeCard` to PaymentService, waits, then confirms the order. The flow is explicit and observable. Preferred for complex, long-running sagas.

**Compensating transactions**: Sagas don't use rollback — they use compensation. If payment fails after stock was reserved, the saga sends a `ReleaseStock` compensating command. Each step in a saga must have a corresponding compensating action defined upfront.

**The critical point interviewers test**: Sagas achieve eventual consistency, not ACID atomicity. A window exists where partial execution has happened (stock reserved, payment not yet charged). Design your business logic to handle this gracefully, and make compensating transactions idempotent.

## Outbox Pattern for Reliable Event Publishing

A common failure mode in event-driven systems: your service updates its database and then publishes an event to Kafka — but the service crashes between the two operations. Database updated, event never sent. Consumers miss it. Data inconsistency ensues.

The outbox pattern solves this with a single atomic database transaction:

1. In the same transaction that updates your domain data, write the event to an `outbox` table
2. A separate "relay" process (or a CDC connector like Debezium) reads the outbox table and publishes events to the message broker
3. Once successfully published, the relay marks the outbox row as processed (or deletes it)

Because the domain update and outbox write are atomic, they either both commit or both roll back. The relay publishes independently. If the relay crashes, it simply re-reads unpublished outbox rows and publishes them. Events are delivered at-least-once — make your consumers idempotent accordingly.

**Debezium** is the common production tool here: it uses PostgreSQL's logical replication (Change Data Capture) to stream the outbox table changes directly to Kafka without a polling loop. Mention Debezium if you want to signal production familiarity.

## Idempotency Patterns

Distributed systems retry. Networks partition. Messages are delivered more than once. Idempotency ensures that processing the same request or event multiple times has the same effect as processing it once.

**Idempotency keys for APIs**: The client generates a unique key (UUID) per logical operation and sends it with the request. The server stores the key and result. On retry with the same key, the server returns the cached result without re-processing. Critical for payment APIs, booking APIs, and any mutating operation the client might retry.

**Deduplication for event consumers**: Store processed event IDs (in Redis or a database) and skip events whose ID has already been processed. The event ID window (how long you retain processed IDs) depends on your maximum expected retry window.

## Common Senior Backend Interview Questions

**"Walk me through how you'd handle a distributed transaction where three services need to update atomically."** — Describe the saga pattern with orchestration, explain compensating transactions, acknowledge eventual consistency.

**"Your service writes to Postgres and Kafka. How do you prevent data loss if the process crashes between the two?"** — Outbox pattern with Debezium.

**"Your read queries are complex and slow down your write path. How do you address this?"** — CQRS with event-driven read model updates.

**"You're building an e-commerce platform. Should you use event sourcing?"** — "For the order domain, potentially yes — audit history and temporal queries are valuable, and the domain is complex enough to justify the overhead. For user profiles and product catalog, no — standard CRUD is appropriate."

The hallmark of a senior backend answer is context-sensitivity: knowing the problem each pattern solves, the operational cost it introduces, and when simpler alternatives are the right choice.
