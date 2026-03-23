---
title: "Graph Algorithms Interview Guide: BFS, DFS, Dijkstra, and Topological Sort"
description: "Complete guide to graph algorithms for coding interviews — BFS, DFS, shortest paths, cycle detection, topological sort, union-find, and when to use each."
date: "2026-03-20"
category: "Algorithms"
---

# Graph Algorithms Interview Guide: BFS, DFS, Dijkstra, and Topological Sort

Graph problems are ubiquitous in senior engineering interviews. Unlike tree problems where the structure is fixed, graph problems require you to recognize the right algorithm from the problem description — and interviewers specifically test whether you can make that selection quickly and correctly.

## Representing Graphs

Before algorithms, representation. Two options:

**Adjacency list:** `graph = defaultdict(list)`. Add edge: `graph[u].append(v)`. Space O(V + E). Efficient for sparse graphs (most interview problems). Iterate neighbors: `for neighbor in graph[node]`.

**Adjacency matrix:** `matrix[i][j] = 1`. Space O(V²). Efficient for dense graphs and quick edge existence checks. Rarely optimal for interview problems.

## BFS: Shortest Path in Unweighted Graphs

BFS explores nodes level by level. Critical property: the first time BFS reaches a node, it's via the shortest path (in terms of edges). Use BFS for:
- Shortest path in unweighted graphs
- Level-order traversal
- Finding all nodes within K hops

```python
from collections import deque

def bfs(graph, start, end):
    visited = {start}
    queue = deque([(start, 0)])  # (node, distance)
    
    while queue:
        node, dist = queue.popleft()
        if node == end:
            return dist
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))
    
    return -1  # unreachable
```

## DFS: Connectivity, Cycle Detection, and Component Labeling

DFS goes deep before backtracking. Use DFS for:
- Checking connectivity
- Detecting cycles
- Topological sort (iterative or recursive)
- Finding connected components
- Path existence (not shortest path)

```python
def dfs(graph, node, visited):
    visited.add(node)
    for neighbor in graph[node]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)
```

**Cycle detection in directed graphs:** Track nodes in the current recursion path ("gray" nodes) vs. fully explored ("black"). If DFS reaches a gray node, there's a cycle.

```python
def has_cycle(graph, node, color):
    color[node] = 'gray'
    for neighbor in graph[node]:
        if color[neighbor] == 'gray':
            return True
        if color[neighbor] == 'white' and has_cycle(graph, neighbor, color):
            return True
    color[node] = 'black'
    return False
```

## Dijkstra: Shortest Path with Weights

When edges have non-negative weights, BFS no longer gives shortest paths. Dijkstra's algorithm uses a min-heap to always expand the cheapest unvisited node.

```python
import heapq

def dijkstra(graph, start):
    dist = {start: 0}
    heap = [(0, start)]  # (distance, node)
    
    while heap:
        d, node = heapq.heappop(heap)
        if d > dist.get(node, float('inf')):
            continue  # stale entry
        for neighbor, weight in graph[node]:
            new_dist = d + weight
            if new_dist < dist.get(neighbor, float('inf')):
                dist[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))
    
    return dist
```

Time: O((V + E) log V). Does not work with negative weights — use Bellman-Ford instead.

## Topological Sort

Topological sort orders nodes of a DAG such that for every edge u→v, u comes before v. Used for dependency resolution, build systems, course prerequisites.

**Kahn's algorithm (BFS-based):** Repeatedly remove nodes with in-degree 0.

```python
from collections import deque

def topological_sort(graph, n):
    in_degree = [0] * n
    for u in range(n):
        for v in graph[u]:
            in_degree[v] += 1
    
    queue = deque([i for i in range(n) if in_degree[i] == 0])
    order = []
    
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return order if len(order) == n else []  # empty = cycle exists
```

## Union-Find: Connected Components and Cycle Detection

Union-Find (Disjoint Set Union) efficiently answers: "are these two nodes connected?" and "connect these two nodes."

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # path compression
        return self.parent[x]
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False  # already connected — adding edge creates cycle
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        return True
```

With path compression and union by rank, both operations are nearly O(1) amortized (O(α(n))).

## Algorithm Selection Cheat Sheet

| Problem type | Algorithm |
|---|---|
| Shortest path, unweighted | BFS |
| Shortest path, non-negative weights | Dijkstra |
| Shortest path, negative weights | Bellman-Ford |
| All-pairs shortest path | Floyd-Warshall |
| Connectivity, components | DFS or BFS |
| Cycle detection, directed | DFS with coloring |
| Cycle detection, undirected | Union-Find |
| Topological order | Kahn's or DFS |
| Minimum spanning tree | Kruskal (Union-Find) or Prim (heap) |

## Common Interview Mistakes

**Forgetting to mark nodes visited before adding to queue (BFS):** Mark when enqueued, not when dequeued — otherwise you'll add the same node multiple times.

**Using BFS for weighted shortest paths:** BFS only works when all edges have equal weight.

**Not handling disconnected graphs:** Always check if all nodes are reachable; iterate over all nodes as potential DFS/BFS starting points.

**Confusing directed and undirected cycle detection:** Undirected cycle: re-visiting any node (except parent) = cycle. Directed cycle: re-visiting a gray (in-progress) node = cycle.

Master these patterns and you can handle the vast majority of graph interview problems.

## Related Articles

- [Data Structures and Algorithms Interview Guide](/blog/data-structures-algorithms-interview-guide)
- [Advanced Dynamic Programming Guide](/blog/advanced-dynamic-programming-guide)
- [Data Structures and Algorithms Cheat Sheet](/blog/data-structures-algorithms-cheat-sheet)
- [Meta Engineering Deep Dive: Inside the Technical Bar](/blog/meta-engineering-deep-dive)
- [System Design: Social Graph](/blog/system-design-social-graph)
