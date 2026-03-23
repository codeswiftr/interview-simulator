# Linear Engineering Deep Dive: Local-First Architecture, Sync Engines, and the 50ms Standard

Linear is a project management tool that does not feel like one. On most productivity software, clicking "change priority" fires a request, waits for a server round trip, and updates the UI when it hears back. On Linear, the action is instant — the UI updates before the network request completes, and the server catches up in the background. This is not a trick. It is the product of a deliberate architectural commitment that has shaped every layer of Linear's stack, from the database engine running in the browser to the conflict resolution protocol running on the server.

Understanding how Linear achieves this is the most productive preparation you can do before interviewing there.

---

## Local-First Architecture and CRDTs

Linear's core architectural bet is that the client owns the truth for the current session. Rather than the traditional request-response model — where the client is a thin view over server state — Linear keeps a full working copy of your data in a local SQLite database embedded in the browser via WebAssembly. Reads never touch the network. When you open an issue, filter a project, or scroll through a backlog, the query hits local storage and returns in under a millisecond.

Writes use optimistic updates. When you change an issue's status, Linear applies the change to the local database immediately and renders it synchronously. The mutation also gets enqueued for sync to the backend. If the server rejects it (rare), the client rolls back. If the server accepts it, no additional UI update is needed — the state is already correct.

This pattern is sometimes called "local-first software," a term coined by Ink & Switch in their 2019 essay. The defining property is that local state is always valid and always authoritative for the user's own actions. Network connectivity is an optimization for sharing, not a prerequisite for working.

The hard problem in local-first systems is concurrent edits. What happens when two engineers edit the same issue simultaneously, or when one engineer works offline and then reconnects with a backlog of changes? This is where conflict-free replicated data types (CRDTs) enter.

A CRDT is a data structure designed so that any two replicas that have seen the same set of operations will converge to the same state, regardless of the order those operations were applied. The classic example is a last-write-wins register: each value is tagged with a logical timestamp, and when two replicas compare values, the one with the higher timestamp wins. Because the merge function is deterministic, two replicas performing the merge independently will always reach the same result.

Linear uses an operation-based variant of this idea. Every mutation is represented as an immutable operation:

```typescript
interface Operation {
  id: string;           // UUID, globally unique
  entityId: string;     // The issue/project/etc. being modified
  entityType: string;   // "issue" | "project" | "cycle" | "comment"
  field: string;        // The specific field being changed
  value: unknown;       // New value
  userId: string;       // Who made the change
  clientTimestamp: number;  // Lamport clock value at client
  serverTimestamp?: number; // Assigned by server on receipt
}
```

When operations arrive at the server, they are assigned a monotonically increasing server timestamp — a logical clock that establishes a total order across all mutations in the system. Clients synchronize by fetching operations they have not yet seen and replaying them against their local database. Conflicts on the same field resolve by server timestamp: the operation with the higher timestamp wins.

This is different from a strict CRDT implementation (which requires the merge function to be commutative, associative, and idempotent without a central arbiter), but it achieves the same practical goal: convergence without coordination. The server's timestamp assignment is the only point of centralization, and it happens asynchronously — it does not block the client.

---

## The Sync Engine

Linear's sync engine is a custom protocol built on WebSockets. When a client connects, it sends a "catch-up" message containing the highest operation sequence number it has applied. The server responds with any operations since that sequence number. After the catch-up is complete, the server pushes new operations in real time as they arrive from other clients.

This is architecturally distinct from Firebase's realtime database, which pushes entire document snapshots, or Supabase's realtime, which streams PostgreSQL change events. Linear's sync is operation-based: the server sends the minimal delta that the client needs to reach the current state, and the client applies it deterministically.

The reconnection flow deserves particular attention because it surfaces several non-obvious tradeoffs:

1. **Gap detection.** When a client reconnects, it requests operations since sequence N. If the server's log has been compacted and operations before some sequence M > N have been pruned, the client cannot catch up incrementally. It must do a full resync: discard local state and re-fetch the current snapshot. Linear handles this by maintaining operation logs long enough that most clients can catch up incrementally, with full resync as a fallback.

2. **Pending operations.** The client may have enqueued mutations while offline. On reconnect, these must be submitted to the server in order, with server timestamps assigned. If any pending operation touches a field that a remote operation also modified (with a later server timestamp), the pending operation loses on that field. The client rolls back the local state for that field and applies the server's version.

3. **Structural conflicts.** Last-write-wins works cleanly for scalar fields (status, priority, title). It breaks down for structural mutations: what if a user deleted an issue while another user was adding a comment to it? Linear's conflict resolution policies for structural operations are explicit: deletes win over modifications, moves win over property changes on the moved entity. These policies are encoded in the sync engine and applied uniformly.

What distinguishes this from simpler realtime approaches (e.g., polling or Firebase) is that the operation log is the source of truth, not the current state of any row. This makes audit history, undo, and time-travel views straightforward to implement — the data is already there.

---

## Performance Engineering: The 50ms Standard

Linear's stated target is that every interaction responds within 50 milliseconds. This is aggressive. For reference, humans perceive latency above 100ms as a system responding rather than reacting. At 50ms, interactions feel instantaneous.

Achieving this requires the local-first architecture as a foundation, but several additional techniques matter:

