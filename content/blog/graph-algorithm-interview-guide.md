---
title: "Graph Algorithm Interview Guide: DFS, BFS, and Advanced Graph Problems"
description: "Complete guide to graph algorithm interview questions — DFS, BFS, topological sort, shortest paths, union-find, and common graph problem patterns for technical interviews."
date: "2026-03-20"
category: "Algorithms"
---

# Graph Algorithm Interview Guide: DFS, BFS, and Advanced Graph Problems

Graph problems show up in nearly every senior engineering interview. They are deceptively approachable — most interviewers give you a problem that looks like a list or grid, and the insight you need is recognizing it as a graph problem at all. This guide walks through the full graph toolkit you need, from representations to advanced algorithms.

## Graph Representations: Adjacency List vs Matrix

The first decision in any graph problem is how to represent it. Most interview problems give you an edge list or a matrix — you translate that into whichever form your algorithm needs.

**Adjacency list** is the default choice. It is memory-efficient for sparse graphs (most real-world problems) and gives O(degree) neighbor iteration. Build it as a `dict` mapping each node to a list of its neighbors.

**Adjacency matrix** shines when you need O(1) edge existence checks or when the graph is dense. A 2D boolean array of size V×V. The tradeoff: O(V²) space regardless of edge count.

For grid problems (number of islands, walls and gates), the "graph" is implicit — each cell is a node, neighbors are the four cardinal directions. You do not need to build an explicit adjacency structure.

## DFS and BFS: When to Use Each

Both traversals visit every reachable node, but they explore in different orders and that order matters.

**DFS** goes deep before wide. Use it when you need to:
- Detect cycles (back edges in the recursion stack)
- Find connected components
- Compute topological order
- Explore all paths between two nodes

**BFS** explores level by level. Use it when you need to:
- Find the shortest path in an unweighted graph
- Find the minimum number of steps/moves
- Level-order traversal

The implementation difference is a stack (DFS, often via recursion) vs a queue (BFS). For iterative DFS, replace the queue with a stack. Mark nodes visited before you push them onto the queue (BFS) to avoid processing duplicates.

## Cycle Detection

For undirected graphs: during DFS, if you reach a neighbor that is already visited and is not the node you came from, there is a cycle.

For directed graphs: maintain a "currently in recursion stack" set alongside the visited set. A back edge (neighbor is in the recursion stack) signals a cycle. This pattern solves Course Schedule (LeetCode 207) directly.

## Topological Sort: Two Implementations

Topological sort orders nodes so that every directed edge u→v has u before v. It only exists for DAGs (directed acyclic graphs).

**Kahn's algorithm (BFS-based)**: compute in-degree for every node. Push all zero-in-degree nodes into a queue. Process the queue: pop a node, add it to the result, decrement the in-degree of its neighbors, push any that reach zero. If the result length equals the total node count, the graph is a DAG.

**DFS-based**: run DFS; when you fully finish a node (all its descendants are processed), prepend it to the result. Reverse the finish-time ordering gives topological order.

Kahn's is usually easier to explain in an interview and doubles as cycle detection (if you cannot process all nodes, a cycle exists).

## Shortest Paths: Dijkstra vs Bellman-Ford

**Dijkstra** works on graphs with non-negative edge weights. Use a min-heap (priority queue). Time complexity: O((V + E) log V). This is the right choice for 95% of weighted shortest-path interview problems.

**Bellman-Ford** handles negative edge weights and detects negative cycles. It relaxes all edges V−1 times: O(VE). Use it when the problem mentions negative weights or asks you to detect a negative cycle. Network delay time with negative costs is a classic trigger.

For unweighted graphs, BFS gives shortest paths in O(V + E) — no need for Dijkstra.

## Union-Find for Connectivity

Union-Find (Disjoint Set Union) answers "are these two nodes connected?" efficiently. The two operations:
- `find(x)`: return the root of x's component (with path compression)
- `union(x, y)`: merge x and y's components (with union by rank)

With both optimizations, operations run in near-constant amortized time. Use Union-Find when the problem asks about connected components, whether adding an edge creates a cycle, or the minimum spanning tree (Kruskal's algorithm).

## Common Interview Problem Patterns

**Islands problems** (Number of Islands, Max Area of Island): DFS/BFS from each unvisited land cell, mark the component visited, count components.

**Clone Graph**: BFS with a `visited` map from original node to cloned node. For each neighbor, clone if not yet seen, then add to the clone's adjacency list.

**Course Schedule (I and II)**: directed graph cycle detection (207) and topological sort (210). Kahn's algorithm handles both cleanly.

**Word Ladder**: BFS where each word is a node and edges connect words differing by one character. Use a set for O(1) lookup. The key insight: precompute all one-letter mutations rather than comparing every word pair.

**Dijkstra problems**: Network Delay Time, Cheapest Flights Within K Stops (with a twist: add a "stops" dimension to the state).

## Interview Execution Tips

State your graph representation choice and justify it before coding. Clarify whether the graph is directed, weighted, and whether it can contain cycles. Write your DFS/BFS helper cleanly with a visited set passed in. When the interviewer says "what if the graph is very large?" pivot to iterative DFS (no stack overflow risk) or discuss time/space complexity explicitly.

Most graph interview failures come from not handling disconnected components — always loop over all nodes as potential starting points, not just node 0.
