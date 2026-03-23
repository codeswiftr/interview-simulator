---
title: "Rate Limiting System Design: A Complete Interview Guide"
description: "Master rate limiting concepts for system design interviews: token bucket vs leaky bucket vs sliding window, Redis-based distributed rate limiting, and client-side retry strategies."
date: "2026-03-20"
category: "Interview Preparation"
---

# Rate Limiting System Design: A Complete Interview Guide

Rate limiting is one of the most commonly asked system design topics in senior engineering interviews — and for good reason. Nearly every production API at scale relies on it. Understanding the tradeoffs between algorithms, the mechanics of distributed enforcement, and the subtleties of per-user versus per-IP limits will set you apart from candidates who stop at "I'd use Redis."

## The Three Core Algorithms

**Token Bucket** is the most widely used algorithm in practice. Imagine a bucket that holds up to N tokens. Tokens are added at a fixed rate (e.g., 100 per second). Each request consumes one token. If the bucket is empty, the request is rejected. The key property: bursts are allowed up to bucket capacity. AWS, Stripe, and most major APIs use token bucket because it handles natural traffic spikes gracefully. In your interview, highlight that the bucket size is your burst tolerance parameter — separate from the sustained rate.

**Leaky Bucket** processes requests at a fixed output rate regardless of how fast they arrive. Incoming requests fill a queue; if the queue is full, excess requests are dropped. Think of it as a queue with a constant dequeue rate. This produces very smooth egress traffic, which is ideal for protecting downstream services that are sensitive to spikes. The downside: legitimate burst traffic gets queued and delayed, which hurts latency-sensitive use cases.

**Sliding Window** (and its approximation, sliding window log) tracks exact request timestamps within a rolling time window. A pure sliding window log stores every request timestamp and counts how many fall within the last N seconds. This is the most accurate but most memory-intensive approach. A common optimization is the **sliding window counter**: blend the previous window's count with the current window's count weighted by the overlap. This approximation reduces memory usage from O(requests) to O(1) per user while staying within ~1% of the true rate.

In interviews, expect to be asked: "Which would you choose and why?" The right answer depends on the use case — token bucket for APIs that need burst tolerance, leaky bucket for protecting fragile downstream services, sliding window for strict per-user SLA enforcement.

## Distributed Rate Limiting with Redis

A single in-process rate limiter breaks the moment you have more than one server. Every production system needs centralized enforcement. Redis is the standard choice because of its atomic operations and sub-millisecond latency.

For a **token bucket in Redis**, store the current token count and the last refill timestamp as a hash. Use a Lua script to atomically compute the new token count (based on elapsed time and refill rate), check if the request can proceed, and update the count — all in a single round trip. Lua scripts in Redis execute atomically, so you avoid race conditions without distributed locks.

For a **sliding window counter in Redis**, use two keys: one for the previous window count and one for the current window count, both with TTLs aligned to the window boundaries. On each request, compute: `rate = prev_count * ((window_size - elapsed) / window_size) + curr_count`. Increment the current window key. This is the approach used by Cloudflare's public rate limiting implementation.

When discussing distributed rate limiting, bring up **data locality**: should rate limit state be sharded by user ID across Redis nodes, or replicated? Sharding gives higher throughput but requires consistent hashing to route requests for a given user to the same shard. Replication ensures availability but introduces coordination overhead.

## Per-User vs Per-IP vs Per-Endpoint Limits

These three dimensions serve different purposes and are often combined:

**Per-IP limits** defend against unauthenticated abuse and DDoS. They're blunt — a NAT gateway can make thousands of legitimate users share one IP — but they're your first line of defense before authentication. Use per-IP limits at the edge (CDN or API gateway layer).

**Per-user limits** are the primary mechanism for authenticated API rate limiting. They allow fair resource allocation and let you offer tiered plans (free: 100 req/min, pro: 1000 req/min). The challenge is that users on mobile apps behind NAT all have different user IDs but may share infrastructure — per-user limits correctly handle this.

**Per-endpoint limits** let you differentiate by resource cost. A `/search` endpoint that triggers a full-text index scan should have a much lower limit than `/health`. This is especially important for compute-intensive or third-party-backed endpoints where each request has significant cost.

In practice, you stack these: per-IP limit → per-user limit → per-endpoint limit, applying whichever is most restrictive.

## Rate Limit Headers and Client-Side Retry Strategies

The HTTP standard for communicating rate limit state uses three headers (RFC 6585 and the emerging `RateLimit` header draft):

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 743
X-RateLimit-Reset: 1711574400
Retry-After: 30
```

Return a `429 Too Many Requests` status when the limit is exceeded. Always include `Retry-After` so clients know when to retry rather than hammering the endpoint.

On the **client side**, the correct retry strategy is **exponential backoff with jitter**: wait `min(cap, base * 2^attempt) + random_jitter` before retrying. Without jitter, all clients that hit a limit simultaneously retry at the same moment, creating a thundering herd that immediately triggers the rate limit again. Full jitter (randomizing the entire wait window) performs better than decorrelated jitter in most empirical studies.

Clients should also implement a **local token bucket** as a pre-check before making requests. If you know your limit is 100 req/min and you've consumed 95 in the last 45 seconds, back off preemptively rather than burning the remaining quota and getting a 429.

## Interview Tips

When you get a rate limiting question, open with: "What are we protecting — the API from abuse, or downstream services from overload?" This frames the algorithm choice correctly. Then walk through: algorithm selection → storage layer → enforcement point (edge vs application) → headers → client behavior. Discuss monitoring: rate limit hit rate is a key SRE metric. A sudden spike in 429s might mean a misconfigured client, a buggy deployment, or a real abuse event — your system should distinguish between them with structured logging on the limit key (user ID, endpoint, IP) and the current counter value.
