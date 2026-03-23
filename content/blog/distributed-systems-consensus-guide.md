---
title: "Distributed Systems: Consensus Algorithms — Raft, Paxos, and Leader Election"
description: "A rigorous guide to distributed consensus for software engineers — covering why consensus is hard, how Raft works in detail, the intuition behind Paxos, leader election patterns, and how these algorithms appear in real systems like etcd, Kafka, and CockroachDB."
date: "2026-03-20"
category: "System Design"
---

# Distributed Systems: Consensus Algorithms — Raft, Paxos, and Leader Election

Consensus is the fundamental problem of distributed systems: how do multiple machines agree on a single value or sequence of values, even when some machines fail or messages are delayed? Algorithms that solve consensus underpin almost every distributed database, coordination service, and fault-tolerant system you've used. This guide explains how they actually work.

## Why Consensus Is Hard

Consider the naive approach: pick one node as the leader, route all writes through it. This works until the leader fails. Now: how do you pick a new leader? You need to agree on which node should be leader — which is itself a consensus problem.

The **FLP impossibility result** (Fischer, Lynch, Paterson, 1985) proved that in an asynchronous system where messages can be delayed arbitrarily, it is impossible to achieve consensus in the presence of even one faulty process. This isn't a practical limitation — it's a mathematical proof.

The practical escape: real systems aren't fully asynchronous. They use timeouts. If a node doesn't hear from the leader within N milliseconds, it assumes the leader is dead. This turns an impossible problem into a solvable one at the cost of occasionally being wrong (network partition looks like node failure).

The **CAP theorem** frames the trade-off: during a network partition, you must choose between:
- **Consistency** (all reads see the latest write) — CP systems
- **Availability** (every request gets a response) — AP systems

Consensus algorithms like Raft and Paxos choose consistency: during a partition, the minority partition becomes unavailable rather than risking inconsistency.

## Raft: Understandable Consensus

Raft was designed explicitly to be more understandable than Paxos. It decomposes consensus into three sub-problems:

1. **Leader election:** select one leader at a time
2. **Log replication:** the leader accepts log entries and replicates them to followers
3. **Safety:** a log entry committed to any server will never be overridden

### Terms and Leader Election

Time in Raft is divided into **terms** — monotonically increasing integers. Each term begins with an election. If a candidate wins, it serves as leader for the rest of the term. If the election fails (split vote), a new term starts.

**Node states:**
- **Follower:** passive, responds to leader and candidates
- **Candidate:** trying to become leader
- **Leader:** handles all client requests, replicates log to followers

**Election process:**
1. Follower's election timeout fires (random between 150–300ms) without hearing from leader
2. Follower increments its term, transitions to Candidate, votes for itself
3. Sends `RequestVote` RPCs to all other nodes
4. Nodes grant their vote if: (a) they haven't voted this term, and (b) the candidate's log is at least as up-to-date as their own
5. If candidate receives majority of votes → becomes Leader
6. Sends periodic heartbeats (`AppendEntries` with empty payload) to prevent new elections

**Why randomized timeouts?** To prevent split votes. If all followers had identical timeouts, they'd all become candidates simultaneously and split the vote repeatedly. Randomization means one node typically becomes a candidate first and wins before others time out.

### Log Replication

Once elected, the leader handles all client writes:

1. Client sends write request to leader
2. Leader appends entry to its log with the current term
3. Leader sends `AppendEntries` RPC to all followers (in parallel)
4. Once a majority acknowledge the append, the entry is **committed**
5. Leader applies the entry to its state machine, responds to client
6. Leader notifies followers of commit in the next heartbeat; followers apply to their state machines

**Commitment requires majority, not unanimity.** This means a cluster of 5 can tolerate 2 simultaneous failures (3 nodes must acknowledge).

**The key safety property:** A log entry is committed only when a majority of nodes have it. Any future leader will have at least one node with the committed entry (because any two majorities overlap by at least one node). The vote-granting rule (only vote for candidates with up-to-date logs) ensures the leader always has all committed entries.

### Log Consistency

What happens when a follower is behind or has conflicting entries (from a former leader that failed before committing)?

