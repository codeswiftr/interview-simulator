---
title: "Segment Trees Interview Guide: Master Range Queries"
date: 2026-03-21
excerpt: "Conquer segment tree interview questions with lazy propagation, range updates, and real patterns from FAANG interviews."
tags: [algorithms, data-structures, segment-trees, range-queries, interview-prep]
---

# Segment Trees Interview Guide: Master Range Queries

Segment trees are the go-to data structure when interviewers ask about range queries. They appear in problems where you need to query or update ranges of values efficiently—think "sum of elements from index 3 to 7" or "find the minimum in a range."

## Why Segment Trees?

A naive approach iterates through the range for each query—O(n) per query. Segment trees reduce this to O(log n) for both queries and updates by precomputing information about ranges in a binary tree structure.

## Core Structure

A segment tree stores information about intervals. Each leaf node represents a single element, while internal nodes represent the union of their children's intervals.

```python
class SegmentTree:
    def __init__(self, data):
        self.n = len(data)
        self.tree = [0] * (4 * self.n)  # Allocate 4x space
        self._build(data, 0, 0, self.n - 1)
    
    def _build(self, data, node, start, end):
        if start == end:
            self.tree[node] = data[start]
        else:
            mid = (start + end) // 2
            self._build(data, 2*node + 1, start, mid)
            self._build(data, 2*node + 2, mid + 1, end)
            self.tree[node] = self.tree[2*node + 1] + self.tree[2*node + 2]
```

## Range Query

To query a range [l, r], traverse the tree and combine results from nodes that fully overlap the query range.

```python
def query(self, l, r):
    return self._query(0, 0, self.n - 1, l, r)

def _query(self, node, start, end, l, r):
    if r < start or end < l:
        return 0  # No overlap
    if l <= start and end <= r:
        return self.tree[node]  # Full overlap
    mid = (start + end) // 2
    left = self._query(2*node + 1, start, mid, l, r)
    right = self._query(2*node + 2, mid + 1, end, l, r)
    return left + right
```

## Lazy Propagation

The real interview challenge is handling range updates efficiently. Lazy propagation defers updates until necessary, storing "pending" updates in a separate array.

```python
def _update_range(self, node, start, end, l, r, val):
    if self.lazy[node] != 0:
        self.tree[node] += (end - start + 1) * self.lazy[node]
        if start != end:
            self.lazy[2*node + 1] += self.lazy[node]
            self.lazy[2*node + 2] += self.lazy[node]
        self.lazy[node] = 0
    
    if r < start or end < l:
        return
    if l <= start and end <= r:
        self.tree[node] += (end - start + 1) * val
        if start != end:
            self.lazy[2*node + 1] += val
            self.lazy[2*node + 2] += val
        return
    mid = (start + end) // 2
    self._update_range(2*node + 1, start, mid, l, r, val)
    self._update_range(2*node + 2, mid + 1, end, l, r, val)
    self.tree[node] = self.tree[2*node + 1] + self.tree[2*node + 2]
```

## Interview Tips

1. **Start with the query type.** Ask if it's sum, min, max, or something custom. This determines the combine operation.

2. **Clarify update patterns.** Point updates vs. range changes significantly affect implementation complexity.

3. **Mention alternatives.** Fenwick trees are simpler for prefix sums; segment trees excel at arbitrary range queries.

4. **Common follow-ups:** "What if we need the k-th smallest in a range?" (Merge sort tree) or "Can you support multiple query types?" (Segment tree with pairs/tuples).

## Time Complexity

- Build: O(n)
- Query: O(log n)
- Point Update: O(log n)
- Range Update (with lazy): O(log n)

## Space Complexity

O(4n) for the tree array, O(n) for lazy propagation.
