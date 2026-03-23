---
title: "Tree Algorithm Interview Guide: DFS, BFS, and Common Tree Problem Patterns"
description: "Complete guide to tree algorithm interview questions — inorder/preorder/postorder traversal, LCA, BST operations, balanced trees, and the iterative vs recursive tradeoff."
date: "2026-03-20"
category: "Algorithms"
---

# Tree Algorithm Interview Guide: DFS, BFS, and Common Tree Problem Patterns

Trees appear in more interview problems than almost any other data structure. They reward candidates who understand a small number of core patterns — because nearly every tree problem is a variation on one of them. This guide covers the essential traversal techniques, the most common problem patterns, and the iterative vs recursive tradeoff that interviewers often probe.

## The Two Core Traversal Strategies

Every tree algorithm is built on one of two traversal approaches: depth-first search (DFS) or breadth-first search (BFS). Understanding both deeply — including their iterative implementations — is non-negotiable for interviews.

### DFS: Recursive Implementation

Recursive DFS maps cleanly to the call stack. The three orderings differ only in where you process the current node relative to its children:

```python
def inorder(root):   # left → node → right (gives sorted order for BST)
    if not root:
        return
    inorder(root.left)
    process(root.val)
    inorder(root.right)

def preorder(root):  # node → left → right (useful for tree serialization)
    if not root:
        return
    process(root.val)
    preorder(root.left)
    preorder(root.right)

def postorder(root): # left → right → node (useful for tree deletion, size)
    if not root:
        return
    postorder(root.left)
    postorder(root.right)
    process(root.val)
```

### DFS: Iterative with a Stack

Interviewers frequently ask for the iterative version after you produce the recursive one. The iterative preorder is straightforward; iterative inorder requires a bit more care:

```python
def inorder_iterative(root):
    result, stack, current = [], [], root
    while current or stack:
        while current:
            stack.append(current)
            current = current.left
        current = stack.pop()
        result.append(current.val)
        current = current.right
    return result
```

### BFS: Level-Order Traversal with a Queue

BFS processes nodes level by level and is the right tool when you need to work with tree structure by depth.

```python
from collections import deque

def level_order(root):
    if not root:
        return []
    result, queue = [], deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    return result
```

The `range(len(queue))` snapshot is the key technique for capturing a full level before processing the next.

## BST-Specific Patterns

Binary Search Trees show up constantly. Know these operations cold:

**Validation** — a BST is valid if every node respects bounds inherited from its ancestors, not just its immediate parent:

```python
def is_valid_bst(root, low=float('-inf'), high=float('inf')):
    if not root:
        return True
    if not (low < root.val < high):
        return False
    return (is_valid_bst(root.left, low, root.val) and
            is_valid_bst(root.right, root.val, high))
```

The common mistake is only comparing a node to its direct children. A node deep in the right subtree must be greater than all ancestors on the left path — that constraint is captured by threading `low` and `high` through the recursion.

**Inorder gives sorted output** — if you need to find the kth smallest element in a BST, an inorder traversal with a counter is the cleanest approach.

## Lowest Common Ancestor (LCA)

LCA problems ask: given two nodes p and q, find the deepest node that is an ancestor of both.

```python
def lca(root, p, q):
    if not root or root == p or root == q:
        return root
    left = lca(root.left, p, q)
    right = lca(root.right, p, q)
    if left and right:
        return root   # p and q are in different subtrees
    return left or right
```

This works because if both recursive calls return non-null, the current node is the split point. If only one side returns non-null, both nodes live in that subtree and the LCA is deeper.

## Path Sum Problems

Path sum variants test your ability to carry state through a DFS. The base pattern:

```python
def has_path_sum(root, target):
    if not root:
        return False
    if not root.left and not root.right:
        return root.val == target
    return (has_path_sum(root.left, target - root.val) or
            has_path_sum(root.right, target - root.val))
```

For the variant that asks for all root-to-leaf paths with a given sum, carry the current path as a list and append/pop around recursive calls (the classic backtracking pattern on trees).

## Tree Reconstruction

Reconstruct a binary tree from inorder + preorder traversal — a classic problem that tests understanding of traversal semantics:

- Preorder: first element is always the root
- Inorder: everything left of the root index is the left subtree; everything right is the right subtree

```python
def build_tree(preorder, inorder):
    if not preorder:
        return None
    root_val = preorder[0]
    root = TreeNode(root_val)
    mid = inorder.index(root_val)
    root.left = build_tree(preorder[1:mid+1], inorder[:mid])
    root.right = build_tree(preorder[mid+1:], inorder[mid+1:])
    return root
```

For large inputs, use a hashmap to make the `inorder.index()` lookup O(1).

## Serialize and Deserialize

Serialize/deserialize tests whether you can encode a tree into a string and reconstruct it exactly. A BFS-based approach works cleanly:

```python
def serialize(root):
    if not root:
        return "null"
    result, queue = [], deque([root])
    while queue:
        node = queue.popleft()
        if node:
            result.append(str(node.val))
            queue.append(node.left)
            queue.append(node.right)
        else:
            result.append("null")
    return ",".join(result)
```

Deserialize reads the level-order string and reconstructs using a queue of parent nodes.

## Balanced Tree Detection

A tree is height-balanced if the height difference between left and right subtrees is at most 1 at every node. The efficient approach combines height computation and balance checking in a single pass:

```python
def is_balanced(root):
    def check(node):
        if not node:
            return 0
        left = check(node.left)
        right = check(node.right)
        if left == -1 or right == -1 or abs(left - right) > 1:
            return -1
        return max(left, right) + 1
    return check(root) != -1
```

Returning -1 as a sentinel value allows the function to short-circuit without a separate boolean flag.

## Iterative vs Recursive: When to Choose

Recursive solutions are cleaner and easier to reason about — use them unless you have a specific reason not to. The cases where iterative is preferable:

- The interviewer explicitly asks for it (common follow-up)
- The tree is extremely deep and stack overflow is a concern (rare in interviews but worth mentioning)
- You need explicit control over the stack for more complex state management

In practice, being able to convert any recursive DFS to iterative on demand signals strong understanding of how the call stack works. It is worth practicing both forms for the core traversals.

## The Pattern to Internalize

Most tree problems reduce to: traverse (DFS or BFS), carry state downward (parameters), carry state upward (return values), and combine left/right results at each node. Once you see this structure clearly, new problems become variations on a familiar theme rather than novel puzzles.