The leader tracks `nextIndex` for each follower. When `AppendEntries` fails due to log inconsistency, the leader decrements `nextIndex` and retries until it finds the point of agreement. Then it overwrites the follower's conflicting entries with its own.

**The guarantee:** Entries in the leader's log are never deleted. Followers' conflicting entries are overwritten. This is safe because uncommitted entries can be overwritten, and committed entries are guaranteed to be on the leader (via the election safety property).

## Paxos: The Classical Algorithm

Paxos (Leslie Lamport, 1989/2001) is the original consensus algorithm. It's known for being difficult to understand — Lamport's original paper "The Part-Time Parliament" used a fictional Greek parliament as metaphor and was rejected for years before being published.

### Single-Decree Paxos (Agreeing on One Value)

Two phases, two roles: **Proposers** propose values; **Acceptors** accept them. A value is chosen when a majority of acceptors have accepted it.

**Phase 1 — Prepare:**
1. Proposer chooses a unique proposal number `n` (higher than any it has seen)
2. Sends `Prepare(n)` to majority of acceptors
3. Acceptors respond with `Promise(n, prev_value)`: they promise not to accept proposals < n, and report the highest-numbered proposal they've already accepted (if any)

**Phase 2 — Accept:**
1. If proposer receives promises from majority:
   - If any acceptor returned a previously accepted value, use that value
   - Otherwise, use its own proposed value
2. Sends `Accept(n, value)` to the same majority
3. Acceptors accept (and notify learners) unless they've promised to a higher proposal number

**The insight:** By using the previously accepted value, Paxos ensures that once a value is chosen, all future proposals agree on it. This is the core of the protocol's safety.

**Multi-Paxos** extends this to agree on a sequence of values (a log) by electing a distinguished proposer (the leader) that can skip Phase 1 for subsequent proposals once it has established its authority.

## Raft vs Paxos

| Property | Raft | Paxos |
|----------|------|-------|
| Understandability | Designed to be easy to understand | Notoriously difficult |
| Leader election | Explicit term-based elections | No explicit leader (Multi-Paxos adds one) |
| Log gaps | No gaps (sequential) | Can have gaps (filled later) |
| Membership changes | Joint consensus or single-server changes | Complex to extend |
| Implementations | etcd, CockroachDB, TiKV, Consul | Chubby (Google), Spanner (Google) |

## Leader Election in Practice

Real systems implement variations on these algorithms:

**etcd** (Kubernetes' coordination store) uses Raft directly. Leader lease-based reads allow followers to serve reads without contacting the leader, improving read throughput while maintaining linearizability.

**Apache Kafka (KRaft mode)** replaced Zookeeper with an internal Raft implementation for controller election and metadata management.

**CockroachDB** uses Raft per-range (each 64MB range of data has its own Raft group). This allows fine-grained replication and failure isolation.

**ZooKeeper (ZAB protocol)** uses a Paxos-like protocol (Zookeeper Atomic Broadcast) that's optimized for the leader-as-primary-order use case. ZAB guarantees that all updates from a leader are delivered to followers in the order they were sent.

## Practical Implications for System Design Interviews

**"How does your distributed database handle node failures?"**
This is a consensus question. The answer involves: leader election (Raft/Paxos), write quorums (majority acknowledgment before commit), read consistency options (linearizable reads via leader, or stale reads from followers).

**"How do you ensure exactly-once semantics?"**
Idempotency keys + consensus-backed state. The consensus log becomes the source of truth for whether an operation has been applied.

**"What happens during a network partition?"**
CP systems (Raft/Paxos based): minority partition becomes unavailable (can't achieve quorum). AP systems (Dynamo-style): both partitions accept writes, conflict resolution on merge. The right choice depends on whether you can tolerate stale reads or unavailability.

**Key numbers to remember:**
- 3-node cluster: tolerates 1 failure (majority = 2)
- 5-node cluster: tolerates 2 failures (majority = 3)
- 7-node cluster: tolerates 3 failures (majority = 4)
- Adding nodes increases fault tolerance but increases write latency (must wait for more acknowledgments)

Consensus is the bedrock of distributed systems correctness. Engineers who understand it — not just the terminology but the actual mechanism — can reason about failure modes, consistency guarantees, and the real costs of distributed coordination in ways that profoundly influence system design decisions.
