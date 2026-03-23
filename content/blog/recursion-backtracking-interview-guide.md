---
title: "Recursion and Backtracking: Mastering the Interview Pattern"
description: "Master recursion and backtracking for coding interviews. Learn the backtracking template, solve 5 classic problems including subsets, permutations, N-queens, and word search, and understand how to analyze time complexity."
date: "2025-10-11"
category: "Interview Preparation"
---
# Recursion and Backtracking: Mastering the Interview Pattern

Backtracking problems are among the most feared in technical interviews, yet they all share the same skeleton. Once you internalize the pattern — choose, explore, unchoose — problems that seemed like puzzles become mechanical. This guide walks through the fundamentals of recursion, the backtracking template, five classic problems with complete solutions, and how to analyze the time complexity of these algorithms without guessing.

## Recursion Fundamentals

Recursion is a function calling itself with a smaller input until it reaches a base case. Every recursive function has exactly two parts:

**Base case:** The condition under which the function returns without making another recursive call. Get this wrong and your function runs forever (stack overflow).

**Recursive case:** The logic that reduces the problem toward the base case, then combines results.

```python
# Classic example: factorial
def factorial(n: int) -> int:
    if n <= 1:          # base case
        return 1
    return n * factorial(n - 1)  # recursive case

# The call stack for factorial(4):
# factorial(4) → 4 * factorial(3)
#                    3 * factorial(2)
#                        2 * factorial(1)
#                            1  (base case, unwinds)
```

When you write a recursive solution, think in terms of the recurrence relation: "If I knew the answer for n-1, how would I compute the answer for n?" For factorial: `f(n) = n * f(n-1)`. For Fibonacci: `f(n) = f(n-1) + f(n-2)`. For tree height: `height(node) = 1 + max(height(node.left), height(node.right))`.

The call stack has depth equal to the maximum recursion depth. Python's default recursion limit is 1000. For inputs larger than that, either use iterative conversion or increase the limit with `sys.setrecursionlimit()` — and mention this to your interviewer when relevant.

## The Backtracking Template

Backtracking is recursion with a twist: you build a solution incrementally, and whenever you detect that the current partial solution cannot possibly lead to a valid complete solution, you undo your last choice (backtrack) and try a different path.

The three-step mantra: **Choose → Explore → Unchoose**

```python
def backtrack(state, choices):
    if is_complete(state):
        record_solution(state)
        return
    
    for choice in choices:
        if is_valid(state, choice):
            make_choice(state, choice)      # Choose
            backtrack(state, next_choices)  # Explore
            undo_choice(state, choice)      # Unchoose (backtrack)
```

The `undo_choice` step is what makes backtracking distinct from regular recursion. Without it, your `state` accumulates changes from every explored path, making results incorrect. The undo must be the exact inverse of the make step — if you appended to a list, pop it; if you incremented a counter, decrement it; if you set a cell to '#', restore it.

## 5 Classic Backtracking Problems

**Problem 1: Subsets (LC 78)**

Generate all subsets of a set of distinct integers. The decision at each step is: include this element or skip it.

```python
def subsets(nums: list[int]) -> list[list[int]]:
    result = []
    def backtrack(start: int, current: list[int]):
        result.append(list(current))  # every state is a valid subset
        for i in range(start, len(nums)):
            current.append(nums[i])       # choose
            backtrack(i + 1, current)     # explore
            current.pop()                 # unchoose
    backtrack(0, [])
    return result
```

The `start` index prevents revisiting elements and avoids duplicate subsets. Time complexity: O(n * 2^n) — 2^n subsets, each taking O(n) to copy.

**Problem 2: Permutations (LC 46)**

Generate all permutations of a list of distinct integers. Unlike subsets, every element must be used exactly once, and order matters.

```python
def permutations(nums: list[int]) -> list[list[int]]:
    result = []
    def backtrack(current: list[int], remaining: list[int]):
        if not remaining:
            result.append(list(current))
            return
        for i in range(len(remaining)):
            current.append(remaining[i])                      # choose
            backtrack(current, remaining[:i] + remaining[i+1:])  # explore
            current.pop()                                      # unchoose
    backtrack([], nums)
    return result
```

Time complexity: O(n * n!) — n! permutations, each taking O(n) to copy.

