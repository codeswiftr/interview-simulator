---
title: "Number Theory Patterns for Coding Interviews"
description: "Master number theory for coding interviews: prime sieves, GCD/LCM, modular arithmetic, fast exponentiation, factorization, and the problems that actually appear on FAANG screens."
date: "2026-03-20"
category: "Algorithm Guides"
---

# Number Theory Patterns for Coding Interviews

Number theory problems appear with surprising frequency in technical interviews — not just at competitive programming shops, but at FAANG companies in phone screens and onsite rounds. They test mathematical reasoning, the ability to recognize structure, and attention to edge cases. This guide covers the patterns and implementations you need to handle any number theory question confidently.

## Prime Numbers and the Sieve of Eratosthenes

The Sieve of Eratosthenes is the canonical O(n log log n) algorithm for generating all primes up to n. Every engineer should be able to implement it from memory.

```python
def sieve(n):
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, n + 1, i):
                is_prime[j] = False
    return [i for i, v in enumerate(is_prime) if v]
```

**Key insight**: Start marking composites at `i*i`, not `2*i`. All smaller multiples were already marked by earlier primes.

**Segmented sieve**: When n is very large but you only need primes in a range `[L, R]`, generate primes up to `sqrt(R)` with the standard sieve, then use them to sieve the segment. This reduces memory from O(n) to O(sqrt(n) + (R-L)).

**Interview variant**: "Count primes less than n" (LeetCode 204). The sieve is the intended solution.

## GCD and LCM

The Euclidean algorithm computes GCD in O(log min(a, b)) time:

```python
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    return a * b // gcd(a, b)
```

In Python 3.9+, `math.gcd` and `math.lcm` are available. In interviews, implement from scratch unless told otherwise — it demonstrates you understand the algorithm.

**Extended Euclidean algorithm**: Computes x, y such that `ax + by = gcd(a, b)`. Used for modular inverse when the modulus is not prime:

```python
def extended_gcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x, y = extended_gcd(b, a % b)
    return g, y, x - (a // b) * y
```

**Common interview applications**: simplifying fractions, checking if two numbers are coprime (`gcd(a,b) == 1`), Bezout's identity problems.

## Modular Arithmetic

Modular arithmetic appears in nearly every counting problem at scale. The core identity:

```
(a + b) % m = ((a % m) + (b % m)) % m
(a * b) % m = ((a % m) * (b % m)) % m
(a - b) % m = ((a % m) - (b % m) + m) % m  # +m to handle negative
```

**Modular inverse**: When you need to divide under a modulus, multiply by the inverse instead. For prime modulus `p`, Fermat's Little Theorem gives `a^(p-2) mod p` as the inverse:

```python
MOD = 10**9 + 7

def mod_inverse(a, mod=MOD):
    return pow(a, mod - 2, mod)  # works when mod is prime
```

Python's built-in `pow(a, b, mod)` uses fast exponentiation — always prefer it over manual implementation in an interview.

**Modular combinations**: For counting problems involving nCr mod p, precompute factorials and inverse factorials:

```python
def precompute(n, mod=MOD):
    fact = [1] * (n + 1)
    for i in range(1, n + 1):
        fact[i] = fact[i-1] * i % mod
    inv_fact = [1] * (n + 1)
    inv_fact[n] = pow(fact[n], mod - 2, mod)
    for i in range(n - 1, -1, -1):
        inv_fact[i] = inv_fact[i+1] * (i+1) % mod
    return fact, inv_fact

def ncr(n, r, fact, inv_fact, mod=MOD):
    if r < 0 or r > n:
        return 0
    return fact[n] * inv_fact[r] % mod * inv_fact[n-r] % mod
```

## Fast Exponentiation (Binary Exponentiation)

Computing `a^n mod m` naively is O(n). Binary exponentiation reduces this to O(log n):

```python
def fast_pow(base, exp, mod):
    result = 1
    base %= mod
    while exp > 0:
        if exp & 1:
            result = result * base % mod
        base = base * base % mod
        exp >>= 1
    return result
```

Again, Python's `pow(base, exp, mod)` handles this natively. The value of knowing the algorithm is explaining it to an interviewer and recognizing when it's needed.

## Integer Factorization

**Trial division**: O(sqrt(n)) factorization, sufficient for n up to 10^12 in an interview:

```python
def factorize(n):
    factors = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors
```

**Number of divisors**: If `n = p1^a1 * p2^a2 * ...`, then divisor count = `(a1+1)(a2+1)...`. Sum of divisors follows a similar multiplicative formula.

**Smallest prime factor (SPF) sieve**: Precompute the smallest prime factor for every number up to n, enabling O(log n) factorization per query:

```python
def spf_sieve(n):
    spf = list(range(n + 1))
    for i in range(2, int(n**0.5) + 1):
        if spf[i] == i:  # i is prime
            for j in range(i*i, n + 1, i):
                if spf[j] == j:
                    spf[j] = i
    return spf
```

## Common Interview Problems

| Problem | Key Insight |
|---|---|
| Count Primes (LC 204) | Sieve of Eratosthenes |
| Ugly Number II (LC 264) | Merge 3 sorted multiples lists |
| Super Pow (LC 372) | Modular exponentiation |
| Factorial Trailing Zeros (LC 172) | Count factors of 5: `sum(n//5^i)` |
| Perfect Squares (LC 279) | BFS or Lagrange's four-square theorem |
| Broken Calculator (LC 991) | Work backwards: odd → +1, even → *2 |
| GCD of Strings (LC 1071) | `gcd(len(s), len(t))` prefix |

## Edge Cases to Never Miss

- GCD(0, n) = n — handle zero inputs
- Modular arithmetic: always add MOD before taking mod when subtracting
- Integer overflow in languages without arbitrary precision: use `long` in Java/C++, or reduce before multiplying
- `lcm(a, b)` can overflow: compute as `a / gcd(a, b) * b`, not `a * b / gcd(a, b)`

Number theory is one of those areas where a little systematic preparation pays off disproportionately. The implementations are compact, the patterns are reusable, and the problems tend to have elegant solutions once you recognize the structure. Spend a session implementing each algorithm from scratch and you'll have this category locked down.
