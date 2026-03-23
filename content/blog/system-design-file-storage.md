---
title: "System Design: Build a File Storage System Like Google Drive or Dropbox"
description: "A comprehensive system design walkthrough for a cloud file storage service — file chunking, deduplication, metadata service, delta sync, conflict resolution, and versioning."
date: "2026-03-20"
category: "System Design"
---

Designing a file storage system like Google Drive or Dropbox is one of the most instructive system design interview problems. It touches nearly every distributed systems concept that matters: large file handling, synchronization, consistency, scalability, and storage economics. Let's work through a complete design.

## Clarifying Requirements

Before diving in, always clarify scope. For this design, assume:

- **Scale:** 500 million users, 1 billion files, average file size 1MB, peak 10 million concurrent users
- **Core features:** Upload, download, sync across devices, file versioning, sharing
- **Non-functional:** High durability (99.999%), eventual consistency acceptable for sync, strong consistency for metadata

## High-Level Architecture

The system has four major components:

1. **Client application** (desktop/mobile sync agent)
2. **Upload/download service** (handles actual file data)
3. **Metadata service** (tracks files, versions, sharing)
4. **Notification service** (real-time sync triggers)

## File Chunking

Uploading large files as a single unit is fragile — a network interruption means restarting from scratch, and full-file uploads are wasteful when only part of a file changes.

**Chunk files into 4-8MB blocks.** Each chunk is:
- Uploaded independently, enabling resumable uploads
- Identified by its content hash (SHA-256)
- Stored only once if multiple files share identical chunks (deduplication)

The client splits the file, uploads chunks in parallel, and sends a manifest (ordered list of chunk hashes) to the metadata service. Download is the reverse: fetch the manifest, download chunks in parallel, reassemble.

```
File: quarterly_report.docx (32MB)
Chunks: [chunk_a3f2..., chunk_b847..., chunk_c129..., chunk_d45e...]
```

**Chunking benefits:** Parallel upload/download, resumable transfers, efficient delta sync, storage deduplication.

## Deduplication

Content-addressable storage (CAS) means two files with identical content at the block level share storage. Before uploading a chunk, the client sends its hash to the server. If the hash already exists in the chunk store, the upload is skipped — the server just adds a reference.

**Block-level dedup example:** If 1,000 users upload the same 5MB image, the data is stored once. References are cheap; re-uploading 5MB per user is expensive.

At Dropbox's scale, deduplication reportedly reduces storage costs by 30-40%.

## Metadata Service

The metadata service is the system's source of truth. It stores:

- **File records:** name, owner, size, creation time, modification time, content type
- **Chunk manifest:** ordered list of chunk hashes for each file version
- **Version history:** each save operation creates a new version record
- **Sharing permissions:** ACL (access control list) per file/folder

**Database choice:** A relational database (PostgreSQL) works well for metadata given its transactional semantics and rich query support. At extreme scale, shard by user ID.

**Schema sketch:**
```
files(id, owner_id, name, parent_folder_id, current_version_id, created_at)
versions(id, file_id, chunk_manifest, size, created_at, creator_id)
chunks(hash, storage_path, size, ref_count)
sharing(file_id, user_id, permission_level)
```

## Delta Sync

When a file changes, you should not re-upload the entire file. Delta sync transfers only the modified chunks.

The client maintains a local manifest of chunk hashes. On change detection:
1. Recompute chunk hashes for the modified file
2. Compare with stored manifest
3. Upload only chunks with changed hashes
4. Update the manifest with new chunk hashes

For a 100MB document where the user edits one paragraph, only the 4-8MB chunk containing that paragraph is re-uploaded. This is the core efficiency that makes desktop sync clients practical.

## Conflict Resolution

When two devices edit the same file simultaneously without syncing, a conflict occurs. The system must decide: overwrite, create a conflict copy, or merge.

**Common strategies:**
- **Last-write-wins (LWW):** Simple but risks data loss. Acceptable for most consumer use cases.
- **Conflict copy:** Rename the conflicting version as "filename (Conflicted Copy - 2026-03-20).docx" and surface both to the user. This is Dropbox's default behavior.
- **Three-way merge:** Used by Google Docs for collaborative editing. Requires tracking a common ancestor and applying diffs from both branches.

For file-granularity systems (not real-time collaborative editors), conflict copies are the pragmatic choice. Merge strategies require application-layer awareness of file format.

## Versioning

Every file modification creates a new version. Design decisions:

**Version retention:** Keep unlimited versions for 30 days, then prune to daily snapshots for 90 days. Users on paid plans get extended version history.

**Storage efficiency:** Versions share chunks. If only 1 of 8 chunks changes between versions, 7 chunks are referenced from both version records at zero additional storage cost.

**Version access:** The metadata service serves the chunk manifest for any version ID. Recovery is O(chunks) download time, not a full backup restoration.

## Notification and Real-Time Sync

When file A is modified on Device 1, Device 2 needs to know to pull the update.

**Approach:** Long-polling or WebSocket connection from each client to a notification service. When the metadata service records a file change, it publishes to a message queue (Kafka). The notification service consumes these events and pushes to connected clients with the affected file.

Clients then fetch the updated manifest and delta-sync only the changed chunks.

## Storage Backend

Chunks are stored in object storage (S3, GCS, or Azure Blob). Object storage is:
- Infinitely scalable
- Extremely durable (11 nines with cross-region replication)
- Cheap at scale (~$0.023/GB/month for S3 Standard)
- Optimized for large sequential reads (ideal for file chunks)

Add a CDN layer for files accessed frequently (popular shared files, recently accessed documents) to reduce latency for downloads.

## Key Trade-offs to Discuss in an Interview

1. **Eventual vs. strong consistency:** Strong consistency for metadata (prevent double-writes); eventual consistency for sync is acceptable.
2. **Chunk size:** Smaller chunks = better dedup and delta sync; larger chunks = fewer metadata operations. 4-8MB is the practical sweet spot.
3. **Client-side vs. server-side chunking:** Client-side chunking offloads compute but requires trust in the client's implementation. Server-side is more reliable.
4. **Sync frequency:** Polling interval vs. push notifications trade off server load against sync latency.

This problem rewards candidates who think through the full data flow from client to storage and back, articulate the trade-offs at each step, and demonstrate awareness of how the pieces interact at scale.
