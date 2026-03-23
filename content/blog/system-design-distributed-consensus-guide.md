---
title: "System Design: Distributed Consensus, Leader Election, and Raft"
description: "Deep dive into distributed consensus for system design interviews — Paxos intuition, Raft algorithm, leader election, log replication, practical implementations in etcd and CockroachDB."
date: "2026-03-20"
category: "System Design"
---

# System Design: Distributed Consensus, Leader Election, and Raft

Distributed consensus is one of the most intellectually demanding topics in system design interviews. It comes up when designing databases, coordination services, or any system that needs agreement across replicated state. Senior and staff-level candidates at companies like Google, Amazon, Meta, and Stripe are expected to discuss consensus at the mechanism level, not just wave their hands at "Raft."

## Why Consensus Is Hard

The fundamental problem: you have N servers that need to agree on a value (a log entry, a configuration change, which node is leader) in the presence of failures and network partitions.

**CAP Theorem framing:** Consensus systems choose consistency and partition tolerance (CP). When a partition occurs, a minority partition will refuse to serve writes rather than risk diverging from the majority. This means consensus is not appropriate for every use case — if you need availability during partitions, you want eventual consistency.

**FLP Impossibility:** A classic result (Fischer, Lynch, Paterson 1985) proves that no deterministic consensus algorithm can guarantee termination in an asynchronous system where even one node can fail. Practical systems work around this with randomized timeouts and bounded asynchrony assumptions.

## Paxos: The Conceptual Foundation

Paxos is the original consensus algorithm. You don't need to implement it, but understanding its structure helps:

**Two phases:**
1. **Prepare/Promise:** A proposer sends a prepare request with a sequence number n. Acceptors promise not to accept proposals with lower numbers and share any previously accepted value.
2. **Accept/Accepted:** If a proposer gets a majority of promises, it sends an accept request. If acceptors haven't promised to a higher number, they accept.

The insight: a value is "chosen" when a majority of acceptors have accepted it. Any future proposer learning the system state will see this value and propagate it. **Multi-Paxos** runs the algorithm repeatedly for a log, with an optimization to skip phase 1 once a leader is established.

Paxos's flaw: the original paper was famously hard to understand and implement correctly. It spawned years of confusion and eventually Raft.

## Raft: Understandability First

Raft was designed explicitly to be more understandable than Paxos. It decomposes consensus into three sub-problems:

### Leader Election

Nodes are in one of three states: **follower**, **candidate**, or **leader**.

1. Followers passively receive heartbeats from the leader.
2. If a follower doesn't hear from a leader within its **election timeout** (randomized 150-300ms), it becomes a candidate and starts an election.
3. A candidate votes for itself and sends `RequestVote` RPCs to all other nodes.
4. A node grants a vote if: (a) it hasn't voted in the current term, and (b) the candidate's log is at least as up-to-date as its own.
5. A candidate that gets votes from a majority becomes leader and begins sending heartbeats.

**Term numbers** serve as logical clocks. If a node sees a higher term, it immediately reverts to follower. This prevents stale leaders from causing confusion.

### Log Replication

Once a leader is elected:

1. Clients send commands to the leader.
2. The leader appends the command to its log and sends `AppendEntries` RPCs to all followers.
3. Once a majority of nodes have acknowledged the entry, the leader **commits** it and applies it to its state machine.
4. The leader notifies followers of the committed index; followers apply it.

**Log matching property:** If two logs contain an entry with the same index and term, all entries up to that point are identical. This is enforced by the consistency check in `AppendEntries` — the leader sends the preceding entry's index and term, and followers reject if they don't match.

### Safety Guarantees

Raft ensures that committed entries are never lost. A key mechanism: a candidate can only win an election if its log is at least as up-to-date as any majority. This means the new leader is guaranteed to have all committed entries.

## Practical Implementations

**etcd:** Kubernetes' backing store. Uses Raft for leader election and key-value replication. `etcd` is the canonical production Raft implementation — battle-tested at Google scale.

**CockroachDB / TiDB:** Use Raft per-range (each key range has its own Raft group). This provides per-shard consistency without a single global leader bottleneck.

**Consul:** Uses Raft for its service catalog and KV store. Important note: Consul's gossip layer for failure detection is separate from its Raft consensus.

**ZooKeeper (ZAB):** Predates Raft but solves the same problem with a slightly different protocol. Used by Kafka for its older controller design (KRaft now replaces it).

## Common Interview Questions

**Q: What happens if a leader is partitioned from the majority?**
The minority partition with the old leader stops accepting writes (it can't get majority acknowledgment). The majority partition elects a new leader after election timeout. When the partition heals, the old leader steps down because it will see the higher term. Any writes only acknowledged by the old leader (not committed) are rolled back.

**Q: Can you have two leaders simultaneously?**
Briefly, yes — between the time a leader becomes partitioned and the time it steps down. However, the old leader cannot commit entries without majority acknowledgment, so committed state remains consistent. This is "split-brain" as a transient state, not a permanent divergence.

**Q: How does Raft handle a log that's too large?**
Log compaction via **snapshots**. Once a log grows too large, a node captures a snapshot of the state machine at a particular index and discards log entries before that point. Late-joining nodes can receive the snapshot rather than replaying the full log.

**Q: When would you choose Raft/etcd vs a database for distributed coordination?**
Use etcd/ZooKeeper for: leader election, distributed locks, service discovery, configuration management — operations that need strong consistency with low write volume. Don't use them as primary data stores — they're optimized for consistency and coordination, not throughput.

## What Interviewers Want to See

You don't need to implement Raft in an interview. What distinguishes strong candidates:
- Understanding that consensus is the mechanism behind distributed databases, not a feature to bolt on
- Being able to explain why minority partitions must block (consistency guarantee)
- Knowing when NOT to use consensus (high-throughput writes, eventual consistency use cases)
- Practical awareness: "In practice I'd use etcd for leader election and let the database handle replication"
