---
title: "LRU Cache: Implementation, Variants, and Interview Patterns"
description: "LRU cache implementation with doubly linked list and hash map, LFU cache, cache eviction policies comparison, and the system design patterns caches enable."
date: "2026-03-20"
category: "Algorithms"
---

# LRU Cache: Implementation, Variants, and Interview Patterns

LRU cache is one of the most asked implementation questions in senior interviews. Beyond the implementation itself, it's a vehicle for testing data structure design (combining a hash map with a doubly linked list), O(1) constraint satisfaction, and understanding cache design in system contexts. This guide covers the implementation, the variants, and the system-level thinking that distinguishes senior candidates.

## LRU Cache: The Constraints

- `get(key)`: Return the value if key exists, otherwise -1. O(1).
- `put(key, value)`: Insert or update the key. If capacity is exceeded, evict the Least Recently Used item. O(1).

O(1) for both operations is the critical constraint. A naive approach (sorted list + hash map) doesn't achieve O(1) eviction because finding the LRU item requires scanning.

## The Data Structure: Doubly Linked List + Hash Map

A doubly linked list maintains order (most recent at head, LRU at tail). The hash map gives O(1) access to any node. Together: O(1) access, O(1) insertion at head, O(1) deletion anywhere (since we have the node directly from the hash map).

```python
class Node:
    def __init__(self, key=0, val=0):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}  # key -> Node

        # Sentinel nodes to avoid edge cases
        self.head = Node()  # Most recently used side
        self.tail = Node()  # Least recently used side
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _insert_at_head(self, node):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    def get(self, key):
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self._remove(node)
        self._insert_at_head(node)
        return node.val

    def put(self, key, value):
        if key in self.cache:
            self._remove(self.cache[key])

        node = Node(key, value)
        self.cache[key] = node
        self._insert_at_head(node)

        if len(self.cache) > self.capacity:
            # Evict from tail
            lru = self.tail.prev
            self._remove(lru)
            del self.cache[lru.key]
```

The sentinel nodes (`head` and `tail`) eliminate edge cases for inserting into an empty list or removing the only node. This is a clean interview technique worth using.

## Python Shortcut: OrderedDict

Python's `collections.OrderedDict` maintains insertion order and allows moving items to the end in O(1). This makes LRU trivially implementable in Python — but interviewers may ask you to implement it without this shortcut.

```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key):
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
```

Clarify with the interviewer which version they want. The OrderedDict version demonstrates Python knowledge; the manual version demonstrates data structure understanding.

## LFU Cache: Least Frequently Used

LFU evicts the key with the lowest access frequency (ties broken by LRU). More complex than LRU — requires tracking frequency per key, multiple buckets of keys by frequency, and the minimum frequency.

```python
from collections import defaultdict, OrderedDict

class LFUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.min_freq = 0
        self.key_to_val = {}       # key -> val
        self.key_to_freq = {}      # key -> frequency
        self.freq_to_keys = defaultdict(OrderedDict)  # freq -> OrderedDict of keys

    def _update_freq(self, key):
        freq = self.key_to_freq[key]
        del self.freq_to_keys[freq][key]
        if not self.freq_to_keys[freq] and freq == self.min_freq:
            self.min_freq += 1
        self.key_to_freq[key] = freq + 1
        self.freq_to_keys[freq + 1][key] = None

    def get(self, key):
        if key not in self.key_to_val:
            return -1
        self._update_freq(key)
        return self.key_to_val[key]

    def put(self, key, value):
        if self.capacity <= 0:
            return
        if key in self.key_to_val:
            self.key_to_val[key] = value
            self._update_freq(key)
        else:
            if len(self.key_to_val) >= self.capacity:
                # Evict LFU (and LRU among ties)
                evict_key, _ = self.freq_to_keys[self.min_freq].popitem(last=False)
                del self.key_to_val[evict_key]
                del self.key_to_freq[evict_key]
            self.key_to_val[key] = value
            self.key_to_freq[key] = 1
            self.freq_to_keys[1][key] = None
            self.min_freq = 1
```

## Eviction Policy Comparison

| Policy | Evicts | Best for | Weakness |
|--------|--------|----------|----------|
| LRU | Least recently used | General-purpose | Scan resistance (one-time scan pollutes cache) |
| LFU | Least frequently used | Skewed frequency access | Cache pollution from past popular items |
| ARC (Adaptive Replacement Cache) | Balanced LRU + LFU | Adaptive workloads | Complex to implement |
| FIFO | Oldest inserted | Simple caches | Ignores access patterns |
| Random | Random eviction | Very simple, approximates LRU | Non-deterministic |

Real databases (PostgreSQL's buffer pool) use variants of LRU with "clock" or "second chance" algorithms for efficiency.

## System Design: When Cache Eviction Matters

In system design interviews, eviction policy discussion matters when:
- You're caching user session data (LRU: recently active users are more likely to be active again)
- You're caching database query results (LFU: popular queries should stay cached)
- You're designing a CDN cache (LRU with large capacity; eviction rarely occurs)
- You're caching ML model predictions (LFU: popular inputs benefit most from caching)

The key insight: cache hit rate is the primary metric. The best eviction policy maximizes hit rate for your specific access pattern. LRU is the safe default; consider LFU when frequency matters more than recency.

## Thread Safety

The implementations above are not thread-safe. For a multi-threaded cache:
- Add a `threading.Lock` around all operations, or
- Use separate locks per bucket (reduces contention), or
- Use a lock-free structure (complex, rarely needed in interviews)

For distributed caches (Redis), thread safety is handled by Redis's single-threaded event loop.
