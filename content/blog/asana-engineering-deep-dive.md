---
title: "Asana Engineering Deep Dive: Task Management at Workflow Scale"
description: "How Asana built Luna (a custom in-memory graph database), a real-time sync protocol, and an offline-first mobile architecture to manage billions of tasks and their dependencies."
date: "2026-03-19"
tags: ["engineering", "system-design", "asana", "distributed-systems", "graph-database", "interview-prep"]
author: "Interview Simulator"
readingTime: "9 min read"
---

Asana looks simple from the outside — tasks, projects, timelines. The engineering underneath is anything but. Asana is built on a custom in-memory graph database called Luna, a real-time sync protocol that keeps millions of concurrent clients consistent, and a mobile architecture that handles the chaos of offline mutations. If you are preparing for a systems design interview about task management, or interviewing at Asana specifically, these are the details that matter.

## Luna: A Graph Database Born from Product Necessity

Asana's data model is fundamentally a graph. A task can belong to multiple projects, have multiple assignees, block other tasks, be blocked by others, live in sections, carry custom fields, be duplicated, templated, or linked to goals. Representing this in a standard relational database means either a deeply normalized schema with expensive JOIN chains, or a denormalized schema that makes consistency hard to enforce.

Asana built **Luna** — an in-memory graph database that models the entire workspace as a graph of typed nodes and edges. In Luna's model:

- **Nodes** are objects: tasks, projects, users, custom fields, portfolios, goals.
- **Edges** are typed relationships: `task-in-project`, `task-blocked-by`, `user-assigned-to`, `task-child-of`.
- The graph is **persistent across server restarts** through an append-only write-ahead log (WAL) replayed on startup.
- **Reads are served from memory**, which is why Luna can return a task's full context — all projects it belongs to, all blocking dependencies, all assignees — in microseconds.

This is a significant architectural bet. Keeping the entire workspace graph in memory means Asana's infrastructure is DRAM-constrained rather than disk I/O-constrained. For an enterprise customer with hundreds of thousands of tasks and complex dependency chains, a single Luna instance may hold gigabytes of graph state. The payoff is query latency that no disk-backed database can match for deeply connected graph traversals.

## Graph Traversal: Detecting Dependency Cycles

One of the hardest problems in a task graph is cycle detection. If Task A blocks Task B, which blocks Task C, which blocks Task A, you have a deadlock that can never resolve. Asana must detect and reject cycle-creating edges before they are committed.

The naive approach — traverse the entire graph from the new edge's target looking for the source — is O(V + E) and acceptable for small graphs. At Asana's scale (billions of tasks, trillions of edges at peak enterprise), this requires careful implementation.

Here is a practical implementation of cycle detection using iterative DFS with early termination:

