---
title: "Binary Search Advanced: Beyond Sorted Arrays"
description: "Advanced binary search patterns for technical interviews — search in rotated sorted array, find minimum in rotated array, search a 2D matrix, kth smallest in sorted matrix, median of two sorted arrays, and the general binary search template."
date: "2026-03-20"
category: "Algorithms"
---

# Binary Search Advanced: Beyond Sorted Arrays

Basic binary search is known by everyone. Advanced binary search — recognizing that the pattern applies to non-obvious problems — separates senior engineers from junior ones. The key insight: binary search applies to any problem where you can determine which half of the search space contains the answer.

## The General Template

Binary search reduces to: maintain `left` and `right` pointers, compute `mid`, determine which half to keep.

```python
def binary_search(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = left + (right - left) // 2  # avoid overflow
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
```

**`left + (right - left) // 2` vs `(left + right) // 2`:** The first avoids integer overflow. In Python this doesn't matter (arbitrary precision integers), but in Java/C++ with 32-bit ints, `(left + right)` can overflow when both are large.

**`left <= right` vs `left < right`:** The `<=` variant terminates with an empty range; good for finding exact matches. The `<` variant terminates with `left == right`; good for finding boundaries.

## Rotated Sorted Array

Array was sorted, then rotated at an unknown pivot. Find a target.

Key insight: at least one half is always sorted. Check which half is sorted (by comparing `nums[mid]` with `nums[left]`), then determine if the target is in that half.

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

**Variant — find minimum in rotated array:** The minimum is at the inflection point. The right half of any split with a rotation contains the minimum. Binary search for the smallest element by always moving toward the unsorted half.

## Search in 2D Matrix

Matrix where each row is sorted and the first element of each row > last element of previous row. Find a target.

Treat the matrix as a flattened sorted array: `nums[mid]` maps to `matrix[mid // cols][mid % cols]`.

```python
def searchMatrix(matrix, target):
    rows, cols = len(matrix), len(matrix[0])
    left, right = 0, rows * cols - 1
    while left <= right:
        mid = (left + right) // 2
        val = matrix[mid // cols][mid % cols]
        if val == target: return True
        elif val < target: left = mid + 1
        else: right = mid - 1
    return False
```

**Variant — matrix where rows and columns are individually sorted (not globally sorted):** Use the staircase search from top-right corner: if `matrix[r][c] > target`, move left; if less, move down. O(M+N) — not binary search.

## First and Last Position

Find the first and last occurrence of target in a sorted array. Two binary searches: one for the leftmost position, one for the rightmost.

```python
def searchRange(nums, target):
    def find_left():
        left, right, result = 0, len(nums)-1, -1
        while left <= right:
            mid = (left + right) // 2
            if nums[mid] == target:
                result = mid
                right = mid - 1  # keep searching left
            elif nums[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return result
    
    def find_right():
        left, right, result = 0, len(nums)-1, -1
        while left <= right:
            mid = (left + right) // 2
            if nums[mid] == target:
                result = mid
                left = mid + 1  # keep searching right
            elif nums[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return result
    
    return [find_left(), find_right()]
```

## Binary Search on Answer Space

The most powerful generalization: binary search on the answer rather than the array.

**Kth smallest in a sorted matrix:** Binary search on value range `[min, max]`. For a given mid value, count elements ≤ mid. If count ≥ k, the answer is ≤ mid; search lower half.

**Minimum days to make M bouquets:** Can we make M bouquets in D days? Binary search on D. For each D, greedily check if M bouquets are possible.

**Find peak element:** Array with no adjacent duplicates has at least one peak. Binary search: if `nums[mid] < nums[mid+1]`, peak is in the right half; otherwise it's in the left half (or at mid itself).

**Template for "binary search on answer":**
```python
def binary_search_answer(low, high, feasible_fn):
    result = -1
    while low <= high:
        mid = (low + high) // 2
        if feasible_fn(mid):
            result = mid
            high = mid - 1  # or low = mid + 1 depending on direction
        else:
            low = mid + 1   # or high = mid - 1
    return result
```

## Median of Two Sorted Arrays

Hardest binary search problem: O(log(min(m,n))) time. Binary search on the partition point of the smaller array.

The idea: find a partition of both arrays such that the left half of the combined array contains the first `(m+n+1)//2` elements. Use binary search on the partition point of the smaller array; the partition point of the larger array is determined by the constraint.

Check: `nums1[partition1-1] <= nums2[partition2]` and `nums2[partition2-1] <= nums1[partition1]`. If not satisfied, move the partition.

This problem is rare in interviews but demonstrates deep binary search mastery. Practice the full implementation at least once.

## Recognizing Binary Search Problems

Ask yourself: is there a monotone property? (All `x < answer` are infeasible; all `x >= answer` are feasible.) Can I eliminate half the search space with each step? Is the space large enough that linear search is O(N) but binary search would be O(log N)?

If yes to these: binary search likely applies. The hardest part is formulating the correct feasibility function and determining which direction to eliminate.