**Problem 3: Combination Sum (LC 39)**

Find all combinations of candidates that sum to a target. Candidates can be reused.

```python
def combination_sum(candidates: list[int], target: int) -> list[list[int]]:
    result = []
    candidates.sort()
    def backtrack(start: int, current: list[int], remaining: int):
        if remaining == 0:
            result.append(list(current))
            return
        for i in range(start, len(candidates)):
            if candidates[i] > remaining:
                break  # pruning: no point trying larger candidates
            current.append(candidates[i])
            backtrack(i, current, remaining - candidates[i])  # i, not i+1 (reuse allowed)
            current.pop()
    backtrack(0, [], target)
    return result
```

The `break` when `candidates[i] > remaining` is a crucial pruning optimization — it avoids exploring branches that cannot possibly reach the target.

**Problem 4: N-Queens (LC 51)**

Place N queens on an N×N chessboard so no two attack each other. A queen attacks along rows, columns, and diagonals.

```python
def solve_n_queens(n: int) -> list[list[str]]:
    result = []
    cols = set()
    pos_diag = set()   # row + col is constant on a positive diagonal
    neg_diag = set()   # row - col is constant on a negative diagonal
    
    board = [['.' for _ in range(n)] for _ in range(n)]
    
    def backtrack(row: int):
        if row == n:
            result.append([''.join(r) for r in board])
            return
        for col in range(n):
            if col in cols or (row + col) in pos_diag or (row - col) in neg_diag:
                continue
            cols.add(col)
            pos_diag.add(row + col)
            neg_diag.add(row - col)
            board[row][col] = 'Q'
            backtrack(row + 1)
            cols.remove(col)
            pos_diag.remove(row + col)
            neg_diag.remove(row - col)
            board[row][col] = '.'
    
    backtrack(0)
    return result
```

Using three sets for constraint checking gives O(1) validity checks instead of O(n) board scans.

**Problem 5: Word Search (LC 79)**

Given a 2D grid of characters, determine if a given word exists as a connected path (up/down/left/right, no cell reused).

```python
def exist(board: list[list[str]], word: str) -> bool:
    rows, cols = len(board), len(board[0])
    
    def backtrack(r: int, c: int, idx: int) -> bool:
        if idx == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        if board[r][c] != word[idx]:
            return False
        
        temp = board[r][c]
        board[r][c] = '#'  # mark visited
        
        found = (backtrack(r+1, c, idx+1) or
                 backtrack(r-1, c, idx+1) or
                 backtrack(r, c+1, idx+1) or
                 backtrack(r, c-1, idx+1))
        
        board[r][c] = temp  # unchoose (restore)
        return found
    
    for r in range(rows):
        for c in range(cols):
            if backtrack(r, c, 0):
                return True
    return False
```

## How to Analyze Backtracking Time Complexity

Backtracking complexity often involves exponential or factorial terms, which intimidates many candidates. The systematic approach: count the number of leaf nodes in the recursion tree, then multiply by the work per node.

- **Subsets:** At each of n positions, make a binary choice (include/exclude). Total leaves = 2^n. Work per leaf = O(n) to copy. Total = **O(n * 2^n)**.
- **Permutations:** n choices at depth 1, n-1 at depth 2, ... 1 at depth n. Total leaves = n!. Work per leaf = O(n). Total = **O(n * n!)**.
- **Combination Sum:** Harder to bound tightly — use the maximum depth (target / min_candidate) and branching factor (number of candidates). In practice, pruning makes the actual runtime much better than the theoretical worst case.
- **N-Queens:** At each row, up to n column choices, but constraint checking eliminates many branches. Theoretical worst case is O(n!) but actual is much less due to diagonal constraints.

When an interviewer asks about complexity, it is acceptable to say: "The exact bound is complex to compute, but the recursion tree has at most X leaves because [reasoning], and we do O(Y) work per leaf, so the overall complexity is O(X * Y)." Showing you can reason about it is more valuable than memorizing the exact bound.

The final insight about backtracking: it is always complete (finds all solutions) and correct (never produces invalid solutions), but it is not always efficient. When you present a backtracking solution, always mention pruning opportunities — places where you can detect early that a branch cannot produce a valid solution and skip it. Good pruning transforms an impractical algorithm into one that runs in reasonable time.
