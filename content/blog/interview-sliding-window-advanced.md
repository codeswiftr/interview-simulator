---
title: "Advanced Sliding Window Patterns: Variable Window, Character Frequency, and Minimum Window Substring"
description: "Deep-dive into sliding window interview problems — fixed window, variable window with shrinkable right/left pointers, character frequency maps, and the patterns for minimum window substring variants."
date: "2026-03-20"
category: "Algorithms"
---

# Advanced Sliding Window Patterns: Variable Window, Character Frequency, and Minimum Window Substring

Sliding window is one of the most productive patterns to master for coding interviews. It transforms O(n²) brute-force solutions into O(n) linear time. The challenge isn't the basic pattern — it's the variations that trip up candidates: variable-size windows, character frequency constraints, and knowing when shrinking is triggered.

## The Core Mental Model

A sliding window maintains a contiguous subarray (or substring) satisfying some constraint, expanding or contracting as it moves through the array.

**Fixed window**: Size is predetermined. Slide right, maintaining exactly k elements.

**Variable window**: Size adjusts based on whether the current window satisfies the constraint. The window grows by advancing the right pointer; it shrinks by advancing the left pointer.

**The invariant**: At every step, your window represents the current best candidate (or the constraint-satisfying state). If the constraint is violated, shrink until it's restored.

## Fixed Window Pattern

Simple application: "Maximum sum of k consecutive elements."

```python
def max_subarray_sum(arr: list[int], k: int) -> int:
    window_sum = sum(arr[:k])
    max_sum = window_sum
    
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]  # Add new, remove old
        max_sum = max(max_sum, window_sum)
    
    return max_sum
```

Time: O(n). Space: O(1). The key operation: `window_sum += arr[i] - arr[i-k]`.

## Variable Window: Two Triggers

Variable windows have two pointer movements:
1. **Expand right** (every iteration): Include the next element
2. **Shrink left** (when constraint violated): Restore the constraint

```python
def longest_subarray_with_sum_k(arr: list[int], k: int) -> int:
    left = 0
    current_sum = 0
    max_len = 0
    
    for right in range(len(arr)):
        current_sum += arr[right]  # Expand
        
        while current_sum > k:     # Shrink until valid
            current_sum -= arr[left]
            left += 1
        
        max_len = max(max_len, right - left + 1)
    
    return max_len
```

**Critical insight**: The while loop condition is the constraint violation. The invariant: when we update `max_len`, the window is valid. When we shrink, we're restoring validity.

## Character Frequency Windows

Many string problems involve character frequency constraints. The sliding window tracks a character frequency map alongside the window.

**Longest substring with at most k distinct characters**:

```python
def longest_k_distinct(s: str, k: int) -> int:
    from collections import defaultdict
    char_count = defaultdict(int)
    left = 0
    max_len = 0
    
    for right in range(len(s)):
        char_count[s[right]] += 1  # Add to window
        
        while len(char_count) > k:  # Too many distinct chars
            char_count[s[left]] -= 1
            if char_count[s[left]] == 0:
                del char_count[s[left]]
            left += 1
        
        max_len = max(max_len, right - left + 1)
    
    return max_len
```

The frequency map doubles as the distinct character counter (via `len(char_count)`). When we remove a character and its count hits zero, we delete it from the map — this correctly decrements the distinct count.

## Minimum Window Substring: The Hardest Variant

LeetCode 76 is the hardest common sliding window problem. "Given strings s and t, find the minimum window in s containing all characters of t."

```python
def min_window(s: str, t: str) -> str:
    from collections import Counter
    need = Counter(t)  # Required character frequencies
    have = {}          # Current window frequencies
    
    formed = 0         # How many chars satisfy their required frequency
    required = len(need)  # How many chars need to be satisfied
    
    left = 0
    min_len = float('inf')
    result = ""
    
    for right in range(len(s)):
        char = s[right]
        have[char] = have.get(char, 0) + 1
        
        # Check if this char now satisfies its requirement
        if char in need and have[char] == need[char]:
            formed += 1
        
        # Try to shrink window while all chars are satisfied
        while formed == required:
            window_len = right - left + 1
            if window_len < min_len:
                min_len = window_len
                result = s[left:right+1]
            
            # Remove left char from window
            left_char = s[left]
            have[left_char] -= 1
            if left_char in need and have[left_char] < need[left_char]:
                formed -= 1  # Lost a satisfied requirement
            left += 1
    
    return result
```

**The key concepts here**:
- `formed` tracks how many required characters have their count satisfied (not just present — at least as many as needed)
- When `formed == required`, every required character is in the window in sufficient quantity — this is when we record and try to shrink
- Shrinking continues while all requirements are met, optimizing the window size

**Time complexity**: O(|s| + |t|). Each character is added and removed at most once.

## Sliding Window with Frequency + Anagram Detection

"Find all anagrams of p in s" — classic interview problem:

```python
def find_anagrams(s: str, p: str) -> list[int]:
    from collections import Counter
    p_count = Counter(p)
    window = Counter(s[:len(p)])
    result = []
    
    if window == p_count:
        result.append(0)
    
    for i in range(len(p), len(s)):
        # Add new character
        window[s[i]] += 1
        # Remove outgoing character
        old = s[i - len(p)]
        window[old] -= 1
        if window[old] == 0:
            del window[old]
        
        if window == p_count:
            result.append(i - len(p) + 1)
    
    return result
```

**Counter equality** comparison works here because Python's Counter handles zero-count keys consistently when we delete zeros.

**Performance optimization**: Instead of comparing full Counter objects (O(k) per comparison), track a `matches` counter that increments when a character's count becomes equal to the target and decrements when it falls away. This reduces comparison to O(1).

## Pattern Recognition Guide

| Problem Type | Trigger to Shrink | Window State |
|-------------|-------------------|--------------|
| Max length with sum ≤ k | `sum > k` | Running sum |
| Max length with ≤ k distinct chars | `distinct > k` | Frequency map |
| Minimum window containing t | Shrink while all requirements met | Frequency + `formed` counter |
| Fixed window max/min | Always after `i >= k` | Single value |
| Longest substring no repeat | `count[char] > 1` | Set or frequency map |

**The shrink condition is always the violation of the constraint you're tracking.** Identify what you're tracking, identify when it's violated, and write the while loop around that.

Sliding window problems are among the highest-yield patterns to master — they appear frequently and have recognizable structure that makes them solvable once you've internalized the template.
