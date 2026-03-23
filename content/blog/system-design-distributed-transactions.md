---
title: "System Design: Distributed Transactions — Two-Phase Commit, Saga Pattern, and Eventual Consistency"
description: "A rigorous guide to distributed transaction design for senior engineering interviews — covering 2PC, the Saga pattern, idempotency, and when to use each approach."
date: "2026-03-20"
category: "System Design"
---

# System Design: Distributed Transactions — Two-Phase Commit, Saga Pattern, and Eventual Consistency

Distributed transactions are among the most frequently mishandled topics in system design interviews. Junior engineers say "use a database transaction." Mid-level engineers say "use two-phase commit." Senior engineers explain why 2PC is rarely the right answer in microservices, describe the Saga pattern in concrete terms, and discuss the operational complexity of achieving consistency without distributed locks.

This guide gives you the framework to answer distributed transaction questions at the senior and staff level.

## The Core Problem

You have an order service, an inventory service, and a payment service. A customer submits an order. You need to:

1. Deduct inventory
2. Charge the payment method
3. Create the order record

All three must succeed together, or none should take effect. In a monolith with a single database, this is a `BEGIN TRANSACTION` / `COMMIT` block. In a microservices architecture with three separate databases, there is no such primitive.

This is the fundamental distributed transaction problem.

## Option 1: Two-Phase Commit (2PC)

Two-phase commit is the classic distributed transaction protocol. A coordinator manages two phases:

**Phase 1 (Prepare):** The coordinator sends a "prepare" message to all participants. Each participant writes the pending changes to durable storage and responds "yes" (ready to commit) or "no" (abort).

**Phase 2 (Commit/Rollback):** If all participants respond "yes," the coordinator sends "commit." If any respond "no," the coordinator sends "rollback."

**Why 2PC is problematic in practice:**

- **Blocking:** If the coordinator crashes after Phase 1 but before Phase 2, participants are blocked — they've voted "yes" and locked resources, but can't commit or rollback without hearing from the coordinator. This can stall indefinitely.
- **Latency:** 2PC requires at least two round trips across services before a transaction completes. For high-throughput systems, this is prohibitive.
- **Availability trade-off:** 2PC prioritizes consistency (CP in CAP theorem). If a participant is unavailable, the transaction cannot proceed. For a payment system processing thousands of transactions per second, this means a brief database hiccup in the inventory service blocks all orders.

2PC is appropriate for low-throughput, high-consistency requirements where you control all participants (e.g., a single-vendor database cluster). It is rarely appropriate for microservices at internet scale.

## Option 2: The Saga Pattern

The Saga pattern decomposes a distributed transaction into a sequence of local transactions, each of which publishes an event or message that triggers the next step. If any step fails, the Saga executes compensating transactions to undo the work already done.

**Two implementations:**

### Choreography-based Saga

Each service listens for events and decides what to do next. There's no central coordinator.

```
1. Order Service: creates order (status: PENDING), publishes OrderCreated event
2. Inventory Service: listens, reserves inventory, publishes InventoryReserved event
3. Payment Service: listens, charges card, publishes PaymentCompleted event
4. Order Service: listens, updates order status to CONFIRMED
```

If payment fails:
```
Payment Service: publishes PaymentFailed event
Inventory Service: listens, releases reservation, publishes InventoryReleased event
Order Service: listens, marks order CANCELLED
```

**Pros:** No single point of failure, loose coupling. **Cons:** Business logic is scattered across services; difficult to reason about the overall flow; debugging failures requires tracing events across multiple services.

### Orchestration-based Saga

A central "Saga Orchestrator" (or process manager) drives the workflow, sending commands to each service and handling responses.

```
Orchestrator → OrderService: CreateOrder
OrderService → Orchestrator: OrderCreated
Orchestrator → InventoryService: ReserveInventory
InventoryService → Orchestrator: InventoryReserved
Orchestrator → PaymentService: ProcessPayment
PaymentService → Orchestrator: PaymentFailed
Orchestrator → InventoryService: CancelReservation (compensating transaction)
Orchestrator → OrderService: CancelOrder (compensating transaction)
```

**Pros:** Business flow is visible in one place; easier to debug; explicit compensation logic. **Cons:** Orchestrator becomes a coordination bottleneck; creates coupling between services and the orchestrator.

**When to choose which:** Orchestration is almost always preferable for complex, multi-step business workflows. Choreography works well for simple two- or three-step flows where the coupling concern outweighs the debugging cost.

## Idempotency: The Non-Negotiable Foundation

Both 2PC and Sagas break down without idempotency. When a service crashes mid-operation and recovers, it may re-process a message it already handled. Without idempotency, you charge the customer twice, reserve inventory twice, or create duplicate orders.

**Idempotency key pattern:**

Every operation carries a client-generated idempotency key (typically a UUID). Before processing, the service checks whether it has already processed a request with this key. If yes, return the cached response. If no, process and store the key with the response.

Implementation checklist:
- The idempotency key check and the operation must happen atomically (use a database transaction for the check-and-write)
- Store idempotency keys with a TTL (keys don't need to live forever — 24 hours is typically sufficient for retry windows)
- Return the same response for duplicate requests, including the same error if the original failed

## Eventual Consistency: The Conceptual Foundation

Both Saga and event-driven approaches embrace eventual consistency: the system will be consistent, but not instantly. During the window between steps, the system is in a partially-applied state.

The key question: **is this acceptable for your use case?**

For most internet-scale applications, yes — with caveats:
- Users can see a brief "processing" state rather than immediate confirmation
- The system must have clear compensation logic for every failure mode
- Observability is critical — you need to detect and alert on Sagas stuck in intermediate states

For financial systems with strict regulatory requirements (e.g., a bank ledger), eventual consistency requires more careful design — typically using outbox patterns and strong ordering guarantees on event streams.

## The Outbox Pattern

A common failure mode in event-driven Sagas: a service successfully writes to its database but then crashes before publishing the event. The Saga stalls.

The Outbox pattern solves this:
1. As part of the local database transaction, write the event to an "outbox" table in the same database
2. A separate process reads the outbox table and publishes events to the message broker
3. Events are published at-least-once (idempotent consumers handle duplicates)

This guarantees that if the local transaction commits, the event will eventually be published — even if the service crashes between the database write and the message publish.

## Interview Framework

When asked about distributed transactions:

1. Identify the consistency requirement: strict (2PC territory) or eventual (Saga territory)?
2. Choose Saga for microservices; explain why 2PC is unsuitable at scale
3. Choose orchestration vs. choreography based on workflow complexity
4. Explain idempotency as a prerequisite, not an afterthought
5. Address the outbox pattern for reliable event publishing
6. Discuss observability: how do you detect and recover stuck Sagas?

The engineers who stand out in these interviews are those who can explain not just the mechanics of the pattern, but the failure modes it creates and how to handle them operationally.
