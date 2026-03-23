---
title: "Kadane's Algorithm and Its Variants: Maximum Subarray Problems Explained"
description: "A thorough guide to Kadane's algorithm — the linear-time maximum subarray solution — and its essential variants: circular array, maximum product subarray, and the buy-and-sell stock family."
date: "2026-03-20"
category: "Algorithms"
---

Kadane's algorithm is one of those elegant solutions that feels almost too simple when you first see it, and then you realize it's the building block for an entire family of problems. The core insight — that extending a subarray is only worthwhile if the current running sum is positive — recurs in circular variants, product variants, and the ubiquitous stock trading family.

## The Classic Problem

Given an integer array (which may contain negative numbers), find the contiguous subarray with the maximum sum, and return that sum.

Example: `[-2, 1, -3, 4, -1, 2, 1, -5, 4]`
Answer: `[4, -1, 2, 1]` with sum 6.

**Brute force** is O(n²): try every (start, end) pair and compute the sum. This is too slow for large inputs.

**Kadane's insight:** At each position i, the maximum subarray ending at i is either:
- Just `arr[i]` (start fresh)
- `arr[i]` plus the maximum subarray ending at `i-1`

Which is larger? If the running sum so far is positive, extend it. If it's negative or zero, it can only hurt us — start fresh.

```python
def max_subarray(nums: list[int]) -> int:
    max_sum = nums[0]
    current_sum = nums[0]
    for i in range(1, len(nums)):
        current_sum = max(nums[i], current_sum + nums[i])
        max_sum = max(max_sum, current_sum)
    return max_sum
```

**Complexity:** O(n) time, O(1) space. This is optimal — you must read every element at least once.

**Key interview consideration:** What if all elements are negative? The algorithm correctly returns the largest (least negative) single element, because `nums[i]` is always an option at each step. Make sure you initialize with `nums[0]`, not 0, to handle this case.

## Tracking the Subarray Indices

Interviewers often follow up: "Return the actual subarray, not just the sum." Track start, end, and a temporary start index:

```python
def max_subarray_with_indices(nums: list[int]):
    max_sum = nums[0]
    current_sum = nums[0]
    start = end = 0
    temp_start = 0
    for i in range(1, len(nums)):
        if current_sum + nums[i] < nums[i]:
            current_sum = nums[i]
            temp_start = i
        else:
            current_sum += nums[i]
        if current_sum > max_sum:
            max_sum = current_sum
            start = temp_start
            end = i
    return nums[start:end+1], max_sum
```

## Variant 1: Maximum Sum Circular Subarray

Now the array is circular — the subarray can wrap around from the end back to the beginning. Example: `[5, -3, 5]` has maximum circular subarray `[5, 5]` (wrapping around) with sum 10.

**The insight:** A circular subarray is either:
1. A non-wrapping subarray (solve with standard Kadane)
2. A wrapping subarray, which equals `total_sum - minimum_non-wrapping_subarray`

To find the minimum subarray, negate all elements and apply Kadane (which finds the maximum of the negated array, i.e., the minimum of the original).

```python
def max_circular_subarray(nums: list[int]) -> int:
    total = sum(nums)

    # Case 1: standard Kadane for non-wrapping
    max_sum = cur_max = nums[0]
    for n in nums[1:]:
        cur_max = max(n, cur_max + n)
        max_sum = max(max_sum, cur_max)

    # Case 2: wrapping = total - min subarray
    min_sum = cur_min = nums[0]
    for n in nums[1:]:
        cur_min = min(n, cur_min + n)
        min_sum = min(min_sum, cur_min)

    # Edge case: if all numbers are negative, circular result would be 0
    # (empty wrapping subarray), but we must return at least one element
    if max_sum < 0:
        return max_sum
    return max(max_sum, total - min_sum)
```

The all-negative edge case is subtle: if all elements are negative, `total - min_sum` would be 0 (corresponding to an empty array), but we must return the least-negative element. Return `max_sum` in that case.

## Variant 2: Maximum Product Subarray

Change the objective from sum to product. The product variant is harder because:
- A negative number can become a maximum if multiplied by another negative
- Zero resets both running max and min

The solution tracks both the running maximum *and* running minimum product at each position, because the minimum (most negative) value can flip to become the maximum when multiplied by a negative element.

```python
def max_product_subarray(nums: list[int]) -> int:
    max_prod = min_prod = result = nums[0]
    for n in nums[1:]:
        candidates = (n, max_prod * n, min_prod * n)
        max_prod = max(candidates)
        min_prod = min(candidates)
        result = max(result, max_prod)
    return result
```

Note: when you compute `max_prod` and `min_prod` for the next step, they must both use the *previous* values, so compute all three candidates first.

## Variant 3: Stock Buy and Sell (Single Transaction)

"Given an array of prices, find the maximum profit from a single buy-sell transaction."

This is Kadane in disguise. Transform the problem: let `diff[i] = prices[i] - prices[i-1]`. The maximum profit from one transaction is the maximum subarray sum of the `diff` array.

Equivalently, track the minimum price seen so far and the maximum profit seen so far:

```python
def max_profit(prices: list[int]) -> int:
    min_price = float('inf')
    max_profit = 0
    for price in prices:
        min_price = min(min_price, price)
        max_profit = max(max_profit, price - min_price)
    return max_profit
```

This is identical in structure to Kadane — at each step, you're deciding whether to "start fresh" (reset min_price) or "extend" (compute profit from current min).

## Variant 4: Stock Buy and Sell (Multiple Transactions)

"As many transactions as you like, but can only hold one share at a time." The greedy solution: take every positive increment. Sum all `max(0, prices[i] - prices[i-1])` for every adjacent pair. This is because in multiple-transaction mode, you capture every upward movement.

## Variant 5: Stock with Cooldown

After selling, you must wait one day before buying again. This requires a state machine DP with three states: holding, sold (in cooldown), and idle. Transitions:

- `holding[i] = max(holding[i-1], idle[i-1] - prices[i])`
- `sold[i] = holding[i-1] + prices[i]`
- `idle[i] = max(idle[i-1], sold[i-1])`

## Interview Patterns and Common Mistakes

**Starting current_sum at 0:** Many candidates initialize `current_sum = 0`, which fails when all elements are negative. Always initialize both `current_sum` and `max_sum` to `nums[0]`.

**Missing the circular edge case:** The all-negative case in circular subarray is a reliable differentiator. Candidates who reason through it explicitly demonstrate careful thinking.

**Product variant forgetting to use old values:** In the product variant, computing `max_prod` first and then using it to compute `min_prod` introduces a bug. Compute all candidates from the previous step's values first.

Kadane's algorithm demonstrates that dynamic programming does not always require a full table. Many 1D DP problems compress to constant space because you only need the immediately preceding state. When you see "maximum/minimum contiguous subarray" in any form — sum, product, circular — Kadane is your starting point.
