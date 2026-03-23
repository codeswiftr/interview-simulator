---
title: "Binary Search Patterns for Coding Interviews: Beyond the Basics"
description: "Master binary search for technical interviews. Covers classic binary search, searching on answer space, rotated arrays, and the template approach for writing bug-free binary search every time."
date: "2025-10-07"
category: "Interview Preparation"
---

# Binary Search Patterns for Coding Interviews

Binary search is one of the most frequently tested patterns in coding interviews — and one of the most frequently implemented incorrectly. Off-by-one errors haunt even experienced engineers. This guide gives you a reliable template and covers the patterns that appear most in interviews.

## Why Binary Search Is Tricky

Binary search is conceptually simple — divide the search space in half each iteration — but gets tricky in implementation because:
- Should `mid` round up or down?
- Should the loop condition be `left < right` or `left <= right`?
- Should we do `right = mid` or `right = mid - 1`?

The answer depends on the invariant you're maintaining. Using a consistent template eliminates these bugs.

## The Two Templates

### Template 1: Exact Match

Use when you're searching for a specific target that must exist.

```python
def binary_search(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = left + (right - left) // 2  # Avoids integer overflow
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1  # Not found
```

### Template 2: Left Boundary (most versatile)

Use when you want the leftmost position where a condition becomes true. Works for finding the first occurrence, insertion position, and "search on answer space."

```python
def left_bound(nums, target):
    left, right = 0, len(nums)  # Note: right = len(nums), not len-1
    while left < right:          # Note: strict less than
        mid = left + (right - left) // 2
        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid           # Note: right = mid, not mid-1
    return left  # Index of leftmost target (or insertion point)
```

**Why Template 2 is powerful**: It works when the "found" condition is continuous — there's a boundary where the condition changes from False to True, and you want the boundary.

## Pattern 1: Search in Rotated Array

A sorted array rotated at some pivot. Find a target element.

```python
def search_rotated(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if nums[mid] == target:
            return mid
        # Left half is sorted
        if nums[left] <= nums[mid]:
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        # Right half is sorted
        else:
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    return -1
```

**Key insight**: At least one half is always sorted. Determine which half, then check if target is in it.

## Pattern 2: Find Peak Element

Find any peak element where `nums[i] > nums[i-1]` and `nums[i] > nums[i+1]`.

```python
def find_peak(nums):
    left, right = 0, len(nums) - 1
    while left < right:
        mid = left + (right - left) // 2
        if nums[mid] > nums[mid + 1]:
            right = mid    # Peak is at or left of mid
        else:
            left = mid + 1  # Peak is right of mid
    return left
```

## Pattern 3: Search on Answer Space ("Squroot")

Binary search doesn't only apply to arrays — it applies whenever you have a monotonic function. Search on the **answer** itself.

```python
# Integer square root: find largest k where k*k <= n
def my_sqrt(n):
    if n < 2:
        return n
    left, right = 1, n // 2
    while left <= right:
        mid = left + (right - left) // 2
        if mid * mid == n:
            return mid
        elif mid * mid < n:
            left = mid + 1
        else:
            right = mid - 1
    return right
```

**General pattern**: Define a predicate `feasible(k)` that is monotonically true/false. Binary search for the boundary.

**Classic problems using this pattern:**
- Minimum speed to arrive on time (LeetCode 1870)
- Koko eating bananas (LeetCode 875)
- Capacity to ship packages (LeetCode 1011)

For these problems, the template is:
```python
left, right = min_possible_answer, max_possible_answer
while left < right:
    mid = left + (right - left) // 2
    if feasible(mid):
        right = mid
    else:
        left = mid + 1
return left
```

## Pattern 4: First and Last Occurrence

Find both the first and last index of a target in a sorted array.

```python
def find_range(nums, target):
    def left_bound(target):
        left, right = 0, len(nums)
        while left < right:
            mid = left + (right - left) // 2
            if nums[mid] < target:
                left = mid + 1
            else:
                right = mid
        return left
    
    first = left_bound(target)
    if first == len(nums) or nums[first] != target:
        return [-1, -1]
    last = left_bound(target + 1) - 1
    return [first, last]
```

## Interview Tips

**1. Always write mid as `left + (right - left) // 2`**, not `(left + right) // 2`. The latter overflows in languages with fixed-size integers (C++, Java).

**2. State your invariant aloud**: "I'm maintaining the invariant that the answer is always in [left, right]." This helps you verify correctness and demonstrates clear thinking.

**3. Test with small inputs**: `[1]`, `[1, 2]`, `[1, 2, 3]`. Binary search bugs almost always manifest on small arrays.

**4. Don't confuse the loop condition**: `left <= right` (Template 1) vs `left < right` (Template 2). Know which you're using and why.

**5. For "search on answer space" problems**: The hardest part is recognizing it IS a binary search problem. Ask: "Is there a monotonic threshold? Below X, condition fails; above X, condition holds?"

With these patterns and a consistent template, binary search goes from a source of interview anxiety to one of your most reliable problem-solving tools.
