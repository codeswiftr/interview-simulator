---
title: "String Algorithms Interview Guide: KMP, Rabin-Karp, and Pattern Matching"
description: "Master string algorithm interviews with KMP, Rabin-Karp rolling hash, Z-algorithm, trie, and pattern matching templates in Python."
date: "2026-03-20"
category: "Algorithm Guides"
---

# String Algorithms Interview Guide: KMP, Rabin-Karp, and Pattern Matching

String algorithms appear in interviews at companies where text processing matters — search engines, compilers, genomics, security. The questions range from basic pattern matching to building tries for autocomplete. Understanding the underlying mechanics of each algorithm — not just the code — is what distinguishes candidates.

## String Hashing

Polynomial rolling hash maps a string to an integer, enabling O(1) equality checks after O(n) preprocessing. The foundation of Rabin-Karp and many sliding window problems.

```python
def string_hash(s, base=31, mod=10**9+7):
    h = 0
    power = 1
    for c in s:
        h = (h + (ord(c) - ord('a') + 1) * power) % mod
        power = (power * base) % mod
    return h
```

For substring hashing, precompute prefix hashes and powers to get hash of any substring in O(1):

```python
def build_prefix_hash(s, base=31, mod=10**9+7):
    n = len(s)
    prefix = [0] * (n + 1)
    power = [1] * (n + 1)
    for i in range(n):
        prefix[i+1] = (prefix[i] + (ord(s[i]) - ord('a') + 1) * power[i]) % mod
        power[i+1] = (power[i] * base) % mod
    return prefix, power

def get_hash(prefix, power, l, r, mod=10**9+7):
    return (prefix[r+1] - prefix[l] * power[r-l+1]) % mod
```

Double hashing (two different mod values) reduces collision probability to near-zero for competitive reliability.

## Rabin-Karp: Rolling Hash Pattern Matching

Rabin-Karp slides a hash window across the text, comparing hash values before character-by-character verification. Average O(n + m); O(nm) worst case due to collisions.

```python
def rabin_karp(text, pattern):
    n, m = len(text), len(pattern)
    base, mod = 31, 10**9+7
    
    def hash_str(s):
        h, p = 0, 1
        for c in s:
            h = (h + ord(c) * p) % mod
            p = (p * base) % mod
        return h, p
    
    ph, _ = hash_str(pattern)
    th, tp = hash_str(text[:m])
    results = []
    
    if ph == th and text[:m] == pattern:
        results.append(0)
    
    for i in range(1, n - m + 1):
        th = (th - ord(text[i-1])) % mod
        th = (th * pow(base, mod-2, mod)) % mod  # modular inverse
        th = (th + ord(text[i+m-1]) * tp) % mod
        if th == ph and text[i:i+m] == pattern:
            results.append(i)
    return results
```

In practice, the additive rolling hash (subtract outgoing character, add incoming character divided by power) is simpler to implement correctly. Know both forms.

## KMP: Knuth-Morris-Pratt

KMP achieves guaranteed O(n + m) by precomputing a failure function that tells you how far to fall back in the pattern without restarting.

The failure function (also called prefix function or LPS — Longest Proper Prefix which is also Suffix):

```python
def build_failure(pattern):
    m = len(pattern)
    fail = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and pattern[i] != pattern[j]:
            j = fail[j-1]
        if pattern[i] == pattern[j]:
            j += 1
        fail[i] = j
    return fail

def kmp_search(text, pattern):
    fail = build_failure(pattern)
    results = []
    j = 0
    for i, c in enumerate(text):
        while j > 0 and c != pattern[j]:
            j = fail[j-1]
        if c == pattern[j]:
            j += 1
        if j == len(pattern):
            results.append(i - len(pattern) + 1)
            j = fail[j-1]
    return results
```

Interview insight: the failure function itself encodes all proper prefix-suffix relationships of the pattern. KMP is also used to find the shortest repeating unit of a string: if `n % (n - fail[n-1]) == 0`, the string is a repetition of its first `n - fail[n-1]` characters.

## Z-Algorithm

The Z-array for string `s` stores at each position `i` the length of the longest substring starting at `i` that is also a prefix of `s`. Z[0] is conventionally 0 or n.

```python
def z_function(s):
    n = len(s)
    z = [0] * n
    l, r = 0, 0
    for i in range(1, n):
        if i < r:
            z[i] = min(r - i, z[i - l])
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        if i + z[i] > r:
            l, r = i, i + z[i]
    return z
```

Pattern matching with Z: concatenate `pattern + '$' + text`, compute Z-array. Any position where Z-value equals `len(pattern)` is a match. The `$` separator prevents matches that span the boundary.

## Trie for String Problems

A trie (prefix tree) enables O(m) insert and search where m is string length. Essential for autocomplete, spell checking, and problems involving common prefixes.

```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        node = self.root
        for c in word:
            if c not in node.children:
                node.children[c] = TrieNode()
            node = node.children[c]
        node.is_end = True
    
    def search(self, word):
        node = self.root
        for c in word:
            if c not in node.children:
                return False
            node = node.children[c]
        return node.is_end
    
    def starts_with(self, prefix):
        node = self.root
        for c in prefix:
            if c not in node.children:
                return False
            node = node.children[c]
        return True
```

For XOR problems (Maximum XOR of Two Numbers in an Array), build a binary trie — each node has children `0` and `1`.

## Common LeetCode String Patterns

| Pattern | Technique | Example Problems |
|---|---|---|
| Pattern matching | KMP / Rabin-Karp | Find All Anagrams, Repeated Substring Pattern |
| Common prefix | Trie | Word Search II, Replace Words |
| Sliding window + count | HashMap | Minimum Window Substring, Permutation in String |
| Palindrome detection | Manacher / expand | Longest Palindromic Substring |
| Anagram grouping | Sort-as-key / hash | Group Anagrams |
| String construction | Stack | Decode String, Remove Duplicate Letters |

## Suffix Arrays (Conceptual)

A suffix array is a sorted array of all suffixes of a string. Building one in O(n log n) is interview-level knowledge at top companies (Google, Jane Street). The key insight: sort suffixes in rounds, doubling the compared prefix length each time. Combined with the LCP array, suffix arrays solve substring search, longest repeated substring, and longest common substring in O(n) or O(n log n).

For most interviews, you won't need to implement suffix arrays from scratch — but knowing they exist, what they solve, and their complexity demonstrates depth that impresses senior interviewers.

String algorithm mastery is not about memorizing code. It is about understanding why each algorithm works — the invariants maintained, the guarantees provided, and the tradeoffs accepted.
