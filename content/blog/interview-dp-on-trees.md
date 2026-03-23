---
title: "Dynamic Programming on Trees: Interview Patterns"
description: "Tree DP patterns for coding interviews — rerooting technique, diameter, maximum path sum, subtree counting, and how to recognize when a tree problem requires DP."
date: "2026-03-20"
category: "Algorithms"
---

# Dynamic Programming on Trees: Interview Patterns

Tree DP combines two of the most tested interview topics: trees and dynamic programming. Problems in this category require you to compute a value for each node based on its subtree, often with a second pass that incorporates parent context. These problems appear at senior-level interviews and are frequently unsolvable with pure DFS without DP insight.

## The Core Pattern: Bottom-Up DP on Trees

Most tree DP follows a single pattern: define what you need to know about each subtree, compute it via post-order DFS (children first, then current node), and return the value up to the parent.

```python
def solve(root):
    def dp(node):
        if not node:
            return base_case_value

        left = dp(node.left)
        right = dp(node.right)

        # Compute answer for this node using left and right subtree values
        result = combine(left, right, node.val)

        # Update global answer if needed
        nonlocal ans
        ans = max(ans, some_function(left, right, node.val))

        return result  # What parent needs to know about this subtree

    ans = initial_value
    dp(root)
    return ans
```

The key design decision: **what does the DP function return?** This shapes everything. It's usually the maximum/minimum value achievable in a subtree that can be extended to the parent (i.e., one path going down). The global answer may be something larger that can't be passed up.

## Problem 1: Binary Tree Maximum Path Sum

"A path is a sequence of nodes where each pair of adjacent nodes has an edge. Find the maximum path sum."

A path can go through any node and must go downward from any point — but crucially, a path through node N can use at most one of N's children (otherwise it would be a Y-shape, not a path).

```python
def maxPathSum(root):
    ans = float('-inf')

    def dp(node):
        nonlocal ans
        if not node:
            return 0

        # Maximum gain from left/right subtrees (0 if negative — ignore that subtree)
        left_gain = max(dp(node.left), 0)
        right_gain = max(dp(node.right), 0)

        # Best path THROUGH this node (can use both children — forms an arch)
        price_through = node.val + left_gain + right_gain
        ans = max(ans, price_through)

        # Return to parent: can only extend ONE path downward
        return node.val + max(left_gain, right_gain)

    dp(root)
    return ans
```

The insight: the global answer considers paths through each node (arched, using both children). But what we return to the parent is the maximum straight path (using only one child), since a path to the parent can't branch.

## Problem 2: Diameter of Binary Tree

The diameter is the longest path between any two nodes (measured in edges or nodes, clarify which).

```python
def diameterOfBinaryTree(root):
    diameter = 0

    def depth(node):
        nonlocal diameter
        if not node:
            return 0

        left = depth(node.left)
        right = depth(node.right)

        # Diameter through this node
        diameter = max(diameter, left + right)

        # Return height of this subtree
        return 1 + max(left, right)

    depth(root)
    return diameter
```

Notice the structure is identical to max path sum: track the global answer separately from what you return to the parent. This two-value pattern recurs throughout tree DP.

## Problem 3: House Robber III (DP on Trees)

"Cannot rob two adjacent nodes (parent-child). Maximum sum."

State: for each node, we need two values: maximum if we rob this node, maximum if we don't.

```python
def rob(root):
    def dp(node):
        if not node:
            return 0, 0  # (rob_this, skip_this)

        left_rob, left_skip = dp(node.left)
        right_rob, right_skip = dp(node.right)

        # Rob current node: cannot rob children
        rob_current = node.val + left_skip + right_skip

        # Skip current node: children can be robbed or not — take best
        skip_current = max(left_rob, left_skip) + max(right_rob, right_skip)

        return rob_current, skip_current

    return max(dp(root))
```

Returning a tuple per node is a natural extension when you need multiple states per node.

## The Rerooting Technique

Some problems ask for a value at every node, where the value depends not just on the subtree but also on the rest of the tree (the "upper" part). Naively, this requires O(n) DFS per node = O(n²) total. Rerooting does it in O(n) with two passes.

**Example:** For each node, find the sum of distances to all other nodes.

Pass 1 (post-order): Compute `count[v]` (size of subtree at v) and `dist[v]` (sum of distances in subtree at v).

```python
# Pass 1: bottom-up
def dfs1(node, parent):
    for child in graph[node]:
        if child != parent:
            dfs1(child, node)
            count[node] += count[child]
            dist[node] += dist[child] + count[child]
    count[node] += 1
```

Pass 2 (pre-order): Reroot by moving root from parent to child.

```python
# Pass 2: top-down
def dfs2(node, parent):
    for child in graph[node]:
        if child != parent:
            # When we move root from node to child:
            # - count[child] nodes get 1 closer
            # - n - count[child] nodes get 1 further
            dist[child] = dist[node] - count[child] + (n - count[child])
            dfs2(child, node)
```

This rerooting technique unlocks a class of problems where the answer at every node requires global context, not just subtree context.

## Subtree Counting: Unique Structures

"How many structurally identical subtrees exist?" Use a hash to represent each subtree structure.

```python
def findDuplicateSubtrees(root):
    count = defaultdict(int)
    result = []

    def serialize(node):
        if not node:
            return '#'
        key = f"{node.val},{serialize(node.left)},{serialize(node.right)}"
        count[key] += 1
        if count[key] == 2:
            result.append(node)
        return key

    serialize(root)
    return result
```

## Recognizing Tree DP Problems

Signals:
- "Find the maximum/minimum over all paths" — classic tree DP
- "Value at each node depends on subtree and parent context" — rerooting
- "Choose nodes with constraints on adjacency" — multi-state DP per node
- "Count structures or configurations" — memoized subtree hashing

Key habit: when you see a tree problem, ask "what do I need to know about a subtree that a parent needs to use?" The answer defines your DP state. Then ask "is the global answer different from what I return to the parent?" — if yes, you need a separate variable tracked via `nonlocal` or a class attribute.
