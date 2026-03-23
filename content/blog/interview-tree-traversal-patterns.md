---
title: "Tree Traversal Patterns: Iterative, Morris, and Advanced Applications"
description: "Beyond recursive traversals — iterative DFS with explicit stack, Morris traversal for O(1) space, level-order variations, and how traversal choice affects interview solutions for binary tree problems."
date: "2026-03-20"
category: "Algorithms"
---

# Tree Traversal Patterns: Iterative, Morris, and Advanced Applications

Most engineers implement tree traversals recursively. Senior interviews sometimes probe whether you can implement them iteratively (to avoid stack overflow risk), or using Morris traversal (O(1) space). More importantly, the choice of traversal order is a design decision that shapes many binary tree solutions.

## Iterative Inorder: The Most Common Iterative Traversal

Iterative inorder traversal (left-root-right) is the most frequently requested iterative traversal:

```python
def inorderIterative(root):
    result = []
    stack = []
    curr = root

    while curr or stack:
        # Go as far left as possible
        while curr:
            stack.append(curr)
            curr = curr.left

        # Process node, then go right
        curr = stack.pop()
        result.append(curr.val)
        curr = curr.right

    return result
```

Pattern: push nodes going left; on pop, process and go right. The stack simulates the recursive call stack implicitly.

## Iterative Preorder

```python
def preorderIterative(root):
    if not root:
        return []
    result = []
    stack = [root]

    while stack:
        node = stack.pop()
        result.append(node.val)
        # Push right first so left is processed first
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)

    return result
```

Preorder is simpler iteratively than inorder — no need for the "go left first" inner loop.

## Iterative Postorder

Postorder (left-right-root) is the trickiest iteratively. One clean approach: reverse preorder.

Preorder is root-left-right. Modified preorder (root-right-left) reversed = left-right-root = postorder.

```python
def postorderIterative(root):
    if not root:
        return []
    result = []
    stack = [root]

    while stack:
        node = stack.pop()
        result.append(node.val)
        if node.left:
            stack.append(node.left)
        if node.right:
            stack.append(node.right)

    return result[::-1]  # Reverse to get left-right-root
```

## Morris Traversal: O(1) Space

Morris traversal modifies the tree temporarily (then restores it) to achieve O(1) space. It works by creating temporary "threads" — backward pointers from the inorder predecessor back to the current node.

```python
def morrisInorder(root):
    result = []
    curr = root

    while curr:
        if not curr.left:
            result.append(curr.val)
            curr = curr.right
        else:
            # Find inorder predecessor (rightmost in left subtree)
            predecessor = curr.left
            while predecessor.right and predecessor.right != curr:
                predecessor = predecessor.right

            if not predecessor.right:
                # Create thread: predecessor.right → curr
                predecessor.right = curr
                curr = curr.left
            else:
                # Thread exists — we've already processed the left subtree
                predecessor.right = None  # Remove thread
                result.append(curr.val)
                curr = curr.right

    return result
```

Morris traversal is O(n) time and O(1) space. Used when stack space is genuinely constrained (embedded systems, very deep trees). Not typically expected in interviews but worth knowing for depth questions.

## Level-Order (BFS) Variations

Basic level-order using a queue:

```python
from collections import deque

def levelOrder(root):
    if not root:
        return []
    result = []
    queue = deque([root])

    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            if node.left: queue.append(node.left)
            if node.right: queue.append(node.right)
        result.append(level)

    return result
```

**Variations:**
- **Zigzag order:** Alternate left-to-right and right-to-left per level. Toggle a direction flag per level; reverse the level list when direction is right-to-left.
- **Right side view:** Take only the last node from each level.
- **Average of levels:** Average each level's node values.
- **Minimum depth:** BFS finds the first leaf — its depth is the minimum depth (O(n/2) vs. O(n) for DFS worst case on a skewed tree).

## Traversal Choice as a Design Decision

The choice of traversal order is a design decision with correctness implications:

**Inorder on BST = sorted order.** If the problem involves sorted values from a BST, inorder traversal produces them in order.

**Postorder for subtree processing.** When the solution at a node depends on both children's solutions (tree DP, diameter, path sum), postorder is natural — process children before parents.

**Preorder for path/prefix problems.** When you're passing information from root to leaves (prefix sum, root-to-leaf paths), preorder is natural.

**BFS for level-dependent problems.** Level-order average, right-side view, minimum depth, and "level-by-level" problems all require BFS.

## Vertical Order Traversal

"Return nodes grouped by vertical column."

Combine BFS with column tracking:

```python
def verticalTraversal(root):
    from collections import defaultdict

    col_table = defaultdict(list)
    queue = deque([(root, 0, 0)])  # (node, row, col)

    while queue:
        node, row, col = queue.popleft()
        col_table[col].append((row, node.val))

        if node.left: queue.append((node.left, row+1, col-1))
        if node.right: queue.append((node.right, row+1, col+1))

    result = []
    for col in sorted(col_table.keys()):
        result.append([val for _, val in sorted(col_table[col])])

    return result
```

## Boundary Traversal

"Return all boundary nodes (left boundary, leaves, right boundary in reverse)."

```python
def boundaryOfBinaryTree(root):
    if not root:
        return []

    def left_boundary(node):
        if not node or (not node.left and not node.right):
            return []
        result = [node.val]
        if node.left:
            result += left_boundary(node.left)
        else:
            result += left_boundary(node.right)
        return result

    def leaves(node):
        if not node:
            return []
        if not node.left and not node.right:
            return [node.val]
        return leaves(node.left) + leaves(node.right)

    def right_boundary(node):
        if not node or (not node.left and not node.right):
            return []
        result = []
        if node.right:
            result += right_boundary(node.right)
        else:
            result += right_boundary(node.left)
        return result + [node.val]

    return [root.val] + left_boundary(root.left) + leaves(root.left) + leaves(root.right) + right_boundary(root.right)
```

Knowing when to use BFS vs. DFS and which DFS order is the most important decision in binary tree interview problems.
