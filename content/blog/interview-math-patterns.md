---
title: "Math-Based Coding Interview Problems: Patterns and Tricks"
description: "A practical guide to math-based coding interview problems: digit counting, palindrome numbers, reverse integer, missing number, single number XOR, and power of two/three/four."
date: "2026-03-20"
category: "Algorithm Guides"
---

# Math-Based Coding Interview Problems: Patterns and Tricks

Math-based problems appear in every tier of technical interview, from phone screens to onsite rounds. They're deceptively approachable — the implementations are short, but the edge cases are brutal and the optimal solutions often require a mathematical insight that doesn't come from brute force. This guide covers the most common patterns with the key observations that unlock each one.

## Digit Manipulation

### Counting Digits

How many digits does n have? `floor(log10(n)) + 1`. But in an interview, simpler is better:

```python
def digit_count(n):
    return len(str(abs(n)))
```

Beware: `log10(0)` is undefined. Handle zero explicitly.

**Digit sum**: `sum(int(d) for d in str(n))`. Repeatedly applying digit sum until you get a single digit is equivalent to `n % 9` (with 9 mapping to 9, not 0).

### Reverse Integer (LC 7)

```python
def reverse(x):
    sign = -1 if x < 0 else 1
    x = abs(x)
    rev = int(str(x)[::-1])
    rev *= sign
    if rev < -(2**31) or rev > 2**31 - 1:
        return 0
    return rev
```

The 32-bit overflow check is the entire point of this problem. In Python, integers don't overflow naturally — you must add the explicit bounds check. In Java/C++, the overflow happens silently, requiring a different approach (check before multiplying).

### Palindrome Number (LC 9)

The constraint "without converting to string" makes this a digit problem:

```python
def isPalindrome(x):
    if x < 0 or (x % 10 == 0 and x != 0):
        return False
    reversed_half = 0
    while x > reversed_half:
        reversed_half = reversed_half * 10 + x % 10
        x //= 10
    return x == reversed_half or x == reversed_half // 10
```

**Key insight**: You only need to reverse half the number. When `reversed_half >= x`, you've processed half the digits. The `x == reversed_half // 10` check handles odd-length numbers (the middle digit doesn't matter).

## Bit Manipulation for Math Problems

### Single Number (LC 136)

Find the element that appears once when all others appear twice:

```python
def singleNumber(nums):
    result = 0
    for n in nums:
        result ^= n
    return result
```

**Why XOR works**: `a ^ a = 0` and `a ^ 0 = a`. All pairs cancel. The remaining value is the single number.

### Single Number II (LC 137)

All elements appear three times except one. XOR alone doesn't work here. Use bit counting:

```python
def singleNumber(nums):
    ones, twos = 0, 0
    for n in nums:
        ones = (ones ^ n) & ~twos
        twos = (twos ^ n) & ~ones
    return ones
```

This uses two bitmasks as a state machine — each bit's count mod 3 is tracked in (twos, ones). When count reaches 3, both bits reset to 0.

### Missing Number (LC 268)

Find the missing number in [0, n]:

```python
# XOR approach
def missingNumber(nums):
    n = len(nums)
    result = n
    for i, num in enumerate(nums):
        result ^= i ^ num
    return result

# Math approach (simpler to explain)
def missingNumber(nums):
    n = len(nums)
    return n * (n + 1) // 2 - sum(nums)
```

In an interview, the math approach (expected sum minus actual sum) is easier to explain and just as correct. Know both — the interviewer might ask for a follow-up without using division.

## Power of Two, Three, Four

These problems have constant-time solutions that interviewers specifically want:

### Power of Two (LC 231)

```python
def isPowerOfTwo(n):
    return n > 0 and (n & (n - 1)) == 0
```

**Insight**: Powers of two have exactly one bit set. Subtracting 1 flips all bits below that position. ANDing gives 0.

### Power of Three (LC 326)

```python
def isPowerOfThree(n):
    return n > 0 and 1162261467 % n == 0
```

