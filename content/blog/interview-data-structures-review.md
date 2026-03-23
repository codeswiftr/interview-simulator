---
title: "Essential Data Structures Interview Review: Arrays, Trees, Graphs, and Hash Tables"
description: "A complete interview review of data structures — time and space complexity, implementation details, and the interview patterns where each structure shines. Covers arrays, linked lists, trees, graphs, heaps, and hash tables."
date: "2026-03-20"
category: "Algorithms"
---

# Essential Data Structures Interview Review: Arrays, Trees, Graphs, and Hash Tables

Data structures are the foundation of every coding interview. Beyond knowing what they are, interviewers expect you to know *when* to reach for each one, what the complexity guarantees are, and the implementation details that matter in practice. This review covers the structures that appear most frequently, with the depth required for senior-level interviews.

## Arrays and Dynamic Arrays

**Static array**: O(1) random access by index. O(n) insert/delete at arbitrary position (requires shifting). Best structure when you need fast indexed access and size is known.

**Dynamic array** (Python list, Java ArrayList): Amortized O(1) append because it allocates extra capacity and copies only when full. The copy happens when size reaches capacity — O(n) copy, but spread over n operations = O(1) amortized.

**Interview patterns**: Two-pointer, sliding window, prefix sums, Dutch national flag (3-way partition). Whenever you need to process elements in-place or track subarrays, start with arrays.

**Prefix sum pattern**: Precompute `prefix[i] = sum(arr[0..i-1])`. Range sum query `sum(l, r) = prefix[r+1] - prefix[l]` in O(1). 2D variant works the same way for rectangle sum queries.

## Linked Lists

**Singly linked**: O(1) insert/delete at head; O(n) at arbitrary position. O(n) search. No random access.

**Doubly linked**: O(1) insert/delete anywhere with a node pointer. Used in LRU Cache (combine with hash map for O(1) get/put).

**Key interview patterns**:
- **Two-pointer (fast/slow)**: Detect cycles, find middle, find Kth from end
- **Reverse in-place**: Iterative with three pointers (prev, curr, next)
- **Merge sorted lists**: Similar to merge sort merge step

**Common mistake**: Forgetting to handle null/None cases (empty list, single element). Always check edge cases explicitly.

## Binary Trees and BSTs

**Binary Tree**: Each node has at most two children. No ordering constraint.

**Binary Search Tree (BST)**: Left subtree values < node < right subtree values. In-order traversal yields sorted sequence. O(log n) search/insert/delete for balanced BST; O(n) worst case for degenerate (sorted input).

**Balanced BST variants**: AVL trees (height-balanced, strict), Red-Black trees (used in most standard library implementations — Java TreeMap, C++ std::map). Both guarantee O(log n) all operations.

**Interview traversals**: Know all four:
- **In-order** (left, root, right): Yields sorted BST sequence
- **Pre-order** (root, left, right): Copy tree structure, serialize
- **Post-order** (left, right, root): Delete tree, evaluate expression trees
- **Level-order** (BFS): Find minimum depth, zigzag traversal, right view

**Recursive DFS pattern** for tree problems:
```python
def solve(node):
    if not node:
        return base_case
    left = solve(node.left)
    right = solve(node.right)
    return combine(left, right, node.val)
```

## Heaps (Priority Queues)

**Min-heap**: Parent ≤ children. Root is always the minimum. O(log n) insert, O(log n) extract-min, O(1) peek-min.

**Max-heap**: Parent ≥ children. Root is always the maximum.

**Implementation**: Stored as an array. For node at index i: left child = 2i+1, right child = 2i+2, parent = (i-1)//2. This gives cache-efficient storage without pointer overhead.

**Interview patterns**:
- **Top-K elements**: Use min-heap of size K. If new element > heap root, remove root and insert new element. O(n log K).
- **Merge K sorted lists**: Insert first element from each list. Extract min, then insert next from that list. O(n log K) where n = total elements.
- **Sliding window maximum**: Use deque (monotonic queue) rather than heap — O(n).
- **Median maintenance**: Two heaps (max-heap for lower half, min-heap for upper half). Rebalance after each insert to keep sizes equal or differ by 1.

## Hash Tables

**Hash map**: Average O(1) get/put/delete. Worst case O(n) if many collisions (degenerate). Good hash function + load factor < 0.75 keeps average-case performance.

**Collision resolution**: Chaining (each bucket is a linked list) or open addressing (linear/quadratic probing). Python dicts use open addressing; Java HashMaps use chaining.

**Hash set**: Same underlying structure, just stores keys, not key-value pairs.

**Interview patterns**:
- **Frequency counting**: Count occurrences, find duplicates, detect anagrams
- **Two-sum**: For each element, check if (target - element) is in the set
- **Caching/memoization**: Map problem parameters to computed results

## Graphs

**Representations**: Adjacency list (O(V+E) space, efficient for sparse) or adjacency matrix (O(V²) space, efficient for dense, O(1) edge lookup).

**BFS**: Level-by-level traversal using a queue. Finds shortest path in unweighted graphs. O(V+E).

**DFS**: Depth-first using stack (explicit or call stack). Finds connected components, detects cycles, topological sort. O(V+E).

**Topological sort**: For DAGs. Two approaches:
1. **Kahn's algorithm**: BFS-based, process nodes with in-degree 0
2. **DFS-based**: Reverse post-order DFS

**Dijkstra's algorithm**: Shortest path in weighted graphs with non-negative edges. O((V+E) log V) with a min-heap. Fails with negative edges.

**Union-Find (Disjoint Set)**: Efficiently merge sets and check connectivity. Used for Kruskal's MST, cycle detection. Near O(1) per operation with path compression and union by rank.

**When to reach for each**:
- BFS: Shortest unweighted path, level-order traversal
- DFS: Connectivity, cycle detection, topological sort, all paths
- Dijkstra: Weighted shortest path
- Union-Find: Dynamic connectivity, MST

## Trie (Prefix Tree)

Node per character. Root represents empty string. Leaf or end-of-word flag marks complete words. O(L) insert/search where L = word length.

**Use cases**: Autocomplete, spell checking, IP routing tables, prefix matching. Significantly faster than hash map for prefix queries because hash maps don't support "all words starting with prefix" without linear scan.

## Choosing the Right Structure

| Need | Structure |
|------|-----------|
| Indexed access | Array |
| Insert/delete at head | Linked list |
| Min/max quickly | Heap |
| Sorted order + range queries | BST |
| Fast key lookup | Hash map |
| Prefix matching | Trie |
| Graph connectivity | Union-Find |

Knowing the right structure reduces a hard problem to a standard implementation. The decision between O(n) and O(log n) often hinges on choosing correctly here.
