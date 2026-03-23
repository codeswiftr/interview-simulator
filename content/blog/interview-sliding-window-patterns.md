---
title: "Mastering Sliding Window Patterns: Fixed, Variable, Minimum, Maximum, and Deque-Based"
description: "Complete guide to all sliding window algorithm variants for interviews: fixed-size windows, variable-size windows, minimum/maximum window problems, and deque-based monotonic window techniques."
date: "2026-03-20"
category: "Algorithms"
---

# Mastering Sliding Window Patterns

Sliding window is one of the most versatile algorithmic patterns, appearing in roughly 15–20% of array/string problems at major tech companies. The pattern reduces O(n²) brute-force solutions to O(n) by maintaining a "window" of elements and updating it incrementally rather than recomputing from scratch.

## The Core Insight

For any problem that asks you to find something in a **contiguous subarray or substring**, ask yourself: "Can I move a window across the data structure instead of checking all subarrays?"

If adding one element to the right and removing one from the left can maintain the property you're tracking — sliding window applies.

## Pattern 1: Fixed-Size Window

The simplest variant. The window size `k` is given. Slide it across the array, adding the new right element and removing the old left element.

**Template:**
```python
def fixed_window(arr: list[int], k: int) -> list[int]:
    result = []
    window_sum = sum(arr[:k])
    result.append(window_sum)

    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]  # Add right, remove left
        result.append(window_sum)

    return result
```

**Classic problems:**
- Maximum sum subarray of size k
- Average of all subarrays of size k
- Count distinct elements in every window of size k (use a frequency map)

**Frequency map pattern for fixed window:**
```python
def count_distinct(arr: list[int], k: int) -> list[int]:
    freq = {}
    result = []

    for i in range(len(arr)):
        freq[arr[i]] = freq.get(arr[i], 0) + 1

        if i >= k:  # Remove element going out of window
            left = arr[i - k]
            freq[left] -= 1
            if freq[left] == 0:
                del freq[left]

        if i >= k - 1:
            result.append(len(freq))

    return result
```

## Pattern 2: Variable-Size Window (Expand/Shrink)

The window size isn't fixed — you expand right until a condition breaks, then shrink from the left until the condition is restored.

**Template:**
```python
def variable_window(arr: list[int], target: int) -> int:
    left = 0
    current = 0  # Whatever you're tracking (sum, count, etc.)
    result = 0

    for right in range(len(arr)):
        current += arr[right]  # Expand window

        while current > target:  # Condition broken — shrink
            current -= arr[left]
            left += 1

        # Window [left, right] satisfies condition
        result = max(result, right - left + 1)

    return result
```

**Key insight:** The inner `while` loop doesn't make this O(n²) — each element enters and exits the window exactly once, so the total work is O(n).

**Classic variable-window problems:**

1. **Longest substring without repeating characters:**
```python
def length_of_longest_substring(s: str) -> int:
    char_index = {}
    left = 0
    result = 0

    for right, char in enumerate(s):
        if char in char_index and char_index[char] >= left:
            left = char_index[char] + 1
        char_index[char] = right
        result = max(result, right - left + 1)

    return result
```

2. **Minimum size subarray with sum ≥ target:**
```python
def min_subarray_len(target: int, nums: list[int]) -> int:
    left = 0
    current_sum = 0
    result = float('inf')

    for right in range(len(nums)):
        current_sum += nums[right]
        while current_sum >= target:
            result = min(result, right - left + 1)
            current_sum -= nums[left]
            left += 1

    return result if result != float('inf') else 0
```

## Pattern 3: Window with Constraint (At Most K)

A powerful meta-pattern: problems asking for subarrays with **exactly K** distinct elements can be solved as:

`exactly(K) = atMost(K) - atMost(K-1)`

