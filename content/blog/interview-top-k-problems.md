---
title: "Top-K and K-th Element Problems: Heaps, QuickSelect, and Frequency Analysis Patterns"
description: "Master the three main approaches to Top-K and K-th element interview problems — heap-based selection, QuickSelect for O(n) average, and bucket sort for frequency problems."
date: "2026-03-20"
category: "Algorithms"
---

Top-K and K-th element problems form a coherent family in interviews. The same three approaches — sorting, heaps, and QuickSelect — solve most variants. Knowing which to reach for, and why, demonstrates the algorithm fluency interviewers look for in mid to senior roles.

## The Three Approaches

### Approach 1: Full Sort (O(n log n))

Sort the array and return the K-th element or top-K elements. This is correct but rarely optimal. Use it when:
- The array is already nearly sorted
- You need the top-K elements in sorted order
- K is close to N (heap approaches lose their advantage)

Always mention this approach first and immediately explain why you'll do better.

### Approach 2: Min-Heap of Size K (O(n log k))

Maintain a heap of exactly K elements. For "K largest elements," use a min-heap (Python's `heapq` default). For each new element, push it to the heap; if the heap exceeds K elements, pop the minimum. After processing all elements, the heap contains the K largest.

```python
import heapq

def top_k_largest(nums, k):
    heap = []
    for num in nums:
        heapq.heappush(heap, num)
        if len(heap) > k:
            heapq.heappop(heap)
    return heap  # k largest elements (unsorted)
```

Time: O(n log k). Space: O(k). This is usually the expected answer for most "top K" interview problems.

`heapq.nlargest(k, nums)` does the same thing in one line — know it exists, but understand the underlying mechanism.

**K Closest Points to Origin** (LeetCode 973): push `(distance, point)` tuples. Use a max-heap of size K (negate distances) to keep the K smallest distances.

### Approach 3: QuickSelect (O(n) average, O(n²) worst case)

QuickSelect finds the K-th smallest element in O(n) average time using the same partition logic as QuickSort but only recursing on one side.

```python
import random

def quickselect(nums, k):
    """Returns the k-th smallest element (1-indexed)."""
    def partition(left, right, pivot_idx):
        pivot = nums[pivot_idx]
        nums[pivot_idx], nums[right] = nums[right], nums[pivot_idx]
        store = left
        for i in range(left, right):
            if nums[i] < pivot:
                nums[store], nums[i] = nums[i], nums[store]
                store += 1
        nums[store], nums[right] = nums[right], nums[store]
        return store

    left, right = 0, len(nums) - 1
    k -= 1  # convert to 0-indexed
    while left <= right:
        pivot_idx = random.randint(left, right)
        pivot_idx = partition(left, right, pivot_idx)
        if pivot_idx == k:
            return nums[pivot_idx]
        elif pivot_idx < k:
            left = pivot_idx + 1
        else:
            right = pivot_idx - 1
```

Randomizing the pivot prevents worst-case O(n²) behavior (which occurs with sorted input and a fixed pivot). In interviews, always mention that you're randomizing and why.

QuickSelect mutates the input array. If that's not acceptable, copy the array first — still O(n) time, O(n) space.

**When to use QuickSelect:** When K-th element is needed (not top-K), and you need optimal average-case time. When N is very large and O(n log k) heap overhead matters.

## Frequency-Based Top-K Problems

**Top K Frequent Elements** (LeetCode 347) adds a frequency counting step:

```python
from collections import Counter
import heapq

def top_k_frequent(nums, k):
    count = Counter(nums)
    # Use heap of size k on (frequency, element) pairs
    return heapq.nlargest(k, count, key=count.get)
```

**Bucket Sort approach for O(n):** Since frequencies range from 1 to n, create n+1 buckets where `bucket[i]` holds all elements with frequency i. Fill buckets from the counter, then scan from the highest frequency bucket down until you collect K elements.

```python
def top_k_frequent_linear(nums, k):
    count = Counter(nums)
    buckets = [[] for _ in range(len(nums) + 1)]
    for num, freq in count.items():
        buckets[freq].append(num)
    result = []
    for freq in range(len(buckets) - 1, 0, -1):
        result.extend(buckets[freq])
        if len(result) >= k:
            return result[:k]
    return result
```

This O(n) solution is impressive in interviews but harder to implement correctly under pressure. Present it as an optimization after the heap solution.

**Sort Characters by Frequency** (LeetCode 451): same pattern — count frequencies, sort by frequency descending, reconstruct string.

## K-th Largest in a Stream

**Data Stream: Find K-th Largest** (LeetCode 703) requires a persistent data structure. Maintain a min-heap of size K. The K-th largest is always the heap's minimum (top).

```python
class KthLargest:
    def __init__(self, k, nums):
        self.k = k
        self.heap = []
        for num in nums:
            self.add(num)

    def add(self, val):
        heapq.heappush(self.heap, val)
        if len(self.heap) > self.k:
            heapq.heappop(self.heap)
        return self.heap[0]
```

The insight: if you always maintain exactly K elements in a min-heap, the heap's minimum is, by definition, the K-th largest overall. Each `add` operation is O(log k).

## K-th Smallest in a Matrix

**Kth Smallest Element in a Sorted Matrix** (LeetCode 378): each row and column is sorted. Two approaches:

1. **Heap:** Push the first element of each row. Pop the minimum K times, pushing the next element from the same row when you pop. O(k log n).

2. **Binary search on value:** Binary search on the value range [matrix[0][0], matrix[n-1][n-1]]. For each candidate value, count how many elements are ≤ that value using the sorted structure. O(n log(max-min)). More complex to implement but demonstrates strong problem-solving.

## Complexity Summary

| Approach | Time | Space | Best for |
|----------|------|-------|----------|
| Full sort | O(n log n) | O(1) | Baseline, sorted output needed |
| Min-heap size K | O(n log k) | O(k) | Top-K in a stream, general case |
| QuickSelect | O(n) avg | O(1) | K-th element, static array |
| Bucket sort | O(n) | O(n) | Frequency problems with bounded range |

## Interview Strategy

Lead with the heap approach — it's clean, O(n log k), and handles streaming data. Then proactively mention QuickSelect as the O(n) alternative for static arrays when K-th element (not top-K) is needed. If the problem involves frequencies, mention bucket sort as the theoretical O(n) ceiling. This progression shows you understand the trade-off space rather than memorizing a single solution.
