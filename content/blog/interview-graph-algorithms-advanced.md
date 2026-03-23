---
title: "Advanced Graph Algorithms: Dijkstra, Bellman-Ford, Floyd-Warshall, and Network Flow"
description: "A rigorous guide to advanced graph algorithms for software engineering interviews — covering shortest path algorithms, their trade-offs, network flow, and the problem patterns where each algorithm applies."
date: "2026-03-20"
category: "Algorithms"
---

# Advanced Graph Algorithms: Dijkstra, Bellman-Ford, Floyd-Warshall, and Network Flow

Graph algorithms appear in interviews more often than any other advanced topic. The challenge isn't learning the algorithms in isolation — it's knowing which algorithm solves which problem, understanding why, and implementing correctly under pressure. This guide covers the four most interview-relevant advanced graph algorithms with the depth needed to actually use them.

## Dijkstra's Algorithm

**What it solves:** Single-source shortest paths in graphs with non-negative edge weights.

**Core idea:** Greedily expand the nearest unvisited node. Use a min-heap (priority queue) to always process the node with the currently known shortest distance.

```python
import heapq
from collections import defaultdict

def dijkstra(graph: dict, start: int) -> dict:
    """
    graph: {node: [(neighbor, weight), ...]}
    Returns: {node: shortest_distance_from_start}
    """
    distances = defaultdict(lambda: float('inf'))
    distances[start] = 0
    heap = [(0, start)]  # (distance, node)
    visited = set()
    
    while heap:
        dist, node = heapq.heappop(heap)
        
        if node in visited:
            continue
        visited.add(node)
        
        for neighbor, weight in graph[node]:
            new_dist = dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))
    
    return dict(distances)
```

**Time complexity:** O((V + E) log V) with a binary heap. O(E + V log V) with a Fibonacci heap (theoretical; rarely implemented in practice).

**The critical constraint:** Edge weights must be non-negative. Why? Dijkstra's greedy assumption is that when you pop a node from the heap, you've found its shortest path. With negative edges, a longer path could have a large negative edge that makes it shorter — violating this assumption.

**When Dijkstra appears in interviews:**
- Navigation/routing problems ("find shortest path from A to B")
- Network latency problems ("minimum latency path")
- Any problem with weighted connections where you need cheapest path

**Common mistakes:**
1. Forgetting the `visited` check — leads to O(E²) worst case
2. Using Dijkstra when negative edges exist — use Bellman-Ford instead
3. Off-by-one in initialization (distances should start at infinity, not 0)

## Bellman-Ford Algorithm

**What it solves:** Single-source shortest paths with possible negative edges; also detects negative cycles.

**Core idea:** Relax all edges V-1 times. Each iteration guarantees shortest paths of at most k edges (where k is the iteration count). A V-th relaxation pass detects negative cycles.

```python
def bellman_ford(edges: list, num_vertices: int, start: int) -> tuple:
    """
    edges: [(from, to, weight), ...]
    Returns: (distances dict, has_negative_cycle bool)
    """
    distances = {i: float('inf') for i in range(num_vertices)}
    distances[start] = 0
    
    # Relax V-1 times
    for _ in range(num_vertices - 1):
        updated = False
        for u, v, w in edges:
            if distances[u] != float('inf') and distances[u] + w < distances[v]:
                distances[v] = distances[u] + w
                updated = True
        if not updated:  # Early termination optimization
            break
    
    # Check for negative cycles (V-th relaxation)
    has_negative_cycle = False
    for u, v, w in edges:
        if distances[u] != float('inf') and distances[u] + w < distances[v]:
            has_negative_cycle = True
            break
    
    return distances, has_negative_cycle
```

**Time complexity:** O(V × E) — significantly slower than Dijkstra for large graphs without negative edges.

**When to use Bellman-Ford over Dijkstra:**
- Currency arbitrage problems (exchange rates create negative-weight cycle potential)
- Game mechanics with negative-cost paths
- Any problem that explicitly mentions negative weights or asks you to detect negative cycles

**Interview insight:** When an interviewer presents a graph problem and mentions "weights can be negative," they're signaling Bellman-Ford. Recognizing this immediately is a positive signal.

## Floyd-Warshall Algorithm

**What it solves:** All-pairs shortest paths — shortest path between every pair of vertices.

**Core idea:** Dynamic programming. For every pair (i, j), consider whether routing through intermediate vertex k gives a shorter path than the current best.

