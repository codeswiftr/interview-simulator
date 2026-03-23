---
title: "Advanced Greedy Algorithms for Interviews: Interval Scheduling, Huffman Coding, and Proving Optimality"
description: "Go beyond basic greedy with interval scheduling maximization, Huffman coding, fractional knapsack, activity selection, and the exchange argument proof technique used in competitive programming."
date: "2026-03-20"
category: "Algorithms"
---

# Advanced Greedy Algorithms for Interviews

Greedy algorithms are deceptively tricky in interviews. The mechanics are often simple — sort and pick — but the intellectual challenge is proving that the greedy choice is correct. Strong candidates don't just implement greedy; they justify it. This post covers advanced greedy patterns and the proof techniques that separate good answers from great ones.

## What Makes a Greedy Algorithm Correct?

A greedy algorithm makes the locally optimal choice at each step and never reconsiders it. The algorithm is correct when:

1. **Greedy choice property**: A globally optimal solution can always be constructed by making the locally optimal choice
2. **Optimal substructure**: The problem's optimal solution contains optimal solutions to subproblems

The standard proof technique is the **exchange argument**: assume an optimal solution exists that differs from the greedy solution. Show that you can "exchange" the differing part with the greedy choice without worsening the solution — contradicting the assumption that the original was strictly better.

## Pattern 1: Interval Scheduling Maximization

**Problem:** Given n activities with start and end times, select the maximum number of non-overlapping activities.

**Greedy choice:** Always select the activity with the earliest finish time.

```python
def max_activities(activities: list[tuple[int, int]]) -> list[tuple[int, int]]:
    # Sort by end time
    activities.sort(key=lambda x: x[1])
    selected = [activities[0]]

    for start, end in activities[1:]:
        if start >= selected[-1][1]:  # No overlap
            selected.append((start, end))

    return selected
# Time: O(n log n), Space: O(1)
```

**Proof (exchange argument):**
Suppose an optimal solution OPT doesn't start with the activity `a` with the earliest finish time. Take the first activity `b` in OPT. Replace `b` with `a`. Since `a` finishes no later than `b`, any activity compatible with `b` is still compatible with `a`. So the replaced solution is no worse — OPT with `a` is also optimal.

**Variants:**
- **Weighted interval scheduling**: Greedy fails here — use DP with binary search
- **Minimum number of rooms** (interval partitioning): Greedy by start time + min-heap

## Pattern 2: Activity Selection with Deadlines

**Problem:** Each job has a deadline and profit. Maximize profit by scheduling at most one job per time unit.

```python
def max_profit_jobs(jobs: list[tuple[int, int, int]]) -> int:
    # jobs: (start, deadline, profit)
    jobs.sort(key=lambda x: -x[2])  # Sort by decreasing profit
    max_deadline = max(j[1] for j in jobs)
    slots = [-1] * (max_deadline + 1)
    total = 0

    for profit, deadline, _ in sorted(jobs, key=lambda x: -x[2]):
        # Find latest available slot before deadline
        for t in range(min(deadline, max_deadline), 0, -1):
            if slots[t] == -1:
                slots[t] = profit
                total += profit
                break

    return total
```

For large inputs, use a Union-Find structure to find the latest free slot in O(α(n)) — a common follow-up question.

## Pattern 3: Huffman Coding

Huffman coding builds an optimal prefix-free code. It's a classic greedy application where the proof of optimality is beautiful.

**Greedy choice:** Always merge the two lowest-frequency nodes.

