---
title: "Longest Common Subsequence and Its Variants: A Complete Interview Guide"
description: "Master LCS and its family of problems — edit distance, shortest common supersequence, LCS of three strings, space-optimized variants — with clear recurrences, implementation patterns, and interview strategy."
date: "2026-03-20"
category: "Algorithms"
---

The Longest Common Subsequence problem is one of the most important dynamic programming foundations in computer science interviews. It's not just a standalone problem — it's the root of a family of problems including edit distance, diff algorithms, biological sequence alignment, and string similarity. Understanding LCS deeply means understanding a substantial fraction of DP string problems.

## The Core Problem

A subsequence of a string is any subset of characters that appear in left-to-right order (not necessarily contiguous). "ACE" is a subsequence of "ABCDE". "AEC" is not.

Given two strings X of length m and Y of length n, find the length of their longest common subsequence.

**The recurrence:**

Define `dp[i][j]` = length of LCS of X[0..i-1] and Y[0..j-1].

- Base case: `dp[0][j] = dp[i][0] = 0` (empty string LCS is 0)
- If `X[i-1] == Y[j-1]`: `dp[i][j] = dp[i-1][j-1] + 1`
- Else: `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`

The logic: if the current characters match, extend the LCS of the prefixes. If not, the best we can do is the LCS obtained by dropping one character from either string — take the better option.

**Complexity:** O(mn) time, O(mn) space.

```python
def lcs_length(X: str, Y: str) -> int:
    m, n = len(X), len(Y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if X[i-1] == Y[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]
```

## Reconstructing the LCS

Returning the length is often not enough. To reconstruct the actual subsequence, backtrack through the DP table from `dp[m][n]`:

- If `X[i-1] == Y[j-1]`: include this character, move to `dp[i-1][j-1]`
- Else: move in the direction of the larger value (up or left)

This runs in O(m+n) after the table is filled and reconstructs one valid LCS (multiple may exist).

## Variant 1: Edit Distance (Levenshtein Distance)

Edit distance between two strings is the minimum number of single-character insertions, deletions, or substitutions needed to transform one string into the other.

**Recurrence:**

- If `X[i-1] == Y[j-1]`: `dp[i][j] = dp[i-1][j-1]` (no operation needed)
- Else: `dp[i][j] = 1 + min(dp[i-1][j-1], dp[i-1][j], dp[i][j-1])`
  - `dp[i-1][j-1]` = substitution
  - `dp[i-1][j]` = deletion from X
  - `dp[i][j-1]` = insertion into X

The connection to LCS: LCS maximizes matches; edit distance minimizes mismatches. They're dual views of the same underlying structure.

**Interview insight:** Edit distance is used in spell checkers, DNA sequence alignment, and natural language processing. When asked about similarity between two strings, edit distance is usually the right framing.

## Variant 2: Shortest Common Supersequence

The Shortest Common Supersequence (SCS) of X and Y is the shortest string Z such that both X and Y are subsequences of Z.

**Key insight:** Any character in the LCS appears exactly once in the SCS. Characters not in the LCS appear once each from X and Y.

Formula: `|SCS| = |X| + |Y| - |LCS(X, Y)|`

To reconstruct the SCS, merge X and Y using the LCS as a backbone: when characters match (part of LCS), include once; when they don't match, include both.

## Variant 3: LCS of Three Strings

Extending to three strings X, Y, Z is a natural interview follow-up. The recurrence extends in the expected way:

Define `dp[i][j][k]` = LCS of X[0..i-1], Y[0..j-1], Z[0..k-1].

- If `X[i-1] == Y[j-1] == Z[k-1]`: `dp[i][j][k] = dp[i-1][j-1][k-1] + 1`
- Else: `dp[i][j][k] = max(dp[i-1][j][k], dp[i][j-1][k], dp[i][j][k-1])`

**Complexity:** O(mnp) time and space. For large inputs, this becomes impractical quickly — an important point to raise in an interview to demonstrate awareness of scaling.

## Space Optimization: Rolling Array

The full O(mn) table is often unnecessary. Since each cell `dp[i][j]` only depends on `dp[i-1][j-1]`, `dp[i-1][j]`, and `dp[i][j-1]`, you only need to keep two rows at a time.

```python
def lcs_space_optimized(X: str, Y: str) -> int:
    m, n = len(X), len(Y)
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if X[i-1] == Y[j-1]:
                curr[j] = prev[j-1] + 1
            else:
                curr[j] = max(prev[j], curr[j-1])
        prev, curr = curr, [0] * (n + 1)
    return prev[n]
```

This reduces space to O(n). Note: the space-optimized version cannot reconstruct the actual LCS without additional bookkeeping.

## Related Problems Worth Knowing

**Longest Palindromic Subsequence:** LPS of string S = LCS(S, reverse(S)). The longest palindromic subsequence is the LCS of the string with its reverse.

**Minimum insertions/deletions to convert X to Y:**
- Minimum deletions = `|X| - |LCS(X, Y)|`
- Minimum insertions = `|Y| - |LCS(X, Y)|`

**Count of distinct LCS:** Harder variant — count how many distinct LCS strings exist. Requires careful handling of duplicate characters in the DP recurrence.

**Longest Increasing Subsequence (LIS):** Reducible to LCS with a sorted copy of the array. LIS of array A = LCS(A, sorted(A)). This gives an O(n²) LIS solution; the patience sorting approach achieves O(n log n).

## Interview Strategy

When you encounter an LCS-flavored problem, establish these points before coding:

1. **Confirm the definition of "subsequence" vs. "substring"** — They require different recurrences. Subsequence: non-contiguous, order preserved. Substring: contiguous.

2. **Name the variant** — If the problem is about converting one string to another with minimum operations, that's edit distance. If it's about the shortest string containing both, that's SCS. Naming it shows pattern recognition.

3. **State the recurrence before coding** — Write the recurrence in plain English first. "If the characters match, we extend the LCS of the shorter prefixes. If they don't, we take the best from dropping one character from either side." This prevents getting lost in the implementation.

4. **Discuss space optimization proactively** — After the O(mn) solution, mention the rolling array optimization. This signals you think about practical constraints, not just asymptotic correctness.

LCS is not a problem to memorize mechanically — it is a DP pattern to internalize. The moment you see a problem about two sequences and "compatibility" between elements, LCS or one of its variants is almost certainly the right mental model.
