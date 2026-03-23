---
title: "Combinatorics in Coding Interviews: Counting Problems from First Principles"
description: "A practical guide to combinatorics in interviews — binomial coefficients, stars and bars, inclusion-exclusion, Catalan numbers, Pascal's triangle, and how to recognize which counting technique applies to each problem type."
date: "2026-03-20"
category: "Algorithms"
---

Counting problems appear in interviews in deceptively simple packaging: "How many ways can you arrange...?", "Count the number of valid...?", "In how many ways can you reach...?". The challenge is that these problems span a wide range of difficulty, and the key skill is recognizing which combinatorial structure is in play. A problem that requires inclusion-exclusion is easy if you recognize the pattern and hard if you try to solve it with brute-force enumeration.

## Foundations: The Basic Counting Rules

**Product rule:** If event A can happen in m ways and event B can happen in n ways, and they are independent, both can happen in m × n ways.

**Sum rule:** If event A can happen in m ways and event B in n ways, and they are mutually exclusive, one or the other can happen in m + n ways.

**Permutations:** Arrangements of k objects chosen from n distinct objects where order matters: P(n, k) = n! / (n−k)!

**Combinations (choose):** Selections of k objects from n where order does not matter: C(n, k) = n! / (k! × (n−k)!)

These rules compound. The number of ways to deal a 5-card poker hand from a 52-card deck is C(52, 5) — choosing 5 cards where order doesn't matter.

## Pascal's Triangle

Pascal's triangle is both a computational tool and a source of combinatorial identities. Each entry is C(n, k), and is computed as the sum of the two entries above it: C(n, k) = C(n-1, k-1) + C(n-1, k).

This identity has a combinatorial interpretation: C(n, k) counts subsets of size k from n items. To include item n, choose the remaining k−1 from n−1 items: C(n-1, k-1). To exclude item n, choose k from n−1 items: C(n-1, k). Sum them.

Pascal's triangle appears in interviews as a dynamic programming problem: compute C(n, k) without overflow by building the triangle row by row, or answer "how many unique paths are there in an m×n grid?" (answer: C(m+n-2, m-1), because you must make exactly m-1 right moves and n-1 down moves in some order).

```python
def unique_paths(m: int, n: int) -> int:
    # C(m+n-2, m-1)
    from math import comb
    return comb(m + n - 2, m - 1)
```

## Stars and Bars

Stars and bars answers questions of the form: "In how many ways can you distribute n identical items into k distinct bins?"

**Unrestricted distribution** (bins can be empty): C(n + k − 1, k − 1)

**At least one item per bin**: C(n − 1, k − 1) (place one item in each bin first, then distribute the remaining n−k items freely)

**Interview applications:**

- "How many non-negative integer solutions are there to x₁ + x₂ + x₃ = 10?" → Stars and bars with n=10, k=3: C(12, 2) = 66
- "How many ways can you make change for $1.00 using pennies, nickels, dimes, and quarters?" → This is harder (the bins are not interchangeable and have structured values), but stars and bars provides the intuition for why it's a counting problem.

The key recognition: whenever you're distributing identical objects into distinct containers, stars and bars is the framework.

## Inclusion-Exclusion Principle

The inclusion-exclusion principle counts elements in the union of sets by alternately adding and subtracting overlapping regions:

|A ∪ B| = |A| + |B| − |A ∩ B|

|A ∪ B ∪ C| = |A| + |B| + |C| − |A ∩ B| − |A ∩ C| − |B ∩ C| + |A ∩ B ∩ C|

**Interview example:** "Count integers from 1 to 100 divisible by 2, 3, or 5."

- Divisible by 2: 50
- Divisible by 3: 33
- Divisible by 5: 20
- Divisible by 6 (2∩3): 16
- Divisible by 10 (2∩5): 10
- Divisible by 15 (3∩5): 6
- Divisible by 30 (2∩3∩5): 3

Answer: 50 + 33 + 20 − 16 − 10 − 6 + 3 = 74.

Inclusion-exclusion also powers the **derangement count** — the number of permutations where no element stays in its original position. The formula is D(n) = n! × Σ (−1)^k / k! for k from 0 to n, which approaches n!/e as n grows.

## Catalan Numbers

The Catalan numbers (1, 1, 2, 5, 14, 42, 132, ...) arise in a remarkable variety of counting problems. The nth Catalan number is C(n) = C(2n, n) / (n+1).

Catalan numbers count:
- The number of valid sequences of n pairs of matched parentheses
- The number of distinct binary trees with n nodes
- The number of ways to triangulate a polygon with n+2 sides
- The number of monotone paths from (0,0) to (n,n) that never go above the diagonal

The parentheses problem is the most common interview appearance. "How many valid parenthesization strings of length 2n are there?" → C(n).

This connects to a DP approach: define dp[i] = number of valid strings of length 2i. At position 2i, the matching closing paren for the first open paren must occur at position 2j for some j from 1 to i. This splits the string into two independent valid strings of lengths 2(j-1) and 2(i-j):

dp[i] = Σ dp[j-1] × dp[i-j] for j from 1 to i

This recurrence generates the Catalan numbers and is the structure behind many DP problems on trees and sequences.

## The Pigeonhole Principle

Simple but powerful: if n+1 items are placed in n bins, at least one bin contains at least two items.

**Interview applications:**

- "Prove that among any 13 people, at least two share a birth month." → 13 people, 12 months.
- "Given an array of n+1 integers from 1 to n, prove there's a duplicate." → n+1 values, n possible values.
- Graph theory: in any group of 6 people, either 3 are mutual acquaintances or 3 are mutual strangers (Ramsey theory, R(3,3) = 6).

Generalized pigeonhole: if n items are in k bins, some bin has at least ⌈n/k⌉ items.

## Recognizing Which Technique to Use

The core interview skill is pattern recognition:

| Pattern | Technique |
|---|---|
| "How many ways to arrange/select" | Permutations or combinations |
| "Distribute identical items into bins" | Stars and bars |
| "At least one / none of condition X" | Inclusion-exclusion or complementary counting |
| "Valid parentheses, binary trees, polygon triangulations" | Catalan numbers |
| "Prove existence of duplicate/overlap" | Pigeonhole principle |
| "Number of paths in a grid" | Pascal's triangle / combinatorics |
| "Recurrence over splits" | DP with Catalan-style recurrence |

**Complementary counting** deserves mention: counting the complement is often easier than counting directly. "How many arrangements of 5 cards have at least one heart?" is harder than "total arrangements minus arrangements with no hearts."

## Implementation Notes

For large n, computing C(n, k) modulo a prime is a common requirement in contest-style problems. Use Lucas' theorem or precompute factorials with modular inverse:

```python
MOD = 10**9 + 7

def mod_comb(n: int, k: int, mod: int = MOD) -> int:
    if k > n or k < 0:
        return 0
    num = den = 1
    for i in range(k):
        num = num * (n - i) % mod
        den = den * (i + 1) % mod
    return num * pow(den, mod - 2, mod) % mod  # Fermat's little theorem
```

Combinatorics is underrepresented in most interview prep resources compared to graphs and DP, which makes it a differentiator. Candidates who can recognize a stars-and-bars problem on sight, apply inclusion-exclusion without hesitation, and know that "count valid binary trees" is a Catalan number question demonstrate breadth that stands out.
