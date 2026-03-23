---
title: "Backend Scaling Interview Guide: Horizontal Scaling, Databases, and High Availability"
description: "System design and backend scaling interview prep — horizontal vs vertical scaling, database scaling patterns, load balancing, caching layers, and building high-availability services."
date: "2026-03-20"
category: "System Design"
---

# Backend Scaling Interview Guide: Horizontal Scaling, Databases, and High Availability

Backend scaling interviews test whether you can reason about systems under load — not just describe textbook patterns, but explain when each pattern applies, what tradeoffs it introduces, and how failures are handled. Senior engineers are expected to design systems that handle failure gracefully, scale predictably, and remain operable at scale. This guide walks through the core scaling concepts that appear in system design interviews.

## Horizontal vs. Vertical Scaling

The foundational question in any scaling discussion is whether to scale up (vertical) or scale out (horizontal).

**Vertical scaling** means adding more resources (CPU, RAM, faster disk) to a single machine. It is simple — no application changes required — but has hard limits set by available hardware and introduces a single point of failure. Vertical scaling is often the right first step; modern cloud instances can scale to hundreds of vCPUs and terabytes of RAM, which covers most workloads before requiring architectural changes.

**Horizontal scaling** means adding more machines and distributing load across them. It offers theoretically unlimited scale and eliminates single points of failure, but introduces complexity: your application must be stateless (or handle distributed state), requests must be routed across instances, and distributed systems introduce consistency and coordination challenges.

In interviews, resist the urge to immediately jump to horizontal scaling. The best answers acknowledge that scaling decisions depend on the workload type (CPU-bound, memory-bound, I/O-bound), the failure tolerance requirements, and the cost model. Most real-world systems use both: vertically scaled databases paired with horizontally scaled application tiers.

## Database Scaling Patterns

Databases are almost always the scaling bottleneck. Know these patterns and their tradeoffs:

**Read replicas** offload read traffic from the primary database. Writes go to the primary; reads go to replicas. This works well when your workload is read-heavy (social feeds, product catalogs). The key tradeoff is replication lag — replicas are eventually consistent with the primary. Applications must tolerate reading slightly stale data or route consistency-sensitive reads to the primary.

**Sharding** partitions data across multiple database instances, each owning a subset of the data. A user shard might route all data for users with IDs 1–1M to shard 1, and IDs 1M–2M to shard 2. Sharding eliminates the single-node write throughput ceiling but introduces operational complexity: cross-shard queries are expensive, resharding is painful, and joins across shard boundaries are often impossible. Use consistent hashing to distribute data more evenly and minimize resharding when adding shards.

**Federation** (also called functional partitioning) splits the database by domain rather than by row range. User data goes to one database, orders to another, product catalog to a third. This reduces write contention and allows each database to be sized for its workload. The tradeoff is that cross-domain queries require joining in application code.

## Caching Strategies

Caching is the highest-leverage performance optimization in most systems. Know the layers:

**CDN caching** serves static assets and cacheable API responses from edge nodes close to the user. Effective for global audiences, dramatically reduces origin server load. Cache invalidation at the CDN layer requires either URL versioning (for immutable assets) or explicit purge APIs.

**Application-level caching** with Redis or Memcached sits between your application and the database. Common patterns:
- **Cache-aside (lazy loading)**: Application checks cache on read. On miss, it loads from the database and writes to cache. Simple, but the first request after a cache miss pays the database latency.
- **Write-through**: Application writes to cache and database simultaneously. Cache is always warm, but every write pays the cache write overhead.
- **Write-behind (write-back)**: Application writes to cache; cache asynchronously flushes to the database. Highest write throughput but risks data loss if the cache fails before flushing.

In interviews, discuss cache eviction policies (LRU, LFU, TTL-based) and the thundering herd problem: when a cached item expires, many concurrent requests may simultaneously hit the database. Mitigations include probabilistic early expiration (PER), mutex locks to let one request populate the cache while others wait, and background refresh before expiration.

## Load Balancing Algorithms

Load balancers distribute traffic across backend instances. Knowing the algorithms and when to use each is table stakes in scaling interviews.

