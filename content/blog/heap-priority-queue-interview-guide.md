---
title: "Heaps and Priority Queues in Coding Interviews"
description: "Master heaps and priority queues for coding interviews. Learn min-heap vs max-heap, Python's heapq module, 5 core patterns including top-K elements and the two-heaps technique, and when to use a heap vs sorted list."
date: "2025-10-11"
category: "Interview Preparation"
---
# Heaps and Priority Queues in Coding Interviews

The heap is the secret weapon that turns "I don't know how to get the largest element efficiently" into a solved problem in thirty seconds. It is the data structure behind the priority queue, and it appears in a surprising number of interview problems once you know what to look for. This guide covers everything you need: the theory, the Python API, the five patterns that cover 90% of heap interview problems, and how to decide when a heap is the right tool.

## Min-Heap vs Max-Heap

A heap is a complete binary tree satisfying the heap property. In a min-heap, every parent is smaller than its children, so the minimum element is always at the root and can be accessed in O(1). In a max-heap, every parent is larger than its children, giving O(1) access to the maximum.

Both structures support the same core operations:
- **Insert (push):** O(log n) — add element, bubble up to restore heap property
- **Extract min/max (pop):** O(log n) — remove root, replace with last element, sift down
- **Peek (top):** O(1) — read the root without removing
- **Heapify:** O(n) — build a heap from an unsorted list (faster than n insertions)

Python's `heapq` module implements a min-heap only. To simulate a max-heap, negate your values: push `-value` and negate again when you pop.

## Python heapq Module

```python
import heapq

# Build from list (in-place, O(n))
nums = [3, 1, 4, 1, 5, 9, 2, 6]
heapq.heapify(nums)

# Push a new element
heapq.heappush(nums, 7)

# Pop the minimum
minimum = heapq.heappop(nums)

# Peek without removing
minimum = nums[0]

# Get k smallest elements (O(n + k log n))
k_smallest = heapq.nsmallest(3, nums)

# Get k largest elements
k_largest = heapq.nlargest(3, nums)

# Max-heap simulation: negate values
max_heap = []
heapq.heappush(max_heap, -10)
heapq.heappush(max_heap, -3)
max_val = -heapq.heappop(max_heap)  # 10
```

For heaps of tuples, Python compares element by element, so `(priority, value)` tuples sort by priority first — exactly what you want for a priority queue.

## 5 Core Patterns

**Pattern 1: Top K Elements**

The most common heap pattern. To find the K largest elements in an array, maintain a min-heap of size K. For each element, push it; if the heap exceeds size K, pop. After processing all elements, the heap contains the K largest.

```python
def find_k_largest(nums: list[int], k: int) -> list[int]:
    min_heap = []
    for num in nums:
        heapq.heappush(min_heap, num)
        if len(min_heap) > k:
            heapq.heappop(min_heap)
    return min_heap
```

Time: O(n log k). Space: O(k). This is more efficient than sorting (O(n log n)) when k is much smaller than n.

**Pattern 2: K-Way Merge**

Given K sorted lists, merge them efficiently. Push the first element from each list into a min-heap (storing element, list index, position). Pop the minimum, add it to the result, and push the next element from that same list.

```python
def merge_k_sorted_lists(lists):
    heap = []
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0], i, 0))
    result = []
    while heap:
        val, list_idx, element_idx = heapq.heappop(heap)
        result.append(val)
        next_idx = element_idx + 1
        if next_idx < len(lists[list_idx]):
            heapq.heappush(heap, (lists[list_idx][next_idx], list_idx, next_idx))
    return result
```

Time: O(n log k) where n is total elements. Classic problems: Merge K Sorted Lists (LC 23), Smallest Range Covering Elements from K Lists (LC 632).

**Pattern 3: Two Heaps**

This pattern partitions a stream of numbers into two halves: a max-heap for the lower half and a min-heap for the upper half. The tops of the two heaps give you O(1) access to the median. Rebalance after each insertion to keep sizes within 1 of each other.

```python
class MedianFinder:
    def __init__(self):
        self.small = []  # max-heap (negated)
        self.large = []  # min-heap

    def add_num(self, num: int) -> None:
        heapq.heappush(self.small, -num)
        # Balance: ensure small's max <= large's min
        if self.small and self.large and (-self.small[0] > self.large[0]):
            heapq.heappush(self.large, -heapq.heappop(self.small))
        # Rebalance sizes
        if len(self.small) > len(self.large) + 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        elif len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def find_median(self) -> float:
        if len(self.small) > len(self.large):
            return -self.small[0]
        return (-self.small[0] + self.large[0]) / 2.0
```

**Pattern 4: Find Median from Data Stream (LC 295)**

This is the canonical two-heaps problem above. The interviewer is testing whether you can maintain running order statistics efficiently. A sorted list insert is O(n); the two-heaps approach is O(log n) per insertion and O(1) for median queries.

**Pattern 5: Scheduling Problems**

Many scheduling and interval problems need to efficiently track the "minimum end time" among active tasks. Push tasks into a min-heap by end time; when processing a new task, pop all tasks that have already completed.

```python
def min_meeting_rooms(intervals):
    if not intervals:
        return 0
    intervals.sort(key=lambda x: x[0])
    heap = []  # stores end times of ongoing meetings
    for start, end in intervals:
        if heap and heap[0] <= start:
            heapq.heapreplace(heap, end)
        else:
            heapq.heappush(heap, end)
    return len(heap)
```

## When to Use Heap vs Sorted List

A heap excels when you only need the minimum or maximum, not full ordering. If you need to repeatedly extract the smallest element from a dynamic dataset, heap is O(log n) per operation. Maintaining a fully sorted list with `bisect.insort` is also O(log n) for the search but O(n) for insertion due to array shifting.

Use a sorted list (via the `sortedcontainers` library's `SortedList`) when you need arbitrary-index access: "give me the k-th smallest element" or "find elements in a range." A heap cannot answer those queries efficiently.

The decision rule: if your operations are exclusively push + extract-min/max, use a heap. If you need range queries or positional access, use a sorted structure. In interviews, when you see "top K," "K closest," or "K most frequent," reach for the heap immediately.
