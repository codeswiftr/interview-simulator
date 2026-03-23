---
title: "Data Structures Interview Cheatsheet: Complexity, Use Cases, and Tradeoffs"
description: "Complete reference for data structure interview questions — time/space complexity for all major structures, when to use each, tradeoffs, and common interview patterns."
date: "2026-03-20"
category: "Algorithms"
---

# Data Structures Interview Cheatsheet: Complexity, Use Cases, and Tradeoffs

Choosing the right data structure is half the solution to most interview problems. This guide covers every major data structure with its complexity profile, ideal use cases, and the tradeoffs that interviewers expect you to articulate. Use it as both a study reference and a quick review before interviews.

## Arrays, Linked Lists, and Deques

**Array** (dynamic: `ArrayList`, `vector`): O(1) random access by index, O(1) amortized append, O(n) insert or delete at arbitrary position (shifting required). Best for indexed access, iteration, and cache-friendly traversal. The memory layout is contiguous, making arrays the fastest structure for sequential reads.

**Linked list**: O(1) insert/delete at a known node, O(n) access by index. No contiguous memory requirement, so it does not have the shifting cost of arrays. In practice, poor cache locality makes linked lists slower than arrays for most real workloads even when asymptotic complexity favors them. Use when you need frequent insert/delete in the middle of a sequence and you already hold a pointer to the position.

**Deque (double-ended queue)**: O(1) insert and delete at both ends. `ArrayDeque` in Java and `collections.deque` in Python are implemented as ring buffers or chunked arrays, not linked lists, so they retain cache efficiency. Use deques for sliding window problems, BFS queues, and monotonic queue patterns.

Tradeoff summary: array for read-heavy workloads, linked list for pointer-heavy manipulation (e.g., LRU cache node splicing), deque for two-ended access.

## Hash Maps and Hash Sets

**Hash map** (unordered): O(1) average insert, lookup, and delete. O(n) worst case when all keys hash to the same bucket (rare with good hash functions). Space: O(n).

Internally, a hash map maintains an array of buckets. Each bucket holds either a single entry (open addressing with probing) or a linked list / tree of entries (chaining). Java's `HashMap` uses chaining and converts chains to red-black trees when a bucket exceeds 8 entries (Java 8+), giving O(log n) worst-case lookup per bucket instead of O(n).

Collision resolution matters in interviews: **separate chaining** (each bucket is a list), **linear probing** (next open slot), and **quadratic probing** (quadratic distance on collision). Linear probing has better cache performance but suffers from primary clustering.

Use hash maps for: frequency counts, two-sum style lookup, memoization, and grouping items by key. Use hash sets for: membership testing, deduplication, and cycle detection in graphs (visited set).

**Ordered map** (`TreeMap` in Java, `SortedDict` equivalent): O(log n) all operations, maintains sorted order. Use when you need range queries, ceiling/floor lookups, or ordered iteration alongside insertion.

## Tree Structures

**Binary Search Tree (BST)**: O(log n) average search, insert, delete; O(n) worst case (degenerate/unbalanced). BSTs are the foundation — understand the invariant (left subtree < node < right subtree) and in-order traversal (produces sorted output).

**Balanced BSTs (AVL, Red-Black)**: Maintain O(log n) worst-case for all operations through rotations. `TreeMap` and `TreeSet` in Java use a Red-Black tree. AVL trees are height-balanced (balance factor ≤ 1); Red-Black trees use color properties for a looser balance with fewer rotations. For interviews, know which operations use them (ordered maps, sorted sets) without needing to implement rotations from scratch.

**Heap (binary heap)**: O(1) find-min/max, O(log n) insert, O(log n) extract-min/max. Implemented as an array (parent at index i, children at 2i+1 and 2i+2). Min-heaps support efficient priority queues. Use heaps for: top-K problems, Dijkstra's algorithm, median maintenance (two heaps), and merge K sorted lists.

**Trie (prefix tree)**: O(m) insert and search where m is the key length (independent of n, the number of keys). Space proportional to total characters stored (with sharing of common prefixes). Use for: autocomplete, prefix search, word dictionaries, IP routing. Each node typically has up to 26 children (lowercase letters) or 128/256 for ASCII.

## Graph Representations

**Adjacency list**: O(V + E) space, O(degree(v)) to enumerate neighbors. Preferred for sparse graphs. In most interview problems, graphs are given as edge lists that you convert to adjacency lists before running BFS/DFS.

**Adjacency matrix**: O(V²) space, O(1) edge existence check, O(V) to enumerate neighbors. Use for dense graphs or when constant-time edge queries are critical (e.g., Floyd-Warshall).

For interviews, always ask whether the graph is directed or undirected, weighted or unweighted, and whether it can have cycles. These properties determine which algorithm applies.

## Complexity Reference Table

| Structure | Access | Search | Insert | Delete | Space |
|---|---|---|---|---|---|
| Array | O(1) | O(n) | O(n) | O(n) | O(n) |
| Linked List | O(n) | O(n) | O(1)* | O(1)* | O(n) |
| Hash Map | — | O(1) avg | O(1) avg | O(1) avg | O(n) |
| BST (balanced) | — | O(log n) | O(log n) | O(log n) | O(n) |
| Heap | O(1) min | — | O(log n) | O(log n) | O(n) |
| Trie | — | O(m) | O(m) | O(m) | O(n·m) |

*at a known position

## Choosing the Right Structure in Interviews

The decision pattern: start with the query type the problem needs most.

- Need O(1) lookup by key? Hash map.
- Need sorted order or range queries? Balanced BST / sorted map.
- Need min or max repeatedly? Heap.
- Need prefix matching? Trie.
- Need two-ended queue? Deque.
- Need graph traversal? Adjacency list + BFS or DFS.

The second question is space: can you afford O(n) extra space? Most interview problems allow it. If the problem says "in-place" or "O(1) extra space," reconsider — you may need to use the input structure itself or a mathematical property.

State the tradeoffs explicitly when explaining your choice. "I'm using a hash map here for O(1) lookup at the cost of O(n) extra space. An alternative would be sorting the input and using binary search, which uses O(1) extra space but O(n log n) time." This kind of analysis is what distinguishes strong candidates from those who just code the first solution that comes to mind.
