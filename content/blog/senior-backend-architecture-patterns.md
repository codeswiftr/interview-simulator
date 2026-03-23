---
title: "Senior Backend Architecture Patterns Every Engineer Should Know"
description: "The architecture patterns that define senior backend engineers — event sourcing, CQRS, saga, outbox pattern, circuit breaker, bulkhead, and how to apply them in system design interviews."
date: "2026-03-20"
category: "Technical Skills Guides"
---

# Senior Backend Architecture Patterns Every Engineer Should Know

The gap between mid-level and senior backend engineers often comes down to pattern recognition. Senior engineers have a vocabulary of proven solutions to common problems — they can identify that a problem is a "CQRS problem" or an "outbox pattern problem" and apply the appropriate solution without reinventing it. These are the architectural patterns that appear in senior-level system design interviews and that separate thoughtful distributed systems engineers from those who are still discovering these solutions independently.

## Event Sourcing: State as a Log of Events

**The pattern:** Instead of storing current state in a database, store the sequence of events that caused the current state. To get current state, replay all events.

**Classic example:** A bank account. Instead of storing `balance: $1,000`, store events: `AccountOpened($0)`, `Deposited($500)`, `Deposited($750)`, `Withdrawn($250)`. Current balance = sum of all events.

**When it's valuable:**
- Full audit trail required (financial systems, medical records, compliance-heavy domains)
- Ability to reconstruct state at any point in time ("what was the account balance on March 1st?")
- Event-driven downstream processing (multiple services consume the same event stream)

**Tradeoffs interviewers expect you to know:**
- Query complexity: getting current state requires replaying events. Solved with snapshots (periodically save aggregated state; replay from latest snapshot)
- Schema evolution: old events must remain valid as schemas change
- Storage growth: events accumulate forever. Solved with event archival and compaction

## CQRS: Command Query Responsibility Segregation

**The pattern:** Separate the write model (commands that change state) from the read model (queries that return data). Different models optimized for each purpose.

**Without CQRS:** One model serves reads and writes. A user activity feed requires joining users, posts, likes, comments, followers — complex query on the write-optimized schema.

**With CQRS:**
- Write side: normalized tables optimized for transactional integrity
- Read side: denormalized projections (materialized views, document store, search index) optimized for specific query patterns

**Often paired with event sourcing:** Events from the write side are consumed by projections that build the read models. A `PostCreated` event updates the timeline projection for all followers.

**Interview application:** "Design a Twitter feed." Strong answer uses CQRS: write model is normalized posts/follows/likes. Read model is pre-computed user feeds (fan-out on write) or lazy-computed feeds with caching (fan-out on read). Decision depends on scale and ratio of reads to writes.

## Outbox Pattern: Reliable Event Publishing

**The problem:** In a distributed system, you need to update your database AND publish an event to a message queue atomically. If you write to the DB then crash before publishing, the event is lost. If you publish first then crash before writing, the event fires without the DB change.

**The outbox pattern solution:**
1. Write both the business entity change AND the event to an outbox table within the same database transaction
2. A separate process (outbox processor) reads from the outbox table and publishes events to the message queue
3. After successful publish, mark the event as processed in the outbox

**Why it works:** The business change + outbox write is atomic (same transaction). The outbox processor handles the eventual consistency between the outbox and the message queue. Even if the processor crashes and replays, the downstream consumer handles duplicates (at-least-once delivery with idempotent consumers).

**Alternatives:** Debezium (change data capture — CDC) reads the database's transaction log and publishes events. Eliminates the application-level outbox table but adds infrastructure complexity.

## Saga Pattern: Distributed Transactions Without 2PC

Already covered in the distributed systems guide, but worth revisiting in the architecture patterns context:

**The pattern:** Replace distributed transactions (2PC) with a series of local transactions connected by events or commands. Each step has a compensating transaction for rollback.

**Two flavors:**
- **Choreography-based:** Services react to events. `OrderPlaced` event → `InventoryReserved` event → `PaymentProcessed` event. No central coordinator; fragile at scale but simple to start
- **Orchestration-based:** A saga orchestrator tells each service what to do and handles compensation. More visible, easier to debug, adds a coordination service

**Interview scenario:** "How would you handle a failed partial order — items shipped from one warehouse, but another warehouse is out of stock?" This is a saga problem: compensate the successful warehouse shipment (issue a return/hold), notify the customer, potentially re-fulfill from an alternative warehouse.

## Bulkhead and Circuit Breaker: Resilience Patterns

**Circuit Breaker:**
Three states: Closed (normal operation) → Open (failing fast, rejecting calls immediately without trying) → Half-Open (testing if service has recovered with limited traffic). Prevents cascading failures when a dependency is degraded.

**Bulkhead:**
Isolate resources (thread pools, connection pools) for different operations. If the image processing thread pool is exhausted (slow S3 uploads), it doesn't block the thread pool serving user API requests. Modeled on ship bulkheads — one compartment flooding doesn't sink the ship.

**Rate Limiting (token bucket vs sliding window):**
- Token bucket: N tokens added per second, up to bucket capacity. Allows bursts (use saved tokens). Simple to implement.
- Sliding window: Track request timestamps in a rolling window. More accurate, more memory.
- Fixed window: Count per minute. Simple but "thundering herd" at window boundary.

## Anti-Corruption Layer

**When:** Integrating with a legacy system or third-party API that uses a different domain model.

**The pattern:** Create a translation layer between your clean domain model and the external system's model. Your domain objects use your language; the anti-corruption layer translates to/from the external API.

**Why it matters:** Without it, the external system's concepts leak into your domain model. This creates coupling — changes to the external API require changes throughout your codebase. With the ACL, only the ACL changes when the external system changes.

These patterns form the vocabulary of senior backend architecture. In a system design interview, naming and correctly applying a pattern demonstrates familiarity with how real production systems are built at scale — which is exactly what senior-level interviews are designed to assess.
