---
title: "Event-Driven Architecture Interview Guide"
description: "Events, queues, and streams in system design interviews: Kafka vs SQS vs RabbitMQ, event sourcing, CQRS, exactly-once delivery, and when event-driven architecture is the wrong choice."
date: "2026-03-19"
category: "Technical Skills"
---

# Event-Driven Architecture Interview Guide

Event-driven architecture appears in system design interviews at companies building distributed systems — Stripe, Uber, Netflix, Shopify, Confluent. The questions test whether you understand when events are the right abstraction, how messaging systems work, and what failure modes require explicit handling. This guide covers what interviewers actually probe.

## Why Events and When to Use Them

The motivation for event-driven design: services that communicate through events are decoupled — the producer doesn't know or care who consumes the event. This enables:

- **Async processing**: The payment service publishes "payment.completed" and moves on; the notification service, analytics service, and fraud service each consume it independently
- **Fan-out**: A single event reaches multiple consumers without the producer managing a list of destinations
- **Temporal decoupling**: Consumers can be offline and catch up when they come back

When events are the wrong choice: when you need synchronous responses (an API call that returns a result), when the ordering guarantees are complex to maintain, or when the team doesn't have the operational maturity to manage a messaging system. "Use events for everything" is as wrong as "never use events."

Interview question: "When would you not use an event-driven approach?" Strong answers give concrete scenarios: payment confirmation flows where the user is waiting for a synchronous response, simple CRUD operations with no downstream consumers, small systems where messaging overhead exceeds the benefit.

## Kafka vs SQS vs RabbitMQ: The Comparison Interviewers Test

These three systems appear constantly in system design interviews. The right choice depends on the use case, and interviewers evaluate whether you know the trade-offs:

**Apache Kafka**: Distributed log. Messages are retained for a configurable time window, enabling replay. Consumers track their own position (consumer group offsets). High throughput, horizontally scalable, ordered within a partition. Best for: event streaming, audit logs, data pipelines where replay matters, high-throughput scenarios.

**Amazon SQS**: Queue. Messages are consumed and deleted (not stored). At-least-once delivery by default; FIFO queues provide exactly-once within a message group. Fully managed. Best for: work queues where you need to distribute tasks to workers, simple async decoupling, serverless workloads.

**RabbitMQ**: Message broker with routing. Supports exchanges, routing keys, and binding patterns that route messages to queues based on rules. Messages can be ACKed/NACKed. Best for: complex routing requirements, task queues with different consumer types, on-premise deployments.

The framing for interviews: "What do you need the message system to do after the consumer reads the message?" Kafka: keep it, the consumer can re-read. SQS: delete it, the consumer is done. RabbitMQ: route it based on rules.

## Delivery Guarantees: The Core Interview Topic

This is where most system design discussions go deeper. Three delivery guarantees:

**At-most-once**: Fire and forget. The producer sends, doesn't retry. Messages may be lost. Acceptable for: logging, metrics, telemetry where occasional loss is tolerable.

**At-least-once**: The producer retries until acknowledged. Messages may be delivered multiple times. Consumers must handle duplicate messages. This is the default for Kafka (with retries) and SQS standard queues.

**Exactly-once**: Each message is processed exactly once. Technically achievable with Kafka transactions + idempotent producers, or with SQS FIFO + message deduplication IDs. Carries overhead and operational complexity.

Interview question: "Your payment processing service consumes events from a queue. What happens if a message is delivered twice?" The answer reveals whether you understand idempotency: the consumer must be idempotent — processing the same payment event twice should produce the same result as processing it once. Implementation: store processed message IDs in a database and check before processing.

## Event Sourcing and CQRS

These patterns appear in senior system design interviews and are often misunderstood.

**Event sourcing**: Store the sequence of events that led to current state, not the current state itself. The current state is derived by replaying events. Benefits: complete audit trail, ability to replay history, natural fit for event-driven systems. Costs: query complexity (you must project current state for reads), event schema evolution, storage growth.

**CQRS (Command Query Responsibility Segregation)**: Separate the write model (commands that change state) from the read model (queries that return state). Often paired with event sourcing: commands produce events that are stored; events are projected into read-optimized views.

When to suggest these in a system design interview: when the interviewer asks about audit logging, when you need to support "what did the system look like at time T", or when read and write access patterns are fundamentally different. Don't suggest them for simple CRUD — the complexity cost is real.

## Practical Patterns for System Design

**Outbox pattern**: Solving the dual-write problem — ensuring that a database write and an event publish either both succeed or both fail. Store the event in an "outbox" table in the same database transaction as the state change; a separate process reads the outbox and publishes to the message system. Guarantees consistency without distributed transactions.

**Dead letter queues**: Where messages go after exceeding retry limits. Essential for production messaging: without a DLQ, failed messages are silently lost. Interviewers ask: "What happens to a message your consumer can't process?" The answer must include retry logic and DLQ handling.

**Consumer groups and partitioning**: Kafka allows multiple consumer groups to read the same topic independently (fan-out). Within a consumer group, each partition is read by exactly one consumer (scale-out). Partitioning key choice affects ordering — all events for the same entity should go to the same partition to preserve order.

## What to Study

- **Kafka documentation**: The consumer group model, offset management, and partitioning are the most interview-relevant concepts
- **Designing Event-Driven Systems** (Ben Stopford): Free O'Reilly book, covers Kafka patterns and event streaming architecture
- **The Outbox Pattern**: Martin Fowler's writing on transactional outbox is the reference implementation
- **Build something**: Running Kafka or RabbitMQ locally and consuming events in a simple service makes the concepts concrete in ways that reading cannot

Engineers who've debugged a consumer lag problem or investigated a duplicate event bug explain these concepts with specificity that pure study cannot replicate. Build the experience before the interview.
