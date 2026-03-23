---
title: "Advanced Bit Manipulation for Interviews: XOR Tricks, Bit DP, and Masking Patterns"
description: "Master advanced bit manipulation techniques: XOR-based algorithms, bitmask DP, counting set bits efficiently, and the 20 patterns that appear most often in technical interviews."
date: "2026-03-20"
category: "Algorithms"
---

# Advanced Bit Manipulation for Interviews

Bit manipulation is one of those topics where the gap between "I know what AND and OR do" and "I can use XOR to find a missing number in O(1) space" separates mid-level candidates from strong ones. This guide covers the advanced patterns that appear frequently at FAANG and tier-1 interviews.

## Why Interviewers Love Bit Problems

Bit manipulation problems test three things simultaneously: low-level hardware intuition, space optimization thinking, and creative problem-solving. A candidate who reaches for bit tricks instinctively — rather than only when prompted — signals genuine CS depth.

## Foundation: Operator Quick Reference

```
x & y   — AND: bits set in both
x | y   — OR: bits set in either
x ^ y   — XOR: bits set in exactly one
~x      — NOT: flip all bits
x << n  — left shift: multiply by 2^n
x >> n  — right shift: divide by 2^n (arithmetic for signed)
```

## XOR: The Swiss Army Knife

XOR has three properties that unlock most "XOR trick" problems:
1. `x ^ x = 0` (self-canceling)
2. `x ^ 0 = x` (identity)
3. XOR is commutative and associative

**Pattern 1: Find the missing number**
```python
def missing_number(nums: list[int]) -> int:
    result = len(nums)
    for i, n in enumerate(nums):
        result ^= i ^ n
    return result
# Time: O(n), Space: O(1)
```

**Pattern 2: Single number (all others appear twice)**
```python
def single_number(nums: list[int]) -> int:
    return reduce(lambda a, b: a ^ b, nums)
```

**Pattern 3: Two unique numbers among duplicates**
```python
def single_number_iii(nums: list[int]) -> list[int]:
    xor = reduce(lambda a, b: a ^ b, nums)
    # Find rightmost differing bit
    diff_bit = xor & (-xor)
    a = 0
    for n in nums:
        if n & diff_bit:
            a ^= n
    return [a, xor ^ a]
```

**Pattern 4: XOR for swap without temp variable**
```python
a ^= b; b ^= a; a ^= b  # Swaps a and b
```

## Counting Set Bits

**Brian Kernighan's algorithm — O(k) where k = number of set bits:**
```python
def count_bits(n: int) -> int:
    count = 0
    while n:
        n &= n - 1  # Clears the lowest set bit
        count += 1
    return count
```

The key insight: `n & (n-1)` always clears exactly the lowest set bit.

**Popcount for ranges (DP approach):**
```python
def count_bits_range(n: int) -> list[int]:
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        dp[i] = dp[i >> 1] + (i & 1)
    return dp
# dp[i] = dp[i/2] + (1 if i is odd else 0)
```

## Bit Masking Patterns

**Check if bit k is set:**
```python
is_set = (n >> k) & 1
```

**Set bit k:**
```python
n |= (1 << k)
```

**Clear bit k:**
```python
n &= ~(1 << k)
```

**Toggle bit k:**
```python
n ^= (1 << k)
```

**Extract lowest set bit:**
```python
lowest = n & (-n)  # Two's complement trick
```

**Turn off lowest set bit:**
```python
n &= n - 1
```

**Check power of two:**
```python
is_power_of_two = n > 0 and (n & (n - 1)) == 0
```

## Bitmask DP: State Compression

Bitmask DP is essential for problems where the state is a subset of elements. The classic form uses a bitmask of size `2^n` to represent which elements have been used.

**Template:**
```python
n = len(items)
dp = [float('inf')] * (1 << n)
dp[0] = base_case

for mask in range(1 << n):
    for i in range(n):
        if mask & (1 << i):  # item i is in current subset
            prev_mask = mask ^ (1 << i)
            dp[mask] = min(dp[mask], dp[prev_mask] + cost(i, mask))
```

**Example: Minimum cost to assign tasks to workers**
```python
def assign_tasks(cost: list[list[int]]) -> int:
    n = len(cost)
    dp = [float('inf')] * (1 << n)
    dp[0] = 0
    for mask in range(1, 1 << n):
        worker = bin(mask).count('1') - 1  # which worker's turn
        for task in range(n):
            if mask & (1 << task):
                dp[mask] = min(dp[mask],
                    dp[mask ^ (1 << task)] + cost[worker][task])
    return dp[(1 << n) - 1]
```

## Interview Patterns Cheat Sheet

| Problem Type | Bit Trick |
|-------------|-----------|
| Find single element | XOR all elements |
| Count set bits | Brian Kernighan / popcount DP |
| Check subset | `(a & b) == b` |
| Enumerate all subsets of n | Loop `0` to `2^n - 1` |
| Enumerate subsets of a mask | `for s = mask; s > 0; s = (s-1) & mask` |
| Power of 2 check | `n & (n-1) == 0` |
| Align to next power of 2 | `1 << (n-1).bit_length()` |

## Enumerating Subsets of a Bitmask

This pattern appears in optimization problems where you need to try all sub-subsets:

```python
# Enumerate all subsets of mask (including empty set)
mask = 0b1011
s = mask
while s > 0:
    # process subset s
    s = (s - 1) & mask
# Time: O(3^n) total across all masks — each element is in/out/excluded
```

## Common Interview Questions and Approaches

1. **Reverse bits** — shift and OR, 32 iterations
2. **Number of 1 bits** — Brian Kernighan
3. **Single Number I/II/III** — XOR variants
4. **Maximum XOR of two numbers** — Trie + bit prefix
5. **XOR queries on subarrays** — prefix XOR array
6. **Subsets via bitmask** — enumerate `0` to `2^n`
7. **Minimum XOR sum** — bitmask DP assignment

## Key Interview Tips

- Always clarify: 32-bit or 64-bit integers? Signed or unsigned? Python has arbitrary precision integers, which changes edge cases.
- Mention time complexity in terms of both `n` and word size `W` when relevant.
- For bitmask DP, immediately state the exponential space/time constraint — interviewers want to see you recognize the tradeoff.
- Practice explaining XOR properties verbally — interviewers often ask "why does this work?" after you write the code.

Bit manipulation mastery is a force multiplier across algorithm categories. The patterns above appear not only in "bit problems" but embedded inside graph problems (bitmask DP for TSP), string problems (character frequency as bitmask), and system design discussions about memory efficiency.
