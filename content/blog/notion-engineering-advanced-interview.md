---
title: "Notion Engineering Advanced Interview Guide"
description: "Deep-dive Notion engineering interview preparation — block-based data model, collaborative editing (CRDT), offline sync, the Notion API, and system design questions you'll face at senior levels."
date: "2026-03-20"
category: "Company Guides"
---

# Notion Engineering Advanced Interview Guide

Notion's engineering interviews are among the most technically interesting at growth-stage companies. The product's collaborative, block-based architecture requires solving hard problems in real-time sync, offline support, and flexible data modeling. Senior engineers interviewing at Notion should understand not just the standard algorithms and systems design, but the specific technical challenges inherent to the product.

## Understanding Notion's Technical Challenges

Notion's core innovation is a flexible, block-based data model where everything — pages, databases, text, embeds — is a block with a parent-child relationship. This creates interesting engineering challenges:

**Recursive data structures:** A page is a block; a database is a block; a database row is a block that contains block children. Queries over this tree require recursive approaches that don't map cleanly to traditional relational schemas.

**Real-time collaboration:** Multiple users editing the same page simultaneously requires conflict resolution. Notion uses Operational Transformations (OT) or CRDT-based approaches to merge concurrent edits without data loss.

**Offline support:** Notion's desktop app works offline and syncs when reconnected. This requires a local queue of uncommitted operations, conflict detection on sync, and optimistic UI updates.

## The Block Data Model in Depth

Notion's data model: every piece of content is a `Block` with:
- `id` (UUID)
- `type` (page, text, heading, todo, database, etc.)
- `parent_id` (nullable — null for workspace-level pages)
- `properties` (key-value, type depends on block type)
- `content` (ordered list of child block IDs)

This flexible schema means a single table structure can represent any document layout. The tradeoff: fetching a complete page requires either recursively loading blocks (N+1 query problem) or a bulk fetch with client-side tree assembly.

**Interview question:** "How would you fetch a complete Notion page with all its blocks efficiently?"

The answer involves fetching the page root block, then all descendant blocks in a single query using a recursive CTE (Common Table Expression) in PostgreSQL:

```sql
WITH RECURSIVE page_blocks AS (
  SELECT * FROM blocks WHERE id = $page_id
  UNION ALL
  SELECT b.* FROM blocks b
  INNER JOIN page_blocks pb ON b.parent_id = pb.id
)
SELECT * FROM page_blocks;
```

## Collaborative Editing: CRDTs vs. OT

Notion uses a form of operational transformation for real-time collaboration. Understanding the tradeoffs between CRDT and OT is a key Notion interview topic.

**Operational Transformation (OT):** Transform operations based on concurrent operations from other users. Requires a central server to order and transform operations. Proven approach (Google Docs). Complex to implement correctly; commutativity and associativity of transforms are hard to guarantee.

**CRDT (Conflict-free Replicated Data Type):** Operations are designed to be commutative by construction. Can merge without a central coordinator. Logoot, LSEQ, and RGA are text CRDTs. Better for offline-first and peer-to-peer scenarios. Higher memory overhead.

**Notion's approach:** A hybrid — operations are sent to a central server that applies them in order and broadcasts to other clients. Local optimistic application with server reconciliation. This simplifies the CRDT/OT complexity by using server-side ordering as the source of truth.

## System Design: Real-Time Collaborative Document

"Design a real-time collaborative document editor supporting 50 concurrent editors."

Key components:
- **Document server:** Maintains authoritative document state; applies and broadcasts operations
- **Operation log:** Append-only log of all operations; enables replay and historical views
- **WebSocket connections:** Persistent connection per client for low-latency operation delivery
- **Operational transformation engine:** Transforms client operations against concurrent server operations before applying
- **Presence service:** Tracks cursor positions and active users; can be eventually consistent

The tricky part: operation ordering. Client A and client B both insert text at position 5 simultaneously. The server receives A first, applies it, then transforms B's operation (since position 5 has shifted) and applies the transformed operation. The transformation function must handle all operation pairs correctly.

## Offline Sync Architecture

Notion's offline mode works by:
1. Caching all viewed blocks in a local SQLite database (or IndexedDB for web)
2. Queuing operations locally while offline
3. On reconnection, replaying the local operation queue to the server
4. Resolving conflicts: if server state diverged from local assumptions, transform queued operations or prompt the user

Design question: "How do you handle a user who edits offline for 3 days and reconnects?"

The answer: server-side operation log enables three-way merge. The client sends its local operations along with the last-known server sequence number. The server identifies the delta (operations since that sequence), and applies OT to transform the client's operations against the intervening server operations before applying.

## Notion's Technology Stack

Notion runs on TypeScript (frontend and backend), PostgreSQL for persistent storage, Redis for caching and pub/sub, and Kubernetes for orchestration. The frontend is React with a custom rendering engine for the block editor.

Understanding TypeScript deeply matters — Notion's interviews test advanced TypeScript including generics, conditional types, and type inference patterns that map to their block type system.

## What Notion Evaluates

Based on engineering blog posts and interview accounts:
- **Systems thinking:** Can you design the collaboration and sync systems?
- **Data modeling:** Can you extend the block model for new content types?
- **TypeScript depth:** Advanced type system usage for type-safe block handling
- **Product understanding:** Do you understand why Notion's design choices were made?

Come prepared with opinions on collaborative editing tradeoffs and a clear understanding of the product. Engineers who have used Notion deeply and can articulate what makes it technically interesting tend to do well.
