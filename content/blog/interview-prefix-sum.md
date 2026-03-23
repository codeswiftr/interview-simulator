---
title: "Prefix Sum: The Most Underused Interview Technique"
description: "How prefix sums solve range queries, subarray problems, and 2D grid problems in O(1) per query — including difference arrays, 2D prefix sums, and hash map variants for interview success."
date: "2026-03-20"
category: "Algorithms"
---

# Prefix Sum: The Most Underused Interview Technique

Prefix sum is one of the highest-ROI techniques in competitive programming and coding interviews. It transforms range query problems from O(n) per query to O(1) per query, after O(n) preprocessing. Engineers who recognize when to apply it solve in minutes what others attempt with nested loops. This guide covers prefix sums, their variants, and the interview patterns they unlock.

## The Core Idea

Given an array `arr`, the prefix sum array `pre` stores the cumulative sum:

```
pre[0] = arr[0]
pre[i] = pre[i-1] + arr[i]
```

With this, any subarray sum `arr[i..j]` is computed in O(1):

```python
def build_prefix(arr):
    n = len(arr)
    pre = [0] * (n + 1)  # pre[0] = 0 for convenience
    for i in range(n):
        pre[i + 1] = pre[i] + arr[i]
    return pre

def range_sum(pre, left, right):
    return pre[right + 1] - pre[left]
```

Using `pre[0] = 0` as a sentinel simplifies the formula: sum from index `left` to `right` (inclusive) = `pre[right+1] - pre[left]`. This avoids special-casing the left boundary.

## Pattern 1: Subarray Sum Equals K

"Find the number of subarrays with sum equal to k."

Brute force: O(n²) — try every pair (i, j). With prefix sums and a hash map: O(n).

```python
def subarraySum(nums, k):
    count = 0
    prefix = 0
    seen = defaultdict(int)
    seen[0] = 1  # Empty prefix (handles subarrays starting at index 0)

    for num in nums:
        prefix += num
        # If prefix - k exists in seen, there's a subarray ending here with sum k
        count += seen[prefix - k]
        seen[prefix] += 1

    return count
```

The insight: a subarray `nums[i+1..j]` has sum `k` if `pre[j+1] - pre[i] = k`, i.e., `pre[j+1] - k = pre[i]`. So we look for previously seen prefix sums equal to `current_prefix - k`.

This pattern extends to: subarrays with sum divisible by k, longest subarray with sum ≤ k (use sorted set instead of hash map), and count of subarrays with sum in range.

## Pattern 2: Range Queries on Immutable Arrays

"Given an array, answer Q queries of the form: sum of elements from index L to R."

Without prefix sum: O(Q × N) — too slow for large Q. With prefix sum: O(N + Q).

```python
class NumArray:
    def __init__(self, nums):
        self.pre = [0] * (len(nums) + 1)
        for i, num in enumerate(nums):
            self.pre[i + 1] = self.pre[i] + num

    def sumRange(self, left, right):
        return self.pre[right + 1] - self.pre[left]
```

This is LeetCode 303 and a building block for more complex problems.

## Pattern 3: 2D Prefix Sum

Extend prefix sums to matrices for rectangle sum queries.

```python
def build_2d_prefix(matrix):
    m, n = len(matrix), len(matrix[0])
    pre = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            pre[i][j] = (matrix[i-1][j-1]
                       + pre[i-1][j]
                       + pre[i][j-1]
                       - pre[i-1][j-1])  # Inclusion-exclusion
    return pre

def rect_sum(pre, r1, c1, r2, c2):
    # Sum of rectangle from (r1, c1) to (r2, c2) inclusive
    return (pre[r2+1][c2+1]
          - pre[r1][c2+1]
          - pre[r2+1][c1]
          + pre[r1][c1])
```

The 2D version uses inclusion-exclusion: add top-left, subtract the two rectangles above and to the left, add back the top-left corner which was subtracted twice.

## Pattern 4: Difference Array (Inverse Prefix Sum)

For bulk range update problems: "Add `v` to all elements in index `[l, r]`."

Naive: O(n) per update. Difference array: O(1) per update, O(n) to finalize.

```python
def range_update(diff, l, r, val):
    diff[l] += val
    if r + 1 < len(diff):
        diff[r + 1] -= val

def finalize(diff):
    # Prefix sum of diff gives the actual values
    for i in range(1, len(diff)):
        diff[i] += diff[i - 1]
    return diff
```

Use case: applying many range updates, then reading final values. Common in scheduling problems ("for each flight, mark seats occupied from row L to R") and animation problems.

## Pattern 5: Prefix XOR, AND, OR

Prefix sums generalize to any associative operation with an inverse. XOR has a natural inverse (XOR with itself = 0):

```python
def xor_range(pre_xor, l, r):
    return pre_xor[r + 1] ^ pre_xor[l]
```

This solves: "Find XOR of all elements in range [l, r]." AND and OR don't have simple inverses, so prefix AND/OR is useful only for prefix or suffix queries, not arbitrary ranges.

## Recognizing Prefix Sum Problems

Apply prefix sums when:
- You need repeated range sum/product queries on a static array
- The problem involves "number of subarrays with property X" where property involves sums
- You need to do many range updates followed by reads (difference array)
- The problem has a 2D grid with rectangle sum queries

Mental model: **prefix sums trade O(n) preprocessing for O(1) queries**. Whenever you catch yourself writing a loop to compute a subarray sum inside another loop, ask: could a prefix array eliminate the inner loop?

## Common Interview Mistakes

**Off-by-one errors:** The 1-indexed prefix array (`pre[0] = 0`) is safer than 0-indexed. Internalize the formula: sum from `l` to `r` = `pre[r+1] - pre[l]`.

**Forgetting the hash map base case:** In the hash map variant, always initialize `seen[0] = 1`. This handles subarrays that start at index 0 (prefix sum from 0 to j equals k directly).

**Missing the difference array pattern:** When a problem has range updates (not range queries), the difference array is often the tool, not the prefix sum.

The prefix sum is one of the few techniques that genuinely shows up at every level of technical interviewing — from new grad screens to staff engineer systems thinking. Master the patterns and their variants.
