---
title: "Monotonic Stack Interview Guide: Next Greater Element, Histograms, and Span Problems"
description: "Master monotonic stacks for coding interviews — next greater/smaller element, largest rectangle in histogram, daily temperatures, and stock span problems."
date: "2026-03-20"
category: "Algorithms"
---

# Monotonic Stack Interview Guide: Next Greater Element, Histograms, and Span Problems

A monotonic stack is a stack that maintains elements in either strictly increasing or strictly decreasing order. It's not a data structure you'll find in a standard library — it's a technique that reduces certain O(n²) brute-force solutions to O(n) by processing elements in a specific order while discarding elements that can no longer contribute to future answers.

## The Core Insight

Many array problems ask: "for each element, find the nearest element to the left/right that is greater/smaller." Brute force: for each element, scan outward — O(n²). Monotonic stack: maintain a stack such that when you process each element, you immediately know the answer for all elements it "dominates."

The key: when you push a new element onto a monotonic stack, you pop all elements that violate the monotonic property. Each element is pushed and popped at most once, so the total work is O(n).

## Next Greater Element

"For each element in the array, find the next element to its right that is greater."

```python
def next_greater(arr):
    n = len(arr)
    result = [-1] * n
    stack = []  # stores indices
    
    for i in range(n):
        # While stack is non-empty and current element is greater
        # than the element at the top of the stack
        while stack and arr[i] > arr[stack[-1]]:
            idx = stack.pop()
            result[idx] = arr[i]
        stack.append(i)
    
    return result
```

The stack maintains indices of elements for which we haven't yet found a next greater element. When we encounter an element larger than the stack top, that's the answer for the popped element.

Variation: **Next Greater Element II** (circular array) — run the same loop twice (indices 0..2n-1, using i % n) so elements near the end can find answers from the beginning.

## Daily Temperatures

"Given temperatures, return how many days until a warmer day."

This is next greater element with distances instead of values:

```python
def daily_temperatures(temps):
    result = [0] * len(temps)
    stack = []
    
    for i, t in enumerate(temps):
        while stack and t > temps[stack[-1]]:
            j = stack.pop()
            result[j] = i - j
        stack.append(i)
    
    return result
```

## Largest Rectangle in Histogram

One of the most famous monotonic stack problems. Given heights of bars in a histogram, find the largest rectangle you can form.

The key insight: for each bar, the rectangle with that bar as the minimum height extends left and right until it hits a shorter bar. Those boundaries are the previous smaller and next smaller elements — computable with monotonic stacks.

```python
def largest_rectangle(heights):
    heights = [0] + heights + [0]  # sentinels
    stack = [0]
    max_area = 0
    
    for i in range(1, len(heights)):
        while heights[i] < heights[stack[-1]]:
            h = heights[stack.pop()]
            w = i - stack[-1] - 1
            max_area = max(max_area, h * w)
        stack.append(i)
    
    return max_area
```

The sentinels (0 at both ends) ensure the stack is always non-empty and all bars get processed.

## Maximal Rectangle in Binary Matrix

This extends histogram to a 2D matrix: for each row, compute the histogram of consecutive 1s above each cell, then apply the largest rectangle algorithm. O(m×n) total.

## Stock Span Problem

"For each day's price, find how many consecutive days (including today) the price was less than or equal to today's price."

This is a "previous greater element" problem. Use a decreasing stack:

```python
def stock_span(prices):
    stack = []  # (price, span)
    result = []
    
    for p in prices:
        span = 1
        while stack and stack[-1][0] <= p:
            span += stack.pop()[1]
        stack.append((p, span))
        result.append(span)
    
    return result
```

## Sum of Subarray Minimums

"Find the sum of the minimum element of every subarray." 

For each element, find how many subarrays have it as the minimum. This uses the "previous less element" and "next less element" — each computed with a monotonic stack. The count of subarrays where arr[i] is minimum equals (i - prev_less[i]) * (next_less[i] - i). O(n) with two passes.

## Trapping Rain Water

"Given an elevation map, compute how much water can be trapped."

Monotonic stack approach: maintain a decreasing stack. When you find a higher bar, the top of the stack is a "valley" — calculate the water trapped between the popped element and the new bar.

The alternative two-pointer approach is often cleaner for this specific problem, but the stack approach generalizes better to variants.

## Recognizing Monotonic Stack Problems

Use a monotonic stack when:
- You need "nearest greater/smaller element to the left/right"
- You need span or distance to the next element that satisfies a condition  
- The problem involves computing properties of subarrays where you care about the minimum or maximum
- You see O(n²) brute force with nested loops that scan left or right

The template is almost always the same: iterate left to right, maintain a stack of indices, pop when the current element violates the monotonic property, process the popped element's answer, push current index.

## Interview Tip

When you identify a monotonic stack problem, state the pattern clearly: "I'll maintain a stack of indices in decreasing order. When I encounter an element larger than the top, I pop and record the answer." This shows you know the technique, not just the solution.

LeetCode practice: 739 (Daily Temperatures), 84 (Largest Rectangle in Histogram), 85 (Maximal Rectangle), 901 (Stock Span), 907 (Sum of Subarray Minimums), 42 (Trapping Rain Water).
