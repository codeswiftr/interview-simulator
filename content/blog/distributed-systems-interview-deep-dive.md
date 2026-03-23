# Distributed Systems Interview Deep Dive 2024: Consensus, Consistency, and CAP

*Most engineers understand distributed systems well enough to build with them. Fewer can reason about them precisely enough to satisfy a principal engineer interviewer. This guide closes that gap.*

---

Distributed systems interviews are where the ceiling gets raised. A mid-level engineer can talk about eventual consistency. A senior engineer can explain why you would choose it over strong consistency for a specific workload. A staff engineer can explain the precise failure modes, articulate the consistency model formally, and reason about what happens when your assumptions break.

This guide is organized around the concepts that separate those tiers. We cover the theoretical foundations, the practical algorithms, and the interview question frameworks that demonstrate depth — not just familiarity.

---

## CAP Theorem: The Correct Understanding

The CAP theorem — formulated by Eric Brewer and formally proved by Gilbert and Lynch in 2002 — states that a distributed system can guarantee at most two of three properties simultaneously:

- **Consistency (C)**: Every read receives the most recent write or an error. All nodes see the same data at the same time.
- **Availability (A)**: Every request receives a non-error response, though it may not contain the most recent write.
- **Partition tolerance (P)**: The system continues operating despite network partitions (message loss between nodes).

The common interview mistake is treating CAP as a static design choice — "we chose AP" or "we chose CP." The correct framing is:

**Network partitions are not optional.** In any real distributed system, you will experience network partitions. The question is never "do I want partition tolerance?" but rather "when a partition occurs, which guarantee do I sacrifice — consistency or availability?"

This makes CAP more accurately a question of partition-handling strategy:

- **CP systems**: During a partition, refuse requests or return errors rather than risk serving stale data. Example: ZooKeeper, HBase, Spanner.
- **AP systems**: During a partition, continue serving requests with potentially stale data. Example: Cassandra (default tuning), CouchDB, DNS.

The interviewers who ask about CAP are not looking for you to recite the theorem. They want you to reason about what happens during a real partition in the system you are designing.

---

## PACELC: The More Useful Model

CAP only addresses behavior during partitions. Most of the time, your system is not partitioned. PACELC (Daniel Abadi, 2012) extends CAP to cover normal operation:

**If there is a Partition (P): trade-off between Availability (A) and Consistency (C). Else (E), even without partitions, trade-off between Latency (L) and Consistency (C).**

This is the model that reflects real system design decisions. Every time you replicate data for low-latency reads, you are making an ELC trade-off: lower latency, looser consistency. Every time you synchronously wait for all replicas before acknowledging a write, you are choosing higher consistency at the cost of latency.

| System | Partition behavior | Normal operation |
|--------|--------------------|-----------------|
| Dynamo/Cassandra | PA (available) | EL (low latency) |
| Spanner | PC (consistent) | EC (consistent) |
| CockroachDB | PC (consistent) | EC (consistent) |
| MongoDB (default) | PC (consistent) | EC (consistent) |
| Riak | PA (available) | EL (low latency) |

The PACELC model gives you a richer vocabulary for interview discussions. Instead of saying "we use eventual consistency," say: "This is an EL system — we sacrifice consistency for latency during normal operation and sacrifice consistency for availability during partitions. That trade-off is acceptable because the data is user preference settings, not financial records."

---

## Consistency Models: A Practical Taxonomy

Consistency models form a hierarchy from strongest to weakest. The stronger the model, the easier it is to reason about — and the higher the cost.

### Linearizability (Strong Consistency)

Linearizability means that operations appear to take effect atomically at some point between their invocation and completion. Every operation is as if it happened instantaneously at a single point in time, and all clients see all operations in the same order.

The practical guarantee: if a write completes and a subsequent read starts, the read will see the written value — even from a different client on a different node.

When to use: financial systems, reservation systems, distributed locks, anything where correctness depends on reading your own writes or where stale reads cause visible user harm.

Cost: requires coordination. Typically implemented with Paxos or Raft. Latency is bounded by the slowest replica in the quorum. A linearizable system cannot be available during a network partition (CAP).

### Sequential Consistency

Weaker than linearizability. All operations appear to execute in some sequential order, and the operations of each individual process appear in that sequence in the order specified by its program.

