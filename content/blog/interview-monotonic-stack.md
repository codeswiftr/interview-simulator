---
title: "Monotonic Stack: The Interview Pattern That Unlocks Hard Problems"
description: "Master monotonic stacks and queues for technical interviews — next greater element, stock span, largest rectangle in histogram, sliding window maximum, and the template for recognizing and solving monotonic stack problems."
date: "2026-03-20"
category: "Algorithms"
---

# Monotonic Stack: The Interview Pattern That Unlocks Hard Problems

Monotonic stacks are a pattern that consistently appears in hard LeetCode problems — next greater element, largest rectangle in histogram, trapping rain water, stock span. Once you understand the pattern, these problems become tractable. Without it, they seem like puzzle-solving with no clear structure.

## What Is a Monotonic Stack?

A monotonic stack maintains elements in either increasing or decreasing order. When you push a new element, you pop everything that violates the order first.

**Monotonically increasing stack:** Each element is greater than the one below it. When pushing `x`, pop everything ≥ `x` first.

**Monotonically decreasing stack:** Each element is smaller than the one below it. When pushing `x`, pop everything ≤ `x` first.

The insight: when you pop an element `top` because `x` is greater (or smaller), you've found a relationship between `x` and `top`. This is how you compute "next greater element," "previous smaller element," and similar relationships in O(N) — each element is pushed and popped at most once.

## Next Greater Element

For each element in an array, find the next element to its right that is greater than it. Brute force: O(N²). With monotonic stack: O(N).

```python
def next_greater(nums):
    result = [-1] * len(nums)
    stack = []  # stores indices
    for i, num in enumerate(nums):
        while stack and nums[stack[-1]] < num:
            idx = stack.pop()
            result[idx] = num  # num is next greater for idx
        stack.append(i)
    return result
```

Pattern: we maintain a decreasing stack (each element awaits a next greater). When we find something greater, we resolve all smaller waiting elements.

## Largest Rectangle in Histogram

Given bar heights, find the largest rectangle that can be drawn. Classic hard problem. O(N) with monotonic stack.

Idea: for each bar, find how far left and right it can extend while remaining the shortest bar. The rectangle area = height × width.

```python
def largest_rectangle(heights):
    heights.append(0)  # sentinel to flush remaining elements
    stack = [-1]  # stack of indices; -1 is a sentinel
    max_area = 0
    for i, h in enumerate(heights):
        while stack[-1] != -1 and heights[stack[-1]] >= h:
            height = heights[stack.pop()]
            width = i - stack[-1] - 1
            max_area = max(max_area, height * width)
        stack.append(i)
    return max_area
```

When we pop `heights[stack[-1]]` because `h` is smaller, the width is determined by the new top of the stack (left boundary) and current index (right boundary).

## Trapping Rain Water

How much water can be trapped between bars? This has multiple solutions; the monotonic stack approach is clean.

Alternative (two-pointer): for each position, water level = min(max_left, max_right) - height. Use two passes (or two pointers) to compute this in O(N) time, O(1) space.

Stack approach: maintain decreasing stack. When we find a taller bar, water fills the gap between the current bar and the one previously taller on the left.

## Sliding Window Maximum

Given a sliding window of size k, find the maximum in each window. Brute force: O(NK). Monotonic deque: O(N).

Use a deque (double-ended queue) maintaining indices in decreasing order by value. Front of deque is always the maximum of the current window.

```python
from collections import deque

def sliding_window_max(nums, k):
    result = []
    dq = deque()
    for i, num in enumerate(nums):
        # Remove elements outside the window
        while dq and dq[0] < i - k + 1:
            dq.popleft()
        # Maintain decreasing order
        while dq and nums[dq[-1]] < num:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result
```

Key: we pop from the back when new element is greater (maintaining decreasing order) and pop from the front when the index is outside the window.

## Daily Temperatures

Given temperatures, find how many days until a warmer temperature. Classic next greater element variant:

```python
def daily_temperatures(temps):
    result = [0] * len(temps)
    stack = []
    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t:
            idx = stack.pop()
            result[idx] = i - idx
        stack.append(i)
    return result
```

## Recognizing Monotonic Stack Problems

The pattern appears when:
- You need "next greater" or "previous smaller" relationships
- The problem involves a span or distance to a boundary
- You're computing something over a sliding window that depends on order
- Rectangles, water trapping, or "how far can this extend" problems

If the brute force is O(N²) involving comparisons of elements at different positions, and the comparisons have a monotonic relationship, a monotonic stack often brings it to O(N).

## Template

```python
def monotonic_stack_template(arr):
    stack = []
    result = [...]
    for i, val in enumerate(arr):
        # Adjust comparison for increasing vs decreasing stack
        while stack and arr[stack[-1]] [</>] val:
            top = stack.pop()
            # Compute result using top, i, and stack[-1] (new top)
            result[top] = ...
        stack.append(i)
    return result
```

Practice these problems in order: 496 (Next Greater Element I), 739 (Daily Temperatures), 84 (Largest Rectangle in Histogram), 42 (Trapping Rain Water), 239 (Sliding Window Maximum). Each builds on the previous.

