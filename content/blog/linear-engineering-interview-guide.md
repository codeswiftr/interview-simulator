---
title: "Linear Engineering Interview: Real-Time Sync, Offline-First, and Developer Tools"
description: "Inside Linear's engineering interview: offline-first architecture, real-time sync, CRDT patterns, optimistic UI, and what makes their stack technically distinctive."
date: "2026-03-20"
category: "Company Interview Guides"
---

# Linear Engineering Interview: Real-Time Sync, Offline-First, and Developer Tools

Linear has earned a reputation among engineers as one of the few companies that genuinely cares about software quality. The product is fast — exceptionally fast — because the team made architecture decisions that most SaaS companies avoid for their complexity. Understanding those decisions deeply is the key to succeeding in a Linear engineering interview.

## Why Linear Is Technically Interesting

Linear's core thesis is that project management software should be as fast as native apps. They achieved this by building an offline-first architecture with local SQLite state, optimistic UI, and a real-time sync engine — choices that are architecturally complex but yield an experience that feels native even in a web app.

Most SaaS apps are request-response: click a button, wait for the server, update the UI. Linear flips this: click a button, update the UI immediately (optimistic), sync to the server in the background. If the sync fails, reconcile. This approach eliminates the perceived latency that makes most web apps feel sluggish.

## The Tech Stack

**Frontend**: React + TypeScript, running in Electron for the desktop app and as a web app in the browser. The same codebase serves both targets.

**Local state**: SQLite via `sql.js` (WebAssembly SQLite for browser) or native SQLite in Electron. The local database stores a copy of the user's workspace data, enabling instant queries without network round-trips.

**Sync engine**: A custom real-time sync layer over WebSockets. Changes are represented as operations that can be applied locally, transmitted to the server, and replicated to other clients.

**Backend**: Node.js (TypeScript), PostgreSQL. The server is the source of truth; clients are authoritative caches.

## Offline-First Architecture

Offline-first means the application functions fully without network connectivity and reconciles when connectivity returns. This requires:

1. **Local database**: All reads come from the local SQLite database — zero network latency for any query.
2. **Operation log**: Changes are recorded as operations in an append-only log before being applied locally.
3. **Sync protocol**: Operations are transmitted to the server. The server assigns a global sequence number and broadcasts to other clients.
4. **Conflict resolution**: When two clients concurrently modify the same entity, the sync engine resolves conflicts deterministically.

Interview angle: "How would you design an offline-first sync system for a collaborative task manager?" This is a core design question at Linear. You need to discuss the operation log structure, how to handle conflicts, and how to ensure eventual consistency.

## CRDT and OT Concepts

Conflict-free Replicated Data Types (CRDTs) and Operational Transformation (OT) are the two main approaches to collaborative editing. Linear's sync is closer to operation-based (op-based) synchronization than strict CRDT, but interviewers expect you to know the concepts.

**CRDTs**: Data structures where concurrent operations always merge without conflicts because the merge function is commutative, associative, and idempotent. Last-Write-Wins (LWW) registers are the simplest CRDT. More complex: Grow-only sets, 2P-sets, RGA sequences.

**OT (Operational Transformation)**: Operations are transformed against concurrent operations before being applied. The transform function handles conflicts. Used by Google Docs. Difficult to implement correctly for more than two clients.

For Linear's use case (task attributes like title, status, assignee), LWW with server-assigned timestamps is often sufficient. The server is the arbiter — when two clients update the same field concurrently, the server's merge order wins.

## Optimistic UI

Optimistic UI applies changes locally before server confirmation, then reconciles if the server rejects or modifies the result.

The pattern requires:
- **Local state mutation**: Apply the operation to local SQLite immediately.
- **Pending operation queue**: Track in-flight operations that haven't been server-confirmed.
- **Rollback mechanism**: If the server rejects an operation, revert local state and notify the user.
- **Rebase**: If the server's response includes other operations that happened concurrently, apply them in order and re-apply pending local operations on top.

In React terms: the component reads from the local database (always fast), submits mutations to the sync engine (which applies locally + queues for server), and the WebSocket handler reconciles server state asynchronously.

## Interview Focus Areas

**Systems Design**: "Design the sync engine for Linear" — the most common design question. Discuss operation log, WebSocket transport, sequence numbers for ordering, conflict resolution strategy, reconnection handling (catch up on missed operations via sequence gaps).

**React and TypeScript**: Deep TypeScript knowledge (generics, conditional types, mapped types), React performance (memoization, avoiding re-renders, virtualized lists for large issue backlogs).

**Database**: SQLite query optimization, indexing strategy for filtered/sorted issue lists, handling schema migrations on the client side.

**Real-time systems**: WebSocket lifecycle (reconnection, backpressure, message ordering), heartbeat mechanisms, handling split-brain scenarios.

## Sample Interview Questions

**Q: How does Linear achieve such fast UI without network requests?**
A: Local SQLite database holds a synchronized copy of workspace data. All reads are local. Writes are applied optimistically to local state and synced asynchronously. The UI never waits for network responses.

**Q: What happens when two users edit the same issue title simultaneously?**
A: Both clients apply their change locally. Both transmit operations to the server. The server receives them in some order, assigns sequence numbers, and broadcasts both. Each client receives the other's operation and resolves the conflict — typically via last-write-wins using server timestamp. One edit wins; the other is rolled back locally and the UI updates.

**Q: How would you handle a client that's been offline for 2 hours reconnecting?**
A: The client tracks its last known server sequence number. On reconnect, it sends this number to the server and requests all operations since then. The server returns the delta. The client applies the delta to local state, then re-applies any pending local operations that weren't yet server-confirmed, resolving conflicts as needed.

**Q: Why use SQLite in the browser instead of IndexedDB directly?**
A: SQLite provides a full relational query engine with joins, indexes, and a familiar query language. IndexedDB is a key-value store with limited querying capability. Linear's issue list has complex filtering, sorting, and grouping that would be painful to implement efficiently in IndexedDB but is trivial in SQLite.

## Culture and Compensation

Linear is famously selective — they hire a small number of exceptional engineers rather than scaling headcount. The culture values taste, attention to detail, and craftsmanship. Engineers own entire features and are expected to think deeply about product decisions, not just implementation.

Senior SWE compensation (2026): $200K-$260K base + equity. The equity upside is meaningful given the company's trajectory.

Linear interviews reward candidates who have thought about the tradeoffs in distributed systems and real-time synchronization — not candidates who can recite CRDT papers, but candidates who can reason clearly about consistency, conflict resolution, and user experience under network uncertainty.
