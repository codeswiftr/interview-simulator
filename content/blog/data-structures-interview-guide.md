---
title: "Data Structures Interview Guide: Arrays, Trees, Graphs, and More"
description: "A comprehensive guide to the most-tested data structures in technical interviews — arrays, strings, trees, graphs, hash maps, and heaps — including when each is used, common patterns, and how to choose the right structure under pressure."
date: "2025-09-16"
category: "Interview Preparation"
---

# Data Structures Interview Guide: Arrays, Trees, Graphs, and More

Technical interviews at software companies overwhelmingly test the same core set of data structures. Not because these structures are the only ones that matter in production engineering, but because they reveal how a candidate thinks about trade-offs, memory, and time complexity. Understanding when to reach for a hash map versus a heap, or when a graph is the right model for a problem, separates candidates who have memorized solutions from those who can reason under novel constraints.

This guide covers the most-tested data structures, the patterns they unlock, and how to make confident choices during an interview.

## Arrays and Strings

Arrays and strings are the most common interview data structures by a wide margin. Almost every problem involves them at some level, and many problems that appear to be about something else — sliding windows, two pointers, sorting — are fundamentally array problems in disguise.

**When arrays are the right choice:** When you need O(1) random access, when you are iterating over a sequence, or when the problem involves subarrays, subsequences, or contiguous windows. Arrays are also the natural choice when input order matters and you need to preserve it.

**Core patterns to internalize:**

The *two-pointer pattern* works when you need to search for a pair or triplet that satisfies a condition. Sort the array first, then move a left pointer and a right pointer toward each other based on whether the current sum is too large or too small. This reduces O(n²) brute-force problems to O(n).

The *sliding window pattern* applies when the problem asks for the maximum or minimum of a contiguous subarray of fixed or variable size. Maintain a window of elements and slide it across the array, updating your running result rather than recalculating from scratch.

The *prefix sum pattern* lets you answer range sum queries in O(1) after O(n) preprocessing. If you find yourself nested-looping over subarrays to compute sums, prefix sums are almost always the right optimization.

For strings specifically, know how to check for anagrams using character frequency maps, how to implement basic string reversal and rotation, and how to handle Unicode correctly if the problem involves non-ASCII characters.

## Trees and Binary Search Trees

Trees appear in interviews more than any other non-linear data structure. Binary trees, binary search trees (BSTs), and n-ary trees all show up regularly, and the patterns that apply to them transfer across problem types.

**When trees are the right model:** When the problem involves hierarchical relationships, when you need to make binary decisions at each step (BST search, binary search), or when the structure of the problem is recursive in nature.

**Core patterns:**

*Depth-first search (DFS)* via recursion is the workhorse of tree problems. Preorder traversal (root → left → right) is useful when you need to process a node before its children. Inorder traversal (left → root → right) of a BST produces sorted output — a fact that unlocks many BST problems. Postorder traversal is useful when you need information from children before processing a parent, as in calculating subtree heights.

*Breadth-first search (BFS)* using a queue is the right choice when the problem involves levels — finding the minimum depth, connecting nodes at the same level, or returning a level-order traversal. Any time a problem mentions "nearest" or "shortest path in a tree," reach for BFS.

*BST invariants* are frequently the key to solving a problem in less than O(n) time. The fact that all left subtree values are less than the root and all right subtree values are greater allows you to prune search space dramatically. Practice problems where you need to validate a BST, find the kth smallest element, or identify the lowest common ancestor.

For interview purposes, also practice converting a tree to a different representation — tree to array, tree to linked list, or tree to another tree structure — as these transformations frequently appear as subproblems.

## Graphs

Graph problems intimidate many candidates, but the underlying algorithms — BFS, DFS, and Dijkstra — are the same ones that apply to trees. The key distinction is that graphs can have cycles and disconnected components, which requires explicit tracking of visited nodes.

**When graphs are the right model:** When the problem involves connections between entities with no inherent hierarchy — social networks, road maps, dependency chains, grid-based movement problems. Any time you see "connected components," "shortest path," or "reachable nodes," you are in graph territory.

