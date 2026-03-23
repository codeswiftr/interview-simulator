---
title: "Backtracking Advanced: N-Queens, Sudoku, and Word Search Patterns"
description: "Advanced backtracking for technical interviews — N-Queens, Sudoku solver, word search, regular expression matching, generate valid parentheses, subsets, permutations II, and the pruning strategies that make backtracking efficient."
date: "2026-03-20"
category: "Algorithms"
---

# Backtracking Advanced: N-Queens, Sudoku, and Word Search Patterns

Backtracking is the technique of exploring all possible solutions by incrementally building candidates and abandoning them ("backtracking") as soon as you determine they can't lead to a valid solution. The key to making backtracking efficient is pruning — cutting off search branches early.

## The Backtracking Template

```python
def backtrack(state, choices):
    if is_solution(state):
        record(state)
        return
    
    for choice in choices:
        if is_valid(choice, state):
            make_choice(state, choice)
            backtrack(state, next_choices(choices, choice))
            undo_choice(state, choice)
```

Always: try a choice, recurse, undo the choice. The undo step is what makes backtracking work — it restores state for the next candidate.

## N-Queens

Place N queens on an N×N board so no two queens share a row, column, or diagonal.

Pruning insight: place one queen per row (eliminates row conflicts). For each row, try each column. Skip if the column or either diagonal is already occupied.

```python
def solveNQueens(n):
    results = []
    cols = set()
    diag1 = set()  # row - col (constant along / diagonal)
    diag2 = set()  # row + col (constant along \ diagonal)
    board = [['.' for _ in range(n)] for _ in range(n)]
    
    def backtrack(row):
        if row == n:
            results.append([''.join(r) for r in board])
            return
        for col in range(n):
            if col in cols or (row-col) in diag1 or (row+col) in diag2:
                continue
            cols.add(col); diag1.add(row-col); diag2.add(row+col)
            board[row][col] = 'Q'
            backtrack(row + 1)
            cols.remove(col); diag1.remove(row-col); diag2.remove(row+col)
            board[row][col] = '.'
    
    backtrack(0)
    return results
```

Using sets for column and diagonal tracking gives O(1) conflict checking vs O(N) scanning.

## Sudoku Solver

Fill the 9×9 Sudoku grid satisfying all constraints.

Strategy: find the empty cell with the fewest valid options (most constrained first) — reduces branching factor. For each valid value, place it and recurse.

```python
def solveSudoku(board):
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    empty = []
    
    for r in range(9):
        for c in range(9):
            if board[r][c] == '.':
                empty.append((r, c))
            else:
                n = int(board[r][c])
                rows[r].add(n); cols[c].add(n); boxes[r//3*3+c//3].add(n)
    
    def backtrack(idx):
        if idx == len(empty): return True
        r, c = empty[idx]
        box = r//3*3+c//3
        for n in range(1, 10):
            if n not in rows[r] and n not in cols[c] and n not in boxes[box]:
                rows[r].add(n); cols[c].add(n); boxes[box].add(n)
                board[r][c] = str(n)
                if backtrack(idx + 1): return True
                rows[r].remove(n); cols[c].remove(n); boxes[box].remove(n)
                board[r][c] = '.'
        return False
    
    backtrack(0)
```

## Word Search

Given a grid of characters, check if a word exists as a path of adjacent cells (no cell reused).

```python
def exist(board, word):
    rows, cols = len(board), len(board[0])
    visited = set()
    
    def dfs(r, c, idx):
        if idx == len(word): return True
        if r < 0 or r >= rows or c < 0 or c >= cols: return False
        if board[r][c] != word[idx]: return False
        if (r, c) in visited: return False
        
        visited.add((r, c))
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            if dfs(r+dr, c+dc, idx+1): return True
        visited.remove((r, c))
        return False
    
    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0): return True
    return False
```

**Pruning:** Early termination when character doesn't match. Check remaining count — if remaining characters > remaining cells, prune (though this requires knowing grid structure).

## Subsets with Duplicates

Generate all unique subsets when input has duplicates. Sort first, then skip duplicate elements at the same recursion level.

```python
def subsetsWithDup(nums):
    nums.sort()
    result = []
    
    def backtrack(start, current):
        result.append(current[:])
        for i in range(start, len(nums)):
            if i > start and nums[i] == nums[i-1]:
                continue  # skip duplicate at same level
            current.append(nums[i])
            backtrack(i + 1, current)
            current.pop()
    
    backtrack(0, [])
    return result
```

The duplicate-skip pattern (`i > start and nums[i] == nums[i-1]`) is reusable for permutations with duplicates, combination sum II, and other "avoid duplicate solutions" problems.

## Generate Parentheses

Generate all valid combinations of N pairs of parentheses.

```python
def generateParenthesis(n):
    result = []
    
    def backtrack(current, open_count, close_count):
        if len(current) == 2 * n:
            result.append(current)
            return
        if open_count < n:
            backtrack(current + '(', open_count + 1, close_count)
        if close_count < open_count:
            backtrack(current + ')', open_count, close_count + 1)
    
    backtrack('', 0, 0)
    return result
```

The constraint `close_count < open_count` is the pruning that prevents invalid states. We never need to explore or backtrack from invalid partial sequences — the constraint prevents them.

## Pruning Strategies

**Constraint checking:** Before recursing, verify the partial solution doesn't violate constraints (like the N-Queens diagonal check).

**Bound checking:** If the remaining elements can't possibly complete the solution (e.g., need sum K but remaining elements are all larger), prune.

**Canonicalization:** Sort input and skip duplicates at the same recursion level to avoid generating duplicate solutions.

**Most-constrained-first:** Try the choice with the fewest valid options first (like Sudoku's "minimum remaining values" heuristic) — reduces the branching factor early.

The time complexity of backtracking is often O(K^N) where K is the branching factor and N is the depth. Pruning reduces the actual states explored, often dramatically — the difference between a timeout and an accepted solution.

