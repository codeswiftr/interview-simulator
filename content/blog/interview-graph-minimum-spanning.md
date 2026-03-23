---
title: "Minimum Spanning Tree: Kruskal, Prim, and Interview Applications"
description: "MST algorithms for coding interviews — Kruskal's with Union-Find, Prim's with priority queue, when to use each, and the interview problems that reduce to MST."
date: "2026-03-20"
category: "Algorithms"
---

# Minimum Spanning Tree: Kruskal, Prim, and Interview Applications

Minimum spanning tree problems appear at senior-level interviews and in systems design contexts (network topology, cluster connections). Most engineers know the concept but can't implement Kruskal's or Prim's cleanly under pressure, or can't recognize when a problem reduces to MST. This guide closes that gap.

## What is a Minimum Spanning Tree?

Given a connected, undirected, weighted graph with n nodes and m edges, an MST is a spanning tree (n-1 edges connecting all nodes, no cycles) with the minimum total edge weight.

Key properties:
- An MST has exactly n-1 edges
- Every spanning tree of n nodes has n-1 edges
- For a graph with unique edge weights, the MST is unique
- Cut property: the minimum-weight edge crossing any cut (partition of nodes) must be in the MST

## Kruskal's Algorithm

**Idea:** Sort edges by weight. Add edges greedily if they don't create a cycle.

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False  # Same component — would create cycle
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        return True

def kruskal(n, edges):
    # edges: [(weight, u, v)]
    edges.sort()
    uf = UnionFind(n)
    mst_weight = 0
    mst_edges = []

    for weight, u, v in edges:
        if uf.union(u, v):
            mst_weight += weight
            mst_edges.append((u, v, weight))
            if len(mst_edges) == n - 1:
                break

    return mst_weight, mst_edges
```

**Time:** O(m log m) for sorting + O(m α(n)) for Union-Find operations ≈ O(m log m).

**When to use:** Sparse graphs (m ≈ n). Works naturally when edges are given explicitly as a list. Easy to implement correctly under pressure.

## Prim's Algorithm

**Idea:** Grow the MST from a starting node. Always add the minimum-weight edge connecting the current tree to a non-tree node.

```python
import heapq

def prim(n, adjacency):
    # adjacency[u] = [(weight, v), ...]
    visited = set()
    min_heap = [(0, 0)]  # (weight, node), start from node 0
    total_weight = 0

    while min_heap and len(visited) < n:
        weight, node = heapq.heappop(min_heap)
        if node in visited:
            continue
        visited.add(node)
        total_weight += weight

        for next_weight, neighbor in adjacency[node]:
            if neighbor not in visited:
                heapq.heappush(min_heap, (next_weight, neighbor))

    return total_weight if len(visited) == n else -1  # -1 if disconnected
```

**Time:** O((n + m) log n) with a binary heap. O(m + n log n) with a Fibonacci heap (rarely needed in interviews).

**When to use:** Dense graphs (m ≈ n²) — Prim's with an adjacency list performs better. Also natural when you're building the MST incrementally from a source.

## Kruskal vs. Prim: When to Choose

| Scenario | Use |
|----------|-----|
| Edges given as a list | Kruskal — sort and process |
| Dense graph (many edges) | Prim — O(m log n) beats Kruskal's O(m log m) |
| Need to detect cycles anyway | Kruskal — Union-Find handles it |
| Add nodes one at a time | Prim — naturally extends |
| Parallel edges or multigraph | Kruskal — straightforward |

In interviews, Kruskal's is usually easier to implement correctly and is the default choice unless the problem structure clearly favors Prim's.

## Interview Problem: Minimum Cost to Connect All Points

**LeetCode 1584.** Given n points, connect all points with the minimum total Manhattan distance.

This is directly an MST problem. Each pair of points is a potential edge; the weight is Manhattan distance. Use Kruskal's (generate all edges, sort, apply Union-Find) or Prim's (use a greedy expansion).

```python
def minCostConnectPoints(points):
    n = len(points)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            dist = abs(points[i][0] - points[j][0]) + abs(points[i][1] - points[j][1])
            edges.append((dist, i, j))

    edges.sort()
    uf = UnionFind(n)
    cost = 0
    count = 0

    for dist, i, j in edges:
        if uf.union(i, j):
            cost += dist
            count += 1
            if count == n - 1:
                break

    return cost
```

O(n² log n) — quadratic edges for n points, but this is expected and optimal for this problem class.

## Interview Problem: Network Delay Time (Dijkstra, not MST)

A common mistake: "find minimum cost to reach all nodes" sounds like MST but is actually a single-source shortest path problem (Dijkstra's). MST minimizes total edge weight of the tree; Dijkstra minimizes path cost from a source.

**When is it MST?** "Connect all nodes" — you're building a tree, not routing. "Network design" — minimize cable/infrastructure cost.

**When is it Dijkstra/BFS?** "Shortest path from A to B" or "minimum time for a signal to reach all nodes" — you're finding paths, not building a tree.

## The Critical Difference

MST: minimize total weight of the structure that spans all nodes. You can use any edges, and the result is a tree.

Shortest paths: minimize the travel cost to reach destinations. The result is a set of paths, not necessarily a tree.

Always clarify which type before coding. The keywords: "connect," "infrastructure cost," "minimum spanning" → MST. "Fastest route," "delay," "distance from source" → shortest path.

## Complexity Summary

| Algorithm | Time | Space | Best for |
|-----------|------|-------|----------|
| Kruskal's | O(m log m) | O(n) | Sparse graphs, edge list input |
| Prim's (binary heap) | O(m log n) | O(n + m) | Dense graphs, adjacency list |
| Prim's (Fibonacci heap) | O(m + n log n) | O(n + m) | Theory; rarely in interviews |

For most interview problems, O(m log m) Kruskal's is the target complexity and the easier implementation to write under pressure.
