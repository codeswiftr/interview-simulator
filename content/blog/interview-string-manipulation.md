---
title: "String Manipulation Patterns for Coding Interviews"
description: "Master string interview problems: anagram detection, palindrome checking, pattern matching (KMP, Rabin-Karp), string compression, encoding/decoding, and regular expression matching patterns."
date: "2026-03-20"
category: "Algorithm Guides"
---

# String Manipulation Patterns for Coding Interviews

String problems are among the most frequently asked in technical interviews precisely because they require a specific combination of pattern recognition, algorithmic thinking, and attention to edge cases. This guide covers the core patterns with implementations you can adapt immediately.

## Character Frequency: The Foundation of Anagram Problems

The majority of anagram problems reduce to comparing character frequencies. Internalize this pattern:

```python
from collections import Counter

def isAnagram(s, t):
    return Counter(s) == Counter(t)

# Space-optimized (O(1) for lowercase ASCII)
def isAnagram(s, t):
    if len(s) != len(t):
        return False
    freq = [0] * 26
    for c in s:
        freq[ord(c) - ord('a')] += 1
    for c in t:
        freq[ord(c) - ord('a')] -= 1
        if freq[ord(c) - ord('a')] < 0:
            return False
    return True
```

**Group Anagrams (LC 49)**: Sort each string to use as a key, or use a tuple of character counts:

```python
from collections import defaultdict

def groupAnagrams(strs):
    groups = defaultdict(list)
    for s in strs:
        key = tuple(sorted(s))  # or: tuple(Counter(s).get(c, 0) for c in 'abcdefghijklmnopqrstuvwxyz')
        groups[key].append(s)
    return list(groups.values())
```

## Palindrome Patterns

**Two-pointer palindrome check** (O(n) time, O(1) space):

```python
def isPalindrome(s):
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True
```

**Longest Palindromic Substring (LC 5)**: Expand around each center. There are 2n-1 centers (including between characters):

```python
def longestPalindrome(s):
    def expand(left, right):
        while left >= 0 and right < len(s) and s[left] == s[right]:
            left -= 1
            right += 1
        return s[left+1:right]

    best = ""
    for i in range(len(s)):
        odd = expand(i, i)
        even = expand(i, i+1)
        if len(odd) > len(best): best = odd
        if len(even) > len(best): best = even
    return best
```

**Manacher's Algorithm**: O(n) palindrome detection using symmetry to skip recomputation. Rarely required in interviews but impressive if you can explain it. The core insight: use previously computed palindrome radii to avoid redundant expansion.

**Valid Palindrome II (LC 680)**: Can you remove at most one character to make a palindrome?

```python
def validPalindrome(s):
    def isPalin(left, right):
        while left < right:
            if s[left] != s[right]:
                return False
            left += 1; right -= 1
        return True

    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return isPalin(left+1, right) or isPalin(left, right-1)
        left += 1; right -= 1
    return True
```

## Pattern Matching

### Knuth-Morris-Pratt (KMP)

KMP finds all occurrences of pattern `p` in text `t` in O(n+m) time by precomputing a failure function that avoids re-examining characters after a mismatch:

```python
def kmp_search(text, pattern):
    # Build failure function (LPS array)
    m = len(pattern)
    lps = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and pattern[i] != pattern[j]:
            j = lps[j-1]
        if pattern[i] == pattern[j]:
            j += 1
        lps[i] = j

    # Search
    j = 0
    matches = []
    for i in range(len(text)):
        while j > 0 and text[i] != pattern[j]:
            j = lps[j-1]
        if text[i] == pattern[j]:
            j += 1
        if j == m:
            matches.append(i - m + 1)
            j = lps[j-1]
    return matches
```

**When to mention KMP**: When asked for O(n) string matching, or when `str.find()` is explicitly disallowed. In most interviews, the naive O(nm) approach or Python's built-in methods are acceptable — but demonstrating KMP knowledge for a senior position signals genuine CS depth.

### Rabin-Karp

