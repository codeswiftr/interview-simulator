---
title: "Implementing Data Structures from Scratch: Interview Edition"
description: "How to implement core data structures for technical interviews — linked list, stack, queue, binary tree, hash map, min-heap — with clean code, edge cases handled, and what interviewers are looking for."
date: "2026-03-20"
category: "Algorithms"
---

# Implementing Data Structures from Scratch: Interview Edition

Some interviewers ask you to implement a data structure from scratch. This tests whether you understand the internals — not just how to use the black box. Here's how to implement each core structure cleanly, with the edge cases that trip people up.

## Singly Linked List

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class LinkedList:
    def __init__(self):
        self.head = None
        self.size = 0
    
    def append(self, val):
        new_node = ListNode(val)
        if not self.head:
            self.head = new_node
        else:
            curr = self.head
            while curr.next:
                curr = curr.next
            curr.next = new_node
        self.size += 1
    
    def delete(self, val):
        dummy = ListNode(0)
        dummy.next = self.head
        curr = dummy
        while curr.next:
            if curr.next.val == val:
                curr.next = curr.next.next
                self.size -= 1
                self.head = dummy.next
                return True
            curr = curr.next
        return False
    
    def to_list(self):
        result, curr = [], self.head
        while curr:
            result.append(curr.val)
            curr = curr.next
        return result
```

**Key pattern — dummy node:** A dummy head node simplifies edge cases (deleting the head, empty list). Always consider using one when modifying the linked list.

## Stack (using array)

```python
class Stack:
    def __init__(self):
        self._data = []
    
    def push(self, val):
        self._data.append(val)
    
    def pop(self):
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._data.pop()
    
    def peek(self):
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self._data[-1]
    
    def is_empty(self):
        return len(self._data) == 0
    
    def size(self):
        return len(self._data)
```

**Min Stack** (popular interview question — get minimum in O(1)):
```python
class MinStack:
    def __init__(self):
        self._data = []
        self._min = []  # parallel stack tracking mins
    
    def push(self, val):
        self._data.append(val)
        self._min.append(min(val, self._min[-1] if self._min else val))
    
    def pop(self):
        self._min.pop()
        return self._data.pop()
    
    def get_min(self):
        return self._min[-1]
```

## Queue (using two stacks)

Classic interview question: implement a queue using two stacks.

```python
class QueueWithStacks:
    def __init__(self):
        self._in_stack = []   # for enqueue
        self._out_stack = []  # for dequeue
    
    def enqueue(self, val):
        self._in_stack.append(val)
    
    def dequeue(self):
        if not self._out_stack:
            # Transfer all items from in_stack to out_stack (reverses order)
            while self._in_stack:
                self._out_stack.append(self._in_stack.pop())
        if not self._out_stack:
            raise IndexError("dequeue from empty queue")
        return self._out_stack.pop()
```

**Amortized analysis:** Each element is moved between stacks at most once. Total operations = 2N for N enqueues. O(1) amortized per dequeue.

## Binary Search Tree

```python
class BST:
    def __init__(self):
        self.root = None
    
    def insert(self, val):
        if not self.root:
            self.root = TreeNode(val)
            return
        curr = self.root
        while True:
            if val < curr.val:
                if not curr.left:
                    curr.left = TreeNode(val)
                    return
                curr = curr.left
            else:
                if not curr.right:
                    curr.right = TreeNode(val)
                    return
                curr = curr.right
    
    def search(self, val):
        curr = self.root
        while curr:
            if val == curr.val: return True
            curr = curr.left if val < curr.val else curr.right
        return False
    
    def inorder(self):
        result = []
        def _inorder(node):
            if node:
                _inorder(node.left)
                result.append(node.val)
                _inorder(node.right)
        _inorder(self.root)
        return result
```

## Hash Map (open addressing with linear probing)

```python
class HashMap:
    def __init__(self, capacity=16):
        self.capacity = capacity
        self.size = 0
        self.keys = [None] * capacity
        self.values = [None] * capacity
        self.DELETED = object()  # sentinel for deleted slots
    
    def _hash(self, key):
        return hash(key) % self.capacity
    
    def put(self, key, value):
        if self.size / self.capacity > 0.7:
            self._resize()
        idx = self._hash(key)
        while self.keys[idx] is not None and self.keys[idx] is not self.DELETED:
            if self.keys[idx] == key:
                self.values[idx] = value
                return
            idx = (idx + 1) % self.capacity
        if self.keys[idx] is None:
            self.size += 1
        self.keys[idx] = key
        self.values[idx] = value
    
    def get(self, key, default=None):
        idx = self._hash(key)
        while self.keys[idx] is not None:
            if self.keys[idx] == key:
                return self.values[idx]
            idx = (idx + 1) % self.capacity
        return default
    
    def _resize(self):
        old_keys, old_values = self.keys, self.values
        self.capacity *= 2
        self.keys = [None] * self.capacity
        self.values = [None] * self.capacity
        self.size = 0
        for k, v in zip(old_keys, old_values):
            if k is not None and k is not self.DELETED:
                self.put(k, v)
```

## Min-Heap

```python
class MinHeap:
    def __init__(self):
        self._data = []
    
    def push(self, val):
        self._data.append(val)
        self._sift_up(len(self._data) - 1)
    
    def pop(self):
        if not self._data: raise IndexError
        min_val = self._data[0]
        last = self._data.pop()
        if self._data:
            self._data[0] = last
            self._sift_down(0)
        return min_val
    
    def peek(self):
        return self._data[0]
    
    def _sift_up(self, i):
        while i > 0:
            parent = (i - 1) // 2
            if self._data[i] < self._data[parent]:
                self._data[i], self._data[parent] = self._data[parent], self._data[i]
                i = parent
            else:
                break
    
    def _sift_down(self, i):
        n = len(self._data)
        while True:
            smallest = i
            left, right = 2*i+1, 2*i+2
            if left < n and self._data[left] < self._data[smallest]:
                smallest = left
            if right < n and self._data[right] < self._data[smallest]:
                smallest = right
            if smallest == i: break
            self._data[i], self._data[smallest] = self._data[smallest], self._data[i]
            i = smallest
```

## What Interviewers Evaluate

**Edge cases:** Empty structure, single element, inserting duplicates, deleting non-existent elements. Handle these explicitly.

**Clean code:** Well-named methods, appropriate use of helper functions, no magic numbers.

**Time/space analysis:** Be ready to state and justify the complexity of each operation.

**Trade-offs:** Why linear probing vs chaining for hash maps? Why array-based heap vs pointer-based? Demonstrating this thinking shows depth.

