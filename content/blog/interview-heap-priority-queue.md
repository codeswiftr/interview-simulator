---
title: "Heap and Priority Queue Patterns for Coding Interviews"
description: "Master heap-based interview problems: K closest points, merge K sorted lists, task scheduler, find median from data stream, and sliding window median — with Python implementations and intuition."
date: "2026-03-20"
category: "Algorithm Guides"
---

# Heap and Priority Queue Patterns for Coding Interviews

The heap (priority queue) is one of the most versatile data structures in technical interviews. When you need the K largest/smallest elements, the next minimum efficiently, or a running statistic on a stream, the heap is usually the right tool. This guide covers the essential heap patterns with clean Python implementations.

## Python Heap Basics

Python's `heapq` module implements a **min-heap**. Key operations:

```python
import heapq

heap = []
heapq.heappush(heap, 5)       # push
heapq.heappush(heap, 2)
min_val = heapq.heappop(heap) # pop minimum (returns 2)
peek = heap[0]                # peek minimum without popping

# Build heap from list (in-place, O(n))
nums = [3, 1, 4, 1, 5]
heapq.heapify(nums)

# Efficient replace: pop + push in one operation
heapq.heapreplace(heap, new_val)  # pop min, push new_val (faster than pop then push)
heapq.heappushpop(heap, new_val)  # push new_val, then pop min (different semantics)
```

**Max-heap**: Python doesn't have a built-in max-heap. The idiom is to negate values:

```python
max_heap = []
heapq.heappush(max_heap, -5)  # "push 5 to max-heap"
max_val = -heapq.heappop(max_heap)  # "pop max = 5"
```

For tuples, heapq compares elements left to right. Use `(priority, item)` for priority queues, and `(-priority, item)` for max-heaps.

## Pattern 1: K Closest / K Largest / K Smallest

**K Closest Points to Origin (LC 973)**:

```python
def kClosest(points, k):
    # Max-heap of size k: keep the k smallest distances
    heap = []
    for x, y in points:
        dist = -(x*x + y*y)  # negative for max-heap
        heapq.heappush(heap, (dist, x, y))
        if len(heap) > k:
            heapq.heappop(heap)
    return [[x, y] for _, x, y in heap]
```

**General pattern — K smallest using max-heap**:
- Maintain a max-heap of size k
- For each element, push it; if size exceeds k, pop the max
- At the end, the heap contains the k smallest elements

**General pattern — K largest using min-heap**:
- Maintain a min-heap of size k
- For each element, push it; if size exceeds k, pop the min
- At the end, the heap contains the k largest elements

**Top K Frequent Elements (LC 347)**:

```python
from collections import Counter

def topKFrequent(nums, k):
    count = Counter(nums)
    return heapq.nlargest(k, count.keys(), key=count.get)
```

`heapq.nlargest` and `heapq.nsmallest` are convenient but internally use a heap — O(n log k).

## Pattern 2: Merge K Sorted Lists

**Merge K Sorted Lists (LC 23)**:

```python
import heapq

def mergeKLists(lists):
    heap = []
    for i, node in enumerate(lists):
        if node:
            heapq.heappush(heap, (node.val, i, node))

    dummy = curr = ListNode(0)
    while heap:
        val, i, node = heapq.heappop(heap)
        curr.next = node
        curr = curr.next
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))

    return dummy.next
```

The index `i` breaks ties when values are equal, avoiding comparison of `ListNode` objects which would raise a TypeError in Python.

**Complexity**: O(n log k) where n is total nodes and k is number of lists.

**Generalization**: This pattern — "initialize heap with one element per source, pop-advance-push" — applies to any merge of K sorted sequences.

## Pattern 3: Task Scheduler

**Task Scheduler (LC 621)**: Given tasks with a cooldown n between identical tasks, find minimum intervals to execute all tasks.

The key insight: the most frequent task determines the minimum length. Idle time fills gaps:

```python
from collections import Counter
import heapq
from collections import deque

def leastInterval(tasks, n):
    freq = Counter(tasks)
    max_heap = [-f for f in freq.values()]
    heapq.heapify(max_heap)

    time = 0
    queue = deque()  # (negative_remaining, available_at_time)

    while max_heap or queue:
        time += 1
        if max_heap:
            remaining = heapq.heappop(max_heap) + 1  # decrement (both negative)
            if remaining < 0:
                queue.append((remaining, time + n))

        if queue and queue[0][1] == time:
            heapq.heappush(max_heap, queue.popleft()[0])

    return time
```

