# System Design for the Impatient: High-Level Concepts You Must Know

*Don't have time to read "Designing Data-Intensive Applications"? Here is the cheat sheet you need to survive the interview.*

---

System design interviews are notorious for being open-ended, vague, and terrifying. One minute you're talking about load balancers, and the next you're being grilled on the specific consistency guarantees of Cassandra vs. DynamoDB.

For busy engineers, reading 500-page textbooks isn't always an option. You need the high-level concepts that give you 80% of the value for 20% of the effort.

Here is your **system design interview guide** for the impatient.

## 1. Vertical vs. Horizontal Scaling
This is the "Hello World" of system design.
*   **Vertical Scaling (Scale Up)**: Buy a bigger machine (more RAM, more CPU).
    *   *Pros*: Simple. No code changes.
    *   *Cons*: Expensive. Hard limit on how big you can go. Single point of failure.
*   **Horizontal Scaling (Scale Out)**: Buy more machines.
    *   *Pros*: Infinite scale (theoretically). Cheaper commodity hardware.
    *   *Cons*: Complex. Requires load balancing, data partitioning, and distributed coordination.

**Interview Tip**: Always start with vertical scaling for simplicity, then move to horizontal as requirements grow.

## 2. Load Balancers
The traffic cop of your system. It sits between the client and your servers.
*   **L4 (Transport Layer)**: Routes based on IP/Port. Fast, dumb.
*   **L7 (Application Layer)**: Routes based on HTTP headers, URLs, cookies. Smart, slower.
*   **Algorithms**: Round Robin (simple), Least Connections (smarter), Consistent Hashing (for caches).

## 3. Caching Strategies
"There are only two hard things in Computer Science: cache invalidation and naming things."
*   **Read-Through**: App asks cache. If miss, cache asks DB, updates itself, returns to App.
*   **Write-Through**: App writes to cache and DB simultaneously. Slow writes, fast reads.
*   **Write-Back**: App writes to cache only. Cache writes to DB later. Fast writes, risk of data loss.

**Interview Tip**: Use Redis or Memcached. Know when to use an LRU (Least Recently Used) eviction policy.

## 4. Database Sharding
When your database gets too big for one server, you split it up.
*   **Horizontal Partitioning (Sharding)**: Split rows by range (A-M, N-Z) or hash (User ID % 10).
*   **The Problem**: Joins across shards are expensive/impossible. Resharding is a nightmare.

## 5. CAP Theorem
You can only have 2 of 3:
1.  **Consistency**: Every read receives the most recent write or an error.
2.  **Availability**: Every request receives a (non-error) response, without the guarantee that it contains the most recent write.
3.  **Partition Tolerance**: The system continues to operate despite an arbitrary number of messages being dropped (or delayed) by the network between nodes.

**Reality Check**: In a distributed system, Partition Tolerance (P) is mandatory. So you really only choose between CP (Consistency) and AP (Availability).

## 6. Asynchronous Processing (Message Queues)
Don't make the user wait for heavy tasks.
*   **Pattern**: User request -> API -> Queue (Kafka/RabbitMQ) -> Worker.
*   **Use Cases**: Sending emails, processing videos, generating reports.
*   **Benefit**: Decouples components and handles traffic spikes (backpressure).

---

## The "Back-of-the-Envelope" Math
Memorize these powers of two to look like a wizard:
*   **10^3** ≈ 1 KB
*   **10^6** ≈ 1 MB
*   **10^9** ≈ 1 GB
*   **10^12** ≈ 1 TB

**Latency Numbers Every Engineer Should Know**:
*   L1 cache reference: 0.5 ns
*   Main memory reference: 100 ns
*   Read 1 MB sequentially from memory: 250,000 ns
*   Round trip within same datacenter: 500,000 ns
*   Disk seek: 10,000,000 ns (10 ms)
*   Send packet CA->Netherlands->CA: 150,000,000 ns (150 ms)

---

## Conclusion
You don't need to be a database architect to pass a system design interview. You need to know the building blocks and how to combine them to solve a specific problem.

**Want to practice these concepts in a low-pressure environment?**
Try our **[Interview Simulator](/dashboard)**. We have specific system design scenarios where you can practice explaining your architecture choices to an AI coach who gives you instant feedback on your trade-off analysis.
