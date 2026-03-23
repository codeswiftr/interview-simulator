---
title: "Data Structures & Algorithms Cheat Sheet: Time Complexity + Interview Patterns (2026)"
description: "The definitive data structures and algorithms reference for technical interview preparation. Big O complexity tables, the top 20 algorithm patterns with Python templates, and a decision guide for choosing the right data structure."
author: "CodeSwiftr Team"
date: "2026-03-19"
tags: ["data structures", "algorithms", "big O notation", "coding interview", "cheat sheet", "Python"]
keywords: ["data structures algorithms cheat sheet", "big O notation", "algorithm complexity", "time complexity cheat sheet", "algorithm patterns interview", "coding interview reference"]
readTime: "13 min read"
slug: "data-structures-algorithms-cheat-sheet"
image: "/images/blog/data-structures-algorithms-cheat-sheet.jpg"
---

# Data Structures & Algorithms Cheat Sheet: Time Complexity + Interview Patterns (2026)

*Print this. Bookmark this. Internalize this. This is the complete reference for every data structure and algorithm pattern that appears in software engineering interviews.*

---

This is not a gentle introduction to data structures. This is the reference document you reach for during active interview preparation — dense, precise, and organized for rapid pattern recognition. Every table here is something you should be able to reconstruct from memory after sufficient practice. Every code template is the exact structure you want internalized before walking into an interview room.

---

## Big O Complexity Reference

### Time Complexity Hierarchy

From fastest to slowest (for large N):

| Complexity | Name | Example |
|------------|------|---------|
| O(1) | Constant | Hash table lookup, array index access |
| O(log n) | Logarithmic | Binary search, BST operations |
| O(n) | Linear | Linear scan, single-pass traversal |
| O(n log n) | Linearithmic | Merge sort, heap sort, most comparison sorts |
| O(n²) | Quadratic | Bubble sort, insertion sort, naive nested loops |
| O(n³) | Cubic | Floyd-Warshall (dense graphs), naive matrix multiply |
| O(2ⁿ) | Exponential | Recursive Fibonacci without memo, power set generation |
| O(n!) | Factorial | Permutation generation, traveling salesman brute force |

**Rule of thumb for interview constraints:**
- N ≤ 10: O(n!) or O(2ⁿ) acceptable
- N ≤ 20: O(2ⁿ) acceptable
- N ≤ 100: O(n³) acceptable
- N ≤ 1,000: O(n²) acceptable
- N ≤ 100,000: O(n log n) required
- N ≤ 10,000,000: O(n) required
- N unlimited: O(log n) or O(1) required

---

### Data Structure Time Complexity — Complete Table

| Data Structure | Access | Search | Insert | Delete | Notes |
|----------------|--------|--------|--------|--------|-------|
| Array | O(1) | O(n) | O(n) | O(n) | O(1) append at end (amortized) |
| Dynamic Array (list) | O(1) | O(n) | O(n) | O(n) | O(1) amortized append |
| Linked List | O(n) | O(n) | O(1) | O(1) | O(1) with pointer to node |
| Stack | O(n) | O(n) | O(1) | O(1) | LIFO; top access O(1) |
| Queue | O(n) | O(n) | O(1) | O(1) | FIFO; front/back O(1) |
| Hash Table | O(1) avg | O(1) avg | O(1) avg | O(1) avg | O(n) worst case (collisions) |
| Binary Search Tree | O(log n) avg | O(log n) avg | O(log n) avg | O(log n) avg | O(n) worst case (skewed) |
| AVL Tree | O(log n) | O(log n) | O(log n) | O(log n) | Self-balancing BST |
| Heap (Binary) | O(1) min/max | O(n) | O(log n) | O(log n) | Heapify: O(n) |
| Trie | — | O(m) | O(m) | O(m) | m = key length |
| Graph (adj list) | — | O(V+E) | O(1) | O(E) | BFS/DFS: O(V+E) |
| Graph (adj matrix) | O(1) | O(V) | O(1) | O(1) | Space O(V²) |
| Segment Tree | O(log n) | O(log n) | O(log n) | O(log n) | Build: O(n) |
| Union-Find | — | O(α(n)) | O(α(n)) | — | α = inverse Ackermann |

---

### Sorting Algorithm Complexity

| Algorithm | Best | Average | Worst | Space | Stable? |
|-----------|------|---------|-------|-------|---------|
| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Selection Sort | O(n²) | O(n²) | O(n²) | O(1) | No |
| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes |
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) | No |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | O(1) | No |
| Tim Sort | O(n) | O(n log n) | O(n log n) | O(n) | Yes |
| Counting Sort | O(n+k) | O(n+k) | O(n+k) | O(k) | Yes |
| Radix Sort | O(nk) | O(nk) | O(nk) | O(n+k) | Yes |

