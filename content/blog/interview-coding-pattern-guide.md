---
title: "Coding Interview Patterns: The 15 Patterns That Solve 90% of Problems"
description: "Master the 15 core coding interview patterns — sliding window, two pointers, fast/slow pointers, merge intervals, cyclic sort, tree traversal, binary search, and more with examples."
date: "2026-03-20"
category: "Interview Preparation"
---

# Coding Interview Patterns: The 15 Patterns That Solve 90% of Problems

The secret to coding interview success isn't memorizing 500 LeetCode problems — it's recognizing the underlying patterns. Most coding interview problems are variations of 15-20 fundamental patterns. When you can identify the pattern, the algorithm becomes obvious. Here are the patterns that appear most often in technical interviews.

## Pattern 1: Sliding Window

**When to use:** Problems involving contiguous subarrays or substrings where you need to find the longest/shortest/maximum/minimum meeting some condition.

**Recognition signals:** "Longest/shortest substring with condition X," "maximum sum subarray of size K," "minimum window containing all characters of..."

**How it works:** Maintain a window (start/end pointers). Expand the window by moving end. When a condition is violated, shrink the window by moving start.

**Classic problems:** Longest substring without repeating characters, maximum sum subarray of size K, minimum window substring.

## Pattern 2: Two Pointers

**When to use:** Sorted arrays or linked lists where you're searching for pairs, triplets, or comparing elements from both ends.

**Recognition signals:** Sorted array, finding pairs that sum to target, comparing from start/end, partitioning.

**How it works:** Place pointers at start and end (or at two positions). Move them based on comparison logic.

**Classic problems:** Two Sum (sorted array), 3Sum, Container with Most Water, Valid Palindrome.

## Pattern 3: Fast and Slow Pointers (Floyd's Cycle Detection)

**When to use:** Linked list cycle detection, finding the middle of a linked list, detecting cycles in arrays treated as linked lists.

**Recognition signals:** "Detect cycle in linked list," "find start of cycle," "find duplicate number without extra space."

**How it works:** Move fast pointer 2 steps, slow pointer 1 step. They meet if there's a cycle.

## Pattern 4: Merge Intervals

**When to use:** Problems involving intervals, overlapping ranges, scheduling.

**Recognition signals:** "Merge overlapping intervals," "insert interval," "meeting rooms," "employee free time."

**How it works:** Sort intervals by start time. Iterate through; merge current interval with last if they overlap (current start ≤ last end).

## Pattern 5: Cyclic Sort

**When to use:** Arrays containing numbers from 1 to N; finding missing/duplicate numbers.

**Recognition signals:** "Array contains numbers 1-N," "find missing number," "find all duplicates," "find the corrupt pair."

**How it works:** For each position i, place the number that belongs at index (number - 1). After sorting, numbers at wrong positions are the answer.

## Pattern 6: In-Place Reversal of Linked List

**When to use:** Reversing a linked list or part of it without extra memory.

**Classic problems:** Reverse a linked list, reverse sublist, rotate list.

## Pattern 7: Tree Breadth-First Search (BFS)

**When to use:** Traversing a tree level by level, finding minimum depth, level-order traversal, connecting nodes at same level.

**How it works:** Use a queue. Dequeue node, process it, enqueue its children.

**Classic problems:** Binary tree level order traversal, minimum depth of binary tree, connect level order siblings, zigzag traversal.

## Pattern 8: Tree Depth-First Search (DFS)

**When to use:** Path finding in trees, all paths from root to leaf, any recursive tree traversal.

**Recognition signals:** "Find path," "all paths," "validate BST," "tree diameter."

**Classic problems:** Path sum, all paths for a sum, tree diameter, binary tree path sum.

## Pattern 9: Two Heaps

**When to use:** Finding median in a data stream, situations requiring access to both the smallest of the large elements and the largest of the small elements.

**How it works:** Maintain a max-heap for the smaller half and a min-heap for the larger half. Balance them to keep sizes equal or differ by one.

**Classic problems:** Find median from data stream, sliding window median.

## Pattern 10: Subsets / Power Set

**When to use:** Generating all permutations, combinations, or subsets.

**How it works:** Start with empty set. For each element, add it to all existing subsets to create new subsets.

**Classic problems:** Subsets, permutations, letter case permutation, generate parentheses.

## Pattern 11: Modified Binary Search

**When to use:** Searching in sorted or partially sorted arrays, including rotated arrays.

**Recognition signals:** Sorted array (possibly rotated), "find first/last occurrence," "search in nearly sorted," "bitonic array."

**Classic problems:** Binary search, search in rotated sorted array, search in a 2D matrix, find first/last occurrence.

## Pattern 12: Bitwise XOR

**When to use:** Finding missing numbers, single numbers, or pairs using XOR properties (a XOR a = 0, a XOR 0 = a).

**Classic problems:** Single number, missing number, find two non-repeating numbers.

## Pattern 13: Top K Elements

**When to use:** Finding K largest/smallest/most frequent elements without fully sorting.

**How it works:** Use a min-heap of size K. For each element, if it's larger than the heap's minimum, replace it. O(N log K) instead of O(N log N).

**Classic problems:** Kth largest element, top K frequent elements, K closest points to origin.

## Pattern 14: K-way Merge

**When to use:** Merging K sorted arrays/lists, finding Kth smallest across K sorted structures.

**How it works:** Use a min-heap containing the current smallest element from each list with a pointer to which list it came from. Extract minimum, add the next element from that list.

**Classic problems:** Merge K sorted lists, Kth smallest in M sorted lists, smallest range covering K lists.

## Pattern 15: Dynamic Programming Patterns

**Recognizing DP problems:**
1. Optimization (maximize/minimize) or counting (how many ways)
2. Choices at each step affect future choices
3. Overlapping subproblems

**Core DP patterns:**
- **0/1 Knapsack:** For each item, include or exclude it. `dp[i][w] = max(dp[i-1][w], dp[i-1][w-weight[i]] + value[i])`
- **Unbounded Knapsack:** Items can be used multiple times (coin change — unlimited coins)
- **Fibonacci numbers:** Current value depends on previous values (house robber, climbing stairs)
- **Palindromic subsequence:** 2D DP expanding around centers
- **Longest Common Substring/Subsequence:** Classic 2D DP

**How to recognize which DP pattern:**
- "0 or 1" of each item? → 0/1 Knapsack
- Unlimited uses? → Unbounded Knapsack
- Depends on previous 1-2 values? → Fibonacci
- Involves two sequences? → LCS variants
- Involves palindromes? → Palindromic subsequence

The most efficient interview preparation strategy: for each of these 15 patterns, solve 2-3 canonical problems until you can implement them from memory. Then practice recognition — given a new problem, identify the pattern before looking at solutions.