```python
def floyd_warshall(n: int, edges: list) -> list:
    """
    n: number of vertices (0-indexed)
    edges: [(from, to, weight), ...]
    Returns: dist[i][j] = shortest path from i to j (inf if unreachable)
    """
    INF = float('inf')
    dist = [[INF] * n for _ in range(n)]
    
    # Distance from node to itself is 0
    for i in range(n):
        dist[i][i] = 0
    
    # Initialize direct edges
    for u, v, w in edges:
        dist[u][v] = min(dist[u][v], w)  # Handle parallel edges
    
    # Relax through each intermediate vertex k
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    
    # Check for negative cycles (dist[i][i] < 0)
    for i in range(n):
        if dist[i][i] < 0:
            raise ValueError(f"Negative cycle detected involving vertex {i}")
    
    return dist
```

**Time complexity:** O(V³). Space: O(V²).

**When Floyd-Warshall is the right choice:**
- Dense graphs where you need all-pairs paths (running Dijkstra V times is O(V × E log V) — for dense graphs E ≈ V², so Floyd-Warshall's O(V³) is comparable)
- Problems asking "is vertex i reachable from vertex j for all pairs?"
- Transitive closure (replace min with OR operation)

**Classic interview problem:** "Find all pairs of cities with no path between them" — Floyd-Warshall, then check for INF in dist matrix.

## Network Flow: Max Flow / Min Cut

**What it solves:** Maximum flow through a capacity-constrained network from a source to a sink.

**The Max-Flow Min-Cut theorem:** Maximum flow = Minimum cut capacity. This duality is powerful: many problems that look like flow problems are actually cut problems and vice versa.

**Ford-Fulkerson with BFS (Edmonds-Karp):**

```python
from collections import deque

def bfs_find_path(graph: dict, source: int, sink: int, parent: dict) -> bool:
    """BFS to find augmenting path in residual graph"""
    visited = {source}
    queue = deque([source])
    
    while queue:
        u = queue.popleft()
        for v in graph[u]:
            if v not in visited and graph[u][v] > 0:  # residual capacity > 0
                visited.add(v)
                parent[v] = u
                if v == sink:
                    return True
                queue.append(v)
    return False

def max_flow(graph: dict, source: int, sink: int) -> int:
    """
    graph: {u: {v: capacity}} — will be modified (residual graph)
    Ensure reverse edges exist: graph[v][u] = 0 initially
    """
    total_flow = 0
    
    while True:
        parent = {}
        if not bfs_find_path(graph, source, sink, parent):
            break  # No augmenting path found
        
        # Find min residual capacity along the path
        path_flow = float('inf')
        v = sink
        while v != source:
            u = parent[v]
            path_flow = min(path_flow, graph[u][v])
            v = u
        
        # Update residual capacities
        v = sink
        while v != source:
            u = parent[v]
            graph[u][v] -= path_flow
            graph[v][u] += path_flow  # Reverse edge
            v = u
        
        total_flow += path_flow
    
    return total_flow
```

**Time complexity:** O(V × E²) for Edmonds-Karp. For most interview problems this is sufficient.

**The residual graph concept is critical.** When you send flow along an edge, you add capacity back on the reverse edge. This allows the algorithm to "undo" suboptimal decisions. Without residual edges, Ford-Fulkerson is incomplete.

**Problems that reduce to max flow:**
- Bipartite matching (classic: job assignments, hospital-doctor matching)
- Image segmentation (min-cut separates foreground/background)
- Escape routes: "Can k people escape a burning building simultaneously?" — max flow ≤ k?
- Baseball elimination (surprisingly, reducing to flow)

## Choosing the Right Algorithm

| Problem | Algorithm | Why |
|---------|-----------|-----|
| Single-source, non-negative weights | Dijkstra | O(E log V), fast |
| Single-source, negative weights | Bellman-Ford | Handles negatives |
| All-pairs shortest path | Floyd-Warshall | O(V³), simple to implement |
| Maximum flow / bipartite matching | Edmonds-Karp | General network flow |
| Unweighted shortest path | BFS | O(V+E), simplest |
| Detect negative cycles | Bellman-Ford | V-th relaxation check |

## Common Interview Patterns

**"Find shortest path with constraint"** — Dijkstra with modified state. Example: shortest path with at most k stops → state is (node, stops_used), heap contains (cost, node, stops).

**"Can we split the graph into two groups?"** — Min cut / Bipartite check. BFS/DFS coloring for bipartite; max-flow for capacity-constrained cuts.

**"N workers, M tasks, can all tasks be assigned?"** — Bipartite matching via max flow.

**Negative weights as a red flag:** In interviews, negative weights almost always signal either Bellman-Ford or a problem that can be transformed (e.g., add a constant to all weights, use Johnson's algorithm for all-pairs with negative weights on sparse graphs).

The pattern-matching skill — seeing "negative weights" → Bellman-Ford, seeing "all pairs" → Floyd-Warshall, seeing "matching/assignment" → max flow — is what interviewers are testing. The implementation follows from recognizing the right algorithm.
