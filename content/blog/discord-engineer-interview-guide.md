---
title: "Discord Software Engineer Interview Guide 2025"
description: "A complete guide to Discord's software engineering interviews in 2025 — covering the technical stack migration from Go to Rust, real-time messaging and voice at scale, system design challenges, and what makes Discord engineering genuinely interesting."
date: "2025-10-20"
category: "Company Interview Guides"
---
# Discord Software Engineer Interview Guide 2025

Discord serves over 500 million registered users and hosts hundreds of millions of messages every day across voice, video, and text. Building the infrastructure that powers this level of real-time communication is genuinely hard engineering — and Discord's technical decisions, including a celebrated migration from Go to Rust for performance-critical services, have made it a company that engineers follow closely.

## Discord's Technical Stack and Why It Matters

Discord has made some of the most publicly discussed engineering decisions in recent years, and understanding them will help you in the interview process.

The most famous is the **Go to Rust migration** for performance-critical services. Discord published a detailed post about this, explaining that Go's garbage collector was introducing latency spikes that were unacceptable for real-time communication. Rust's lack of a garbage collector eliminated these pauses entirely, dramatically improving tail latency. This decision reflects a broader principle at Discord: performance is not a nice-to-have — it is part of the product.

The move to Rust signals that Discord takes **systems-level thinking seriously**. Engineers who understand memory management, concurrency models, and runtime behavior will fit in well. You do not need to be a Rust expert to interview at Discord, but understanding why Rust matters — and why it was chosen over alternatives — is valuable context.

For the application layer, Discord uses **Python and Elixir** extensively. The Gateway (which handles WebSocket connections) is written in Elixir, leveraging the BEAM VM's lightweight process model for handling millions of concurrent connections. Python handles much of the API and business logic. This polyglot environment is part of what makes Discord's engineering interesting.

## Engineering Culture at Discord

Discord's culture is shaped by its mission: building the best place for communities to exist online. This includes gaming communities, study groups, hobby servers, and professional organizations. The diversity of use cases means engineers must build systems that are flexible, scalable, and accessible.

The team values **pragmatism over ideological purity**. The Go-to-Rust migration was not done because Rust is fashionable — it was done because it solved a real problem. Discord engineers are expected to make decisions based on evidence and tradeoffs, not trends.

There is also a strong culture of **ownership and curiosity**. Engineers tend to investigate deeply when something is wrong, and the "it's not my service" mindset is not welcome. Given the interdependency of real-time systems, you need engineers who can follow a problem across service boundaries.

## The Interview Process

**Recruiter screen (30 min):** Background and motivation. Be ready to talk about what you find technically interesting about Discord's scale and architecture.

**Technical phone screen (45–60 min):** A coding problem, typically algorithmic. Discord's screen is similar in format to other major tech companies — expect to solve a problem and explain your approach clearly.

**Virtual onsite (4–5 rounds):**
- *Coding (2 rounds):* Algorithmic problems, medium to hard difficulty. Data structures and graph problems are common.
- *System design (1 round):* Real-time messaging and presence are typical themes. See below.
- *Behavioral (1 round):* How you've handled large-scale incidents, cross-team collaboration, and technical decisions under uncertainty.
- *Depth interview (optional, senior roles):* A deeper technical conversation about a specific area — distributed systems, networking, or the relevant domain for your role.

## System Design: Real-Time at Scale

Discord's system design round will almost certainly touch on the challenges of real-time communication at massive scale. Key topics:

**Message delivery guarantees:** How do you ensure a message sent by one user is delivered to all members of a server with tens of thousands of online members? Understand fan-out approaches, the tradeoff between delivery consistency and latency, and how ordering guarantees interact with distributed systems.

**Presence system:** Knowing which users are online in real-time is deceptively hard. With hundreds of millions of users, naively maintaining presence state in a single system doesn't scale. Discord's presence system uses a combination of heartbeats, timeouts, and distributed state. Be ready to design a presence system that handles millions of concurrent connections with acceptable accuracy.

**Voice and video infrastructure:** Real-time voice requires low-latency UDP-based protocols (WebRTC), media servers that handle routing and mixing, and regional distribution to minimize round-trip times. Understanding the basics of WebRTC, SRTP, and the role of TURN/STUN servers will differentiate you.

**Gateway and connection management:** Discord's Gateway handles persistent WebSocket connections. Understand how to design a system that authenticates, routes, and manages millions of concurrent WebSocket connections, handles reconnects gracefully, and delivers events reliably.

**Sharding:** Discord servers (guilds) can have millions of members. Understanding how Discord shards its data and distributes load across its gateway infrastructure is relevant for design questions.

## Compensation

Discord's compensation is competitive with major tech companies. Mid-level engineers can expect total compensation of $250,000–$370,000, with senior engineers typically in the $350,000–$500,000+ range. Equity is in the form of RSUs or options, with Discord having raised significant institutional funding. The company has been reported to be evaluating public market options.

## What Makes Discord Engineering Interesting

**Real-time systems at genuine scale:** Very few companies operate messaging and voice infrastructure at Discord's scale. The engineering problems are both classic and novel.

**Polyglot engineering:** Working with Rust, Elixir, Python, and Go in a single company gives engineers broad exposure to different paradigms and tradeoffs.

**Public engineering culture:** Discord's engineering blog is excellent. The company communicates technical decisions openly, which means you can study their real challenges before interviewing.

**Product that engineers use:** Discord is widely used by engineers personally. The team builds for a community they are part of, which creates authentic motivation.

Prepare for a Discord interview by studying real-time systems deeply, understanding WebSocket and WebRTC at a conceptual level, and being ready to discuss the specific tradeoffs in Discord's published architecture decisions.
