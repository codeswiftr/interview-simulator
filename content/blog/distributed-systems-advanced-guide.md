---
title: "Distributed Systems Advanced Interview Guide: Consensus, CAP, and Fault Tolerance"
description: "Advanced distributed systems interview preparation — consensus algorithms (Raft, Paxos), CAP theorem in practice, distributed transactions, vector clocks, and fault tolerance patterns."
date: "2026-03-20"
category: "System Design"
---

# Distributed Systems Advanced Interview Guide: Consensus, CAP, and Fault Tolerance

Distributed systems questions separate senior engineers from the rest. Interviewers at top companies expect you to reason precisely about tradeoffs — not just recite definitions. This guide covers the advanced topics that come up most frequently at the senior and staff engineer level.

## CAP Theorem vs. PACELC

CAP theorem says a distributed system can guarantee at most two of: Consistency, Availability, and Partition Tolerance. Because network partitions are unavoidable in practice, the real choice is between CP (consistency during partitions) and AP (availability during partitions).

PACELC extends CAP to cover the non-partition case: when the network is healthy, you still choose between latency (L) and consistency (C). This is the more nuanced model interviewers prefer. For example, DynamoDB is PA/EL — it sacrifices consistency for availability during partitions, and sacrifices consistency for lower latency otherwise. HBase is PC/EC — it favors consistency in both scenarios.

When answering, avoid stating "we need CP" or "we need AP" without explaining the workload. A financial ledger demands CP; a social media feed tolerates AP. Frame your answer around business requirements, then derive the consistency model.

## Consensus Algorithms: Raft vs. Paxos

Consensus is the mechanism by which distributed nodes agree on a single value despite failures. It underlies replicated state machines, distributed databases, and leader election.

**Paxos** is the foundational algorithm. It operates in two phases: Prepare/Promise (leader proposes a ballot number, acceptors promise not to accept lower ballots) and Accept/Accepted (leader sends value, acceptors commit). Multi-Paxos optimizes repeated consensus by skipping phase one after stable leadership. Paxos is notoriously hard to implement correctly — log compaction, membership changes, and reconfiguration are all underspecified.

**Raft** was designed for understandability. It decomposes consensus into leader election, log replication, and safety. A leader is elected by majority vote with randomized timeouts. All writes go through the leader, which replicates entries to followers before committing. Raft's explicit leader model makes it easier to reason about and implement. etcd, CockroachDB, and TiKV all use Raft.

Interview-critical distinctions: Raft enforces that only candidates with up-to-date logs can win elections (preventing data loss). Paxos requires a separate mechanism for this. Raft also handles membership changes with joint consensus or single-server changes.

## Distributed Transactions: 2PC and Saga

**Two-Phase Commit (2PC)** achieves atomicity across nodes. A coordinator sends a Prepare to all participants; if all vote Yes, the coordinator sends Commit. 2PC is blocking — if the coordinator crashes after Prepare but before Commit, participants hold locks indefinitely. It also fails if a participant crashes between voting Yes and receiving Commit. 2PC is used in Google Spanner (via TrueTime to bound uncertainty) and traditional RDBMS clusters.

**Saga pattern** breaks a distributed transaction into a sequence of local transactions, each publishing an event. If any step fails, compensating transactions undo prior steps. Sagas are non-blocking and fit microservices well. The tradeoff is that intermediate states are visible (no isolation), and compensating logic is complex. Choreography-based sagas (event-driven) have no central coordinator but are harder to trace; orchestration-based sagas centralize coordination at the cost of a single point of control.

In interviews, choose 2PC when you need strict atomicity and can tolerate blocking (small participant sets, short transactions). Choose Saga for long-running business processes across services where blocking is unacceptable.

## Vector Clocks and Logical Time

Lamport clocks assign a scalar timestamp to events. They preserve causal ordering — if A happened before B, timestamp(A) < timestamp(B) — but the converse is not guaranteed. Two events with equal timestamps may be concurrent or causally related.

Vector clocks assign each node a counter in a vector. Node i increments its own counter on each event. On message receipt, the receiver takes the element-wise maximum. Vector clocks capture causality precisely: A happened before B if and only if A's vector is strictly less than B's vector in every position. Concurrent events have incomparable vectors — neither dominates the other.

Amazon's Dynamo uses vector clocks (or a variant called dotted version vectors) to detect conflicting writes. Clients must resolve conflicts (or last-write-wins is applied). In interviews, vector clocks arise when designing eventually consistent stores, conflict detection, and causal messaging systems.

## Eventual Consistency Patterns

Eventual consistency means all replicas converge to the same value given no new writes. Concrete patterns:

**Read-your-writes consistency**: After a write, subsequent reads by the same client see the updated value. Achieved by routing reads to the same replica or using monotonic read sessions.

**CRDT (Conflict-free Replicated Data Types)**: Data structures that merge automatically without coordination. G-counters, PN-counters, LWW-registers, and OR-Sets are common examples. Used in collaborative editors (Figma, Google Docs internals) and distributed counters.

**Anti-entropy and gossip**: Nodes periodically exchange state with random peers to propagate updates. Gossip achieves logarithmic convergence time with no central coordinator. Cassandra uses gossip for cluster membership and schema propagation.

## Distributed Locking

Distributed locks require a shared storage layer. Redis-based locking (Redlock) uses a majority quorum across independent Redis nodes to acquire a lock with a TTL. Controversy exists around Redlock's correctness under clock skew and GC pauses — Martin Kleppmann's critique and antirez's response are worth knowing for senior interviews.

ZooKeeper's ephemeral sequential nodes provide lock semantics: the node with the lowest sequence number holds the lock; others watch the next-lowest node. This avoids thundering herd. Chubby (Google's internal system) uses a similar model with distributed consensus underneath.

Key interview point: always pair distributed locks with fencing tokens (monotonically increasing IDs) to prevent stale lock holders from corrupting shared state after a GC pause or network partition.

## Common Advanced Distributed Systems Questions

- **How does Raft handle a leader that becomes isolated?** — It cannot commit new entries (requires majority), but the partition's majority will elect a new leader after a timeout. The old leader may see its term is stale when it reconnects and step down.
- **Design a distributed counter that supports millions of increments per second** — Shard the counter, use local aggregation with periodic flush, or use a CRDT PN-counter.
- **How do you detect and resolve write conflicts in a leaderless database?** — Vector clocks for detection; application-level resolution or LWW for resolution, with CRDT where possible.
- **What is split-brain and how do you prevent it?** — Two partitions each believe they are the leader. Prevented by requiring a strict majority quorum for any decision (quorum-based consensus).

Mastering these topics — with concrete examples, tradeoffs, and failure scenarios — signals the depth interviewers expect from senior distributed systems engineers.
