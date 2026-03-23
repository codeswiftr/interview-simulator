---
title: "Bit Manipulation Tricks for Coding Interviews"
description: "Essential bit manipulation patterns for interviews — XOR tricks, power of two checks, counting set bits, bit masking, and the 20 most common bitwise problems with explanations."
date: "2026-03-20"
category: "Algorithms"
---

# Bit Manipulation Tricks for Coding Interviews

Bit manipulation problems appear in interviews at companies that value low-level thinking — gaming companies, embedded systems teams, and FAANG's hardware-adjacent roles. Even for general SWE interviews, a handful of bit tricks appear regularly in medium-difficulty problems. This guide covers what you actually need and skips the academic fluff.

## Foundation: Bitwise Operators

```
a & b   — AND: 1 only if both 1
a | b   — OR: 1 if either 1
a ^ b   — XOR: 1 if exactly one is 1
~a      — NOT: flip all bits
a << n  — left shift: multiply by 2^n
a >> n  — right shift: divide by 2^n (arithmetic for signed, logical for unsigned)
```

## The Power of XOR

XOR is the most interesting operator for interviews because of two properties:
- `a ^ a = 0` (any number XOR'd with itself is 0)
- `a ^ 0 = a` (any number XOR'd with 0 is itself)
- XOR is commutative and associative

**Single number:** Given an array where every element appears twice except one, find the single element.

```python
def singleNumber(nums):
    result = 0
    for n in nums:
        result ^= n
    return result  # All pairs cancel; single element remains
```

**Find two non-repeating numbers:** Given an array where two elements appear once and all others appear twice.

```python
def singleNumberIII(nums):
    xor = 0
    for n in nums:
        xor ^= n
    # xor = a ^ b (the two unique numbers)
    # Find a bit that differs (any set bit in xor)
    diff_bit = xor & (-xor)  # Isolate rightmost set bit

    a = 0
    for n in nums:
        if n & diff_bit:
            a ^= n
    return [a, xor ^ a]
```

## Power of Two and Bit Counting

**Is power of two:** A power of two has exactly one set bit.

```python
def isPowerOfTwo(n):
    return n > 0 and (n & (n - 1)) == 0
# n & (n-1) clears the lowest set bit. If n is a power of two, nothing remains.
```

**Count set bits (Hamming weight):**

```python
def hammingWeight(n):
    count = 0
    while n:
        n &= (n - 1)  # Clear lowest set bit
        count += 1
    return count
```

**Number of bits to flip A to B:**

```python
def hammingDistance(x, y):
    return bin(x ^ y).count('1')
# XOR gives bits that differ; count the 1s
```

## Bit Masking Patterns

**Get bit i:** `(n >> i) & 1`
**Set bit i:** `n | (1 << i)`
**Clear bit i:** `n & ~(1 << i)`
**Toggle bit i:** `n ^ (1 << i)`
**Check if bit i is set:** `bool(n & (1 << i))`

These primitives appear in bitmask DP where each bit in an integer represents a boolean state (which nodes visited, which items selected).

## Isolate and Manipulate Lowest Set Bit

```python
lowest_bit = n & (-n)       # Isolate lowest set bit
n_without_lowest = n & (n - 1)  # Clear lowest set bit
```

The `n & (-n)` trick works because `-n` in two's complement is `~n + 1`. The `+1` propagates a carry through the trailing zeros, flipping them to 1 and the lowest set bit to 0. Then AND with `n` isolates just the lowest bit.

## Reverse Bits

```python
def reverseBits(n):
    result = 0
    for _ in range(32):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result
```

## Missing Number (XOR approach)

```python
def missingNumber(nums):
    n = len(nums)
    result = n  # Start with n
    for i, num in enumerate(nums):
        result ^= i ^ num  # XOR index and value; all pairs cancel
    return result
```

## Bitwise AND of Numbers in Range

"Given a range [left, right], return the bitwise AND of all numbers in that range."

Key insight: the AND of a range of numbers loses all bits below the position where `left` and `right` first differ.

```python
def rangeBitwiseAnd(left, right):
    shift = 0
    while left != right:
        left >>= 1
        right >>= 1
        shift += 1
    return left << shift
# Find common prefix (bits that never change in the range)
```

## Subset Generation with Bits

Enumerate all subsets of a set of n elements using bitmask:

```python
def all_subsets(nums):
    n = len(nums)
    for mask in range(1 << n):  # 0 to 2^n - 1
        subset = [nums[i] for i in range(n) if mask & (1 << i)]
        yield subset
```

This generates all 2^n subsets. The bitmask encodes which elements are included.

## Common Patterns Summary

| Problem | Technique |
|---------|-----------|
| Single unique element | XOR all elements |
| Is power of two? | `n & (n-1) == 0` |
| Count set bits | `n &= (n-1)` loop |
| Isolate lowest bit | `n & (-n)` |
| Clear lowest bit | `n & (n-1)` |
| All subsets | Enumerate `0` to `2^n - 1` |
| Bitmask state | Each bit = boolean flag |
| Swap two integers | `a^=b; b^=a; a^=b` |

## When to Reach for Bit Tricks

Use bit manipulation when:
- The problem involves "unique" or "appears N times" — XOR is likely
- The problem involves sets of booleans that need to be tracked compactly
- The input size allows bitmask enumeration (n ≤ 20 for bitmask DP, n ≤ 30 for meet-in-the-middle)
- The problem asks about individual bits or binary representations

The tricks that appear most in real interviews: XOR for unique elements, `n & (n-1)` for set-bit operations, and bitmask for subset enumeration. Master these and you've covered 80% of interview bit manipulation.
