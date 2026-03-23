---
title: "Fenwick Trees (Binary Indexed Trees): Prefix Sums in O(log n)"
date: 2026-03-21
excerpt: "Learn Fenwick trees for efficient prefix sum queries and range updates—the simpler cousin of segment trees."
tags: [algorithms, data-structures, fenwick-tree, prefix-sums, interview-prep]
---

# Fenwick Trees (Binary Indexed Trees): Prefix Sums in O(log n)

When interviewers ask for efficient prefix sums with updates, Fenwick trees (Binary Indexed Trees) offer a compact O(log n) solution with a smaller constant factor than segment trees.

## The Key Insight

Fenwick trees exploit the binary representation of indices. Each index i is responsible for a range determined by the lowest set bit in i.

For index i:
- The lowest set bit is `i & (-i)`
- Index i stores the sum of elements from `(i - lowest_set_bit + 1)` to `i`

## Core Operations

### Building

```python
class FenwickTree:
    def __init__(self, n):
        self.n = n
        self.bit = [0] * (n + 1)  # 1-indexed
    
    def build(self, arr):
        for i, val in enumerate(arr, 1):
            self.bit[i] += val
            j = i + (i & -i)
            if j <= self.n:
                self.bit[j] += self.bit[i]
```

### Prefix Sum Query

To get sum of first k elements, traverse upward by removing the lowest set bit:

```python
def prefix_sum(self, i):
    result = 0
    while i > 0:
        result += self.bit[i]
        i -= i & -i  # Remove lowest set bit
    return result
```

### Point Update

To update element at index i, traverse upward by adding the lowest set bit:

```python
def update(self, i, delta):
    while i <= self.n:
        self.bit[i] += delta
        i += i & -i  # Add lowest set bit
```

### Range Sum

```python
def range_sum(self, l, r):
    return self.prefix_sum(r) - self.prefix_sum(l - 1)
```

## Range Updates

With two BITs, you can support range updates and point queries:

```python
class FenwickTreeRangeUpdate:
    def __init__(self, n):
        self.n = n
        self.bit1 = [0] * (n + 2)
        self.bit2 = [0] * (n + 2)
    
    def _update(self, bit, i, delta):
        while i <= self.n:
            bit[i] += delta
            i += i & -i
    
    def range_update(self, l, r, delta):
        self._update(self.bit1, l, delta)
        self._update(self.bit1, r + 1, -delta)
        self._update(self.bit2, l, delta * (l - 1))
        self._update(self.bit2, r + 1, -delta * r)
    
    def _prefix_sum(self, bit, i):
        result = 0
        while i > 0:
            result += bit[i]
            i -= i & -i
        return result
    
    def point_query(self, i):
        return self._prefix_sum(self.bit1, i) * i - self._prefix_sum(self.bit2, i)
```

## 2D Fenwick Tree

For matrix prefix sums:

```python
class FenwickTree2D:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.bit = [[0] * (cols + 1) for _ in range(rows + 1)]
    
    def update(self, row, col, delta):
        r = row
        while r <= self.rows:
            c = col
            while c <= self.cols:
                self.bit[r][c] += delta
                c += c & -c
            r += r & -r
    
    def query(self, row, col):
        result = 0
        r = row
        while r > 0:
            c = col
            while c > 0:
                result += self.bit[r][c]
                c -= c & -c
            r -= r & -r
        return result
```

## Interview Tips

1. **Fenwick vs Segment Tree.** Fenwick is simpler and faster for prefix sums. Segment trees handle more complex queries (min, max, gcd).

2. **1-indexed convention.** Most implementations use 1-indexed arrays to simplify bit manipulation.

3. **Common applications.** Counting inversions, prefix sums with updates, range frequency queries.

4. **Watch for overflow.** The tree can accumulate large values—use appropriate data types.

## Time Complexity

- Build: O(n)
- Prefix Sum: O(log n)
- Update: O(log n)
- Range Sum: O(log n)
