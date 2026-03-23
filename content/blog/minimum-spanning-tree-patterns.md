---
title: "Minimum Spanning Tree Patterns: Kruskal, Prim & Interview Variants"
date: 2026-03-21
excerpt: "Master MST algorithms for interview success—Kruskal, Prim, and problem variants like bottleneck spanning tree."
tags: [algorithms, graph-theory, minimum-spanning-tree, kruskal, prim, interview-prep]
---

# Minimum Spanning Tree Patterns: Kruskal, Prim & Interview Variants

Minimum Spanning Tree (MST) questions test your understanding of greedy algorithms and graph properties. Two classic algorithms dominate interviews: Kruskal's and Prim's.

## The Problem

Given a connected, undirected graph with weighted edges, find a subset of edges that:
1. Connects all vertices
2. Has minimum total weight
3. Contains no cycles

## Kruskal's Algorithm

Greedy approach: sort edges by weight, add each if it doesn't create a cycle. Use Union-Find for cycle detection.

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
            return False
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        return True

def kruskal(n, edges):
    edges.sort(key=lambda e: e[2])  # Sort by weight
    uf = UnionFind(n)
    mst = []
    total_weight = 0
    
    for u, v, w in edges:
        if uf.union(u, v):
            mst.append((u, v, w))
            total_weight += w
            if len(mst) == n - 1:
                break
    
    return mst, total_weight
```

## Prim's Algorithm

Grow the MST from a starting vertex, always adding the minimum-weight edge to a new vertex.

```python
import heapq

def prim(n, graph):
    # graph[u] = [(v, weight), ...]
    mst = []
    total_weight = 0
    visited = [False] * n
    min_heap = [(0, 0, -1)]  # (weight, vertex, parent)
    
    while min_heap and len(mst) < n - 1:
        weight, u, parent = heapq.heappop(min_heap)
        if visited[u]:
            continue
        visited[u] = True
        if parent != -1:
            mst.append((parent, u, weight))
            total_weight += weight
        
        for v, w in graph[u]:
            if not visited[v]:
                heapq.heappush(min_heap, (w, v, u))
    
    return mst, total_weight
```

## Interview Variants

### Bottleneck Spanning Tree
Find the MST that minimizes the maximum edge weight. The MST itself is a bottleneck spanning tree.

### Minimum Spanning Forest
For disconnected graphs, find MST for each component.

### Second-Best MST
Find the spanning tree with second-minimum total weight:

```python
def second_best_mst(n, edges):
    mst, best = kruskal(n, edges)
    second_best = float('inf')
    
    for excluded_edge in mst:
        # Find MST without this edge
        temp_edges = [e for e in edges if e != excluded_edge]
        uf = UnionFind(n)
        weight = 0
        count = 0
        for u, v, w in temp_edges:
            if uf.union(u, v):
                weight += w
                count += 1
        if count == n - 1:
            second_best = min(second_best, weight)
    
    return second_best
```

### Maximum Spanning Tree
Negate all weights and run standard MST algorithm.

## Interview Tips

1. **Choose the right algorithm.** Kruskal is better for sparse graphs (edge list), Prim for dense graphs (adjacency matrix).

2. **Know the properties.** Cycle property (heaviest edge on a cycle is never in MST), cut property (lightest edge crossing a cut is in some MST).

3. **Common follow-ups:** "How would you handle online edge additions?" "What about dynamic graphs?"

4. **Real applications.** Network design, clustering, image segmentation.

## Time Complexity

- Kruskal: O(E log E) or O(E α(V)) with sorted edges
- Prim with binary heap: O(E log V)
- Prim with Fibonacci heap: O(E + V log V)
