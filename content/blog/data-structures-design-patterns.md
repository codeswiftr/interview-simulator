---
title: "Data Structure Design Patterns: When to Use What in Coding Interviews"
description: "A practical framework for choosing the right data structure in coding interviews — hash maps, heaps, tries, segment trees, and how to identify patterns quickly."
date: "2026-03-20"
category: "Algorithms"
---

# Data Structure Design Patterns: When to Use What in Coding Interviews

One of the most valuable skills in coding interviews is quickly identifying which data structure belongs in a solution. This isn't about memorizing — it's about recognizing problem patterns and mapping them to structures that make the solution efficient. Here's a practical framework.

## The Core Question: What Operation Do You Need to Be Fast?

Every data structure optimizes certain operations at the expense of others. Before choosing, ask: what operation happens repeatedly in the inner loop?

- **O(1) lookup by key?** → Hash map
- **O(log n) ordered access?** → Balanced BST, heap, sorted list
- **O(log n) prefix queries?** → Trie
- **O(log n) range queries with updates?** → Segment tree, Fenwick tree
- **Near-O(1) union and find?** → Union-Find (DSU)
- **LIFO ordering?** → Stack
- **FIFO ordering?** → Queue, deque

Start by identifying the bottleneck operation, then select the data structure that makes it efficient.

## Hash Map: The Swiss Army Knife

Hash maps appear in roughly 60% of coding interview solutions. They provide O(1) average-case lookup, insert, and delete.

**Classic patterns:**
- Frequency counting: `Counter(arr)` in Python, `defaultdict(int)` — count occurrences
- Complement lookup: Two Sum — for each element, check if `target - element` is in the map
- Group by key: Group anagrams — use sorted string as key, group values
- Memoization: Cache computed results in recursion

**When NOT to use:** when you need ordered operations (use TreeMap/SortedDict), or when keys are ranges (use segment tree).

## Heap: Top-K and Streaming Minimums/Maximums

A heap gives O(log n) insert and O(1) peek at the minimum (min-heap) or maximum (max-heap), with O(log n) extraction.

**Classic patterns:**
- Top-K elements: Maintain a min-heap of size K. When heap size exceeds K, pop the minimum. Result: K largest elements. O(n log K).
- K-th largest element: Same pattern — maintain a size-K min-heap; the root is the K-th largest.
- Merge K sorted lists: Min-heap of (value, list_index, element_index) — always extract minimum and push the next element from that list.
- Scheduling/task management: Priority queue where priority is deadline or cost.

**Key insight:** A heap doesn't give you arbitrary sorted order — only efficient access to the current extreme. If you need the 5th smallest of a range query, you need a different structure.

## Stack: Matching and History

Stacks enforce LIFO. The pattern: "something about the most recent element matters."

**Classic patterns:**
- Balanced parentheses: Push open brackets, pop and verify when closing bracket seen
- Monotonic stack (see separate guide): Next greater/smaller element
- Expression evaluation: Evaluate infix expressions with operator precedence
- DFS iteratively: Use explicit stack instead of recursion
- Undo history: Each action pushed; pop to undo

**Signature:** whenever you need to refer back to "the thing you were just processing" before moving to the next thing.

## Trie: Prefix and String Problems

A trie is a tree where each node represents a character and paths from root to leaves spell words. O(L) operations where L is string length.

**Classic patterns:**
- Autocomplete: Insert words; to find completions, traverse to the prefix node, then DFS all paths from there
- Spell checker / word validation: Insert dictionary; lookup word
- Longest common prefix: The path from root to the point where the trie branches is the common prefix
- Word search in matrix: Combined with DFS, trie prunes paths that don't lead to valid words (Word Search II)

**When to prefer hash set over trie:** if you only need exact word lookup, a hash set is simpler. Trie is worth it when prefix queries matter.

## Union-Find: Connectivity and Components

Union-Find answers "are X and Y connected?" and "connect X and Y" in nearly O(1) with path compression and union by rank.

**Classic patterns:**
- Connected components: Process edges one by one; union endpoints; count distinct roots at the end
- Cycle detection in undirected graphs: If `find(u) == find(v)` before union, edge creates a cycle
- Minimum spanning tree (Kruskal): Sort edges by weight; add edge if it doesn't create cycle (union-find check)
- Dynamic connectivity: Process connectivity queries in order

**Key distinction from BFS/DFS:** Union-Find is incremental — it handles dynamic edge additions efficiently. BFS/DFS requires the full graph upfront. Use Union-Find when you're processing edges one at a time.

## Deque: Sliding Window Extremes

A deque (double-ended queue) supports O(1) insertion and deletion from both ends.

**Classic patterns:**
- Sliding window maximum: Maintain a decreasing deque of indices. When the window slides, pop from front if the index is out of window. Pop from back while the new element is larger than back. Front always holds the maximum.
- BFS with priority: 0-1 BFS uses a deque where cost-0 edges go to front, cost-1 edges go to back.

## Choosing Between Segment Tree and Fenwick Tree

Both solve range query + point update in O(log n). The practical choice:

**Fenwick tree (BIT):** Simpler code, less memory, but limited to operations with inverses (sum, XOR — not min/max). If the problem fits, prefer Fenwick for cleaner code.

**Segment tree:** More complex, but handles any associative operation (min, max, GCD, custom). Required for range updates with lazy propagation.

## The Decision Framework in Practice

When you see a problem:
1. **Identify the operations** that need to be fast (lookup, insert, min/max, range query, connectivity)
2. **Match to a data structure** using the operation → structure mapping
3. **State the complexity** before coding: "With a min-heap, each operation is O(log n), total O(n log n)"
4. **Code the structure** — if standard, use the library; if custom (trie, segment tree), outline the class

The ability to name the structure, justify it with complexity, and code it cleanly is exactly what interviewers assess in algorithm rounds. Practice this framework until it's automatic.
