# How to Ace System Design Interviews for Real-Time Collaborative Applications

Real-time collaborative applications are one of the most technically rich system design topics you will encounter at companies like Figma, Notion, Google, Dropbox, and Linear. "Design a collaborative document editor" or "design Figma" are interview questions that separate candidates who understand distributed systems deeply from those who only know the surface patterns. This guide gives you the conceptual framework, the technical vocabulary, and the trade-off language you need to give a strong answer.

## The Core Problem: Concurrent Edits and the Lost Update

Before you jump to a solution, make sure your interviewer sees that you understand why this problem is genuinely hard.

Imagine two users — Alice and Bob — are editing the same document. Alice sees `"Hello World"` and deletes `"World"`, leaving `"Hello "`. At the same moment, Bob appends `"!"` to get `"Hello World!"`. Both send their operations to the server. The server applies Alice's change, then Bob's. The final state is `"Hello !"` — Bob's exclamation point is preserved, but his `"World"` is silently gone.

This is the **lost update problem**. It happens whenever two operations are based on the same document state but are applied sequentially without accounting for each other's intent.

The naive fix — **last write wins (LWW)** at the document level — is even worse. Under LWW, whichever write arrives last simply overwrites the other. Alice and Bob each save their entire document snapshot; whoever clicks last wins, and the other user's work vanishes completely. LWW is acceptable only when conflicts are extremely rare and data loss is tolerable (e.g., a settings toggle). For collaborative text or structured content, it destroys user trust immediately.

A strong interview answer names this problem explicitly and explains why LWW fails before proposing any architecture.

## Operational Transform (OT)

Google Docs uses Operational Transform, and it remains the canonical academic solution to collaborative editing.

The core idea: instead of sending document snapshots, clients send **operations** (insert character at position 5, delete 3 characters at position 12). When the server receives an operation that was generated against an older document state, it **transforms** the operation to account for any operations that have been applied in the meantime.

Here is a minimal Python sketch of the transformation function concept for plain text:

```python
def transform(op_a, op_b):
    """
    Transform op_a assuming op_b has already been applied.
    Both ops were generated against the same document state.
    Returns a new op_a' that is correct against the post-op_b state.
    """
    if op_a["type"] == "insert" and op_b["type"] == "insert":
        # If op_b inserted text before op_a's position, shift op_a right
        if op_b["pos"] <= op_a["pos"]:
            return {**op_a, "pos": op_a["pos"] + len(op_b["text"])}
        return op_a

    if op_a["type"] == "insert" and op_b["type"] == "delete":
        if op_b["pos"] < op_a["pos"]:
            return {**op_a, "pos": op_a["pos"] - op_b["length"]}
        return op_a

    if op_a["type"] == "delete" and op_b["type"] == "insert":
        if op_b["pos"] <= op_a["pos"]:
            return {**op_a, "pos": op_a["pos"] + len(op_b["text"])}
        return op_a

    # delete vs delete — overlapping deletions need special handling
    if op_a["type"] == "delete" and op_b["type"] == "delete":
        if op_b["pos"] + op_b["length"] <= op_a["pos"]:
            return {**op_a, "pos": op_a["pos"] - op_b["length"]}
        return op_a  # simplified; real OT handles overlap explicitly

    return op_a
```

The key insight: OT requires a **server as a central coordinator**. Clients send operations to the server, the server applies transformations, and it fans out the transformed operations to all other clients. This is why Google Docs has a single authoritative server per document — there is no peer-to-peer OT in production. The algorithm's complexity explodes when you try to eliminate the central server.

OT handles rich text well and has decades of academic validation, but its implementation complexity is notoriously high. The Jupiter protocol (used by early Google Wave) has subtle correctness bugs that took years to discover. Most startups and even many large teams avoid building OT from scratch.

## CRDTs: Conflict-Free Replicated Data Types

CRDTs are the modern alternative that powers Figma, Linear, Loom, and many other collaborative tools. The key difference: CRDTs require **no server coordination** for merging. Any two replicas can merge in any order and arrive at the same final state.

The mathematical foundation is a **join-semilattice**: a set of states with a merge operation that is commutative, associative, and idempotent. In plain terms: merging always produces the same result regardless of order, merging three things in any grouping gives the same result, and merging the same thing twice does nothing. These three properties are what make CRDTs safe without coordination.

**Common CRDT types:**

**G-Counter (grow-only counter):** Each node maintains its own counter slot. The global count is the sum of all slots. Incrementing only touches your own slot. Merging takes the max of each slot. This is the simplest CRDT and a great interview example:

