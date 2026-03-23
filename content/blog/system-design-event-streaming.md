---
title: "System Design: Real-Time Event Streaming Platform"
description: "Design a real-time event streaming platform like Apache Kafka — partitioning, replication, consumer groups, exactly-once semantics, stream processing, and the production architecture behind high-throughput event pipelines."
date: "2026-03-20"
category: "System Design"
---

# System Design: Real-Time Event Streaming Platform

Event streaming platform design is a senior-level system design question that tests distributed systems depth. Unlike simpler queue-based designs, streaming platforms must handle millions of events per second with persistent storage, multiple consumer groups reading independently, and ordered processing guarantees. This guide covers the architecture that makes platforms like Kafka work.

## Core Requirements

For a streaming platform serving production workloads:
- **Throughput:** Millions of events per second across the cluster
- **Durability:** Events persisted to disk, replicated across nodes
- **Ordering:** Events in a partition are ordered; global order not guaranteed
- **Multiple consumers:** Many consumer groups can read independently; one consumer's progress doesn't affect others
- **Retention:** Events retained for configurable duration (hours to days to indefinitely)
- **Latency:** End-to-end publish-to-consume latency in milliseconds

## Partitioned Log: The Core Data Structure

The fundamental abstraction is a partitioned, ordered, immutable log. A topic is divided into N partitions. Each partition is a sequential, append-only log of messages. Messages within a partition are ordered by offset (monotonically increasing integer).

**Why partitions?** Parallelism. A single node can't handle millions of events/second, but 100 nodes each handling a partition can. Partition count determines the maximum parallelism of both producers and consumers.

**Why ordered per partition but not globally?** Global ordering across a distributed system requires coordination (Paxos/Raft) that limits throughput. Partition-level ordering is achievable with sequential writes per partition. Most application-level ordering requirements can be satisfied with partition-level ordering by routing related events to the same partition (same key → same partition).

## Partition Key and Assignment

Events are assigned to partitions based on a partition key (typically extracted from the message):

```
partition = hash(key) % num_partitions
```

This ensures messages with the same key always go to the same partition, providing ordering for that key. Without a key, round-robin assignment distributes load but provides no ordering.

**Hot partition problem:** If one key represents a disproportionate share of events (a single user generating 90% of traffic), that partition becomes a bottleneck. Solutions: add a random suffix to the key to spread across multiple partitions (gives up ordering), or pre-allocate more partitions with different hash ranges.

## Replication for Durability

Each partition has one leader and N-1 followers (replicas). Producers write to the leader; followers replicate from the leader. The replication factor (typically 3) determines fault tolerance: can survive loss of 2 replicas.

**In-Sync Replicas (ISR):** The set of replicas that are fully caught up with the leader. A message is considered committed when all ISR replicas have acknowledged it. If a replica falls behind, it's removed from ISR; when it catches up, it rejoins.

**`acks` configuration:**
- `acks=0`: Producer doesn't wait for acknowledgment. Fastest, may lose data.
- `acks=1`: Leader acknowledges. Data safe unless leader fails before follower replication.
- `acks=all`: All ISR replicas acknowledge. Strongest durability guarantee.

## Consumer Groups

A consumer group is a set of consumers that collectively read a topic. Each partition is assigned to exactly one consumer in a group. This enables parallel consumption — N consumers can process N partitions simultaneously.

Multiple consumer groups can read the same topic independently. Each group maintains its own offset per partition. Group A can be at offset 1000 while Group B is at offset 5000 on the same partition.

**Offset management:** Consumers periodically commit their current offset. On restart, the consumer reads from the last committed offset. The gap between the consumer's current position and the partition's latest offset is consumer lag — a key monitoring metric.

**Rebalancing:** When consumers join or leave a group, partitions are reassigned. During rebalancing, consumption pauses. Minimize rebalancing frequency by using static membership and avoiding consumer restarts.

## Exactly-Once Semantics

Achieving exactly-once delivery end-to-end requires coordination between producer, broker, and consumer:

**Producer idempotency:** Each producer is assigned a Producer ID and sequence number per partition. The broker deduplicates retried sends within a session.

**Transactions:** A producer can atomically write to multiple partitions and commit offsets within a single transaction. Consumers with `isolation.level=read_committed` only see committed messages.

**Implementation:** Producers wrap their message-sending and offset-commit operations in `begin_transaction` / `commit_transaction`. Consumers subscribe with `isolation.level=read_committed` to filter out uncommitted messages.

The overhead of exactly-once semantics is non-trivial — roughly 5-10% throughput reduction. Most production systems design for at-least-once delivery with idempotent consumers rather than the complexity of exactly-once.

## Storage Architecture

**Sequential writes:** The broker writes messages to partition log files sequentially (append-only). Sequential I/O is orders of magnitude faster than random I/O on both SSDs and HDDs.

**Page cache:** The OS page cache stores recently written data. Consumers reading recent data often read from page cache rather than disk, making reads nearly as fast as writes.

**Log segments:** Large partitions are divided into segments (e.g., 1GB each). This enables efficient cleanup — delete the oldest segment when retention expires, rather than compacting a single large file.

**Log compaction:** For "changelog" use cases (current state of each key), enable log compaction. The broker retains only the last message per key, cleaning up old values. Useful for maintaining database-like snapshots from a stream.

## Stream Processing

The streaming platform is a data substrate; stream processing is the compute layer on top. Apache Flink and Kafka Streams are common processing layers that:
- Consume events from topics
- Apply stateful or stateless transformations (filter, map, join, aggregate)
- Produce results to output topics

**Stateful processing challenges:** Time-windowed aggregations (count events per user per 5-minute window) require maintaining state across events. State must be fault-tolerant (persisted to state stores) and handle late-arriving events (watermarks).

## Monitoring

Key metrics: producer throughput (events/second per partition), consumer lag (per group, per partition), broker disk usage, ISR shrink rate (indicates replication issues), and end-to-end latency.

Alert on: consumer lag growing monotonically (consumer not keeping up), ISR count < replication factor (durability reduced), disk approaching capacity.
