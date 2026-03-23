---
title: "Technical Interview Glossary: Terms Every Engineer Should Know"
description: "A comprehensive glossary of technical terms that appear in engineering interviews — ACID, CAP theorem, eventual consistency, idempotency, and more, with clear explanations and interview context."
category: "Technical Skills"
date: "2026-03-19"
tags: ["glossary", "technical terms", "system design", "databases", "distributed systems", "interview preparation"]
---

# Technical Interview Glossary: Terms Every Engineer Should Know

Engineering interviews expect you to use technical vocabulary precisely. Using a term incorrectly — or hesitating when an interviewer uses one — signals a gap in foundational knowledge. This glossary covers the terms that appear most frequently in system design and backend engineering interviews, with clear definitions and context for how each term comes up in practice.

---

## ACID

**What it means:** A set of properties that guarantee database transactions are processed reliably:

- **Atomicity:** A transaction either fully succeeds or fully fails — no partial updates
- **Consistency:** A transaction moves the database from one valid state to another
- **Isolation:** Concurrent transactions appear to execute serially — they don't interfere
- **Durability:** Committed transactions persist even if the system crashes

**In interviews:** ACID properties are why relational databases are the default for financial systems, inventory management, and anything where partial updates are dangerous. When you choose a NoSQL database, you often sacrifice some ACID guarantees. Be ready to explain what you're giving up and why it's acceptable for your use case.

---

## BASE

**What it means:** The relaxed consistency model used by many NoSQL databases:

- **Basically Available:** The system guarantees availability, even if some nodes are down
- **Soft state:** State may change over time even without new input (due to eventual consistency)
- **Eventually consistent:** Given no new updates, all replicas will converge to the same value

**In interviews:** BASE is the counterpart to ACID. When an interviewer asks "how does your NoSQL database handle consistency?" the answer involves explaining eventual consistency and where BASE trade-offs are acceptable (e.g., a "likes" counter being slightly stale is fine; a bank balance cannot be).

---

## CAP Theorem

**What it means:** In a distributed system, you can only guarantee two of the following three properties at the same time:

- **Consistency:** Every read receives the most recent write (or an error)
- **Availability:** Every request receives a response (not necessarily the most recent data)
- **Partition Tolerance:** The system continues operating even if network partitions occur

**Critical nuance:** Since network partitions are unavoidable in distributed systems, you're really choosing between **CP** (consistent but potentially unavailable during partitions) and **AP** (available but potentially returning stale data during partitions).

**In interviews:** CAP theorem is a framework for discussing trade-offs, not a rigid classification system. Real systems make different choices for different operations. Be careful not to claim you can have all three — interviewers will immediately challenge this.

---

## Eventual Consistency

**What it means:** A consistency model where updates to a distributed system will propagate to all nodes *eventually* — but not instantaneously. Reads immediately after a write may return stale data.

**In interviews:** Eventual consistency is acceptable when stale data doesn't cause incorrect behavior. Social media likes, DNS propagation, shopping cart item availability, and product review counts are all common examples. It's not acceptable for bank balances, inventory deductions where overselling is catastrophic, or any use case requiring a consistent view across concurrent reads and writes.

---

## Idempotency

**What it means:** An operation is idempotent if performing it multiple times has the same effect as performing it once. `GET /user/123` is idempotent; `POST /charges` (creating a payment) is not.

**Why it matters:** In distributed systems, network failures cause uncertainty — did the request succeed? If retrying a non-idempotent operation causes harm (double-charging a customer), you need to design for idempotency using idempotency keys.

**In interviews:** Idempotency is critical for payment systems, order processing, and any mutation that has real-world consequences. When designing an API, be ready to explain how you'd make non-idempotent operations safe to retry — typically by generating a unique idempotency key per logical operation and deduplicating on the server side.

---

## Sharding

**What it means:** Partitioning a database horizontally across multiple machines. Each shard holds a subset of the data. A shard key determines which shard stores each record.

**Common sharding strategies:**
- **Range-based:** Records with keys in a given range go to the same shard (easy range queries, risk of hot shards)
- **Hash-based:** Hash the shard key to distribute records uniformly (better balance, harder range queries)
- **Directory-based:** A lookup table maps keys to shards (flexible, but lookup table is a bottleneck)

**In interviews:** Sharding is a scaling solution of last resort for relational databases — it adds operational complexity and complicates queries across shards. Before proposing sharding, discuss read replicas, caching, and query optimization. When you do propose sharding, always address the choice of shard key and its trade-offs.

---

## Index (Database)

