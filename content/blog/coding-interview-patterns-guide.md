---
title: "Coding Interview Pattern Recognition: The 15 Patterns That Cover 80% of Problems"
description: "Master the 15 core coding interview patterns — two pointers, sliding window, BFS/DFS, dynamic programming, heaps, and more — with examples and recognition cues for each pattern."
date: "2026-03-20"
category: "Algorithm Guides"
---

# Coding Interview Pattern Recognition: The 15 Patterns That Cover 80% of Problems

The secret to coding interview success isn't memorizing 500 LeetCode problems — it's recognizing which of a small set of patterns applies to a new problem. Once you can pattern-match reliably, you can solve problems you've never seen before. Here are the 15 patterns that appear in the vast majority of coding interviews.

## 1. Two Pointers

**When to use:** Sorted arrays, finding pairs with a target sum, comparing elements from both ends.

**Recognition cue:** "Find pair/triplet with sum X in sorted array," "remove duplicates in-place," "is palindrome."

**Example:** Find two numbers summing to target in sorted array.
```python
left, right = 0, len(nums) - 1
while left < right:
    s = nums[left] + nums[right]
    if s == target: return [left, right]
    elif s < target: left += 1
    else: right -= 1
```

## 2. Sliding Window

**When to use:** Contiguous subarray/substring problems with a constraint.

**Recognition cue:** "Longest/shortest subarray with property X," "maximum sum subarray of size K."

**Template:** Expand right, shrink left when constraint violated.
```python
left = max_len = 0
window = {}
for right, c in enumerate(s):
    window[c] = window.get(c, 0) + 1
    while len(window) > k:  # constraint check
        window[s[left]] -= 1
        if window[s[left]] == 0: del window[s[left]]
        left += 1
    max_len = max(max_len, right - left + 1)
```

## 3. Fast and Slow Pointers

**When to use:** Cycle detection in linked lists, finding middle of list.

**Recognition cue:** "Does this linked list have a cycle?" "Find middle node."

Fast pointer moves 2x; when fast reaches end (or meets slow), you have your answer.

## 4. Merge Intervals

**When to use:** Overlapping intervals — merging, inserting, finding gaps.

**Recognition cue:** "Given list of intervals, merge overlapping ones."

Sort by start time, then iterate: if current start ≤ last merged end, extend; otherwise append.

## 5. Cyclic Sort

**When to use:** Arrays containing numbers in range [1, n] — find missing/duplicate numbers in O(n) time, O(1) space.

**Recognition cue:** "Find missing number in [1, n]" without using extra space.

Place each number at its correct index (nums[i] = i+1), then scan for mismatches.

## 6. In-Place Linked List Reversal

**When to use:** Reverse a linked list or sub-list without extra space.

**Recognition cue:** "Reverse linked list from position m to n."

Three pointers: prev, curr, next. Iterate reversing links.

## 7. Tree BFS (Level Order Traversal)

**When to use:** Level-by-level tree traversal, connecting nodes at same level.

**Recognition cue:** "Return level order traversal," "connect right pointers at each level."

```python
from collections import deque
queue = deque([root])
while queue:
    level_size = len(queue)
    for _ in range(level_size):
        node = queue.popleft()
        if node.left: queue.append(node.left)
        if node.right: queue.append(node.right)
```

## 8. Tree DFS

**When to use:** Path-related problems in trees, finding all paths, path sums.

**Recognition cue:** "Find all root-to-leaf paths with sum X," "max path sum."

Choose preorder/inorder/postorder depending on when you need parent vs child info.

## 9. Two Heaps

**When to use:** Finding median from a stream, maintaining a running median.

**Recognition cue:** "Median of data stream," "schedule tasks with deadlines."

Max-heap for lower half, min-heap for upper half. Balance heaps after each insert.

## 10. Subsets / Combinations

**When to use:** Generate all subsets, permutations, or combinations.

**Recognition cue:** "Find all subsets," "all permutations," "all combinations summing to X."

BFS approach: start with empty set, for each element add it to all existing subsets.
Or backtracking recursion: include/exclude choice at each step.

## 11. Modified Binary Search

**When to use:** Sorted or rotated-sorted arrays; finding specific conditions.

**Recognition cue:** "Search in rotated sorted array," "find first/last occurrence," "minimum in rotated array."

The key: identify which half is sorted, then determine which half contains your target.

## 12. Top K Elements

**When to use:** Finding K largest/smallest elements, K most frequent.

**Recognition cue:** "K largest elements," "K most frequent words," "K closest points."

Min-heap of size K: push elements, pop when size exceeds K.
```python
import heapq
heap = []
for num in nums:
    heapq.heappush(heap, num)
    if len(heap) > k:
        heapq.heappop(heap)
return list(heap)
```

## 13. K-Way Merge

**When to use:** Merging K sorted arrays/lists.

**Recognition cue:** "Merge K sorted lists," "smallest range covering K lists."

Min-heap with (value, list_index, element_index). Pop minimum, push next element from same list.

## 14. 0/1 Knapsack (DP)

**When to use:** Optimization over a set of items, each used at most once.

**Recognition cue:** "Maximum profit with weight constraint," "subset sum equals target," "partition equal subset sum."

```python
dp = [False] * (target + 1)
dp[0] = True
for num in nums:
    for j in range(target, num - 1, -1):  # iterate backwards for 0/1
        dp[j] = dp[j] or dp[j - num]
```

## 15. Bitwise XOR

**When to use:** Finding single/missing numbers, complement problems.

**Recognition cue:** "Find the one number that appears once," "complement of binary number."

XOR of a number with itself is 0; XOR of a number with 0 is itself. XOR all elements — duplicates cancel.

## How to Apply Pattern Recognition in an Interview

When you see a new problem, run through these prompts:
1. Is the input sorted? → Two pointers, binary search, merge intervals
2. Does it involve a linked list? → Fast/slow pointers, reversal
3. Is it a tree problem about levels? → BFS. About paths? → DFS
4. Does it involve a stream or "running" state? → Two heaps, sliding window
5. Is it "find K best"? → Heap
6. Is it asking for all combinations? → Subsets/backtracking
7. Does it involve items with constraints? → DP (knapsack family)
8. Are there duplicate/missing numbers in a range? → Cyclic sort or XOR

State the pattern out loud: "This looks like a sliding window problem because we're looking for the longest subarray with at most K distinct characters." Interviewers reward pattern articulation — it signals structured thinking, not luck.
