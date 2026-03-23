---
title: "Segment Trees: Range Query Problems in Technical Interviews"
description: "Master segment trees for technical interviews — range sum queries, range minimum/maximum, lazy propagation, when to use segment trees vs BIT, and the problems that require them."
date: "2026-03-20"
category: "Algorithms"
---

# Segment Trees: Range Query Problems in Technical Interviews

Segment trees appear in hard interview problems involving range queries with updates. Most engineers have heard of them but can't implement one under pressure. This guide gives you the implementation pattern, when to use them, and the interview problems that require them.

## What Is a Segment Tree?

A segment tree is a binary tree that stores aggregate information about array segments. The root covers the entire array. Each node stores an aggregate value (sum, min, max) for its segment. Leaves represent individual elements.

For an array of N elements, a segment tree has at most 4N nodes. Point updates and range queries both run in O(log N).

Compare to prefix sums: prefix sums give O(1) range queries but can't handle updates — you'd need to recompute the entire prefix array for each update. Segment trees handle both updates and queries in O(log N).

## Implementation: Range Sum

```python
class SegmentTree:
    def __init__(self, nums):
        self.n = len(nums)
        self.tree = [0] * (4 * self.n)
        self._build(nums, 0, 0, self.n - 1)
    
    def _build(self, nums, node, start, end):
        if start == end:
            self.tree[node] = nums[start]
        else:
            mid = (start + end) // 2
            self._build(nums, 2*node+1, start, mid)
            self._build(nums, 2*node+2, mid+1, end)
            self.tree[node] = self.tree[2*node+1] + self.tree[2*node+2]
    
    def update(self, idx, val, node=0, start=0, end=None):
        if end is None: end = self.n - 1
        if start == end:
            self.tree[node] = val
        else:
            mid = (start + end) // 2
            if idx <= mid:
                self.update(idx, val, 2*node+1, start, mid)
            else:
                self.update(idx, val, 2*node+2, mid+1, end)
            self.tree[node] = self.tree[2*node+1] + self.tree[2*node+2]
    
    def query(self, l, r, node=0, start=0, end=None):
        if end is None: end = self.n - 1
        if r < start or l > end:
            return 0  # out of range
        if l <= start and end <= r:
            return self.tree[node]  # fully covered
        mid = (start + end) // 2
        return (self.query(l, r, 2*node+1, start, mid) + 
                self.query(l, r, 2*node+2, mid+1, end))
```

For range minimum/maximum, change the merge operation from `+` to `min`/`max` and the out-of-range return to `float('inf')`/`float('-inf')`.

## Lazy Propagation

Lazy propagation handles range updates efficiently. Without it, updating a range of elements would take O(N) time. With lazy propagation, range updates are O(log N).

The idea: defer updates. Instead of propagating an update through the entire subtree immediately, store the pending update at the node and propagate it only when the children are actually needed.

A segment tree with lazy propagation maintains a separate `lazy` array. When you update a range:
1. If the current segment is fully within the update range: update the node value, store the update in `lazy`, return.
2. Before recursing into children: push down pending `lazy` updates to children.
3. After recursing: recombine children values.

This pattern is essential for LeetCode 307 (Range Sum Query - Mutable), 308 (Range Sum Query 2D - Mutable), and competitive programming problems.

## Binary Indexed Tree (Fenwick Tree) Alternative

For pure range sum queries with point updates, a Binary Indexed Tree (BIT/Fenwick Tree) is simpler to implement and has better constant factors:

```python
class BIT:
    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)
    
    def update(self, i, delta):
        i += 1  # 1-indexed
        while i <= self.n:
            self.tree[i] += delta
            i += i & (-i)
    
    def prefix_sum(self, i):
        i += 1  # 1-indexed
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= i & (-i)
        return total
    
    def range_sum(self, l, r):
        return self.prefix_sum(r) - (self.prefix_sum(l-1) if l > 0 else 0)
```

**When to use BIT vs segment tree:** BIT for range sum with point updates (simpler). Segment tree for range min/max, range updates (lazy propagation), or custom merge operations.

## Interview Problems That Require Range Query Structures

**307 — Range Sum Query Mutable:** Classic segment tree or BIT problem. Point updates, range sum queries.

**315 — Count of Smaller Numbers After Self:** For each element, count how many elements to its right are smaller. Process right to left; use BIT indexed by value.

**327 — Count of Range Sum:** Count subarrays whose sum falls in [lower, upper]. Use prefix sums + merge sort or segment tree with coordinate compression.

**493 — Reverse Pairs:** Count pairs where `nums[i] > 2 * nums[j]` and `i < j`. Merge sort or BIT with coordinate compression.

## Coordinate Compression

Many segment tree problems involve large value ranges (e.g., values up to 10^9). You can't allocate a 10^9-node tree. Coordinate compression maps values to a dense range:

```python
values = sorted(set(nums))
compress = {v: i for i, v in enumerate(values)}
compressed = [compress[x] for x in nums]
```

Now build your segment tree on the compressed values (size = number of distinct values).

## When to Use in Interviews

Signal that a segment tree might be needed: "range query" + "updates" in the same problem. If there are no updates, prefix sums are simpler. If the range query is "range sum," BIT is sufficient and simpler. If range query is min/max or requires range updates, reach for a segment tree.

For interviews below senior level, segment trees rarely appear. For senior/staff roles at top companies or competitive programming-heavy interviews, they're a tested pattern. Know the implementation cold — a segment tree you can't implement under pressure is worthless.

