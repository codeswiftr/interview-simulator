---
title: "Sliding Window Technique: The Complete Interview Guide"
description: "Master the sliding window technique for coding interviews. Learn fixed-size and variable-size window patterns, the shrink-when-invalid approach, and 6 classic problems with Python solutions."
date: "2025-10-11"
category: "Interview Preparation"
---
# Sliding Window Technique: The Complete Interview Guide

If you have spent any time grinding LeetCode, you have almost certainly run into problems that feel impossible to solve efficiently with brute force. A nested loop solution exists, but it is O(n²) and times out. The interviewer is waiting. This is exactly where the sliding window technique comes in, and understanding it deeply will unlock a whole category of string and array problems that appear constantly in technical interviews.

## What Sliding Window Is and When to Use It

The sliding window technique is an optimization pattern that transforms a naive O(n²) nested loop into an O(n) single-pass solution by maintaining a "window" — a contiguous subarray or substring — and moving it across the input rather than restarting from scratch each time.

The key insight is that adjacent windows share most of their elements. When you slide the window one step to the right, you lose one element on the left and gain one on the right. This means you can update your running calculation incrementally rather than recomputing it from zero.

**Use sliding window when you see these signals in a problem:**
- "Find the maximum/minimum/longest/shortest subarray or substring"
- The problem involves contiguous elements
- There is a constraint on the window (size k, sum ≥ target, at most k distinct chars)
- A brute force O(n²) or O(n³) solution is obvious but too slow

## Fixed-Size Window Pattern

When the window size k is given to you directly, the pattern is straightforward: initialize the window with the first k elements, then slide it one step at a time, adding the new element on the right and removing the old element on the left.

**Problem: Maximum sum subarray of size k**

```python
def max_sum_subarray(nums: list[int], k: int) -> int:
    window_sum = sum(nums[:k])
    max_sum = window_sum
    for i in range(k, len(nums)):
        window_sum += nums[i] - nums[i - k]
        max_sum = max(max_sum, window_sum)
    return max_sum
```

Time complexity: O(n). Space complexity: O(1). The subtraction `nums[i - k]` removes the element that just left the window. This pattern applies to any fixed-size window problem: maximum average subarray, number of subarrays containing all ones after replacing at most k zeros, and similar variants.

## Variable-Size Window Pattern

Variable windows are trickier because the window size changes dynamically based on whether the current window satisfies the problem's constraint. You expand by moving the right pointer and shrink by moving the left pointer.

**Problem: Longest substring without repeating characters**

```python
def length_of_longest_substring(s: str) -> int:
    char_set = set()
    left = 0
    max_len = 0
    for right in range(len(s)):
        while s[right] in char_set:
            char_set.remove(s[left])
            left += 1
        char_set.add(s[right])
        max_len = max(max_len, right - left + 1)
    return max_len
```

**Problem: Minimum size subarray sum**

```python
def min_subarray_len(target: int, nums: list[int]) -> int:
    left = 0
    current_sum = 0
    min_len = float('inf')
    for right in range(len(nums)):
        current_sum += nums[right]
        while current_sum >= target:
            min_len = min(min_len, right - left + 1)
            current_sum -= nums[left]
            left += 1
    return 0 if min_len == float('inf') else min_len
```

## The "Shrink When Invalid" Approach

The most powerful framing for variable window problems is "shrink when invalid." Expand the right pointer freely, adding elements to your window. When the window violates the constraint (window is invalid), shrink from the left until it is valid again. This produces an amortized O(n) solution because each element enters and exits the window at most once.

**Problem: Longest substring with at most k distinct characters**

```python
def longest_substring_k_distinct(s: str, k: int) -> int:
    from collections import defaultdict
    freq = defaultdict(int)
    left = 0
    max_len = 0
    for right in range(len(s)):
        freq[s[right]] += 1
        while len(freq) > k:          # window invalid
            freq[s[left]] -= 1
            if freq[s[left]] == 0:
                del freq[s[left]]
            left += 1
        max_len = max(max_len, right - left + 1)
    return max_len
```

**Problem: Fruit into baskets** (equivalent to at most 2 distinct values):

```python
def total_fruit(fruits: list[int]) -> int:
    from collections import defaultdict
    basket = defaultdict(int)
    left = 0
    max_picked = 0
    for right in range(len(fruits)):
        basket[fruits[right]] += 1
        while len(basket) > 2:
            basket[fruits[left]] -= 1
            if basket[fruits[left]] == 0:
                del basket[fruits[left]]
            left += 1
        max_picked = max(max_picked, right - left + 1)
    return max_picked
```

**Problem: Minimum window substring** (the hardest classic):

```python
def min_window(s: str, t: str) -> str:
    from collections import Counter
    need = Counter(t)
    have = {}
    formed = 0
    required = len(need)
    left = 0
    result = ""
    min_len = float('inf')
    for right in range(len(s)):
        c = s[right]
        have[c] = have.get(c, 0) + 1
        if c in need and have[c] == need[c]:
            formed += 1
        while formed == required:
            if right - left + 1 < min_len:
                min_len = right - left + 1
                result = s[left:right + 1]
            have[s[left]] -= 1
            if s[left] in need and have[s[left]] < need[s[left]]:
                formed -= 1
            left += 1
    return result
```

## Interview Strategy and Common Mistakes

When you encounter a sliding window problem in an interview, verbalize your thought process: "This looks like a subarray constraint problem — I'm thinking sliding window. Let me define what makes my window valid and what happens when it becomes invalid."

The most common mistake is forgetting to shrink the window when it becomes invalid. Another pitfall is using a frequency map incorrectly — always decrement before checking if deletion is needed, not after.

For any variable window problem, ask yourself three questions before coding: What does my window represent? What is the validity condition? What am I tracking to efficiently check that condition? Answer those, and the code almost writes itself.

The sliding window pattern appears in roughly 10-15% of array and string problems across FAANG interviews. Combined with the two-pointer technique it shares DNA with, mastering it gives you coverage over a substantial portion of the medium-difficulty problem set.
