---
title: "LRU Cache Implementation & Variants: LFU, TTL Cache Design"
date: 2026-03-21
excerpt: "Master cache implementations for system design interviews—LRU, LFU, TTL caches with production-ready code patterns."
tags: [algorithms, data-structures, caching, system-design, interview-prep]
---

# LRU Cache Implementation & Variants: LFU, TTL Cache Design

Cache implementation is a staple of system design and coding interviews. Understanding LRU and its variants demonstrates your grasp of data structures and practical system constraints.

## LRU Cache

Least Recently Used evicts the item not accessed for the longest time. The classic implementation combines a hash map with a doubly linked list.

```python
class Node:
    def __init__(self, key=0, value=0):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.head = Node()  # Dummy head
        self.tail = Node()  # Dummy tail
        self.head.next = self.tail
        self.tail.prev = self.head
    
    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev
    
    def _add_to_front(self, node):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node
    
    def get(self, key):
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self._remove(node)
        self._add_to_front(node)
        return node.value
    
    def put(self, key, value):
        if key in self.cache:
            node = self.cache[key]
            node.value = value
            self._remove(node)
            self._add_to_front(node)
        else:
            if len(self.cache) >= self.capacity:
                lru = self.tail.prev
                self._remove(lru)
                del self.cache[lru.key]
            node = Node(key, value)
            self.cache[key] = node
            self._add_to_front(node)
```

## LFU Cache

Least Frequently Used evicts the item with the lowest access count. Tie-breaking usually uses recency.

```python
from collections import defaultdict, OrderedDict

class LFUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.min_freq = 0
        self.key_to_val = {}
        self.key_to_freq = {}
        self.freq_to_keys = defaultdict(OrderedDict)
    
    def get(self, key):
        if key not in self.key_to_val:
            return -1
        
        freq = self.key_to_freq[key]
        self.key_to_freq[key] = freq + 1
        
        del self.freq_to_keys[freq][key]
        self.freq_to_keys[freq + 1][key] = None
        
        if not self.freq_to_keys[freq]:
            if freq == self.min_freq:
                self.min_freq += 1
        
        return self.key_to_val[key]
    
    def put(self, key, value):
        if self.capacity <= 0:
            return
        
        if key in self.key_to_val:
            self.key_to_val[key] = value
            self.get(key)  # Update frequency
            return
        
        if len(self.key_to_val) >= self.capacity:
            old_key, _ = self.freq_to_keys[self.min_freq].popitem(last=False)
            del self.key_to_val[old_key]
            del self.key_to_freq[old_key]
        
        self.key_to_val[key] = value
        self.key_to_freq[key] = 1
        self.freq_to_keys[1][key] = None
        self.min_freq = 1
```

## TTL Cache

Time-To-Live caches automatically expire entries after a duration:

```python
import time

class TTLCache:
    def __init__(self, capacity, ttl_seconds):
        self.capacity = capacity
        self.ttl = ttl_seconds
        self.cache = {}  # key -> (value, expiration_time)
        self.access_order = OrderedDict()
    
    def _cleanup(self):
        current = time.time()
        expired = [k for k, (_, exp) in self.cache.items() if current > exp]
        for k in expired:
            del self.cache[k]
            del self.access_order[k]
    
    def get(self, key):
        self._cleanup()
        if key not in self.cache:
            return None
        self.access_order.move_to_end(key)
        return self.cache[key][0]
    
    def put(self, key, value):
        self._cleanup()
        if key in self.cache:
            del self.cache[key]
            del self.access_order[key]
        elif len(self.cache) >= self.capacity:
            oldest, _ = self.access_order.popitem(last=False)
            del self.cache[oldest]
        
        expiration = time.time() + self.ttl
        self.cache[key] = (value, expiration)
        self.access_order[key] = None
```

## Interview Tips

1. **Explain trade-offs.** LRU is simple but may not handle frequency patterns. LFU handles hot items but is more complex.

2. **Thread safety.** Production caches need locks. Mention ConcurrentHashMap-style optimizations.

3. **Distributed caching.** Discuss consistent hashing for distributed caches.

4. **Common follow-ups:** "Implement with O(1) operations," "Handle concurrent access," "Design a distributed cache."

## Time Complexity

All operations (get, put): O(1)
