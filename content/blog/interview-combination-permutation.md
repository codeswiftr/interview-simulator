---
title: "Combinations, Permutations, and Subsets: Interview Patterns for Backtracking Problems"
description: "Master the backtracking framework for generating combinations, permutations, and subsets — the pattern that underlies dozens of interview problems from sudoku solving to N-Queens."
date: "2026-03-20"
category: "Algorithms"
---

Backtracking problems share a common structure: build a solution incrementally, explore branches, and undo choices when a branch leads nowhere. Once you internalize the framework, combinations, permutations, subsets, and their variants all become instances of the same pattern with minor parameter changes.

## The Backtracking Template

```python
def backtrack(start, current_path, result):
    if base_case(current_path):
        result.append(current_path[:])  # copy, not reference
        return
    
    for choice in get_choices(start):
        if is_valid(choice, current_path):
            current_path.append(choice)
            backtrack(next_start(start, choice), current_path, result)
            current_path.pop()  # undo choice
```

The critical details:
- **Copy when adding to result:** `result.append(current_path[:])` — if you append the list directly, all entries in `result` will reference the same list and end up identical when the recursion finishes.
- **The undo step** (`current_path.pop()`) must always execute, even if the recursive call returns early. This is why it's not inside an `if` block.
- **`start` parameter** controls which elements are still available for selection, preventing re-use of elements.

## Subsets (Power Set)

Generate all subsets of a list. There are 2^n subsets for n elements.

```python
def subsets(nums):
    result = []
    
    def backtrack(start, path):
        result.append(path[:])  # add current subset (including empty)
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i + 1, path)
            path.pop()
    
    backtrack(0, [])
    return result
```

Key: we add the current path to result at every call (not just at a base case), because every partial path is a valid subset. Each element is either included or not — advancing `start` to `i + 1` ensures elements are not reused and maintains sorted order.

**Subsets II** (with duplicates, LeetCode 90): sort the input first, then skip duplicate elements at the same tree level:
```python
for i in range(start, len(nums)):
    if i > start and nums[i] == nums[i-1]:
        continue  # skip duplicate at same level
    # ... rest of backtrack
```

## Combinations

Generate all combinations of k elements from a set of n.

```python
def combine(n, k):
    result = []
    
    def backtrack(start, path):
        if len(path) == k:
            result.append(path[:])
            return
        # Pruning: remaining elements must be enough to complete the combination
        remaining = k - len(path)
        for i in range(start, n - remaining + 2):
            path.append(i)
            backtrack(i + 1, path)
            path.pop()
    
    backtrack(1, [])
    return result
```

The pruning condition `range(start, n - remaining + 2)` prevents exploring branches that can't produce a complete combination — if you need 2 more elements but only 1 is left, skip that branch. This optimization can matter significantly on larger inputs.

**Combination Sum** (LeetCode 39): elements can be reused, target sum must be reached. Change `backtrack(i + 1, ...)` to `backtrack(i, ...)` to allow reuse, and add a `total` parameter tracking the running sum.

**Combination Sum II** (LeetCode 40): each element used at most once, duplicates in input. Sort first, skip duplicates at same level (same technique as Subsets II).

## Permutations

Generate all permutations. There are n! permutations for n elements.

```python
def permutations(nums):
    result = []
    used = [False] * len(nums)
    
    def backtrack(path):
        if len(path) == len(nums):
            result.append(path[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True
            path.append(nums[i])
            backtrack(path)
            path.pop()
            used[i] = False
    
    backtrack([])
    return result
```

Unlike combinations, permutations don't have a `start` parameter — every position can use any unused element. The `used` array tracks which elements are currently in the path.

**Permutations II** (with duplicates, LeetCode 47): sort first, then add: `if i > 0 and nums[i] == nums[i-1] and not used[i-1]: continue`. This ensures that among duplicate elements, you always use the earlier one before the later one at the same recursion level.

**Swap-based permutations** (alternative implementation): swap `nums[start]` with each element from `start` to end, recurse on `start+1`, then swap back. Avoids the `used` array but is harder to extend to duplicates.

## Letter Combinations of a Phone Number (LeetCode 17)

This looks different but is the same backtracking pattern with a different choice set:

```python
def letter_combinations(digits):
    if not digits:
        return []
    phone_map = {"2": "abc", "3": "def", "4": "ghi", "5": "jkl",
                 "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz"}
    result = []
    
    def backtrack(idx, path):
        if idx == len(digits):
            result.append("".join(path))
            return
        for letter in phone_map[digits[idx]]:
            path.append(letter)
            backtrack(idx + 1, path)
            path.pop()
    
    backtrack(0, [])
    return result
```

The `start` concept here is `idx` — which digit position we're choosing letters for.

## N-Queens and Constraint Backtracking

N-Queens adds validity checking to the backtracking framework:

```python
def solve_n_queens(n):
    result = []
    cols = set()
    diag1 = set()  # row - col
    diag2 = set()  # row + col
    
    def backtrack(row, path):
        if row == n:
            result.append(["." * c + "Q" + "." * (n - c - 1) for c in path])
            return
        for col in range(n):
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue
            cols.add(col); diag1.add(row - col); diag2.add(row + col)
            backtrack(row + 1, path + [col])
            cols.remove(col); diag1.remove(row - col); diag2.remove(row + col)
    
    backtrack(0, [])
    return result
```

Sets for column and diagonal tracking give O(1) validity checks instead of O(n) scanning.

## Complexity Analysis

| Problem | Time | Space |
|---------|------|-------|
| Subsets | O(n × 2^n) | O(n) |
| Combinations C(n,k) | O(k × C(n,k)) | O(k) |
| Permutations | O(n × n!) | O(n) |
| N-Queens | O(n!) | O(n) |

Time complexity counts both the number of solutions generated and the work per solution (copying the path). Space is the recursion depth — O(n) for all these problems.

## Practice Order

- LeetCode 78 (Subsets) — base pattern
- LeetCode 90 (Subsets II) — handle duplicates
- LeetCode 46 (Permutations) — used array pattern
- LeetCode 39 (Combination Sum) — reuse allowed
- LeetCode 40 (Combination Sum II) — no reuse, duplicates
- LeetCode 17 (Letter Combinations) — different choice mapping
- LeetCode 51 (N-Queens) — constraint-based pruning
