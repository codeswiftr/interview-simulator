---
title: "Dynamic Programming Pattern Recognition: The Complete Framework"
description: "A systematic approach to recognizing and solving DP problems in interviews — the 5 DP categories, state design, transition formulation, space optimization, and the mental model that turns DP from intimidating to mechanical."
date: "2026-03-20"
category: "Algorithms"
---

# Dynamic Programming Pattern Recognition: The Complete Framework

Dynamic programming stops being intimidating when you realize that most interview DP problems fit into a small number of categories with predictable state designs and transitions. This guide gives you the pattern recognition framework that turns DP from "guess and check" into a systematic process.

## The Five DP Categories

**1. Linear DP:** State depends on previous index/indices. Fibonacci, climbing stairs, house robber, maximum subarray.
- State: `dp[i]` = answer for problem up to index i
- Transition: `dp[i] = f(dp[i-1], dp[i-2], ..., arr[i])`

**2. Interval DP:** State is a subinterval [i, j]. Matrix chain multiplication, burst balloons, palindrome partitioning, stone merge.
- State: `dp[i][j]` = answer for subproblem on interval [i, j]
- Transition: Try all split points k between i and j

**3. Knapsack DP:** Choose items to optimize value subject to weight constraint. 0/1 knapsack, unbounded knapsack, subset sum, coin change.
- State: `dp[i][w]` = best value using first i items with weight limit w
- Transition: take or skip item i

**4. Grid DP:** State is a position in a 2D grid. Unique paths, minimum path sum, dungeon game, cherry pickup.
- State: `dp[i][j]` = answer at cell (i, j)
- Transition: from adjacent cells

**5. State machine DP:** Multiple states with transitions. Stock buy/sell with cooldown, best time to buy/sell with k transactions, regex matching.
- State: `dp[i][state]` = best answer at index i in state s
- Transition: state machine rules

## The DP Design Process

For any DP problem, ask these questions in order:

**Step 1: Identify the recurrence.** What is the optimal substructure? Can the optimal solution to the full problem be built from optimal solutions to subproblems? If yes, you likely have a DP problem.

**Step 2: Define the state.** What information do you need to fully characterize a subproblem? This becomes your DP array dimensions. Common state dimensions: current index, remaining budget/capacity, current state (state machine), endpoints of an interval.

**Step 3: Write the transition.** Given the current state, what choices can you make? For each choice, how does the cost/value relate to smaller subproblems?

**Step 4: Identify base cases.** Empty subproblems, single elements, boundary conditions.

**Step 5: Determine evaluation order.** Ensure subproblems are solved before they're needed. For `dp[i]` depending on `dp[i-1]`, process left to right.

**Step 6: Extract the answer.** Which state(s) represent the full problem's answer?

## Pattern 1: Linear DP — House Robber

```python
def rob(nums):
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]

    dp = [0] * len(nums)
    dp[0] = nums[0]
    dp[1] = max(nums[0], nums[1])

    for i in range(2, len(nums)):
        dp[i] = max(dp[i-1], dp[i-2] + nums[i])

    return dp[-1]
```

Space optimization: since dp[i] only depends on dp[i-1] and dp[i-2], use two variables:

```python
prev2, prev1 = nums[0], max(nums[0], nums[1])
for i in range(2, len(nums)):
    curr = max(prev1, prev2 + nums[i])
    prev2, prev1 = prev1, curr
return prev1
```

## Pattern 2: Interval DP — Burst Balloons

"Burst all balloons to maximize coins. When bursting balloon i, you earn nums[i-1] * nums[i] * nums[i+1]."

The key insight: think about the last balloon you burst in an interval, not the first.

```python
def maxCoins(nums):
    nums = [1] + nums + [1]  # Sentinels
    n = len(nums)
    dp = [[0] * n for _ in range(n)]

    for length in range(2, n):
        for left in range(n - length):
            right = left + length
            for k in range(left + 1, right):  # k = last burst in (left, right)
                coins = nums[left] * nums[k] * nums[right]
                dp[left][right] = max(
                    dp[left][right],
                    dp[left][k] + coins + dp[k][right]
                )

    return dp[0][n-1]
```

## Pattern 3: Knapsack — Coin Change

```python
def coinChange(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0

    for a in range(1, amount + 1):
        for coin in coins:
            if coin <= a:
                dp[a] = min(dp[a], dp[a - coin] + 1)

    return dp[amount] if dp[amount] != float('inf') else -1
```

Unbounded knapsack pattern: each coin can be used multiple times. Process amounts from 1 to target; for each, try all coins.

## Pattern 4: State Machine DP — Stock with Cooldown

Three states: held (have stock), sold (just sold, in cooldown), rest (no stock, not in cooldown).

```python
def maxProfit(prices):
    held = -prices[0]   # Buy at day 0
    sold = 0            # After selling
    rest = 0            # Resting (no stock, no cooldown)

    for price in prices[1:]:
        prev_held, prev_sold, prev_rest = held, sold, rest

        held = max(prev_held, prev_rest - price)   # Keep or buy
        sold = prev_held + price                    # Sell
        rest = max(prev_rest, prev_sold)            # Keep resting or come off cooldown

    return max(sold, rest)
```

## Space Optimization Patterns

When `dp[i]` only depends on a constant number of previous states, reduce to O(1) or O(k) space.

**Rolling array for 2D DP:** If `dp[i][j]` depends only on `dp[i-1][*]`, use two 1D arrays and alternate:

```python
prev = dp[0]  # Previous row
for i in range(1, m):
    curr = [0] * n
    for j in range(n):
        curr[j] = ...  # Function of prev[j] and curr[j-1]
    prev = curr
```

**In-place 1D for 0/1 knapsack:** Process weights in reverse to avoid using an item twice:

```python
for item_weight, item_val in items:
    for w in range(capacity, item_weight - 1, -1):  # Reverse!
        dp[w] = max(dp[w], dp[w - item_weight] + item_val)
```

## The Interview Mental Model

When you see a DP problem, cycle through:
1. "Optimal substructure?" — Can I build the answer from smaller answers?
2. "What category?" — Linear, interval, knapsack, grid, or state machine?
3. "What are the state dimensions?" — What info characterizes a subproblem?
4. "What's the transition?" — For each state, what choices lead to which other states?

The most common interview mistake: defining the wrong state. If the transition is complicated or requires multiple "previous" states, your state definition is likely too narrow. Broaden it to capture the necessary context.

For the exam: be able to code the basic 1D knapsack, LCS, and matrix chain multiplication from scratch. These cover the core patterns from which most DP variations derive.
