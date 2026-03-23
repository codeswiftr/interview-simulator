---
title: "Stacks and Queues in Coding Interviews: Patterns and Problems"
description: "Master stack and queue patterns for technical interviews. Covers monotonic stacks, BFS with queues, implementing stacks/queues from scratch, and 8 classic problems with Python solutions."
date: "2025-10-16"
category: "Interview Preparation"
---

# Stacks and Queues in Coding Interviews

Stacks and queues are foundational data structures that appear in dozens of interview problems. Beyond the basic LIFO/FIFO mechanics, the patterns that emerge — especially monotonic stacks — are genuinely powerful and appear frequently at top tech companies.

## Stack Fundamentals

A stack is Last-In-First-Out (LIFO). Python's built-in list works perfectly as a stack:

```python
stack = []
stack.append(1)   # push
stack.append(2)
stack.append(3)
top = stack[-1]   # peek — O(1)
val = stack.pop() # pop — O(1)
```

**When to reach for a stack:**
- Problems involving matching/balancing (parentheses, brackets, braces)
- Problems where you need to "undo" or backtrack
- Next greater/smaller element problems
- Implementing recursive algorithms iteratively (DFS)
- Evaluating expressions

## Queue Fundamentals

A queue is First-In-First-Out (FIFO). Use `collections.deque` for O(1) operations at both ends:

```python
from collections import deque
queue = deque()
queue.append(1)    # enqueue — O(1)
queue.append(2)
val = queue.popleft()  # dequeue — O(1), not O(n) like list.pop(0)
front = queue[0]       # peek — O(1)
```

**When to reach for a queue:**
- BFS (level-order traversal)
- Processing items in order with a sliding window
- Implementing caches (deque + dict for LRU)

## Pattern 1: Valid Parentheses

The classic stack problem. Works for any matching-pair scenario.

```python
def is_valid(s):
    stack = []
    matching = {')': '(', '}': '{', ']': '['}
    for c in s:
        if c in '([{':
            stack.append(c)
        else:
            if not stack or stack[-1] != matching[c]:
                return False
            stack.pop()
    return len(stack) == 0
```

**Variations**: Minimum remove to make valid, minimum add to make valid, longest valid parentheses substring.

## Pattern 2: Monotonic Stack — Next Greater Element

The monotonic stack pattern solves "next greater/smaller/warmer/colder" problems in O(n) instead of O(n²).

**Key insight**: Maintain a stack where elements are always in monotonically increasing (or decreasing) order. When a new element violates the order, pop and record the "next greater" for the popped element.

```python
def next_greater_elements(nums):
    n = len(nums)
    result = [-1] * n
    stack = []  # stores indices
    
    for i in range(n):
        while stack and nums[stack[-1]] < nums[i]:
            idx = stack.pop()
            result[idx] = nums[i]
        stack.append(i)
    
    return result
```

**Classic monotonic stack problems:**
- Daily Temperatures (next warmer day)
- Largest Rectangle in Histogram
- Trapping Rain Water
- 132 Pattern
- Sum of Subarray Minimums

## Pattern 3: Largest Rectangle in Histogram

One of the most famous stack problems. Appears frequently at top companies.

```python
def largest_rectangle(heights):
    stack = []  # stores indices
    max_area = 0
    heights = heights + [0]  # Sentinel to flush the stack
    
    for i, h in enumerate(heights):
        while stack and heights[stack[-1]] > h:
            height = heights[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            max_area = max(max_area, height * width)
        stack.append(i)
    
    return max_area
```

## Pattern 4: BFS with Queue

Every BFS problem uses a queue. The pattern is identical whether you're traversing a tree, a graph, or a matrix.

```python
from collections import deque

def bfs_matrix(grid, start):
    rows, cols = len(grid), len(grid[0])
    queue = deque([start])
    visited = {start}
    distance = 0
    directions = [(0,1), (0,-1), (1,0), (-1,0)]
    
    while queue:
        for _ in range(len(queue)):  # Process level by level
            r, c = queue.popleft()
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if (0 <= nr < rows and 0 <= nc < cols 
                        and (nr, nc) not in visited
                        and grid[nr][nc] != '#'):  # Adjust condition
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        distance += 1
    
    return distance
```

## Pattern 5: Min Stack

Implement a stack with O(1) `getMin()`. Classic design problem.

```python
class MinStack:
    def __init__(self):
        self.stack = []
        self.min_stack = []
    
    def push(self, val):
        self.stack.append(val)
        min_val = min(val, self.min_stack[-1] if self.min_stack else val)
        self.min_stack.append(min_val)
    
    def pop(self):
        self.stack.pop()
        self.min_stack.pop()
    
    def top(self):
        return self.stack[-1]
    
    def getMin(self):
        return self.min_stack[-1]
```

## Pattern 6: LRU Cache (Deque + Dict)

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

## Interview Tips

**1. Monotonic stack recognition**: If the problem asks for "next greater/smaller" or involves spans and ranges, immediately think monotonic stack.

**2. Stack for DFS, queue for BFS**: This is a reliable heuristic for graph traversal problems.

**3. Trapping Rain Water**: This is one of the most commonly asked stack problems. The two-pointer O(1) space solution is cleaner, but the stack approach shows good pattern recognition.

**4. Process level by level in BFS**: Using `for _ in range(len(queue))` inside the while loop lets you track depth/levels without extra variables.

**5. Sentinel values**: Adding a 0 or infinity at the end of the input (as in the histogram problem) often simplifies stack cleanup logic.

Stacks and queues reward pattern memorization — once you've solved 10–15 problems in each category, you'll see the templates applying almost instantly.