**Mathematical shortcut** (interview-worthy explanation):

```python
def leastInterval(tasks, n):
    freq = sorted(Counter(tasks).values())
    max_freq = freq[-1]
    max_count = freq.count(max_freq)
    return max(len(tasks), (max_freq - 1) * (n + 1) + max_count)
```

The formula: `(max_freq - 1)` "blocks" of size `(n+1)` plus the final block of tasks with max frequency. The answer is either this value or `len(tasks)` (if tasks are spread out enough that idle time is 0).

## Pattern 4: Find Median from Data Stream

**Find Median from Data Stream (LC 295)**: Maintain two heaps — a max-heap for the lower half, a min-heap for the upper half:

```python
class MedianFinder:
    def __init__(self):
        self.low = []   # max-heap (store negated values)
        self.high = []  # min-heap

    def addNum(self, num):
        heapq.heappush(self.low, -num)

        # Ensure max of low <= min of high
        if self.low and self.high and -self.low[0] > self.high[0]:
            heapq.heappush(self.high, -heapq.heappop(self.low))

        # Balance sizes: low can have at most 1 more element than high
        if len(self.low) > len(self.high) + 1:
            heapq.heappush(self.high, -heapq.heappop(self.low))
        elif len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def findMedian(self):
        if len(self.low) > len(self.high):
            return -self.low[0]
        return (-self.low[0] + self.high[0]) / 2.0
```

**Invariants to maintain**:
1. `max(low) <= min(high)`
2. `len(low) == len(high)` or `len(low) == len(high) + 1`

Every insertion may require up to 2 heap operations. Both `addNum` and `findMedian` run in O(log n) and O(1) respectively.

## Pattern 5: Sliding Window Median

**Sliding Window Median (LC 480)**: More complex — you need to remove arbitrary elements from a heap efficiently.

The standard approach uses two heaps with lazy deletion:

```python
import heapq
from collections import defaultdict

def medianSlidingWindow(nums, k):
    small = []  # max-heap (negated)
    large = []  # min-heap
    lazy = defaultdict(int)  # delayed deletions

    for i in range(k):
        heapq.heappush(small, -nums[i])
    for _ in range(k // 2):
        heapq.heappush(large, -heapq.heappop(small))

    def get_median():
        return (-small[0] + large[0]) / 2.0 if k % 2 == 0 else -small[0]

    def rebalance():
        while small and lazy[-small[0]] > 0:
            lazy[-small[0]] -= 1
            heapq.heappop(small)
        while large and lazy[large[0]] > 0:
            lazy[large[0]] -= 1
            heapq.heappop(large)
        if len(small) > len(large) + 1:
            heapq.heappush(large, -heapq.heappop(small))
        elif len(large) > len(small):
            heapq.heappush(small, -heapq.heappop(large))

    result = [get_median()]
    small_size = k - k // 2
    large_size = k // 2

    for i in range(k, len(nums)):
        out_num = nums[i - k]
        in_num = nums[i]

        # Mark outgoing for lazy deletion
        lazy[out_num] += 1

        # Add incoming
        if in_num <= -small[0]:
            heapq.heappush(small, -in_num)
        else:
            heapq.heappush(large, in_num)

        rebalance()
        result.append(get_median())

    return result
```

Lazy deletion is the standard technique when you need heap operations on arbitrary elements. The SortedList from `sortedcontainers` is an alternative if allowed.

## Heap Pattern Decision Guide

| Problem Type | Approach |
|---|---|
| K smallest from stream | Max-heap of size k |
| K largest from stream | Min-heap of size k |
| Merge K sorted sequences | Min-heap with one element per sequence |
| Running median | Two heaps (max for lower half, min for upper half) |
| Minimum cost to combine | Min-heap, always combine two smallest |
| Next event in simulation | Min-heap keyed by time |

The heap is most powerful when you identify problems involving "the next optimal element" in a sequence of decisions. When you find yourself wanting a sorted structure but only ever touching the minimum or maximum, reach for a heap.
