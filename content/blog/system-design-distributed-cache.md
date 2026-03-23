---
title: "System Design: Distributed Cache — Memcached vs Redis, Consistent Hashing, and Eviction Policies"
description: "Deep dive into distributed cache system design: compare Memcached and Redis clusters, implement consistent hashing, choose eviction policies, and handle cache invalidation at scale."
date: "2026-03-20"
category: "System Design"
---

# System Design: Distributed Cache

Caching questions appear in virtually every senior-level system design interview. The ability to reason about cache topology, consistency tradeoffs, and failure modes separates engineers who "know Redis" from those who can design reliable distributed systems. This post walks through the full design discussion.

## Why Distributed Caches Exist

A single cache node can hold only so much data and serve only so many requests per second. When your system handles millions of daily active users, you need horizontal scale: multiple cache nodes working in coordination. This introduces three problems that don't exist with single-node caches:

1. **How do you decide which node stores a given key?**
2. **What happens when a node is added or removed?**
3. **How do you keep cached data consistent with your source of truth?**

## Memcached vs Redis: When to Use Each

Both are in-memory key-value stores, but their design philosophies differ fundamentally.

**Memcached** is purpose-built for simple caching:
- Multi-threaded: scales vertically across CPU cores better than Redis
- Purely key-value (string values only)
- No persistence — restart means empty cache
- Simpler memory management, often more memory-efficient for pure caching
- **Choose Memcached when:** you need a pure, high-throughput read cache, your values are simple blobs, and you want multi-threading without complexity

**Redis** is a data structure server that happens to be fast:
- Supports strings, lists, sets, sorted sets, hashes, streams, bitmaps, HyperLogLog
- Optional persistence (RDB snapshots, AOF log)
- Native pub/sub, Lua scripting, transactions (MULTI/EXEC)
- Redis Cluster for horizontal scaling; Redis Sentinel for HA
- **Choose Redis when:** you need rich data structures, pub/sub, persistence, or need atomic operations like rate limiting with INCR

**The honest answer in most interviews:** Redis is the default choice for 90% of use cases. Memcached only wins in very high-throughput, memory-constrained environments where multi-threading matters.

## Consistent Hashing

Naive partitioning (`key % N`) breaks catastrophically when N changes — every key remaps to a different node, causing a cache stampede. Consistent hashing solves this.

**The ring abstraction:**
1. Map nodes to positions on a circular hash ring (0 to 2^32)
2. To store a key, hash it and walk clockwise to the first node
3. When a node is added: only the keys between the new node and its predecessor need to move
4. When a node is removed: only that node's keys move to the next node

**Virtual nodes** solve uneven distribution: instead of one position per physical node, each node gets K virtual positions (K = 150–200 is common). This ensures keys distribute roughly evenly even with heterogeneous nodes.

```
Physical node A → Virtual nodes: A-1, A-2, ..., A-150
Physical node B → Virtual nodes: B-1, B-2, ..., B-150
```

**Implementation sketch:**
```python
import hashlib
from sortedcontainers import SortedList

class ConsistentHashRing:
    def __init__(self, nodes, replicas=150):
        self.replicas = replicas
        self.ring = SortedList(key=lambda x: x[0])
        for node in nodes:
            self.add_node(node)

    def _hash(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node):
        for i in range(self.replicas):
            h = self._hash(f"{node}:{i}")
            self.ring.add((h, node))

    def get_node(self, key):
        h = self._hash(key)
        # Find first node at or after hash position
        idx = self.ring.bisect_left((h,))
        if idx == len(self.ring):
            idx = 0
        return self.ring[idx][1]
```

## Cache Invalidation Strategies

Cache invalidation is famously one of the two hard problems in computer science. There are four main strategies:

**1. TTL (Time-to-Live)**
Set an expiration on every cached entry. Simple, always eventually consistent. Works when slight staleness is acceptable.

**2. Write-Through**
Write to cache and database simultaneously on every write. Cache is always consistent, but write latency increases. Used when reads are expensive and writes are infrequent.

**3. Write-Behind (Write-Back)**
Write to cache immediately, batch-write to database asynchronously. Lowest write latency, but risk of data loss on crash. Used for high-write workloads where durability is less critical.

**4. Cache-Aside (Lazy Loading)**
Application checks cache first. On miss, fetches from DB and populates cache. This is the most common pattern — cache only holds what's actually read.

```
Read path:
  if key in cache → return cache[key]
  else → value = db.get(key); cache[key] = value; return value

Write path:
  db.write(key, value)
  cache.delete(key)  # Invalidate, don't update (avoids race conditions)
```

Note: On writes, **delete** from cache rather than updating — updating creates a race condition where a slow in-flight read might overwrite the new value with stale data.

## Eviction Policies

When the cache is full, something must be evicted. The policy depends on your access patterns:

| Policy | When to Use | Complexity |
|--------|------------|------------|
| **LRU** (Least Recently Used) | General-purpose, temporal locality | O(1) with doubly linked list + hashmap |
| **LFU** (Least Frequently Used) | Hot items that should stay forever | O(1) but complex to implement |
| **FIFO** | Simple, no temporal locality | O(1) |
| **Random** | When access is truly random | O(1) |
| **TTL-based** | When freshness matters more than access pattern | O(log n) with min-heap |

Redis supports: `noeviction`, `allkeys-lru`, `allkeys-lfu`, `allkeys-random`, `volatile-lru`, `volatile-ttl`.

**LRU implementation** uses a doubly-linked list (most to least recent) and a hashmap (O(1) lookup):
- On get: move node to head → O(1)
- On put: add to head, evict tail if full → O(1)

## Handling Cache Failures

**Cache stampede (thundering herd):** When a popular key expires, many requests simultaneously miss and hammer the database. Solutions:
- **Probabilistic early expiration**: refresh slightly before expiry
- **Mutex/lock on miss**: only one request fetches from DB, others wait
- **Cache warming**: pre-populate before expiry

**Hot key problem:** One key receives disproportionate traffic, overwhelming a single shard. Solutions:
- **Key replication**: store the hot key on multiple shards with a suffix (`hot_key_1`, `hot_key_2`) and randomly select
- **Local in-process cache**: add an L1 in-process cache in front of Redis

## Interview Framework

When asked to design a distributed cache:
1. Clarify consistency requirements (eventually consistent vs strong)
2. Estimate data size and request rate to determine number of nodes
3. Choose partitioning strategy (consistent hashing)
4. Choose invalidation strategy based on write frequency
5. Choose eviction policy based on access patterns
6. Address failure scenarios: node failure, network partition, cache stampede

A strong answer treats the cache as part of a larger system — not just "add Redis" — but reasons about tradeoffs at each layer.

## Related Articles

- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Rate Limiter (Advanced)](/blog/system-design-rate-limiter-advanced)
- [System Design: Social Media Feed](/blog/system-design-social-media-feed)
- [System Design: Notification System](/blog/system-design-notification-system)
- [Cracking the System Design Interview](/blog/cracking-the-system-design-interview)
