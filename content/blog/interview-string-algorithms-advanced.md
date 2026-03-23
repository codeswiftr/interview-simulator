---
title: "Advanced String Algorithms: KMP, Rabin-Karp, and Z-Algorithm"
description: "String matching algorithms for advanced coding interviews — KMP failure function, Rabin-Karp rolling hash, Z-algorithm, Aho-Corasick for multi-pattern matching, and when to use each."
date: "2026-03-20"
category: "Algorithms"
---

# Advanced String Algorithms: KMP, Rabin-Karp, and Z-Algorithm

Basic string problems use built-in methods or brute-force O(n×m) approaches. At senior level, interviewers expect pattern matching algorithms that run in O(n + m). These algorithms appear in competitive programming, systems questions (text indexing, virus scanning), and occasionally in interview problems that are impractical without them.

## The Problem: Naive String Matching is O(n×m)

Find all occurrences of pattern `p` (length m) in text `t` (length n). Naive: try each position in `t`, compare all m characters. Worst case: O(n×m).

For n=10^6, m=10^3 text and pattern, this is 10^9 operations — too slow. We need O(n + m).

## KMP (Knuth-Morris-Pratt): O(n + m)

KMP avoids re-examining characters we've already matched. When a mismatch occurs, the "failure function" tells us the longest proper prefix of the matched portion that is also a suffix — we can skip to that position.

**Step 1: Build the failure function (also called LPS — Longest Proper Prefix Suffix)**

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
        elif length != 0:
            length = lps[length - 1]  # Fall back
        else:
            lps[i] = 0
            i += 1

    return lps
```

**Step 2: Search using the LPS**

```python
def kmp_search(text, pattern):
    n, m = len(text), len(pattern)
    lps = build_lps(pattern)
    matches = []

    i = j = 0  # i = text index, j = pattern index
    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
        if j == m:
            matches.append(i - j)
            j = lps[j - 1]
        elif i < n and text[i] != pattern[j]:
            if j != 0:
                j = lps[j - 1]  # Don't re-examine text[i]
            else:
                i += 1

    return matches
```

**Time:** O(n + m). Never re-examines text characters.

## Rabin-Karp: Rolling Hash for O(n + m) Average

Instead of comparing characters, compare hash values. Compute hash of pattern; slide a window over the text and compare hashes. On hash match, verify (to handle collisions).

```python
def rabin_karp(text, pattern):
    n, m = len(text), len(pattern)
    BASE = 31
    MOD = 10**9 + 9
    matches = []

    def hash_str(s):
        h = 0
        for c in s:
            h = (h * BASE + ord(c) - ord('a') + 1) % MOD
        return h

    pattern_hash = hash_str(pattern)

    # Compute rolling hash for text windows
    high_power = pow(BASE, m - 1, MOD)
    window_hash = hash_str(text[:m])

    if window_hash == pattern_hash and text[:m] == pattern:
        matches.append(0)

    for i in range(1, n - m + 1):
        # Roll the hash: remove leftmost char, add new rightmost char
        window_hash = (
            (window_hash - (ord(text[i-1]) - ord('a') + 1) * high_power) * BASE
            + (ord(text[i+m-1]) - ord('a') + 1)
        ) % MOD

        if window_hash == pattern_hash and text[i:i+m] == pattern:
            matches.append(i)

    return matches
```

**Why Rabin-Karp shines:** Multi-pattern matching. If you have K patterns, compute all K hashes and check against a set. One pass over text checks against all patterns simultaneously. This extends KMP to multi-pattern without the O(K×m) preprocessing overhead.

## Z-Algorithm: O(n + m) Without Failure Function

The Z-array at position i contains the length of the longest substring starting at position i that matches a prefix of the string.

```python
def z_function(s):
    n = len(s)
    z = [0] * n
    z[0] = n
    l = r = 0  # Current Z-box [l, r)

    for i in range(1, n):
        if i < r:
            z[i] = min(r - i, z[i - l])
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        if i + z[i] > r:
            l, r = i, i + z[i]

    return z

def z_search(text, pattern):
    combined = pattern + '$' + text  # Separator not in alphabet
    z = z_function(combined)
    m = len(pattern)
    return [i - m - 1 for i in range(m + 1, len(combined)) if z[i] == m]
```

**Z-algorithm advantage:** The implementation is arguably cleaner than KMP. Same O(n + m) complexity. Some find it more intuitive.

## Aho-Corasick: Multi-Pattern Matching

For matching K patterns in text simultaneously in O(n + total_pattern_length + matches) time. Builds a trie of patterns, then adds failure links (like KMP's failure function but for a trie).

Used in: spam filters, antivirus scanning, network intrusion detection. Not typically implemented in interviews but worth knowing for systems design questions about text processing.

## When to Use Which Algorithm

| Scenario | Algorithm |
|---|---|
| Single pattern search | KMP or Z-algorithm |
| Multiple patterns | Rabin-Karp (hash set) or Aho-Corasick |
| Repeated search, same pattern | Preprocess with KMP/Z once |
| Approximate matching | None of these — use DP (edit distance) |
| Implement quickly under pressure | Z-algorithm (clean code) or Rabin-Karp (intuitive concept) |

## Interview Reality

Most interviewers asking pattern matching questions accept O(n×m) brute force for partial credit. The O(n + m) algorithms are a "strong signal" that earns full marks and impresses. If you're applying to companies like Google, Meta, or competitive programming-heavy orgs, know at least KMP and Rabin-Karp.

For practical interview prep: implement KMP once from scratch until you can do it without references. The failure function derivation is the core — if you understand why `j = lps[j-1]` on mismatch (rather than `j = 0`), you understand KMP.

Rolling hash (Rabin-Karp) is often more useful in practice because the multi-pattern extension is clean and the algorithm is easier to reason about under pressure.