```python
def subarrays_with_k_distinct(nums: list[int], k: int) -> int:
    def at_most(k):
        count = {}
        left = 0
        result = 0
        for right in range(len(nums)):
            count[nums[right]] = count.get(nums[right], 0) + 1
            while len(count) > k:
                count[nums[left]] -= 1
                if count[nums[left]] == 0:
                    del count[nums[left]]
                left += 1
            result += right - left + 1  # All subarrays ending at right
        return result

    return at_most(k) - at_most(k - 1)
```

## Pattern 4: Minimum Window Substring

The canonical "minimum window" problem: find the smallest window in `s` containing all characters of `t`.

```python
def min_window(s: str, t: str) -> str:
    if not t or not s:
        return ""

    need = {}
    for c in t:
        need[c] = need.get(c, 0) + 1

    missing = len(t)
    left = 0
    best_left, best_right = 0, float('inf')

    for right, char in enumerate(s):
        if need.get(char, 0) > 0:
            missing -= 1
        need[char] = need.get(char, 0) - 1

        if missing == 0:  # Valid window found — shrink from left
            while need.get(s[left], 0) < 0:
                need[s[left]] += 1
                left += 1

            if right - left < best_right - best_left:
                best_left, best_right = left, right

            need[s[left]] += 1
            missing += 1
            left += 1

    return s[best_left:best_right + 1] if best_right != float('inf') else ""
```

**Key trick:** Track `missing` (how many characters still needed) rather than checking the entire frequency map each iteration.

## Pattern 5: Deque-Based Sliding Window Maximum

Finding the maximum in every window of size k naively is O(nk). Using a **monotonic deque**, it's O(n).

**Monotonic deque property:** The deque stores indices in decreasing order of their values. The front always holds the index of the current window's maximum.

```python
from collections import deque

def max_sliding_window(nums: list[int], k: int) -> list[int]:
    dq = deque()  # Stores indices, decreasing order of values
    result = []

    for i in range(len(nums)):
        # Remove indices outside window
        while dq and dq[0] < i - k + 1:
            dq.popleft()

        # Remove smaller elements from back (they can never be maximum)
        while dq and nums[dq[-1]] < nums[i]:
            dq.pop()

        dq.append(i)

        if i >= k - 1:
            result.append(nums[dq[0]])  # Front is always the max

    return result
```

The same technique works for **sliding window minimum** — reverse the comparison.

## Pattern 6: Longest Subarray with Bounded Max-Min

When the constraint is `max(window) - min(window) <= limit`, maintain two deques:

```python
from collections import deque

def longest_subarray(nums: list[int], limit: int) -> int:
    max_dq = deque()  # Decreasing
    min_dq = deque()  # Increasing
    left = 0
    result = 0

    for right in range(len(nums)):
        while max_dq and nums[max_dq[-1]] <= nums[right]:
            max_dq.pop()
        while min_dq and nums[min_dq[-1]] >= nums[right]:
            min_dq.pop()

        max_dq.append(right)
        min_dq.append(right)

        while nums[max_dq[0]] - nums[min_dq[0]] > limit:
            left += 1
            if max_dq[0] < left:
                max_dq.popleft()
            if min_dq[0] < left:
                min_dq.popleft()

        result = max(result, right - left + 1)

    return result
```

## Problem-to-Pattern Recognition

| Problem clue | Pattern |
|-------------|---------|
| "subarray of size k" | Fixed window |
| "longest subarray where..." | Variable window (expand/shrink) |
| "minimum window containing..." | Minimum window substring |
| "maximum in every window" | Monotonic deque |
| "exactly K distinct" | atMost(K) − atMost(K-1) |

## Interview Tips

1. **State the invariant clearly.** Before coding, articulate what property your window maintains at every step.
2. **Justify O(n) complexity.** Interviewers will ask — explain that each element enters and exits the window once.
3. **Handle edge cases first.** Empty array, k larger than array, all-same elements.
4. **Prefer `while` over `if` when shrinking.** A `while` loop correctly handles multiple consecutive violations; `if` doesn't.

Sliding window mastery comes from recognizing which pattern applies, not from memorizing code. Practice identifying the window invariant before reaching for a template.
