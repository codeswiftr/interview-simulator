---
title: "Distributed Systems Deep Dive: Interview Guide for Senior Engineers"
description: "Advanced distributed systems concepts for senior and staff engineer interviews: consensus algorithms (Raft, Paxos), consistency models, clock synchronization, partition tolerance tradeoffs, and how to discuss them in system design interviews."
date: "2026-03-19"
category: "Technical Skills Guides"
---

# Distributed Systems Deep Dive: Interview Guide for Senior Engineers

System design interviews at senior and staff level go beyond "add a load balancer." Interviewers at FAANG and well-engineered companies probe your mental model of distributed systems — what can go wrong, what the correctness guarantees actually mean, and how to make principled tradeoffs. This guide covers the concepts that separate strong senior candidates from average ones.

## The CAP Theorem: What It Actually Means

CAP is frequently cited and frequently misunderstood. The theorem: in a distributed system, during a network partition, you can choose either consistency (C) or availability (A), but not both.

What this means in practice:
- **CP systems** (favor consistency): During a partition, some nodes reject writes to prevent serving stale data. Examples: etcd, ZooKeeper, HBase. The system becomes unavailable rather than inconsistent.
- **AP systems** (favor availability): During a partition, nodes continue accepting reads and writes, potentially serving stale data. Examples: DynamoDB (with eventual consistency), Cassandra, CouchDB.

The common misconception: "pick two." You don't pick two — you always have Partition tolerance (network partitions happen; systems that ignore P only work on single machines). The real choice is C vs A during a partition.

PACELC extends CAP: even when there's no partition (E = else), there's a latency/consistency tradeoff. Systems that replicate synchronously are consistent but slower; systems that replicate asynchronously are faster but eventually consistent.

## Consistency Models: The Spectrum

Strong consistency (linearizability): every operation appears instantaneous, the system behaves as if there's one copy of the data. Example: reading after a successful write always returns that write. Expensive — requires coordination across replicas.

Sequential consistency: operations appear to execute in some sequential order consistent with each program's order. Weaker than linearizability — two clients may observe different orderings of concurrent operations, but each client's operations are ordered correctly.

Causal consistency: causally related operations are seen in order by all nodes. If Bob reads Alice's write and then writes himself, Carol must see Alice's write before Bob's write. Concurrent operations (no causal relationship) can be seen in any order.

Eventual consistency: replicas will eventually converge if writes stop. No guarantee of ordering, no bound on how long "eventually" takes. Most flexible, cheapest to implement.

**Interview application**: "Design a distributed key-value store" — the interviewer will ask about consistency. You should explain the spectrum and make a principled choice based on the use case: "For user session data, eventual consistency is acceptable since sessions have natural expiry and minor staleness is invisible to users. For inventory counts during checkout, we need stronger guarantees to prevent overselling."

## Consensus: Paxos and Raft

You don't need to implement Paxos or Raft in an interview, but you need to understand what problem they solve and why it's hard.

**The consensus problem**: multiple nodes must agree on a single value, even if some nodes crash or messages are lost. This is the foundation of leader election, distributed logs, and replicated state machines.

**Paxos**: the original consensus algorithm (Lamport, 1989). Notoriously difficult to understand and implement correctly. Two phases: prepare/promise and accept/commit. Real systems use Multi-Paxos (one leader, continuous log).

**Raft**: designed to be more understandable than Paxos. Decomposes into: leader election (whoever wins an election becomes leader, others follow), log replication (leader replicates log entries to followers, commits when a majority acknowledges), safety (at most one leader per term, committed entries are never lost). Used by: etcd, CockroachDB, TiKV, Consul.

**What to say in interviews**: "We need consensus for distributed coordination. Raft is more understandable and has good library support (etcd is a Raft implementation). The tradeoff: consensus is expensive — it requires a round-trip to a majority of nodes per write, which adds latency. For a coordination service like distributed locks, this is acceptable. For a high-write data store, we'd avoid consensus in the hot path."

## Vector Clocks and Causality

Physical clocks in distributed systems are unreliable — NTP provides millisecond accuracy, not nanosecond, and network latency is variable. Two events with close physical timestamps have no reliable ordering.

**Lamport timestamps**: a logical clock where each message carry's the sender's logical time, and receivers advance their clock to max(local, received) + 1. Establishes causal ordering: if A → B (A causes B), then timestamp(A) < timestamp(B). But the converse is not necessarily true.

**Vector clocks**: each node maintains a vector of counters, one per node. Increments its own counter on each event; merges vectors on message receipt. Allows detecting concurrent vs. causally related events: if neither V[a] ≤ V[b] nor V[b] ≤ V[a] in every position, the events are concurrent.

**Interview relevance**: "How would you detect conflicts in a distributed shopping cart?" The answer involves vector clocks to detect concurrent writes (user updated cart on web and mobile simultaneously), and a merge strategy to resolve them.

## Two-Phase Commit and Its Problems

Two-phase commit (2PC): coordinator sends "prepare" to all participants, waits for votes, then sends "commit" or "abort." Used for distributed transactions.

The problem: the coordinator is a single point of failure. If the coordinator crashes after sending prepare but before sending commit, participants are blocked — they've voted to commit but can't proceed without the coordinator's decision. 2PC is blocking.

Three-phase commit adds a pre-commit phase to reduce blocking, but doesn't eliminate it under all failure modes.

**Saga pattern**: an alternative to 2PC for distributed transactions. Each step has a compensating transaction (undo). If any step fails, execute the compensating transactions for previous successful steps. Not ACID (no isolation between steps), but doesn't require distributed locks.

## The Interview Approach

When a system design question involves distributed state, demonstrate the depth:
1. State the consistency requirement explicitly ("this is a write-heavy inventory system — I'll argue for...")
2. Identify the failure modes ("if the payment service is partitioned from the inventory service during checkout...")
3. Make a principled tradeoff ("I'll use optimistic locking with idempotent retries rather than 2PC to avoid blocking under coordinator failure")

The goal isn't to use the most sophisticated algorithm — it's to show you understand what problem each algorithm solves and why you'd choose it.
