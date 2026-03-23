---
title: "25 Essential Coding Patterns for Technical Interviews: A Visual Guide"
description: "Master the 25 most important algorithmic patterns — two pointers, sliding window, BFS/DFS, dynamic programming, binary search, and more, with when to use each pattern and practice problems."
date: "2026-03-20"
category: "Interview Preparation"
---

# 25 Essential Coding Patterns for Technical Interviews: A Visual Guide

Technical interview success depends less on knowing thousands of LeetCode problems and more on recognizing a small set of patterns that apply to most problems. Once you can identify which pattern a problem requires, the implementation follows naturally. This guide covers 25 essential patterns, when each applies, and which problems exemplify them.

## Pattern Group 1: Array and String Manipulation

**1. Two Pointers**: Two indices moving through an array, typically from opposite ends or at different speeds. *When to use*: sorted array problems, palindrome checking, pair-finding with a target sum, removing duplicates in-place. *Example problems*: Two Sum II, Container with Most Water, Valid Palindrome.

**2. Sliding Window**: A window of fixed or variable size slides through an array/string. *When to use*: "longest/shortest subarray/substring" problems, all problems with contiguous element constraints. *Example problems*: Maximum Sum Subarray of Size K, Longest Substring Without Repeating Characters, Minimum Window Substring.

**3. Prefix Sums**: Precompute cumulative sums for O(1) range queries. *When to use*: problems involving sums or counts over subarrays. *Example problems*: Subarray Sum Equals K, Range Sum Query.

**4. Hash Map Frequency Count**: Count occurrences for O(1) lookup. *When to use*: anagram detection, duplicate finding, frequency-based problems. *Example problems*: Group Anagrams, Top K Frequent Elements.

## Pattern Group 2: Binary Search

**5. Standard Binary Search**: Eliminate half the search space each iteration. *When to use*: sorted arrays, "find target" problems. O(log n) time.

**6. Binary Search on Answer Space**: Search on possible answers, not the array itself. *When to use*: "minimum maximum" or "maximum minimum" problems, feasibility queries. *Example problems*: Koko Eating Bananas, Capacity to Ship Packages.

**7. Rotated Array Binary Search**: Modified binary search for rotated sorted arrays. *When to use*: any problem mentioning "rotated sorted array." *Example*: Search in Rotated Sorted Array.

## Pattern Group 3: Linked Lists

**8. Fast and Slow Pointers (Floyd's Cycle Detection)**: Two pointers at different speeds detect cycles or find midpoints. *When to use*: cycle detection, finding the middle node, nth from end. *Example problems*: Linked List Cycle, Middle of the Linked List.

**9. Reversal**: Reverse a linked list or sublists. *When to use*: reordering, palindrome checking, rotation problems. *Example problems*: Reverse Linked List, Reverse Nodes in k-Group.

## Pattern Group 4: Trees

**10. DFS Tree Traversal**: Depth-first exploration of tree structure. *When to use*: path problems, tree validation, subtree operations. *Variants*: preorder, inorder, postorder.

**11. BFS Level-Order Traversal**: Process nodes level by level using a queue. *When to use*: level-based problems, minimum depth, zigzag traversal. *Example problems*: Binary Tree Level Order Traversal, Minimum Depth of Binary Tree.

**12. Path Problems**: Track current path and check properties. *When to use*: root-to-leaf path sum, maximum path sum, all root-to-leaf paths. Recursion with state is the typical implementation.

## Pattern Group 5: Graphs

**13. BFS on Graphs**: Shortest path in unweighted graphs, component exploration. *When to use*: minimum steps/moves, word ladder, spread problems. *Example problems*: Number of Islands (treat grid as graph), Word Ladder.

**14. DFS on Graphs**: Deep exploration, connected components, cycle detection. *When to use*: connectivity problems, topological considerations. *Example problems*: Course Schedule, Clone Graph.

**15. Union-Find (Disjoint Set)**: Track connected components efficiently. *When to use*: dynamic connectivity, minimum spanning tree (Kruskal's), cycle detection in undirected graphs. *Example problems*: Number of Connected Components, Redundant Connection.

**16. Topological Sort (Kahn's Algorithm)**: Order nodes with dependencies. *When to use*: dependency resolution, course prerequisite problems. *Example problems*: Course Schedule II, Task Scheduler.

## Pattern Group 6: Dynamic Programming

**17. 1D DP**: Single array of subproblem solutions. *When to use*: Fibonacci variants, climbing stairs, coin change, house robber. State is usually index or amount.

**18. 2D DP**: 2D table of subproblem solutions. *When to use*: string comparison (edit distance, LCS), grid path problems, knapsack. *Example problems*: Longest Common Subsequence, Unique Paths.

**19. Interval DP**: DP on intervals of an array. *When to use*: palindrome partitioning, burst balloons, matrix chain multiplication.

**20. State Machine DP**: Finite number of states with transitions. *When to use*: stock trading problems (buy/sell/hold/cooldown states), regex matching.

## Pattern Group 7: Heap and Sorting

**21. K-th Largest/Smallest**: Min-heap of size k for k-th largest. *When to use*: any problem involving "k-th" in a stream or large dataset. *Example problems*: Kth Largest Element in a Stream, K Closest Points.

**22. Merge K Sorted Lists**: Min-heap to merge K sorted sequences. *When to use*: merging sorted data sources. *Example problems*: Merge K Sorted Lists, Find K Pairs with Smallest Sums.

## Pattern Group 8: Backtracking

**23. Subsets/Permutations**: Generate all valid combinations. *When to use*: "all possible" combinations, N-Queens, Sudoku solver. *Template*: choose element → recurse → undo choice.

**24. Decision Tree Pruning**: Prune invalid branches early. *When to use*: constraint satisfaction with early termination opportunity significantly reduces time complexity.

## Pattern Group 9: Greedy

**25. Greedy with Sorting**: Sort by one criterion, greedily pick. *When to use*: interval scheduling, meeting rooms, assignment problems. Proof of correctness typically via exchange argument. *Example problems*: Merge Intervals, Jump Game, Meeting Rooms II.

## How to Apply Pattern Recognition

When you see a problem:
1. Identify the input type (array? string? tree? graph?)
2. Identify the question type (finding? counting? optimizing? validating?)
3. Note any constraints (sorted? positive numbers? k elements?)
4. Map to pattern: sorted + finding → binary search; "longest subarray" → sliding window; "all combinations" → backtracking

**Practice method**: For each problem you solve, explicitly name the pattern used. After 100 problems, pattern recognition becomes automatic. The patterns don't change — only the specific implementation varies.

Knowing these 25 patterns provides a mental toolkit that covers >90% of LeetCode medium problems and most hard problems (which combine 2-3 patterns). Master the patterns, not the problems.
