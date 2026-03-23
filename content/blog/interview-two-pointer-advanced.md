---
title: "Advanced Two-Pointer Patterns: 3Sum, Container Water, Trapping Rain Water"
description: "Go beyond the basic two-pointer pattern with in-depth coverage of the classic hard problems: 3Sum with duplicate handling, Container With Most Water, and the Trapping Rain Water problem with multiple approaches."
date: "2026-03-20"
category: "Algorithms"
---

The two-pointer technique is one of those patterns that looks obvious in hindsight but requires practice to apply consistently. The basic idea — converge two pointers from opposite ends based on a comparison — becomes non-obvious when you need to handle duplicates correctly or prove to yourself why convergence finds the optimal answer. This guide works through the three hardest two-pointer problems in depth.

## Why Two Pointers Work for Sorted Arrays

The core insight: when an array is sorted and you have pointers at opposite ends, you can eliminate large chunks of possibilities with each step. If `a[left] + a[right] > target`, every pair with `right` and anything to the right of `left` is also too large (since the array is sorted). Moving `right` left eliminates those. Similarly for too-small sums. This gives O(n) pair evaluation after O(n log n) sorting.

The invariant: at every step, the optimal answer (if it exists) is within the range `[left, right]`. Both pointers' moves preserve this invariant. Proving this to your interviewer is what distinguishes a candidate who understands the pattern from one who memorized the code.

## 3Sum: The Duplicate Handling Problem

**LeetCode 15.** Find all unique triplets that sum to zero.

The naive approach — three nested loops — is O(n³). The standard approach: sort, then for each element, run two pointers on the remainder.

```python
def three_sum(nums):
    nums.sort()
    result = []
    
    for i in range(len(nums) - 2):
        # Skip duplicate values for the first element
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        
        left, right = i + 1, len(nums) - 1
        
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total == 0:
                result.append([nums[i], nums[left], nums[right]])
                # Skip duplicates for second and third elements
                while left < right and nums[left] == nums[left + 1]:
                    left += 1
                while left < right and nums[right] == nums[right - 1]:
                    right -= 1
                left += 1
                right -= 1
            elif total < 0:
                left += 1
            else:
                right -= 1
    
    return result
```

The duplicate skipping logic is where most candidates make mistakes. There are two places duplicates can occur:

1. **The outer loop:** If `nums[i]` equals the previous `nums[i-1]`, we'd generate the same triplets we already generated with that value. Skip with `if i > 0 and nums[i] == nums[i-1]: continue`.

2. **After finding a valid triplet:** If `nums[left+1] == nums[left]`, including it would produce a duplicate triplet. Advance past all duplicates before moving both pointers. The advance loops run *before* the final `left += 1; right -= 1` move.

A common bug: writing `nums[left] == nums[left + 1]` but forgetting the `while left < right` bounds check inside the skip loop.

**3Sum Closest** (LeetCode 16): track the triplet sum closest to target. Same structure, no duplicate handling needed (just return when diff == 0).

**4Sum** (LeetCode 18): add another outer loop. Two outer loops for the first two elements, two-pointer for the remaining two. Same duplicate-skip pattern at each level.

## Container With Most Water

**LeetCode 11.** Given heights of n vertical lines, find two lines that form a container holding the most water.

```python
def max_area(height):
    left, right = 0, len(height) - 1
    max_water = 0
    
    while left < right:
        width = right - left
        water = min(height[left], height[right]) * width
        max_water = max(max_water, water)
        
        if height[left] <= height[right]:
            left += 1
        else:
            right -= 1
    
    return max_water
```

**Why moving the shorter side is correct** — this is the proof interviewers want to see:

When `height[left] <= height[right]`, the current container's area is limited by `height[left]`. If we move `right` inward instead, the width decreases and the height is still limited by `height[left]` (since whatever is at `right-1` is either shorter than `height[left]`, equal, or taller — but the minimum with `height[left]` stays the same or decreases). We cannot improve by moving `right`. Therefore, moving `left` is the only move that could possibly find a better container.

This proof by elimination is the key insight. Stating it — even briefly — in an interview separates a good answer from an excellent one.

## Trapping Rain Water

**LeetCode 42.** Given an elevation map, compute how much rain water it can trap.

Water above position `i` equals `min(max_left[i], max_right[i]) - height[i]`. You need the maximum height to the left and right of every position.

**Approach 1: Precompute arrays (O(n) time, O(n) space):**

```python
def trap(height):
    n = len(height)
    max_left = [0] * n
    max_right = [0] * n
    
    for i in range(1, n):
        max_left[i] = max(max_left[i-1], height[i-1])
    for i in range(n-2, -1, -1):
        max_right[i] = max(max_right[i+1], height[i+1])
    
    water = 0
    for i in range(n):
        water_at_i = min(max_left[i], max_right[i]) - height[i]
        water += max(0, water_at_i)
    return water
```

**Approach 2: Two pointers (O(n) time, O(1) space):**

```python
def trap_two_pointer(height):
    left, right = 0, len(height) - 1
    left_max = right_max = 0
    water = 0
    
    while left < right:
        if height[left] <= height[right]:
            if height[left] >= left_max:
                left_max = height[left]
            else:
                water += left_max - height[left]
            left += 1
        else:
            if height[right] >= right_max:
                right_max = height[right]
            else:
                water += right_max - height[right]
            right -= 1
    
    return water
```

**Why the two-pointer approach works:** When `height[left] <= height[right]`, we know the right boundary is at least as tall as the left boundary. So the water above `left` is determined by `left_max` (since the right side won't be the limiting factor). We can compute the water at `left` with confidence and advance. The argument is symmetric for the right side.

This proof is subtler than Container With Most Water. Practice articulating it before your interview — writing the code is easier than explaining the correctness.

**Approach 3: Stack-based** — useful for understanding the 2D variant (LeetCode 407, Trapping Rain Water II). Process bars using a monotonic stack; when you find a taller bar, compute trapped water horizontally between the stack's top and the new bar.

## Choosing the Right Approach in an Interview

For Trapping Rain Water, present in this order:
1. Brute force O(n²): for each cell, scan left and right for max heights
2. Precompute arrays O(n) time and space: explain the `min(max_left, max_right) - height` formula
3. Two pointers O(n) time, O(1) space: explain why the pointer movement preserves correctness

Interviewers at top companies expect you to know all three and be able to explain the trade-offs. Jumping straight to two pointers without explaining why it's correct is common and unsatisfying.

## Summary of Patterns

| Problem | Key technique | Watch for |
|---------|--------------|-----------|
| 3Sum | Sort + two pointers per outer element | Duplicate skip at outer and inner levels |
| Container Water | Converge from both ends, move shorter | Prove why moving shorter is correct |
| Trapping Rain Water | Left/right max + two pointers | Prove why pointer movement is safe |

The two-pointer technique rewards candidates who understand *why* pointer movements are safe, not just *how* to implement them. That understanding is what you're building with each problem.
