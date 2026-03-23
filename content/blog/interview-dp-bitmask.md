---
title: "Bitmask Dynamic Programming: TSP, Set Cover, Assignment Problems, and State Compression"
description: "Master bitmask DP for technical interviews: traveling salesman problem, minimum set cover, optimal assignment, subset enumeration, and when to use state compression to reduce exponential problems."
date: "2026-03-20"
category: "Algorithms"
---

# Bitmask Dynamic Programming

Bitmask DP is the technique for problems where the state is "which subset of elements have been used." By representing a subset as a bitmask (an integer where bit `i` is 1 if element `i` is included), we compress exponentially many states into integers we can use as array indices — turning otherwise intractable problems into O(2^n × n) solutions.

## When Does Bitmask DP Apply?

Look for these signals in a problem:
- Small n (typically n ≤ 20, sometimes n ≤ 25)
- The problem asks about subsets or assignments of n elements
- Optimal solution requires tracking which elements have been visited or assigned
- The phrase "minimum cost to visit all" or "assign all tasks" appears

The fundamental constraint: 2^n states × O(n) per state = O(n × 2^n) time and O(2^n) space. For n=20, this is ~20 million operations — feasible. For n=30, it's ~30 billion — not feasible.

## Foundation: Bitmask Operations

```python
# Check if bit i is set in mask
(mask >> i) & 1

# Set bit i
mask | (1 << i)

# Remove bit i (turn off)
mask & ~(1 << i)

# Iterate over all subsets of n elements
for mask in range(1 << n):
    ...

# Full mask (all n bits set)
full = (1 << n) - 1

# Number of bits set
bin(mask).count('1')  # or popcount
```

## Problem 1: Traveling Salesman Problem (TSP)

**Problem:** Visit all n cities exactly once and return to start. Find minimum total cost.

**State:** `dp[mask][i]` = minimum cost to visit exactly the cities in `mask`, ending at city `i`.

**Base case:** `dp[1 << 0][0] = 0` (at city 0, only city 0 visited)

**Transition:** For each mask and current city `i`, try moving to any unvisited city `j`:
```
dp[mask | (1 << j)][j] = min(dp[mask | (1 << j)][j],
                              dp[mask][i] + dist[i][j])
```

```python
def tsp(dist: list[list[int]]) -> int:
    n = len(dist)
    INF = float('inf')
    # dp[mask][i]: min cost visiting cities in mask, ending at i
    dp = [[INF] * n for _ in range(1 << n)]
    dp[1][0] = 0  # Start at city 0

    for mask in range(1, 1 << n):
        for i in range(n):
            if dp[mask][i] == INF:
                continue
            if not (mask >> i) & 1:
                continue  # i not in current path

            for j in range(n):
                if (mask >> j) & 1:
                    continue  # j already visited
                next_mask = mask | (1 << j)
                dp[next_mask][j] = min(dp[next_mask][j],
                                       dp[mask][i] + dist[i][j])

    full = (1 << n) - 1
    return min(dp[full][i] + dist[i][0] for i in range(n))
# Time: O(n² × 2^n), Space: O(n × 2^n)
```

**Memory optimization:** For n=20, the dp table is 20 × 2^20 ≈ 20M integers — manageable with care. If n=25, you need profile-guided optimization or branch-and-bound.

## Problem 2: Minimum Set Cover

**Problem:** Given n elements (bits) and m subsets, find the minimum number of subsets that cover all n elements.

```python
def min_set_cover(n: int, sets: list[int]) -> int:
    """
    n: number of elements to cover
    sets: list of bitmasks representing which elements each set covers
    """
    full = (1 << n) - 1
    INF = float('inf')
    dp = [INF] * (1 << n)
    dp[0] = 0

    for mask in range(1 << n):
        if dp[mask] == INF:
            continue
        for s in sets:
            dp[mask | s] = min(dp[mask | s], dp[mask] + 1)

    return dp[full]
# Time: O(m × 2^n), Space: O(2^n)
```

**Note:** Set cover is NP-hard in general — bitmask DP only works because n is small. The greedy approximation (always pick the subset covering the most uncovered elements) achieves O(log n) approximation for large n.

## Problem 3: Optimal Task Assignment (Assignment Problem)

**Problem:** Assign n tasks to n workers, one task per worker, to minimize total cost. More flexible than the Hungarian algorithm when n is small.

