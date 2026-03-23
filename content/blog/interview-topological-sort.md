---
title: "Topological Sort for Coding Interviews: Kahn's Algorithm, DFS, and Classic Problems"
description: "Complete guide to topological sort — Kahn's BFS algorithm, DFS-based approach, cycle detection, and how to solve Course Schedule I & II, alien dictionary, and dependency problems."
date: "2026-03-20"
category: "Algorithms"
---

Topological sort is one of those algorithms that shows up disguised as many different interview problems. Course prerequisites, build systems, task scheduling, package dependency resolution — whenever you have a directed acyclic graph (DAG) and need to process nodes in dependency order, you need topological sort. Mastering both standard approaches gives you the flexibility to handle any variation an interviewer throws at you.

## What Is Topological Sort?

A topological ordering of a directed graph is a linear ordering of its vertices such that for every directed edge (u → v), vertex u appears before v. This ordering only exists for DAGs — if a cycle is present, no valid topological order can exist.

A graph can have multiple valid topological orderings. For example, in a graph where A → C and B → C, both [A, B, C] and [B, A, C] are valid.

## Kahn's Algorithm (BFS-based)

Kahn's algorithm uses in-degree tracking to process nodes in topological order. The intuition: nodes with no incoming edges (in-degree 0) can always come first in any valid ordering.

```python
from collections import deque

def topological_sort_kahn(num_nodes, edges):
    # Build adjacency list and in-degree count
    adj = [[] for _ in range(num_nodes)]
    in_degree = [0] * num_nodes

    for u, v in edges:
        adj[u].append(v)
        in_degree[v] += 1

    # Start with all nodes of in-degree 0
    queue = deque([i for i in range(num_nodes) if in_degree[i] == 0])
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)

        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Cycle detection: if order doesn't contain all nodes, a cycle exists
    if len(order) != num_nodes:
        return []  # cycle detected

    return order
```

**Time complexity:** O(V + E). **Space:** O(V + E).

**Cycle detection built in:** After processing, if `len(order) != num_nodes`, some nodes never reached in-degree 0 — meaning they are part of a cycle. This is cleaner than running a separate cycle detection algorithm.

## DFS-based Topological Sort

The DFS approach processes nodes by post-order: a node is added to the result *after* all its descendants are processed. Reverse the post-order traversal to get the topological order.

```python
def topological_sort_dfs(num_nodes, edges):
    adj = [[] for _ in range(num_nodes)]
    for u, v in edges:
        adj[u].append(v)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = [WHITE] * num_nodes
    result = []
    has_cycle = [False]

    def dfs(node):
        if has_cycle[0]:
            return
        color[node] = GRAY  # currently being processed
        for neighbor in adj[node]:
            if color[neighbor] == GRAY:
                has_cycle[0] = True  # back edge = cycle
                return
            if color[neighbor] == WHITE:
                dfs(neighbor)
        color[node] = BLACK  # fully processed
        result.append(node)

    for i in range(num_nodes):
        if color[i] == WHITE:
            dfs(i)

    return [] if has_cycle[0] else result[::-1]
```

The three-color marking (WHITE/GRAY/BLACK) is the clean way to detect back edges, which indicate cycles. GRAY means "in the current DFS path" — if you hit a gray node, you've found a cycle.

## Course Schedule I & II

**Course Schedule I (LeetCode 207):** Can you complete all courses given prerequisites?

This reduces to: does the directed graph have a cycle? Apply Kahn's algorithm — if `len(order) == numCourses`, no cycle exists.

```python
def canFinish(numCourses, prerequisites):
    adj = [[] for _ in range(numCourses)]
    in_degree = [0] * numCourses
    for u, v in prerequisites:
        adj[v].append(u)
        in_degree[u] += 1
    queue = deque([i for i in range(numCourses) if in_degree[i] == 0])
    count = 0
    while queue:
        node = queue.popleft()
        count += 1
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    return count == numCourses
```

**Course Schedule II (LeetCode 210):** Return the actual order to take courses. This is exactly Kahn's algorithm returning the full order array, or an empty array if a cycle exists.

## Alien Dictionary

The alien dictionary problem (LeetCode 269) is a masterclass in problem reduction. Given a sorted list of alien-language words, determine the order of characters in the alien alphabet.

The key insight: compare adjacent words character by character. The first position where they differ tells you one ordering constraint: `words[i][j]` comes before `words[i+1][j]` in the alphabet. Collect all such constraints and run topological sort.

```python
def alienOrder(words):
    # Initialize graph with all unique characters
    adj = {c: set() for word in words for c in word}

    # Extract ordering constraints
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i+1]
        min_len = min(len(w1), len(w2))
        # Edge case: "abc" before "ab" is invalid
        if len(w1) > len(w2) and w1[:min_len] == w2[:min_len]:
            return ""
        for j in range(min_len):
            if w1[j] != w2[j]:
                adj[w1[j]].add(w2[j])
                break

    # Topological sort using DFS
    visited = {}  # False = visited, True = in current path
    result = []

    def dfs(char):
        if char in visited:
            return visited[char]  # True if cycle
        visited[char] = True
        for neighbor in adj[char]:
            if dfs(neighbor):
                return True
        visited[char] = False
        result.append(char)
        return False

    for c in adj:
        if dfs(c):
            return ""

    return "".join(result[::-1])
```

## When to Reach for Topological Sort

The pattern: you have items with ordering constraints where some items must come before others. Any time you see words like "prerequisite," "dependency," "must complete X before Y," or "valid ordering," your brain should immediately think topological sort.

**Kahn's vs. DFS — which to use?**

- Use **Kahn's** when you need to process nodes in batches (BFS level by level), when cycle detection is the primary goal, or when you want an iterative solution.
- Use **DFS** when you are already traversing the graph for other reasons or when the problem naturally fits a recursive structure.

Both produce valid topological orderings; neither is universally "better." Being comfortable with both signals algorithmic maturity to interviewers.
