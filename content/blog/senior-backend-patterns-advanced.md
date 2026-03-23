---
title: "Advanced Backend Patterns for Senior Engineers: Circuit Breakers, Sagas, and CQRS"
description: "Deep dive into advanced backend patterns — circuit breakers, bulkhead pattern, saga pattern for distributed transactions, event sourcing implementation, and CQRS in practice."
date: "2026-03-20"
category: "System Design"
---

Senior backend engineering is largely about managing failure gracefully at scale. The patterns in this guide represent battle-tested approaches to building systems that remain available, consistent, and recoverable when — not if — things go wrong. These are the patterns that come up in staff/senior interviews and that distinguish engineers who have operated production systems from those who have only built them.

## Circuit Breaker Pattern

When a downstream service is failing, continuing to send requests wastes resources, increases latency for users, and can cascade failures across your system. The circuit breaker pattern stops calling a failing service after a threshold of errors, giving it time to recover.

**Three states:**
- **Closed:** Normal operation. Requests pass through. Failures increment a counter.
- **Open:** Too many failures. Requests are immediately rejected (fail fast). A timer starts.
- **Half-Open:** Timer expired. A limited number of test requests are allowed through. Success closes the circuit; failure reopens it.

```python
import time
from enum import Enum

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60, success_threshold=2):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        self.state = "CLOSED"
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                self.success_count = 0
            else:
                raise Exception("Circuit breaker is OPEN — service unavailable")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "CLOSED"

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
```

**Key interview discussion point:** Where should the failure threshold be set? Too low and you trip the breaker on transient errors; too high and you let cascading failures propagate. The answer depends on your SLA, the criticality of the dependency, and whether you have fallback behavior (cached data, degraded mode).

## Bulkhead Pattern

Named after ship compartments that prevent flooding from sinking the whole vessel, the bulkhead pattern isolates different parts of your system so that failures in one partition do not exhaust resources in another.

**Thread pool bulkheads:** Instead of one shared thread pool for all outbound calls, maintain separate pools per downstream service. If the payment service becomes slow and fills its thread pool, the inventory service thread pool is unaffected.

**Semaphore bulkheads:** Limit concurrent calls to a specific dependency using semaphores. When the limit is reached, new calls fail fast rather than queuing indefinitely.

```python
import threading

class Bulkhead:
    def __init__(self, max_concurrent):
        self.semaphore = threading.Semaphore(max_concurrent)

    def execute(self, func, *args, **kwargs):
        acquired = self.semaphore.acquire(blocking=False)
        if not acquired:
            raise Exception("Bulkhead limit reached — request rejected")
        try:
            return func(*args, **kwargs)
        finally:
            self.semaphore.release()
```

Bulkheads pair naturally with circuit breakers. Netflix's Hystrix (now maintained as Resilience4j) popularized combining both patterns.

## Saga Pattern: Distributed Transactions Without 2PC

When a business operation spans multiple services (e.g., "place an order" touches inventory, payment, and shipping), you cannot use a database transaction. Two-phase commit (2PC) exists but introduces tight coupling and availability risk. The saga pattern breaks a distributed transaction into a sequence of local transactions, each with a compensating transaction (undo) that runs if a step fails.

**Choreography-based saga:** Each service publishes events and listens for events from other services. No central coordinator.

```
Order Service: OrderCreated event →
Inventory Service: InventoryReserved event →
Payment Service: PaymentProcessed event →
Shipping Service: ShipmentCreated event

On failure:
Payment fails: PaymentFailed event →
Inventory Service: ReleaseInventory (compensation) →
Order Service: OrderCancelled
```

**Orchestration-based saga:** A central saga orchestrator sends commands to each service and handles the compensation logic.

**When to use which:** Choreography is simpler for simple flows but becomes hard to reason about as flows grow. Orchestration is more complex upfront but provides a single source of truth for the flow's state — easier to debug and monitor.

## Event Sourcing

Traditional systems store current state. Event sourcing stores the sequence of events that led to the current state. The current state is derived by replaying events.

```
# Traditional: User table row
user_id: 123, balance: 850, last_updated: 2026-03-20

# Event sourced: Events for user 123
[AccountOpened(balance=1000), Withdrawal(amount=200), Deposit(amount=50)]
# Current balance derived: 1000 - 200 + 50 = 850
```

**Benefits:** Complete audit log for free, time-travel queries (what was the state at time T?), replay events to rebuild projections, easier debugging.

**Challenges:** Event schema evolution (old events must remain deserializable as schemas change), eventual consistency in read models, growing event log size.

**Implementation pattern:** Events are immutable and append-only. Snapshots periodically capture current state to avoid replaying the full event history for every read.

## CQRS: Command Query Responsibility Segregation

CQRS separates the write model (commands that mutate state) from the read model (queries that return data). This enables independent optimization of each path.

```
Write path: Command → Validate → Apply business logic → Persist event → Update write store
Read path: Query → Read from optimized read store (denormalized, cached)
```

**Why it matters:** A normalized write model (3NF, optimized for consistency) is often poorly suited for complex read queries. A denormalized read model (pre-joined, pre-aggregated) can serve queries orders of magnitude faster. CQRS lets you have both.

**CQRS + Event Sourcing:** Events on the write side are consumed by projectors that maintain the read side's denormalized views. The read side is eventually consistent — it catches up as events are processed.

**When NOT to use CQRS:** Simple CRUD applications do not benefit from CQRS. The pattern adds complexity (eventual consistency, dual models, projector logic) that must be justified by the read/write imbalance or the domain complexity.

## Interview Positioning

These patterns matter in senior and staff interviews because they demonstrate that you think about system failure and recovery, not just happy-path implementation. When discussing any distributed system design, consider proactively asking: "What happens when service X fails here?" and then answering your own question with one of these patterns. That signal — anticipating failure modes without being prompted — is a strong indicator of production engineering experience.
