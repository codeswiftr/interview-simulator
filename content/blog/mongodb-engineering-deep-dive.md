# MongoDB Engineering Deep Dive: Document Database at Global Scale

MongoDB powers some of the most demanding workloads on the planet — from financial transaction ledgers to real-time analytics pipelines serving billions of events per day. To succeed in a senior engineering interview, you need to understand not just how to write queries, but how the engine executes them, how replication maintains consistency, and how sharding distributes data under pressure. This deep dive covers the internals that separate candidates who "use MongoDB" from those who genuinely understand it.

## WiredTiger: The Storage Engine Underneath

Since MongoDB 3.2, WiredTiger has been the default storage engine, and understanding it is table stakes for senior interviews.

WiredTiger implements **Multi-Version Concurrency Control (MVCC)**. Rather than taking row-level locks for reads, each transaction sees a snapshot of the data at the moment the transaction began. Writers create new versions of documents; readers access the appropriate historical version without blocking. This means reads never block writes and writes never block reads — a critical property for high-throughput systems.

The checkpoint mechanism is equally important. WiredTiger writes a consistent snapshot to disk every 60 seconds by default (configurable via `storage.wiredTiger.engineConfig.checkpointSizeMB`). Between checkpoints, modified pages accumulate in the **write-ahead log (journal)**. On crash recovery, MongoDB replays the journal from the last checkpoint forward, ensuring durability without fsync on every write.

WiredTiger uses a **hybrid storage format** that borrows from both B-tree and LSM (Log-Structured Merge-tree) designs. The on-disk structure is a B-tree for point lookups and range scans, but in-memory updates are buffered in a SkipList before being reconciled to the B-tree pages. This amortizes the cost of random writes, similar to how an LSM tree works, while preserving the read performance characteristics of a B-tree. The result: write throughput that scales with available RAM (the larger the cache, the more reconciliation can be deferred).

Interview implication: when asked about write performance degradation under sustained load, the answer often traces back to cache pressure — WiredTiger evicts dirty pages to make room, and if eviction cannot keep pace with writes, the engine throttles ingestion. Tune `storage.wiredTiger.engineConfig.cacheSizeGB` to roughly 50% of available RAM (MongoDB's default), no higher.

## The Aggregation Pipeline: Execution and Optimization

The aggregation pipeline is MongoDB's primary tool for server-side data transformation. Each stage processes documents from the previous stage and emits documents to the next. What many engineers miss is that **stage ordering affects whether indexes can be used**.

Consider this pipeline:

```javascript
db.orders.aggregate([
  {
    $lookup: {
      from: "customers",
      localField: "customerId",
      foreignField: "_id",
      as: "customer"
    }
  },
  {
    $match: {
      "customer.tier": "enterprise",
      createdAt: { $gte: ISODate("2024-01-01") }
    }
  },
  {
    $group: {
      _id: "$customer.region",
      totalRevenue: { $sum: "$amount" }
    }
  }
])
```

Now examine what happens when you run `explain("executionStats")`:

```javascript
db.orders.aggregate([...], { explain: "executionStats" })
// Look for: queryPlanner.winningPlan.inputStage.stage
// A COLLSCAN here means no index was used — the match came too late
```

The problem: `$lookup` expands every document before the `$match` filters. MongoDB must join the entire `orders` collection with `customers` before filtering. The fix is to push selective `$match` stages **before** `$lookup`:

```javascript
db.orders.aggregate([
  {
    $match: {
      createdAt: { $gte: ISODate("2024-01-01") }
    }
  },
  {
    $lookup: { /* ... */ }
  },
  {
    $match: { "customer.tier": "enterprise" }
  },
  {
    $group: {
      _id: "$customer.region",
      totalRevenue: { $sum: "$amount" }
    }
  }
])
```

MongoDB's query planner will automatically push a `$match` to use an index if it appears at the start of the pipeline — this is called **pipeline optimization coalescence**. An index on `createdAt` now reduces the input to `$lookup` from millions of documents to thousands. Always run `explain` in staging before promoting aggregation pipelines to production.

## Replica Set Election: Raft-Inspired Consensus

MongoDB's replica set election algorithm is a Raft-inspired protocol — not pure Raft, but close enough that understanding Raft illuminates MongoDB's behavior.

A replica set requires a **majority of voting members to elect a primary**. With a 3-node set, 2 votes are needed. With 5 nodes, 3 votes. This is why even-numbered replica sets are discouraged without an arbiter: a 4-node set that loses 2 nodes cannot elect a primary, even though half the nodes remain available.

**Oplog replication** is the mechanism for propagating writes. The primary writes operations to its oplog (a capped collection in the `local` database). Secondaries tail the primary's oplog and replay operations in order. The oplog is **idempotent** — replaying the same operation twice produces the same result. This is why MongoDB transforms certain operations (like `$inc`) into their absolute equivalents in the oplog.

**Write concern semantics** control durability acknowledgment:

```javascript
db.transactions.insertOne(
  { accountId: "ACC-001", amount: 5000, type: "credit" },
  { writeConcern: { w: "majority", j: true, wtimeout: 5000 } }
)
```

`w: "majority"` means the write is acknowledged only after a majority of voting members have applied it. `j: true` means the primary must flush to journal before acknowledging. Together, these provide the strongest durability guarantee — the write survives primary failure. The tradeoff is latency: you pay network round-trip time to the nearest secondary.

## Sharding Architecture: Distributing Data at Scale

Sharding horizontally partitions data across multiple replica sets (shards). The **shard key** determines how documents are distributed. Choosing the wrong shard key is one of the most expensive mistakes in a MongoDB deployment — it cannot be changed without a full collection migration.

Good shard keys have three properties: high cardinality (many distinct values), low frequency (values are roughly evenly distributed), and non-monotonically increasing (to avoid "hotspot" shards). Using `_id` with ObjectId as a shard key is an anti-pattern because ObjectIds are timestamp-prefixed — all recent writes go to the same shard.

MongoDB divides shard key space into **chunks** (default 128MB each). The balancer migrates chunks between shards when one shard holds significantly more chunks than others. Chunk migrations cause temporary write amplification; monitor with `sh.status()` and the `config.migrations` collection.

**Scatter-gather queries** occur when a query cannot be routed to a specific shard because it doesn't include the shard key. MongoDB broadcasts the query to all shards and merges results at the `mongos` router. These queries do not scale with shard count — each additional shard adds latency. For read-heavy workloads on sharded clusters, always include the shard key in query predicates where possible.

## What Interviewers Are Really Testing

When a senior engineer asks about MongoDB in an interview, they are usually probing one of three things: your understanding of the consistency/availability tradeoff (MVCC, write concerns, election quorums), your ability to reason about query performance (aggregation pipeline optimization, index usage, explain output), or your operational judgment (shard key selection, replica set sizing, WiredTiger cache tuning).

The candidates who stand out are not those who list features — they are those who can say "I chose `w: majority` because we were processing financial transactions and could not afford to lose a write on primary failover, accepting the 10-15ms additional latency as a reasonable tradeoff." Operational judgment backed by mechanical understanding is what senior interviews reward.