`1162261467 = 3^19`, the largest power of 3 that fits in a 32-bit integer. If n is a power of 3, it must divide the maximum power of 3. This works because 3 is prime — an analogous trick doesn't work for non-prime bases (e.g., `12 % 4 == 0` but 4 is not a power of 6).

### Power of Four (LC 342)

```python
def isPowerOfFour(n):
    return n > 0 and (n & (n - 1)) == 0 and (n & 0xAAAAAAAA) == 0
```

First condition: positive. Second: power of two (single bit set). Third: that bit is in an odd position (positions 0, 2, 4, ... counting from 0). `0xAAAAAAAA` in binary is `...10101010` — masking with it leaves only even-position bits. If the result is 0, the bit is in an odd position (valid power of 4).

## Number Decomposition Problems

### Excel Column Title (LC 168)

Convert column number to title (1→"A", 26→"Z", 27→"AA"):

```python
def convertToTitle(n):
    result = ""
    while n:
        n -= 1  # adjust to 0-indexed: 1→0, 26→25
        result = chr(ord('A') + n % 26) + result
        n //= 26
    return result
```

The `n -= 1` before each digit extraction is the critical insight. This is essentially base-26 with no zero — forcing 0-indexing before modding handles the "Z" case correctly.

### Happy Number (LC 202)

A number is happy if repeatedly replacing it with the sum of squares of its digits eventually reaches 1:

```python
def isHappy(n):
    slow = n
    fast = _next(n)
    while fast != 1 and slow != fast:
        slow = _next(slow)
        fast = _next(_next(fast))
    return fast == 1

def _next(n):
    total = 0
    while n:
        total += (n % 10) ** 2
        n //= 10
    return total
```

Unhappy numbers enter a cycle. Floyd's cycle detection (slow/fast pointers) detects the cycle without a hash set. Alternative: use a set and check if 1 or any known cycle number is hit.

### Ugly Number II (LC 264)

The nth ugly number (only prime factors 2, 3, 5):

```python
def nthUglyNumber(n):
    ugly = [1] * n
    i2 = i3 = i5 = 0
    for i in range(1, n):
        next2 = ugly[i2] * 2
        next3 = ugly[i3] * 3
        next5 = ugly[i5] * 5
        ugly[i] = min(next2, next3, next5)
        if ugly[i] == next2: i2 += 1
        if ugly[i] == next3: i3 += 1
        if ugly[i] == next5: i5 += 1
    return ugly[-1]
```

**Pattern**: Three virtual sorted lists (multiples of 2, 3, 5). Merge them lazily with three pointers. This generalizes to any set of multipliers.

## Common Math Interview Patterns

| Problem | Key Observation |
|---|---|
| Factorial Trailing Zeros | Count pairs of (2,5) — count factors of 5: Σ floor(n/5^k) |
| Sqrt(x) without sqrt | Binary search on [0, x] or Newton's method |
| Divide Without Division | Bit shifting: x >> 1 = x/2 |
| Roman to Integer | If current value < next value, subtract; else add |
| Count Bits (LC 338) | `dp[i] = dp[i >> 1] + (i & 1)` |
| Nth Digit (LC 400) | Count digits in each range: 1-digit (9), 2-digit (90), etc. |

## Edge Cases That Sink Candidates

**Negative numbers**: `isPalindrome(-121)` → false. Always handle negative inputs.

**Zero and one**: Power-of-anything questions: is 0 a valid input? Is 1 (= n^0) included? Read the constraints.

**Integer overflow**: In Java/C++, `Integer.MAX_VALUE + 1` wraps to negative. In Python, this doesn't happen — but interviewers may specifically ask for a solution that would work in a 32-bit context.

**Floating point precision**: `math.sqrt(4) == 2.0` returns True in Python, but `math.sqrt(2)**2 == 2` might not. For integer sqrt problems, use integer arithmetic or binary search.

Math problems are often underestimated in preparation, which means they're an opportunity to differentiate. The candidates who nail these cold — without fumbling through trial division or missing the XOR insight — stand out. Build the muscle memory now.
