---
title: "Distributed Systems Deep Dive: Consistency, Replication, and Partitioning"
description: "Master the core distributed systems concepts that senior engineering interviews test: CAP theorem, consistency models, replication strategies, and partitioning schemes with real examples."
date: "2026-03-20"
category: "System Design"
---

# Distributed Systems Deep Dive: Consistency, Replication, and Partitioning

Distributed systems questions separate senior engineers from mid-level candidates. Interviewers aren't looking for memorized definitions — they want to see you reason through trade-offs under realistic constraints. This guide covers the concepts that matter most, with the depth interviews expect.

## CAP Theorem: What It Actually Means in Practice

CAP theorem states that a distributed system can guarantee at most two of three properties: Consistency, Availability, and Partition Tolerance. The critical insight most candidates miss: **partition tolerance is not optional**. Network partitions happen in any real distributed system, so the real trade-off is always between consistency and availability during a partition.

Real systems apply this selectively. HBase and ZooKeeper choose CP — during a partition, they refuse writes rather than risk inconsistency. Cassandra and DynamoDB choose AP — they accept writes during partitions and reconcile later. Most production systems pick a default and then carve out exceptions per operation.

Interview answer pattern: "CAP forces a choice only during partitions. Our system would choose X because our business requirement is Y, and we'd mitigate Z by doing W."

## Consistency Models

This is where most candidates get vague. Be specific:

**Linearizability (strong consistency)**: Every operation appears instantaneous at some point between its invocation and completion. Reads always return the latest write. Example: Google Spanner uses TrueTime to achieve this globally. Cost: high latency, significant coordination overhead.

**Sequential consistency**: Operations appear to happen in some global order consistent with each process's program order, but not necessarily in real-time order. You may read stale data, but all nodes see operations in the same sequence.

**Eventual consistency**: Given no new updates, all replicas converge to the same value. DNS is the classic example. Most NoSQL databases default here. The key question interviewers probe: what happens during the window of inconsistency, and does your application tolerate it?

**Read-your-writes consistency**: You always see your own updates immediately, even if other clients see stale data. This is a common practical requirement for user-facing applications.

## Replication Strategies

**Primary-replica (leader-follower)**: One node accepts writes and propagates to replicas. PostgreSQL streaming replication works this way. Reads can go to replicas (accepting potential staleness) or to primary (guaranteed fresh). Failure scenario: if primary dies before propagating, you lose writes.

**Multi-primary (multi-leader)**: Multiple nodes accept writes. Useful for geo-distributed deployments where latency to a single primary is unacceptable. Complexity cost: you must resolve write conflicts. Last-write-wins, CRDTs, and application-level conflict resolution are the main approaches.

**Leaderless replication**: Any node accepts writes; consistency is achieved through quorums. Dynamo-style systems use W + R > N (write quorum + read quorum > total replicas) to guarantee overlap. With N=3, W=2, R=2: you'll always read at least one node that has the latest write.

## Partitioning (Sharding)

**Range partitioning**: Data divided by key ranges (A-M on shard 1, N-Z on shard 2). Simple to implement, supports range queries efficiently. Problem: hotspots when access patterns are skewed (all writes going to the shard containing the latest timestamp).

**Hash partitioning**: Apply a hash function to the key, assign to a shard by hash value. Distributes load evenly, eliminates range hotspots. Problem: range queries now require scatter-gather across all shards.

**Consistent hashing**: Maps both keys and nodes onto a ring. When a node is added or removed, only the adjacent keys migrate, minimizing reshuffling. Used by Cassandra, Amazon DynamoDB, and most CDNs. Virtual nodes (vnodes) address uneven load distribution on the ring.

## Interview Questions and How to Answer Them

**Q: How would you design a globally distributed database that handles 1M writes/second?**

Walk through: partitioning strategy (consistent hashing), replication topology (multi-primary across regions), consistency choice (eventual with read-your-writes for user data, strong for financial), conflict resolution approach, and monitoring for replication lag.

**Q: What happens in your system when a network partition occurs?**

Name your consistency model explicitly. Describe the failure scenario concretely. Explain your recovery process: how replicas reconcile, how clients detect staleness, what the user experience looks like during degraded state.

**Q: When would you choose Cassandra over PostgreSQL?**

Cassandra: high write throughput, multi-region active-active, schema flexibility, acceptable eventual consistency. PostgreSQL: complex queries, strong consistency requirements, ACID transactions, moderate scale.

## Tying It Together

The strongest distributed systems answers connect the technical choice to a business requirement. "We chose eventual consistency because our product shows recommendation feeds — a user seeing a slightly stale feed is invisible, but a 500ms latency spike from synchronous replication would tank our engagement metrics." That reasoning — not just reciting definitions — is what senior interviewers remember.
