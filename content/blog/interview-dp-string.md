---
title: "Dynamic Programming on Strings: LCS, Edit Distance, and Beyond"
description: "Master the most common string DP patterns in coding interviews — from LCS and edit distance to palindromes, interleaving strings, and regex matching."
date: "2026-03-20"
category: "Algorithms"
---

String dynamic programming is one of the most frequently tested areas in technical interviews, appearing at companies like Google, Amazon, and Meta. These problems share a common pattern: you define a 2D table where `dp[i][j]` represents some optimal property of the first `i` characters of one string and the first `j` characters of another. Once you internalize this structure, an entire class of hard problems becomes tractable.

## The Core Pattern: 2D DP Table

Every string DP problem starts the same way. You have one or two strings, you define what `dp[i][j]` means, you handle the base cases, and then you find the recurrence relation. The magic is that the cell `dp[i][j]` depends only on nearby cells — usually `dp[i-1][j]`, `dp[i][j-1]`, and `dp[i-1][j-1]`.

## Longest Common Subsequence (LCS)

LCS asks: given two strings `s` and `t`, what is the longest subsequence common to both? A subsequence doesn't require consecutive characters.

```python
def lcs(s: str, t: str) -> int:
    m, n = len(s), len(t)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s[i-1] == t[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    return dp[m][n]
```

The recurrence is clean: if the characters match, extend the previous common subsequence. Otherwise, take the best of skipping one character from either string. Time and space complexity are both O(m × n), though space can be optimized to O(min(m, n)) by keeping only two rows.

In interviews, you'll often be asked to reconstruct the actual subsequence — do this by backtracking through the DP table from `dp[m][n]`.

## Edit Distance (Levenshtein Distance)

Edit distance asks for the minimum number of insertions, deletions, or substitutions to transform `s` into `t`. This underpins spell-checkers, diff tools, and DNA sequence alignment.

```python
def edit_distance(s: str, t: str) -> int:
    m, n = len(s), len(t)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Base cases: transforming to/from empty string
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s[i-1] == t[j-1]:
                dp[i][j] = dp[i-1][j-1]  # No cost
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],    # Delete from s
                    dp[i][j-1],    # Insert into s
                    dp[i-1][j-1]   # Replace
                )

    return dp[m][n]
```

The base cases are crucial: `dp[i][0] = i` because you need `i` deletions to reduce `s[0..i]` to empty, and `dp[0][j] = j` because you need `j` insertions to build `t[0..j]` from empty.

## Palindrome Problems

### Longest Palindromic Subsequence

Here you use a single string but still build a 2D table: `dp[i][j]` is the length of the longest palindromic subsequence in `s[i..j]`.

```python
def longest_palindromic_subsequence(s: str) -> int:
    n = len(s)
    dp = [[0] * n for _ in range(n)]

    for i in range(n):
        dp[i][i] = 1  # Every single char is a palindrome

    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                dp[i][j] = dp[i+1][j-1] + 2
            else:
                dp[i][j] = max(dp[i+1][j], dp[i][j-1])

    return dp[0][n-1]
```

Note the iteration order: you must fill by increasing substring length, not row by row, because `dp[i][j]` depends on `dp[i+1][j-1]` which is a shorter substring.

### Minimum Insertions to Make a Palindrome

This is a classic transformation: the answer equals `n - LPS(s)`. If the longest palindromic subsequence has length `k`, you need `n - k` insertions to make the whole string palindromic.

## Interleaving Strings

Given strings `s1`, `s2`, and `s3`, determine if `s3` is formed by interleaving `s1` and `s2` while preserving relative order in each.

```python
def is_interleave(s1: str, s2: str, s3: str) -> bool:
    m, n = len(s1), len(s2)
    if m + n != len(s3):
        return False

    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True

    for i in range(1, m + 1):
        dp[i][0] = dp[i-1][0] and s1[i-1] == s3[i-1]
    for j in range(1, n + 1):
        dp[0][j] = dp[0][j-1] and s2[j-1] == s3[j-1]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp[i][j] = (
                (dp[i-1][j] and s1[i-1] == s3[i+j-1]) or
                (dp[i][j-1] and s2[j-1] == s3[i+j-1])
            )

    return dp[m][n]
```

The key insight: `dp[i][j]` is true if we can form `s3[0..i+j-1]` using `s1[0..i-1]` and `s2[0..j-1]`.

## Regex Matching

This is one of the harder string DP problems, requiring careful handling of `*` wildcards.

```python
def is_match(s: str, p: str) -> bool:
    m, n = len(s), len(p)
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True

    # Patterns like a*, a*b*, a*b*c* can match empty string
    for j in range(2, n + 1):
        dp[0][j] = dp[0][j-2] and p[j-1] == '*'

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if p[j-1] == '*':
                # Zero occurrences of preceding char
                dp[i][j] = dp[i][j-2]
                # One or more occurrences (if char matches)
                if p[j-2] == '.' or p[j-2] == s[i-1]:
                    dp[i][j] = dp[i][j] or dp[i-1][j]
            elif p[j-1] == '.' or p[j-1] == s[i-1]:
                dp[i][j] = dp[i-1][j-1]

    return dp[m][n]
```

## Interview Tips for String DP

**Identify the state clearly.** Before writing any code, define precisely what `dp[i][j]` represents — this is half the problem.

**Handle base cases explicitly.** String DP bugs almost always live in base case handling. Walk through small examples (empty strings, single characters) by hand.

**Trace through the recurrence.** For any recurrence, verify it on a 3×3 example before coding. If the logic holds for small inputs, the implementation is usually correct.

**Space optimization.** Many interviewers will ask about reducing O(m×n) space. For problems that only look at the previous row, you can use two arrays. For edit distance, you can reduce to O(n) with careful updates.

**Complexity matters.** All of these run in O(m×n) time. State this upfront. Interviewers want to know you can analyze your own solution.

String DP problems reward methodical thinking over cleverness. Define your state, handle your bases, derive the recurrence, and implement carefully — the pattern is the same every time.
