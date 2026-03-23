---
title: "Bit Manipulation Interview Guide: XOR Tricks, Bitmasking, and Common Patterns"
description: "Bit manipulation interview problems explained — XOR properties, bit counting, bitmask DP, power-of-two tricks, and how to approach bit-level problems with confidence."
date: "2026-03-20"
category: "Algorithms"
---

# Bit Manipulation Interview Guide: XOR Tricks, Bitmasking, and Common Patterns

Bit manipulation problems appear in technical interviews at all levels. They're compact, require specific knowledge, and reward candidates who understand binary arithmetic. This guide covers the patterns that appear most frequently.

## Essential Bit Operations

Know these operations cold:

| Operation | Syntax (Python) | Use |
|-----------|-----------------|-----|
| AND | `a & b` | Clear bits, check if bit is set |
| OR | `a \| b` | Set bits |
| XOR | `a ^ b` | Toggle bits, find difference |
| NOT | `~a` | Flip all bits |
| Left shift | `a << n` | Multiply by 2^n |
| Right shift | `a >> n` | Divide by 2^n |

**Check if bit k is set:** `(n >> k) & 1`
**Set bit k:** `n | (1 << k)`
**Clear bit k:** `n & ~(1 << k)`
**Toggle bit k:** `n ^ (1 << k)`
**Remove lowest set bit:** `n & (n - 1)` — this is the most useful trick

## XOR Properties

XOR is the most interesting operator for interviews because of its mathematical properties:
- `a ^ a = 0` (XOR with itself = 0)
- `a ^ 0 = a` (XOR with 0 = identity)
- XOR is commutative and associative

These properties power many interview problems:

**Find the single non-duplicate:** Given an array where every element appears twice except one, XOR all elements. The pairs cancel out (a ^ a = 0), leaving the single element.

```python
def single_number(nums):
    result = 0
    for n in nums:
        result ^= n
    return result
```

**Find two missing/extra numbers:** If two elements appear once in an array of pairs, XOR all gives `a ^ b`. Find any set bit in the result (they differ there), partition the array on that bit, XOR each partition — you get each number separately.

**Swap without temp:** `a ^= b; b ^= a; a ^= b` — cute but don't use in production.

## Power of Two Checks

`n & (n-1) == 0` checks if n is a power of two (and n > 0). Why: powers of two have exactly one set bit. Subtracting 1 flips all lower bits. AND with original clears the only set bit → zero.

```python
def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0
```

Related: `n & (n-1)` removes the lowest set bit. Use in Brian Kernighan's algorithm to count set bits in O(number of set bits) instead of O(32).

```python
def count_bits(n):
    count = 0
    while n:
        n &= n - 1  # remove lowest set bit
        count += 1
    return count
```

## Bitmask for Subset Problems

Bitmasks represent subsets: for n items, each number from 0 to 2^n-1 represents a unique subset. Bit i set means item i is included.

This enables O(2^n * n) solutions for small n (n ≤ 20):

```python
n = len(items)
for mask in range(1 << n):  # iterate all 2^n subsets
    subset = [items[i] for i in range(n) if mask & (1 << i)]
```

**Bitmask DP** — common for problems involving "which elements have been visited/used":
- Traveling Salesman Problem (TSP): `dp[mask][i]` = min cost to visit all cities in `mask`, ending at city i
- Minimum XOR of subsets: iterate masks, build from smaller submasks

## Common Interview Problems

**Number of 1 Bits:** Use `n & (n-1)` to strip bits.

**Reverse Bits:** Process each bit from LSB, shift into result from MSB.

**Sum of Two Integers Without + Operator:** Use XOR for sum without carry, AND + left shift for the carry. Repeat until carry is zero.

```python
def get_sum(a, b):
    mask = 0xFFFFFFFF  # 32-bit mask
    while b & mask:
        carry = (a & b) << 1
        a = a ^ b
        b = carry
    return a if b == 0 else a & mask
```

**Single Number III:** Two unique numbers in an array of pairs. XOR all → `a ^ b`. Find a set bit. Partition by that bit. XOR each partition.

**Maximum XOR of Two Numbers in Array:** Use a trie to greedily build each number's maximum XOR partner in O(n * 32) = O(n).

## Communicating Bit Problems

Bit problems often have elegant O(1) or O(n) solutions that aren't obvious. When you see a problem mentioning XOR, powers of two, or bit counting, explicitly state that you're looking for a bitwise approach before coding.

Walk through an example in binary: "If n = 12 = 1100 in binary, then n-1 = 1011, so n & (n-1) = 1000." Showing binary explicitly in your explanation demonstrates that you understand what the operation is actually doing, not just pattern-matching to a formula.
