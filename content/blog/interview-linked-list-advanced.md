---
title: "Advanced Linked List Interview Patterns: Floyd's Cycle, Merge, and Reversal Variants"
description: "Master the advanced linked list patterns that consistently appear in FAANG and top-tier engineering interviews, including cycle detection, merge strategies, and in-place reversal techniques."
date: "2026-03-20"
category: "Algorithms"
---

Linked lists sit at the core of interview curricula for a reason: they test pointer manipulation, recursion, and space-complexity reasoning simultaneously. Once you move past the basics, a handful of advanced patterns cover the vast majority of hard linked list problems. This guide breaks them down with the mental models you need to apply them under pressure.

## Floyd's Cycle Detection (Fast and Slow Pointers)

The classic cycle detection algorithm uses two pointers moving at different speeds. The slow pointer advances one node per step; the fast pointer advances two. If a cycle exists, fast will eventually lap slow and they will meet inside the cycle.

```python
def has_cycle(head):
    slow, fast = head, head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    return False
```

**Finding the cycle entry point** is the follow-up that separates prepared candidates from the rest. After detecting the meeting point inside the cycle, reset one pointer to `head` and advance both one step at a time. They will meet exactly at the cycle's entry node. This works because of a mathematical property: the distance from head to the entry equals the distance from the meeting point to the entry (measured along the cycle direction).

```python
def detect_cycle(head):
    slow, fast = head, head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            # Reset slow to head
            slow = head
            while slow != fast:
                slow = slow.next
                fast = fast.next
            return slow  # cycle entry node
    return None
```

The same fast/slow pattern solves "find the middle node" (stop when fast reaches the end) and "find the k-th node from the end" (advance fast k steps first, then move both until fast reaches null).

## In-Place Reversal Patterns

Reversal is often a building block embedded in larger problems. The iterative version is O(1) space; the recursive version is elegant but uses O(n) call-stack space.

**Full reversal (iterative):**
```python
def reverse_list(head):
    prev, curr = None, head
    while curr:
        next_node = curr.next
        curr.next = prev
        prev = curr
        curr = next_node
    return prev
```

**Reversal of a sublist** (LeetCode 92) reverses nodes from position `left` to `right`. The trick is to locate the node just before `left`, then apply a counted reversal, and reconnect the ends. Drawing out the before/after pointer state on paper prevents index-off-by-one errors that kill interview performance.

**Reverse in k-groups** (LeetCode 25) extends this: reverse every group of k nodes, leave the remainder as-is if it has fewer than k nodes. The recursive formulation is clean — reverse the first k, recurse on the rest, attach.

## Merging and Sorting Linked Lists

**Merge two sorted lists** is foundational. Use a dummy head node to avoid special-casing the first node:

```python
def merge_two_lists(l1, l2):
    dummy = ListNode(0)
    curr = dummy
    while l1 and l2:
        if l1.val <= l2.val:
            curr.next = l1
            l1 = l1.next
        else:
            curr.next = l2
            l2 = l2.next
        curr = curr.next
    curr.next = l1 or l2
    return dummy.next
```

**Merge k sorted lists** scales this with a min-heap. Push the head of each list into a heap keyed by value. Pop the minimum, append it to the result, and push that node's next (if it exists) back into the heap. Time complexity is O(N log k) where N is total nodes and k is list count.

**Sort a linked list** in O(n log n) uses merge sort. Find the midpoint with slow/fast pointers, split, sort each half recursively, merge. This is cleaner than quicksort on linked lists because random access is expensive.

## Intersection and Reordering

**Find intersection of two linked lists:** Advance both pointers; when one reaches null, redirect it to the head of the other list. After at most L1 + L2 steps, they either meet at the intersection or both reach null simultaneously (no intersection). No length computation required.

**Reorder list** (LeetCode 143) — interleave first half and reversed second half:
1. Find the middle
2. Reverse the second half
3. Merge the two halves alternately

Each sub-step uses a pattern you already know. Breaking composite problems into known sub-patterns is the meta-skill interviewers are evaluating.

## Common Pitfalls

**Off-by-one on k-th from end:** Remember that "k-th from end" is ambiguous — clarify whether k=1 means the last node or the node before last. Establish with your interviewer before coding.

**Losing references:** Always save `curr.next` before overwriting `curr.next` during reversal. Losing a reference mid-reversal produces untraceable bugs.

**Dummy node discipline:** Use a dummy head whenever the result list is built incrementally. It eliminates null-checking the head on every iteration and keeps code consistent.

**Cycle problems with empty or single-node lists:** Always handle `head is None` and `head.next is None` early.

## Practice Sequence

Work through these problems in order to build pattern recognition:
- LeetCode 141 (cycle detection) → 142 (cycle entry)
- LeetCode 206 (full reversal) → 92 (sublist reversal) → 25 (k-group reversal)
- LeetCode 21 (merge two) → 23 (merge k)
- LeetCode 148 (sort list)
- LeetCode 160 (intersection)
- LeetCode 143 (reorder)

Each problem in this sequence adds one layer of complexity to a pattern you've already internalized. That's how you build the fluency to produce clean code in 30–45 minutes under interview conditions.