**Round Robin**: Requests distributed evenly in sequence. Works well when requests have similar cost. Fails when requests have highly variable cost — a slow request monopolizes a backend while others are idle.

**Least Connections**: Routes to the backend with the fewest active connections. Better than round robin for variable-cost requests.

**IP Hash**: Routes each client IP to a consistent backend. Useful for maintaining session affinity (sticky sessions) when session state is stored in-process. Note that this breaks if backends are added or removed — consistent hashing handles this more gracefully.

**Weighted Round Robin**: Assigns higher traffic proportion to more powerful instances. Used in mixed-capacity fleets or blue-green deployments where you want to gradually shift traffic.

Layer 4 load balancers (TCP/UDP) operate at the transport layer — high throughput, low overhead. Layer 7 load balancers operate at the HTTP level, enabling routing by URL path, host header, or request content — more flexible, slightly higher overhead.

## Queuing Systems and Asynchronous Processing

Synchronous request-response architectures break down when processing is slow or when you need to decouple producers from consumers. Message queues (Kafka, SQS, RabbitMQ) are the solution.

**Kafka** is a distributed log — it retains messages for a configurable period (default 7 days) and allows multiple consumer groups to read independently at different offsets. Use Kafka when you need high throughput, message replay, or event sourcing patterns. Topics are partitioned for parallelism; partition count determines maximum consumer parallelism.

**SQS** is a managed queue — messages are consumed and deleted. Simpler operationally than Kafka, but without replay capability. SQS FIFO queues provide exactly-once delivery and ordering within a message group; standard queues offer at-least-once delivery and higher throughput.

In interviews, discuss how queues improve availability: a downstream service outage no longer fails the caller — messages queue up and are processed when the service recovers. Discuss dead-letter queues for messages that fail processing repeatedly, and idempotency requirements (consumers must handle duplicate delivery safely).

## Stateless Services and High Availability

High availability requires eliminating single points of failure. The first requirement is stateless application servers — session state and user data must live outside the process, in the database or a distributed cache. Stateless services can be load balanced and replaced freely, enabling zero-downtime deployments and instant auto-scaling.

**Availability patterns**:
- **Active-passive failover**: One instance handles traffic; a standby takes over on failure. Simpler but wastes capacity and has a failover gap (seconds to minutes).
- **Active-active**: Multiple instances simultaneously handle traffic. No failover gap, no wasted capacity, but requires careful handling of split-brain scenarios in stateful components.

**Health checks** are the mechanism by which load balancers detect unhealthy instances. Shallow health checks (does the process respond to TCP?) catch crashes. Deep health checks (can the service reach the database?) catch degraded states. Design health check endpoints carefully — avoid making health checks themselves slow or expensive.

**Circuit breakers** prevent cascading failures when a downstream dependency degrades. If call failure rate exceeds a threshold, the circuit opens and requests fail fast without waiting for timeout. After a recovery period, a limited probe request tests whether the dependency has recovered. The pattern comes from electrical circuit breakers that prevent a fault from propagating through a system.

## Connection Pooling

Database connections are expensive to establish. Connection pooling maintains a pool of open connections that application threads reuse. Without pooling, each request opens and closes a database connection, adding latency and overwhelming the database with connection overhead.

Key parameters: pool size (max connections per application instance), connection timeout, idle timeout. Pool size should match your database's max connection limit divided by the number of application instances. PgBouncer and ProxySQL sit between application and database, providing pooling as an external service — essential when you have many application instances connecting to a single PostgreSQL or MySQL instance.

## Common Backend Scaling Interview Questions

- "Design a URL shortener that handles 100,000 writes and 10 million reads per day."
- "How would you scale a system from 1,000 to 10 million users?"
- "Explain the tradeoffs between read replicas and sharding."
- "How does a circuit breaker prevent cascading failures?"
- "Design a notification system that delivers to 50 million users within 5 minutes."

The strongest candidates tie every pattern to the failure mode it prevents and the tradeoff it introduces. Scaling decisions are not engineering puzzles — they are economic and operational choices with real consequences.
