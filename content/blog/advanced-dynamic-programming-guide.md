---
title: "Advanced Dynamic Programming: Bitmask DP, Interval DP, and Tree DP"
description: "Master advanced DP techniques for senior interviews: bitmask DP, digit DP, interval DP, tree DP, and how to recognize and solve any DP problem systematically."
date: "2026-03-20"
category: "Algorithm Guides"
---

# Advanced Dynamic Programming: Bitmask DP, Interval DP, and Tree DP

Passing the DP round at a top-tier company is what separates senior candidates from mid-level ones. Standard knapsack and Fibonacci-style problems are table stakes. The questions that actually filter candidates involve bitmask state compression, interval DP on subsequences, and tree DP with re-rooting. This guide covers each technique with templates and the mental model for recognizing when to apply them.

## How to Recognize a DP Problem

Before any template, train your recognition. DP applies when:

1. The problem asks for an optimal value (max/min) or a count of ways.
2. The problem has overlapping subproblems — the same state is computed multiple times in naive recursion.
3. Optimal substructure holds — the global optimum is built from local optima.

Red flags that it's NOT DP: the problem asks for a specific arrangement (often greedy), requires real-time updates (segment tree), or the state space is continuous without discretization.

## Memoization vs Tabulation

**Top-down memoization**: Write the recursive solution naturally, cache results with `@functools.lru_cache` or a dictionary. Easier to write; only computes states actually reached.

**Bottom-up tabulation**: Fill a table iteratively in dependency order. Better cache locality; avoids Python's recursion limit; mandatory for space optimization.

For interviews, start with memoization to establish correctness, then optimize if asked.

## Bitmask DP

Use when the state requires tracking a subset of a small set (typically n ≤ 20). Each subset is represented as an integer bitmask.

**Classic problem: Traveling Salesman Problem (TSP)**

```python
def tsp(dist, n):
    INF = float('inf')
    dp = [[INF] * n for _ in range(1 << n)]
    dp[1][0] = 0  # start at node 0, visited = {0}
    
    for mask in range(1 << n):
        for u in range(n):
            if dp[mask][u] == INF:
                continue
            if not (mask >> u & 1):
                continue
            for v in range(n):
                if mask >> v & 1:
                    continue
                new_mask = mask | (1 << v)
                dp[new_mask][v] = min(dp[new_mask][v], dp[mask][u] + dist[u][v])
    
    full = (1 << n) - 1
    return min(dp[full][i] + dist[i][0] for i in range(n))
```

**Key operations**:
- Check if bit `i` is set: `mask >> i & 1`
- Set bit `i`: `mask | (1 << i)`
- Clear bit `i`: `mask & ~(1 << i)`
- Enumerate all submasks of `mask`: `sub = mask; while sub: sub = (sub - 1) & mask`

Bitmask DP appears in: assignment problems, covering problems, state machine problems where you track which items are "used."

## Interval DP

Use when the optimal answer for a range `[i, j]` depends on answers for sub-ranges. The hallmark is splitting a range at some pivot `k`.

**Classic problem: Matrix Chain Multiplication**

```python
def matrix_chain(dims):
    n = len(dims) - 1
    dp = [[0] * n for _ in range(n)]
    
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float('inf')
            for k in range(i, j):
                cost = dp[i][k] + dp[k+1][j] + dims[i] * dims[k+1] * dims[j+1]
                dp[i][j] = min(dp[i][j], cost)
    return dp[0][n-1]
```

**Other interval DP problems**: Burst Balloons (LeetCode 312), Strange Printer, Minimum Cost to Cut a Stick. The iteration order matters: always iterate by increasing length (length 1, then 2, ..., then n).

## Digit DP

Use when counting integers in a range `[L, R]` with digit-based constraints (sum of digits, no repeating digits, divisibility).

The state is typically `(position, tight, additional_constraint)`. `tight` tracks whether the current prefix matches the upper bound — if tight, the next digit can be at most the upper bound's digit; otherwise it can be 0-9.

```python
from functools import lru_cache

def count_special(n):
    digits = list(map(int, str(n)))
    
    @lru_cache(maxsize=None)
    def dp(pos, tight, current_sum):
        if pos == len(digits):
            return 1 if current_sum % 7 == 0 else 0
        
        limit = digits[pos] if tight else 9
        result = 0
        for d in range(0, limit + 1):
            result += dp(pos + 1, tight and d == limit, current_sum + d)
        return result
    
    return dp(0, True, 0)
```

## Tree DP

Problems on trees are amenable to DP when the answer for a subtree rooted at `v` depends on answers from its children.

**Classic: Diameter of a Binary Tree**

```python
def diameter(root):
    max_diameter = [0]
    
    def depth(node):
        if not node:
            return 0
        left = depth(node.left)
        right = depth(node.right)
        max_diameter[0] = max(max_diameter[0], left + right)
        return 1 + max(left, right)
    
    depth(root)
    return max_diameter[0]
```

**Re-rooting technique**: When you need the DP answer for every node as root (not just the global root), compute down-values in one DFS pass, then propagate up-values in a second pass. This solves "sum of distances in tree" (LeetCode 834) in O(n) instead of O(n²).

## Common DP Patterns Cheatsheet

| Pattern | Signature | Classic Problems |
|---|---|---|
| 0/1 Knapsack | `dp[i][w] = max(dp[i-1][w], dp[i-1][w-wi]+vi)` | Subset Sum, Partition Equal Subset |
| Unbounded Knapsack | `dp[w] = max(dp[w], dp[w-wi]+vi)` | Coin Change, Rod Cutting |
| LCS | `dp[i][j]` on two sequences | Edit Distance, Longest Common Subsequence |
| LIS | `dp[i] = max(dp[j]+1 for j<i if a[j]<a[i])` | Russian Doll Envelopes |
| Bitmask | `dp[mask][node]` | TSP, Min Cost to Connect All Nodes |
| Interval | `dp[i][j]` with pivot `k` | Burst Balloons, Matrix Chain |
| Tree | Post-order DFS | Diameter, Max Path Sum |

## Optimization Techniques

**Space optimization**: When `dp[i]` depends only on `dp[i-1]`, collapse to a 1D array — iterate in reverse for 0/1 knapsack, forward for unbounded.

**Divide and conquer optimization**: When the optimal split point `k` for `dp[i][j]` is monotone, reduces O(n³) interval DP to O(n² log n).

**Knuth's optimization**: For quadrangle inequality problems (like optimal BST), reduces interval DP to O(n²).

In interviews, the ability to derive the recurrence from scratch — rather than memorizing solutions — is what interviewers are actually evaluating. State the subproblem definition in English, write the recurrence, then code. That discipline is what gets offers.

## Related Articles

- [Data Structures and Algorithms Interview Guide](/blog/data-structures-algorithms-interview-guide)
- [Graph Algorithms Interview Guide](/blog/graph-algorithms-interview-guide)
- [Data Structures and Algorithms Cheat Sheet](/blog/data-structures-algorithms-cheat-sheet)
- [Meta Engineering Deep Dive: Inside the Technical Bar](/blog/meta-engineering-deep-dive)
- [Google Interview Guide](/blog/google-interview-guide)
