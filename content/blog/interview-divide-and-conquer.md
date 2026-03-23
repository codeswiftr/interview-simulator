---
title: "Divide and Conquer: Patterns Beyond Merge Sort and Binary Search"
description: "Advanced divide and conquer patterns for coding interviews — closest pair of points, count inversions, median of two sorted arrays, Karatsuba multiplication, and the systematic approach to recognizing D&C problems."
date: "2026-03-20"
category: "Algorithms"
---

# Divide and Conquer: Patterns Beyond Merge Sort and Binary Search

Divide and conquer is a paradigm, not just merge sort and binary search. Senior interviews probe whether you can apply D&C thinking to novel problems — not just recognize it in textbook algorithms. This guide covers the patterns and the reasoning process.

## The D&C Framework

Every divide and conquer algorithm has three steps:
1. **Divide:** Split the problem into subproblems (usually of roughly equal size)
2. **Conquer:** Solve subproblems recursively (or directly if small enough)
3. **Combine:** Merge subproblem solutions into the full solution

The power of D&C: if splitting and combining are O(n) and the depth is O(log n), the total work is O(n log n). This beats O(n²) brute force for many problems.

## Median of Two Sorted Arrays: O(log(m+n))

"Find the median of two sorted arrays of total length m+n."

Binary search on the partition point: partition both arrays such that the left halves contain exactly (m+n)/2 elements. The max of the left halves and min of the right halves determine the median.

```python
def findMedianSortedArrays(nums1, nums2):
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1  # Ensure nums1 is shorter

    m, n = len(nums1), len(nums2)
    lo, hi = 0, m

    while lo <= hi:
        partition1 = (lo + hi) // 2
        partition2 = (m + n + 1) // 2 - partition1

        max_left1 = float('-inf') if partition1 == 0 else nums1[partition1 - 1]
        min_right1 = float('inf') if partition1 == m else nums1[partition1]
        max_left2 = float('-inf') if partition2 == 0 else nums2[partition2 - 1]
        min_right2 = float('inf') if partition2 == n else nums2[partition2]

        if max_left1 <= min_right2 and max_left2 <= min_right1:
            if (m + n) % 2 == 1:
                return float(max(max_left1, max_left2))
            else:
                return (max(max_left1, max_left2) + min(min_right1, min_right2)) / 2
        elif max_left1 > min_right2:
            hi = partition1 - 1
        else:
            lo = partition1 + 1

    return -1.0
```

The key insight: binary search on partition position (not on values). The valid partition is where max_left1 ≤ min_right2 and max_left2 ≤ min_right1.

## Closest Pair of Points: O(n log n)

Brute force is O(n²). D&C achieves O(n log n):

1. Sort points by x-coordinate
2. Recursively find closest pair in left half (distance `d_L`) and right half (distance `d_R`)
3. Let `d = min(d_L, d_R)`. Check if there's a closer pair that straddles the midpoint: only examine points within `d` of the center line, sorted by y-coordinate

The non-obvious insight: in the strip of width `2d` around the center line, you only need to check 7 subsequent points (by y-coordinate) for each point. This bounds the combine step at O(n), giving O(n log n) total.

```python
def closest_pair(points):
    def dist(p1, p2):
        return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2) ** 0.5

    def closest(pts):
        n = len(pts)
        if n <= 3:
            return min(dist(pts[i], pts[j])
                      for i in range(n) for j in range(i+1, n))

        mid = n // 2
        midX = pts[mid][0]
        d = min(closest(pts[:mid]), closest(pts[mid:]))

        # Check strip
        strip = sorted([p for p in pts if abs(p[0] - midX) < d], key=lambda p: p[1])
        for i in range(len(strip)):
            for j in range(i+1, min(i+8, len(strip))):
                if strip[j][1] - strip[i][1] >= d:
                    break
                d = min(d, dist(strip[i], strip[j]))

        return d

    return closest(sorted(points, key=lambda p: p[0]))
```

## Count Inversions: O(n log n)

Covered in the merge sort guide — inversions are naturally counted during the merge step. This is D&C: count inversions in left half, right half, and cross-inversions during merge.

## Skyline Problem: O(n log n) with D&C or Priority Queue

"Given buildings as [left, right, height], return the skyline (silhouette outline)."

D&C approach: recursively compute skyline of left half and right half, then merge the two skylines in O(n) (similar to merge in merge sort).

The merge of two skylines: two pointers, one on each skyline, tracking the current height of each. The result height is max(h1, h2).

## Quickselect: Expected O(n) for k-th Element

Finding the k-th smallest element. Partition like quicksort, but recurse only on the side containing k.

```python
import random

def quickselect(nums, k):
    def select(lo, hi, k):
        if lo == hi:
            return nums[lo]

        pivot_idx = random.randint(lo, hi)
        nums[pivot_idx], nums[hi] = nums[hi], nums[pivot_idx]

        p = lo
        for i in range(lo, hi):
            if nums[i] <= nums[hi]:
                nums[i], nums[p] = nums[p], nums[i]
                p += 1
        nums[p], nums[hi] = nums[hi], nums[p]

        if k == p:
            return nums[p]
        elif k < p:
            return select(lo, p - 1, k)
        else:
            return select(p + 1, hi, k)

    return select(0, len(nums) - 1, k)
```

Expected O(n) time because random pivot partitions roughly in half on average. Worst case O(n²) with pathological input — mitigated by random pivot selection.

## Recognizing D&C Opportunities

D&C is worth considering when:
- The problem on n elements can be reduced to 2+ subproblems of size ≈ n/2
- Combining subproblem solutions is O(n) or less
- Brute force is O(n²) or worse and you need better

The master theorem tells you the complexity: T(n) = 2T(n/2) + O(n) → O(n log n). That's the D&C sweet spot.

If combining subproblems is expensive (O(n log n) or more), D&C may not help. If the subproblems don't reduce to roughly equal sizes, analyze with the full recurrence.
