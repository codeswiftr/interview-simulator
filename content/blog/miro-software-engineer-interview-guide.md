---
title: "Miro Software Engineer Interview Guide"
description: "A practical guide to Miro's engineering interview process — covering the real-time collaboration tech stack, system design expectations, coding rounds, and behavioral themes for their async-first remote culture."
date: "2026-03-19"
category: "Company Interview Guides"
---

Miro engineers build a collaborative whiteboard used by over 50 million people — product managers, designers, developers, and executives — all working on the same infinite canvas, often at the same time. That constraint (simultaneous multi-user editing at scale, with sub-100ms perceived latency) shapes every part of how Miro hires.

This guide covers what you'll face in a Miro software engineering interview and how to prepare.

## The Engineering Challenge Miro Solves

Before you interview, internalize the actual problem Miro engineers deal with daily:

**Infinite canvas with real-time sync.** A Miro board is unbounded. Hundreds of users can be active on the same board simultaneously, each dragging, resizing, typing, or connecting shapes. The system must broadcast changes fast enough that collaboration feels live, while gracefully handling conflict resolution when two users edit the same object.

**WebGL rendering at scale.** Miro's frontend renders boards using WebGL, not the DOM. This enables smooth 60fps interaction with thousands of objects on-screen. Engineering that layer requires deep knowledge of GPU pipelines, draw call batching, and occlusion culling — a skill set that overlaps more with game development than typical frontend work.

**Operational transforms and CRDTs.** Miro uses conflict-free replicated data types (CRDTs) and operational transform (OT) principles to handle concurrent edits without requiring a central locking mechanism. This is a known hard distributed systems problem, and interviewers expect senior candidates to be aware of these approaches.

**50M+ users, enterprise-grade reliability.** Large enterprise customers (Fortune 500 companies, design firms, consultancies) rely on Miro for critical work. Downtime or data loss at that scale is unacceptable. Their backend teams run on AWS with a distributed microservices architecture designed for high availability.

## Tech Stack

Knowing the stack helps you frame your answers in familiar terms to interviewers:

- **Backend:** Java and Kotlin (primary), running on AWS (ECS, RDS, SQS, S3, ElastiCache)
- **Frontend:** TypeScript and React, with a custom WebGL rendering layer for the canvas
- **Real-time layer:** WebSockets (custom protocol) for live collaboration, with a pub/sub architecture for board event distribution
- **Data:** PostgreSQL for persistent board state, Redis for ephemeral session state and pub/sub
- **Infrastructure:** AWS-native, Kubernetes for container orchestration, Terraform for IaC

You do not need to have used all of these, but you should be comfortable reasoning about the tradeoffs involved in these choices.

## Interview Process (Typical Format)

Miro's process for software engineers generally follows this structure:

1. **Recruiter screen** (30 min) — role fit, compensation, timeline
2. **Technical phone screen** (60 min) — one or two LeetCode-style coding problems, focus on arrays/graphs/trees
3. **System design round** (60 min) — design a collaborative or distributed system; expect follow-up depth questions
4. **Coding round** (60 min) — one harder algorithmic problem or a take-home followed by a review
5. **Behavioral / values round** (45–60 min) — structured around Miro's values: focus on impact, async-first communication, creative problem-solving
6. **Hiring manager conversation** (30–45 min) — team fit, growth trajectory, project scope

The pipeline can vary by level and team, but system design and coding are always present. Senior+ candidates should expect a deeper system design session with explicit follow-ups on tradeoffs.

## What They Test: Coding

Miro's coding questions trend toward medium-to-hard difficulty on the standard scale. Common patterns:

- **Graph traversal** (BFS/DFS): board elements and their connections map naturally to graph problems
- **Interval merging / range queries**: relevant to spatial indexing on a 2D canvas
- **Concurrent data structures**: understanding of thread safety, atomic operations, and lock-free structures
- **String manipulation and parsing**: for collaborative document editing features

