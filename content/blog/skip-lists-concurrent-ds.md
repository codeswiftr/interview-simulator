---
title: "Skip Lists: Concurrent Data Structures for Interviews"
date: 2026-03-21
excerpt: "Master skip lists—the probabilistic alternative to balanced trees with excellent concurrent access properties."
tags: [algorithms, data-structures, skip-lists, concurrency, interview-prep]
---

# Skip Lists: Concurrent Data Structures for Interviews

Skip lists are probabilistic data structures that provide O(log n) operations like balanced trees but with simpler implementation and better concurrent access properties.

## How Skip Lists Work

A skip list has multiple layers of linked lists. The bottom layer contains all elements. Each higher layer acts as an "express lane," containing a subset of elements.

```
Layer 3: HEAD -------------------------> 50 -------------------------> NIL
Layer 2: HEAD ---------> 25 ---------> 50 ---------> 75 ---------> NIL
Layer 1: HEAD -> 10 -> 25 -> 30 -> 50 -> 60 -> 75 -> 80 -> 90 -> NIL
```

## Basic Implementation

```python
import random

class SkipNode:
    def __init__(self, value=None, levels=0):
        self.value = value
        self.forward = [None] * levels

class SkipList:
    def __init__(self, max_levels=16, p=0.5):
        self.max_levels = max_levels
        self.p = p
        self.level = 1
        self.head = SkipNode(levels=max_levels)
    
    def random_level(self):
        level = 1
        while random.random() < self.p and level < self.max_levels:
            level += 1
        return level
    
    def search(self, value):
        current = self.head
        for i in range(self.level - 1, -1, -1):
            while current.forward[i] and current.forward[i].value < value:
                current = current.forward[i]
        current = current.forward[0]
        return current if current and current.value == value else None
    
    def insert(self, value):
        update = [None] * self.max_levels
        current = self.head
        
        for i in range(self.level - 1, -1, -1):
            while current.forward[i] and current.forward[i].value < value:
                current = current.forward[i]
            update[i] = current
        
        new_level = self.random_level()
        if new_level > self.level:
            for i in range(self.level, new_level):
                update[i] = self.head
            self.level = new_level
        
        new_node = SkipNode(value, new_level)
        for i in range(new_level):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
    
    def delete(self, value):
        update = [None] * self.max_levels
        current = self.head
        
        for i in range(self.level - 1, -1, -1):
            while current.forward[i] and current.forward[i].value < value:
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        if current and current.value == value:
            for i in range(self.level):
                if update[i].forward[i] != current:
                    break
                update[i].forward[i] = current.forward[i]
            
            while self.level > 1 and not self.head.forward[self.level - 1]:
                self.level -= 1
```

## Concurrent Skip List

The key advantage of skip lists is lock-free or fine-grained locking for concurrent access:

```python
import threading

class ConcurrentSkipList:
    def __init__(self, max_levels=16):
        self.max_levels = max_levels
        self.level = 1
        self.head = SkipNode(levels=max_levels)
        self.locks = [threading.Lock() for _ in range(max_levels)]
    
    def search(self, value):
        current = self.head
        for i in range(self.level - 1, -1, -1):
            while current.forward[i] and current.forward[i].value < value:
                current = current.forward[i]
        current = current.forward[0]
        return current if current and current.value == value else None
    
    def insert(self, value):
        update = [None] * self.max_levels
        current = self.head
        
        # Find positions (read-only, no locks needed)
        for i in range(self.level - 1, -1, -1):
            while current.forward[i] and current.forward[i].value < value:
                current = current.forward[i]
            update[i] = current
        
        new_level = self.random_level()
        
        # Lock affected levels
        for i in range(new_level):
            self.locks[i].acquire()
        
        try:
            new_node = SkipNode(value, new_level)
            for i in range(new_level):
                new_node.forward[i] = update[i].forward[i]
                update[i].forward[i] = new_node
            
            if new_level > self.level:
                self.level = new_level
        finally:
            for i in range(new_level):
                self.locks[i].release()
```

## Skip Lists vs Balanced Trees

| Property | Skip List | Red-Black Tree |
|----------|-----------|----------------|
| Implementation | Simple | Complex |
| Concurrency | Easy to parallelize | Rebalancing complicates locking |
| Memory | More pointers | Less overhead |
| Deterministic | Probabilistic O(log n) | Guaranteed O(log n) |

## Interview Tips

1. **Explain the probability.** Each level contains roughly half the elements of the level below, giving O(log n) expected search.

2. **Concurrency angle.** Skip lists are used in Java's ConcurrentSkipListMap, Redis for sorted sets.

3. **Common follow-ups:** "Compare with B-trees," "Implement range queries," "Handle duplicates."

4. **Real applications.** LevelDB uses skip lists for memtables, Apache Lucene for term dictionaries.

## Time Complexity

All operations (search, insert, delete): O(log n) expected, O(n) worst case

Space Complexity: O(n) expected
