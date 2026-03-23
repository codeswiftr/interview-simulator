---
title: "Union-Find (Disjoint Set Union) for Coding Interviews: Path Compression and Key Problems"
description: "Master Union-Find with path compression and union by rank. Solve Number of Provinces, Redundant Connection, Accounts Merge, Most Stones Removed, and other common interview problems."
date: "2026-03-20"
category: "Data Structures & Algorithms"
---

# Union-Find (Disjoint Set Union) for Coding Interviews: Path Compression and Key Problems

Union-Find (also called Disjoint Set Union, or DSU) is one of the most underestimated data structures in coding interviews. It handles a specific but important class of problems — dynamic connectivity, component membership, and cycle detection in undirected graphs — with nearly O(1) amortized time per operation. Engineers who know it well solve a category of graph problems in minutes that others struggle with for hours.

## The Core Data Structure

Union-Find maintains a partition of elements into disjoint sets, supporting two operations:
- `find(x)`: which set does `x` belong to? (returns a representative/root)
- `union(x, y)`: merge the sets containing `x` and `y`

The naive implementation is a flat parent array where `parent[i]` points to `i`'s parent (root points to itself). The two optimizations that make it efficient:

```python
class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n  # union by rank
        self.components = n  # track connected component count

    def find(self, x: int) -> int:
        # Path compression: make every node on the path point to root
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False  # already in same set — signals a cycle

        # Union by rank: attach smaller tree under larger tree
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

        self.components -= 1
        return True

    def connected(self, x: int, y: int) -> bool:
        return self.find(x) == self.find(y)
```

**Path compression**: during `find`, every visited node is made to point directly to the root. This flattens the tree over successive operations.

**Union by rank**: always attach the shorter tree under the taller tree. This prevents degeneration into a linked list.

Combined, these two optimizations give amortized `O(α(n))` per operation, where `α` is the inverse Ackermann function — effectively constant for any real-world input size.

## Number of Provinces (LeetCode 547)

Find the number of connected components in an undirected graph given as an adjacency matrix.

```python
def findCircleNum(isConnected: list[list[int]]) -> int:
    n = len(isConnected)
    uf = UnionFind(n)

    for i in range(n):
        for j in range(i + 1, n):
            if isConnected[i][j] == 1:
                uf.union(i, j)

    return uf.components
```

This is the simplest Union-Find application: iterate all edges, union connected nodes, count remaining components. Time: `O(n² * α(n))`.

## Redundant Connection (LeetCode 684)

Find the edge that, if removed, makes the graph a tree. Since a tree with `n` nodes has exactly `n-1` edges, the first edge that creates a cycle is the redundant one.

```python
def findRedundantConnection(edges: list[list[int]]) -> list[int]:
    n = len(edges)
    uf = UnionFind(n + 1)  # nodes are 1-indexed

    for u, v in edges:
        if not uf.union(u, v):
            return [u, v]  # union returned False → cycle detected

    return []
```

The key insight: `union` returns `False` when two nodes are already in the same component. The first edge that triggers this is the redundant connection.

## Accounts Merge (LeetCode 721)

This is Union-Find applied to a non-obvious domain: merging user accounts that share email addresses.

```python
def accountsMerge(accounts: list[list[str]]) -> list[list[str]]:
    email_to_id: dict[str, int] = {}
    email_to_name: dict[str, str] = {}
    counter = 0

    for account in accounts:
        name = account[0]
        for email in account[1:]:
            if email not in email_to_id:
                email_to_id[email] = counter
                counter += 1
            email_to_name[email] = name

    uf = UnionFind(counter)

    for account in accounts:
        first_email_id = email_to_id[account[1]]
        for email in account[2:]:
            uf.union(first_email_id, email_to_id[email])

    # Group emails by their root representative
    from collections import defaultdict
    components: dict[int, list[str]] = defaultdict(list)
    for email, eid in email_to_id.items():
        root = uf.find(eid)
        components[root].append(email)

    result = []
    for root, emails in components.items():
        name = email_to_name[emails[0]]
        result.append([name] + sorted(emails))

    return result
```

The pattern here: assign integer IDs to non-integer entities (emails), run Union-Find on the integers, then re-group by root ID.

## Most Stones Removed with Same Row or Column (LeetCode 947)

Remove the maximum number of stones from a 2D plane, where a stone can be removed if it shares a row or column with another stone. The answer is `total_stones - number_of_connected_components`.

```python
def removeStones(stones: list[list[int]]) -> int:
    # Map row and column indices to the same Union-Find
    # Offset columns to avoid collision with row indices
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        if x not in parent:
            parent[x] = x
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x: int, y: int) -> None:
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for r, c in stones:
        union(r, c + 10001)  # offset columns to avoid row-column collision

    # Count distinct roots among stones only
    unique_roots = len({find(r) for r, c in stones})
    return len(stones) - unique_roots
```

The elegant trick: union each stone's row index with its column index (offset to avoid collision). Two stones in the same component means they're transitively connected through shared rows/columns.

## Number of Islands II (LeetCode 305)

Given a grid initially all water, add land cells one by one and report the number of islands after each addition.

```python
def numIslands2(m: int, n: int, positions: list[list[int]]) -> list[int]:
    uf = UnionFind(m * n)
    land: set[int] = set()
    result = []

    def idx(r: int, c: int) -> int:
        return r * n + c

    for r, c in positions:
        i = idx(r, c)
        if i in land:
            result.append(uf.components - (m * n - len(land)))
            continue
        land.add(i)
        # Each new land cell starts as its own component
        # (already initialized in UnionFind)

        # Union with adjacent land cells
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            j = idx(nr, nc)
            if 0 <= nr < m and 0 <= nc < n and j in land:
                uf.union(i, j)

        result.append(len(land) - (len(land) - uf.components +
                                   (m * n - len(land))))

    return result
```

This problem is better solved with a cleaner component counter approach, but the core pattern remains: each new land cell is added to the Union-Find and unioned with adjacent land cells.

## When to Use Union-Find vs. BFS/DFS

Union-Find excels when:
- You need **online** connectivity queries (process edges one at a time)
- The graph is **undirected** (directed graphs need Tarjan's/Kosaraju's for SCCs)
- You need to **detect cycles** during edge insertion
- **Dynamic connectivity**: nodes/edges added over time (not batch-processed)

BFS/DFS excels when:
- You need the **actual path** between nodes, not just connectivity
- The graph is **directed**
- You need **ordering** (topological sort)
- The graph is given as a full adjacency list up front

## Interview Tips

1. **Recognize the pattern**: "connected components," "merge groups," "cycle detection in undirected graph" → Union-Find is likely the right tool.
2. **Always use path compression and union by rank**: Without them, your solution may TLE on the largest inputs.
3. **Encode non-integer keys**: Emails, strings, coordinate pairs — map to integers first, then run Union-Find on the integers.
4. **Track component count**: Add a `components` counter to your UnionFind class by default. Interviewers frequently ask for the count.
5. **State the complexity**: `O(α(n))` per operation. If the interviewer asks, explain that α grows so slowly it's effectively constant.

Union-Find is one of those data structures where pattern recognition is half the battle. Once you see the connection between the problem and dynamic connectivity, the implementation is nearly mechanical.
