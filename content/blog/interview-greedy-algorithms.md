---
title: "Greedy Algorithms: Interview Patterns and When They Work"
description: "Master greedy algorithms for technical interviews — when greedy is optimal, proof techniques, activity selection, interval scheduling, Huffman coding, and 10 classic greedy problems with solutions."
date: "2026-03-20"
category: "Algorithms"
---

# Greedy Algorithms: Interview Patterns and When They Work

Greedy algorithms make locally optimal choices at each step hoping to reach a global optimum. The challenge: proving that the greedy choice actually leads to the global optimum, which isn't always obvious. Interviewers test both your ability to recognize greedy opportunities and your understanding of why they work.

## When Greedy Works

Greedy algorithms work when the problem has two properties:

**Greedy choice property:** A global optimum can be reached by making locally optimal choices. The choice at each step doesn't need to consider future consequences.

**Optimal substructure:** An optimal solution to the problem contains optimal solutions to subproblems.

If you make a greedy choice and the subproblem that remains is the same type of problem just smaller, greedy often works. If the greedy choice can invalidate future choices in a non-recoverable way, greedy won't work and you need dynamic programming.

## Proving Greedy Correctness

Two common proof techniques:

**Exchange argument:** Assume an optimal solution that differs from the greedy solution. Show you can exchange the non-greedy choice for the greedy choice without making the solution worse. By induction, the greedy solution is optimal.

**Inductive argument:** Show the greedy choice is never worse than any other choice at each step, so making greedy choices never closes off a path to optimality.

In interviews, you rarely need to prove optimality formally. But you should be able to articulate why your greedy choice is safe: "taking the earliest-finishing activity first never prevents us from taking more activities later."

## Activity Selection / Interval Scheduling

Classic problem: given intervals with start and end times, find the maximum number of non-overlapping intervals.

Greedy: sort by end time. Always take the interval that ends earliest. When you take an interval, skip all intervals that overlap it.

Why it works: taking the earliest-ending interval leaves the most room for future intervals. Any other choice of first interval either ends later (worse) or is the same end time (equivalent).

```python
def max_intervals(intervals):
    intervals.sort(key=lambda x: x[1])  # sort by end time
    count, last_end = 0, float('-inf')
    for start, end in intervals:
        if start >= last_end:
            count += 1
            last_end = end
    return count
```

Variant: minimum number of meeting rooms (merge intervals — overlapping intervals need separate rooms). Sort by start time, use a min-heap of end times. For each interval, if it starts after the earliest-ending room, reuse that room; otherwise add a room.

## Jump Game Variants

**Can you reach the last index?** Greedy: track the furthest position reachable. For each position, update furthest. If current position exceeds furthest, return false.

**Minimum jumps to reach end?** Greedy: track current reach and next reach. When current reach is exhausted, increment jumps and extend to next reach.

```python
def min_jumps(nums):
    jumps = curr_end = curr_far = 0
    for i in range(len(nums) - 1):
        curr_far = max(curr_far, i + nums[i])
        if i == curr_end:
            jumps += 1
            curr_end = curr_far
    return jumps
```

## Coin Change: When Greedy Fails

The classic trap: greedy fails for general coin change. Coins [1, 3, 4], target 6. Greedy picks 4, then 1, then 1 → 3 coins. Optimal: 3+3 → 2 coins.

Greedy works for coin change only when the coin system is "canonical" (like US coins: 25, 10, 5, 1 cents). In interviews, if you're asked about arbitrary coin denominations, greedy is wrong — use dynamic programming.

Understanding why greedy fails here demonstrates deeper algorithmic understanding than just knowing the DP solution.

## Task Scheduler

Given tasks with cooldown n (same task can't run within n steps), find minimum time to finish all tasks.

Greedy: always execute the most frequent remaining task (or idle if not possible). Use a max-heap.

Insight: the minimum time is `max(total_tasks, (max_freq - 1) * (n + 1) + count_of_max_freq_tasks)`. The idle slots are (max_freq - 1) * n minus the space filled by other tasks.

## Gas Station

Can you travel around a circular route? Start at any station; tank starts empty; at each station you gain `gas[i]`, travel costs `cost[i]`.

Greedy: if total gas >= total cost, a solution exists. The starting station is the point after the last station where cumulative balance goes negative.

```python
def can_complete_circuit(gas, cost):
    total = curr = start = 0
    for i in range(len(gas)):
        diff = gas[i] - cost[i]
        total += diff
        curr += diff
        if curr < 0:
            start = i + 1
            curr = 0
    return start if total >= 0 else -1
```

## Partition Labels

Given a string, partition it into as many parts as possible such that each letter appears in at most one part.

Greedy: for each character, track the last occurrence. Scan left to right. The current partition ends at the farthest last-occurrence of any character seen so far.

```python
def partition_labels(s):
    last = {c: i for i, c in enumerate(s)}
    result, start, end = [], 0, 0
    for i, c in enumerate(s):
        end = max(end, last[c])
        if i == end:
            result.append(end - start + 1)
            start = i + 1
    return result
```

## Huffman Coding (Concept)

Huffman coding builds an optimal prefix-free encoding. Greedy: merge the two lowest-frequency nodes into a combined node, repeat. The resulting binary tree assigns shorter codes to more frequent characters.

This is O(N log N) using a min-heap. The greedy property: always merging the two least frequent nodes minimizes the total encoding length.

## Recognizing Greedy Opportunities

When you see these patterns, think greedy: sorting by some attribute and making a sequential decision, problems involving "minimum cost to cover" or "maximum items selected", interval problems, problems where the locally best choice never hurts future choices. When in doubt, try to construct a counterexample where the greedy fails. If you can't, greedy likely works.

