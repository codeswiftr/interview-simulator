---
title: "Dynamic Arrays and Amortized Analysis: Interview Deep Dive"
description: "Master dynamic arrays for technical interviews — amortized O(1) append, resizing strategies, ArrayList vs LinkedList tradeoffs, and common array manipulation patterns asked at FAANG."
date: "2026-03-20"
category: "Algorithms"
---

# Dynamic Arrays and Amortized Analysis: Interview Deep Dive

Dynamic arrays are the foundation of most programming languages' list implementations — Python's `list`, Java's `ArrayList`, C++'s `vector`. Yet most engineers can't explain why append is O(1) amortized or when resizing hurts performance. Interviewers know this and probe accordingly.

## How Dynamic Arrays Work

A dynamic array is a contiguous block of memory with a capacity (allocated size) and a length (used size). When the array fills, it allocates a new block (typically 2× larger), copies all elements, and frees the old block.

The question interviewers ask: if resize happens every N elements and copies N items, isn't append O(N)? The answer is amortized analysis — spread the cost over all appends.

With doubling: after N appends from empty, total copies = N/2 + N/4 + ... + 1 < N. So N appends perform fewer than 2N total operations — O(1) amortized per append.

## Resizing Strategies

**Doubling (growth factor 2):** Most common. Each append is amortized O(1). Memory waste up to 50% (half the allocated block may be empty). Python uses 1.125× growth for small arrays scaling to approximately 1.125, Java `ArrayList` uses 1.5×, C++ `vector` uses 2×.

**Why not grow by a fixed amount (e.g., +10)?** Append becomes O(N) amortized — after N appends you've done O(N²) total copies.

**Shrinking:** Many implementations don't shrink until the array is less than 25% full (to avoid thrashing on alternating push/pop). Python's list doesn't shrink on `pop()` unless the list is very small.

## Amortized Analysis in Interviews

The bank account analogy: charge each append 3 tokens — 1 for the actual append, 2 saved. When resize occurs, use the 2N saved tokens to pay for copying N existing items plus N new items. Account never goes negative → O(1) amortized.

Interviewers may ask you to prove amortized O(1) for a custom data structure. Apply the same technique: define a potential function and show the amortized cost of each operation is bounded.

## ArrayList vs LinkedList

The question appears in Java interviews but the principle is universal:

| Operation | ArrayList | LinkedList |
|-----------|-----------|------------|
| Random access | O(1) | O(N) |
| Append (end) | O(1) amortized | O(1) |
| Insert (middle) | O(N) | O(1) with pointer |
| Memory | Better (contiguous) | Worse (pointer overhead) |
| Cache performance | Excellent | Poor |

The practical answer: use dynamic arrays for almost everything. Linked lists win only for frequent O(1) insertion/deletion in the middle when you already have a pointer to the node — a rare case in practice.

## Array Manipulation Patterns

**Two pointers:** Most in-place array problems (reverse, remove duplicates, move zeros) use two pointers. One for reading, one for writing. Examples: `removeElement`, `removeDuplicates`, `moveZeroes`.

**Prefix sums:** Precompute cumulative sums for O(1) range sum queries. Pattern: `prefix[i] = prefix[i-1] + arr[i]`. Range sum [l, r] = `prefix[r] - prefix[l-1]`.

**Sliding window:** For subarray problems with a constraint, maintain a window that expands/contracts. Avoids O(N²) brute force. Two flavors: fixed size (window always has k elements) and variable size (window satisfies/violates condition).

**Kadane's algorithm:** Maximum subarray sum in O(N). `curr = max(nums[i], curr + nums[i])`. Classic DP on arrays.

## Interview Questions

Common dynamic array questions: rotate array by k positions (reverse three times), product of array except self (prefix + suffix product arrays, O(1) space with a running product trick), find duplicate in 1..N array (Floyd's cycle detection treating array as linked list), merge sorted arrays from the end in-place.

For the product-except-self problem without division: forward pass builds prefix products left of i; backward pass accumulates suffix products right of i while writing to the result array. O(N) time, O(1) extra space (not counting output).

## Memory Alignment and Cache

Dynamic arrays beat linked lists in practice not just on paper — cache lines load 64 bytes at a time, so accessing `arr[i]` also loads `arr[i+1]` through `arr[i+7]` (for 8-byte elements) into cache. Traversal is nearly free after the first access. Linked list node traversal follows pointers to arbitrary memory locations, causing a cache miss for nearly every node.

This is why benchmarks show ArrayList outperforming LinkedList for nearly all operations even when algorithmic complexity suggests LinkedList should win.

## Implementation Notes

If asked to implement a dynamic array in an interview: start with fixed-capacity array and size counter, implement `get(i)` with bounds check, `set(i, val)` with bounds check, `append(val)` with resize when full, `insert(i, val)` by shifting elements right, and `delete(i)` by shifting elements left. Skip shrinking unless asked — it adds complexity without changing the core concepts the interviewer is testing.

