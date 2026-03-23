---
title: "System Design: Object Storage Service (S3 Clone)"
description: "Design an object storage service like Amazon S3 — metadata service, chunk storage, consistent hashing for distribution, multipart upload, versioning, and the architecture behind petabyte-scale storage."
date: "2026-03-20"
category: "System Design"
---

# System Design: Object Storage Service (S3 Clone)

Object storage design is a senior-level system design question that tests distributed systems fundamentals: data distribution, metadata management, consistency, and fault tolerance at scale. Designing an S3-like service requires thinking through petabyte-scale storage while maintaining availability and durability guarantees.

## Requirements Clarification

Clarify before designing:
- **Scale:** How many objects? Total storage? Read/write ratio?
- **Object sizes:** Small files (thumbnails, configs) vs. large files (videos, backups)?
- **Durability:** 99.999999999% (11 nines, like S3) or more relaxed?
- **Availability:** How important vs. consistency? (Object storage typically prioritizes availability)
- **Features:** Versioning? Lifecycle management? Access control? Multipart upload?

Reasonable baseline: 1 billion objects, 10 PB total storage, 10:1 read:write ratio, strong durability requirement, support for both small and large objects.

## High-Level Architecture

Two core components:

**Metadata service:** Stores object metadata — bucket, key, size, content type, version, creation time, and crucially, the location of the object's data chunks. This is a relational database problem (structured, transactional) but needs to scale horizontally.

**Data service:** Stores the actual bytes. Pure blob storage — no complex queries, just store and retrieve. Optimized for large sequential reads and writes.

This separation is key: metadata is read on every operation, must be queryable, and is relatively small. Object data is large but accessed by ID. Separating them allows each to be scaled independently.

## Metadata Design

Each object record contains:
```
bucket_id | object_key | version_id | size_bytes | content_type |
created_at | etag (MD5) | storage_class | chunk_ids | deleted
```

The `chunk_ids` field references the actual data location. For small objects (<1MB), the data may be stored inline or in a single chunk. For large objects, stored as multiple chunks.

**Metadata storage choices:**
- PostgreSQL with sharding by `(bucket_id, object_key)` — familiar, ACID, but sharding adds complexity
- Cassandra — designed for this access pattern, wide rows, consistent hashing for distribution
- DynamoDB-style: bucket+key as partition key, version as sort key

For 1 billion objects with ~200 bytes of metadata each: ~200GB of metadata — fits in a well-provisioned PostgreSQL cluster with read replicas. Scale to 100B objects: sharded Cassandra.

## Data Storage: Chunk Distribution

Large objects are split into chunks (typically 5MB-1GB). Chunks are distributed across storage nodes using consistent hashing.

**Consistent hashing:** Map chunk IDs (hashed) to a virtual ring. Storage nodes own segments of the ring. This enables adding/removing nodes with minimal re-balancing — only the chunks adjacent to the changed node need to move.

**Replication:** Each chunk is stored on 3 nodes (configurable). The replication factor provides durability: even if 2 nodes fail simultaneously, data is preserved. S3's 11 nines durability comes from cross-region replication and erasure coding.

**Erasure coding:** More storage-efficient than 3× replication. A (k, m) erasure code splits data into k data chunks and m parity chunks. Any k of the k+m chunks can reconstruct the original. For k=6, m=3: can survive loss of any 3 chunks using only 1.5× storage overhead vs. 3× for replication.

## Multipart Upload

For large files (>5GB), multipart upload allows:
1. Initiate upload → server returns `upload_id`
2. Upload parts in parallel (each part is a chunk, minimum 5MB)
3. Complete upload → server assembles metadata

```
POST /buckets/{b}/objects/{key}?uploads → {upload_id}
PUT /buckets/{b}/objects/{key}?uploadId={id}&partNumber={n} → {etag}
POST /buckets/{b}/objects/{key}?uploadId={id} (with part list) → 200 OK
```

Each part is stored independently with its own etag. The complete operation is atomic from the client's perspective — the object appears either complete or not at all.

**Incomplete multipart uploads:** Must be cleaned up (lifecycle rule). Otherwise they accumulate as orphaned chunks consuming storage.

## Read Path

```
Client → API Gateway → Metadata Service (look up chunk locations)
                              ↓
                       Data Service (fetch chunks from storage nodes)
                              ↓
                       Stream assembled response to client
```

For range reads (streaming byte ranges): fetch only the chunks containing the requested byte range. Critical for video streaming (seeking) and large file partial processing.

## Write Path

```
Client → API Gateway → Metadata Service (create pending object record)
                              ↓
                       Data Service (distribute chunks to storage nodes)
                              ↓
                       Metadata Service (mark object as committed, store chunk IDs)
```

The two-phase write (pending → committed) ensures that a failed write doesn't leave a partially-visible object. Clients only see the object after all chunks are durably written.

## Versioning

Versioning stores all versions of an object, not just the latest. Each version has a unique `version_id`. Listing the object returns the latest version; listing with version IDs returns all versions.

Deletes are "soft deletes" when versioning is enabled: a delete marker is created rather than the data being removed. The delete marker becomes the current version; previous versions remain accessible.

Storage impact: versioning can multiply storage costs if objects are updated frequently. Lifecycle rules (expire non-current versions after N days) control costs.

## Consistency Model

S3 provides strong read-after-write consistency (since 2020). Before that, it was eventually consistent for overwrite PUTs and DELETEs.

Strong consistency implementation: route all reads and writes for an object through the same metadata shard. The metadata record is the consistency point — once the write is committed to metadata, subsequent reads from any instance see the new version.

## Design Trade-offs to Articulate

- **Replication vs. erasure coding:** Replication simpler to implement; erasure coding more storage-efficient but computationally expensive to repair
- **Single namespace vs. hierarchical:** S3 uses a flat namespace with "/" as a pseudo-hierarchy; true hierarchical namespaces simplify listing but add write-path complexity
- **Synchronous vs. asynchronous replication:** Synchronous is durable but slow; async is fast but risks data loss on failure

Object storage is one of the most interesting system design questions because it combines all distributed systems concepts — consistent hashing, replication, eventual consistency, and scale — in a concrete, well-understood system.
