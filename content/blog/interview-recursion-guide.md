---
title: "Mastering Recursion in Interviews: Permutations, Subsets, and Divide-and-Conquer Patterns"
description: "A systematic guide to recursion problems in technical interviews — covering backtracking templates for permutations and subsets, divide-and-conquer patterns, memoization, and how to think about recursive state clearly under interview pressure."
date: "2026-03-20"
category: "Algorithms"
---

# Mastering Recursion in Interviews: Permutations, Subsets, and Divide-and-Conquer Patterns

Recursion problems make many engineers anxious in interviews. The anxiety usually comes from unclear mental models — candidates try to trace through recursive calls step by step, which doesn't scale to complex problems. The shift from tracing to trusting your recursive structure is what separates confident recursion from nervous trial-and-error.

## The Recursive Leap of Faith

The most important mindset shift: assume your recursive function works correctly for smaller inputs. Don't trace through it. Trust the contract.

If you're implementing merge sort, you don't trace through how `mergeSort(left)` sorts the left half — you trust that it does, then figure out how to combine sorted halves. This faith is not blind; it's the mathematical principle of induction applied to code.

When you're stuck on a recursive problem, ask: "If this function already worked for n-1 elements, how would I solve the n-element case?"

## Backtracking: The Universal Template

Backtracking solves problems where you build solutions incrementally and abandon paths that can't lead to a valid solution. The template is consistent across problem types:

```python
def backtrack(state, choices):
    if is_solution(state):
        record(state)
        return
    
    for choice in choices:
        if is_valid(state, choice):
            make_choice(state, choice)
            backtrack(new_state, remaining_choices)
            undo_choice(state, choice)  # The "backtrack" step
```

The undo step is the defining characteristic. Without it, you're doing DFS with a global state that corrupts across branches.

### Subsets (Power Set)

```python
def subsets(nums):
    result = []
    
    def backtrack(start, current):
        result.append(current[:])  # Snapshot at every node (not just leaves)
        
        for i in range(start, len(nums)):
            current.append(nums[i])
            backtrack(i + 1, current)
            current.pop()
    
    backtrack(0, [])
    return result
```

Key insight: record the result at **every** recursive call, not just base cases. Each node in the recursion tree represents a valid subset.

### Permutations

```python
def permute(nums):
    result = []
    
    def backtrack(current, remaining):
        if not remaining:
            result.append(current[:])
            return
        
        for i in range(len(remaining)):
            current.append(remaining[i])
            backtrack(current, remaining[:i] + remaining[i+1:])
            current.pop()
    
    backtrack([], nums)
    return result
```

For permutations with duplicates (LeetCode 47), sort the input first, then skip duplicates at the same recursion level:

```python
def permuteUnique(nums):
    result = []
    nums.sort()
    
    def backtrack(current, remaining):
        if not remaining:
            result.append(current[:])
            return
        
        seen = set()
        for i in range(len(remaining)):
            if remaining[i] in seen:
                continue
            seen.add(remaining[i])
            current.append(remaining[i])
            backtrack(current, remaining[:i] + remaining[i+1:])
            current.pop()
    
    backtrack([], nums)
    return result
```

### Combination Sum

```python
def combinationSum(candidates, target):
    result = []
    
    def backtrack(start, current, remaining):
        if remaining == 0:
            result.append(current[:])
            return
        if remaining < 0:
            return
        
        for i in range(start, len(candidates)):
            current.append(candidates[i])
            backtrack(i, current, remaining - candidates[i])  # i not i+1: reuse allowed
            current.pop()
    
    backtrack(0, [], target)
    return result
```

The `start` parameter is the key to avoiding duplicate combinations — we never look backward in the array.

## Divide and Conquer

Divide-and-conquer recursion follows a different pattern: split the problem, solve subproblems independently, then merge results.

### Merge Sort

```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    return result + left[i:] + right[j:]
```

Merge sort's invariant: both halves are sorted before merging. The merge step is O(n), and the recursion tree has O(log n) levels, giving O(n log n) total.

### Count Inversions

A beautiful extension: count pairs `(i, j)` where `i < j` but `arr[i] > arr[j]`. Modify merge sort to count while merging:

```python
def count_inversions(arr):
    if len(arr) <= 1:
        return arr, 0
    
    mid = len(arr) // 2
    left, left_inv = count_inversions(arr[:mid])
    right, right_inv = count_inversions(arr[mid:])
    merged, split_inv = merge_count(left, right)
    
    return merged, left_inv + right_inv + split_inv

def merge_count(left, right):
    result = []
    inversions = 0
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            inversions += len(left) - i  # All remaining left elements > right[j]
            j += 1
    return result + left[i:] + right[j:], inversions
```

## Memoization: Recursion Plus Cache

When a recursive function computes the same subproblems repeatedly, add memoization:

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
```

The mental model for when to memoize: if you draw the recursion tree and see subtrees appearing more than once, memoize. If every subproblem is unique, memoization adds overhead without benefit.

## Debugging Recursive Code

When a recursive solution is wrong, these are the most common culprits:

1. **Missing base case** — the function recurses forever or misses the trivial case
2. **Wrong base case** — returns an incorrect value for the simplest input
3. **Off-by-one in the recursive call** — passing `n-1` when you need `n-2`, or `start+1` vs `start`
4. **Mutating shared state without backtracking** — common with list arguments; always check if you're copying or mutating

When debugging, test the base case first, then test the simplest non-trivial case. If both are correct, trust the inductive step.

Recursion confidence comes from practice. Once you've implemented subsets, permutations, combination sum, and merge sort cleanly, the patterns become second nature and the anxiety disappears.
