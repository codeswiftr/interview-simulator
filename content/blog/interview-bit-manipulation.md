---
title: "Bit Manipulation Interview Guide: XOR Tricks, Bit Counting, and Common Patterns"
description: "A practical guide to bit manipulation for software engineering interviews — covering the core operations, XOR properties, counting bits, and the patterns that appear most frequently in interview problems."
date: "2026-03-20"
category: "Algorithms"
---

# Bit Manipulation Interview Guide: XOR Tricks, Bit Counting, and Common Patterns

Bit manipulation appears in interviews for several types of roles: systems programming, embedded software, competitive programming-heavy companies, and any role where low-level optimization matters. Even for general software engineering, a handful of bit manipulation patterns appear frequently enough that knowing them cold is worthwhile.

This guide covers the fundamentals, the most useful tricks, and the patterns that show up most often in actual interviews.

## The Essential Operations

Before patterns, you need these operations to be automatic:

| Operation | Symbol | Meaning |
|-----------|--------|---------|
| AND | `a & b` | 1 only where both bits are 1 |
| OR | `a \| b` | 1 where either bit is 1 |
| XOR | `a ^ b` | 1 where bits differ |
| NOT | `~a` | Flip all bits |
| Left shift | `a << n` | Multiply by 2ⁿ |
| Right shift | `a >> n` | Divide by 2ⁿ (arithmetic shift for signed) |

**Quick checks to make automatic:**

- Is bit k set? `(n >> k) & 1 == 1`
- Set bit k: `n | (1 << k)`
- Clear bit k: `n & ~(1 << k)`
- Toggle bit k: `n ^ (1 << k)`
- Is n a power of 2? `n > 0 && (n & (n-1)) == 0`

That last one is a classic. If n is a power of 2, its binary representation has exactly one 1 bit. Subtracting 1 flips all bits below that position and the bit itself. ANDing them together gives 0.

## XOR: The Most Useful Bit Operation in Interviews

XOR has properties that make it uniquely powerful for certain problem types:

1. `a ^ a = 0` (any value XOR'd with itself is 0)
2. `a ^ 0 = a` (XOR with 0 is a no-op)
3. XOR is commutative and associative

These three properties together enable elegant solutions to otherwise O(n) space problems:

**Classic problem: Find the single number.** Given an array where every element appears twice except one, find the element that appears once.

Brute force: use a hash map to count occurrences — O(n) time, O(n) space.

XOR solution: XOR all elements together. Every pair cancels out (a ^ a = 0), leaving only the single element. O(n) time, O(1) space.

```python
def single_number(nums):
    result = 0
    for n in nums:
        result ^= n
    return result
```

**Extension: Two distinct numbers.** Given an array where every element appears twice except two, find both.

1. XOR all elements. The result is `a ^ b` (where a and b are the two singles).
2. Find any set bit in `a ^ b` — this bit differs between a and b (use `diff = (a^b) & -(a^b)` to isolate the lowest set bit).
3. Partition all numbers into two groups: those with this bit set, those without. XOR each group — one group yields a, the other yields b.

This pattern — using XOR to find a "distinguishing bit" and partition — appears in multiple interview problems.

## Counting Set Bits

**Brian Kernighan's algorithm:**

```python
def count_bits(n):
    count = 0
    while n:
        n &= n - 1  # clears the lowest set bit
        count += 1
    return count
```

`n & (n-1)` clears the rightmost set bit. By repeatedly applying this until n is 0, you count the bits. Time complexity: O(k) where k is the number of set bits.

**Interview follow-up: Count bits for all numbers 0 to n.** Naive: call count_bits for each number — O(n log n). Optimal: dynamic programming.

```python
def count_bits_range(n):
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        dp[i] = dp[i >> 1] + (i & 1)
    return dp
```

`i >> 1` is i with the last bit dropped (equivalent to i // 2, which we've already computed). We just add 1 if the last bit is set. O(n) time, O(n) space.

## Two's Complement and Negative Numbers

In most languages, integers use two's complement representation. Important consequences:

- `-1` in binary is all 1s (0xFFFFFFFF for 32-bit)
- `-n` is represented as `~n + 1`
- The minimum negative value has only the sign bit set

**Why this matters in interviews:**

The `>>` operator for signed integers is an arithmetic right shift — it fills with the sign bit (preserving negative numbers). For unsigned right shift (filling with 0s), use `>>>` in Java, or `(n >> k) & (0x7FFFFFFF >> (k-1))` in Python (which has arbitrary precision integers, not fixed-width).

Interview traps involving this:
- Right-shifting -1 in Java with `>>` gives -1 (sign extension)
- Python's integers don't overflow, which changes the behavior of ~n (it gives -(n+1), not what you'd get in C/Java for unsigned bit patterns)

## Common Interview Patterns

**Masking with AND:**

Extract the lower k bits: `n & ((1 << k) - 1)`

This creates a mask of k ones (e.g., `(1 << 4) - 1 = 0b1111`) and ANDs it with n.

**Swap without temporary variable:**

```python
a ^= b
b ^= a
a ^= b
```

This works because: after line 1, `a = a^b`. Line 2: `b = b ^ (a^b) = a`. Line 3: `a = (a^b) ^ a = b`. A fun interview question, but don't use in production (readability, and fails when a and b are the same memory location).

**Reversing bits:**

For a 32-bit integer, reverse the bit order. Standard approach: repeatedly take the lowest bit and shift it into the result:

```python
def reverse_bits(n):
    result = 0
    for _ in range(32):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result
```

Can be optimized with divide-and-conquer (swap adjacent bits, then adjacent pairs, then nibbles, etc.) for repeated calls.

## Preparing for Bit Manipulation Interviews

The patterns above cover roughly 90% of what appears in interviews. Before an interview where bit manipulation is likely (embedded roles, systems programming, Palantir, Jane Street), make sure you can:

1. Write `count_bits` using Kernighan's algorithm without thinking
2. Solve "single number" problems using XOR instantly
3. Explain two's complement and how it affects right shifts
4. Generate masks for arbitrary bit ranges

The candidates who struggle are usually tripped up not by the algorithms but by language-specific behavior (Python's arbitrary precision, Java's signed shift operators). Know your language's specific behavior cold.
