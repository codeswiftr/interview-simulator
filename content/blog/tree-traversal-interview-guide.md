---
title: "Tree Traversal Patterns for Coding Interviews"
description: "Master tree traversal for coding interviews. Learn DFS (inorder, preorder, postorder) and BFS both recursively and iteratively, when each traversal applies, and how to solve classic problems like validate BST and serialize/deserialize."
date: "2025-10-11"
category: "Interview Preparation"
---
# Tree Traversal Patterns for Coding Interviews

Binary trees appear in roughly 15-20% of FAANG-level coding interviews. Of all tree topics, traversal is the foundation — almost every tree problem is secretly a traversal problem with some additional logic layered on top. Validate BST? Traversal with a constraint. Path sum? Traversal with running totals. Lowest common ancestor? Traversal with state tracking. Get traversal right, and hard tree problems become much more manageable.

## DFS: Inorder, Preorder, and Postorder

Depth-first search visits nodes by going deep before wide. The three orderings differ only in when you process the current node relative to its children.

- **Inorder (Left → Node → Right):** Processes nodes in sorted order for a BST
- **Preorder (Node → Left → Right):** Useful for serialization and copying trees
- **Postorder (Left → Right → Node):** Useful when you need children's results before processing the parent (e.g., computing subtree sizes)

**Recursive implementation (the natural form):**

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def inorder(root: TreeNode) -> list[int]:
    result = []
    def dfs(node):
        if not node:
            return
        dfs(node.left)
        result.append(node.val)
        dfs(node.right)
    dfs(root)
    return result

def preorder(root: TreeNode) -> list[int]:
    result = []
    def dfs(node):
        if not node:
            return
        result.append(node.val)
        dfs(node.left)
        dfs(node.right)
    dfs(root)
    return result

def postorder(root: TreeNode) -> list[int]:
    result = []
    def dfs(node):
        if not node:
            return
        dfs(node.left)
        dfs(node.right)
        result.append(node.val)
    dfs(root)
    return result
```

**Iterative implementation (using an explicit stack):**

Interviewers often ask for iterative solutions to avoid stack overflow on deep trees and to demonstrate understanding of what the call stack is actually doing.

```python
def inorder_iterative(root: TreeNode) -> list[int]:
    result = []
    stack = []
    curr = root
    while curr or stack:
        while curr:
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()
        result.append(curr.val)
        curr = curr.right
    return result

def preorder_iterative(root: TreeNode) -> list[int]:
    if not root:
        return []
    result = []
    stack = [root]
    while stack:
        node = stack.pop()
        result.append(node.val)
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
    return result

def postorder_iterative(root: TreeNode) -> list[int]:
    if not root:
        return []
    stack = [root]
    result = []
    while stack:
        node = stack.pop()
        result.append(node.val)
        if node.left:
            stack.append(node.left)
        if node.right:
            stack.append(node.right)
    return result[::-1]  # reverse preorder gives postorder
```

Note the postorder trick: postorder is the reverse of a modified preorder (Node → Right → Left). Push right first so left is processed first in the reversed result.

## BFS: Level Order Traversal

BFS visits all nodes at depth d before any node at depth d+1. Use a queue (Python's `collections.deque` for O(1) pops from both ends).

```python
from collections import deque

def level_order(root: TreeNode) -> list[list[int]]:
    if not root:
        return []
    result = []
    queue = deque([root])
    while queue:
        level_size = len(queue)
        current_level = []
        for _ in range(level_size):
            node = queue.popleft()
            current_level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(current_level)
    return result
```

The `level_size = len(queue)` snapshot at the start of each loop iteration is the key: it tells you exactly how many nodes belong to the current level before you start adding the next level's children.

## When Each Traversal Is Useful

**Use inorder when:**
- Working with BSTs (inorder produces sorted output)
- Validating BST property
- Finding kth smallest/largest in BST

**Use preorder when:**
- Serializing a tree (root first, so you can reconstruct by inserting in preorder)
- Copying a tree
- Printing directory structures

**Use postorder when:**
- Computing properties that depend on subtree results (height, subtree sum)
- Deleting a tree (delete children before parent)
- Evaluating expression trees

**Use BFS (level order) when:**
- Finding shortest path in an unweighted tree
- Processing nodes level by level (right side view, zigzag traversal)
- Finding the minimum depth of a tree

## Top Interview Problems by Traversal Type

**Validate BST (LC 98) — Inorder with constraint:**

```python
def is_valid_bst(root: TreeNode) -> bool:
    def validate(node, min_val, max_val):
        if not node:
            return True
        if node.val <= min_val or node.val >= max_val:
            return False
        return (validate(node.left, min_val, node.val) and
                validate(node.right, node.val, max_val))
    return validate(root, float('-inf'), float('inf'))
```

**Path Sum II (LC 113) — Preorder DFS:**

```python
def path_sum(root: TreeNode, target: int) -> list[list[int]]:
    result = []
    def dfs(node, remaining, path):
        if not node:
            return
        path.append(node.val)
        if not node.left and not node.right and remaining == node.val:
            result.append(list(path))
        dfs(node.left, remaining - node.val, path)
        dfs(node.right, remaining - node.val, path)
        path.pop()  # backtrack
    dfs(root, target, [])
    return result
```

**Lowest Common Ancestor (LC 236) — Postorder:**

```python
def lowest_common_ancestor(root, p, q):
    if not root or root == p or root == q:
        return root
    left = lowest_common_ancestor(root.left, p, q)
    right = lowest_common_ancestor(root.right, p, q)
    if left and right:
        return root  # p and q on different sides
    return left or right
```

**Serialize and Deserialize Binary Tree (LC 297) — Preorder:**

Serialize using preorder DFS, using "null" as a sentinel for missing nodes. Deserialize by consuming values from the serialized string in preorder.

## Common Mistakes

**Off-by-one in level-order:** Forgetting the `level_size` snapshot means you process more nodes than belong to the current level, collapsing all levels into one.

**Mutating a list while iterating:** Using `path.pop()` (backtracking) is correct. A common bug is passing `path + [node.val]` to recursive calls — this creates a new list each time and is O(n) extra space per call, making the total space O(n * depth).

**Missing the base case for None:** Almost every tree DFS starts with `if not node: return`. Forgetting this causes a NoneType attribute error on the first leaf node.

**Confusing BST validation:** Checking only `node.left.val < node.val < node.right.val` at each node is insufficient. A node's value must be within bounds set by all its ancestors, not just its immediate parent. Use the min/max bound approach shown above.

Practice switching fluidly between recursive and iterative implementations. Being able to convert one to the other on demand demonstrates depth of understanding that impresses interviewers and gives you flexibility when faced with constraints like "implement this without recursion."
