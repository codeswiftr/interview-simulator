---
title: "Designing a Distributed File Storage System"
description: "A deep dive into the architecture of distributed file storage systems like HDFS, GFS, and S3—covering sharding, replication, consistency, and fault tolerance for senior system design interviews."
date: "2026-03-21"
category: "System Design"
---

# Designing a Distributed File Storage System

Distributed file storage is one of the foundational system design problems at senior-level interviews. Companies like Google, Amazon, Meta, and Microsoft have built these systems at planetary scale. Understanding the tradeoffs will set you apart.

## Core Requirements

Before drawing boxes, clarify requirements:

**Functional:**
- Upload, download, delete files of arbitrary size
- Support directories and metadata (owner, timestamps, permissions)
- Versioning and soft deletes

**Non-functional:**
- Durability: 11 nines (99.999999999%) — no data loss
- Availability: 99.99% uptime
- Latency: < 200ms for small files, streaming for large
- Scale: billions of files, petabytes of storage

## High-Level Architecture

A distributed file system has three planes:

1. **Metadata plane** — tracks where files live (namenode in HDFS, master in GFS)
2. **Data plane** — stores the actual bytes (datanodes, chunkservers)
3. **Client layer** — coordinates reads and writes

```
Client → Metadata Server → returns chunk locations
Client → Data Nodes (directly) → transfer bytes
```

This separation is key: metadata is small and cacheable; data is large and chunked.

## Chunking Strategy

Large files are split into fixed-size chunks (GFS uses 64MB). This enables:

- Parallel uploads across multiple nodes
- Partial reads without fetching entire files
- Easier replication at the chunk level

Each chunk has a globally unique ID. The metadata server maps `(file_id, chunk_index) → [chunk_server_1, chunk_server_2, chunk_server_3]`.

## Replication and Durability

Store each chunk on **3 replicas** across different fault domains:

- Replica 1: same rack as the writer (fast write)
- Replica 2: different rack, same datacenter (rack failure tolerance)
- Replica 3: different datacenter (regional failure tolerance)

Use a **chain replication** model: client writes to primary, primary forwards to secondary, secondary to tertiary. Only ACK after all three confirm. This gives strong consistency with bounded latency.

For erasure coding (what S3 uses), store k data shards + m parity shards. Recover from any m failures with less storage overhead (1.5x vs 3x for replication), but slower recovery time.

## Consistency Model

The hardest part. Three options:

**Strong consistency**: every read sees the latest write. Requires synchronous replication. Higher latency but simplest to reason about.

**Eventual consistency**: replicas converge over time. Lower latency, but clients may read stale data. Use vector clocks or timestamps to order writes.

**Session consistency**: a client always sees its own writes. Common in practice (read your writes). Use sticky sessions or client-side caching of write tokens.

For an interview, recommend **strong consistency for metadata** (to prevent split-brain) and **eventual consistency with read-your-writes for data**.

## Metadata Storage

The metadata server is the single point of truth. It must be:

- **Highly available**: use Raft or Paxos for consensus (3-node or 5-node cluster)
- **Fast**: keep the entire namespace in memory (HDFS namenode does this — 150 bytes per file object, 150M files = 22GB RAM)
- **Persistent**: write-ahead log + periodic checkpoints

For scale beyond a single cluster, use **namespace federation**: partition the directory tree across multiple namenode clusters by prefix.

## Write Path

```
1. Client requests upload, gets chunk assignments from metadata server
2. Metadata server creates chunk IDs, assigns 3 datanodes per chunk
3. Client splits file, writes chunk 1 to primary datanode
4. Primary streams to replica 2, replica 2 streams to replica 3
5. All three ACK → client ACKs metadata server → file visible
```

Atomic commit at step 5 prevents partial writes from being visible.

## Read Path

```
1. Client requests file, gets chunk map from metadata server
2. Client picks closest replica (via network topology or latency probe)
3. Client reads chunks in parallel across replicas
4. Client reassembles file in order
```

Caching chunk locations client-side avoids repeated metadata lookups.

## Garbage Collection

Deletes are soft. The metadata server marks a file as deleted and logs it. A background GC process reclaims chunk IDs after a configurable delay (default: 3 days). Datanodes heartbeat to the metadata server; unreferenced chunks are identified and freed.

This lag provides recoverability (accidental deletes) and avoids distributed coordination on the hot path.

## Fault Tolerance

- **Datanode failure**: detected via missed heartbeats (30s). Metadata server initiates re-replication from surviving replicas.
- **Metadata server failure**: Raft leader election, new leader continues from WAL.
- **Network partition**: metadata server uses quorum writes; datanodes buffer and replay.

## Interview Tips

When asked this in a real interview:

1. Start with requirements and capacity estimation (don't skip this)
2. Sketch the three-plane architecture first
3. Deep dive chunk replication and consistency model
4. Discuss failure scenarios explicitly
5. Compare with real systems (GFS, HDFS, S3) to show breadth

The interviewer wants to see that you understand the fundamental tradeoffs: consistency vs. availability, latency vs. durability, and storage efficiency vs. recovery speed.