```python
def min_cost_assignment(cost: list[list[int]]) -> int:
    n = len(cost)
    INF = float('inf')
    dp = [INF] * (1 << n)
    dp[0] = 0

    for mask in range(1 << n):
        if dp[mask] == INF:
            continue
        worker = bin(mask).count('1')  # Next worker to assign
        if worker == n:
            continue
        for task in range(n):
            if not (mask >> task) & 1:  # Task not yet assigned
                dp[mask | (1 << task)] = min(
                    dp[mask | (1 << task)],
                    dp[mask] + cost[worker][task]
                )

    return dp[(1 << n) - 1]
# Time: O(n × 2^n), Space: O(2^n)
```

**Reconstruct the assignment:**
```python
def reconstruct(cost, dp, n):
    assignment = []
    mask = (1 << n) - 1
    for worker in range(n - 1, -1, -1):
        for task in range(n):
            if (mask >> task) & 1:
                prev_mask = mask ^ (1 << task)
                if dp[mask] == dp[prev_mask] + cost[worker][task]:
                    assignment.append(task)
                    mask = prev_mask
                    break
    return assignment[::-1]
```

## Problem 4: Shortest Path Visiting All Nodes (Graph Variant)

**Problem:** In an undirected graph, find the shortest path that visits every node (at least once). Nodes can be revisited.

This differs from TSP in two ways: the graph isn't complete, and nodes can be revisited.

```python
from collections import deque

def shortest_path_visiting_all(graph: list[list[int]]) -> int:
    n = len(graph)
    full = (1 << n) - 1

    # BFS: state = (node, visited_mask)
    queue = deque()
    visited = set()

    for i in range(n):
        state = (i, 1 << i)
        queue.append((state, 0))  # (state, distance)
        visited.add(state)

    while queue:
        (node, mask), dist = queue.popleft()

        if mask == full:
            return dist

        for neighbor in graph[node]:
            new_mask = mask | (1 << neighbor)
            new_state = (neighbor, new_mask)
            if new_state not in visited:
                visited.add(new_state)
                queue.append((new_state, dist + 1))

    return -1
# Time: O(n × 2^n), Space: O(n × 2^n)
```

## Problem 5: Enumerate All Subsets of a Mask

A frequently overlooked technique — iterating over all subsets of a given bitmask:

```python
def enumerate_subsets(mask: int):
    s = mask
    while s > 0:
        yield s
        s = (s - 1) & mask
    yield 0  # Include empty set

# Total iterations across all masks of n bits: 3^n
# Proof: each element is either (1) in mask but not subset,
#         (2) in both mask and subset, or (3) in neither
```

**Application — partition DP:**
```python
def min_cost_partition(nums: list[int], group_cost: list[int]) -> int:
    n = len(nums)
    full = (1 << n) - 1
    dp = [float('inf')] * (1 << n)
    dp[0] = 0

    for mask in range(1, 1 << n):
        # Try all subsets of mask as one group
        sub = mask
        while sub > 0:
            if dp[mask ^ sub] != float('inf'):
                dp[mask] = min(dp[mask],
                               dp[mask ^ sub] + group_cost[sub])
            sub = (sub - 1) & mask

    return dp[full]
```

## Complexity Summary

| Problem | Time | Space |
|---------|------|-------|
| TSP | O(n² × 2^n) | O(n × 2^n) |
| Set Cover | O(m × 2^n) | O(2^n) |
| Assignment | O(n × 2^n) | O(2^n) |
| Subset enumeration | O(3^n) total | O(2^n) |

## Interview Tips for Bitmask DP

1. **State the state clearly.** Before coding, say: "Let `dp[mask]` represent the minimum cost to [accomplish X] having used the elements in `mask`."
2. **Declare n ≤ constraint immediately.** Bitmask DP requires bounded n — state this to the interviewer upfront.
3. **Use Python carefully.** Python integers are arbitrary precision, but bit operations and list indexing still work. In C++, prefer `int` or `long long` and `vector<int>(1 << n)`.
4. **Reconstruction matters.** Many interviewers follow up with "now output the actual assignment" — know how to backtrack through the dp table.
5. **Space optimization.** If the DP only looks at subsets of the current mask, you may be able to iterate in increasing popcount order and use rolling arrays.

Bitmask DP is one of the clearest demonstrations of the "trading exponential brute force for polynomial × exponential" insight that underlies all dynamic programming. Master it and you'll be ready for the hardest subset problems in interviews.
