---
title: "System Design Interview Checklist: A Step-by-Step Framework"
description: "A practical checklist for approaching any system design interview question. Covers requirements clarification, capacity estimation, component design, scaling, and trade-off discussion."
date: "2025-10-31"
category: "Interview Preparation"
---

# System Design Interview Checklist

System design interviews are open-ended by design. Without a framework, it's easy to dive into details too early, miss important requirements, or leave the interviewer without a clear picture of your architecture. This checklist gives you a repeatable approach for any system design question.

## Step 1: Clarify Requirements (5 minutes)

Never start designing before understanding what you're building. Most system design interview questions are deliberately vague — the questions you ask reveal your engineering maturity.

**Functional requirements** (what the system does):
- [ ] What are the core use cases? (write down 3–5)
- [ ] What actions does a user take? (read, write, search, stream?)
- [ ] What data does the system store, and how?
- [ ] Are there real-time requirements?
- [ ] Is there a mobile component?

**Non-functional requirements** (how the system performs):
- [ ] Scale: How many users? Daily active vs. monthly active?
- [ ] Read/write ratio: Is this read-heavy, write-heavy, or balanced?
- [ ] Latency requirements: p50, p99 targets?
- [ ] Availability target: 99.9%? 99.99%?
- [ ] Consistency: Strong, eventual, or somewhere in between?
- [ ] Data size: How much data per user? Total storage?

**Constraints and out of scope**:
- [ ] What can you explicitly exclude from your design?

**Write your requirements on the whiteboard** — it shows structure and gives you a reference point throughout.

## Step 2: Capacity Estimation (3–5 minutes)

Back-of-envelope calculations anchor your design decisions and show you can reason about scale.

**Common estimation math**:
- 1 million DAU × 10 requests/day = 10M requests/day ≈ 116 requests/second
- Storage: posts × size per post × retention period
- Bandwidth: requests/second × average response size

**Examples**:
- Twitter-scale: 200M DAU, 500M tweets/day ≈ 6K writes/second, 10x reads = 60K reads/second
- Instagram photos: 2GB/photo → 1M photos/day → 2TB/day

You don't need to be precise — show that you understand the magnitude.

## Step 3: Define the API (5 minutes)

Sketch the primary API endpoints before diving into the internal architecture.

```
POST   /tweets           # Create tweet
GET    /timeline/{userId} # Fetch timeline
GET    /tweet/{tweetId}   # Get single tweet
POST   /follow            # Follow a user
```

Defining the API makes the interface explicit and forces you to think about what data flows in and out.

## Step 4: High-Level Design (10–15 minutes)

Draw the major components and data flows. Start with the simplest possible design that meets requirements, then evolve it.

**Components to consider**:
- [ ] Clients (web, mobile, API consumers)
- [ ] Load balancer / API gateway
- [ ] Application servers
- [ ] Primary database(s)
- [ ] Cache layer (Redis, Memcached)
- [ ] Message queue / event streaming (Kafka, SQS)
- [ ] File/blob storage (S3)
- [ ] CDN (for static assets)
- [ ] Search service (Elasticsearch)

**Draw arrows showing data flow** for the primary use cases (e.g., "user creates a tweet → API server → write to DB → publish to Kafka → fan-out service → each follower's timeline").

## Step 5: Deep Dive on Critical Components (15 minutes)

The interviewer will typically guide this: "How does your database scale?" or "How does the feed generation work?" Anticipate the hard parts and proactively address them.

**Common deep-dive topics**:

**Database design**:
- [ ] Schema: tables, relationships, indexes
- [ ] Read replicas for scaling reads?
- [ ] Sharding strategy (by user ID? by content ID?)
- [ ] What consistency model do you need?

**Feed/timeline generation**:
- [ ] Fan-out on write vs. fan-out on read
- [ ] How do you handle celebrity accounts with millions of followers?

**Caching**:
- [ ] What data goes in cache?
- [ ] Cache invalidation strategy?
- [ ] What happens on cache miss?

**Scaling the write path**:
- [ ] Is the write throughput manageable?
- [ ] Do you need message queues to absorb write spikes?

## Step 6: Address Bottlenecks and Scale (5 minutes)

Revisit your design and identify where it breaks at 10x, 100x scale.

**Scaling checklist**:
- [ ] Application tier: stateless? Can you add servers?
- [ ] Database: can your primary handle the write load? Read replicas for reads?
- [ ] Cache: hot keys? Cache stampede on miss?
- [ ] Network: any data transfer bottlenecks?
- [ ] Single points of failure: what breaks if one component goes down?

## Step 7: Trade-Off Discussion (ongoing)

Throughout the interview, explicitly acknowledge trade-offs. This is one of the highest-signal behaviors:

**Example trade-off discussion**:
> "I'm choosing to denormalize the user data into the post table. This means writes are more complex — we have to update in multiple places — but reads are much faster and simpler. Given this is a read-heavy system with 100:1 read:write ratio, I think that trade-off makes sense."

**Common trade-offs to discuss**:
- Consistency vs. availability (CAP theorem)
- Read performance vs. write complexity
- Storage cost vs. query flexibility
- Operational simplicity vs. scale
- Latency vs. throughput

## Common Mistakes to Avoid

**Diving into code**: System design is about architecture and trade-offs, not code.

**Ignoring the requirements you gathered**: If you said the system needs 99.99% availability, show how your design achieves it.

**Choosing fashionable tech without justification**: "I'd use Kafka because it's scalable" is weak. "I'd use Kafka because we have multiple downstream consumers that need the feed events and we want replay capability" is strong.

**Stopping at a toy design**: A single server with one database is not a system design interview answer. Push to at least one level of scaling.

**Not asking clarifying questions**: The single highest-value action in a system design interview is asking good questions. It shows you understand that requirements drive architecture.

With this checklist internalized, you'll walk into any system design question with a structure that keeps you organized, demonstrates architectural thinking, and leaves room for the deep-dive conversations that differentiate strong candidates.