```python
from collections import defaultdict
from typing import Optional

class TaskDependencyGraph:
    def __init__(self):
        # adjacency list: task_id -> set of tasks it blocks
        self.blocks: dict[str, set[str]] = defaultdict(set)
        # reverse adjacency: task_id -> set of tasks blocking it
        self.blocked_by: dict[str, set[str]] = defaultdict(set)

    def add_dependency(self, blocker_id: str, blocked_id: str) -> bool:
        """
        Add a dependency: blocker_id blocks blocked_id.
        Returns True if the edge was added, False if it would create a cycle.
        """
        if self._would_create_cycle(blocker_id, blocked_id):
            return False
        self.blocks[blocker_id].add(blocked_id)
        self.blocked_by[blocked_id].add(blocker_id)
        return True

    def _would_create_cycle(self, new_blocker: str, new_blocked: str) -> bool:
        """
        Check if adding (new_blocker -> new_blocked) would create a cycle.
        A cycle exists if new_blocked can already reach new_blocker.
        Uses iterative DFS to avoid stack overflow on deep dependency chains.
        """
        if new_blocker == new_blocked:
            return True

        visited: set[str] = set()
        stack: list[str] = [new_blocked]

        while stack:
            current = stack.pop()
            if current == new_blocker:
                return True
            if current in visited:
                continue
            visited.add(current)
            # Traverse tasks that current blocks (follow dependency chain forward)
            for downstream in self.blocks.get(current, set()):
                if downstream not in visited:
                    stack.append(downstream)

        return False

    def get_dependency_chain(self, task_id: str) -> list[str]:
        """
        Return all tasks in the transitive dependency chain upstream of task_id.
        These are the tasks that must complete before task_id can start.
        """
        chain: list[str] = []
        visited: set[str] = set()
        stack: list[str] = list(self.blocked_by.get(task_id, set()))

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            chain.append(current)
            for upstream in self.blocked_by.get(current, set()):
                if upstream not in visited:
                    stack.append(upstream)

        return chain

    def get_critical_path(self, start_id: str, end_id: str) -> Optional[list[str]]:
        """
        Find the longest dependency chain between two tasks using topological ordering.
        Returns None if no path exists.
        """
        # BFS to find all reachable nodes from start
        reachable: set[str] = set()
        queue: list[str] = [start_id]
        while queue:
            node = queue.pop(0)
            if node in reachable:
                continue
            reachable.add(node)
            queue.extend(self.blocks.get(node, set()))

        if end_id not in reachable:
            return None

        # Dynamic programming: find longest path
        dist: dict[str, int] = {start_id: 0}
        prev: dict[str, Optional[str]] = {start_id: None}
        # Topological sort of reachable subgraph (Kahn's algorithm)
        in_degree = {n: 0 for n in reachable}
        for node in reachable:
            for neighbor in self.blocks.get(node, set()):
                if neighbor in reachable:
                    in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

        topo_queue = [n for n in reachable if in_degree[n] == 0]
        topo_order: list[str] = []
        while topo_queue:
            node = topo_queue.pop(0)
            topo_order.append(node)
            for neighbor in self.blocks.get(node, set()):
                if neighbor in reachable:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        topo_queue.append(neighbor)

        for node in topo_order:
            for neighbor in self.blocks.get(node, set()):
                if neighbor in reachable:
                    new_dist = dist.get(node, 0) + 1
                    if new_dist > dist.get(neighbor, -1):
                        dist[neighbor] = new_dist
                        prev[neighbor] = node

        # Reconstruct path
        path: list[str] = []
        current: Optional[str] = end_id
        while current is not None:
            path.append(current)
            current = prev.get(current)
        path.reverse()
        return path if path[0] == start_id else None
```

In production, Luna augments this with incremental cycle detection — maintaining auxiliary data structures that make `would_create_cycle` O(depth of affected subgraph) rather than O(total graph size) by tracking reachability sets per node.

**Interview implication:** "Design a task management system" is one of the most common systems design questions. The cycle detection problem is an excellent hook for demonstrating graph algorithm knowledge in a product context. Show the interviewer you understand that the naive DFS is correct but that production requires incremental computation — you cannot afford a full graph scan on every new dependency edge at Asana's scale.

## The NUX Protocol: Real-Time Sync Across Clients

Asana's real-time sync layer uses a protocol they call **NUX** (Network Update Exchange), built on top of WebSockets. NUX is not a standard pub/sub system — it is designed specifically for the consistency requirements of a shared mutable graph.

NUX operates on a **delta log** model. Every mutation to the workspace graph generates a typed delta record. These delta records are:

