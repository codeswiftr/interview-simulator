---
title: "Graph Shortest Path Algorithms: The Complete Interview Guide"
description: "Master Dijkstra's algorithm, Bellman-Ford, Floyd-Warshall, BFS for unweighted graphs, and an intro to A* — with interview patterns and when to use each."
date: "2026-03-20"
category: "Algorithms"
---

Shortest path problems are among the most frequently tested graph topics in technical interviews. They appear not just as explicit "find the shortest path" problems but embedded inside network flow, dependency resolution, and optimization problems. Knowing which algorithm to reach for — and why — separates candidates who pattern-match from candidates who genuinely understand graphs.

## BFS for Unweighted Graphs

Before reaching for a heavyweight algorithm, recognize that if all edges have equal weight (or weight 1), BFS gives you the shortest path in O(V + E) time with minimal code.

```python
from collections import deque

def bfs_shortest_path(graph, start, end):
    queue = deque([(start, [start])])
    visited = {start}
    while queue:
        node, path = queue.popleft()
        if node == end:
            return path
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return []
```

**When to use:** Grid problems (find shortest path in maze), word ladder, minimum steps problems. The key insight: if you can model the problem as a graph where each edge costs 1, BFS is always your first choice.

## Dijkstra's Algorithm

For weighted graphs with non-negative edges, Dijkstra's is the standard. The core insight: always process the node with the current shortest known distance first.

```python
import heapq

def dijkstra(graph, start):
    # graph[u] = [(weight, v), ...]
    dist = {node: float('inf') for node in graph}
    dist[start] = 0
    heap = [(0, start)]  # (distance, node)

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue  # stale entry
        for weight, v in graph[u]:
            if dist[u] + weight < dist[v]:
                dist[v] = dist[u] + weight
                heapq.heappush(heap, (dist[v], v))
    return dist
```

**Time complexity:** O((V + E) log V) with a binary heap. **Space:** O(V).

**Interview tip:** The `if d > dist[u]: continue` check handles stale heap entries without needing a visited set. Many candidates miss this, leading to incorrect implementations.

**Classic interview problems that reduce to Dijkstra:**
- Network Delay Time (LeetCode 743)
- Cheapest Flights Within K Stops (modified Dijkstra with state)
- Path with Minimum Effort (grid Dijkstra)

**Negative edges:** Dijkstra breaks with negative edges because the greedy assumption — once a node is settled, its distance is final — is violated. Use Bellman-Ford instead.

## Bellman-Ford Algorithm

Bellman-Ford handles negative edge weights and can detect negative cycles. The approach: relax all edges V-1 times.

```python
def bellman_ford(vertices, edges, start):
    # edges = [(u, v, weight), ...]
    dist = {v: float('inf') for v in range(vertices)}
    dist[start] = 0

    for _ in range(vertices - 1):
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w

    # Check for negative cycles
    for u, v, w in edges:
        if dist[u] + w < dist[v]:
            return None  # negative cycle detected

    return dist
```

**Time complexity:** O(V * E). Slower than Dijkstra, but handles negative weights.

**Why V-1 iterations?** A shortest path in a graph with V nodes has at most V-1 edges. After V-1 relaxation passes, all shortest paths are finalized — unless a negative cycle exists, in which case distances keep decreasing.

**Interview appearance:** The "Cheapest Flights Within K Stops" problem is Bellman-Ford with a twist (limit the number of relaxation rounds to K).

## Floyd-Warshall: All-Pairs Shortest Path

When you need shortest paths between every pair of nodes, Floyd-Warshall computes all of them at once using dynamic programming.

```python
def floyd_warshall(n, edges):
    # Initialize distance matrix
    dist = [[float('inf')] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
    for u, v, w in edges:
        dist[u][v] = w

    for k in range(n):          # intermediate node
        for i in range(n):      # source
            for j in range(n):  # destination
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]

    return dist
```

**Time complexity:** O(V³). **Space:** O(V²).

**The key insight:** `dist[i][j]` after considering intermediate nodes `{0, 1, ..., k}` is either the path not using `k`, or the best path through `k`. The triple nested loop evaluates this for all (i, j) pairs.

**When interviewers ask for Floyd-Warshall:** Dense graphs where you need all-pairs distances, or when V is small (< 500) and simplicity of implementation is valued. Find the City With the Smallest Number of Neighbors (LeetCode 1334) is a classic application.

## A* Algorithm: Informed Search

A* extends Dijkstra by adding a heuristic — an estimate of remaining distance to the goal. It is not always tested in standard interviews but appears in game development, robotics, and specialized algorithm roles.

```python
# f(n) = g(n) + h(n)
# g(n) = actual cost from start to n
# h(n) = heuristic estimate from n to goal (must be admissible: never overestimate)

import heapq

def a_star(graph, start, goal, heuristic):
    open_set = [(heuristic(start, goal), 0, start)]
    g_score = {start: 0}

    while open_set:
        f, g, current = heapq.heappop(open_set)
        if current == goal:
            return g
        for weight, neighbor in graph[current]:
            new_g = g + weight
            if new_g < g_score.get(neighbor, float('inf')):
                g_score[neighbor] = new_g
                f_score = new_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score, new_g, neighbor))
    return float('inf')
```

For grid problems, Manhattan distance (`|x1-x2| + |y1-y2|`) is the canonical admissible heuristic.

## Choosing the Right Algorithm

| Scenario | Algorithm |
|----------|-----------|
| Unweighted graph, single source | BFS |
| Weighted, non-negative, single source | Dijkstra |
| Negative edge weights possible | Bellman-Ford |
| All-pairs shortest path needed | Floyd-Warshall |
| Heuristic available, goal-directed | A* |

The ability to quickly identify which algorithm applies — and articulate *why* the others don't — is what interviewers at top companies are testing. An answer that starts with "I'd use Dijkstra because..." is dramatically stronger than one that jumps straight into code.
