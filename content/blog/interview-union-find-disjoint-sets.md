---
title: "Union-Find (Disjoint Set Union): The Complete Interview Guide"
description: "Master the Union-Find data structure for coding interviews — path compression, union by rank, connected components, cycle detection, and classic problems like number of islands and redundant connection."
date: "2026-03-20"
category: "Algorithms"
---

Union-Find, also called Disjoint Set Union (DSU), is one of the most underrated data structures in interview preparation. It solves a specific class of problems — dynamic connectivity — with near-constant time operations, making it invaluable for graph problems that require grouping elements into sets and quickly determining if two elements belong to the same set.

## The Core Idea

Imagine tracking connected components in a network. You need two operations:
- **Union(u, v):** Connect nodes u and v (merge their groups)
- **Find(x):** Return the "representative" (root) of x's group

If `Find(u) == Find(v)`, u and v are in the same connected component.

Naive implementation with arrays gives O(n) per operation. With two key optimizations, we get nearly O(1) amortized time.

## Implementation with Path Compression and Union by Rank

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))  # Each node is its own parent initially
        self.rank = [0] * n           # Rank (approximate tree height)
        self.components = n           # Number of distinct components

    def find(self, x):
        # Path compression: make every node point directly to root
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return False  # Already connected — unioning would create a cycle

        # Union by rank: attach smaller tree under larger tree
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1

        self.components -= 1
        return True  # Successfully merged two components

    def connected(self, x, y):
        return self.find(x) == self.find(y)
```

**Path compression:** When finding the root, reattach every node on the path directly to the root. Future finds on any of those nodes become O(1). This single optimization transforms a chain of n nodes into a star topology after the first traversal.

**Union by rank:** Always attach the shorter tree under the taller one. This keeps trees flat, preventing degeneration into a linked list. The rank is an upper bound on tree height.

**Combined time complexity:** O(α(n)) per operation, where α is the inverse Ackermann function — effectively constant for all practical inputs (α(n) ≤ 4 for n < 10^600).

## Problem 1: Number of Connected Components

**LeetCode 323.** Count connected components in an undirected graph.

```python
def countComponents(n, edges):
    uf = UnionFind(n)
    for u, v in edges:
        uf.union(u, v)
    return uf.components
```

The `components` counter starts at n (each node is its own component) and decrements by 1 each time two previously disconnected components are merged.

## Problem 2: Redundant Connection (Cycle Detection)

**LeetCode 684.** In a tree with one extra edge, find the redundant edge that creates a cycle.

```python
def findRedundantConnection(edges):
    n = len(edges)
    uf = UnionFind(n + 1)

    for u, v in edges:
        if not uf.union(u, v):
            return [u, v]  # Already connected — this edge is redundant

    return []
```

**The insight:** In a tree, adding any edge creates exactly one cycle. When we process edges in order and encounter an edge (u, v) where u and v are already connected (`union` returns False), that edge is the one creating the cycle. Process edges in order and return the first one that would create a cycle.

## Problem 3: Number of Islands II

**LeetCode 305.** Given an m x n grid, process a sequence of "add land" operations and after each operation report the number of islands.

This is the dynamic connectivity problem — islands merge as adjacent land cells are added. Union-Find handles this elegantly because it supports incremental merging (unlike BFS/DFS which would require reprocessing from scratch).

```python
def numIslands2(m, n, positions):
    uf = UnionFind(m * n)
    result = []
    land = set()
    directions = [(0,1),(0,-1),(1,0),(-1,0)]

    for r, c in positions:
        if (r, c) in land:
            result.append(uf.components - (m*n - len(land)))
            continue
        land.add((r, c))
        uf.components -= (m * n - len(land))  # Adjust for water cells hack

        # Union with adjacent land cells
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and (nr, nc) in land:
                uf.union(r * n + c, nr * n + nc)

        result.append(uf.components - (m * n - len(land)))

    return result
```

A cleaner approach maintains a separate island count and increments/decrements as cells are added and merged. The key point for interviews: BFS/DFS re-processes from scratch each time (O(positions × m × n)); Union-Find processes each position once (O(positions × α(m × n))).

## Problem 4: Accounts Merge

**LeetCode 721.** Merge accounts that share common email addresses.

Each account may share emails with other accounts. Two accounts should be merged if they share at least one email. This is a graph connectivity problem — emails are nodes, shared emails between accounts are edges.

```python
def accountsMerge(accounts):
    email_to_id = {}
    email_to_name = {}
    uf_id = [0]

    def get_id(email):
        if email not in email_to_id:
            email_to_id[email] = uf_id[0]
            uf_id[0] += 1
        return email_to_id[email]

    uf = UnionFind(10001)  # Upper bound on distinct emails

    for account in accounts:
        name = account[0]
        first_email_id = get_id(account[1])
        email_to_name[account[1]] = name
        for email in account[1:]:
            email_id = get_id(email)
            email_to_name[email] = name
            uf.union(first_email_id, email_id)

    # Group emails by root
    from collections import defaultdict
    groups = defaultdict(list)
    for email, email_id in email_to_id.items():
        groups[uf.find(email_id)].append(email)

    return [[email_to_name[emails[0]]] + sorted(emails)
            for emails in groups.values()]
```

## When to Reach for Union-Find

The pattern: you have elements that need to be grouped dynamically, and you frequently need to check if two elements belong to the same group. Keywords in problem statements: "connected components," "union," "merge groups," "same group," "redundant connection."

**Union-Find beats BFS/DFS when:**
- You need to process operations incrementally (dynamic connectivity)
- You only need to answer "are these connected?" — not find the actual path
- The graph is dense and you process many connectivity queries

For static graphs where you need the actual path or traversal order, BFS/DFS remains preferable. Union-Find's power is specifically in its near-O(1) connectivity queries.
