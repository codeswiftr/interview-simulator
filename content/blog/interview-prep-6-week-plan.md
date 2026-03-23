---
title: "6-Week Interview Preparation Plan: From Zero to Offer-Ready"
description: "A structured, week-by-week interview preparation plan for software engineers — covering data structures, algorithms, system design, behavioral interviews, and the psychological preparation that most guides skip."
date: "2026-03-20"
category: "Interview Prep"
---

# 6-Week Interview Preparation Plan: From Zero to Offer-Ready

Most interview preparation advice tells you what to study but not how to structure six weeks of actual time alongside a job, family, and life. This plan is different: it's structured for real constraints, progressive in difficulty, and covers the full stack of modern software engineering interviews — not just LeetCode.

## Before Week 1: Baseline Assessment

Before you start, spend 2 hours honestly assessing your current state:

1. **Solve 5 LeetCode easy problems** without looking anything up. Time yourself.
2. **Write out a system design** for a URL shortener (Bitly) from memory. No notes.
3. **Tell your "why are you leaving / why this company" story** out loud. Record yourself.

This reveals your actual gaps. Common findings:
- Strong DS/A, weak system design — common for engineers who've been heads-down in a codebase
- Strong system design, rusty DS/A — common for senior engineers who haven't done interviews in years
- Both weak — genuinely starting from scratch, which this plan handles

## Week 1: Foundation Reset

**Daily commitment: 1.5–2 hours**

**Data structures review (3 days):**
- Arrays, strings, hash maps — review the operations and complexities
- Stacks, queues, linked lists — implement each from scratch once
- Trees: BST properties, BFS, DFS (inorder/preorder/postorder)
- Don't try to solve hard problems yet. Build confidence with easy problems.

**Target: 15 easy LeetCode problems** across arrays (Two Sum, Contains Duplicate), strings (Valid Palindrome, Valid Anagram), and trees (Maximum Depth of Binary Tree, Symmetric Tree).

**Behavioral: Draft your stories**
Write three concrete examples from your career using STAR format (Situation, Task, Action, Result). These become your building blocks for every behavioral question. Choose stories that show: technical leadership, handling conflict, delivering under pressure.

**System design: Read, don't design**
Read one system design resource per day. Understand what load balancers do, what databases are good at, what caches solve. Don't design systems yet — build vocabulary.

## Week 2: Core Patterns

**Daily commitment: 2 hours**

**Algorithms focus (5 days):**
- Binary search: solve 5 problems. Master the boundary condition (lo < hi vs lo <= hi, return lo vs hi)
- Sliding window: understand the two-pointer approach for subarray problems
- Two pointers: sorted array problems, palindrome checks
- Recursion and backtracking: understand the call stack; solve N-Queens and letter combinations

**Target: 20 medium problems.** Accept that you'll look at hints. The goal is pattern recognition, not pure problem-solving.

**Behavioral: Practice out loud**
Set a timer for 2 minutes and answer "Tell me about a time you disagreed with a technical decision" out loud. The difference between reading a story and saying it smoothly is enormous. Do this daily.

**System design: Your first design**
Design a parking lot system. It sounds trivial but forces you to think about object modeling, class design, and state management. This pattern appears in actual interviews.

## Week 3: Intermediate DS/A

**Daily commitment: 2 hours**

**Data structures:**
- Heaps/Priority queues: top-K problems, median of data stream
- Graphs: BFS and DFS traversal, connected components, has cycle detection
- Tries: prefix matching problems (implement a trie, word search)

**Target: 25 medium problems**, with a bias toward dynamic programming introductions (climbing stairs, coin change, longest common subsequence). DP is hard — don't expect to master it this week. Just build familiarity.

**System design: Scale-out thinking**
Design a key-value store. Cover: single-node implementation, replication for fault tolerance, sharding for scale, consistency trade-offs (eventual vs strong). This forces you to think about the CAP theorem practically.

