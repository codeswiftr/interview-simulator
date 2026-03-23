---
title: "Advanced Stack Patterns: Monotonic Stack and Beyond"
description: "Stack patterns for senior coding interviews — monotonic stack for next greater element, largest rectangle in histogram, daily temperatures, trapping rain water, and the pattern recognition behind stack-based solutions."
date: "2026-03-20"
category: "Algorithms"
---

# Advanced Stack Patterns: Monotonic Stack and Beyond

The stack is one of the most versatile data structures for solving a class of problems that involve finding the next/previous greater or smaller element. These appear regularly at all interview levels. Recognizing the monotonic stack pattern — and knowing when to apply it — is a high-value skill.

## The Monotonic Stack Pattern

A monotonic stack maintains elements in a strictly increasing or decreasing order. When you push an element, you pop all elements that violate the ordering invariant first.

**Key insight:** The elements popped when pushing a new element are exactly those for which the new element is the "answer." If you're looking for the next greater element, the element being pushed is the next greater element for everything it pops.

## Problem 1: Next Greater Element

"For each element in an array, find the next element that is greater than it. Return -1 if no such element exists."

```python
def nextGreaterElement(nums):
    n = len(nums)
    result = [-1] * n
    stack = []  # Stack of indices

    for i in range(n):
        # Pop elements that now have their next greater found
        while stack and nums[i] > nums[stack[-1]]:
            idx = stack.pop()
            result[idx] = nums[i]
        stack.append(i)

    return result  # Remaining elements in stack: result stays -1
```

**Time:** O(n) — each element pushed and popped at most once.

The stack stores indices of elements waiting for their next greater element. When we find a larger element, we answer all waiting elements smaller than it.

## Problem 2: Daily Temperatures

"Given daily temperatures, find how many days until a warmer day. If no warmer day exists, output 0."

Identical pattern to next greater element:

```python
def dailyTemperatures(temperatures):
    n = len(temperatures)
    result = [0] * n
    stack = []  # Stack of indices

    for i in range(n):
        while stack and temperatures[i] > temperatures[stack[-1]]:
            idx = stack.pop()
            result[idx] = i - idx  # Days until warmer
        stack.append(i)

    return result
```

## Problem 3: Largest Rectangle in Histogram

"Given bar heights, find the largest rectangle you can form within the histogram."

For each bar, the rectangle it supports extends left until it hits a shorter bar, and right until it hits a shorter bar. The area = height × (right_boundary - left_boundary - 1).

The stack maintains a monotonically increasing sequence of bar heights. When we encounter a shorter bar, we know the right boundary for all taller bars we're about to pop.

```python
def largestRectangleArea(heights):
    heights.append(0)  # Sentinel to flush stack at end
    stack = [-1]  # Index -1 as sentinel left boundary
    max_area = 0

    for i, h in enumerate(heights):
        while stack[-1] != -1 and heights[stack[-1]] >= h:
            height = heights[stack.pop()]
            width = i - stack[-1] - 1
            max_area = max(max_area, height * width)
        stack.append(i)

    heights.pop()  # Restore array
    return max_area
```

**Time:** O(n). Each bar processed once.

The sentinel `-1` in the stack and `0` appended to heights elegantly handle the edge cases of empty stack and remaining elements after the main loop.

## Problem 4: Trapping Rain Water

"Given heights of walls, compute how much rainwater is trapped."

**Stack approach:** Water is trapped when there's a valley — a shorter element between two taller ones. Process bars left to right; when we find a taller bar (right wall), compute water for the valley between it and the left wall (previous bar in stack).

```python
def trap(height):
    stack = []
    water = 0

    for i, h in enumerate(height):
        while stack and height[i] > height[stack[-1]]:
            bottom = height[stack.pop()]
            if stack:
                left_wall = height[stack[-1]]
                width = i - stack[-1] - 1
                water += (min(left_wall, height[i]) - bottom) * width
        stack.append(i)

    return water
```

Note: Two-pointer approach also solves this in O(n) time and O(1) space (better space than stack approach).

## Problem 5: Remove Duplicate Letters / Smallest Subsequence

"Remove duplicate letters from a string such that each letter appears exactly once and the result is the lexicographically smallest possible subsequence."

This requires a monotonic stack that's character-ordered (greedy), with the constraint that we can only remove a character if it appears later in the string.

```python
def removeDuplicateLetters(s):
    count = Counter(s)  # Remaining occurrences
    in_stack = set()    # Letters currently in stack
    stack = []

    for c in s:
        count[c] -= 1

        if c in in_stack:
            continue

        # Pop larger characters that will appear again later
        while stack and c < stack[-1] and count[stack[-1]] > 0:
            in_stack.remove(stack.pop())

        stack.append(c)
        in_stack.add(c)

    return ''.join(stack)
```

## Recognizing Monotonic Stack Problems

The pattern applies when:
- "Find the next/previous greater/smaller element"
- "For each element, find the nearest element satisfying condition X"
- Problems involving nested structures that pop in LIFO order (brackets, parentheses)
- Histogram and sliding-window maximum problems

The invariant: the stack represents a series of elements in some ordered relationship. When that relationship is violated by a new element, it "resolves" all the elements it violates against.

## Parentheses and Validity

A simpler but related use: validating parentheses nesting using a stack.

```python
def isValid(s):
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}

    for c in s:
        if c in pairs.values():
            stack.append(c)
        elif c in pairs:
            if not stack or stack[-1] != pairs[c]:
                return False
            stack.pop()

    return not stack
```

The stack-based parentheses check generalizes to: "Find the minimum number of bracket removals to make a string valid" (count unmatched open brackets in stack + unmatched close brackets as counter), and "Score of parentheses" (use stack to track nested depth).
