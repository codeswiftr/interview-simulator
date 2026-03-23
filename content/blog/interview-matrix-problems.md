---
title: "Matrix and 2D Grid Interview Problems: BFS, DFS, Dynamic Programming on Grids"
description: "A systematic guide to solving matrix and 2D grid problems in interviews, covering BFS/DFS traversal patterns, island counting, shortest paths, and dynamic programming on grids."
date: "2026-03-20"
category: "Algorithms"
---

Grid problems appear in roughly 20% of medium and hard LeetCode interview rounds. They test whether you can translate spatial reasoning into algorithmic structure — specifically, whether you instinctively reach for BFS, DFS, or DP depending on what the problem actually needs. This guide gives you the decision framework and the canonical implementations.

## The Core Traversal Setup

Almost every grid problem starts with the same skeleton: iterate over cells, trigger traversal from unvisited cells, track visited state. The directional neighbors pattern is the first thing to internalize:

```python
DIRS = [(0,1),(0,-1),(1,0),(-1,0)]  # right, left, down, up

def in_bounds(r, c, rows, cols):
    return 0 <= r < rows and 0 <= c < cols
```

Some problems include diagonals — add `(1,1),(1,-1),(-1,1),(-1,-1)` to DIRS. Clarify with your interviewer whether diagonal moves are allowed; it's a common trap.

## DFS: Island Counting and Connected Components

**Number of Islands** (LeetCode 200) is the gateway problem. DFS from each unvisited land cell, marking all connected land cells as visited. Count how many times you initiate DFS.

```python
def num_islands(grid):
    rows, cols = len(grid), len(grid[0])
    count = 0

    def dfs(r, c):
        if not in_bounds(r, c, rows, cols) or grid[r][c] != '1':
            return
        grid[r][c] = '#'  # mark visited in-place
        for dr, dc in DIRS:
            dfs(r + dr, c + dc)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                dfs(r, c)
                count += 1
    return count
```

In-place mutation avoids a separate visited set but modifies input — ask your interviewer if that's acceptable.

**Max Area of Island** (LeetCode 695): return the area from DFS instead of 1. **Surrounded Regions** (LeetCode 130): DFS from border-connected 'O' cells first, marking them safe, then flip all remaining 'O' to 'X'. These are variations on the same connected-component DFS pattern.

## BFS: Shortest Path and Multi-Source Problems

Use BFS whenever the problem asks for minimum distance, minimum steps, or the shortest path. BFS guarantees shortest-path correctness in unweighted graphs.

**Rotting Oranges** (LeetCode 994): multi-source BFS starting from all rotten oranges simultaneously. The key insight is that you enqueue all starting nodes before beginning the BFS, not just one.

```python
from collections import deque

def oranges_rotting(grid):
    rows, cols = len(grid), len(grid[0])
    queue = deque()
    fresh = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                queue.append((r, c, 0))  # (row, col, time)
            elif grid[r][c] == 1:
                fresh += 1
    max_time = 0
    while queue:
        r, c, t = queue.popleft()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc, rows, cols) and grid[nr][nc] == 1:
                grid[nr][nc] = 2
                fresh -= 1
                max_time = max(max_time, t + 1)
                queue.append((nr, nc, t + 1))
    return max_time if fresh == 0 else -1
```

**01 Matrix** (LeetCode 542): distance from every cell to the nearest 0. Same multi-source BFS from all 0-cells simultaneously.

**Word Ladder** and **Shortest Path in Binary Matrix** follow the same BFS template — the difference is only in what constitutes a valid neighbor.

## Dynamic Programming on Grids

DP applies when the problem asks for counts, maximum values, or optimal paths — and when the answer for each cell depends only on previously computed cells (usually cells above and to the left).

**Unique Paths** (LeetCode 62): `dp[r][c] = dp[r-1][c] + dp[r][c-1]`. Base cases: first row and first column are all 1s.

**Minimum Path Sum** (LeetCode 64): `dp[r][c] = grid[r][c] + min(dp[r-1][c], dp[r][c-1])`. Same structure, different operation.

**Maximal Square** (LeetCode 221): the side length of the largest square of 1s ending at `(r,c)` is:
```
dp[r][c] = min(dp[r-1][c], dp[r][c-1], dp[r-1][c-1]) + 1  if grid[r][c] == '1'
```
This recurrence is non-obvious and worth memorizing explicitly.

**Dungeon Game** (LeetCode 174) requires filling the DP table from bottom-right to top-left because the constraint (minimum health) flows backward from the exit.

## Choosing BFS vs. DFS vs. DP

| Problem asks for | Use |
|-----------------|-----|
| Count of components / regions | DFS |
| Minimum distance / steps | BFS |
| Count of all paths / arrangements | DP |
| Maximum/minimum value over a path | DP |
| Whether a path exists | BFS or DFS (BFS finds shortest if needed) |
| All cells reachable from borders | DFS or BFS |

When a problem is ambiguous, BFS is usually safer because it terminates at the optimal solution for unweighted graphs. DFS can get trapped deep in a dead end before exploring other options.

## Space Optimization

Visited arrays can often be replaced with in-place modification when you're allowed to mutate the grid. DP tables often reduce from O(m*n) to O(n) by observing that each row only depends on the previous row — maintain two 1D arrays or update in-place with a single array scanning left-to-right.

## Common Mistakes

**Forgetting diagonal directions** when the problem requires them, or including them when only cardinal directions are valid.

**BFS with a set instead of in-place marking:** Re-adding visited cells to the queue before marking them visited creates exponential blowup. Mark a cell visited *when you enqueue it*, not when you dequeue it.

**DP initialization:** Off-by-one errors in base cases (row 0, column 0) cause cascading incorrect values. Always verify base cases on a 1x1 or 2x2 grid before scaling up.

## Practice Sequence

- LeetCode 200 (Number of Islands) — DFS foundation
- LeetCode 695 (Max Area of Island) — DFS with return value
- LeetCode 542 (01 Matrix) — multi-source BFS
- LeetCode 994 (Rotting Oranges) — multi-source BFS with time
- LeetCode 64 (Minimum Path Sum) — grid DP
- LeetCode 221 (Maximal Square) — non-obvious DP recurrence
- LeetCode 130 (Surrounded Regions) — border-first DFS
