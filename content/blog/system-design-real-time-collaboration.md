---
title: "Real-Time Document Collaboration: OT, CRDT, and Conflict Resolution"
description: "Deep dive into operational transformation math, CRDT theory, conflict resolution algorithms, and offline sync for collaborative editing systems beyond surface-level Notion design."
date: "2026-03-20"
category: "System Design"
---

Real-time collaborative editing — the kind that lets two people type in the same document simultaneously — is deceptively hard. Most system design answers describe the API surface (WebSockets, presence indicators) but miss the fundamental challenge: **how do you reconcile concurrent edits that conflict?** The answer requires either Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs), and understanding both is what separates a strong answer from a great one.

## The Core Problem

Consider two users editing the string "Hello":

- User A inserts "!" at position 5 → "Hello!"
- User B deletes "o" at position 4 → "Hell"

If both edits start from "Hello" and are applied independently, they conflict. The naive approach (last write wins) loses data. The right approach transforms each operation against the other before applying it.

## Operational Transformation: The Math

OT defines a transform function `T(op1, op2)` that adjusts `op1` assuming `op2` has already been applied, such that:

```
apply(apply(doc, op1), T(op2, op1)) == apply(apply(doc, op2), T(op1, op2))
```

This **convergence property** guarantees all clients reach the same final state regardless of the order in which they receive operations.

### Basic Text OT

Operations on text are insert(pos, char) and delete(pos):

```
Transform insert(pos1, c) against delete(pos2):
  if pos2 < pos1:
    return insert(pos1 - 1, c)  // deleted char shifts our position left
  else:
    return insert(pos1, c)      // deletion was after us, no change

Transform insert(pos1, c1) against insert(pos2, c2):
  if pos2 < pos1:
    return insert(pos1 + 1, c1) // inserted char shifts our position right
  elif pos2 == pos1 and user2_has_priority:
    return insert(pos1 + 1, c1) // tie-break by user ID
  else:
    return insert(pos1, c1)
```

This is simple for character-by-character operations but becomes exponentially complex for rich text (bold, lists, tables). Google Docs uses OT, and maintaining correctness across their full feature set required years of engineering.

### The Jupiter/Wave Protocol

Google Wave (and later Google Docs) uses the Jupiter protocol for client-server OT. Rather than peer-to-peer transformation, the server is the single source of truth:

1. Client sends operation + revision number the client was at when they created the op
2. Server transforms the operation against all ops that arrived since that revision
3. Server applies the transformed op and broadcasts to all clients
4. Clients transform the server's broadcast against any in-flight local ops

The server-centric model reduces the transformation complexity from O(n²) to O(n) — you only transform against the server's history, not against all other clients.

## CRDTs: A Different Approach

CRDTs (Conflict-free Replicated Data Types) embed convergence into the data structure itself, eliminating the need for a central server to transform operations. Two properties:

**Join-semilattice:** The state space has a merge function that is commutative, associative, and idempotent. You can merge any two states in any order and get the same result.

**Two flavors:**
- **State-based (CvRDT):** Send the full state periodically; merge states on receive
- **Operation-based (CmRDT):** Send only operations; guarantee exactly-once delivery

### RGA: Replicated Growable Array

The most practical CRDT for collaborative text is the RGA (Replicated Growable Array) or its relatives (LSEQ, Logoot, FUGUE).

Each character is assigned a globally unique identifier — typically `(timestamp, site_id)` — forming a total order. Characters are stored as a linked list sorted by their identifiers:

```
"Hello" represented as:
[(1,A,'H'), (2,A,'e'), (3,A,'l'), (4,A,'l'), (5,A,'o')]

User A inserts '!' after (5,A,'o'):
new char: (6,A,'!')

User B inserts '?' after (5,A,'o') simultaneously:
new char: (6,B,'?')

After merging: sort by (timestamp, site_id) for tie-breaking
Result: [(5,A,'o'), (6,A,'!'), (6,B,'?')] → "Hello!?"
or [(5,A,'o'), (6,B,'?'), (6,A,'!')] → "Hello?!"
```

The tie-breaking is consistent — everyone applies the same ordering rule — so all clients converge to the same document, even if one ordering is arguably wrong from a semantic standpoint.

### Tombstoning Deletions

Deletions in CRDTs are typically implemented as **tombstones** — marking a character as deleted without removing it from the list. This prevents the "delete then insert at same position" confusion:

```python
class RGAChar:
    def __init__(self, uid, char):
        self.uid = uid
        self.char = char
        self.deleted = False

    def delete(self):
        self.deleted = True
```

Tombstones accumulate over time — garbage collection requires knowledge of which clients have seen which deletions, which is a distributed snapshot problem.

### CRDT Drawbacks

1. **Identifier bloat:** Each character carries a unique identifier. Documents become much larger in memory.
2. **Tombstone accumulation:** Deleted content stays in the structure until GC.
3. **Interleaving:** Some CRDT algorithms allow interleaved insertions from concurrent edits in ways that produce semantically confusing results (the "interleaving anomaly"). FUGUE was designed specifically to prevent this.
4. **Rich text complexity:** Formatting spans require additional CRDT structures (RichText CRDT, or combining RGA with a separate formatting layer).

## Practical Architecture

### Real-Time Sync Layer

```
Client → WebSocket → Server → Broadcast to other clients
         (op + rev)           (transformed op + new rev)
```

For OT: the server is the authority. For CRDTs: you can go peer-to-peer, but most production systems use a server relay for presence, persistence, and access control even with CRDTs.

**Automerge** (JavaScript/Rust CRDT library) and **Yjs** are the two dominant open-source CRDT implementations. Yjs is preferred for web because of its performance and provider ecosystem (WebRTC, WebSocket, IndexedDB).

### Presence and Cursor Awareness

Cursor positions are ephemeral — they don't need the same consistency guarantees as document content. Use a separate lightweight pub/sub for presence (who is editing) and cursor position (mapped to document positions using the CRDT identifiers). Update cursors on every keystroke; users expect near-zero latency here.

### Offline Sync

CRDTs shine for offline editing:
1. Client works offline, accumulating operations in a local CRDT
2. On reconnect, merge local CRDT state with server state
3. Convergence is guaranteed by CRDT properties

For OT, offline sync is harder — you need to preserve the full operation history to transform against server changes since you disconnected.

## OT vs CRDT: When to Use Each

| Aspect | OT | CRDT |
|--------|----|----|
| Server requirement | Centralized server required | Optional |
| Implementation complexity | Complex transform functions | Simpler per-operation logic |
| Memory overhead | Low | Higher (identifiers + tombstones) |
| Offline support | Complex | Natural |
| Rich text | Mature (Google Docs) | Maturing (Yjs, Automerge) |
| Production maturity | Very high (20+ years) | High and growing |

## What to Say in Interviews

When asked "design Google Docs," the differentiating answer covers:

1. The conflict problem concretely (two users, one document, show the conflict)
2. OT vs CRDT trade-offs with honest assessment of both
3. Server architecture for operation log, version management, and broadcast
4. Presence as a separate low-latency channel
5. Offline sync strategy
6. Snapshot + garbage collection for managing document history size

Most candidates stop at WebSockets and optimistic updates. Going deeper into convergence algorithms signals that you've thought about the hardest problem in collaborative systems.
