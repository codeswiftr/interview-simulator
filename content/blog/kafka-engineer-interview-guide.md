---
title: "Kafka Engineer Interview: Event Streaming, Consumer Groups, and Distributed Logs"
description: "Master Kafka engineering interviews with deep coverage of topics, partitions, consumer groups, ISR, Kafka Streams, ksqlDB, and common event streaming patterns including CQRS and event sourcing."
date: "2026-03-20"
category: "Technical Skills"
---

# Kafka Engineer Interview: Event Streaming, Consumer Groups, and Distributed Logs

Apache Kafka has become the backbone of event-driven architectures at companies of every scale. Originally built at LinkedIn to handle activity streams, Kafka has evolved into a complete event streaming platform that underpins everything from payment processing and fraud detection to microservice communication and ML feature pipelines. Engineers who can design, operate, and reason about Kafka systems deeply are consistently in demand.

## Kafka Architecture: The Foundation

Kafka's architecture is built around a small number of well-defined concepts that compose into powerful patterns. Interviewers at companies using Kafka seriously will probe each of these precisely.

**Topics and Partitions**: A topic is a named, ordered, immutable log. Topics are divided into **partitions** — independent ordered logs that can be distributed across broker nodes. Partitions are the unit of parallelism. A topic with 12 partitions can be consumed by up to 12 consumers in a consumer group simultaneously. Choosing partition count is a critical design decision: too few limits throughput, too many increases coordinator overhead and rebalance time. The standard guidance is to provision 3-10x the expected peak consumer parallelism.

**Offsets**: Each message in a partition has a monotonically increasing integer offset. Consumers track their position by committing offsets — either automatically (risky) or manually (recommended for exactly-once semantics). The committed offset represents "I have processed everything up to here." Interviewers often ask about the difference between **at-least-once** (commit after processing — safest, may reprocess on failure) and **exactly-once** (Kafka transactions + idempotent producers — complex, necessary for financial data).

**Consumer Groups**: A consumer group is a set of consumers that collectively consume a topic. Kafka assigns each partition to exactly one consumer in the group at any time. This is the mechanism behind horizontal scaling: add consumers to a group to increase throughput, up to the partition count ceiling. Multiple consumer groups can independently consume the same topic at their own offsets — this fan-out pattern is how a single order event can simultaneously update inventory, trigger a confirmation email, and feed a fraud detection system.

**ISR (In-Sync Replicas)**: Each partition has a leader and zero or more replicas. The ISR is the set of replicas that are caught up with the leader. Producers configured with `acks=all` wait for all ISR members to acknowledge a write before returning success. The `min.insync.replicas` setting defines the minimum ISR size required for writes to succeed — typically 2 in production, preventing data loss when the leader fails. Interviewers test understanding of the availability vs. durability trade-off: `acks=0` (highest throughput, data loss possible), `acks=1` (leader acknowledges, replicas may lag), `acks=all` (durable, lower throughput).

## Common Interview Questions with Detailed Answers

**"A consumer is lagging significantly behind the producer. How do you diagnose and fix this?"**

First, measure consumer lag with `kafka-consumer-groups.sh --describe`. Determine whether lag is on all partitions (throughput problem) or specific ones (hot partition or stuck consumer). Check consumer metrics: is processing time per message increasing (downstream dependency issue), or is the consumer healthy but overwhelmed? Solutions in order of preference: increase consumer instances (if partitions allow), optimize processing logic, increase partition count (requires data migration), or move expensive processing to a separate topic with downstream consumers.

**"Explain exactly-once semantics in Kafka and when you'd use them."**

Exactly-once requires three components working together: **idempotent producers** (each producer has a producer ID; duplicate sends are deduplicated by the broker), **Kafka transactions** (atomic writes across multiple partitions using `beginTransaction`/`commitTransaction`), and **consumer isolation** (set `isolation.level=read_committed` to prevent reading uncommitted messages). Use exactly-once for financial transactions, inventory updates, and any domain where double-processing has business consequences. Avoid it where the overhead isn't justified — it adds latency and complexity.

**"How would you design a Kafka topic for a payment processing system?"**

Key decisions: partition key should be account ID or merchant ID (not random), ensuring all events for an entity go to the same partition and arrive in order. Partition count: estimate peak events per second, divide by single-consumer throughput. Retention: financial regulations typically require 7 years — Kafka's `retention.ms` (set to -1 for log compaction, or a large value for time-based retention). Replication factor: 3, `min.insync.replicas=2`. Schema: Avro with Schema Registry ensures backward-compatible evolution.

## Kafka Streams vs ksqlDB

Both are stream processing layers on top of Kafka, but they serve different audiences and use cases.

**Kafka Streams** is a Java/Scala library for building stream processing applications. It runs inside your application process — no separate cluster required. Key abstractions: `KStream` (unbounded stream of records), `KTable` (changelog stream with compaction semantics, representing current state), and `GlobalKTable` (replicated lookup table). Stateful operations (aggregations, joins) use **state stores** backed by RocksDB locally and a changelog topic for fault tolerance.

```java
KStream<String, Order> orders = builder.stream("orders");
KGroupedStream<String, Order> byCustomer = orders.groupBy(
    (key, order) -> order.getCustomerId()
);
KTable<String, Long> orderCounts = byCustomer.count();
orderCounts.toStream().to("customer-order-counts");
```

**ksqlDB** exposes a SQL interface for stream processing. It's appropriate for analytics, monitoring, and data transformation use cases where the SQL model fits. For complex stateful logic, custom join semantics, or tight integration with application code, Kafka Streams is more appropriate.

## Event Sourcing and CQRS with Kafka

Kafka naturally implements the **event log** that event sourcing requires. Events are the system of record; state is derived by replaying events from offset 0. Compacted topics enable efficient state reconstruction — Kafka retains only the latest value per key, so replaying a compacted topic reconstructs current state without processing the entire history.

**CQRS (Command Query Responsibility Segregation)** pairs naturally: commands produce events to Kafka, which consumers materialize into read-optimized views in Elasticsearch, PostgreSQL, or Redis. The command side is append-only and highly available; the read side is eventually consistent but tuned for query patterns.

## Confluent Cloud vs Self-Hosted

**Self-hosted Kafka** (on-premises or EC2/VMs) requires significant operational expertise: ZooKeeper management (or KRaft in modern versions), replication factor tuning, JVM heap tuning, disk I/O optimization, and rolling upgrades. It provides full control and is cost-effective at very high throughput where managed pricing becomes prohibitive.

**Confluent Cloud** (or AWS MSK, Google Cloud Pub/Sub Kafka-compatible) eliminates operational overhead in exchange for cost and some configuration flexibility. For organizations where Kafka is infrastructure rather than a core competency, managed Kafka is usually the right choice. Confluent adds Schema Registry, ksqlDB, and connectors as managed services.

**Interview question: "When would you choose self-hosted Kafka over Confluent Cloud?"**
Strong answers: when throughput exceeds the point where managed pricing is cost-prohibitive (typically >5TB/month ingested), when compliance requirements prohibit cloud-managed services, or when deep customization of broker configuration is required. Most other cases favor managed.

The strongest Kafka interview candidates combine theoretical depth with operational experience — they can explain ISR quorum calculation and also describe a real incident where a consumer group rebalance cascade caused a production outage and what they did to prevent recurrence.
