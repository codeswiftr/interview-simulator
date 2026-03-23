---
title: "Two Heaps Pattern: Median and Beyond"
description: "The two heaps pattern for coding interviews — finding median from a data stream, sliding window median, finding the optimal meeting point, and recognizing when two heaps solve an otherwise hard problem."
date: "2026-03-20"
category: "Algorithms"
---

# Two Heaps Pattern: Median and Beyond

The two heaps pattern is a specialized but elegant technique for a class of problems that require tracking the median or partition point of a dynamically changing dataset. Once you see it, you'll recognize it in problems that otherwise seem hard to solve in O(log n).

## The Core Pattern

Maintain two heaps:
- **Max-heap** (lo): Stores the lower half of numbers. The top is the largest in the lower half.
- **Min-heap** (hi): Stores the upper half of numbers. The top is the smallest in the upper half.

**Invariants to maintain:**
1. Every element in `lo` ≤ every element in `hi`
2. Size difference between `lo` and `hi` is at most 1

With these invariants, the median is:
- `lo.top()` if `lo` is larger
- `(lo.top() + hi.top()) / 2` if equal size

**The add operation:**

```python
def add(self, num):
    # Step 1: Add to lo (max-heap)
    heapq.heappush(self.lo, -num)

    # Step 2: Ensure lo's max ≤ hi's min (cross-heap ordering)
    if self.hi and -self.lo[0] > self.hi[0]:
        heapq.heappush(self.hi, -heapq.heappop(self.lo))

    # Step 3: Balance sizes
    if len(self.lo) > len(self.hi) + 1:
        heapq.heappush(self.hi, -heapq.heappop(self.lo))
    elif len(self.hi) > len(self.lo):
        heapq.heappush(self.lo, -heapq.heappop(self.hi))
```

**Why add to lo first?** Adding to lo first ensures ordering invariant maintenance through the "leakage" step in step 2. You could also add to hi first with appropriate sign changes.

## Problem: Find Median from Data Stream

```python
import heapq

class MedianFinder:
    def __init__(self):
        self.lo = []  # Max-heap (negate values)
        self.hi = []  # Min-heap

    def addNum(self, num):
        heapq.heappush(self.lo, -num)
        if self.hi and -self.lo[0] > self.hi[0]:
            heapq.heappush(self.hi, -heapq.heappop(self.lo))
        if len(self.lo) > len(self.hi) + 1:
            heapq.heappush(self.hi, -heapq.heappop(self.lo))
        elif len(self.hi) > len(self.lo):
            heapq.heappush(self.lo, -heapq.heappop(self.hi))

    def findMedian(self):
        if len(self.lo) > len(self.hi):
            return float(-self.lo[0])
        return (-self.lo[0] + self.hi[0]) / 2.0
```

**O(log n) per add, O(1) per median.**

## Problem: Sliding Window Median

"Find the median in each sliding window of size k."

This is harder — you need to add new elements AND remove elements as the window slides. Heaps don't support arbitrary deletion efficiently.

**Lazy deletion approach:** Mark elements for deletion but don't remove them immediately. Track "pending deletions" in a hash map. When the deleted element is at the top of a heap, remove it then.

```python
from collections import defaultdict
import heapq

def medianSlidingWindow(nums, k):
    lo = []  # Max-heap (negated)
    hi = []  # Min-heap
    deleted = defaultdict(int)
    result = []

    def add(num):
        heapq.heappush(lo, -num)
        if hi and -lo[0] > hi[0]:
            heapq.heappush(hi, -heapq.heappop(lo))
        balance()

    def remove(num):
        deleted[num] += 1
        if num <= -lo[0]:
            prune(lo, True)
        else:
            prune(hi, False)
        balance()

    def prune(heap, is_lo):
        sign = -1 if is_lo else 1
        while heap and deleted[sign * heap[0]] > 0:
            deleted[sign * heap[0]] -= 1
            heapq.heappop(heap)

    def balance():
        if len(lo) > len(hi) + 1:
            heapq.heappush(hi, -heapq.heappop(lo))
            prune(hi, False)
        elif len(hi) > len(lo):
            heapq.heappush(lo, -heapq.heappop(hi))
            prune(lo, True)

    def get_median():
        if len(lo) > len(hi):
            return float(-lo[0])
        return (-lo[0] + hi[0]) / 2.0

    for i, num in enumerate(nums):
        add(num)
        if i >= k - 1:
            result.append(get_median())
            remove(nums[i - k + 1])

    return result
```

Lazy deletion achieves O(n log k) overall — each element added and lazily deleted once.

## Problem: IPO (Maximize Capital)

"Given k projects each with a capital requirement and profit, starting with W capital, maximize capital after selecting at most k projects."

Strategy: at each step, among all affordable projects, pick the highest-profit one. This is a greedy algorithm enabled by two heaps.

```python
def findMaximizedCapital(k, w, profits, capital):
    # Min-heap of (capital, profit) — sorted by capital requirement
    available = sorted(zip(capital, profits))
    # Max-heap of (-profit) — available profitable projects
    profitable = []

    i = 0
    for _ in range(k):
        # Add all newly affordable projects to profitable heap
        while i < len(available) and available[i][0] <= w:
            heapq.heappush(profitable, -available[i][1])
            i += 1

        if not profitable:
            break  # No affordable projects

        w -= heapq.heappop(profitable)  # Take highest profit project

    return w
```

The two-heap structure: one heap sorted by capital (access smallest first), one by profit (access largest first). At each step, transfer newly affordable projects to the profitable heap.

## Recognizing Two Heap Problems

The pattern applies when:
- "Find the median of a dynamic dataset" — core use case
- "Partition elements into two groups dynamically" — two heaps maintain the partition
- "At each step, need both the maximum and minimum of two partitions" — two heaps provide both

The tell: you need O(1) access to the "middle" of a dynamically changing set, or you need to efficiently track the boundary between two partitions.

Key limitation: if you also need arbitrary deletion, add lazy deletion with a hash map of pending deletions. If you need the k-th element (not just median), consider augmented BST or order statistics tree instead.
