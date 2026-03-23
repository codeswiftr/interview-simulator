---
title: "Probability and Expected Value in Coding Interviews"
description: "How to approach probability, expected value, random algorithms, Monte Carlo simulations, and randomized data structures in technical interviews."
date: "2026-03-20"
category: "Algorithms"
---

Probability questions appear in coding interviews at a higher rate than most candidates expect. They range from pure math puzzles to practical randomized algorithms like reservoir sampling and skip lists. Understanding the fundamentals — and knowing how to derive expected values from first principles — separates candidates who memorize answers from those who can reason under pressure.

## The Basics Interviewers Assume You Know

**Linearity of expectation** is the single most useful tool in probabilistic analysis. It states that `E[X + Y] = E[X] + E[Y]` regardless of whether X and Y are independent. This lets you analyze complex random variables by decomposing them into simple indicator variables.

**Classic example:** Expected number of coin flips to get heads. If `p` is the probability of heads, then `E[flips] = 1/p`. For a fair coin, that's 2. This comes from the geometric distribution.

**Indicator random variables:** Define `X_i = 1` if event i occurs, 0 otherwise. Then `E[X_i] = P(event i occurs)`. Sum over all i using linearity of expectation.

## Expected Value Derivations You Must Know

### Expected comparisons in QuickSort

QuickSort's average case analysis uses indicator variables elegantly. For an array of n elements, let `X_{ij} = 1` if elements i and j are compared during the sort. An element i is compared to j exactly when i or j is chosen as the pivot before any element between them in sorted order.

```
P(i compared to j) = 2 / (j - i + 1)

E[total comparisons] = Σ_{i<j} 2/(j-i+1) ≈ 2n ln n = O(n log n)
```

### Birthday Problem

How many people until expected collision in birthdays? The exact answer: you need about `√(2 × 365 × ln 2) ≈ 23` people for a 50% probability of collision. More generally, for n equally likely values, you need O(√n) draws.

This matters for hash tables — it's why hash collisions become likely much sooner than most developers expect.

### Coupon Collector Problem

Given n distinct coupons, each draw picks one uniformly at random. How many draws until you collect all n?

```
E[draws] = n × H_n = n × (1 + 1/2 + 1/3 + ... + 1/n) ≈ n ln n
```

This models cache warming, DNS record discovery, and test coverage — expect interviewers to use it as a warmup.

## Randomized Algorithms

### Reservoir Sampling

Given a stream of unknown length, sample k elements uniformly at random:

```python
import random

def reservoir_sample(stream, k):
    reservoir = []
    for i, item in enumerate(stream):
        if i < k:
            reservoir.append(item)
        else:
            j = random.randint(0, i)
            if j < k:
                reservoir[j] = item
    return reservoir
```

**Why it works:** After processing element i (0-indexed), each of the first i+1 elements has probability k/(i+1) of being in the reservoir. This invariant is maintained at each step.

**Interview follow-up:** What if elements have weights? Use the weighted reservoir sampling algorithm (A-Res or A-Chao).

### Fisher-Yates Shuffle

The correct O(n) in-place shuffle — a common interview question where candidates often get the subtle bias wrong:

```python
def shuffle(arr):
    n = len(arr)
    for i in range(n - 1, 0, -1):
        j = random.randint(0, i)  # inclusive on both ends
        arr[i], arr[j] = arr[j], arr[i]
```

The common mistake: picking `j = random.randint(0, n-1)` introduces bias because `n^n` permutations don't divide evenly into `n!` outcomes.

### Random Pivot in QuickSort / QuickSelect

QuickSelect finds the k-th smallest element in expected O(n) time using random pivots:

```python
def quickselect(arr, k):
    pivot = random.choice(arr)
    lows = [x for x in arr if x < pivot]
    highs = [x for x in arr if x > pivot]
    pivots = [x for x in arr if x == pivot]

    if k < len(lows):
        return quickselect(lows, k)
    elif k < len(lows) + len(pivots):
        return pivot
    else:
        return quickselect(highs, k - len(lows) - len(pivots))
```

Expected time analysis: each call reduces the problem size by a constant fraction on average, giving O(n) expected time.

## Monte Carlo Methods

Monte Carlo simulations estimate values through random sampling. The canonical example is estimating π:

```python
import random

def estimate_pi(n_samples):
    inside = 0
    for _ in range(n_samples):
        x, y = random.uniform(-1, 1), random.uniform(-1, 1)
        if x*x + y*y <= 1:
            inside += 1
    return 4 * inside / n_samples
```

**Convergence:** Error decreases as O(1/√n). Doubling samples only reduces error by √2 — Monte Carlo is slow to converge but parallelizes perfectly.

**Interview context:** Interviewers use Monte Carlo to test if you understand variance reduction techniques (importance sampling, stratified sampling, antithetic variates). You don't need to implement these, but knowing they exist signals depth.

## Randomized Data Structures

### Skip Lists

Skip lists use randomization to achieve O(log n) expected search, insert, and delete — same asymptotic performance as balanced BSTs, but simpler to implement. Each node is promoted to higher levels with probability p (typically 0.5).

Expected height: O(log n). Expected number of nodes examined in a search: O(log n).

### Bloom Filters

A space-efficient probabilistic set. Uses k hash functions; a query returns "definitely not in set" or "probably in set." False positive probability is approximately `(1 - e^{-kn/m})^k` where m is bit array size and n is elements inserted.

**When interviewers ask about false positive rates:** The optimal k (minimizing false positives) is `(m/n) × ln 2 ≈ 0.693 × (m/n)`.

## Expected Time Complexity in Randomized Algorithms

A key distinction: expected time complexity differs from worst-case. For QuickSort, worst case is O(n²) but expected is O(n log n). Interviewers often probe:

1. "What's the probability QuickSort runs in O(n²)?" — Astronomically small for random pivot; exponentially unlikely
2. "Can we guarantee O(n log n) worst case?" — Yes, with median-of-medians pivot selection, but with worse constants

## Common Interview Mistakes

**Confusing independence with uncorrelation.** Independent random variables are uncorrelated, but the converse is false. Linearity of expectation holds for all random variables; the variance formula `Var[X+Y] = Var[X] + Var[Y]` only holds for independent ones.

**Off-by-one in reservoir sampling.** When i is 0-indexed, the replacement probability at step i is k/(i+1), not k/i.

**Forgetting to state assumptions.** When you write O(n log n) for QuickSort, say "expected O(n log n) assuming random pivots." Interviewers reward precision.

Probability questions reward candidates who think from first principles. When in doubt, define your random variables, apply linearity of expectation, and work through small examples explicitly. The math is rarely harder than calculus — the challenge is systematic setup.
