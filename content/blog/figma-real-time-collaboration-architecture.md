---
title: "Figma Real-Time Collaboration Architecture"
description: "How Figma enables real-time multiplayer design—operational transforms vs CRDTs, delta synchronization, cursor broadcasting, and the architecture behind 4M+ concurrent design sessions."
date: "2026-03-21"
category: "System Design"
---

# Figma Real-Time Collaboration Architecture

Figma was the first design tool to enable real-time multiplayer collaboration in the browser. Multiple designers can edit the same file simultaneously, seeing each other's changes instantly—like Google Docs but for complex vector graphics. The engineering behind this is a rich combination of distributed systems, CRDTs, and WebSocket infrastructure.

## The Core Challenge

Design files are complex structured documents: frames, layers, components, text, constraints, auto-layout. Multiple users editing simultaneously must:
1. See each other's changes in real-time (< 100ms)
2. Never lose data (no overwrites when two users edit the same thing)
3. Converge to a consistent state (everyone ends up with the same document)

This is the **collaborative editing problem**, solved by either Operational Transforms (OT) or CRDTs.

## Figma's Document Model

Figma represents documents as a tree of nodes, each with a unique ID and a map of properties:

```
Node {
  id: "abc123",
  type: "RECTANGLE",
  properties: {
    x: 100,
    y: 200,
    width: 300,
    height: 150,
    fill: "#FF0000"
  },
  children: ["def456", "ghi789"]
}
```

Operations on this document are granular: set property, add child, remove child, reorder children. This granularity is key — conflicting operations are usually on different properties of different nodes.

## CRDTs for Conflict Resolution

Figma uses a CRDT (Conflict-free Replicated Data Type) approach. Each property value is a **Last-Write-Wins Register**: if two users set the same property simultaneously, the one with the later logical timestamp wins.

```python
class LWWRegister:
    def __init__(self):
        self.value = None
        self.timestamp = 0
        self.author = None

    def set(self, value, timestamp, author):
        if timestamp > self.timestamp or (
            timestamp == self.timestamp and author > self.author
        ):
            self.value = value
            self.timestamp = timestamp
            self.author = author
```

Tie-breaking by author ID ensures determinism when timestamps collide.

For tree structure (node ordering, parent-child relationships), Figma uses a **fractional indexing** scheme: node positions are represented as fractions between their neighbors, allowing insertions without renumbering.

## Delta Synchronization

When User A moves a rectangle, only the changed property is sent — not the entire document:

```json
{
  "op": "set_property",
  "node_id": "abc123",
  "property": "x",
  "value": 250,
  "timestamp": 1000,
  "author": "user_A"
}
```

The server receives this operation, applies it to the server-side document, and broadcasts it to all other connected clients. Each client applies the operation to their local copy.

Bandwidth estimate: moving a shape continuously generates ~10 ops/second. At 4M concurrent users × 10 ops/s × 50 bytes/op = 2 TB/s total bandwidth. With delta compression and grouping (batch 100ms of ops into one message), this becomes manageable.

## WebSocket Architecture

```
Client ──WebSocket──> Presence Server
                           ↓
                     Message Bus (Kafka)
                           ↓
                     Document Server (authoritative state)
                           ↓
                     Broadcast to other clients via Presence Server
```

**Presence servers** manage WebSocket connections. They're stateless except for connection routing—they don't store document state.

**Document servers** maintain authoritative document state in memory. Each document is assigned to a single document server. This avoids the need for distributed consensus within a document.

Problem: what if the document server goes down? Periodic snapshots to durable storage (PostgreSQL + S3). On restart, restore from snapshot and replay Kafka log since snapshot.

## Cursor and Selection Broadcasting

Seeing other users' cursors is separate from document operations:
- Cursor positions are **ephemeral** (not persisted)
- Broadcast to all clients in the file room
- High frequency (30 fps for smooth cursor movement)
- Best-effort delivery (dropped cursor position just shows cursor a bit behind)

Cursor events flow directly through the presence server without touching the document server. They're published as typed messages in the Kafka topic but not applied to document state.

## Offline and Reconnection

When a client loses connection:
1. Client continues editing locally (optimistic UI)
2. On reconnect, client sends all unacknowledged operations
3. Server applies operations (CRDT semantics handle conflicts)
4. Server sends the client all operations it missed

The client's local document state and the server's state may have diverged. CRDT merge converges them deterministically — same operations applied in different orders produce the same result.

## Large Files and Performance

Design files can be huge: 50K+ nodes, complex components. Challenges:

**Progressive loading**: Load only visible viewport initially. Load off-screen layers lazily.

**Operation batching**: Batch rapid small operations (dragging a shape sends 30 ops/second; batch into 100ms windows = ~3 batches/second per operation type).

**Canvas rendering**: WebGL-based renderer (Figma built their own). Only re-render dirty regions.

**Component libraries**: Shared components stored separately. Changes to a component propagate to all files using it asynchronously (not in real-time — that would be too disruptive).

## Multiplayer Presence Features

Beyond cursors:
- **User avatars** in the toolbar: colored dots showing who's in the file
- **View following**: "Follow" another user to see what they're looking at
- **Observation mode**: watch without ability to edit
- **Named selections**: see what each user has selected (highlighted bounding boxes)

These are all built on the presence system, separate from document operations.

## Version History

Figma auto-saves version history. This is implemented as:
1. Periodic snapshots of full document state (every 30 minutes, or on significant edits)
2. Each snapshot is a complete document state stored in S3
3. Version history UI shows snapshots; restoring loads the snapshot as a new document state

Named versions ("Final_v2") are user-created bookmarks in the snapshot timeline.

## Interview Tips

Real-time collaboration is a niche but impressive system design answer:

1. **LWW CRDTs vs Operational Transforms** — explain why CRDTs are simpler to implement correctly at scale
2. **Document server = single authoritative state** — avoids distributed consensus per-document
3. **Cursor broadcasting as ephemeral separate channel** — don't conflate with document ops
4. **CRDT merge on reconnection** — deterministic convergence regardless of operation order
5. **Fractional indexing for tree structure** — the clever trick for node ordering without renumbering

The single authoritative document server (per document) is the key scalability decision. It's simple and correct—Figma can afford it because documents are the unit of isolation, not the entire system.
