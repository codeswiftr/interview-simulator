---
title: "Strategy for LeetCode Hard Problems: When to Attempt Them and How to Approach"
description: "How to approach hard LeetCode problems — which categories of hards actually appear in interviews, time/effort tradeoff, mental models for breaking down hard problems, and specific hard problem patterns worth knowing."
date: "2026-03-20"
category: "Algorithms"
---

# Strategy for LeetCode Hard Problems: When to Attempt Them and How to Approach

Most interview candidates have an unhealthy relationship with hard problems. Some avoid them entirely, relying only on mediums and hoping for the best. Others spend weeks grinding hard problems when they would have been far better served by perfecting their medium-level execution. A smaller group understands the actual ROI of hard problems and uses them strategically.

This guide is for that last group, or for anyone who wants to join it.

## The Real Distribution of Hard Problems in Interviews

First, a reality check: the overwhelming majority of technical interviews — including at top-tier companies — use medium-difficulty problems. A 2024 analysis of Glassdoor and Blind interview reports estimated that hard problems account for roughly 15–20% of questions even at the most demanding companies. At most mid-sized and large tech companies, hard problems are rare.

That said, certain companies and certain roles are exceptions. Competitive trading firms (Jane Street, Citadel, HRT), some ML engineering roles, and occasional FAANG rounds do use hard problems. If you're targeting those specifically, hard practice is justified. If you're not, the ROI math shifts.

## Which Hard Problems Actually Appear

Not all hard problems are created equal. Some hard problems are hard because of a genuinely difficult insight; others are hard primarily because of implementation complexity. Interview hard problems skew toward the former — a clean insight that's non-obvious, not a 150-line implementation.

**Hard problem categories that appear in interviews:**

- **Sliding window (hard variant):** Problems like "minimum window substring" or "sliding window maximum" where you need a monotonic deque or careful window management. These appear at a surprising frequency relative to their difficulty label.
- **Two-pointer with sorting:** Some hard two/three-sum variants. The insight is usually clear once you've done enough medium problems, but the edge cases are unforgiving.
- **Graph hard:** Topological sort with cycle detection on complex graphs, shortest path in a weighted graph with constraints, minimum spanning tree variants. These appear in platform and infrastructure interviews.
- **DP hard — 1D/2D:** Edit distance, coin change II, burst balloons, and similar. Interviewers who use these usually signal it in advance or reserve them for staff-level roles.
- **Interval problems:** Meeting rooms III, task scheduler, employee free time. These require understanding event-based simulation or interval merging at a deeper level.

**Hard problems that rarely appear:**

- Segment trees and Fenwick trees — except at very specialized roles
- Suffix arrays and advanced string algorithms
- Network flow (max flow, min cut) — almost never in standard engineering interviews
- Advanced graph algorithms (Dijkstra's variants, A* search) — occasionally in game company interviews

## The Hard Problem Approach

When you encounter a hard problem — whether in a contest, practice, or (less likely) an interview — the effective approach is systematic:

**1. Simplify the constraints.** Strip the problem to a minimal version. If the problem asks for an optimal solution across all inputs, first ask: what would the answer be for a tiny, trivial case? Build up from there.

**2. Solve the related subproblem.** Almost every hard problem has a medium or easy subproblem embedded in it. Identify it. Can you solve the problem if you ignore one of the constraints? Can you solve it with a brute force approach? The brute force gives you something to optimize from.

**3. Work small examples by hand.** Don't read a hard problem and immediately start coding. Trace through three or four examples manually. Patterns usually emerge from this that aren't visible from reading the problem statement.

**4. Recognize the pattern family.** Hard problems usually belong to a recognizable family. If you see "next greater element" or "temperature" intuitions, think monotonic stack. If you see overlapping subproblems, think DP. If you see a stream of intervals, think heap.

**5. Accept non-optimal first passes.** A working O(n²) solution is better than a half-implemented O(n log n) solution. Get something running, then optimize. In an interview, a working slower solution with a discussion of why it can be optimized often scores better than a broken optimal solution.

## Patterns Worth Knowing for Hards

If you're going to spend time on hard problems, these patterns offer the best ROI:

**Monotonic stack.** Used in "next greater element," "largest rectangle in histogram," "maximal rectangle," and "trapping rainwater" (hard variant). Once you internalize the pattern — maintain a stack where elements are in monotonic order — a whole category of hard problems becomes approachable.

**Advanced DP — interval DP.** Problems like "burst balloons," "strange printer," and "minimum cost to merge stones" follow a pattern where you define `dp[i][j]` as the optimal value over a range. Understanding how to think about interval subproblems unlocks several of the most commonly cited hard DP problems.

**Binary search on the answer.** Some hard optimization problems become tractable when you binary search on the answer value and check feasibility. "Split array largest sum" and "koko eating bananas" (medium, but the pattern scales to hard) exemplify this.

**Bit manipulation for state.** Some hard DP problems on sets use bitmask DP where the state includes a bitmask of visited elements. This appears in traveling salesman variants and some assignment problems.

## When to Skip Hards in Your Prep

If you have six weeks before your target interviews, here is the honest advice: prioritize mastering mediums first.

Hard problems reward you at the margin. If you can't consistently solve mediums within 20–25 minutes, grinding hards will not fix that — it will just expose you to problems you can't solve, which is demoralizing and teaches bad habits.

The right trigger for adding hards to your practice is: you're solving new medium problems reliably, your medium time-to-solution is dropping, and you're targeting a company or role where hards are genuinely expected.

At that point, pick 15–20 hards from the categories above, solve them, review the patterns, and move on. Hard problems reward diminishing returns quickly — a narrow, deep practice beats broad hard problem exposure every time.
