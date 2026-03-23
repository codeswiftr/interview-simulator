---
title: "Hash Tables in Coding Interviews: From Basics to Advanced Patterns"
description: "Master hash table problems for technical interviews. Covers hash map fundamentals, collision handling, frequency counting, two-sum patterns, and sliding window with hash maps."
date: "2025-10-05"
category: "Interview Preparation"
---

# Hash Tables in Coding Interviews

Hash tables (hash maps in Python, objects in JavaScript, `map` in C++/Go) are involved in more coding interview solutions than almost any other data structure. Understanding when and how to use them is essential for interview success.

## Why Hash Tables Are So Powerful

Hash tables provide O(1) average-case lookup, insertion, and deletion. This property lets you trade space for time — a core pattern in competitive programming and interviews.

The fundamental trade-off: If you've seen something before, you can remember it in a hash table and look it up in O(1) instead of rescanning an array in O(n).

**When to reach for a hash table:**
- "Have I seen this element before?"
- "How many times have I seen this element?"
- "What's the complement of this element that would satisfy some condition?"
- "Is there a fast way to look up a related value given a key?"

## Core Pattern 1: Frequency Counting

Count occurrences of elements. Almost every string or array problem where you need to compare distributions uses this.

```python
from collections import Counter

# Problem: Are two strings anagrams?
def is_anagram(s, t):
    return Counter(s) == Counter(t)

# Manual frequency count
def is_anagram_manual(s, t):
    if len(s) != len(t):
        return False
    count = {}
    for c in s:
        count[c] = count.get(c, 0) + 1
    for c in t:
        if count.get(c, 0) == 0:
            return False
        count[c] -= 1
    return True
```

**Common problems**: Group Anagrams, Top K Frequent Elements, Minimum Window Substring.

## Core Pattern 2: Two-Sum / Complement Lookup

Instead of O(n²) nested loops to find pairs, use a hash map to record what you've seen and look up complements in O(1).

```python
# Classic two-sum: find two indices summing to target
def two_sum(nums, target):
    seen = {}  # value -> index
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
```

**Extension:** Three sum = fix one element, then two-sum on the rest. Four sum = fix two, two-sum on the rest.

## Core Pattern 3: Sliding Window with Hash Map

Combine sliding window with a hash map when you need to track character/element frequencies within a window.

```python
# Minimum window substring containing all chars of t
def min_window(s, t):
    need = Counter(t)
    have = {}
    formed = 0
    required = len(need)
    left = 0
    result = ""
    min_len = float('inf')
    
    for right, c in enumerate(s):
        have[c] = have.get(c, 0) + 1
        if c in need and have[c] == need[c]:
            formed += 1
        
        while formed == required:
            window = s[left:right+1]
            if len(window) < min_len:
                min_len = len(window)
                result = window
            have[s[left]] -= 1
            if s[left] in need and have[s[left]] < need[s[left]]:
                formed -= 1
            left += 1
    
    return result
```

**Common problems**: Longest Substring Without Repeating Characters, Fruit Into Baskets, Permutation in String.

## Core Pattern 4: Prefix Sum with Hash Map

Store prefix sums in a hash map to answer "how many subarrays sum to k?" in O(n).

```python
# Count subarrays summing to k
def subarray_sum(nums, k):
    count = 0
    prefix_sum = 0
    seen = {0: 1}  # prefix_sum -> frequency
    
    for num in nums:
        prefix_sum += num
        count += seen.get(prefix_sum - k, 0)
        seen[prefix_sum] = seen.get(prefix_sum, 0) + 1
    
    return count
```

**Why it works**: If prefix_sum[j] - prefix_sum[i] = k, then the subarray from i+1 to j sums to k. By storing prefix sums in a map, we can look up how many previous prefix sums equal prefix_sum - k.

## Core Pattern 5: Group By Key

Group elements with a shared property using a hash map of lists.

```python
# Group anagrams together
def group_anagrams(strs):
    groups = {}
    for s in strs:
        key = tuple(sorted(s))  # Canonical form
        groups.setdefault(key, []).append(s)
    return list(groups.values())
```

**Variation**: Use frozen sorted tuple as key, character frequency tuple as key, or any computed canonical form.

## Handling Hash Collisions (Theory Question)

Interviewers occasionally ask about hash map internals:

**Chaining**: Each bucket holds a linked list. Collision = append to list. O(1) average, O(n) worst case (all collide).

**Open addressing**: On collision, probe for next empty slot (linear probing, quadratic probing, double hashing). Better cache performance, sensitive to load factor.

**Python's implementation**: CPython uses open addressing with a compact hash table. Python 3.7+ dicts maintain insertion order.

## Space-Time Trade-offs

Hash tables use O(n) extra space. Sometimes an interviewer will ask for O(1) space, which means you can't use a hash map and need a different approach (sorting, two pointers, etc.).

Always state the space complexity of your solution. "I'm using a hash map here, so this is O(n) space — would you like me to discuss a space-optimized approach?"

## Common Interview Mistakes with Hash Maps

1. **Forgetting to check existence**: `d[key]` vs `d.get(key, default)` — the former raises KeyError
2. **Using lists as keys**: Lists are unhashable; convert to tuples
3. **Off-by-one in the seen set**: In sliding window, be careful about when you add to `seen` (before or after processing)
4. **Ignoring hash collision edge cases**: In interviews, mentioning you know collisions exist (even if not implementing collision handling) shows depth

Hash tables are the fastest path from O(n²) to O(n) in most interview problems. Internalizing these 5 patterns will let you recognize when and how to apply them on sight.