**Core patterns:**

*BFS from a source node* gives you the shortest path in an unweighted graph. This applies to classic problems like finding the minimum number of moves in a grid, the shortest word transformation sequence, or the minimum hops between network nodes.

*DFS for connectivity* tells you whether two nodes are in the same connected component and lets you count components, detect cycles, and perform topological sorting. For cycle detection in directed graphs, use the three-state visited tracking (unvisited, in-progress, complete) rather than the two-state version.

*Union-Find (Disjoint Set Union)* is the right tool when the problem asks you to group elements into sets and check membership efficiently — detecting redundant connections, finding the number of provinces, or solving Kruskal's minimum spanning tree algorithm.

**Dijkstra's algorithm** is essential for weighted shortest-path problems. It uses a min-heap (priority queue) to always expand the lowest-cost frontier node first. Practice implementing it from scratch, including the heap-based version.

## Hash Maps and Sets

Hash maps are the most powerful problem-solving tool in the average candidate's toolkit. When you find yourself thinking "I need to look up X quickly" or "I need to count occurrences of Y," a hash map is almost certainly the answer.

**When hash maps are the right choice:** When you need O(1) average-case lookup, insertion, or deletion. When the problem involves counting frequencies, grouping elements by a key, or checking for previously seen values.

**Core patterns:**

The *frequency map* pattern counts occurrences of each element and enables anagram detection, majority element problems, and top-K frequency problems. Build the map in one pass, then process it.

The *complement search* pattern — used in Two Sum and similar problems — stores values you have already seen in a set and checks whether the complement of the current element exists. This converts an O(n²) nested loop into O(n).

The *grouping pattern* uses a computed key to group elements. For grouping anagrams, the key is the sorted string. For grouping numbers by their difference, the key is a modular value. Practice identifying what the grouping key should be.

Sets are the simpler cousin of hash maps — use them when you only need membership testing, not value lookup. Cycle detection in linked lists, duplicate elimination, and intersection/union operations are natural set problems.

## Heaps and Priority Queues

Heaps are the data structure most candidates underestimate. They are the right tool for any problem involving "the K largest," "the K smallest," or "the next minimum/maximum" — patterns that appear far more often than they seem to at first glance.

**When heaps are the right choice:** When you need repeated access to the minimum or maximum element, and the set of elements is changing over time (elements are added or removed as you process the input).

**Core patterns:**

*Top-K elements* using a min-heap of size K: iterate through all elements and maintain a heap that always contains the K largest seen so far. When the heap grows beyond K, pop the minimum. The remaining heap contains the K largest elements in O(n log K) time — better than sorting the entire array.

*K-way merge* using a min-heap: when merging K sorted lists or arrays, push the first element of each list into a min-heap. Repeatedly pop the minimum, add it to the result, and push the next element from the same list. This runs in O(n log K) instead of O(n log n).

*Median of a data stream* uses two heaps — a max-heap for the lower half and a min-heap for the upper half — balanced so that the median is always at the top of one or both heaps. This is a classic problem that rewards knowing the pattern cold.

## Choosing the Right Structure During an Interview

When you see a new problem, resist the urge to immediately start coding. Take thirty seconds to ask: what operations does this problem need? If it needs fast lookup, that is a hash map. If it needs ordered traversal, that is a tree or sorted array. If it needs repeated minimum access, that is a heap. If it involves connections between entities, that is a graph.

Then ask: what is the shape of the optimal solution? Problems with O(n log n) solutions almost always involve sorting or a heap. Problems with O(n) solutions usually involve a hash map or a two-pointer approach. Problems with O(log n) solutions involve binary search or a BST.

Connecting operation requirements to data structure properties — rather than matching problem descriptions to memorized solutions — is what allows you to handle unfamiliar problems confidently. That reasoning process, made visible to your interviewer, is what data structure interviews are ultimately designed to assess.
