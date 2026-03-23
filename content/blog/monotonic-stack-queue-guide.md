---
title: "Monotonic Stack and Deque: Interview Patterns and Problem-Solving Guide"
description: "How to recognize and solve monotonic stack and deque problems in technical interviews — next greater element, sliding window maximum, largest rectangle, and the pattern recognition framework."
date: "2026-03-20"
category: "Algorithms"
---

# Monotonic Stack and Deque: Interview Patterns and Problem-Solving Guide

Monotonic stack problems appear regularly in medium and hard technical interviews, but many engineers don't have a clear mental model for when to use them. Once you see the pattern, a whole class of "how do I do this in O(n)?" problems becomes tractable.

## What Is a Monotonic Stack?

A monotonic stack is a stack that maintains elements in monotonically increasing or decreasing order. When you push a new element, you first pop all elements that violate the monotonic property.

The key insight: every element is pushed and popped at most once, giving O(n) total time even though the inner loop appears nested.

```python
def next_greater_element(nums):
    result = [-1] * len(nums)
    stack = []  # indices of elements without a "next greater" yet
    
    for i, num in enumerate(nums):
        # Pop elements smaller than current — current is their "next greater"
        while stack and nums[stack[-1]] < num:
            idx = stack.pop()
            result[idx] = num
        stack.append(i)
    
    return result
```

This is the core template. The stack holds indices of elements that haven't found their answer yet.

## When to Use a Monotonic Stack

The pattern applies when you need to find, for each element, the next/previous element that is greater/smaller. The trigger phrases in problem statements:
- "Next greater element"
- "Previous smaller element"
- "Days until warmer temperature"
- "Largest rectangle in histogram"
- "Trapping rain water"

Any problem asking "for each position, what's the nearest position to the left/right satisfying some comparison" is a candidate.

## Core Patterns

**Next Greater (Increasing from bottom):**
Maintain a decreasing stack (top is smallest). When you encounter a larger element, it's the "next greater" for everything it pops.

**Next Smaller (Decreasing from bottom):**
Maintain an increasing stack. When you encounter a smaller element, it's the "next smaller" for everything it pops.

**Largest Rectangle in Histogram:**
For each bar, find the nearest shorter bar on the left and right. The rectangle using this bar as height extends from left+1 to right-1.

```python
def largest_rectangle(heights):
    stack = []  # monotonically increasing
    max_area = 0
    heights = heights + [0]  # sentinel forces all remaining bars to process
    
    for i, h in enumerate(heights):
        while stack and heights[stack[-1]] > h:
            height = heights[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            max_area = max(max_area, height * width)
        stack.append(i)
    
    return max_area
```

**Trapping Rain Water:**
Classic two-pointer or monotonic stack. The stack approach: for each position, when we find a bar taller than the stack top, water can be trapped between the new bar, the stack top, and the next element.

## Monotonic Deque: Sliding Window Maximum

A monotonic deque (double-ended queue) extends the idea to sliding windows. For sliding window maximum, maintain a decreasing deque of indices:

```python
from collections import deque

def max_sliding_window(nums, k):
    dq = deque()  # indices, decreasing values
    result = []
    
    for i, num in enumerate(nums):
        # Remove elements outside the window
        while dq and dq[0] < i - k + 1:
            dq.popleft()
        
        # Maintain decreasing order — pop smaller elements from right
        while dq and nums[dq[-1]] < num:
            dq.pop()
        
        dq.append(i)
        
        # Window is full
        if i >= k - 1:
            result.append(nums[dq[0]])
    
    return result
```

The deque front always holds the index of the maximum in the current window.

## Interview Problem Recognition

When you see a problem and don't immediately know the approach, ask:
1. "For each element, do I need to know the nearest element satisfying some comparison?" → monotonic stack
2. "Do I need the maximum/minimum in a sliding window?" → monotonic deque
3. "Does the brute force involve nested loops comparing each element to a range of others?" → probably monotonic stack or deque can reduce to O(n)

## Common Interview Problems

| Problem | Approach |
|---------|----------|
| Next Greater Element I/II | Decreasing stack |
| Daily Temperatures | Decreasing stack (indices) |
| Largest Rectangle in Histogram | Increasing stack |
| Trapping Rain Water | Stack or two-pointer |
| Sliding Window Maximum | Monotonic deque |
| Sum of Subarray Minimums | Monotonic stack + contribution |
| Remove K Digits (lexicographically smallest) | Monotonic stack greedy |

## Communicating in Interviews

When you recognize a monotonic stack problem, narrate the insight: "I notice that for each element I need the nearest element that's larger/smaller, which is a classic monotonic stack pattern. The key is that each element is pushed and popped exactly once, giving O(n) time."

Then walk through a small example by hand before coding. The stack state at each step reveals the logic. Interviewers reward candidates who can explain *why* the monotonic property enables O(n) — it's not magic, it's that the amortized cost per element is O(1).