The key difference from linearizability: sequential consistency does not require that the sequential order respect real time. If Client A writes X=1 and then Client B reads X, sequential consistency allows Client B to still read X=0, as long as all clients see a consistent global ordering.

Practical use: multi-player game state (all players see the same sequence of events, but may lag real time), database transaction isolation.

### Causal Consistency

Operations that are causally related must be seen in the same order by all processes. Concurrent operations may be seen in different orders.

Causality is tracked through happens-before relationships: if event A could have influenced event B (A happened before B in the same process, or A's result was communicated to the process that did B), then A causally precedes B.

When to use: social networks (replies must appear after the post they reply to), collaborative editing (document edits that depend on each other must be ordered), messaging (replies after messages).

Cost: requires vector clocks or similar causal tracking metadata. More performant than linearizability but more complex than eventual consistency.

### Eventual Consistency

If no new updates are made to a given data item, eventually all accesses to that item will return the last updated value. There is no guarantee about when "eventually" is.

The weakest useful model. Requires conflict resolution strategies (last-write-wins, CRDTs, application-level merge).

When to use: DNS, shopping carts, user profiles, social media follower counts, any system where availability matters more than freshness and stale reads are not catastrophic.

The right answer is never "we use eventual consistency for simplicity." The right answer is "we use eventual consistency because this specific workload can tolerate this specific staleness window, and here is how we handle conflicts."

---

## Consensus Algorithms: Paxos and Raft

Consensus is the problem of getting a distributed system to agree on a single value despite failures. It underpins distributed transactions, replicated state machines, and leader election.

### Paxos: The Conceptual Foundation

Paxos (Lamport, 1989) is the foundational consensus algorithm. It guarantees safety (nodes never disagree on a committed value) and liveness under certain conditions (eventually reaches agreement if enough nodes are reachable).

Paxos has two phases:

**Phase 1 (Prepare/Promise)**: A proposer sends a Prepare(n) message with a proposal number n. Each acceptor, if it has not seen a higher proposal number, responds with a Promise to not accept proposals with lower numbers, and reports the highest-numbered proposal it has already accepted.

**Phase 2 (Accept/Accepted)**: If the proposer receives promises from a majority of acceptors, it sends Accept(n, v) where v is either the value from the highest-numbered previously accepted proposal (if any) or the proposer's own value. Acceptors that have not seen a higher proposal number accept and send Accepted.

A value is chosen when a majority of acceptors have accepted it.

In practice, Paxos is notoriously difficult to implement correctly. Multi-Paxos (extending single-decree Paxos to a log of values) requires additional mechanisms for leader election, log compaction, and membership changes. This complexity led to Raft.

### Raft: Leader Election and Log Replication

Raft (Ongaro and Ousterhout, 2014) was explicitly designed for understandability. It decomposes consensus into three problems: leader election, log replication, and safety.

**Terms**: Raft time is divided into terms numbered with consecutive integers. Each term begins with an election. If a candidate wins, it serves as leader for the rest of the term. If the election results in a split vote, the term ends with no leader and a new term begins. Terms act as logical clocks — they detect stale leaders.

**Leader Election**: Nodes start as followers. If a follower receives no communication from a leader within an election timeout (typically 150-300ms, randomized to avoid split votes), it transitions to candidate. A candidate:
1. Increments its current term
2. Votes for itself
3. Sends RequestVote RPCs to all other servers

A server grants a vote if: it has not voted in this term, and the candidate's log is at least as up-to-date as its own log. A candidate that receives votes from a majority of servers becomes leader and immediately sends heartbeats to all followers to prevent new elections.

**Log Replication**: The leader accepts client requests, appends them to its log as new entries, then issues AppendEntries RPCs in parallel to each follower. When a majority have confirmed the entry, it is committed. The leader applies the entry to its state machine and returns the result to the client.

The critical safety guarantee: a leader never overwrites or deletes entries in its log — it only appends. Log entries flow in one direction only, from leader to followers.

**Why term numbers matter**: If a node receives an RPC with a term number higher than its own, it immediately updates its term and reverts to follower state. If a node receives an RPC with a stale term number, it rejects the RPC. This prevents split-brain scenarios where an old leader continues to believe it is authoritative.

**Log matching property**: If two logs have an entry with the same index and term, they are identical in all entries up through that index. Raft enforces this with a consistency check: AppendEntries includes the index and term of the entry immediately preceding the new entries, and followers reject the RPC if their log does not match.

---

## Distributed Transactions

### Two-Phase Commit (2PC)

2PC is the classical protocol for atomic distributed transactions across multiple participants:

**Phase 1 (Prepare)**: The coordinator sends a Prepare message to all participants. Each participant prepares (writes to a WAL, acquires locks) and responds with either Yes (ready to commit) or No (abort).

**Phase 2 (Commit or Abort)**: If all participants voted Yes, the coordinator sends Commit. Otherwise, it sends Abort. Participants execute accordingly.

The fundamental problem with 2PC: the coordinator is a single point of failure. If the coordinator crashes after participants have voted Yes but before sending the Commit/Abort decision, participants are blocked indefinitely — they have locked resources and cannot proceed without the coordinator's decision. This is called the "blocking problem" of 2PC.

3PC (Three-Phase Commit) was designed to address this but introduces its own complexities under network partitions and is rarely used in practice.

### Saga Pattern

The Saga pattern is the dominant approach to distributed transactions in microservice architectures. Instead of a single ACID transaction, a saga is a sequence of local transactions where each transaction publishes a message or event to trigger the next step.

If a step fails, the saga executes compensating transactions to undo the preceding steps.

**Choreography-based sagas**: Each service listens for events and decides what to do. No central coordinator. The workflow emerges from the event chain. Simple for small workflows, difficult to debug and monitor at scale.

**Orchestration-based sagas**: A central saga orchestrator tells each participant what to do. The orchestrator tracks state and invokes compensating transactions on failure. Easier to reason about, but introduces a coordinator that must be fault-tolerant.

The key limitation of sagas: they do not provide isolation. Between the time the first local transaction commits and the last, intermediate states are visible to other operations. This is eventually consistent, not ACID.

### Outbox Pattern

The outbox pattern ensures reliable event publishing without distributed transactions. Instead of publishing to a message broker directly (which could fail after the database write or succeed while the database write fails), you write to an "outbox" table in the same database transaction as your business data.

A separate process reads from the outbox table and publishes to the message broker, then marks the record as published. This guarantees at-least-once delivery and atomicity without 2PC.

Common implementation: Debezium CDC (Change Data Capture) reading the outbox table and streaming to Kafka.

---

## Clock Synchronization and Ordering

In a distributed system, there is no global clock. This makes event ordering non-trivial.

### Lamport Clocks

Lamport timestamps assign a logical timestamp to each event, establishing a partial ordering that respects causality:

- Each process maintains a counter, initially 0.
- Before each event, increment the counter.
- When sending a message, include the current counter value.
- When receiving a message, set the counter to max(local, received) + 1.

Guarantee: if A causally precedes B, then timestamp(A) < timestamp(B). The converse is not true — a lower timestamp does not imply causal precedence. Lamport clocks cannot detect concurrent events.

### Vector Clocks

Vector clocks extend Lamport clocks to capture causality precisely. Each process maintains a vector of counters, one per process in the system.

- On event at process i: increment vector[i].
- When sending a message: include the current vector.
- When receiving at process j: set vector[k] = max(local[k], received[k]) for all k, then increment vector[j].

Two events A and B are concurrent if neither A's vector dominates B's nor B's vector dominates A's (neither is component-wise greater than the other).

Dynamo uses vector clocks to detect conflicts between concurrent writes. When a conflict is detected, it is surfaced to the client (or resolved by last-write-wins, depending on configuration).

### Hybrid Logical Clocks (HLC)

HLC combines physical time and logical time. The clock value has two components: a physical timestamp (from the system clock) and a logical counter. HLC advances with the physical clock when possible, and falls back to the logical counter when needed.

HLC provides a bounded difference from physical time, making it useful for systems where you want "close to real time" ordering without requiring synchronized clocks. CockroachDB uses HLC as its global clock.

Google Spanner uses TrueTime — GPS-synchronized atomic clocks with explicit uncertainty intervals — to implement external consistency (a stronger form of linearizability across globally distributed nodes).

---

## Failure Models

Understanding failure models prevents incorrect assumptions in your design:

**Crash-stop (fail-stop)**: A node either operates correctly or stops permanently. It does not send incorrect data. Simplest model, rarely accurate for real systems.

**Crash-recovery**: A node can crash and later recover, with persistent state intact. The realistic model for most databases and services. Requires write-ahead logging and recovery protocols.

**Network partition**: Links between nodes fail, but the nodes themselves continue operating. Raft and Paxos are designed for this failure model.

**Byzantine failure**: A node can behave arbitrarily — sending incorrect, inconsistent, or malicious data. The most severe failure model. BFT (Byzantine Fault Tolerant) consensus requires 3f+1 nodes to tolerate f Byzantine failures. Used in blockchain consensus but rare in traditional distributed systems due to cost.

In interviews, clarify which failure model your design assumes. A design for crash-recovery that silently breaks under Byzantine failures is a notable gap.

---

## Partition Handling Strategies

When a network partition occurs, your system must make a choice. The common strategies:

**Refuse writes, allow reads**: The system remains available for reads (which may be stale) but refuses writes until the partition heals. Common in CP databases.

**Allow writes to all partitions**: Each partition continues accepting writes. On healing, conflicts must be resolved. Common in AP databases (Cassandra, Riak). Conflict resolution may use last-write-wins (by timestamp), vector clock-based merge, or application-level semantics.

**Quorum-based decisions**: Reads and writes require acknowledgment from a majority of nodes. During a partition, the minority partition cannot process requests (no quorum). The majority partition continues normally. This is the approach Raft uses.

**Hinted handoff**: During a partition, a node that cannot reach the target node stores the write locally with a "hint" indicating the target. When the partition heals, the hint is replayed. Used by Cassandra and Dynamo for high availability.

---

## CRDTs: Conflict-Free Replicated Data Types

CRDTs are data structures that can be replicated across multiple nodes, updated independently and concurrently, and merged without conflicts — by design.

The key insight: CRDTs constrain the operations on a data structure so that concurrent operations always commute. The merge function is associative, commutative, and idempotent.

**Common CRDT types:**

**G-Counter (grow-only counter)**: Each node maintains its own counter. The global value is the sum. Increment is only allowed on the local counter. Merge takes the max of each node's counter. Used for: page view counts, like counts.

**PN-Counter**: Combines two G-Counters — one for increments, one for decrements. The global value is increment_total - decrement_total. Used for: inventory quantities, subscriber counts.

**G-Set (grow-only set)**: Items can only be added, never removed. Merge is set union. Used for: event logs, tag sets.

**OR-Set (Observed-Remove Set)**: Supports both add and remove. Each add tags the element with a unique identifier. A remove removes all tagged copies known at that time. Concurrent adds and removes are reconciled by the unique tags. Used for: collaborative document elements, shopping cart items.

**LWW-Register (Last-Write-Wins Register)**: A single value with a timestamp. Merge takes the value with the higher timestamp. The simplest CRDT, but discards concurrent writes. Used where last-write-wins semantics are acceptable.

**LWW-Element-Set**: Elements have add/remove timestamps. An element is in the set if its latest add timestamp is greater than its latest remove timestamp.

CRDTs are used in Riak (OR-Set, G-Counter), Redis (HyperLogLog is a CRDT-like structure), collaborative editors (Peritext, Automerge), and real-time sync systems.

---

## Interview Question Frameworks

### Design a Distributed Lock

**The question**: Design a distributed locking service. What guarantees should it provide?

**Framework for a strong answer**:

Start by clarifying requirements: Is this for mutual exclusion (exactly one holder at a time), or advisory locking? What is the expected lock hold duration? What happens if the lock holder crashes?

The core properties a distributed lock must provide: mutual exclusion (at most one holder at a time), deadlock prevention (locks must eventually be released), fault tolerance (if the holder crashes, the lock is released).

**Redis-based approach (Redlock)**: Each lock is a key with a TTL. Acquire by SET NX PX (set if not exists, with expiry). Release by checking the lock value matches a unique token before deleting (using a Lua script for atomicity). For fault tolerance, Redlock acquires the lock on a majority of N independent Redis nodes.

The controversy: Martin Kleppmann showed that Redlock does not provide strong guarantees under certain clock drift and GC pause scenarios. If a process holds a lock, experiences a GC pause longer than the TTL, and then resumes, it believes it holds the lock but another process has already acquired it. Solution: fencing tokens — the lock service issues a monotonically increasing token with each successful acquisition, and protected resources reject requests with older tokens.

**ZooKeeper-based approach**: Use ZooKeeper ephemeral sequential nodes. The node with the lowest sequence number holds the lock. Each node watches the node immediately before it, creating a lock queue without the thundering herd problem.

**Trade-offs to articulate**: Redis is faster but requires clock synchronization and has subtle failure modes. ZooKeeper provides stronger guarantees but is slower and adds operational complexity.

### Design a Distributed Cache with Consistency Guarantees

**Framework**: Start by clarifying the consistency requirement. Read-your-writes? Causal consistency? Eventual?

For read-your-writes with a cache-aside pattern: route all writes to the database and invalidate the cache. Read from cache; on a miss, read from database, populate cache. The problem: after a write, a cache read from a different node may still return the old value. Solution: stick sessions to a single cache node, or use a version number and reject cache entries older than the last write.

For causal consistency: use vector clocks or logical timestamps on cache entries. A read is only served from cache if the cache entry's timestamp is at least the write timestamp the client last observed.

For strong consistency: the cache is a read replica. All reads go through the primary database, or the cache uses synchronous replication with quorum reads. This eliminates most of the performance benefit of caching — articulate that trade-off explicitly.

Discuss cache invalidation strategies: time-to-live (simple, may serve stale data), event-driven invalidation (complex, requires reliable event delivery), write-through (write to cache and database together, consistent but slower writes).

### Linearizability vs. Serializability

**The common confusion**: These sound similar but describe different things.

**Serializability** is a property of transactions (database concept): the result of executing transactions concurrently is equivalent to executing them in some serial order. It says nothing about real time — the serial order does not need to correspond to when the transactions actually occurred.

**Linearizability** is a property of individual operations (distributed systems concept): each operation appears to take effect atomically at some point between its invocation and completion, and this point respects real time. All clients see a globally consistent view of all operations.

**Strict serializability** (also called external consistency) combines both: transactions are serializable, and the serial order corresponds to real time. This is the gold standard and what Spanner provides.

A database can be serializable without being linearizable: two transactions that appear to execute concurrently can be ordered arbitrarily in the serial history, even if one started after the other completed in real time.

In interviews: if someone asks for "the strongest consistency guarantee," the answer is linearizability for single operations and strict serializability for transactions. If they ask what PostgreSQL provides, the answer is serializability (with SERIALIZABLE isolation level) — strong, but not linearizable.

---

## Pulling It Together: How to Answer in an Interview

When a distributed systems question lands, use this structure:

1. **Clarify the failure model**: Crash-stop? Crash-recovery? Network partitions? Byzantine?
2. **State the consistency requirement**: What does "correct" behavior look like for this system?
3. **Apply PACELC**: During partitions, which do you sacrifice — availability or consistency? During normal operation, latency or consistency?
4. **Identify the coordination mechanism**: Consensus (Raft/Paxos), quorums, CRDTs, conflict resolution?
5. **Address failure scenarios explicitly**: What happens when nodes crash? When the network partitions? When the leader fails?

The engineers who get offers are not the ones with perfect knowledge — they are the ones who reason precisely, acknowledge uncertainty, and articulate trade-offs with the confidence that comes from genuinely understanding the material.

---

## Practice Distributed Systems Reasoning

Understanding these concepts on paper is not the same as being able to explain them clearly, precisely, and confidently in a 45-minute interview round.

**[Interview Simulator at app.codeswiftr.com](https://app.codeswiftr.com)** includes system design scenarios that specifically probe distributed systems depth — including follow-up questions on consistency models, failure handling, and consensus that mirror what principal engineers ask at FAANG and growth-stage companies.

Start with a free session and find out where your reasoning breaks down before an interview does.

**[Start Practicing Distributed Systems Questions Free](https://app.codeswiftr.com)**

---

*Related guides: [The Complete System Design Interview Guide](/blog/system-design-interview-guide) | [System Design for the Impatient](/blog/system-design-for-the-impatient) | [Staff and Principal Engineer Interview Guide](/blog/staff-principal-engineer-interview-guide)*
