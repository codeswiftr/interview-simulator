---
title: "Distributed Systems Interview Patterns: Consistency, Availability, and Partition Tolerance"
description: "Distributed systems concepts for interviews — CAP theorem, consensus algorithms, distributed transactions, leader election, clock synchronization, and failure handling patterns."
date: "2026-03-20"
category: "System Design"
---

# Distributed Systems Interview Patterns: Consistency, Availability, and Partition Tolerance

Distributed systems questions appear in senior and staff engineering interviews at companies with non-trivial scale. The topics are theoretical foundations applied to practical design: when to sacrifice consistency for availability, how services agree on order of operations, and how to handle partial failures.

## CAP Theorem: The Right Mental Model

The CAP theorem states that a distributed data store can provide at most two of: Consistency (every read returns the most recent write), Availability (every request receives a response), and Partition tolerance (the system continues operating despite network partitions).

The key insight: partition tolerance is not optional for real distributed systems. Network partitions happen. So the real choice is: during a partition, do you prioritize consistency (CP) or availability (AP)?

**CP systems** (consistency + partition tolerance): When a partition occurs, some nodes refuse to serve requests to avoid returning stale data. Examples: ZooKeeper, etcd, HBase. Use when stale reads are unacceptable (financial systems, coordination services).

**AP systems** (availability + partition tolerance): When a partition occurs, nodes continue serving requests — some may return stale data. They reconcile after the partition heals. Examples: Cassandra, DynamoDB (with eventual consistency), CouchDB. Use when availability matters more than absolute consistency (shopping carts, social media feeds, recommendation systems).

## Consistency Models

The consistency spectrum from weakest to strongest:

**Eventual consistency:** Given enough time without updates, all replicas will converge to the same value. DNS is a classic example — a DNS update propagates globally over time.

**Read-your-writes consistency:** After a client writes, it always reads its own write. Common in session-scoped consistency: your own posts appear immediately; others' posts may lag.

**Monotonic read consistency:** Once a client reads value V, subsequent reads never return older values. Prevents the confusion of seeing a post, then not seeing it on refresh.

**Causal consistency:** Writes that are causally related are seen by all clients in the same order. "Reply to a post is always seen after the original post."

**Strong (linearizable) consistency:** The gold standard. Every operation appears to take effect instantaneously at some point between its invocation and completion. All clients see the same order of operations. Most expensive to implement — requires coordination.

## Consensus Algorithms

Consensus: getting distributed nodes to agree on a single value. Required for: leader election, atomic broadcast, distributed transactions.

**Paxos:** The original consensus algorithm. Complex to understand and implement correctly. Two phases: Prepare (leader proposes a round, gets quorum acknowledgment) and Accept (leader sends chosen value, gets quorum acceptance).

**Raft:** Designed to be more understandable than Paxos. Used by etcd, CockroachDB, TiKV. Three roles: leader (handles all writes), follower (replicates, votes), candidate (seeking leadership). Leadership is time-leased — if followers don't hear from the leader within the election timeout, they initiate an election. A candidate wins by getting a quorum of votes.

Key Raft property: a leader only wins election if its log is at least as up-to-date as the majority. This ensures elected leaders always have the most complete log.

## Vector Clocks and Causal Ordering

In distributed systems, wall clock time is unreliable across nodes (clock skew, NTP drift). Vector clocks provide a logical clock for determining causal ordering.

Each node maintains a counter. When sending a message, the node increments its counter and includes the full vector clock. The receiver updates its vector clock to the element-wise maximum.

If vector clock A ≥ vector clock B on all components and > on at least one: A "happened after" B (A causally follows B). If neither A ≥ B nor B ≥ A: concurrent writes — conflict must be resolved (last writer wins, application-specific merge).

DynamoDB uses vector clocks for conflict detection. Shopping carts with concurrent edits from mobile and desktop are a canonical vector clock use case.

## Distributed Transactions: 2PC and Sagas

**Two-Phase Commit (2PC):** A coordinator asks all participants to "prepare" (vote yes/no), then commits if all say yes. Atomic across participants. Problem: if the coordinator fails after participants vote yes but before the commit message, participants are blocked indefinitely — the classic 2PC blocking problem.

2PC is used by relational databases for distributed transactions but is generally avoided in microservices due to the coordinator dependency.

**Saga pattern:** Break a distributed transaction into local transactions. Each local transaction publishes an event; the next step reacts. On failure, compensating transactions reverse completed steps. See the architecture patterns guide for implementation detail.

## Failure Detection

In distributed systems, nodes can't distinguish between a slow node and a crashed node. Failure detection uses:

**Heartbeat:** Nodes send periodic heartbeats. If a heartbeat is missed for threshold T, the node is suspected failed. Threshold must balance false positives (too short — unnecessary failovers) and false negatives (too long — actual failures detected late).

**Phi Accrual Failure Detector:** Cassandra's approach. Instead of a binary failed/alive judgment, outputs a φ value representing the suspicion level. Applications set their own threshold based on acceptable false positive rate.

**SWIM (Scalable Weakly-consistent Infection-style Membership Protocol):** Used by Consul and Serf. Gossip-based failure detection that scales better than centralized heartbeat monitoring.

## Leader Election

Coordinating which node is the leader for a service:

**Bully algorithm:** Highest-ID node becomes leader. When a node suspects leader failure, it starts an election. Nodes with higher IDs respond, take over the election. Node with no higher-ID response wins.

**ZooKeeper/etcd ephemeral nodes:** Create an ephemeral node with a sequence number. The node with the lowest sequence number is the leader. When the leader dies, its ephemeral node is automatically deleted, triggering re-election.

Understanding these patterns demonstrates that you've thought about distributed systems failures, not just the happy path. That's what distinguishes senior distributed systems thinking.
