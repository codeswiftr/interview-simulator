---
title: "Advanced String Interview Problems: KMP, Rabin-Karp, and Sliding Window Patterns"
description: "Master advanced string algorithms for technical interviews — the KMP pattern matching algorithm, Rabin-Karp rolling hash, sliding window for substring problems, and the key invariants that make these problems tractable."
date: "2026-03-20"
category: "Algorithms"
---

# Advanced String Interview Problems: KMP, Rabin-Karp, and Sliding Window Patterns

String problems occupy a special place in technical interviews. They're approachable enough to appear at every level, yet the advanced variants test genuine algorithmic depth — knowledge of string-specific data structures, clever hash techniques, and the sliding window invariant.

This guide covers the patterns that separate adequate string problem-solving from truly strong performance.

## Sliding Window: The Universal Substring Pattern

The sliding window technique solves a family of substring problems: find the shortest/longest substring satisfying some condition. The key invariant is maintaining a window `[left, right]` where the window is always valid (or always invalid), and expanding/contracting it as you scan.

### Minimum Window Substring (LeetCode 76)

Find the smallest window in `s` that contains all characters of `t`.

```python
def minWindow(s, t):
    if not t or not s:
        return ""
    
    need = Counter(t)
    have = {}
    formed = 0  # Number of chars with required frequency
    required = len(need)  # Number of unique chars needed
    
    left = 0
    result = float('inf'), None, None
    
    for right, char in enumerate(s):
        have[char] = have.get(char, 0) + 1
        if char in need and have[char] == need[char]:
            formed += 1
        
        # Contract window while valid
        while left <= right and formed == required:
            if right - left + 1 < result[0]:
                result = (right - left + 1, left, right)
            
            left_char = s[left]
            have[left_char] -= 1
            if left_char in need and have[left_char] < need[left_char]:
                formed -= 1
            left += 1
    
    return "" if result[0] == float('inf') else s[result[1]:result[2]+1]
```

The `formed` counter is the key optimization — it tracks when the window is valid in O(1) rather than checking every character.

### Longest Substring Without Repeating Characters

```python
def lengthOfLongestSubstring(s):
    seen = {}
    left = 0
    max_len = 0
    
    for right, char in enumerate(s):
        if char in seen and seen[char] >= left:
            left = seen[char] + 1
        seen[char] = right
        max_len = max(max_len, right - left + 1)
    
    return max_len
```

Notice the `seen[char] >= left` check — when a character was seen before the current window's left boundary, it doesn't affect the window.

## KMP: O(n) Pattern Matching

The Knuth-Morris-Pratt algorithm finds all occurrences of a pattern in a text in O(n + m) time, where n is text length and m is pattern length. The naive approach is O(n·m).

The insight: when a mismatch occurs, we don't need to restart from scratch. The "failure function" (also called partial match table or LPS — Longest Proper Prefix which is also Suffix) tells us where to resume.

### Building the Failure Function

```python
def build_lps(pattern):
    m = len(pattern)
    lps = [0] * m
    length = 0  # Length of previous longest prefix suffix
    i = 1
    
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]  # Key: don't increment i
            else:
                lps[i] = 0
                i += 1
    return lps

def kmp_search(text, pattern):
    n, m = len(text), len(pattern)
    lps = build_lps(pattern)
    
    results = []
    i = j = 0  # i for text, j for pattern
    
    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
        
        if j == m:
            results.append(i - j)
            j = lps[j - 1]  # Continue searching
        elif i < n and text[i] != pattern[j]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    
    return results
```

**When to reach for KMP in interviews**: Repeated pattern matching, finding all occurrences, or when the interviewer specifically asks about linear-time string matching. For most LeetCode-style problems, Python's `in` operator or `str.find()` (which uses optimized C code) is fine, but explaining KMP shows genuine CS depth.

## Rabin-Karp: Rolling Hash

Rabin-Karp uses hashing to find pattern matches in O(n + m) average time. Its main advantage over KMP is elegantly generalizing to *multiple pattern search* and to 2D pattern matching (finding a pattern matrix within a larger matrix).

```python
def rabin_karp(text, pattern):
    n, m = len(text), len(pattern)
    if m > n:
        return []
    
    BASE = 31
    MOD = 10**9 + 7
    
    def char_val(c):
        return ord(c) - ord('a') + 1
    
    # Compute pattern hash and initial window hash
    pattern_hash = 0
    window_hash = 0
    power = 1  # BASE^(m-1)
    
    for i in range(m):
        pattern_hash = (pattern_hash * BASE + char_val(pattern[i])) % MOD
        window_hash = (window_hash * BASE + char_val(text[i])) % MOD
        if i < m - 1:
            power = (power * BASE) % MOD
    
    results = []
    for i in range(n - m + 1):
        if window_hash == pattern_hash:
            if text[i:i+m] == pattern:  # Verify to handle hash collisions
                results.append(i)
        
        if i < n - m:
            # Roll the hash: remove leftmost, add rightmost
            window_hash = (window_hash - char_val(text[i]) * power) % MOD
            window_hash = (window_hash * BASE + char_val(text[i+m])) % MOD
            window_hash = (window_hash + MOD) % MOD  # Handle negative values
    
    return results
```

The rolling hash update is the core idea: instead of recomputing the hash for each window from scratch, slide the hash window in O(1) by removing the contribution of the leftmost character and adding the rightmost.

## Z-Algorithm: Linear Prefix Matching

Less commonly asked but elegant: the Z-array `Z[i]` stores the length of the longest substring starting at `s[i]` that is also a prefix of `s`. Useful for finding all occurrences and solving some KMP-equivalent problems with simpler code.

## Practical Interview Tips

**On sliding window problems**: Always be explicit about the window invariant — what property must hold for the window to be "valid"? Stating this clearly shows algorithmic maturity.

**On KMP**: Know it conceptually and be able to explain why the failure function works. Coding it from memory under pressure is hard; the conceptual understanding matters more.

**On Rabin-Karp**: The rolling hash trick appears beyond strings — it shows up in hashing for dynamic programming and plagiarism detection. Understand the collision handling requirement.

When you encounter a string problem, the first question to ask is: does this look like a fixed-size window, a variable-size window, or a pattern-matching problem? That classification usually points directly to the right algorithm.
