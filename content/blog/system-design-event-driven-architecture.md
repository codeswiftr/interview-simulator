---
title: "System Design: Event-Driven Architecture and Message Queues"
description: "How to design event-driven systems in interviews — Kafka vs SQS vs RabbitMQ, event sourcing, CQRS, exactly-once delivery, and handling backpressure in distributed event systems."
date: "2026-03-20"
category: "System Design"
---

# System Design: Event-Driven Architecture and Message Queues

Event-driven architecture questions appear frequently in senior and staff engineer interviews. Whether you're designing a notification system, an order processing pipeline, or a real-time analytics platform, the patterns repeat. This guide gives you the vocabulary, the tradeoffs, and the interview-ready answers.

## Why Event-Driven Architecture?

Event-driven systems decouple producers from consumers. When an order is placed, the order service publishes an event. The inventory service, notification service, and analytics pipeline each consume that event independently — none of them need to know about each other, and the order service doesn't wait for them.

This coupling reduction comes at a cost: complexity. You now have a distributed system with all the failure modes that implies. Interviewers probe this tradeoff: "When would you choose event-driven over direct service calls?" The answer: when you need loose coupling, fan-out (one event → many consumers), temporal decoupling (consumer can process at its own pace), or resilience (consumer can catch up after downtime).

## Kafka vs SQS vs RabbitMQ

Know the key tradeoffs between the major message systems:

**Apache Kafka:** Log-based, ordered per partition, consumer maintains offset (pull model), messages are retained for a configurable period. Excellent for high throughput, replay, and multiple independent consumer groups reading the same stream. Complex to operate. Kafka is the standard for event streaming and event sourcing architectures.

**Amazon SQS:** Queue-based, distributed, at-least-once delivery, messages deleted after consumption. Standard queues have no ordering guarantee; FIFO queues guarantee ordering but have lower throughput. Fully managed, simple to operate. Best for job queues and simple fan-out patterns with SNS.

**RabbitMQ:** Broker-based with flexible routing (direct, fanout, topic, headers exchanges). Supports complex routing patterns. At-most-once or at-least-once delivery. Better suited than Kafka for task queues with acknowledgments and routing logic; less suited for high-throughput streaming.

The interview decision: Kafka for streaming, event sourcing, and replay. SQS/RabbitMQ for task queues and job processing.

## Delivery Guarantees

This is almost always asked in depth. Know the three guarantees:

**At-most-once:** Message may be lost, never delivered twice. Lowest overhead. Acceptable for metrics and logging where some loss is tolerable.

**At-least-once:** Message delivered one or more times. Requires idempotent consumers — processing the same message twice must have the same effect as processing it once. Most practical for production systems.

**Exactly-once:** Each message processed exactly once. Requires coordination between the broker and consumer. Kafka supports exactly-once semantics (EOS) within Kafka using transactions, but it's complex and has performance overhead. SQS FIFO provides exactly-once processing per message group within a deduplication window.

For most systems: design for at-least-once with idempotent consumers. This is simpler, more reliable, and scales better than exactly-once semantics.

## Idempotency Patterns

Designing idempotent consumers is a core skill. Patterns:

**Idempotency keys:** Include a unique event ID. Before processing, check if the ID has been processed (store in Redis or DB). If yes, skip. Requires deduplication storage.

**Natural idempotency:** Some operations are naturally idempotent. Setting a field to a specific value is idempotent; incrementing a counter is not. Design your event payloads to enable idempotent application.

**Versioned state:** Use optimistic locking on the state being updated. If the event tries to update a version that's already been superseded, discard it.

## Event Sourcing and CQRS

Event sourcing stores all state changes as an immutable log of events rather than current state. Current state is derived by replaying events. Advantages: complete audit log, ability to replay and rebuild state, temporal queries ("what was the state at time T?").

CQRS (Command Query Responsibility Segregation) often accompanies event sourcing: separate models for writes (commands) and reads (queries). The write model handles commands and produces events; the read model subscribes to events and maintains optimized read representations.

Interview question: "What are the downsides of event sourcing?" Answer honestly: eventual consistency (read models lag behind writes), schema evolution complexity (old events with old schemas must still be replayable), query complexity (you can't simply SELECT * WHERE), and operational overhead (storing and managing the event log).

## Backpressure and Flow Control

Backpressure is the mechanism by which consumers signal to producers that they're overwhelmed, preventing the system from drowning in unprocessed messages. Interviewers probe this in capacity planning questions.

In Kafka, backpressure is implicit: producers block when the buffer is full (based on `max.block.ms`). Consumers can slow down by simply not committing offsets while they process. This is a key advantage of pull-based systems — consumers control their pace.

In push-based systems (webhooks, some queue patterns), you need explicit backpressure: consumers returning 429 with Retry-After headers, circuit breakers that stop consuming when downstream is slow, adaptive rate limiting.

Common anti-pattern: a queue that grows unboundedly because the consumer is slower than the producer. Detect with lag monitoring (consumer group lag in Kafka, queue depth in SQS). Respond by scaling consumers or reducing producer rate.

## Ordering Guarantees

Total ordering across a distributed system is expensive. Kafka provides per-partition ordering — all messages for a given key go to the same partition, so related messages are ordered. For unrelated messages, there's no global ordering.

This affects system design: if you need strong ordering for account transactions, use a single partition per account (or equivalent sharding). If you need total global ordering, you'll need a more expensive consensus mechanism, which rarely scales.

## Designing a Notification System

A common interview question that exercises these concepts: "Design a notification system that sends email, SMS, and push notifications to millions of users based on platform events."

Key design points:
- Event bus (Kafka) receives platform events (purchase, comment, mention)
- Notification service subscribes, applies user preferences and deduplification
- Three fanout queues: email, SMS, push
- Workers per channel with at-least-once delivery and idempotency
- Retry with exponential backoff for failed deliveries
- Dead-letter queue for messages that exceed retry limit

Walk through the failure modes: what happens if the email worker is down? (Queue accumulates; SLA for email delivery is degraded but no events are lost.) What prevents duplicate notifications? (Idempotency key = event ID + user ID + channel, stored in Redis with TTL.)

This kind of structured walkthrough — topology, guarantees, failure modes, monitoring — is what senior engineers produce in system design interviews.
