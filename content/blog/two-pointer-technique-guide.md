---
title: "Two Pointer Technique: The Complete Guide for Coding Interviews"
description: "Master the two-pointer technique for coding interviews. Learn when to use it, how to apply it to arrays, linked lists, and strings, plus 10 classic problems with solutions."
date: "2025-09-28"
category: "Interview Preparation"
---

# Two Pointer Technique: Complete Guide for Coding Interviews

The two-pointer technique is one of the most versatile and commonly tested patterns in coding interviews. Mastering it can reduce O(n²) brute force solutions to O(n) — the kind of optimization that impresses interviewers and demonstrates algorithmic thinking.

## What Is the Two Pointer Technique?

Two pointers simply means using two index variables to traverse a data structure, typically an array or linked list. The key insight is that by moving these pointers intelligently based on conditions, you can avoid redundant work.

There are two main variants:

**Same-direction pointers (fast/slow):**
Both pointers start at the same end and move in the same direction at different speeds. Used for linked list cycle detection, removing duplicates, and finding the middle of a linked list.

**Opposite-direction pointers (left/right):**
One pointer starts at the beginning, one at the end, and they move toward each other. Used for two-sum on sorted arrays, checking palindromes, and container problems.

## When to Use Two Pointers

Look for these signals in an interview problem:
- The input is **sorted** (or can be sorted without breaking the problem)
- You're asked to find **pairs** that satisfy a condition
- You need to **partition** an array in place
- The problem involves a **sliding window** over a sequence
- You're working with a **linked list** and need relative position tracking

Red flag to NOT use: unsorted data where the relative position of elements matters and you can't sort.

## Core Patterns

### Pattern 1: Two Sum on Sorted Array

**Problem:** Find two numbers in a sorted array that sum to a target.

```python
def two_sum_sorted(nums, target):
    left, right = 0, len(nums) - 1
    while left < right:
        current_sum = nums[left] + nums[right]
        if current_sum == target:
            return [left, right]
        elif current_sum < target:
            left += 1  # Need larger sum
        else:
            right -= 1  # Need smaller sum
    return []
```

Why it works: Because the array is sorted, moving `left` right always increases the sum; moving `right` left always decreases it. We never need to re-examine pairs.

**Time:** O(n) | **Space:** O(1)

### Pattern 2: Valid Palindrome

**Problem:** Check if a string is a palindrome after removing non-alphanumeric characters.

```python
def is_palindrome(s):
    left, right = 0, len(s) - 1
    while left < right:
        while left < right and not s[left].isalnum():
            left += 1
        while left < right and not s[right].isalnum():
            right -= 1
        if s[left].lower() != s[right].lower():
            return False
        left += 1
        right -= 1
    return True
```

### Pattern 3: Remove Duplicates In Place

**Problem:** Remove duplicates from a sorted array in place, return the new length.

```python
def remove_duplicates(nums):
    if not nums:
        return 0
    slow = 0
    for fast in range(1, len(nums)):
        if nums[fast] != nums[slow]:
            slow += 1
            nums[slow] = nums[fast]
    return slow + 1
```

`slow` points to the last unique element; `fast` scans ahead to find the next unique value.

### Pattern 4: Floyd's Cycle Detection (Linked List)

**Problem:** Detect a cycle in a linked list.

```python
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    return False
```

The slow pointer moves one step; the fast pointer moves two. If there's a cycle, they'll eventually meet inside it.

### Pattern 5: Container With Most Water

**Problem:** Given heights at each index, find two lines forming a container with maximum water.

```python
def max_area(height):
    left, right = 0, len(height) - 1
    max_water = 0
    while left < right:
        width = right - left
        water = width * min(height[left], height[right])
        max_water = max(max_water, water)
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    return max_water
```

Key insight: the water is bounded by the shorter wall. Moving the shorter wall inward is the only move that could ever increase water.

## Three Pointers: An Extension

Some problems extend naturally to three pointers. The classic is **3Sum** (find all unique triplets summing to zero):

```python
def three_sum(nums):
    nums.sort()
    result = []
    for i in range(len(nums) - 2):
        if i > 0 and nums[i] == nums[i-1]:
            continue  # Skip duplicates for first element
        left, right = i + 1, len(nums) - 1
        while left < right:
            s = nums[i] + nums[left] + nums[right]
            if s == 0:
                result.append([nums[i], nums[left], nums[right]])
                while left < right and nums[left] == nums[left+1]:
                    left += 1
                while left < right and nums[right] == nums[right-1]:
                    right -= 1
                left += 1
                right -= 1
            elif s < 0:
                left += 1
            else:
                right -= 1
    return result
```

## Interview Tips for Two Pointer Problems

**1. Always clarify if the array is sorted.** Two pointers on unsorted arrays require sorting first (adding O(n log n)) or a different approach entirely.

**2. Clarify whether you can modify the array.** Some "in place" problems require O(1) extra space; others allow O(n) extra space.

**3. Draw it out.** Before coding, draw the initial state, a mid-state, and the final state with both pointers annotated. This prevents off-by-one errors.

**4. State your invariant.** Before each while loop iteration, what is always true? Naming this invariant makes your code easier to reason about and impresses interviewers.

**5. Handle edge cases**: empty array, single element, two elements, all identical elements.

The two-pointer technique rewards pattern recognition. Once you've internalized the 5 patterns above, you'll start seeing two-pointer solutions within seconds of reading a problem — which is exactly the kind of fluency that makes the difference between "passed" and "strong hire."
