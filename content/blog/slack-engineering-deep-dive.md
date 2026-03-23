---
title: "Slack Engineering Deep Dive: Technical Interview Preparation Guide"
description: "What Slack's engineering team builds — real-time messaging infrastructure, WebSocket at scale, search, notifications, and the transition to Salesforce — and how to prepare for their technical interviews."
date: "2026-03-19"
category: "Company Deep Dives"
---

Slack handles over 10 billion messages per day across millions of concurrent users. Before Salesforce acquired it in 2021, Slack was already one of the most technically demanding real-time communication platforms ever built. Understanding what that infrastructure looks like — and why it was built that way — is your entry point into their interview process.

## The Core Technical Problem: Real-Time at Scale

The defining challenge of Slack's architecture is maintaining persistent, low-latency connections for millions of simultaneous users. Every active Slack session holds an open WebSocket connection to Slack's servers. At peak load, that means millions of long-lived TCP connections that must receive messages with sub-second latency.

This is architecturally hard for several reasons. Connection state is not naturally distributed — a user's WebSocket connection lives on one server, but the message might originate from a sender connected to a completely different server. The routing layer must identify which server holds the target user's connection and push the message there. Slack calls this the "channel" problem: a Slack workspace channel might have thousands of members across thousands of active connections, and every message must fan out to all of them reliably.

Their solution involved building a dedicated connection gateway layer, where lightweight servers handle only WebSocket I/O, decoupled from application logic. Application servers process the business logic and write to a message bus (Kafka), and the gateway layer subscribes and pushes to the right connections. This separation of concerns is a pattern you should know cold for their system design interviews.

## Tech Stack: From PHP to Modern Microservices

Slack's origins are in PHP — the same language behind early Facebook and WordPress. Their backend was PHP/Hack (Facebook's statically-typed PHP dialect) for a long time, which is unusual for a high-scale real-time system. As they scaled, they introduced a hybrid architecture:

**Data layer:** MySQL is the primary database, but at Slack's scale, a single MySQL cluster can't handle the write volume for billions of messages. They adopted Vitess, the MySQL sharding and scaling layer originally built by YouTube. Vitess allows horizontal sharding across MySQL clusters with query routing handled transparently. Interview-relevant detail: Vitess enforces per-shard transactions, which means cross-shard joins and transactions are either avoided or implemented at the application layer.

**Event streaming:** Kafka powers the internal event bus. When a message is sent, it's written to Kafka, which fans out to downstream consumers — search indexing, notification routing, analytics, the gateway layer for real-time delivery. This decoupling is critical to their reliability story: a slow notification service can't block message delivery.

**Search:** Searching across billions of messages with relevance ranking, access control enforcement, and sub-second latency is a genuinely hard problem. Slack built a custom search infrastructure rather than relying entirely on Elasticsearch, because access control at query time — enforcing channel membership and workspace permissions per result — doesn't map cleanly onto standard search engine primitives.

**The Salesforce layer:** Post-acquisition, Slack engineering has integrated with Salesforce's CRM data, which introduces a new class of problems: joining Slack message context with Salesforce records, cross-product identity management, and enterprise data governance requirements. New roles at Slack often involve working on this integration surface.

## Message Delivery Guarantees

Slack promises "at least once" delivery with deduplication. When a client sends a message, the client assigns a locally unique ID (a client-side nonce). The server acknowledges receipt. If the client doesn't receive an acknowledgment within a timeout, it retries. The server uses the nonce to detect and drop duplicates.

For delivery to recipients, Slack uses a combination of real-time push (via the WebSocket connection) and polling fallback. If a recipient's connection is unavailable at delivery time, the message is stored durably and delivered when the client reconnects. The client requests a "replay" of missed events since its last sequence number — a simple and reliable catch-up mechanism.

This is a standard pattern for reliable real-time systems. In your interviews, expect to be asked to design exactly this: how do you guarantee a message is delivered exactly once, even with client disconnections and server failures?

## Notification Routing at Scale

Slack's notification system sits at the intersection of several hard problems: cross-device fan-out (desktop, mobile, email digests), user-configurable muting rules, do-not-disturb schedules, keyword alerts, and @mention detection. Every message triggers evaluation of notification rules for every channel member.

At millions of messages per day, naive rule evaluation doesn't scale. Slack pre-computes notification preferences and caches them aggressively. The notification pipeline is asynchronous — it reads from Kafka, evaluates rules, and calls platform-specific delivery APIs (APNs for iOS, FCM for Android). Rule evaluation failures don't block message delivery.

A subtle reliability requirement: mobile push notifications can wake a sleeping app to show a preview. If the preview is stale — if the message was deleted before the user sees it — Slack must send a notification update or retraction. This requires the notification pipeline to subscribe to message deletion events, not just creation events.

## Interview Process

Slack's process typically runs four to five rounds:

1. **Recruiter screen** — role fit, compensation, timeline
2. **Technical phone screen** — one coding problem, medium Leetcode difficulty, 45 minutes
3. **Take-home or second coding round** — sometimes assigned, sometimes skipped for senior candidates
4. **Virtual onsite** — three to four interviews back to back:
   - Two coding interviews (data structures, algorithms, occasionally concurrency)
   - One system design interview
   - One behavioral interview

For senior engineers (L5+), the system design interview carries the most weight. The coding problems are generally not trick questions — they're testing that you can write clean, working code under mild time pressure.

## What They Actually Ask

**Coding:** Expect graph traversal, tree problems, and string manipulation. Slack's product involves threaded messages (a tree structure), channels as graphs of user memberships, and lots of text parsing. Union-Find problems show up occasionally given the implicit grouping/connectivity problems in their domain. Hash maps for deduplication are a recurring pattern.

**System design:** The canonical Slack-adjacent problems are:
- Design a real-time chat system (they will push on delivery guarantees, connection management, and fan-out)
- Design a notification system with user-configurable rules
- Design full-text search over user-generated content with access control

For any of these, structure your answer around: data model first, then write path, then read path, then scale and failure modes. Don't jump to infrastructure choices before you've established what you're actually building.

**Behavioral:** Slack's engineering culture emphasizes async-first communication (they eat their own dog food), user empathy, and reliability. STAR-format answers that demonstrate you've thought about the downstream user impact of your technical decisions land well here. They also value candidates who've worked in high-ambiguity environments — Slack teams often span product and infrastructure concerns simultaneously.

## Preparation Priorities

If you have two weeks, focus in this order:

1. Read Slack's engineering blog — their posts on Flannel (edge caching), Vinograd (Vitess adoption), and their WebSocket gateway architecture are publicly available and directly relevant.
2. Practice designing a real-time messaging system from scratch. Time yourself. Get it to a full solution — data model, APIs, storage layer, delivery mechanism — in 35 minutes.
3. Review Kafka consumer group semantics, at-least-once vs. exactly-once delivery patterns, and WebSocket connection lifecycle.
4. For coding, grind medium-difficulty graph and string problems. Two weeks of focused practice is enough to be comfortable here.
5. Prepare three behavioral stories that involve shipping something under constraints — reliability pressure, ambiguous requirements, or cross-team dependencies.

Slack is a technically sophisticated team working on genuinely hard infrastructure. They're looking for engineers who understand the tradeoffs in distributed systems and can communicate them clearly. That combination — technical depth plus clear thinking — is what their interview process is designed to surface.
