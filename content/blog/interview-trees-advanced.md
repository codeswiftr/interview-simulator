---
title: "Binary Trees Advanced: Interview Patterns Beyond the Basics"
description: "Advanced binary tree interview patterns — lowest common ancestor, serialize/deserialize, path sum variants, BST operations, AVL and Red-Black tree concepts, and Morris traversal for O(1) space."
date: "2026-03-20"
category: "Algorithms"
---

# Binary Trees Advanced: Interview Patterns Beyond the Basics

Once you have basic tree traversals (inorder, preorder, postorder) memorized, interviews probe deeper. This guide covers the patterns that appear in senior engineer interviews and the tree problems that trip up candidates who only studied the basics.

## Lowest Common Ancestor (LCA)

LCA of nodes p and q in a binary tree is the deepest node that has both p and q as descendants.

**LCA in a general binary tree:** Post-order DFS. If current node is p or q, return it. Recursively search left and right subtrees. If both return non-null, current node is the LCA. If only one returns non-null, that's the LCA or contains the LCA.

```python
def lca(root, p, q):
    if not root or root == p or root == q:
        return root
    left = lca(root.left, p, q)
    right = lca(root.right, p, q)
    if left and right:
        return root
    return left or right
```

**LCA in a BST:** Simpler — use BST property. If both p and q are less than root, recurse left. If both are greater, recurse right. Otherwise, root is the split point — it's the LCA.

**Follow-up: LCA with parent pointers.** Traverse from p to root, store path in a set. Traverse from q to root — first node in the parent path set is the LCA. O(depth) time and space.

## Serialize and Deserialize

Classic hard-difficulty problem. Approach: preorder DFS with null markers.

Serialize: `root.val, LEFT_SUBTREE, RIGHT_SUBTREE`. Use a sentinel (e.g., "null") for null nodes. Produces a string like `"1,2,null,null,3,null,null"`.

Deserialize: Split on comma, process tokens from left to right using a queue or index pointer. Each call to the recursive deserialize function consumes one token.

BFS-based serialize (level order) is also valid — use null for absent children. The same level-order sequence uniquely represents the tree.

## Path Sum Variants

**Path sum from root to leaf (Path Sum I):** DFS, subtract current value from target as you recurse. Return true when you hit a leaf and remaining target equals 0.

**All root-to-leaf paths with sum (Path Sum II):** Backtracking DFS. Add current node to path, recurse both subtrees, remove when backtracking. Append a copy when leaf with target sum found.

**Maximum path sum (Path Sum III — no root/leaf constraint):** Each node can be the apex of a path. At each node, compute max path gain from left and right subtrees (take only if positive — contributes 0 if negative). Update global max with `left_gain + node.val + right_gain`. Return `node.val + max(left_gain, right_gain)` for parent's use.

**Path sum equals k (count paths, any start/end):** Prefix sum approach. DFS with running sum. Use a hash map counting prefix sums seen so far. At each node, check how many paths ending here have sum k: `prefix_map[running_sum - k]`.

## BST Operations and Validation

**Validate BST:** Pass valid range `[min_val, max_val]` down. Left subtree's max becomes the current node's value. Right subtree's min becomes the current node's value. Common mistake: only comparing parent-child — you must propagate bounds.

**Kth smallest in BST:** Inorder traversal gives sorted order. Stop early when kth element found. With follow-ups about frequent insertions: augment each node with the count of nodes in its left subtree.

**BST iterator:** Use a stack that simulates iterative inorder traversal. `next()` pops from the stack and pushes the right child's leftmost spine.

**Delete in BST:** Three cases: leaf (just remove), one child (replace with child), two children (replace value with inorder successor — leftmost node in right subtree — then delete the successor).

## AVL and Red-Black Trees (Conceptual)

Interviewers rarely ask you to implement self-balancing trees, but they may ask you to explain them.

**AVL trees:** Height-balanced binary search trees. Each node stores the height of its subtree. Balance factor = height(left) - height(right). If balance factor exceeds ±1 after insertion/deletion, perform rotations (single or double) to rebalance. O(log N) for all operations. AVL trees are more strictly balanced than Red-Black, so lookup is faster but insertions/deletions are slower.

**Red-Black trees:** Each node is red or black. Rules: root is black, red nodes have black children, all paths from any node to null have the same number of black nodes. These rules ensure height ≤ 2·log(N+1). Used in Java's `TreeMap` and `TreeSet`, C++'s `std::map`. O(log N) for all operations.

**When to use which:** AVL for read-heavy workloads (stricter balance → faster lookups). Red-Black for write-heavy workloads (fewer rotations on insert/delete).

## Morris Traversal

Inorder traversal in O(N) time, O(1) space — no recursion, no explicit stack. Uses threaded binary trees temporarily.

For each node: if no left child, process current, move right. If has left child, find inorder predecessor (rightmost node in left subtree). If predecessor's right is null, create thread (set predecessor.right = current), move left. If predecessor's right is current, remove thread, process current, move right.

This is a classic interview question for follow-ups on space optimization. Rare to be asked to code from scratch but understanding the principle (temporary links to parent) demonstrates deep knowledge.

## Building Trees from Traversals

**From preorder + inorder:** Preorder[0] is the root. Find it in inorder — everything left is left subtree, everything right is right subtree. Recurse.

**From postorder + inorder:** Postorder[-1] is the root. Same split in inorder.

**From preorder + postorder:** Only works for full binary trees (every node has 0 or 2 children). Preorder[1] is left subtree root. Find it in postorder to determine left subtree size.

You cannot reconstruct a tree from preorder + postorder alone for general trees — multiple trees can produce the same sequences.

## Trie (Prefix Tree) Patterns

Tries are trees where the path from root to a node spells out a key. Each node represents a character; edges connect characters.

When to use a trie over a hash set: when you need prefix queries (all words with prefix "pre"), autocomplete, or longest common prefix operations. Hash sets can tell you if a word exists in O(L) — tries can tell you all words with a prefix in O(P + K) where P is prefix length and K is number of matching words.

Implement a trie with a dictionary mapping characters to children and an is_end flag. Insert: traverse existing nodes, create new ones where needed. Search: traverse; return false if any character is missing.

