---
title: "Suffix Arrays & String Matching: Interview Deep Dive"
date: 2026-03-21
excerpt: "Master suffix arrays and trees for complex string problems—from longest repeated substring to pattern matching in linear time."
tags: [algorithms, strings, suffix-arrays, pattern-matching, interview-prep]
---

# Suffix Arrays & String Matching: Interview Deep Dive

String problems in interviews often go beyond simple pattern matching. When asked about longest repeated substrings, suffix arrays and suffix trees are your secret weapons.

## What is a Suffix Array?

A suffix array is a sorted array of all suffixes of a string. Instead of storing the actual suffixes, we store their starting indices.

For string "banana":
```
Suffixes:          Sorted:           Suffix Array:
0: banana          5: a              [5, 3, 1, 0, 4, 2]
1: anana    →      3: ana
2: nana            1: anana
3: ana             0: banana
4: na              4: na
5: a               2: nana
```

## Building a Suffix Array

The naive O(n² log n) approach sorts suffixes directly. Interview solutions often use the O(n log² n) prefix doubling method:

```python
def build_suffix_array(s):
    n = len(s)
    suffixes = [(s[i:], i) for i in range(n)]
    suffixes.sort()
    return [idx for _, idx in suffixes]
```

For interview-worthy O(n log n), use the prefix doubling technique with rank tuples.

## Longest Common Prefix Array (LCP)

The LCP array stores the length of the longest common prefix between consecutive suffixes in the suffix array. It's crucial for many applications.

```python
def build_lcp(s, sa):
    n = len(s)
    rank = [0] * n
    for i in range(n):
        rank[sa[i]] = i
    
    lcp = [0] * (n - 1)
    h = 0
    for i in range(n):
        if rank[i] > 0:
            j = sa[rank[i] - 1]
            while i + h < n and j + h < n and s[i + h] == s[j + h]:
                h += 1
            lcp[rank[i] - 1] = h
            if h > 0:
                h -= 1
    return lcp
```

## Key Applications

### Longest Repeated Substring

The longest repeated substring has length equal to the maximum value in the LCP array.

```python
def longest_repeated_substring(s):
    sa = build_suffix_array(s)
    lcp = build_lcp(s, sa)
    max_len = max(lcp) if lcp else 0
    idx = lcp.index(max_len) if max_len > 0 else 0
    return s[sa[idx]:sa[idx] + max_len]
```

### Count Occurrences of a Pattern

Binary search on the suffix array to find the range of suffixes starting with the pattern:

```python
def count_occurrences(text, pattern):
    sa = build_suffix_array(text)
    n = len(text)
    
    # Find leftmost
    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi) // 2
        if text[sa[mid]:] < pattern:
            lo = mid + 1
        else:
            hi = mid
    
    left = lo
    pattern_len = len(pattern)
    
    # Find rightmost
    hi = n
    while lo < hi:
        mid = (lo + hi) // 2
        if text[sa[mid]:sa[mid] + pattern_len] <= pattern:
            lo = mid + 1
        else:
            hi = mid
    
    return lo - left
```

## Interview Tips

1. **Clarify the alphabet.** Standard ASCII? Unicode? This affects radix sort optimizations.

2. **Know the trade-offs.** Suffix trees are O(n) to build but harder to implement. Suffix arrays are simpler and often sufficient.

3. **Common follow-ups:** "Find the longest substring appearing at least k times" (use LCP with sliding window), "Find all distinct substrings" (n*(n+1)/2 - sum(LCP)).

## Time Complexity

- Suffix Array: O(n log n) with prefix doubling
- LCP Array: O(n) with Kasai's algorithm
- Pattern Search: O(m log n) where m is pattern length
