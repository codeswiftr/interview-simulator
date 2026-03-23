---
title: "Bloom Filters & Probabilistic Data Structures for Interviews"
date: 2026-03-21
excerpt: "Understand Bloom filters, counting filters, and probabilistic data structures—when to trade accuracy for space efficiency."
tags: [algorithms, data-structures, bloom-filter, probabilistic, interview-prep]
---

# Bloom Filters & Probabilistic Data Structures for Interviews

Bloom filters answer "is this item possibly in the set?" with minimal space. They're essential for systems where false positives are acceptable but false negatives are not.

## How Bloom Filters Work

A Bloom filter is a bit array of m bits and k hash functions. To add an item:
1. Hash the item with all k functions
2. Set the bits at all k positions to 1

To query an item:
1. Hash with all k functions
2. If any bit is 0, the item is definitely not in the set
3. If all bits are 1, the item is probably in the set

## Implementation

```python
import mmh3
from bitarray import bitarray

class BloomFilter:
    def __init__(self, size, hash_count):
        self.size = size
        self.hash_count = hash_count
        self.bit_array = bitarray(size)
        self.bit_array.setall(0)
    
    def add(self, item):
        for i in range(self.hash_count):
            index = mmh3.hash(str(item), i) % self.size
            self.bit_array[index] = 1
    
    def check(self, item):
        for i in range(self.hash_count):
            index = mmh3.hash(str(item), i) % self.size
            if not self.bit_array[index]:
                return False
        return True
```

## Optimal Parameters

For n items and desired false positive rate p:

```
m = -n * ln(p) / (ln(2))²  # Optimal size
k = m / n * ln(2)          # Optimal hash count
```

```python
import math

def optimal_params(n, p):
    m = int(-n * math.log(p) / (math.log(2) ** 2))
    k = int(m / n * math.log(2))
    return m, k
```

## Counting Bloom Filter

Standard Bloom filters don't support deletion. Counting Bloom filters replace bits with counters:

```python
class CountingBloomFilter:
    def __init__(self, size, hash_count):
        self.size = size
        self.hash_count = hash_count
        self.counters = [0] * size
    
    def add(self, item):
        for i in range(self.hash_count):
            index = mmh3.hash(str(item), i) % self.size
            self.counters[index] += 1
    
    def remove(self, item):
        if not self.check(item):
            return False
        for i in range(self.hash_count):
            index = mmh3.hash(str(item), i) % self.size
            self.counters[index] -= 1
        return True
    
    def check(self, item):
        for i in range(self.hash_count):
            index = mmh3.hash(str(item), i) % self.size
            if self.counters[index] == 0:
                return False
        return True
```

## Applications

1. **Web caches:** Avoid disk lookups for non-existent pages
2. **Databases:** Bloom filters on SSTables (LevelDB, Cassandra)
3. **Spell checkers:** Quick rejection of unknown words
4. **Network routing:** Avoid routing loops

## Other Probabilistic Structures

### HyperLogLog
Estimate cardinality (unique count) in O(log log n) space:

```python
class HyperLogLog:
    def __init__(self, precision=14):
        self.precision = precision
        self.registers = [0] * (1 << precision)
    
    def add(self, item):
        h = mmh3.hash64(str(item))[0]
        index = h & ((1 << self.precision) - 1)
        h >>= self.precision
        self.registers[index] = max(self.registers[index], 
                                     self._count_leading_zeros(h) + 1)
    
    def _count_leading_zeros(self, x):
        if x == 0:
            return 64
        count = 0
        while (x & (1 << 63)) == 0:
            x <<= 1
            count += 1
        return count
```

## Interview Tips

1. **Clarify requirements.** Bloom filters trade accuracy for space—make sure that's acceptable.

2. **Discuss alternatives.** Hash sets for exact membership, tries for prefix queries.

3. **Common follow-ups:** "How to resize?" "Handle deletion?" "Distributed Bloom filters?"

4. **Real examples.** Google Bigtable, Apache Cassandra, Reddit's URL deduplication.
