---
title: "Stack and Queue Interview Patterns: Monotonic Stack, Deque, and Priority Queue Applications"
description: "Go beyond basic stack and queue mechanics to master the advanced patterns — monotonic stacks, sliding window deques, and priority queue strategies — that appear in medium and hard interview problems."
date: "2026-03-20"
category: "Algorithms"
---

Stacks and queues look simple until the interview problem requires a monotonic invariant or a sliding window maximum. These are the patterns that separate candidates who have memorized data structures from those who understand when and why to reach for each tool. This guide focuses on the non-obvious applications.

## The Monotonic Stack

A monotonic stack maintains elements in strictly increasing or strictly decreasing order. When a new element violates the monotonic property, you pop until it doesn't, processing the popped elements before pushing the new one. This gives you O(n) solutions to problems that naively look like O(n²).

**Next Greater Element** is the canonical example. For each element, find the first element to its right that is greater. The naive approach is O(n²). With a monotonic decreasing stack:

```python
def next_greater_element(nums):
    result = [-1] * len(nums)
    stack = []  # stores indices
    for i, val in enumerate(nums):
        while stack and nums[stack[-1]] < val:
            idx = stack.pop()
            result[idx] = val
        stack.append(i)
    return result
```

The insight: when you encounter a larger element, every element on the stack waiting for its "next greater" that is smaller than the current element gets its answer right now. Each element is pushed and popped at most once, so the total work is O(n).

**Largest Rectangle in Histogram** (LeetCode 84) uses a monotonic increasing stack. When you encounter a bar shorter than the stack's top, the top bar's rectangle cannot extend further right. Pop it, compute its rectangle width using the new top as the left boundary, record the area, and continue.

**Trapping Rain Water** can be solved with a monotonic stack or with two-pointer approaches. The stack approach is more generalizable to 2D variants.

**Daily Temperatures** (LeetCode 739) is next-greater-element with days instead of values — same pattern, different framing. Recognize the pattern immediately when you see "how many days until a warmer temperature."

## Sliding Window Maximum with Deque

Finding the maximum in a sliding window of size k over an array is O(nk) naively. A deque (double-ended queue) that stores indices in decreasing order of their values reduces this to O(n).

```python
from collections import deque

def max_sliding_window(nums, k):
    dq = deque()  # stores indices, decreasing by nums value
    result = []
    for i, val in enumerate(nums):
        # Remove indices outside the window
        while dq and dq[0] < i - k + 1:
            dq.popleft()
        # Remove indices with smaller values (they'll never be max)
        while dq and nums[dq[-1]] < val:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result
```

The deque's front always holds the index of the current window's maximum. This pattern extends to sliding window minimum (flip the comparison) and to problems where you need to maintain a running statistic over a window efficiently.

## Priority Queue (Heap) Patterns

Python's `heapq` is a min-heap. For a max-heap, negate values.

**K Closest Points to Origin** (LeetCode 973): maintain a max-heap of size k. For each point, push it; if the heap exceeds k, pop the maximum. After processing all points, the heap contains the k closest.

**Top K Frequent Elements**: use a counter to get frequencies, then use `heapq.nlargest(k, counter, key=counter.get)` or build a heap manually. If k is close to n, sorting may be faster (O(n log n) vs O(n log k)).

**Merge K Sorted Arrays**: push the first element of each array into a min-heap as `(value, array_index, element_index)`. Pop the minimum, output it, push the next element from the same array. This is the same strategy as merge-k-sorted-lists but with random-access arrays.

**Find Median from Data Stream** (LeetCode 295) uses two heaps: a max-heap for the lower half and a min-heap for the upper half. After each insertion, rebalance so the heaps differ in size by at most one. The median is the top of the larger heap (or the average of both tops if equal size).

```python
import heapq

class MedianFinder:
    def __init__(self):
        self.lo = []  # max-heap (negate values)
        self.hi = []  # min-heap

    def add_num(self, num):
        heapq.heappush(self.lo, -num)
        heapq.heappush(self.hi, -heapq.heappop(self.lo))
        if len(self.hi) > len(self.lo):
            heapq.heappush(self.lo, -heapq.heappop(self.hi))

    def find_median(self):
        if len(self.lo) > len(self.hi):
            return -self.lo[0]
        return (-self.lo[0] + self.hi[0]) / 2
```

## Stack for Expression Evaluation

Stacks are the natural tool for parsing nested or ordered structures:

- **Valid Parentheses**: push open brackets, pop and check match on close brackets.
- **Basic Calculator** (LeetCode 224): maintain a stack for sign context when entering/leaving parentheses.
- **Decode String** (LeetCode 394): stack of (current_string, repeat_count) pairs for nested encodings like `3[a2[bc]]`.

The general pattern for expression parsing: process left-to-right, use the stack to defer computation until you have enough context (a closing bracket, a lower-precedence operator, etc.).

## Choosing the Right Tool

| Signal in the problem | Likely tool |
|----------------------|-------------|
| "Next greater/smaller element" | Monotonic stack |
| "Largest rectangle / histogram" | Monotonic stack |
| "Sliding window max/min" | Deque |
| "Top K / K largest / K smallest" | Heap |
| "Merge K sorted" | Heap |
| "Find median dynamically" | Two heaps |
| "Balanced parentheses / expression" | Stack |

The faster you recognize the signal, the more time you have to handle edge cases and discuss trade-offs — which is where senior-level candidates differentiate themselves.

## Practice Sequence

- LeetCode 739 (Daily Temperatures) — basic monotonic stack
- LeetCode 84 (Largest Rectangle in Histogram) — advanced monotonic stack
- LeetCode 239 (Sliding Window Maximum) — deque
- LeetCode 295 (Find Median from Data Stream) — two heaps
- LeetCode 23 (Merge K Sorted Lists) — heap
- LeetCode 394 (Decode String) — stack for nested structures
