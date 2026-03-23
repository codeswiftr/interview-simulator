---
title: "Advanced API Rate Limiting System Design"
description: "Design a production-grade API rate limiting system — token bucket vs. sliding window log vs. sliding window counter, distributed rate limiting with Redis, rate limiting at scale, and Stripe/GitHub API rate limiting patterns."
date: "2026-03-20"
category: "System Design"
---

# Advanced API Rate Limiting System Design

Rate limiting appears in almost every senior engineer system design interview involving APIs. It's a seemingly simple problem — "allow N requests per time window" — that becomes complex when you introduce distributed systems, multiple rate limit tiers, and the need for accurate-yet-efficient counting. This guide covers the algorithms and architecture in the depth interviewers expect.

## Why Rate Limiting Is Hard

Three fundamental tensions:
1. **Accuracy vs. efficiency:** The most accurate rate limiting (per-request log) is expensive at scale. Approximations (fixed windows) are cheap but allow bursting at window boundaries.
2. **Strict limits vs. user experience:** Immediate 429 responses are correct but harsh. Token buckets allow bursting, which users perceive as more fair.
3. **Local vs. distributed:** In-memory rate limiting is fast but doesn't work across multiple server instances.

The right algorithm depends on which tensions matter for your use case.

## Algorithm 1: Fixed Window Counter

Divide time into fixed windows (e.g., 1 minute). Count requests in the current window. Reset at each window boundary.

```python
def is_allowed_fixed_window(user_id, limit, window_seconds=60):
    now = int(time.time())
    window_key = now // window_seconds
    key = f"ratelimit:{user_id}:{window_key}"

    count = redis.incr(key)
    if count == 1:
        redis.expire(key, window_seconds * 2)  # Cleanup

    return count <= limit
```

**Problem:** Burst at window boundary. If a user sends 100 requests in the last second of window 1, and 100 in the first second of window 2, they've sent 200 requests in 2 seconds — double the limit. This is a real issue for strict API enforcement.

## Algorithm 2: Sliding Window Log

Store a timestamp for each request. On each request, remove timestamps older than the window, count remaining, compare to limit.

```python
def is_allowed_sliding_log(user_id, limit, window_seconds=60):
    now = time.time()
    key = f"ratelimit_log:{user_id}"

    with redis.pipeline() as pipe:
        pipe.zremrangebyscore(key, '-inf', now - window_seconds)
        pipe.zadd(key, {str(uuid.uuid4()): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds)
        _, _, count, _ = pipe.execute()

    return count <= limit
```

**Accurate** — no boundary burst. **Expensive** — stores a timestamp per request. For 1M requests/minute, this is 1M Redis entries. Not suitable for high-throughput APIs.

## Algorithm 3: Sliding Window Counter

Best of both: accuracy close to sliding log, cost close to fixed window.

Approximate the sliding window by interpolating between two fixed windows:

```python
def is_allowed_sliding_counter(user_id, limit, window_seconds=60):
    now = time.time()
    current_window = int(now // window_seconds)
    prev_window = current_window - 1

    current_key = f"ratelimit:{user_id}:{current_window}"
    prev_key = f"ratelimit:{user_id}:{prev_window}"

    current_count = int(redis.get(current_key) or 0)
    prev_count = int(redis.get(prev_key) or 0)

    # Fraction of previous window that falls within the sliding window
    elapsed_fraction = (now % window_seconds) / window_seconds
    estimated_count = prev_count * (1 - elapsed_fraction) + current_count

    if estimated_count < limit:
        redis.incr(current_key)
        redis.expire(current_key, window_seconds * 2)
        return True

    return False
```

This approximation has <1% error in practice. Cloudflare uses this pattern for their rate limiting infrastructure.

## Algorithm 4: Token Bucket

The most user-friendly algorithm. A bucket holds up to `capacity` tokens. Tokens refill at rate `r` per second. Each request consumes one token. If the bucket is empty, reject the request.

```python
class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second

    def is_allowed(self, user_id):
        key = f"token_bucket:{user_id}"
        now = time.time()

        # Get current state
        data = redis.hmget(key, 'tokens', 'last_refill')
        tokens = float(data[0] or self.capacity)
        last_refill = float(data[1] or now)

        # Refill tokens since last request
        elapsed = now - last_refill
        tokens = min(self.capacity, tokens + elapsed * self.refill_rate)

        if tokens >= 1:
            tokens -= 1
            redis.hmset(key, {'tokens': tokens, 'last_refill': now})
            redis.expire(key, 3600)
            return True

        redis.hset(key, 'last_refill', now)
        return False
```

**Advantage:** Allows bursting up to capacity, which users experience as fair. A user who hasn't made requests recently has a full bucket to burst with.

**Use case:** Stripe uses token bucket for their API. GitHub uses something similar with a per-hour limit.

## Distributed Rate Limiting Architecture

Single-server rate limiting is straightforward. Across multiple API servers, you need shared state.

**Option 1: Centralized Redis.** All servers check a shared Redis instance. Accurate but Redis becomes a bottleneck and single point of failure. Use Redis Sentinel or Cluster for HA.

**Option 2: Local + sync.** Each server maintains local counters. Periodically sync to a central store (every 100ms). Approximate but more scalable. Works when a small percentage of over-limit requests is acceptable.

**Option 3: Rate limit at the API gateway.** Move rate limiting to a centralized gateway (Kong, AWS API Gateway) before requests reach your services. Single enforcement point; no distributed coordination needed.

For high-scale production: gateway-level rate limiting with a backing Redis cluster, with fallback to local approximation during Redis unavailability.

## Multi-Tier Rate Limiting

Production systems typically have multiple tiers:

```
Global rate limit: 10,000 req/minute per API key
Per-endpoint: POST /payments: 100 req/minute per user
Burst allowance: 200% of limit for 10-second windows
Free tier: 100 req/hour, paid tier: 10,000 req/hour
```

Implementation: check in priority order (cheapest checks first). Use a rate limit configuration store (database + cache) that maps API keys to their limits. Cache the limits aggressively — they change rarely.

## Rate Limit Headers (RFC 6585 and Drafts)

Production APIs communicate rate limit status via headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 43
X-RateLimit-Reset: 1714500000  # Unix timestamp when limit resets
Retry-After: 30  # Seconds until client should retry (on 429)
```

These allow clients to implement backoff without guessing. Stripe, GitHub, and Twitter all implement this pattern.

## Interview Clarification Checklist

Before designing, clarify:
- Per user? Per IP? Per API key? Per endpoint?
- Hard limit (reject at N+1) or soft limit (queue/delay)?
- Sliding or fixed window?
- What happens during Redis downtime — allow all or deny all?
- What rate limit tiers exist?
- Should the system handle limit configuration changes without restarts?

The most important design decision to articulate: centralized vs. distributed enforcement, and the accuracy vs. performance tradeoff you're accepting.
