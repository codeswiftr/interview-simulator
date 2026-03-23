---
title: "Apache Kafka and Stream Processing Interview Guide"
description: "Technical interview preparation for Kafka and streaming: topic and partition design, consumer group semantics, exactly-once delivery, Kafka Streams vs Flink, and how streaming architecture shows up in senior backend and data engineering interviews."
date: "2026-03-19"
category: "Technical Skills Guides"
---

# Apache Kafka and Stream Processing Interview Guide

Kafka knowledge is expected for senior backend engineers, data engineers, and infrastructure engineers at any company that processes real-time data. The interview depth ranges from "explain what a consumer group is" (midlevel) to "design a globally distributed event bus with exactly-once semantics" (senior/staff). This guide covers the full range.

## Kafka Fundamentals: The Model

Kafka is a distributed, append-only log. Messages are written to topics, which are divided into partitions. Partitions are the unit of parallelism and ordering.

**Topics and partitions**: A topic is a logical feed. A partition is an ordered, immutable sequence of messages. Each partition is stored on one broker (with replication to others). Ordering is guaranteed within a partition, not across partitions. If you need globally ordered messages, use a single partition — but this limits throughput.

**Offsets**: Each message in a partition has a unique offset (monotonically increasing integer). Consumers track their position by committing offsets. If a consumer crashes and restarts, it resumes from the last committed offset.

**Producers**: Write to topics, choosing which partition (by key hash, round-robin, or custom logic). Key-based partitioning ensures all messages with the same key go to the same partition — important for maintaining order per entity (all events for `user_id=123` in order).

**Consumers and consumer groups**: A consumer group is a logical subscriber. Each partition is consumed by exactly one consumer in a group at a time. Adding consumers to a group increases parallelism up to the number of partitions. Multiple consumer groups can each read all messages independently — Kafka's multi-subscriber model.

## Interview Questions: Consumer Groups

"You have a Kafka topic with 6 partitions and a consumer group with 4 consumers. How are partitions assigned?"

Kafka assigns partitions to consumers via a partition assignment strategy (Range, RoundRobin, Sticky). With 6 partitions and 4 consumers: some consumers get 2 partitions, others get 1. No partition is assigned to more than one consumer in a group.

"What happens if you add a 7th consumer to this group?"

One consumer gets no partitions and sits idle. The maximum useful parallelism is limited by partition count. This is why partition count planning matters at topic creation time (repartitioning requires recreation).

"What happens if a consumer crashes during processing?"

Partition rebalance: Kafka detects the consumer as dead (via heartbeat timeout), triggers a rebalance, reassigns its partitions to surviving consumers. Consumers pick up from the last committed offset for those partitions.

## Delivery Semantics

**At-most-once**: Commit offset before processing. If consumer crashes after commit but before processing completes, the message is lost. Simple but may lose data.

**At-least-once**: Process first, then commit offset. If consumer crashes after processing but before commit, the message is reprocessed. Possible duplicates — downstream processing must be idempotent.

**Exactly-once**: Kafka 0.11+ supports exactly-once semantics (EOS) using transactions. Producer transactions ensure a batch of messages is either all committed or none. Combined with transactional consumers and idempotent producers, you get end-to-end exactly-once within the Kafka ecosystem. The tradeoff: higher latency (transactions add overhead). Use exactly-once for financial systems, avoid it for high-throughput low-importance event tracking.

## Kafka vs. Other Message Queues

Interview question: "When would you use Kafka vs. RabbitMQ vs. SQS?"

Kafka excels at: high-throughput event streams, replay (rewind to any offset and reprocess), multiple independent consumers, event sourcing / CQRS architectures, long retention (days to months of messages).

RabbitMQ / SQS excels at: task queues (work is consumed once and done), complex routing (exchange types, topic patterns in RabbitMQ), simpler operational model, lower latency for small volumes.

Kafka is the wrong choice for: low-volume task queues (operational overhead is high), request-reply patterns (Kafka is one-way), when you need complex routing without building it yourself.

## Kafka Streams and Stream Processing

Kafka Streams is a library (not a cluster) for stateful stream processing on Kafka topics. Transforms one or more input streams to output streams with operations like filter, map, join, aggregate, windowing.

**Windowing**: Aggregate over time windows. Tumbling windows (non-overlapping, fixed-size), hopping windows (overlapping, fixed-size), session windows (gaps between events define boundaries). "Count events per user per hour" = aggregate with 1-hour tumbling window, keyed by user_id.

**Joins in streams**: Stream-stream join (both sides are infinite streams), stream-table join (enrich stream with reference data from a table). Stream-stream join requires a time window (you can't join events that arrived days apart).

**Kafka Streams vs Apache Flink**: Kafka Streams is simpler (library, no cluster), suitable for per-service stateful processing. Flink is more powerful (its own cluster, complex event processing, SQL interface, exactly-once semantics across heterogeneous sources), suitable for complex analytical pipelines and large-scale stream processing.

## Producer Configuration That Matters

`acks` setting: `0` = fire-and-forget (fastest, no durability), `1` = leader ACK (durable to leader, not replicas), `all` or `-1` = all in-sync replicas ACK (strongest durability, more latency). For financial/critical data: `acks=all` + `min.insync.replicas=2`.

`linger.ms` and `batch.size`: Producers batch messages for efficiency. Higher `linger.ms` = more batching = higher throughput, higher latency. Tune based on throughput vs. latency requirements.

`compression.type`: Kafka supports Gzip, Snappy, LZ4, Zstd. Compression improves throughput at the cost of CPU. LZ4 for balanced; Zstd for best compression ratio. Almost always worth enabling for high-volume topics.

Understanding delivery semantics and consumer group mechanics is what separates engineers who have run Kafka in production from those who've only read the documentation.