**Mock interview: Week 3 checkpoint**
Do your first timed mock interview. Set a 45-minute timer. Pick one LeetCode medium you haven't seen. Solve it while narrating your thought process out loud. Record yourself if possible. Review where you got stuck and why.

## Week 4: System Design Deep Dive

**Daily commitment: 2 hours, system design focus**

**Dedicate this week to system design.**

Core designs to master (one per day):
1. **URL shortener** — teaches hashing, database schema design, caching
2. **Twitter/social feed** — teaches fan-out patterns, timeline generation, sharding strategies
3. **Ride-sharing (Uber)** — teaches geospatial indexing, real-time location updates, matching algorithms
4. **Chat system** — teaches WebSockets, message delivery guarantees, read receipts
5. **Search autocomplete** — teaches trie data structure at scale, prefix matching, ranking

**For each design, structure your answer in 4 parts:**
1. Clarify requirements (functional + non-functional, scale)
2. High-level architecture (components and data flow)
3. Deep-dive on 2-3 critical components
4. Discuss trade-offs and alternatives

**DS/A maintenance: 15 minutes daily**
Don't let DS/A atrophy while focusing on system design. Do 2-3 easy problems per day to keep the pattern-matching sharp.

## Week 5: Advanced Topics and Company-Specific Prep

**Daily commitment: 2–2.5 hours**

**Advanced DS/A (3 days):**
- Dynamic programming: 0/1 knapsack, longest increasing subsequence, edit distance
- Graph algorithms: Dijkstra's, BFS for shortest path in unweighted graphs, topological sort
- Advanced trees: segment trees (range queries), disjoint set / union-find

**Company research (2 days):**
- Read the company's engineering blog. Find 2-3 technical challenges they've solved.
- Understand their product deeply. What are the hard technical problems in their space?
- Look at job posting requirements — which skills are listed first? Depth, not breadth, in those areas.

**Behavioral: Full practice run**
Answer the following questions out loud, timed at 2 minutes each:
- "Why do you want to leave your current company?"
- "Tell me about your most impactful project"
- "Describe a time you had to learn something quickly"
- "How do you handle technical disagreements with your team?"
- "Where do you want to be in 5 years?"

Review the recordings. Eliminate "um," reduce hedging language, make sure you're naming specific outcomes.

**Salary research:** Know the market rate for your target role/level before any offer conversation. Use Levels.fyi, Glassdoor, Blind, and LinkedIn Salary.

## Week 6: Peak and Rest

**Daily commitment: 1.5 hours (taper intensity)**

**Target: Full mock interviews**
Do 3-4 complete mock interviews this week — ideally with a friend or on a platform like Pramp or interviewing.io. A full mock interview (DS/A + system design + behavioral) takes 2 hours.

**DS/A final push:**
Review problems you got wrong in weeks 2-5. Reattempt them without hints. If you still can't solve them, understand why — don't just re-read the solution.

**Day before interview:**
- Do 2-3 easy problems to stay warm, not to learn new material
- Review your behavioral stories once
- Sleep 8 hours. Seriously. Cognitive performance on sleep debt is measurably worse.

**Day of interview:**
- Eat before. Don't interview hungry.
- Review your target company's product for 20 minutes
- Trust your preparation

## The Psychology of Preparation

**Progress isn't linear.** Week 3 often feels worse than week 1 because you're attempting harder problems and encountering real gaps. This is normal. Push through.

**Understand over memorize.** If you memorize solutions without understanding, you'll fail variations. If you understand the pattern, you can adapt. Always ask "why does this work?"

**Use the interview to show your process.** Interviewers evaluate your reasoning, not just your answer. Narrate your thinking. Say "I'm not sure about this edge case — let me think through it." Being stuck and working through it methodically is better than getting the answer by luck.

**Six weeks is enough for most engineers to move from rusty to competitive.** Eight weeks is comfortable. Four weeks is possible but intense. The plan scales — compress or expand by adjusting daily problem count.

Start today, not tomorrow.
