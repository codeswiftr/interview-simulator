---
title: "Linear Engineering Interview: Sync Engine, Local-First Architecture, and Interview Prep"
description: "Deep dive into Linear's engineering culture, sync engine architecture, Electron+SQLite local-first approach, and how to prepare for their software engineering interviews."
date: "2026-03-20"
category: "Company Deep Dives"
---

# Linear Engineering Interview: Sync Engine, Local-First Architecture, and Interview Prep

Linear has earned an outsized reputation in the developer community — not just for the product's speed and design quality, but for the engineering decisions behind it. The company runs a remarkably small team (under 100 people at the time of writing) while serving tens of thousands of engineering teams. Interviewing at Linear means demonstrating the kind of first-principles thinking and execution quality that makes this possible.

## The Local-First Architecture

Linear's most technically distinctive decision is its local-first sync architecture. Unlike most web applications where all state lives on the server and the client re-fetches on every operation, Linear stores a complete copy of your workspace data in an SQLite database embedded in the Electron app. Every interaction — creating an issue, changing status, leaving a comment — writes to the local SQLite database first and syncs to the server asynchronously.

The result is the near-instant UI responsiveness that Linear users frequently cite as their favorite feature. There's no network round-trip between you clicking "Create issue" and seeing the issue appear in your list.

```typescript
// Simplified view of Linear's local mutation flow
async function createIssue(input: CreateIssueInput): Promise<Issue> {
  const optimisticIssue = buildOptimisticIssue(input);

  // Write to local SQLite immediately — UI updates synchronously
  await localDB.issues.insert(optimisticIssue);

  // Emit to sync engine — server write happens asynchronously
  syncEngine.emit({
    type: "CreateIssue",
    data: input,
    localId: optimisticIssue.id,
    timestamp: Date.now(),
  });

  return optimisticIssue;
}
```

This pattern is called **optimistic UI** taken to its logical extreme. Most apps do optimistic updates for specific interactions; Linear makes it the default for everything.

## The Sync Engine: Delta Sync with CRDTs

The sync engine is the heart of Linear's architecture. It needs to reconcile local mutations with server state across multiple clients (web, desktop, mobile) that may all be making changes simultaneously and going offline independently.

Linear uses a **delta sync** approach: rather than sending full state snapshots, clients send and receive deltas — the minimal set of changes since a given version. Each delta is associated with a logical clock (a sequence number per workspace), enabling clients to request exactly the changes they've missed since their last sync.

```typescript
interface SyncDelta {
  workspaceId: string;
  fromVersion: number;
  toVersion: number;
  operations: SyncOperation[];
}

interface SyncOperation {
  type: "insert" | "update" | "delete";
  model: "Issue" | "Comment" | "Cycle" | "Project" | ...;
  id: string;
  data: Partial<ModelData>;
  version: number;
}
```

For conflict resolution, Linear leans on last-writer-wins semantics for most fields, with a few CRDT-like behaviors for fields that need merge semantics (e.g., sets of labels or assignees that can be modified concurrently). The server is the authority for resolving conflicts; the local database is eventually consistent with server state.

## The Tech Stack

Linear's stack, based on public engineering blog posts and job descriptions:

- **Desktop**: Electron with React + TypeScript, SQLite via better-sqlite3
- **Web**: React + TypeScript, same sync engine running in a Web Worker with IndexedDB instead of SQLite
- **Backend**: Node.js + TypeScript, GraphQL API
- **Database**: PostgreSQL (primary), Aurora for read replicas
- **Sync infrastructure**: Custom sync protocol over WebSockets
- **Infrastructure**: AWS, Kubernetes

The GraphQL API is interesting: Linear's GraphQL schema closely mirrors the sync engine's operation types, which means the API and the sync protocol share type definitions. This reduces the impedance mismatch between client-server and client-local communications.

## Engineering Culture

Linear's engineering culture can be summarized in three principles that they've stated publicly:

**Craftsmanship over compromise**: Linear is famous for not shipping features until they meet a high quality bar. Engineers are expected to push back on timelines if quality is at risk — this is explicitly part of the culture, not just a stated value.

**Small team, large ownership**: Every engineer owns significant surface area. There are no narrow specialists. An engineer working on the mobile app might also contribute to the sync engine and the GraphQL schema in the same week.

**Opinionated product decisions**: Linear has strong opinions about how project management should work and resists feature bloat. Engineers are expected to internalize these opinions and push back on feature requests that contradict them, even from customers.

## The Interview Process

1. **Recruiter screen** (30 min): Background, compensation alignment
2. **Technical screen** (60 min): Live coding, typically 1–2 medium algorithm problems
3. **Take-home project** (optional for some roles): Build a small feature or debug a provided codebase
4. **Onsite loop** (4 rounds):
   - Two coding rounds (medium to hard algorithm problems)
   - System design (often local-first sync, conflict resolution, or real-time collaboration)
   - Values and experience round with an engineering leader

Linear interviews skew toward senior engineers and expect candidates to have thought deeply about the tradeoffs in their past work. "I implemented X" is less interesting than "I chose X over Y because of Z, and it turned out to have this unexpected cost that we addressed by doing W."

## What to Prepare

**Algorithm-wise**: Graph algorithms, dynamic programming, and string processing are all relevant. Linear's engineering problems are practical — don't expect purely academic puzzles.

**System design**: Be deeply comfortable with local-first and offline-first architectures. Understand the difference between optimistic UI and true local-first. Know the major CRDT types (G-Counter, OR-Set, LWW-Register) and when to apply them. Practice designing sync protocols that handle network partitions gracefully.

**Behavioral / values**: Read Linear's public engineering blog. Form opinions about the tradeoffs they've made. Be ready to articulate a time you pushed back on shipping something undercooked — and what happened.

**Key technical concepts**: Logical clocks vs. wall clocks, SQLite WAL mode, IndexedDB limitations, WebSocket reconnection strategies, and GraphQL subscriptions vs. polling.

Linear raises the bar for what "fast software" can mean on the web. Engineers who join there tend to come away with permanently raised standards for product quality — that aspiration should come through clearly in your interview.