```typescript
type GCounter = Record<string, number>; // nodeId -> count

function increment(counter: GCounter, nodeId: string): GCounter {
  return { ...counter, [nodeId]: (counter[nodeId] ?? 0) + 1 };
}

function merge(a: GCounter, b: GCounter): GCounter {
  const result: GCounter = { ...a };
  for (const [nodeId, count] of Object.entries(b)) {
    result[nodeId] = Math.max(result[nodeId] ?? 0, count);
  }
  return result;
}

function value(counter: GCounter): number {
  return Object.values(counter).reduce((sum, n) => sum + n, 0);
}
```

**LWW-Element-Set:** A set where each element carries a timestamp. Add and remove operations are both recorded with timestamps; the higher timestamp wins. This is how Figma tracks which objects are in a canvas.

**RGA (Replicated Growable Array):** The CRDT for collaborative text. Each character is assigned a unique ID (typically `nodeId + localClock`). Insertions reference the ID of the character they follow. Deletions mark characters as tombstones. Because IDs are globally unique and insertion order is deterministic, any two replicas converge to the same sequence.

CRDTs unlock **local-first architectures**: clients apply operations immediately to their local state without waiting for a server round-trip. Users get zero-latency feedback. The server (if any) is just another replica. This is why Figma feels instantaneous even on a slow connection — your local canvas updates immediately, and sync happens in the background.

## Practical Hybrid Approaches

Most production systems are not pure OT or pure CRDT. Interviewers at Notion, Dropbox, and similar companies will respect you more for knowing this.

**Notion's approach** is instructive. Notion treats each block (paragraph, heading, table) as the unit of conflict resolution. Within a single block, they use **block-level LWW**: the last write to that block wins. Across blocks — adding, deleting, reordering — they use server-authoritative ordering with version vectors. This is not theoretically elegant, but it is simple to implement, simple to debug, and covers 99% of real editing patterns. Two users rarely edit the exact same paragraph at the exact millisecond.

In your interview, the strongest answer is not necessarily the one that reaches for CRDTs first. It is the one that:

1. States the problem clearly (concurrent edits, lost updates)
2. Explains the spectrum of solutions and their trade-offs (LWW → block LWW → OT → CRDTs)
3. Asks about the consistency requirements and the conflict frequency expected
4. Proposes the simplest solution that meets the requirements, then describes how to extend it

If the interviewer asks you to design Google Docs, reach for OT or CRDT semantics for character-level text. If they ask you to design a Jira-like tool or Notion, block-level LWW with server authority is a defensible and honest answer.

## Supporting Infrastructure

The conflict resolution algorithm is only one part of the answer. Strong candidates also address the surrounding infrastructure.

**WebSocket connection management at scale:** Collaborative apps need persistent bidirectional connections. At scale, you cannot route all users on a document to a single WebSocket server. Use a pub/sub layer (Redis, NATS, Kafka) behind a fleet of WebSocket gateway servers. When user A sends an operation, the gateway publishes it to a channel keyed by document ID. All gateways subscribed to that channel fan the operation out to their connected clients.

**Presence: who is editing right now?** Presence is eventually consistent by nature — a few seconds of lag is acceptable. Use a lightweight heartbeat: clients broadcast a presence ping (user ID, document ID, timestamp) every 5 seconds. A presence server aggregates these and broadcasts the active-users list to all clients in the document. On timeout (no ping for 15 seconds), the user is removed from the presence list.

**Cursor sharing and awareness:** Figma and Google Docs both show collaborators' cursors. Cursor position is highly ephemeral — there is no value in persisting it. Broadcast cursor updates over the same WebSocket channel as operations, but tag them as non-durable. Clients render cursor positions locally with a brief animation and discard them after a few seconds of inactivity.

**Offline support and sync-on-reconnect:** Local-first architectures handle this naturally — the client applies operations to its local CRDT replica while offline and syncs the operation log on reconnect. For OT-based systems, clients queue operations with their originating server version and replay them in order when the connection is restored. The server applies each queued operation through the transformation pipeline as if it arrived in real time.

## What Makes a Strong vs. Weak Answer

A **weak answer** jumps straight to "use WebSockets and a database" without addressing concurrency semantics, proposes last-write-wins without acknowledging data loss, or treats the problem as purely a networking challenge.

A **strong answer** demonstrates that you understand the correctness properties required — convergence, intent preservation, causality — and can map those properties to specific algorithms. You explain trade-offs honestly: OT is battle-tested but operationally complex; CRDTs are mathematically elegant but have higher memory overhead (tombstones accumulate); block-level LWW is pragmatic but fails for character-level collaboration.

Mention the names engineers know: Jupiter protocol, WOOT, Automerge, Yjs (a production-grade CRDT library used by dozens of companies). Show awareness that Figma built their own CRDT engine in C++ compiled to WebAssembly for performance. These details signal that you have thought about this problem outside the interview room.

The goal is not to memorize one right answer. It is to show that you can reason from first principles, navigate ambiguity, and explain trade-offs clearly — which is exactly what strong engineers do every day.
