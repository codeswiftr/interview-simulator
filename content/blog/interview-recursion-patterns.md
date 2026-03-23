---
title: "Recursion Patterns for Coding Interviews: Beyond the Basics"
description: "Advanced recursion patterns for interviews — memoization vs tabulation, tree recursion, mutual recursion, tail recursion, and the systematic approach to writing correct recursive solutions."
date: "2026-03-20"
category: "Algorithms"
---

# Recursion Patterns for Coding Interviews: Beyond the Basics

Most engineers learn recursion through factorial and Fibonacci and stop there. Interview-level recursion requires understanding the structural patterns that underlie every recursive problem: how to identify the recursive case, how to define the base case precisely, and when to memoize vs. iterate. This guide gives you the systematic approach.

## The Recursive Thinking Framework

Every recursive function has three components:
1. **Base case(s):** When to stop recursing. Must be reachable from any input.
2. **Recursive case:** How to reduce the problem toward a base case.
3. **Combination:** How to combine recursive results to solve the current problem.

Before coding, always answer: "What is the smallest version of this problem that I can solve directly?" That's your base case. "How can I break the current problem into the same problem on smaller input?" That's your recursive case.

## Pattern 1: Linear Recursion

One recursive call, reducing input by a constant. Factorial, reverse a string, sum of array.

```python
def sum_array(arr, n):
    if n == 0:
        return 0
    return arr[n - 1] + sum_array(arr, n - 1)
```

Linear recursion is always replaceable by a simple loop. If you find yourself writing linear recursion in an interview, ask whether iteration is clearer.

## Pattern 2: Binary Recursion (Divide and Conquer)

Two recursive calls on halves of the input. Merge sort, binary search, tree traversals.

```python
def binary_search(arr, target, lo, hi):
    if lo > hi:
        return -1
    mid = (lo + hi) // 2
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search(arr, target, mid + 1, hi)
    else:
        return binary_search(arr, target, lo, mid - 1)
```

Binary recursion has O(log n) or O(n log n) complexity depending on how much work is done per level.

## Pattern 3: Tree Recursion

Multiple recursive calls, potentially on overlapping subproblems. Classic example: Fibonacci without memoization.

```python
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)  # Exponential without memoization
```

Tree recursion with overlapping subproblems = opportunity for memoization. The call tree for `fib(5)` recomputes `fib(2)` multiple times. Memoization reduces this to O(n).

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)  # Now O(n) time, O(n) space
```

## Pattern 4: Backtracking

Explore all possibilities, undoing choices that lead to dead ends. Subsets, permutations, N-queens, Sudoku.

```python
def permutations(nums):
    result = []

    def backtrack(current, remaining):
        if not remaining:
            result.append(current[:])
            return
        for i, num in enumerate(remaining):
            current.append(num)
            backtrack(current, remaining[:i] + remaining[i+1:])
            current.pop()  # Undo the choice

    backtrack([], nums)
    return result
```

The template: choose, recurse, unchoose. The "unchoose" step (backtrack) is what distinguishes backtracking from pure recursion.

## Pattern 5: Generate All Structures

Generate all valid structures: parentheses, subsets, combinations. The key is including only the recursive call when a choice is valid.

```python
def generateParenthesis(n):
    result = []

    def generate(current, open_count, close_count):
        if len(current) == 2 * n:
            result.append(current)
            return
        if open_count < n:
            generate(current + '(', open_count + 1, close_count)
        if close_count < open_count:
            generate(current + ')', open_count, close_count + 1)

    generate('', 0, 0)
    return result
```

The constraints (`open_count < n`, `close_count < open_count`) prune invalid branches early, making this efficient despite the exponential output size.

## Recursion vs. Iteration: When to Use Which

| Use Recursion | Use Iteration |
|---|---|
| Tree/graph traversal (natural fit) | Linear traversal |
| Backtracking | Simple accumulation |
| Divide and conquer | When stack overflow is a risk |
| When the recursive structure is clearer | Performance-critical inner loops |

The practical rule: if a problem is naturally hierarchical (trees, nested structures) or requires exploring multiple choices (backtracking), recursion is clearer. If the problem is fundamentally iterative, a loop is simpler and avoids stack overflow risk.

## Avoiding Stack Overflow

Deep recursion hits Python's default recursion limit (1000). In interviews:

**Option 1:** Use iterative approach with an explicit stack.
```python
def inorder_iterative(root):
    result, stack = [], []
    curr = root
    while curr or stack:
        while curr:
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()
        result.append(curr.val)
        curr = curr.right
    return result
```

**Option 2:** Increase recursion limit (mention this as a hack, not a solution):
```python
import sys
sys.setrecursionlimit(100000)
```

**Option 3:** Tail recursion (Python doesn't optimize this, but other languages do).

## Memoization vs. Tabulation

Both are DP, but structured differently:

**Memoization (top-down):** Recursive + cache. Compute on demand. Simpler to write, may have function call overhead.

```python
@lru_cache
def dp(i, j): ...  # Cached recursive calls
```

**Tabulation (bottom-up):** Build the DP table iteratively from smallest to largest. No recursion overhead. Typically better space optimization.

```python
dp = [[0] * (n+1) for _ in range(m+1)]
for i in range(1, m+1):
    for j in range(1, n+1):
        dp[i][j] = ...  # Built from dp[i-1] or dp[i][j-1]
```

In interviews: start with memoization (easier to derive from the recursive formulation), then offer to convert to tabulation if asked for space optimization.

## The Recursion Interview Checklist

Before coding:
1. Identify base cases (what inputs can I solve directly?)
2. Define the recursive call (same function, smaller input)
3. Combine results (how does the recursive result help?)
4. Check for overlapping subproblems (memoize if yes)
5. Estimate depth (risk of stack overflow?)
6. Consider backtracking if exploring choices

After coding:
- Trace through a small example manually
- Verify base cases are correct and reachable
- Check the combine step handles edge cases