**Python's `sort()` and `sorted()` use Tim Sort: O(n log n) worst case, O(n) best case on nearly-sorted data.**

---

## Array and String Patterns

### Pattern 1: Two Pointers (Opposite Ends)

Use when: sorted array, finding pairs with a target sum, palindrome check.

```python
def two_sum_sorted(nums: list[int], target: int) -> list[int]:
    left, right = 0, len(nums) - 1
    while left < right:
        current = nums[left] + nums[right]
        if current == target:
            return [left, right]
        elif current < target:
            left += 1
        else:
            right -= 1
    return []
```

**Time:** O(n) | **Space:** O(1)

---

### Pattern 2: Two Pointers (Same Direction — Fast/Slow)

Use when: removing duplicates in-place, partitioning arrays.

```python
def remove_duplicates(nums: list[int]) -> int:
    if not nums:
        return 0
    slow = 0
    for fast in range(1, len(nums)):
        if nums[fast] != nums[slow]:
            slow += 1
            nums[slow] = nums[fast]
    return slow + 1
```

**Time:** O(n) | **Space:** O(1)

---

### Pattern 3: Sliding Window (Fixed Size)

Use when: maximum/minimum sum of k consecutive elements.

```python
def max_sum_subarray(nums: list[int], k: int) -> int:
    window_sum = sum(nums[:k])
    max_sum = window_sum
    for i in range(k, len(nums)):
        window_sum += nums[i] - nums[i - k]
        max_sum = max(max_sum, window_sum)
    return max_sum
```

**Time:** O(n) | **Space:** O(1)

---

### Pattern 4: Sliding Window (Variable Size)

Use when: longest/shortest subarray/substring satisfying a condition.

```python
def longest_substring_no_repeat(s: str) -> int:
    char_index: dict[str, int] = {}
    left = 0
    max_len = 0
    for right, char in enumerate(s):
        if char in char_index and char_index[char] >= left:
            left = char_index[char] + 1
        char_index[char] = right
        max_len = max(max_len, right - left + 1)
    return max_len
```

**Time:** O(n) | **Space:** O(min(n, alphabet_size))

---

### Pattern 5: Prefix Sum

Use when: range sum queries, subarray sum equals target.

```python
def subarray_sum_equals_k(nums: list[int], k: int) -> int:
    prefix_counts: dict[int, int] = {0: 1}
    prefix_sum = 0
    count = 0
    for num in nums:
        prefix_sum += num
        count += prefix_counts.get(prefix_sum - k, 0)
        prefix_counts[prefix_sum] = prefix_counts.get(prefix_sum, 0) + 1
    return count
```

**Time:** O(n) | **Space:** O(n)

---

## Tree and Graph Patterns

### Pattern 6: Binary Tree DFS (Recursive)

```python
def max_depth(root) -> int:
    if not root:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))
```

**Time:** O(n) | **Space:** O(h) where h = tree height

---

### Pattern 7: Binary Tree BFS (Level Order)

```python
from collections import deque

def level_order(root) -> list[list[int]]:
    if not root:
        return []
    result = []
    queue = deque([root])
    while queue:
        level_size = len(queue)
        level = []
        for _ in range(level_size):
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    return result
```

**Time:** O(n) | **Space:** O(n)

---

### Pattern 8: Graph BFS (Shortest Path)

```python
from collections import deque

def bfs_shortest_path(graph: dict, start: int, end: int) -> int:
    if start == end:
        return 0
    visited = {start}
    queue = deque([(start, 0)])
    while queue:
        node, distance = queue.popleft()
        for neighbor in graph.get(node, []):
            if neighbor == end:
                return distance + 1
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))
    return -1  # no path
```

**Time:** O(V+E) | **Space:** O(V)

---

### Pattern 9: Graph DFS (Cycle Detection in Directed Graph)

```python
def has_cycle(num_nodes: int, edges: list[tuple]) -> bool:
    graph: dict[int, list] = {i: [] for i in range(num_nodes)}
    for u, v in edges:
        graph[u].append(v)

    # 0=unvisited, 1=in_stack, 2=done
    state = [0] * num_nodes

    def dfs(node: int) -> bool:
        state[node] = 1
        for neighbor in graph[node]:
            if state[neighbor] == 1:
                return True
            if state[neighbor] == 0 and dfs(neighbor):
                return True
        state[node] = 2
        return False

    return any(dfs(i) for i in range(num_nodes) if state[i] == 0)
```

**Time:** O(V+E) | **Space:** O(V)

---

### Pattern 10: Topological Sort (Kahn's Algorithm)

```python
from collections import deque

def topological_sort(num_nodes: int, edges: list[tuple]) -> list[int]:
    in_degree = [0] * num_nodes
    graph: dict[int, list] = {i: [] for i in range(num_nodes)}
    for u, v in edges:
        graph[u].append(v)
        in_degree[v] += 1

    queue = deque(node for node in range(num_nodes) if in_degree[node] == 0)
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return order if len(order) == num_nodes else []  # empty = cycle detected
```