Rolling hash approach: compute hash of pattern, then slide a window over text computing the hash in O(1) per step:

```python
def rabin_karp(text, pattern):
    n, m = len(text), len(pattern)
    if m > n: return -1

    base, mod = 31, 10**9 + 7
    power = pow(base, m-1, mod)

    def hash_str(s):
        h = 0
        for c in s:
            h = (h * base + (ord(c) - ord('a') + 1)) % mod
        return h

    ph = hash_str(pattern)
    th = hash_str(text[:m])

    if th == ph and text[:m] == pattern:
        return 0

    for i in range(1, n - m + 1):
        th = (th - (ord(text[i-1]) - ord('a') + 1) * power) % mod
        th = (th * base + (ord(text[i+m-1]) - ord('a') + 1)) % mod
        if th == ph and text[i:i+m] == pattern:
            return i

    return -1
```

Rabin-Karp excels at **multi-pattern search**: compute hashes of all patterns, store in a set, and check each window hash against the set in O(1).

## String Compression and Encoding

**Run-length encoding (LC 443)**:

```python
def compress(chars):
    write = 0
    i = 0
    while i < len(chars):
        char = chars[i]
        count = 0
        while i < len(chars) and chars[i] == char:
            i += 1
            count += 1
        chars[write] = char
        write += 1
        if count > 1:
            for c in str(count):
                chars[write] = c
                write += 1
    return write
```

**Encode and Decode Strings (LC 271)**: The key challenge is choosing a delimiter that can't appear in the strings. Use length-prefix encoding:

```python
def encode(strs):
    return ''.join(f"{len(s)}#{s}" for s in strs)

def decode(s):
    result = []
    i = 0
    while i < len(s):
        j = s.index('#', i)
        length = int(s[i:j])
        result.append(s[j+1:j+1+length])
        i = j + 1 + length
    return result
```

## Sliding Window on Strings

**Minimum Window Substring (LC 76)**:

```python
from collections import Counter

def minWindow(s, t):
    need = Counter(t)
    missing = len(t)
    best = ""
    left = 0

    for right, c in enumerate(s):
        if need[c] > 0:
            missing -= 1
        need[c] -= 1

        if missing == 0:
            while need[s[left]] < 0:
                need[s[left]] += 1
                left += 1
            window = s[left:right+1]
            if not best or len(window) < len(best):
                best = window
            need[s[left]] += 1
            missing += 1
            left += 1

    return best
```

**Permutation in String (LC 567)**: Fixed-size sliding window with character count comparison.

## Regular Expression Matching (LC 10)

This is a hard DP problem that frequently appears at senior levels:

```python
def isMatch(s, p):
    m, n = len(s), len(p)
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True

    for j in range(1, n + 1):
        if p[j-1] == '*':
            dp[0][j] = dp[0][j-2]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if p[j-1] == '*':
                dp[i][j] = dp[i][j-2]  # zero occurrences
                if p[j-2] == '.' or p[j-2] == s[i-1]:
                    dp[i][j] |= dp[i-1][j]  # one or more occurrences
            elif p[j-1] == '.' or p[j-1] == s[i-1]:
                dp[i][j] = dp[i-1][j-1]

    return dp[m][n]
```

The state `dp[i][j]` = "does `s[:i]` match `p[:j]`?" The star case is the tricky one: either match zero characters (use `dp[i][j-2]`) or match one more character (use `dp[i-1][j]`).

## Key String Interview Patterns Summary

| Pattern | Use For |
|---|---|
| Character frequency (Counter/array) | Anagram, permutation, window |
| Two pointers expand from center | Palindrome substring |
| Sliding window with two pointers | Min window, substring with K distinct |
| KMP / Rabin-Karp | O(n) pattern matching |
| Length-prefix encoding | Serialization without delimiters |
| DP on string indices | Regex, edit distance, wildcard matching |

String problems reward thorough edge case thinking. Always consider: empty strings, single characters, strings with repeated characters, case sensitivity, and Unicode vs ASCII. Interviewers notice when you ask these questions before coding.
