---
title: "Dynamic Programming for Coding Interviews: Patterns, Not Memorization"
description: "Learn dynamic programming through patterns, not problem memorization. Master the 6 core DP patterns that cover 80% of interview problems and develop intuition for when and how to apply them."
date: "2025-09-29"
category: "Interview Preparation"
---

# Dynamic Programming for Coding Interviews: Patterns, Not Memorization

Dynamic programming (DP) is the most feared topic in coding interviews — and the most over-complicated. Most engineers try to memorize solutions to specific problems. The better approach is to recognize that 80% of interview DP problems fit into 6 patterns. Master the patterns, and the problems become tractable.

## The Core Insight: When to Use DP

DP applies when:
1. The problem has **optimal substructure**: the optimal solution can be built from optimal solutions to subproblems
2. The problem has **overlapping subproblems**: the same subproblems are solved multiple times in a naive recursive approach

Both conditions must be present. If subproblems don't overlap, divide-and-conquer (mergesort, quicksort) applies. If there's no optimal substructure, DP won't help.

**Quick test:** Can you write a recursive solution that clearly re-solves the same subproblems? If yes, DP is likely the right tool.

## Pattern 1: Linear DP (1D)

**When:** Problem can be solved by scanning an array linearly, where each cell depends on previous cells.

**Canonical problem:** Climbing Stairs — n steps, can take 1 or 2 at a time, how many ways?

```python
def climb_stairs(n):
    if n <= 2:
        return n
    dp = [0] * (n + 1)
    dp[1] = 1
    dp[2] = 2
    for i in range(3, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]
```

**Other problems:** House Robber, Maximum Subarray, Coin Change (1D variant)

**Key question to ask:** "What's the minimum set of previous cells I need to compute each cell?"

## Pattern 2: Grid DP (2D)

**When:** You have a 2D grid and need to find optimal paths or configurations.

**Canonical problem:** Unique Paths — robot moving from top-left to bottom-right, only right/down moves.

```python
def unique_paths(m, n):
    dp = [[1] * n for _ in range(m)]
    for i in range(1, m):
        for j in range(1, n):
            dp[i][j] = dp[i-1][j] + dp[i][j-1]
    return dp[m-1][n-1]
```

**Other problems:** Minimum Path Sum, Dungeon Game, Edit Distance (strings as a 2D grid)

**Key question:** "What does dp[i][j] represent, and what's the recurrence relation?"

## Pattern 3: Knapsack / Subset DP

**When:** You're choosing items from a set with some constraint (weight, count) to maximize/minimize a value.

**Canonical problem:** 0/1 Knapsack — given weights and values, maximize value within weight limit.

```python
def knapsack(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            dp[i][w] = dp[i-1][w]  # Don't take item i
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], dp[i-1][w - weights[i-1]] + values[i-1])
    return dp[n][capacity]
```

**Other problems:** Coin Change, Partition Equal Subset Sum, Target Sum

**Key question:** "What's the state? (item index + remaining capacity) What's the choice? (take or skip)"

## Pattern 4: String DP

**When:** Given two strings, find optimal alignment, edit distance, or common subsequences.

**Canonical problem:** Longest Common Subsequence (LCS)

```python
def lcs(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]
```

**Other problems:** Edit Distance, Longest Palindromic Subsequence, Interleaving String

**Key question:** "What does dp[i][j] mean in terms of the two string prefixes?"

## Pattern 5: Interval DP

**When:** You need to solve subproblems on contiguous intervals, and larger intervals are built from smaller ones.

**Canonical problem:** Matrix Chain Multiplication — find optimal parenthesization order.

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

**Other problems:** Burst Balloons, Palindrome Partitioning, Stone Game

**Key pattern:** Loop over interval lengths, then over starting positions.

## Pattern 6: State Machine DP

**When:** The problem has explicit states you can be in at each step, and the optimal solution depends on the current state.

**Canonical problem:** Buy/Sell Stock with Cooldown

```python
def max_profit_with_cooldown(prices):
    held = -prices[0]
    sold = 0
    rest = 0
    for price in prices[1:]:
        prev_held = held
        held = max(held, rest - price)  # Keep holding or buy
        rest = max(rest, sold)           # Rest or stay resting
        sold = prev_held + price         # Sell what was held
    return max(sold, rest)
```

**Other problems:** Buy/Sell Stock variants (at most k transactions), Paint House

**Key question:** "What are the distinct states I can be in? What are the transitions between them?"

## The DP Problem-Solving Framework

When you see a problem in an interview, work through this:

1. **Recognize**: Does this have optimal substructure + overlapping subproblems?
2. **Define the state**: What does dp[i] or dp[i][j] represent?
3. **Write the recurrence**: dp[i] = f(dp[i-1], dp[i-2], ...)
4. **Identify base cases**: What are the smallest subproblems you can answer directly?
5. **Determine traversal order**: Fill the table in the right order (usually left-to-right, top-to-bottom)
6. **Optimize space**: Can you replace the full table with a rolling window?

Most interviewers are more impressed by a candidate who explains this framework clearly than one who jumps to the code.
