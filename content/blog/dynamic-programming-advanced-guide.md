---
title: "Advanced Dynamic Programming: Interval DP, Digit DP, and Bitmask DP Patterns"
description: "Go beyond basic DP with in-depth coverage of interval DP, digit DP, and bitmask DP — three advanced patterns that appear in senior-level coding interviews at top tech companies."
date: "2026-03-20"
category: "Algorithms"
---

Dynamic programming is one of those topics where knowing the basics gets you through junior-level screens, but senior and staff interviews expect fluency with advanced patterns. Interval DP, digit DP, and bitmask DP represent the tier of problems that separate candidates who have practiced thoughtfully from those who have memorized solutions. This guide covers all three with the mental models you need to apply them under pressure.

## Interval DP: Thinking in Ranges

Interval DP solves problems where the optimal answer over a range `[i, j]` depends on answers over smaller sub-ranges. The signature structure is: you split `[i, j]` at some pivot `k`, solve both halves, and combine.

**When to reach for interval DP:** matrix chain multiplication, optimal BST construction, balloon burst, stone merge, palindrome partitioning minimum cuts.

The canonical template:

```python
n = len(arr)
dp = [[0] * n for _ in range(n)]

# Fill by increasing length
for length in range(2, n + 1):
    for i in range(n - length + 1):
        j = i + length - 1
        dp[i][j] = float('inf')
        for k in range(i, j):
            dp[i][j] = min(dp[i][j], dp[i][k] + dp[k+1][j] + cost(i, k, j))
```

The **Balloon Burst** problem (LeetCode 312) is a masterclass in reframing interval DP. Instead of thinking about which balloon to pop first, think about which balloon to pop *last* in range `[i, j]`. This inversion makes the subproblems independent — a technique worth remembering whenever the naive decomposition creates dependency problems.

**Palindrome DP variants** often combine interval DP with other patterns. For minimum palindrome partitioning, you precompute `is_palindrome[i][j]` with interval DP in O(n²) time, then use a separate 1D DP for the cut counts.

## Digit DP: Counting in Ranges

Digit DP answers the question: "How many numbers in [L, R] satisfy property P?" The approach is to count valid numbers from 0 to N and use subtraction: `count(R) - count(L-1)`.

The state typically encodes:
- Current digit position
- Whether we're still bounded by the original number (tight constraint)
- Any accumulated property value (digit sum, digit count, etc.)

```python
from functools import lru_cache

def count_valid(n: int) -> int:
    digits = list(map(int, str(n)))
    
    @lru_cache(maxsize=None)
    def dp(pos, tight, accumulated_state):
        if pos == len(digits):
            return 1 if is_valid(accumulated_state) else 0
        
        limit = digits[pos] if tight else 9
        result = 0
        for d in range(0, limit + 1):
            new_tight = tight and (d == limit)
            new_state = transition(accumulated_state, d)
            result += dp(pos + 1, new_tight, new_state)
        return result
    
    return dp(0, True, initial_state)
```

The `tight` flag is the crucial insight. When `tight=True`, the current digit can be at most `digits[pos]`. Once you place a digit smaller than the limit, all subsequent positions are free (`tight=False`).

**Common digit DP problems:** count numbers with digit sum divisible by K, numbers without consecutive equal digits, numbers where no digit exceeds its position index, count of stepping numbers in a range.

A frequent mistake is forgetting leading zeros. Numbers like "007" should be treated as "7" for most problems — track a `leading_zero` flag in your state or handle it in the base case.

## Bitmask DP: Exponential State with Polynomial Transitions

Bitmask DP handles problems over subsets of a small set (typically n ≤ 20). The bitmask represents which elements have been "used," and you iterate over all 2^n subsets.

**Classic problems:** Traveling Salesman Problem, assignment problems, counting Hamiltonian paths, set cover variants.

TSP template:

```python
INF = float('inf')
n = len(cities)
dist = [[...]]  # precomputed distances

# dp[mask][i] = min cost to visit all cities in mask, ending at city i
dp = [[INF] * n for _ in range(1 << n)]
dp[1][0] = 0  # start at city 0, only city 0 visited

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

# Complete the tour
ans = min(dp[(1<<n)-1][i] + dist[i][0] for i in range(1, n))
```

**Iterating over subsets efficiently:** to enumerate all subsets of a mask, use `sub = mask; while sub > 0: process(sub); sub = (sub - 1) & mask`. This runs in O(3^n) total across all masks, which is the correct complexity for subset-sum enumeration.

**Profile DP** extends bitmask DP to grid problems. The "mask" represents the state of the current column or row boundary, allowing you to solve tiling and path problems that would otherwise be exponential.

## Interview Strategy for Advanced DP

When you see a hard DP problem in an interview:

1. **Classify the structure first.** Does it ask about ranges? Digit counts? Subset selection? This maps directly to interval, digit, or bitmask DP.

2. **Define state before writing code.** Write `dp[i][j] = ...` in plain English before touching the keyboard. Interviewers evaluate your reasoning, not just your code.

3. **Identify recurrence, then base cases, then traversal order.** Many candidates write the recurrence correctly but get the fill order wrong for interval DP (must fill by increasing length, not by `i`).

4. **Optimize memory only after correctness.** Many 2D DP tables can be reduced to two rolling arrays, but only mention this after your solution is correct. Premature optimization is a red flag.

5. **Practice the memoization ↔ tabulation conversion.** Top-down memoization is faster to write under pressure; bottom-up tabulation often has better constant factors. Be able to do both.

Advanced DP problems are rare in phone screens but common in onsite loops at FAANG and high-growth companies. Each pattern rewards deliberate study over pattern-matching — understand the structure, and you'll recognize variants you've never seen before.