```python
import heapq
from dataclasses import dataclass, field
from typing import Optional

@dataclass(order=True)
class HuffmanNode:
    freq: int
    char: Optional[str] = field(compare=False, default=None)
    left: Optional['HuffmanNode'] = field(compare=False, default=None)
    right: Optional['HuffmanNode'] = field(compare=False, default=None)

def huffman_tree(freq: dict[str, int]) -> HuffmanNode:
    heap = [HuffmanNode(f, c) for c, f in freq.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(left.freq + right.freq, left=left, right=right)
        heapq.heappush(heap, merged)

    return heap[0]

def get_codes(node: HuffmanNode, prefix="", codes=None) -> dict[str, str]:
    if codes is None:
        codes = {}
    if node.char:
        codes[node.char] = prefix or "0"
    else:
        get_codes(node.left, prefix + "0", codes)
        get_codes(node.right, prefix + "1", codes)
    return codes
```

**Time:** O(n log n). **Proof of optimality:** The two least frequent characters must be at the greatest depth in the optimal tree (otherwise swap them with deeper characters to improve cost). They can be siblings (merge them and reduce to a subproblem). Induction completes the proof.

## Pattern 4: Fractional Knapsack

Unlike 0/1 knapsack (requires DP), the fractional variant has a greedy solution.

**Greedy choice:** Sort items by value/weight ratio, take as much of the highest-ratio item as possible.

```python
def fractional_knapsack(items: list[tuple[float, float]], capacity: float) -> float:
    # items: (value, weight)
    items.sort(key=lambda x: x[0] / x[1], reverse=True)
    total_value = 0.0

    for value, weight in items:
        if capacity <= 0:
            break
        take = min(weight, capacity)
        total_value += take * (value / weight)
        capacity -= take

    return total_value
```

**Why greedy works:** Any solution that doesn't take as much as possible of the highest-ratio item can be improved by swapping a fraction of another item for the high-ratio item — contradicting optimality.

**Why 0/1 knapsack doesn't:** You can't take fractions, so a greedy item might "waste" capacity that a combination of smaller items fills optimally.

## Pattern 5: Gas Station / Circular Greedy

**Problem:** Gas stations in a circle with gas[i] and cost[i]. Find the starting station to complete the circuit.

```python
def can_complete_circuit(gas: list[int], cost: list[int]) -> int:
    if sum(gas) < sum(cost):
        return -1

    tank = 0
    start = 0

    for i in range(len(gas)):
        tank += gas[i] - cost[i]
        if tank < 0:  # Can't proceed from current start
            start = i + 1
            tank = 0

    return start
```

**Key insight:** If total gas ≥ total cost, a solution exists. If you can't reach station i from start j, then no station between j and i can be a valid start (any such intermediate start inherits a partial deficit). This is the non-obvious greedy leap that requires proof.

## Pattern 6: Jump Game

**Problem:** Given an array where each element is the max jump length, can you reach the last index?

```python
def can_jump(nums: list[int]) -> bool:
    max_reach = 0
    for i, jump in enumerate(nums):
        if i > max_reach:
            return False
        max_reach = max(max_reach, i + jump)
    return True

def jump_minimum(nums: list[int]) -> int:
    jumps = 0
    current_end = 0
    farthest = 0

    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == current_end:  # Must jump — extend window to farthest reach
            jumps += 1
            current_end = farthest

    return jumps
```

## Proving Your Greedy is Wrong: Counterexamples

A key skill is recognizing when greedy *doesn't* work:

- **Coin change**: Greedy (largest coin first) fails for arbitrary denominations — `{1, 3, 4}`, target 6: greedy gives `4+1+1=3 coins`, optimal is `3+3=2 coins`
- **0/1 Knapsack**: As discussed above
- **Longest path in a graph**: Greedy on edge weights fails — longest path is NP-hard in general

## Interview Framework for Greedy Problems

When you suspect greedy applies:
1. **State the greedy choice**: "At each step, I will pick the X with the smallest/largest Y"
2. **Prove the exchange argument**: "If OPT differs, I can swap without worsening the solution"
3. **Verify optimal substructure**: "After the first greedy choice, the remaining subproblem has the same structure"
4. **Implement and check edge cases**: Empty input, single element, all-same values

The ability to articulate the exchange argument verbally — even informally — is what elevates a greedy solution from "code that works on examples" to a proof that it always works.