**Time:** O(V+E) | **Space:** O(V)

---

### Pattern 11: Union-Find (Disjoint Set Union)

```python
class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.components = n

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # path compression
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False  # already connected
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        self.components -= 1
        return True
```

**Time:** O(α(n)) per operation | **Space:** O(n)

---

## Dynamic Programming Patterns

### Pattern 12: 1D DP (Bottom-Up)

```python
def coin_change(coins: list[int], amount: int) -> int:
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for coin in coins:
        for i in range(coin, amount + 1):
            dp[i] = min(dp[i], dp[i - coin] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1
```

**Time:** O(amount × len(coins)) | **Space:** O(amount)

---

### Pattern 13: 2D DP (Grid/String)

```python
def longest_common_subsequence(text1: str, text2: str) -> int:
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]
```

**Time:** O(m×n) | **Space:** O(m×n), optimizable to O(min(m,n))

---

### Pattern 14: DP with Memoization (Top-Down)

```python
from functools import lru_cache

def word_break(s: str, word_dict: list[str]) -> bool:
    word_set = set(word_dict)

    @lru_cache(maxsize=None)
    def dp(start: int) -> bool:
        if start == len(s):
            return True
        return any(
            s[start:end] in word_set and dp(end)
            for end in range(start + 1, len(s) + 1)
        )

    return dp(0)
```

**Time:** O(n³) | **Space:** O(n)

---

## Top 20 Algorithm Patterns — Quick Reference

For each pattern, the signal (when to recognize it), the template idea, and the complexity.

| # | Pattern | Signal Words | Core Idea | Complexity |
|---|---------|--------------|-----------|------------|
| 1 | Two Pointers | "pair", "sorted", "palindrome" | Converge from both ends | O(n) |
| 2 | Sliding Window | "subarray", "substring", "consecutive" | Expand/shrink a window | O(n) |
| 3 | Prefix Sum | "range sum", "subarray sum = k" | Precompute cumulative sums | O(n) |
| 4 | Fast/Slow Pointer | "cycle", "middle of list" | Two speeds on same structure | O(n) |
| 5 | Binary Search | "sorted", "rotated", "minimum in range" | Eliminate half search space | O(log n) |
| 6 | Merge Intervals | "overlapping intervals", "meeting rooms" | Sort by start, merge greedily | O(n log n) |
| 7 | Tree DFS | "path", "depth", "validate" | Recurse left/right, combine | O(n) |
| 8 | Tree BFS | "level order", "zigzag", "shortest path in tree" | Queue-based level processing | O(n) |
| 9 | Graph BFS | "shortest path", "word ladder" | Queue with visited set | O(V+E) |
| 10 | Graph DFS | "islands", "connected components" | Stack/recursion with visited | O(V+E) |
| 11 | Topological Sort | "prerequisite", "dependency order" | Kahn's or DFS post-order | O(V+E) |
| 12 | Union-Find | "connected", "number of groups" | Path compression + rank | O(α(n)) |
| 13 | Monotonic Stack | "next greater", "largest rectangle" | Maintain sorted invariant | O(n) |
| 14 | Heap / Priority Queue | "top K", "K closest", "median stream" | Min or max heap | O(n log k) |
| 15 | Backtracking | "all combinations", "permutations", "valid placements" | Choose-explore-unchoose | O(n!) |
| 16 | 1D DP | "ways to climb", "min coins", "longest increasing" | Build from base case | O(n) |
| 17 | 2D DP | "grid paths", "edit distance", "longest common" | Fill table row by row | O(m×n) |
| 18 | Trie | "prefix search", "autocomplete", "word dictionary" | 26-ary tree of characters | O(m) |
| 19 | Divide and Conquer | "merge K lists", "majority element" | Split, solve, combine | O(n log n) |
| 20 | Bit Manipulation | "single number", "count set bits", "power of 2" | XOR, AND, OR, shift tricks | O(n) or O(1) |

---

### Pattern 15: Monotonic Stack

```python
def next_greater_element(nums: list[int]) -> list[int]:
    result = [-1] * len(nums)
    stack: list[int] = []  # stores indices
    for i, num in enumerate(nums):
        while stack and nums[stack[-1]] < num:
            idx = stack.pop()
            result[idx] = num
        stack.append(i)
    return result
```

**Time:** O(n) | **Space:** O(n)

---

### Pattern 16: Backtracking Template

```python
def subsets(nums: list[int]) -> list[list[int]]:
    result: list[list[int]] = []

    def backtrack(start: int, current: list[int]) -> None:
        result.append(current[:])  # record state
        for i in range(start, len(nums)):
            current.append(nums[i])       # choose
            backtrack(i + 1, current)     # explore
            current.pop()                 # unchoose

    backtrack(0, [])
    return result
```