**SQLite via WebAssembly.** Linear runs a full SQLite database in the browser using WASM. This is not a key-value store or an IndexedDB wrapper — it is the complete SQLite engine, compiled to WebAssembly, executing queries against a local file in the browser's origin-private file system. A query like "return all open issues assigned to me, sorted by priority, with their project names" executes in the browser with no network I/O and returns results in single-digit milliseconds.

The query pattern looks roughly like this in practice:

```typescript
// Local SQLite query via WASM — no network, <2ms typical
async function getMyOpenIssues(userId: string): Promise<Issue[]> {
  const db = await getLocalDatabase();
  return db.query<Issue>(`
    SELECT
      i.id,
      i.title,
      i.priority,
      i.stateId,
      p.name AS projectName,
      s.name AS stateName,
      s.type AS stateType
    FROM issues i
    JOIN projects p ON i.projectId = p.id
    JOIN workflow_states s ON i.stateId = s.id
    WHERE i.assigneeId = ?
      AND s.type != 'completed'
      AND s.type != 'cancelled'
      AND i.trashed = 0
    ORDER BY i.priority ASC, i.updatedAt DESC
  `, [userId]);
}
```

**React virtualization.** Linear's issue lists can contain thousands of items. Rendering 5,000 DOM nodes simultaneously would destroy frame rates. Linear uses windowed rendering — only the rows currently visible in the viewport (plus a small buffer) are in the DOM. As the user scrolls, rows are recycled. This keeps the DOM size bounded regardless of list length.

**Aggressive prefetching.** Linear prefetches data that is likely to be needed before the user requests it. When a user hovers over an issue, the detail view's data is already being fetched. When a user opens a project, the adjacent cycles are preloaded. This converts perceived latency from "wait for data" to "wait for render," and with a local database, render latency is deterministic and fast.

**Priority-ordered sync.** Not all data is equally urgent. The sync engine prioritizes fetching the user's own issues and recent activity before fetching full team backlogs. This means the application is useful within seconds of load even before the full sync is complete.

---

## The Data Model

Linear's data model is designed around the query patterns of a software team, not around normalized relational purity. The core entities are: issues, projects, cycles, teams, workflow states, and users.

Issues are the central entity. Each issue belongs to a team, optionally belongs to a project, and optionally belongs to a cycle. Workflow states are team-scoped and typed (unstarted / started / completed / cancelled / triage), which allows Linear to provide opinionated views (e.g., "all started work") while supporting custom states within each type.

The GraphQL API reflects these query patterns directly. Rather than exposing a generic CRUD API and asking clients to do N+1 fetches, Linear's API includes connection types that allow nested traversal:

```graphql
query TeamIssues($teamId: String!, $first: Int, $after: String) {
  team(id: $teamId) {
    issues(
      first: $first
      after: $after
      filter: { state: { type: { nin: ["completed", "cancelled"] } } }
      orderBy: priority
    ) {
      nodes {
        id
        title
        priority
        state { name type color }
        assignee { name avatarUrl }
        project { name color }
        cycle { number startsAt endsAt }
      }
      pageInfo { hasNextPage endCursor }
    }
  }
}
```

The GraphQL layer is thin over the local database for reads (the client queries SQLite directly) and thin over the operation queue for writes (mutations enqueue operations rather than making direct HTTP calls). This layering is what allows the API to feel responsive — the transport layer is almost never in the critical path.

---

## Interview Implications: What Linear Is Actually Testing

Linear runs approximately 50 engineers serving millions of users. The ratio is extraordinary, and it is intentional. At that scale, every hire either raises or lowers the team's average. The interview process is explicitly designed to find engineers in the top few percent — not on competitive programming puzzles, but on the specific combination of technical depth and product judgment that Linear's work requires.

**System design questions at Linear** are almost always grounded in their actual architecture. "Design a real-time issue tracker" and "design a local-first sync engine" are canonical. The evaluation is not whether you converge on their exact solution, but whether you understand the tradeoffs. Can you articulate why local-first requires a different conflict resolution model than server-authoritative? Do you understand why CRDTs solve eventual consistency without coordination? Can you reason about what breaks when users edit the same field concurrently versus different fields?

When discussing sync engine design, demonstrate that you know the difference between state-based and operation-based CRDTs, and why the choice matters for a product like Linear. State-based CRDTs (like G-Sets and LWW-Registers) merge by comparing full state; operation-based CRDTs merge by commuting operations. Operation-based approaches produce smaller deltas (you send the operation, not the full state) but require reliable delivery guarantees. Linear's choice of an operation log with server-assigned timestamps is a hybrid: it leverages the delta efficiency of operation-based sync while using the server as a lightweight coordinator for total ordering.

**What Linear looks for** beyond technical competence is taste — the ability to recognize the difference between a product decision that is right and one that merely works. In practice this means: do you have strong opinions about API design? Can you articulate why a feature should be scoped the way it is? Do you push back constructively when a proposed design has the wrong tradeoffs? Engineers who have spent time thinking about user experience as a technical problem — not just as something designers handle — fit the culture well.

The take-home project is where most candidates lose. Linear's rubric explicitly favors code quality over feature completeness. A clean, well-structured implementation of 70% of the requirements will outscore a working but sloppy implementation of 100%. If you are preparing for Linear, practice writing code that you would be proud to put in a production codebase — not code that passes a test suite.

The canonical preparation loop: use Linear daily, read their engineering blog (they publish occasionally on local-first architecture and performance), and practice system design questions that involve sync and conflict resolution. The technical content of the interview is largely predictable. What is less predictable is whether you have the taste to recognize the right answer when you see it.
