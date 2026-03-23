---
title: "Network Flow Algorithms: From Max Flow to Bipartite Matching"
date: 2026-03-21
excerpt: "Complete guide to network flow interview problems—Ford-Fulkerson, Edmonds-Karp, and real applications like bipartite matching."
tags: [algorithms, graph-theory, network-flow, max-flow, interview-prep]
---

# Network Flow Algorithms: From Max Flow to Bipartite Matching

Network flow problems appear in interviews disguised as resource allocation, matching, or path-finding challenges. Understanding max flow opens doors to solving these elegantly.

## The Problem

Given a directed graph with source s and sink t, each edge has a capacity. Find the maximum flow from s to t without violating capacity constraints.

## Ford-Fulkerson Method

The foundational approach uses augmenting paths—find any path from source to sink, push as much flow as possible, and repeat.

```python
def ford_fulkerson(graph, source, sink):
    def bfs(parent):
        visited = set([source])
        queue = [source]
        while queue:
            u = queue.pop(0)
            for v, cap in enumerate(graph[u]):
                if v not in visited and cap > 0:
                    visited.add(v)
                    parent[v] = u
                    queue.append(v)
        return sink in visited
    
    max_flow = 0
    parent = {}
    
    while bfs(parent):
        path_flow = float('inf')
        v = sink
        while v != source:
            u = parent[v]
            path_flow = min(path_flow, graph[u][v])
            v = u
        
        max_flow += path_flow
        v = sink
        while v != source:
            u = parent[v]
            graph[u][v] -= path_flow
            graph[v][u] += path_flow  # Residual edge
            v = u
    
    return max_flow
```

## Edmonds-Karp Algorithm

Ford-Fulkerson's worst case is unbounded for irrational capacities. Edmonds-Karp guarantees O(VE²) by always choosing the shortest augmenting path (BFS).

The implementation is nearly identical—just use BFS to find augmenting paths (as shown above).

## Dinic's Algorithm

For interviews demanding optimal solutions, Dinic's runs in O(V²E) and uses concepts of level graphs and blocking flows:

```python
def dinic(graph, source, sink):
    n = len(graph)
    level = [0] * n
    
    def bfs():
        nonlocal level
        level = [-1] * n
        level[source] = 0
        queue = [source]
        while queue:
            u = queue.pop(0)
            for v in range(n):
                if level[v] < 0 and graph[u][v] > 0:
                    level[v] = level[u] + 1
                    queue.append(v)
        return level[sink] >= 0
    
    def dfs(u, flow):
        if u == sink:
            return flow
        for v in range(n):
            if level[v] == level[u] + 1 and graph[u][v] > 0:
                pushed = dfs(v, min(flow, graph[u][v]))
                if pushed:
                    graph[u][v] -= pushed
                    graph[v][u] += pushed
                    return pushed
        return 0
    
    max_flow = 0
    while bfs():
        while True:
            pushed = dfs(source, float('inf'))
            if not pushed:
                break
            max_flow += pushed
    return max_flow
```

## Bipartite Matching

Convert bipartite matching to max flow: add source connected to all left nodes, sink connected to all right nodes, all edges have capacity 1.

```python
def bipartite_matching(graph, left_size):
    # Graph is adjacency list, left nodes are 0..left_size-1
    n = len(graph) + 2
    source, sink = len(graph), len(graph) + 1
    
    # Build flow network
    flow_graph = [[0] * n for _ in range(n)]
    for u in range(left_size):
        flow_graph[source][u] = 1
    for u in range(left_size):
        for v in graph[u]:
            flow_graph[u][v] = 1
    for v in range(left_size, len(graph)):
        flow_graph[v][sink] = 1
    
    return ford_fulkerson(flow_graph, source, sink)
```

## Min-Cut

The minimum s-t cut has capacity equal to max flow (max-flow min-cut theorem). Find it by locating all nodes reachable from source in the residual graph.

## Interview Tips

1. **Model the problem.** Most interview questions don't mention "flow"—they describe resource allocation, assignment, or capacity constraints.

2. **Choose the right algorithm.** Edmonds-Karp is usually sufficient for interviews; mention Dinic's if asked for optimal complexity.

3. **Common variations:** Multi-source/sink (add super source/sink), vertex capacities (split vertices into in/out edges), minimum cost flow (add Bellman-Ford for shortest augmenting path).