**Time:** O(2ⁿ) | **Space:** O(n)

---

### Pattern 17: Binary Search on Answer Space

Use when: "find minimum X such that condition holds" or "find maximum X such that condition holds."

```python
def min_eating_speed(piles: list[int], h: int) -> int:
    def can_finish(speed: int) -> bool:
        return sum((p + speed - 1) // speed for p in piles) <= h

    left, right = 1, max(piles)
    while left < right:
        mid = (left + right) // 2
        if can_finish(mid):
            right = mid
        else:
            left = mid + 1
    return left
```

**Time:** O(n log(max_pile)) | **Space:** O(1)

---

### Pattern 18: Trie Implementation

```python
class TrieNode:
    def __init__(self):
        self.children: dict[str, 'TrieNode'] = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.is_end = True

    def search(self, word: str) -> bool:
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end

    def starts_with(self, prefix: str) -> bool:
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True
```

**Time:** O(m) per operation | **Space:** O(m × n) total

---

## When to Use Which Data Structure

This is the decision guide you want internalized before your interview.

| Need | Use | Why |
|------|-----|-----|
| O(1) lookup by key | Hash table (`dict`) | Average O(1) get/set |
| Sorted order + O(log n) search | BST / `SortedList` | Maintains order automatically |
| Track min or max efficiently | Heap (`heapq`) | O(1) peek, O(log n) push/pop |
| LIFO — undo, DFS, expression parsing | Stack (`list`) | O(1) push/pop from end |
| FIFO — BFS, task queues | Queue (`collections.deque`) | O(1) append and popleft |
| Fast prefix/substring search | Trie | O(m) per word operation |
| Count elements efficiently | `collections.Counter` | Built-in frequency map |
| Fast membership test, deduplication | Set | O(1) average membership check |
| Detect connected components | Union-Find | Near-O(1) union/find with compression |
| Range queries, point updates | Segment Tree | O(log n) query and update |
| Sliding window max/min | Monotonic Deque | O(n) total across all windows |
| Top K frequent / K closest | Min-heap of size K | O(n log k) |
| Graph shortest path (unweighted) | BFS | O(V+E) |
| Graph shortest path (weighted) | Dijkstra + min-heap | O((V+E) log V) |
| Graph shortest path (negative edges) | Bellman-Ford | O(V×E) |
| All-pairs shortest path | Floyd-Warshall | O(V³) |
| Minimum spanning tree | Kruskal's (Union-Find) or Prim's | O(E log V) |

---

## Common Interview Edge Cases to Always Check

Before declaring your solution complete, run through this checklist:

**Array/String:**
- Empty input `[]` or `""`
- Single element
- All same values
- Negative numbers (if applicable)
- Integer overflow (in languages without arbitrary precision)

**Linked List:**
- `None` head
- Single node
- Cycle present (when not expected)
- Even vs. odd length (for middle-finding)

**Tree:**
- Empty tree (`root = None`)
- Single node (root only)
- Skewed tree (all left or all right — worst case for BST)
- Complete binary tree

**Graph:**
- Disconnected components
- Self-loops
- No edges (all isolated nodes)
- Directed vs. undirected (confirm with interviewer)

**Dynamic Programming:**
- Empty input → base case returns correctly?
- Target = 0 or target = 1
- Values larger than target (skip or exclude)

---

## Practice These Patterns with AI Feedback

Knowing the patterns intellectually is not the same as executing them fluently under interview pressure. The gap closes with deliberate, timed practice and immediate feedback on where you break down.

**[Interview Simulator at app.codeswiftr.com](https://app.codeswiftr.com)** gives you:

- Timed coding problems organized by the patterns in this guide
- AI evaluation of your pattern recognition speed and code quality
- Edge case coverage analysis — did your solution handle the tricky inputs?
- Time and space complexity coaching on every solution

Use this cheat sheet to study. Use the simulator to test under real conditions.

**[Start Practicing with AI Feedback at app.codeswiftr.com](https://app.codeswiftr.com)**

---

*Related guides: [Software Engineer Coding Interview: 6-Week Preparation Plan](/blog/software-engineer-coding-interview-prep) | [The Complete System Design Interview Guide](/blog/system-design-interview-guide) | [30-Minute Daily Routine for FAANG Offers](/blog/30-minute-daily-routine-faang-offers)*

## Related Articles

- [Data Structures and Algorithms Interview Guide](/blog/data-structures-algorithms-interview-guide)
- [Advanced Dynamic Programming Guide](/blog/advanced-dynamic-programming-guide)
- [Graph Algorithms Interview Guide](/blog/graph-algorithms-interview-guide)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [Google Interview Guide](/blog/google-interview-guide)
