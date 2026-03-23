# Cracking the System Design Interview: A Framework That Actually Works

System design interviews are the most open-ended part of the technical interview process — and the most frequently failed. The failure mode is almost never knowledge: candidates who have read enough system design know the concepts. The failure mode is structure. Candidates who jump to solutions without establishing context, or who cover surface area at the expense of depth, or who mistake listing technologies for design thinking — these are the candidates who leave interviewers uncertain.

This guide covers a repeatable framework for system design interviews that works at senior and above, at companies from FAANG to early-stage startups.

## The Four-Phase Framework

Every system design interview should move through four phases:

1. **Requirements clarification** (5-10 minutes)
2. **Capacity estimation and constraints** (5 minutes)  
3. **High-level design** (10-15 minutes)
4. **Deep dive on selected components** (15-20 minutes)

Most candidates skip or rush phases 1 and 2 and spend all their time in phase 3. This is backwards. The most information-dense part of the interview — the part where you signal senior-level thinking — is in phases 1 and 4.

## Phase 1: Requirements Clarification

Never design before you know what you are designing. Interviewers give deliberately underspecified problems. "Design Twitter" could mean: the Twitter of 2006 with 1M users and no algorithmic feed, or the Twitter of 2023 with 250M users, real-time trends, and a recommendation engine. These are different systems.

Ask about:

**Functional scope**: "What features are in scope? For a Twitter-like system: tweeting, following, timeline, likes, retweets, search, DMs?" Explicitly agree on what you are building before you build it.

**Scale**: "What scale are we designing for? Are we starting from scratch or designing for an existing product at scale? What are the read and write volumes?" Scale changes almost every design decision.

**Consistency requirements**: "Is eventual consistency acceptable for timelines, or does the user need to see their own tweet immediately?" Consistency requirements determine whether you need strong consistency infrastructure (adds cost and complexity) or can use eventual consistency (simpler, cheaper).

**Users and geography**: "Is this global or a single region? Do we need to support multiple languages or locales?" CDN strategy, database geography, and caching all depend on this.

Write the agreed requirements on the shared whiteboard or document. This creates a contract for the rest of the interview: you are designing for these requirements, and the interviewer can't move the goalposts.

## Phase 2: Capacity Estimation

Capacity estimation serves two purposes: it forces you to reason about the scale of the problem concretely, and it surfaces the most important design constraints before you commit to an architecture.

A minimal estimation:

**Writes per second**: If 100M daily active users each write 1 tweet/day: 100M / 86,400 seconds ≈ 1,200 writes/second.

**Reads per second**: Reads are typically 10-100x writes. At 100x: 120,000 reads/second.

**Storage**: A tweet is ~300 bytes. At 1,200 writes/second × 86,400 seconds × 300 bytes ≈ 30GB/day, or ~10TB/year.

These numbers tell you immediately: this is a read-heavy system (cache aggressively), writes are manageable on a single database (but reads are not), and storage is substantial but not exotic.

Estimation does not need to be precise — order of magnitude is enough. "We're in the millions of writes per second, which changes the architecture significantly" is the level of precision that matters.

## Phase 3: High-Level Design

Only now do you draw boxes. The high-level design should include:

- **Client layer**: web, mobile
- **Load balancer / API gateway**
- **Core services**: what are the main responsibilities? Keep it to 2-5 services unless complexity warrants more
- **Data stores**: what data needs to be stored, what are the access patterns, what type of store fits (relational, document, wide-column, cache)?
- **Communication**: synchronous (HTTP/gRPC) or asynchronous (message queue)? Why?

At this stage, you are establishing the skeleton. Do not go deep on any component. Move through the diagram in 5-10 minutes so you have time for the deep dive.

The one thing that distinguishes strong candidates at this phase: they name the trade-off they are making, not just the technology. "I'd use Kafka here because we need fan-out to multiple consumers and want to decouple the write path from the notification service — the trade-off is operational complexity" is stronger than "I'd use Kafka here."

## Phase 4: Deep Dive

Ask the interviewer where they want to go deep, or propose the most interesting component yourself: "I'd like to go deep on the timeline service — that's where the fan-out vs. fan-in trade-off is most interesting. Would that be useful?"

The deep dive is where seniority shows. Pick one component and go to second and third-order consequences:

- Fan-out on write: fast reads, slow writes, scalability problems for celebrity accounts → hybrid approach
- Cassandra for timeline storage: wide-row design, TTL for old tweets, consistency model
- Cache invalidation: when does a cached timeline go stale? How do you handle a delete?

Interviewers do not expect you to cover everything. They expect you to demonstrate that you can reason about one component with the depth of someone who has actually built it.

## What Strong Candidates Do Differently

**They say "it depends" and then resolve it.** "It depends on the consistency requirement. If we need strong consistency, I'd use a single primary. If eventual is acceptable, we can replicate with async replication and accept lag." Never leave a trade-off hanging.

**They drive the interview.** At transition points, they say "I'm going to move to capacity estimation now, unless you have questions on the requirements." They own the pacing.

**They make their uncertainty explicit.** "I've used DynamoDB for read-heavy workloads, so I'm more confident about its read performance. I'm less certain about how it handles the write amplification in this fan-out pattern — how do you usually think about that?" Interviewers respond well to intellectual honesty.

**They know what they don't know about their own design.** "This approach has a potential thundering herd problem when a celebrity posts — I'd want to think more about that." Identifying failure modes in your own design signals maturity.

## Related Articles

- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design Interview Framework](/blog/interview-system-design-framework)
- [System Design: URL Shortener](/blog/system-design-url-shortener)
- [System Design: Distributed Cache](/blog/system-design-distributed-cache)
- [Data Structures and Algorithms Interview Guide](/blog/data-structures-algorithms-interview-guide)
