---
title: "System Design Interview Checklist: Complete Framework for Every Question"
description: "A step-by-step system design interview framework covering requirements gathering, capacity estimation, API design, data modeling, high-level architecture, deep dives, and tradeoffs — with time allocation and scoring criteria."
date: "2026-03-20"
category: "System Design"
---

# System Design Interview Checklist: Complete Framework for Every Question

System design interviews are the most variable part of the technical interview process. Unlike coding problems with deterministic correct answers, system design questions have no single right answer — which means candidates who don't bring explicit structure tend to wander, cover too little ground, and leave interviewers uncertain about their depth. A repeatable framework solves this.

This checklist gives you a step-by-step process that works across every common system design question, from "design a URL shortener" to "design the Twitter timeline." Follow the structure, adapt the depth based on what the interviewer focuses on, and you'll cover the ground that actually matters.

## Step 1: Requirements Clarification (5–7 minutes)

Never start designing before you understand what you're building. Spend the first several minutes asking clarifying questions. Interviewers expect and reward this.

**Functional requirements:** What does the system need to do? Be specific. For a URL shortener: does it need custom slugs? Link expiration? Analytics on clicks? API access?

**Non-functional requirements:** Scale, latency targets, consistency guarantees, availability requirements. Ask explicitly: "Should I optimize for read-heavy or write-heavy traffic?" "Is strong consistency required, or is eventual consistency acceptable?" "What's the target p99 latency?"

**Scope constraints:** "Should I focus on the full system or a specific component?" This prevents you from over-engineering the wrong part.

**Common mistake at this step:** Spending too long asking questions and never getting to design. Five to seven minutes is enough. After that, restate your understanding — "So I'm designing a system that does X and Y, targeting Z scale, prioritizing availability over consistency" — and move forward.

## Step 2: Capacity Estimation (5 minutes)

Rough back-of-envelope math establishes whether your design choices are plausible. Interviewers use this step to evaluate whether you have intuition about scale.

Calculate read and write QPS from given numbers: daily active users, average requests per user per day, divided by 86,400 seconds. Estimate storage: average object size multiplied by write volume per day multiplied by retention period. Estimate bandwidth: QPS multiplied by average response size.

Don't obsess over precision. Orders of magnitude matter — knowing whether you're dealing with 100 QPS or 100,000 QPS determines whether you need caching, sharding, or replication. Round aggressively and document your assumptions.

**Common mistake:** Skipping this step entirely or doing it incorrectly. Candidates who skip estimation often propose architectures that don't match the stated scale, which signals a gap in systems thinking.

## Step 3: API Design (3–5 minutes)

Define the contract between clients and your system before you design the internals. This grounds the rest of the discussion in concrete behavior.

Specify the key API endpoints or RPC methods. For each: method name or HTTP verb, parameters, return type, and any important error conditions. You don't need every endpoint — cover the core operations that the requirements specify.

**Example for URL shortener:**
- `POST /links` — body: `{url, custom_slug?, expires_at?}` — returns: `{short_url, id}`
- `GET /{slug}` — returns 301 redirect or 404

**Common mistake:** Skipping API design and jumping to the data model. The API defines behavior; the data model follows from it.

## Step 4: Data Model (5 minutes)

Define your primary entities, their attributes, and their relationships. Choose storage types and justify the choice.

Sketch the main tables or document schemas. Identify primary keys, foreign keys, and any fields that will be queried heavily (these need indexes). Then justify your storage choices: relational database for structured data with complex relationships, document store for flexible schemas, key-value store for low-latency point lookups, wide-column store for time-series or high write-volume data.

**Common mistake:** Choosing a storage technology without explaining why. "I'll use Cassandra" is not sufficient. "I'll use Cassandra because we need high write throughput and the access pattern is always by user_id with no complex joins" is.

## Step 5: High-Level Design (10 minutes)

Draw the major system components and their interactions. This is the core of the interview.

Start with clients, move through load balancers or API gateways, to application servers, to data stores. Add caching layers where you identified read-heavy hotspots. Add queues where you need to decouple write-heavy operations or handle async processing. Add CDN if static content or geographic distribution matters.

Keep it component-level at first. Don't dive into implementation details yet — save those for the deep dive. Name each component clearly and explain what it does in one sentence as you draw it.

**Common mistake:** Jumping immediately to specific implementation details (which database cluster configuration, which AWS service) before the overall flow is clear. Start macro, then micro.

## Step 6: Deep Dive (10–15 minutes)

This is where seniority shows. After you've established the overall design, ask the interviewer: "Which component would you like to explore in more depth?" Then go deep on that component.

Common deep dive areas: the caching strategy (cache aside vs write-through, cache invalidation, eviction policy), database sharding strategy (by what key, how to handle hotspots, resharding), consistency model implementation, failure handling and recovery, rate limiting design.

Demonstrate that you understand the hard problems inside each component — not just that they exist, but how you'd actually solve them.

**Common mistake:** Staying at the same level of abstraction as the high-level design. An interviewer who asks you to deep dive on the caching layer wants to hear about TTL strategy, cache warming, stampede prevention, and how you handle cache invalidation — not "we add a Redis cache in front of the database."

## Step 7: Tradeoffs and Alternatives (5 minutes)

Conclude by explicitly naming the key design decisions you made and the alternatives you rejected. What would you do differently at 10x the scale? What's the biggest risk in this design?

This demonstrates architectural maturity. No design is perfect, and engineers who acknowledge tradeoffs explicitly are more credible than those who present a design as obviously correct.

## Time Allocation Summary

| Step | Duration |
|------|----------|
| Requirements clarification | 5–7 min |
| Capacity estimation | 5 min |
| API design | 3–5 min |
| Data model | 5 min |
| High-level design | 10 min |
| Deep dive | 10–15 min |
| Tradeoffs | 5 min |
| **Total** | **~45 min** |

## What Interviewers Are Scoring

Interviewers evaluate: **communication clarity** (can you explain your thinking as you go), **problem decomposition** (do you break complexity into manageable pieces), **technical depth** (do you understand the hard problems inside each component), **pragmatism** (do you make reasonable choices without over-engineering), and **ownership** (do you drive the interview or wait to be led).

The checklist gives you the structure to demonstrate all five. Practice it until the steps are automatic, so your cognitive budget during the interview goes entirely toward the actual technical problem.