Miro cares about clean code and communication during the interview. Explain your approach before coding, call out edge cases as you encounter them, and discuss time/space complexity as you go — not as an afterthought.

## What They Test: System Design

This is the most differentiating round. Miro interviewers expect candidates to reason about collaborative systems specifically, not just generic distributed systems.

**High-signal topics to be fluent in:**

- **Operational Transforms vs. CRDTs:** Understand both at a conceptual level. Be able to explain why Google Docs uses OT, why newer systems often prefer CRDTs, and the tradeoffs (complexity, memory, conflict resolution semantics).
- **WebSocket architecture at scale:** How do you manage 10,000 concurrent WebSocket connections per board? What happens when the server handling those connections fails?
- **Eventual consistency in collaborative tools:** What does it mean for two users to see "different" states of a board momentarily? How do you converge to a consistent state without data loss?
- **Viewport-based data loading:** How do you efficiently load only the objects visible in a user's current viewport on an infinite canvas, as they pan and zoom?
- **Presence and awareness:** How do you show cursor positions, selections, and active users in real time without flooding the backend with position updates?

Bring up these considerations proactively rather than waiting to be asked. Interviewers reward candidates who demonstrate domain awareness.

## Sample System Design Questions

These are representative of what Miro asks or topics closely adjacent to their product:

1. **Design a real-time collaborative whiteboard.** Start broad — what are the core entities, how does state sync work, how do you handle concurrent edits? Then narrow into the real-time layer.

2. **Design a system to support 10,000 concurrent users on a single board.** Focus: WebSocket management, horizontal scaling, event fan-out.

3. **Design a conflict resolution mechanism for two users simultaneously moving the same sticky note.** Focus: last-write-wins vs. CRDT semantics, user experience implications.

4. **Design a viewport-aware data loading system for an infinite 2D canvas.** Focus: spatial indexing (quadtrees, R-trees), progressive loading, caching.

5. **Design the backend for board versioning and undo/redo.** Focus: event sourcing, CQRS, storage tradeoffs for large boards.

For each of these, drive the conversation toward explicit tradeoffs. Miro interviewers are less interested in the "correct" answer and more interested in how you reason about competing constraints — latency vs. consistency, cost vs. scalability, complexity vs. correctness.

## Behavioral Themes

Miro is a fully distributed company with an async-first communication culture. Their behavioral questions reflect this directly:

**Async communication:** Expect questions about how you've handled disagreements or decisions without synchronous meetings. They value written clarity over verbal agility. Prepare examples of design docs, RFCs, or detailed async discussions you've led.

**Creativity and product thinking:** Miro's mission is explicitly about enabling human creativity. Engineers are expected to care about what they build, not just how. Be ready to discuss features or improvements you've advocated for — or shipped — because you understood user needs.

**Ownership under ambiguity:** Miro moves fast and operates across time zones. They want engineers who can define scope, make reasonable decisions with incomplete information, and communicate those decisions clearly to stakeholders.

**Impact at scale:** Frame your behavioral examples with concrete metrics. "I improved board load time by 40% for boards with 5,000+ objects" lands better than "I worked on performance."

Use the STAR format (Situation, Task, Action, Result) but weight heavily toward the Result — Miro cares about measurable outcomes.

## Preparation Checklist

- Implement a basic CRDT (e.g., a grow-only set or LWW-register) from scratch to build intuition
- Practice WebSocket-based system design on paper: connection lifecycle, message format, fan-out strategies
- Review spatial indexing data structures (quadtrees, R-trees) and their complexity tradeoffs
- Solve 5–10 graph problems at medium-hard difficulty on LeetCode, with a focus on BFS/DFS variants
- Prepare 3–4 behavioral stories that demonstrate async leadership, ownership, and measurable technical impact
- Read Miro's engineering blog — they publish detailed technical writeups on their real-time architecture and WebGL rendering work

Miro hires engineers who think in systems and communicate with precision. If you can speak fluently about how real-time collaboration actually works at a technical level, you will stand out.
