---
title: "Interval DP: The Dynamic Programming Pattern for Range Problems"
description: "Master interval dynamic programming for technical interviews — matrix chain multiplication, burst balloons, minimum cost to cut a stick, palindrome partitioning, and the template for solving interval DP problems."
date: "2026-03-20"
category: "Algorithms"
---

# Interval DP: The Dynamic Programming Pattern for Range Problems

Interval DP is a specific dynamic programming pattern where you build solutions for larger intervals by combining solutions for smaller sub-intervals. It appears in hard interview questions like Burst Balloons, Matrix Chain Multiplication, and Strange Printer. Once you recognize the pattern, the approach becomes systematic.

## The Core Pattern

Interval DP problems have this structure:
- You're working with a sequence (array or string)
- You need to compute the optimal value for the entire sequence
- The optimal value for an interval `[i, j]` depends on some choice `k` in the middle
- Smaller intervals must be solved before larger ones

**General form:**
```python
dp[i][j] = optimal result for interval [i, j]

for length in range(2, n+1):        # length of interval
    for i in range(n - length + 1): # start of interval
        j = i + length - 1          # end of interval
        dp[i][j] = WORST
        for k in range(i, j):       # split point
            dp[i][j] = optimal(dp[i][j], combine(dp[i][k], dp[k+1][j], cost(i, k, j)))
```

Fill by increasing interval length. This ensures that when computing `dp[i][j]`, all smaller intervals are already computed.

## Burst Balloons (LeetCode 312)

Given N balloons with values, burst them in some order. When you burst balloon `i`, you earn `nums[i-1] * nums[i] * nums[i+1]`. Maximize total coins.

The key insight: think about which balloon to burst **last** in the interval `[i, j]`, not first. If `k` is the last balloon burst in `[i, j]`, then at the time of bursting, its neighbors are the boundaries (i-1 and j+1).

```python
def maxCoins(nums):
    nums = [1] + nums + [1]  # add boundary balloons
    n = len(nums)
    dp = [[0] * n for _ in range(n)]
    
    for length in range(2, n):
        for left in range(0, n - length):
            right = left + length
            for k in range(left + 1, right):  # k is last burst in (left, right)
                coins = nums[left] * nums[k] * nums[right]
                dp[left][right] = max(dp[left][right],
                                     dp[left][k] + coins + dp[k][right])
    return dp[0][n-1]
```

Time: O(N³), Space: O(N²).

## Matrix Chain Multiplication

Given matrices A₁, A₂, ..., Aₙ, find the parenthesization that minimizes scalar multiplications. Matrix multiplication is associative but not commutative — order of operations matters for cost.

`dp[i][j]` = minimum multiplications to compute the product of matrices i through j.

```python
def matrix_chain(dims):
    n = len(dims) - 1  # number of matrices
    dp = [[0] * n for _ in range(n)]
    
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float('inf')
            for k in range(i, j):
                cost = dp[i][k] + dp[k+1][j] + dims[i]*dims[k+1]*dims[j+1]
                dp[i][j] = min(dp[i][j], cost)
    return dp[0][n-1]
```

## Minimum Cost to Cut a Stick (LeetCode 1547)

Given a stick of length `n` and cuts at positions `cuts[]`, find the minimum cost to make all cuts. The cost of each cut is the length of the stick being cut.

Insight: frame as interval DP. Add 0 and n as boundaries. `dp[i][j]` = minimum cost to make all cuts strictly between cuts[i] and cuts[j].

```python
def minCost(n, cuts):
    cuts = sorted([0] + cuts + [n])
    m = len(cuts)
    dp = [[0] * m for _ in range(m)]
    
    for length in range(2, m):
        for i in range(m - length):
            j = i + length
            dp[i][j] = float('inf')
            for k in range(i + 1, j):
                cost = cuts[j] - cuts[i] + dp[i][k] + dp[k][j]
                dp[i][j] = min(dp[i][j], cost)
    return dp[0][m-1]
```

## Palindrome Partitioning II

Minimum cuts to partition a string into palindromes. This uses interval DP to precompute palindrome checks:

```python
def minCut(s):
    n = len(s)
    # is_palindrome[i][j] = True if s[i:j+1] is a palindrome
    is_pal = [[False] * n for _ in range(n)]
    for i in range(n):
        is_pal[i][i] = True
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if length == 2:
                is_pal[i][j] = (s[i] == s[j])
            else:
                is_pal[i][j] = (s[i] == s[j] and is_pal[i+1][j-1])
    
    # dp[i] = min cuts for s[0:i+1]
    dp = list(range(n))  # worst case: cut every character
    for i in range(1, n):
        if is_pal[0][i]:
            dp[i] = 0
        else:
            for j in range(1, i + 1):
                if is_pal[j][i]:
                    dp[i] = min(dp[i], dp[j-1] + 1)
    return dp[n-1]
```

## Recognizing Interval DP Problems

Key indicators:
- Problem asks for optimal value over a contiguous sequence
- The answer for the whole sequence depends on combining answers for subsequences
- There's a "choice" of where to split or which element to process last/first
- Problem involves removing elements from a sequence with costs that depend on neighbors

Common examples: matrix chain multiplication, game theory problems over sequences, breaking/merging sequences with costs, finding minimum/maximum over all possible orderings of operations.

The insight that usually unlocks interval DP: think about **the last operation** in the optimal sequence rather than the first. "Last burst balloon," "last matrix multiplication," "last cut" — defining the optimal substructure in terms of the final operation makes the recurrence clear.

