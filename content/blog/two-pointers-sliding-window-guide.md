---
title: "Two Pointers and Sliding Window: Interview Pattern Mastery"
description: "Complete guide to two-pointer and sliding window interview patterns — when to use each variant, the template code, and how to solve the most common medium and hard problems."
date: "2026-03-20"
category: "Algorithms"
---

# Two Pointers and Sliding Window: Interview Pattern Mastery

Two pointers and sliding window are among the most frequently tested patterns in algorithm interviews. They appear in LeetCode mediums and hards at companies from Google to early-stage startups. Both patterns exploit the structure of sorted arrays or contiguous subarrays to reduce O(n²) brute-force solutions to O(n). This guide teaches you to recognize which variant applies, the template code for each, and the reasoning to explain your approach in an interview.

## Two Pointers: Opposite Ends

**When to use**: sorted array, pair-sum problems, partitioning, palindrome checks. You need to find a pair (or shrink a search space) from both ends simultaneously.

**Template**:

```python
def two_sum_sorted(nums, target):
    left, right = 0, len(nums) - 1
    while left < right:
        s = nums[left] + nums[right]
        if s == target:
            return [left, right]
        elif s < target:
            left += 1
        else:
            right -= 1
    return []
```

The invariant: everything to the left of `left` is too small as a first element; everything to the right of `right` is too large as a second element. Each step eliminates at least one candidate, so the loop terminates in O(n).

**Container With Most Water** is the canonical hard application: place two pointers at the ends, compute the area, and advance the pointer pointing to the shorter bar. The key insight — moving the taller bar can never increase the area (the width shrinks and the height is still bounded by the shorter bar), so advancing the shorter bar is the only move that could possibly find a larger area.

**3Sum** uses the opposite-ends pattern inside a loop: fix one element, then run two pointers on the remainder. Skipping duplicates requires advancing past equal values after each successful pair to avoid duplicate triplets.

## Two Pointers: Same Direction (Fast-Slow)

**When to use**: linked list cycle detection, finding the middle of a list, removing duplicates in-place, detecting happy numbers.

**Template (cycle detection)**:

```python
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False
```

Floyd's algorithm: a slow pointer advances one step; a fast pointer advances two. If a cycle exists, the fast pointer will lap the slow pointer. The meeting point has a well-known mathematical property that also allows finding the cycle start.

For in-place duplicate removal from a sorted array, `slow` tracks the write position and `fast` scans ahead:

```python
def remove_duplicates(nums):
    slow = 0
    for fast in range(1, len(nums)):
        if nums[fast] != nums[slow]:
            slow += 1
            nums[slow] = nums[fast]
    return slow + 1
```

## Sliding Window: Fixed Size

**When to use**: maximum/minimum/sum of a subarray of fixed length k.

**Template**:

```python
def max_sum_k(nums, k):
    window_sum = sum(nums[:k])
    best = window_sum
    for i in range(k, len(nums)):
        window_sum += nums[i] - nums[i - k]
        best = max(best, window_sum)
    return best
```

The trick is computing the sum incrementally: add the new element entering the window, subtract the element leaving. This keeps each step O(1) instead of recomputing the sum from scratch.

Fixed-size windows also apply to string problems: check if any window of size k is an anagram of a pattern by maintaining a character frequency count and comparing counts rather than sorting.

## Sliding Window: Variable Size

**When to use**: longest/shortest subarray satisfying a condition, minimum window substring, problems where the window boundary is determined by a constraint rather than a fixed k.

**Template (expand right, shrink left)**:

```python
def length_of_longest_substring_no_repeat(s):
    seen = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        if ch in seen and seen[ch] >= left:
            left = seen[ch] + 1
        seen[ch] = right
        best = max(best, right - left + 1)
    return best
```

The invariant: `[left, right]` always contains a valid window (no repeated characters). When the new character would violate the constraint, advance `left` until the window is valid again.

**Minimum Window Substring** is the hardest common variant. Maintain a frequency map of characters needed, a count of how many distinct characters are fully satisfied, and shrink the window from the left whenever all characters are covered — recording the minimum each time:

```python
def min_window(s, t):
    from collections import Counter
    need = Counter(t)
    have, total = 0, len(need)
    window = {}
    left = 0
    res = ""
    for right, ch in enumerate(s):
        window[ch] = window.get(ch, 0) + 1
        if ch in need and window[ch] == need[ch]:
            have += 1
        while have == total:
            if not res or right - left + 1 < len(res):
                res = s[left:right+1]
            window[s[left]] -= 1
            if s[left] in need and window[s[left]] < need[s[left]]:
                have -= 1
            left += 1
    return res
```

## Recognizing Which Variant Applies

Ask three questions when you see an array or string problem:

1. Is the array sorted or can it be? → Consider opposite-ends two pointers.
2. Does the problem involve contiguous subarrays or substrings? → Consider sliding window.
3. Fixed-length window, or does the valid window size vary based on a condition? → Fixed or variable sliding window.
4. Linked list, or detecting a pattern with two speeds? → Fast-slow pointers.

Problems that do NOT fit these patterns: non-contiguous subsequences (use DP), problems requiring backtracking over all possibilities, problems with non-linear structure. Recognizing when the pattern does not apply is as important as recognizing when it does.

## Time and Space Analysis

All variants above run in O(n) time. The two-pointer patterns use O(1) extra space (or O(n) for hash maps in sliding window). Compare this to the brute force: O(n²) for all pair or subarray enumeration problems. When explaining your solution in an interview, state the brute force first, identify why it is slow (redundant recomputation), then explain how the pointer invariant eliminates recomputation.

Practice the templates until the code is automatic. The interview time should go to choosing the right pattern, explaining the invariant, and handling edge cases — not remembering syntax.
