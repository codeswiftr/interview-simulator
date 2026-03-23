---
title: "Advanced Graph Algorithms: Interview Patterns for Senior Engineers"
description: "Advanced graph problems for senior-level interviews — strongly connected components (Tarjan's, Kosaraju's), articulation points, bridges, Bellman-Ford for negative weights, and flow networks."
date: "2026-03-20"
category: "Algorithms"
---

# Advanced Graph Algorithms: Interview Patterns for Senior Engineers

Beyond BFS/DFS and Dijkstra's, senior engineer interviews test a second tier of graph algorithms: strongly connected components, bridges and articulation points, negative-weight shortest paths, and occasionally network flow. These appear less frequently than the basics but separate candidates who've studied algorithms seriously from those who haven't.

## Strongly Connected Components (SCCs)

An SCC is a maximal set of vertices such that every vertex is reachable from every other vertex. Practical uses: circular dependencies in build systems, network reliability, condensation of directed graphs.

**Kosaraju's Algorithm (two-pass DFS):**

Pass 1: Run DFS on the original graph, push nodes onto a stack in completion order.
Pass 2: Process nodes from the stack on the reversed graph. Each DFS tree is an SCC.

```python
def kosaraju(n, adj):
    # adj[u] = list of v where u → v
    rev = [[] for _ in range(n)]
    for u in range(n):
        for v in adj[u]:
            rev[v].append(u)

    visited = [False] * n
    order = []

    def dfs1(u):
        visited[u] = True
        for v in adj[u]:
            if not visited[v]:
                dfs1(v)
        order.append(u)

    for i in range(n):
        if not visited[i]:
            dfs1(i)

    visited = [False] * n
    sccs = []

    def dfs2(u, comp):
        visited[u] = True
        comp.append(u)
        for v in rev[u]:
            if not visited[v]:
                dfs2(v, comp)

    while order:
        u = order.pop()
        if not visited[u]:
            comp = []
            dfs2(u, comp)
            sccs.append(comp)

    return sccs
```

**Time:** O(V + E). **Tarjan's algorithm** finds SCCs in a single pass using a discovery time and low-link values — slightly more complex to implement but only one DFS.

## Bridges and Articulation Points

**Bridge:** An edge whose removal disconnects the graph.
**Articulation point:** A vertex whose removal disconnects the graph.

Both use a DFS with discovery times and low-link values. The low-link value of a node is the minimum discovery time reachable from its subtree (via any path, including back edges).

```python
def find_bridges(n, edges):
    adj = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    disc = [-1] * n
    low = [0] * n
    timer = [0]
    bridges = []

    def dfs(u, parent):
        disc[u] = low[u] = timer[0]
        timer[0] += 1

        for v in adj[u]:
            if disc[v] == -1:  # Tree edge
                dfs(v, u)
                low[u] = min(low[u], low[v])
                if low[v] > disc[u]:  # No back edge from v's subtree to u or above
                    bridges.append((u, v))
            elif v != parent:  # Back edge
                low[u] = min(low[u], disc[v])

    for i in range(n):
        if disc[i] == -1:
            dfs(i, -1)

    return bridges
```

**Articulation point criterion:** Node `u` is an articulation point if:
- It's the root of the DFS tree with 2+ children, OR
- It has a child `v` such that `low[v] >= disc[u]` (no back edge from v's subtree to u's ancestor)

## Bellman-Ford for Negative Weights

Dijkstra's fails with negative edge weights. Bellman-Ford handles them by relaxing all edges V-1 times.

```python
def bellman_ford(n, edges, src):
    # edges: [(u, v, weight)]
    dist = [float('inf')] * n
    dist[src] = 0

    for _ in range(n - 1):
        for u, v, w in edges:
            if dist[u] != float('inf') and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w

    # Check for negative cycles: if any edge can still be relaxed,
    # there's a negative cycle reachable from src
    for u, v, w in edges:
        if dist[u] != float('inf') and dist[u] + w < dist[v]:
            return None  # Negative cycle detected

    return dist
```

**Time:** O(V × E). **When to use:** Negative edge weights, detecting negative cycles (arbitrage detection, financial modeling).

## Floyd-Warshall: All-Pairs Shortest Paths

Find shortest paths between ALL pairs of nodes. O(V³) — only practical for dense graphs with V ≤ 1000.

```python
def floyd_warshall(n, weights):
    # weights[i][j] = edge weight, float('inf') if no edge
    dist = [row[:] for row in weights]

    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]

    return dist
```

Can detect negative cycles: if `dist[i][i] < 0` after completion, node `i` is part of a negative cycle.

## Topological Sort: Kahn's Algorithm (BFS-based)

An alternative to DFS-based topological sort. More intuitive for some and detects cycles naturally.

```python
def topological_sort_kahn(n, adj):
    in_degree = [0] * n
    for u in range(n):
        for v in adj[u]:
            in_degree[v] += 1

    queue = deque([i for i in range(n) if in_degree[i] == 0])
    order = []

    while queue:
        u = queue.popleft()
        order.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    if len(order) != n:
        return []  # Cycle detected — no valid topological order

    return order
```

**Cycle detection:** If the resulting order doesn't contain all n nodes, a cycle exists.

## Bipartite Check

A graph is bipartite if its nodes can be 2-colored such that no two adjacent nodes share a color. Equivalent to: contains no odd-length cycles.

```python
def is_bipartite(n, adj):
    color = [-1] * n

    def bfs(start):
        color[start] = 0
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if color[v] == -1:
                    color[v] = 1 - color[u]
                    queue.append(v)
                elif color[v] == color[u]:
                    return False  # Same color adjacent
        return True

    for i in range(n):
        if color[i] == -1:
            if not bfs(i):
                return False
    return True
```

## When These Appear in Interviews

- **SCCs:** Dependency analysis, detecting cycles in a directed graph, "course schedule" variants
- **Bridges/articulation points:** Network resilience ("which connection removal disconnects the network?")
- **Bellman-Ford:** Negative weights, arbitrage detection
- **Floyd-Warshall:** Small graphs, all-pairs queries
- **Kahn's:** Course schedule, build order, whenever topological sort is needed with cycle detection

At senior/staff level, expect to be able to derive these algorithms from their core invariants rather than purely recall them. Understanding *why* Kosaraju's works (the reverse graph reverses reachability) is more valuable than memorizing the implementation.