**What it means:** A data structure (typically a B-tree or hash map) that allows the database to locate rows matching a query condition without scanning every row in the table.

**Types to know:**
- **Primary index:** On the primary key, automatically maintained
- **Secondary index:** On non-primary columns; adds write overhead but enables fast lookups
- **Composite index:** Index on multiple columns; order matters (leftmost prefix rule)
- **Covering index:** Index that includes all columns a query needs, eliminating the need to fetch the actual row

**In interviews:** When asked about slow queries, index optimization is usually the first discussion point. Know when not to index: high-cardinality writes generate overhead, and over-indexing slows down write-heavy workloads.

---

## Consistent Hashing

**What it means:** A technique for distributing data across nodes such that adding or removing a node requires remapping only a small fraction of keys, rather than all keys (as in simple mod-based hashing).

**In interviews:** Consistent hashing appears when designing distributed caches (Memcached, Redis Cluster), load balancers, and distributed storage systems. The key advantage is minimal key remapping during node additions/removals — critical for systems where rebalancing causes latency spikes.

---

## Circuit Breaker

**What it means:** A pattern that prevents cascading failures by "opening" when downstream service failures exceed a threshold. Open circuit calls fail fast without attempting the downstream call. After a timeout, the circuit enters a half-open state to test recovery.

**In interviews:** Mention circuit breakers whenever designing microservices communication. The three states — closed, open, half-open — and their transitions are worth describing precisely.

---

## Rate Limiting

**What it means:** Controlling the rate at which a client can make requests to a service, to prevent abuse and protect system capacity.

**Algorithms to know:**
- **Token bucket:** Tokens accumulate at a fixed rate; each request consumes one token. Allows bursting up to bucket capacity.
- **Leaky bucket:** Requests are processed at a fixed rate regardless of arrival rate. No bursting.
- **Sliding window:** Track request count in a rolling time window. More accurate than fixed window but higher memory cost.
- **Fixed window:** Count requests in fixed time buckets (e.g., per minute). Simpler but allows 2x burst at window boundaries.

**In interviews:** Rate limiting is a common system design question. Know the algorithms, where to implement rate limiting (API gateway vs. application layer vs. edge), and storage requirements (counters per client, per endpoint).

---

## Replication

**What it means:** Maintaining copies of data on multiple nodes for availability and fault tolerance.

**Two main models:**
- **Synchronous:** The primary waits for acknowledgment from replicas before confirming the write to the client. Stronger consistency, higher latency.
- **Asynchronous:** The primary returns success immediately and replicates in the background. Lower latency, risk of data loss if the primary fails before replication completes.

**In interviews:** Replication affects your availability and durability guarantees. Multi-region replication introduces latency; synchronous cross-region replication is often impractical. Know the trade-offs for read replicas (lag, consistency) and failover (manual vs. automatic, RPO/RTO).

---

## RPO and RTO

**What it means:**
- **Recovery Point Objective (RPO):** Maximum acceptable data loss measured in time. "We can lose at most 1 hour of data."
- **Recovery Time Objective (RTO):** Maximum acceptable time to restore service after a failure. "We must be back online within 30 minutes."

**In interviews:** These metrics define backup and disaster recovery requirements. Lower RPO requires more frequent backups or synchronous replication; lower RTO requires hot standby infrastructure. Both have cost implications.

---

## Microservices vs. Monolith

**What it means:**
- **Monolith:** All application functionality in a single deployable unit. Simple to develop, test, and deploy early on; harder to scale and modify independently as the codebase grows.
- **Microservices:** Application decomposed into independently deployable services, each with its own database. Enables independent scaling and deployment; adds operational complexity (service discovery, distributed tracing, distributed transactions).

**In interviews:** Don't advocate for microservices by default. They add complexity that small teams often can't support. The strangler fig pattern is the standard recommendation for migrating a monolith to microservices incrementally.

---

## Latency vs. Throughput

**What it means:**
- **Latency:** Time to complete a single operation (milliseconds for a single request)
- **Throughput:** Number of operations completed per unit time (requests per second)

**Why they conflict:** Batching increases throughput but increases latency for individual items. Caching reduces latency but may reduce throughput for write-through patterns. Most optimization problems require choosing which to prioritize.

**In interviews:** Always clarify what you're optimizing for. "We have a high-read, low-latency requirement" and "we need to process 10 million events per day in batch" call for fundamentally different architectures.

---

Knowing these terms precisely — and being able to use them naturally in conversation — signals the kind of foundational depth that strong engineering interviews require. More importantly, understanding the *concepts* behind each term means you can reason through novel problems even when the exact term isn't familiar.
