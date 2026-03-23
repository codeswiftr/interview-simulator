---
title: "Network Flow Algorithms: Max Flow, Min Cut, and Bipartite Matching"
description: "Network flow for senior engineering interviews — Ford-Fulkerson and Edmonds-Karp max flow, the max-flow min-cut theorem, bipartite matching as flow, and the surprisingly wide range of problems that reduce to flow."
date: "2026-03-20"
category: "Algorithms"
---

# Network Flow Algorithms: Max Flow, Min Cut, and Bipartite Matching

Network flow is a specialized but powerful algorithmic topic. Interviewers at companies with scheduling, matching, or resource allocation problems occasionally probe it. More commonly, it appears as a conceptual framework: recognizing that a problem can be modeled as a flow network unlocks an efficient solution that wouldn't be obvious otherwise.

## The Max Flow Problem

Given a directed graph with edge capacities, a source `s`, and a sink `t`, find the maximum flow from `s` to `t`. Each edge can carry up to its capacity; flow is conserved at intermediate nodes.

**Ford-Fulkerson:** Repeatedly find augmenting paths from `s` to `t` in the residual graph. An augmenting path's bottleneck capacity increases the total flow. Repeat until no augmenting path exists.

```python
from collections import defaultdict, deque

def bfs_augmenting_path(graph, source, sink, parent):
    visited = {source}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v, capacity in graph[u].items():
            if v not in visited and capacity > 0:
                visited.add(v)
                parent[v] = u
                if v == sink:
                    return True
                queue.append(v)
    return False

def edmonds_karp(graph, source, sink):
    # Edmonds-Karp: Ford-Fulkerson with BFS (guarantees O(VE^2))
    max_flow = 0
    while True:
        parent = {}
        if not bfs_augmenting_path(graph, source, sink, parent):
            break

        # Find bottleneck capacity along the augmenting path
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
            graph[v][u] += path_flow  # Reverse edge for residual graph
            v = u

        max_flow += path_flow

    return max_flow
```

**Residual graph:** The key concept. For each edge (u, v) with capacity c and current flow f, the residual graph has:
- Forward edge (u, v) with residual capacity c - f
- Backward edge (v, u) with capacity f (allows "undoing" flow)

This backward edge is what makes it possible to find augmenting paths that reroute flow through previously used edges.

## Max-Flow Min-Cut Theorem

The maximum flow equals the minimum cut capacity. A cut is a partition of vertices into two sets (one containing s, one containing t). The cut capacity is the total capacity of edges from the s-side to the t-side.

This theorem is useful in two ways:
1. **Proof of optimality:** When no augmenting path exists, we have maximum flow and minimum cut simultaneously
2. **Problem reduction:** Any problem asking for "minimum capacity that separates s from t" can be solved as max flow

## Bipartite Matching

Bipartite matching — assign items from set A to items from set B with one-to-one correspondence maximizing matches — reduces to max flow.

Create a source connected to all nodes in A (capacity 1), connect each A-node to compatible B-nodes (capacity 1), connect all B-nodes to sink (capacity 1). Max flow = max matching.

```python
def max_bipartite_matching(n_left, n_right, edges):
    # Build flow network
    # Nodes: 0=source, 1..n_left=left side, n_left+1..n_left+n_right=right side,
    #        n_left+n_right+1=sink
    source = 0
    sink = n_left + n_right + 1

    graph = defaultdict(lambda: defaultdict(int))

    for u in range(1, n_left + 1):
        graph[source][u] = 1

    for u, v in edges:
        graph[u][n_left + v] = 1

    for v in range(1, n_right + 1):
        graph[n_left + v][sink] = 1

    return edmonds_karp(graph, source, sink)
```

**Practical applications:**
- Task assignment (jobs → workers)
- Matching students to schools (admissions systems)
- Image segmentation (min-cut formulation)
- Network reliability analysis (minimum edge cut)

## When Flow Problems Appear in Interviews

Flow algorithms are tested rarely in pure form but the min-cut theorem and bipartite matching recognition appear more often:

**"Find the minimum number of edges/nodes to remove to disconnect the network"** → minimum cut, solved as max flow

**"Match N students to N projects, each with constraints"** → bipartite matching

**"What is the maximum number of edge-disjoint paths from s to t?"** → max flow where each edge has capacity 1

**"Minimum cost assignment problem"** → min-cost flow (extension of max flow)

The skill interviewers test is recognizing the reduction, not implementing the full algorithm from scratch. Saying "this is a bipartite matching problem, solvable with max flow in O(E√V)" is often sufficient at senior level.

## Complexity

| Algorithm | Time Complexity | Notes |
|-----------|----------------|-------|
| Ford-Fulkerson (DFS augmenting paths) | O(max_flow × E) | Slow for large flows |
| Edmonds-Karp (BFS augmenting paths) | O(VE²) | Polynomial, preferred |
| Dinic's algorithm | O(V²E) | Better for unit-capacity graphs |
| Bipartite matching (Hopcroft-Karp) | O(E√V) | Specialized for bipartite |

For competitive programming and interview contexts, Edmonds-Karp is the practical default. Dinic's is worth knowing for large dense graphs.
