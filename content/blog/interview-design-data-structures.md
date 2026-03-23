---
title: "Design Custom Data Structures: Interview Problems and Patterns"
description: "How to design custom data structures in coding interviews — median finder, LFU cache, stack with min, iterator design, random set, and the patterns that enable O(1) operations on complex structures."
date: "2026-03-20"
category: "Algorithms"
---

# Design Custom Data Structures: Interview Problems and Patterns

Data structure design problems test whether you can combine primitive data structures (arrays, hash maps, heaps, linked lists) to achieve operations with specific time complexity constraints. These problems appear at senior-level interviews and require creative thinking about which structures complement each other's strengths.

## Pattern: Use Multiple Structures Together

The core insight in most data structure design problems: no single primitive data structure satisfies all the required operations. The solution is to combine two or more structures, keeping them synchronized on updates, so each structure handles the queries it's best at.

## Problem 1: Stack with Min/Max in O(1)

"Design a stack that supports push, pop, and getMin in O(1)."

```python
class MinStack:
    def __init__(self):
        self.stack = []
        self.min_stack = []  # Parallel stack of minimums

    def push(self, val):
        self.stack.append(val)
        min_val = val if not self.min_stack else min(val, self.min_stack[-1])
        self.min_stack.append(min_val)

    def pop(self):
        self.stack.pop()
        self.min_stack.pop()

    def top(self):
        return self.stack[-1]

    def getMin(self):
        return self.min_stack[-1]
```

The `min_stack` stores the current minimum after each push. When you push a value, the new minimum is `min(new_value, previous_minimum)`. This takes O(n) extra space but achieves O(1) for all operations.

**Variation:** Stack with max in O(1) — identical approach with max instead of min.

## Problem 2: Queue from Two Stacks

"Implement a queue using two stacks."

```python
class MyQueue:
    def __init__(self):
        self.inbox = []   # Receives new elements
        self.outbox = []  # Serves dequeue

    def push(self, x):
        self.inbox.append(x)

    def pop(self):
        self._move_if_needed()
        return self.outbox.pop()

    def peek(self):
        self._move_if_needed()
        return self.outbox[-1]

    def _move_if_needed(self):
        if not self.outbox:
            while self.inbox:
                self.outbox.append(self.inbox.pop())
```

**Amortized O(1)** per operation. Each element is pushed to inbox once and moved to outbox once — 2 operations per element over its lifetime.

## Problem 3: Insert/Delete/GetRandom in O(1)

"Design a data structure that supports insert, delete, and getRandom (uniformly random) in O(1)."

The challenge: hash maps support O(1) insert/delete/lookup but not O(1) random access. Arrays support O(1) random access but not O(1) deletion.

**Solution:** Combine a hash map with a dynamic array. On deletion, swap the target element with the last element, then delete from the end.

```python
import random

class RandomizedSet:
    def __init__(self):
        self.val_to_idx = {}  # value -> index in array
        self.arr = []

    def insert(self, val):
        if val in self.val_to_idx:
            return False
        self.arr.append(val)
        self.val_to_idx[val] = len(self.arr) - 1
        return True

    def remove(self, val):
        if val not in self.val_to_idx:
            return False
        idx = self.val_to_idx[val]
        last = self.arr[-1]

        # Swap val with last element
        self.arr[idx] = last
        self.val_to_idx[last] = idx

        # Delete from end
        self.arr.pop()
        del self.val_to_idx[val]
        return True

    def getRandom(self):
        return random.choice(self.arr)
```

The swap trick for O(1) deletion is reusable in many contexts — whenever you have an array and want to remove an arbitrary element, swap it with the last element and pop.

## Problem 4: All O(1) Data Structure

"Design a data structure that supports inc(key), dec(key), getMaxKey(), getMinKey() all in O(1)."

This is the hardest class of design problem. Requires a doubly linked list of buckets (each bucket = a count, storing all keys with that count) plus a hash map from key to its bucket.

```python
class AllOne:
    # Each node stores a count and the set of keys with that count
    # Doubly linked list ordered by count
    # head.next = min count node, tail.prev = max count node

    def __init__(self):
        self.head = Node(0)  # Sentinel min
        self.tail = Node(float('inf'))  # Sentinel max
        self.head.next = self.tail
        self.tail.prev = self.head
        self.key_to_node = {}  # key -> count_node

    def inc(self, key):
        if key in self.key_to_node:
            node = self.key_to_node[key]
            node.keys.remove(key)
            next_node = self._get_or_create(node.count + 1, node)
            next_node.keys.add(key)
            self.key_to_node[key] = next_node
            if not node.keys:
                self._remove_node(node)
        else:
            first = self._get_or_create(1, self.head)
            first.keys.add(key)
            self.key_to_node[key] = first
```

This is O(1) amortized for all operations due to the structure's invariants.

## Problem 5: Time-Based Key-Value Store

"Store (key, value, timestamp) triples. Support get(key, timestamp) that returns the value with the largest timestamp ≤ query timestamp."

```python
from bisect import bisect_right

class TimeMap:
    def __init__(self):
        self.store = defaultdict(list)  # key -> [(timestamp, value)]

    def set(self, key, value, timestamp):
        self.store[key].append((timestamp, value))
        # Assumes timestamps arrive in order (problem guarantee)

    def get(self, key, timestamp):
        if key not in self.store:
            return ""
        entries = self.store[key]
        # Binary search for largest timestamp <= query
        idx = bisect_right(entries, (timestamp, chr(127))) - 1
        return entries[idx][1] if idx >= 0 else ""
```

Binary search on a sorted list of timestamps: O(log n) per get. The `chr(127)` trick makes bisect_right find the insertion point after any value with that timestamp.

## The Pattern Recognition Checklist

When you see a data structure design problem, ask:
1. Which operations need to be O(1)?
2. What primitive structures support those operations?
3. Can I combine two structures, keeping them in sync, to satisfy all constraints?
4. Do deletions require a "swap with last" trick?
5. Do range/order queries require a sorted structure or linked list for ordering?

Common combinations:
- Hash map + doubly linked list → LRU cache, All O(1)
- Hash map + array → RandomizedSet
- Two heaps → median
- Stack + stack → queue
- Stack + auxiliary stack → min/max stack