1. **Sequenced**: Each delta has a monotonically increasing sequence number per workspace.
2. **Idempotent**: Applying the same delta twice produces the same result — critical for at-least-once delivery semantics.
3. **Self-describing**: A delta includes enough context to apply it without needing to fetch related state (the delta for "assign user X to task Y" includes both the task ID and the user's display data).

When a client reconnects after a gap (browser tab restored, flaky connection), it sends its last-seen sequence number. The server replays all deltas from that point forward. For long disconnections where the delta log has been compacted, the server sends a full snapshot of the workspace subgraph the client subscribes to, then continues with deltas.

The subscription model is workspace-scoped but filtered. Asana clients subscribe to a **view** — "all tasks in Project P that match these filters" — not to the entire workspace. The server maintains a subscription registry and evaluates each outgoing delta against active subscriptions to determine delivery targets. This filtering happens in memory inside Luna, where the full graph is already resident.

## Mobile Architecture: Offline-First with Conflict Resolution

Asana's mobile app is offline-first. Creating a task, updating a field, or completing a task queues a local mutation immediately and syncs when connectivity is restored. This design choice means the app is always responsive, but it introduces conflict resolution complexity.

The conflict resolution strategy is operation-type-aware:

- **Last-Write-Wins** for scalar properties (task name, description, due date). The device timestamp with a logical clock tiebreak determines the winner.
- **Union semantics** for set-valued properties (tags, assignees): concurrent additions by two offline clients both survive; concurrent removals are handled with CRDT tombstone semantics.
- **Ordered merge** for section membership: the server maintains authoritative ordering; client reorderings that conflict are resolved by rebasing the client's local ordering delta onto the server's current ordering.

The mobile client maintains a **local SQLite database** that mirrors the server-side Luna graph schema. Mutations are first written to a pending queue in SQLite, applied optimistically to the local cache (the UI updates immediately), then sent to the server. On server acknowledgment, the pending record is cleared. On conflict rejection, the client receives the server's canonical state and rolls back the local optimistic update.

**Interview implication:** Offline-first sync with conflict resolution is a common mobile systems design question. The key is showing that there is no single conflict resolution strategy — you choose LWW, CRDT, or server-wins per operation type based on what losing the conflict means to the user. A lost task name edit is annoying but recoverable; a lost "mark complete" on a recurring task could silently drop work. Product semantics drive the technical choice.

## Scale: Billions of Tasks, Trillions of Edges

Asana has stated that their graph contains hundreds of billions of objects. At this scale, a single Luna instance cannot hold everything in memory. Asana's architecture shards workspaces across Luna instances, with each instance owning a subset of workspaces.

This means cross-workspace operations (linking a task to a goal in a different workspace, or portfolio views spanning multiple teams) require cross-shard coordination. Asana handles this with a **federated query layer** that fans out read requests to the relevant Luna shards and aggregates results. Write operations that span shards use a two-phase approach: write to the primary shard, then propagate the edge reference to the secondary shard.

The graph's edge density creates interesting indexing challenges. Asana's "workload" views (all tasks assigned to a user across all projects) require efficient inverted indices maintained inside Luna as first-class data structures rather than computed at query time.

## Key Takeaways for Asana Interviews

1. **Graph modeling**: When you see a domain with many-to-many relationships and dependency semantics (tasks, projects, users, goals), think graph database first. Understand the trade-off — in-memory graphs give fast traversals at the cost of RAM and sharding complexity.

2. **Cycle detection**: Know DFS-based cycle detection and be ready to discuss why the naive approach doesn't scale. Incremental reachability maintenance is the production pattern.

3. **Real-time sync**: The delta log + sequence number + client-side replay pattern is a common correct answer for "how do you keep millions of clients consistent." The details are in what happens at reconnection and during subscription filtering.

4. **Offline-first**: Show interviewers you understand that offline-first is not "sync when online" — it requires a conflict resolution strategy designed around the semantics of each operation type.

5. **Systems design question**: For "design a task management system," structure your answer around: data model (graph), write path (mutation queue, WAL), read path (in-memory graph, views), real-time sync (delta log + WebSockets), and scale (workspace sharding). That framing shows architectural completeness.

Asana is a company that has made deep technical investments in infrastructure most engineers never encounter. Demonstrating familiarity with those choices — even at a conceptual level — signals that you think at the infrastructure layer, not just the feature layer.
