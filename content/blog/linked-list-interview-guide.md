---
title: "Linked List Problems in Coding Interviews: Patterns and Techniques"
description: "Master linked list interview problems with Python. Learn the 5 core patterns including fast/slow pointers, reverse in place, and cycle detection, plus common mistakes and interview tips."
date: "2025-10-11"
category: "Interview Preparation"
---
# Linked List Problems in Coding Interviews: Patterns and Techniques

Linked list problems are a staple of coding interviews, particularly at the phone screen and early onsite stages. They test your ability to manipulate pointers carefully — a skill that matters enormously in systems programming even if most modern Python work rarely touches raw pointers. More importantly, linked list problems are a reliable signal to interviewers: candidates who solve them cleanly demonstrate precise thinking and the ability to track multiple state variables simultaneously. This guide covers the patterns you need and the mistakes that trip candidates up.

## Python Linked List Implementation

Before diving into patterns, you need a working node definition. In interviews, you will be given this, but you should be able to write it from memory:

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

# Build a linked list from a Python list (useful for testing)
def build_list(values: list) -> ListNode:
    dummy = ListNode(0)
    current = dummy
    for val in values:
        current.next = ListNode(val)
        current = current.next
    return dummy.next

# Convert linked list back to Python list (useful for verification)
def to_list(head: ListNode) -> list:
    result = []
    while head:
        result.append(head.val)
        head = head.next
    return result
```

The dummy node is one of the most useful patterns in linked list problems — it eliminates special-casing for an empty list or operations at the head, because you always have a node before the first real element.

## 5 Core Patterns

**Pattern 1: Fast and Slow Pointers (Floyd's Algorithm)**

Two pointers move at different speeds. The slow pointer moves one step at a time; the fast pointer moves two. This elegant technique solves multiple problems:

- Detect a cycle: if fast and slow ever point to the same node, there is a cycle
- Find the middle: when fast reaches the end, slow is at the middle
- Find the start of a cycle: after detection, move slow to head and advance both one step at a time until they meet

```python
def has_cycle(head: ListNode) -> bool:
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    return False

def find_middle(head: ListNode) -> ListNode:
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow
```

**Pattern 2: Reverse In Place**

Reversing a linked list (or a sublist) is fundamental and appears as a standalone problem and as a subroutine in harder problems. The key is maintaining three pointers: previous, current, and next.

```python
def reverse_list(head: ListNode) -> ListNode:
    prev = None
    curr = head
    while curr:
        next_node = curr.next   # save next BEFORE overwriting
        curr.next = prev        # reverse the pointer
        prev = curr             # advance prev
        curr = next_node        # advance curr
    return prev  # prev is now the new head

def reverse_between(head: ListNode, left: int, right: int) -> ListNode:
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    for _ in range(left - 1):
        pre = pre.next
    curr = pre.next
    for _ in range(right - left):
        next_node = curr.next
        curr.next = next_node.next
        next_node.next = pre.next
        pre.next = next_node
    return dummy.next
```

**Pattern 3: Find the Middle Node**

Already shown via fast/slow pointers. The subtlety is in how you define "middle" for even-length lists. The standard fast/slow approach returns the second middle node for even-length lists. Adjust by checking whether you need the first or second middle before picking your stopping condition.

**Pattern 4: Merge Sorted Lists**

Merging is the core operation of merge sort and appears in "Merge K Sorted Lists" problems. Always use a dummy head to simplify edge cases:

```python
def merge_two_lists(l1: ListNode, l2: ListNode) -> ListNode:
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

Time: O(n + m). Space: O(1). The `curr.next = l1 or l2` line at the end elegantly handles whichever list still has remaining elements.

**Pattern 5: Detect and Remove a Cycle**

Finding the cycle start requires Floyd's algorithm extended:

```python
def detect_cycle(head: ListNode) -> ListNode:
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            # Cycle detected; find start
            slow = head
            while slow != fast:
                slow = slow.next
                fast = fast.next
            return slow  # cycle start
    return None
```

The mathematical proof: when slow and fast meet inside the cycle, moving slow back to head and advancing both one step at a time guarantees they meet at the cycle's entry point.

## Common Mistakes

**Forgetting null checks.** Before accessing `node.next.next`, always check that both `node.next` and `node.next.next` are not None. A missing null check causes an AttributeError on a None object — the most common linked list bug in interviews.

**Losing track of the next pointer.** In reversal operations, always save `curr.next` to a temporary variable BEFORE redirecting `curr.next`. If you redirect first, you lose the rest of the list permanently. This is the mistake the interviewers expect you to avoid by walking through your code step by step.

**Forgetting to return the correct head.** After reversal, the original head is now the tail. The new head is `prev`. Many candidates return `head` by habit and get wrong answers on tests.

**Mutating input unexpectedly.** When the problem says "do not modify the values in the list's nodes," you must only change pointer directions, not node values. If you are reversing by swapping values, you are doing it wrong.

## Interview Tips

Draw the problem before writing code. On a whiteboard or on paper, draw the linked list with explicit boxes and arrows. Trace your algorithm manually for a 4-5 node example. This catches pointer bugs before they appear in code.

Always test on edge cases: empty list (head is None), single node, two nodes, and a list where all values are identical. These are the cases most likely to break incomplete solutions.

When a problem feels complex — like "reverse nodes in k-group" — decompose it into subroutines you already know. That problem is just "reverse a sublist" applied repeatedly, with the sublist boundaries determined by counting k steps ahead.

Finally, linked list problems are one of the few areas where the iterative solution is almost always preferred over recursive. Recursion on a linked list of length n uses O(n) stack space. Iterative uses O(1). Unless the recursive solution is significantly cleaner, go iterative and mention the space advantage to your interviewer.
