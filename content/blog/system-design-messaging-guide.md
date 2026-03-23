---
title: "Message Queues and Event Streaming in System Design Interviews"
description: "Master messaging systems for system design interviews. Covers Kafka vs SQS vs RabbitMQ trade-offs, pub/sub patterns, event-driven architecture, and how messaging enables scalable distributed systems."
date: "2025-11-03"
category: "Technical Skills Guides"
---

# Message Queues and Event Streaming in System Design Interviews

Message queues and event streaming systems appear in almost every system design interview involving asynchronous processing, service decoupling, or high-throughput data pipelines. Understanding when to use messaging and which system to choose is a core competency for senior backend engineers.

## Why Messaging Systems Matter

Synchronous, request-response communication is simple but creates tight coupling:
- Service A must wait for Service B to respond
- If Service B is slow or unavailable, Service A is blocked
- Scaling Service B requires Service A to be aware of multiple instances

**Messaging solves this** by making communication asynchronous:
- Service A publishes a message and continues immediately
- Service B processes the message when ready
- Services scale independently
- The queue absorbs traffic spikes (producers write fast; consumers process at their pace)

## Message Queue vs. Event Streaming

These terms are often conflated but represent different models:

**Message Queue** (RabbitMQ, Amazon SQS, Google Pub/Sub):
- A message is consumed by one consumer (or one consumer group)
- Once consumed, the message is deleted
- "Work queue" model — distribute tasks across workers
- Good for: background jobs, task distribution, async RPC

**Event Streaming** (Apache Kafka, Amazon Kinesis):
- Events are retained in a log, potentially indefinitely
- Multiple consumers can read the same events independently (at different positions)
- Events are ordered within a partition
- Good for: event sourcing, audit logs, fan-out to multiple systems, replaying history

**Interview question**: "When would you use Kafka vs. SQS?"
- Multiple independent consumers needing the same data → Kafka (each consumer tracks its own offset)
- Simple task queue where one consumer processes each task → SQS (simpler, cheaper)
- Need to replay events → Kafka
- Need exactly-once delivery semantics → SQS with FIFO queues or Kafka with transactions

## Kafka Architecture

Kafka is the most commonly discussed messaging system in system design interviews. Key concepts:

**Topics and Partitions**: A topic is divided into partitions. Each partition is an ordered, immutable log. Messages within a partition are ordered; across partitions, there's no ordering guarantee.

**Producers**: Write messages to topics. Can choose which partition using a key (same key → same partition, enabling per-key ordering).

**Consumer Groups**: A group of consumers that collectively consume a topic. Each partition is assigned to exactly one consumer in the group. Scale out by adding consumers (up to the number of partitions).

**Brokers**: Kafka servers that store partitions. A cluster has multiple brokers; partitions are replicated across brokers for fault tolerance.

**Offsets**: Each message in a partition has an offset (sequential integer). Consumers commit their offset to track position. On restart, they resume from the committed offset.

```
Topic: orders
  Partition 0: [msg0, msg1, msg2, ...]
  Partition 1: [msg0, msg1, msg2, ...]
  Partition 2: [msg0, msg1, msg2, ...]

Consumer Group A: C0 reads Partition 0, C1 reads Partition 1, C2 reads Partition 2
Consumer Group B: B0 reads all partitions independently
```

**Throughput**: Kafka is designed for very high throughput — millions of messages/second on commodity hardware. The key: sequential disk writes and batch sending/receiving.

## Common Messaging Patterns

### Fan-Out

One producer, multiple independent consumers:
```
Order Service → Kafka topic "orders"
  → Inventory Service (reserves stock)
  → Notification Service (emails customer)
  → Analytics Service (records for reporting)
  → Fraud Detection Service (evaluates order)
```

All consumers read the same topic independently. In Kafka, each runs as its own consumer group.

### Work Queue (Competing Consumers)

Multiple workers share the load of processing tasks:
```
Upload Service → SQS "video-encoding-queue"
  → Worker 1 (processes some videos)
  → Worker 2 (processes other videos)
  → Worker 3 (processes other videos)
```

SQS's visibility timeout ensures each message is processed by exactly one worker.

### Event Sourcing

The system's state is derived from a sequence of events, stored in Kafka:
```
Kafka topic "account-events":
  [AccountOpened, MoneyDeposited, MoneyWithdrawn, ...]

Current balance = replay all events for an account
```

Enables complete audit history, replaying to rebuild projections, and temporal queries ("what was the balance on date X?").

### Dead Letter Queue (DLQ)

When a consumer fails to process a message after N retries, route it to a DLQ for inspection and manual handling. Essential for production systems to prevent poisoned messages from blocking queues.

## Delivery Semantics

**At-most-once**: Fire and forget. Messages may be lost but never duplicated. Fastest, acceptable for metrics/analytics where loss is tolerable.

**At-least-once**: Message is retried until acknowledged. May be delivered multiple times — consumers must be idempotent.

**Exactly-once**: Each message is processed exactly once. Hardest to achieve; requires distributed transactions or idempotency + deduplication. Kafka supports this with the transactional API.

**Interview guidance**: "I'd design for at-least-once delivery and make my consumers idempotent — it's simpler and more reliable than exactly-once semantics. Idempotency means processing the same message twice produces the same result (use a unique ID to detect duplicates)."

## Backpressure

When consumers can't keep up with producers:
- **Consumer-side**: Scale out consumers (more worker instances)
- **Producer-side**: Rate limit or reject incoming requests when queue depth exceeds a threshold
- **Partition scaling**: Add more Kafka partitions (allows more consumer instances)

In system design interviews, mentioning backpressure handling shows operational maturity — it's the difference between a system that handles load spikes gracefully and one that falls over.
