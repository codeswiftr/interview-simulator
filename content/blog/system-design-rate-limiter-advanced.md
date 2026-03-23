---
title: "System Design: Rate Limiter — Token Bucket, Sliding Window, and Distributed Rate Limiting"
description: "How to design a rate limiter in system design interviews — token bucket vs leaky bucket vs sliding window algorithms, Redis-based implementation, distributed rate limiting, and handling rate limit headers."
date: "2026-03-20"
category: "System Design"
---

# System Design: Rate Limiter — Token Bucket, Sliding Window, and Distributed Rate Limiting

Rate limiting is a fundamental API infrastructure component that appears in system design interviews across all levels. Interviewers expect you to know the algorithms, understand the trade-offs, and design a distributed solution. This guide covers all three with the implementation detail interviews require.

## Why Rate Limiting?

Rate limiting protects services from:
- **Abuse and DDoS**: Prevent malicious actors from overwhelming a service
- **Cost control**: Limit expensive operations (LLM calls, third-party API requests)
- **Fair usage**: Ensure one tenant can't degrade service for others
- **Downstream protection**: Prevent cascading failures when a downstream service is slow

## Rate Limiting Algorithms

### Fixed Window Counter

Divide time into fixed windows (e.g., each minute). Count requests per window. Simple but has a flaw: a client can send 2N requests in 2 seconds by placing N requests at the end of one window and N at the start of the next.

```
11:00:58 — 50 requests (window 11:00, used 50/100)
11:01:01 — 50 requests (window 11:01, used 50/100)
```

100 requests in 3 seconds — the window boundary allows bursting.

### Sliding Window Log

Store a timestamp for each request. On each request, count entries in the window `[now - window_size, now]`. Remove old entries. No boundary burst problem, but O(n) storage per user where n = requests per window.

### Sliding Window Counter

Hybrid approach. Track counts for current and previous windows. Estimate the count for the sliding window using the previous window proportionally.

```
current_count = prev_window_count * (1 - elapsed_fraction) + curr_window_count
```

where `elapsed_fraction = (now - window_start) / window_size`. O(1) storage, good approximation, widely used in production.

### Token Bucket

Users have a "bucket" that fills at a constant rate (e.g., 10 tokens/second, max capacity 100). Each request costs 1 token. If the bucket is empty, the request is rejected.

Allows bursting up to bucket capacity while enforcing an average rate. Better UX than hard limits — a user who hasn't used the API recently can burst at full speed.

```python
def is_allowed(user_id, tokens_per_second, max_tokens):
    key = f"ratelimit:{user_id}"
    now = time.time()
    
    # Atomic Lua script in Redis
    script = """
    local tokens = tonumber(redis.call('get', KEYS[1]) or ARGV[1])
    local last_refill = tonumber(redis.call('get', KEYS[2]) or ARGV[3])
    local elapsed = tonumber(ARGV[3]) - last_refill
    local new_tokens = math.min(tokens + elapsed * tonumber(ARGV[2]), tonumber(ARGV[1]))
    if new_tokens >= 1 then
        redis.call('set', KEYS[1], new_tokens - 1)
        redis.call('set', KEYS[2], ARGV[3])
        return 1
    else
        return 0
    end
    """
    return redis.eval(script, 2, f"tokens:{user_id}", f"last:{user_id}", 
                      max_tokens, tokens_per_second, now)
```

### Leaky Bucket

Requests enter a queue ("bucket"). A processor drains the queue at a constant rate. Excess requests overflow (rejected). Smooths out bursts — even if 100 requests arrive simultaneously, they're served at the constant drain rate.

Use token bucket when you want to allow bursts but enforce average rate. Use leaky bucket when you need smooth, predictable output rate (e.g., sending emails — don't want to blast 1000 at once).

## Redis Implementation

Redis is the standard backing store for distributed rate limiting. Its atomic operations (via Lua scripts) prevent race conditions.

**Sliding window counter with Redis**:

```python
def check_rate_limit(user_id, limit, window_seconds):
    pipe = redis.pipeline()
    now = time.time()
    window_start = now - window_seconds
    key = f"ratelimit:{user_id}"
    
    # Remove old entries, add current, count
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window_seconds + 1)
    
    results = pipe.execute()
    request_count = results[2]
    return request_count <= limit
```

The sorted set key is user_id, score is timestamp. We remove old timestamps, add the current one, count the total. This is a clean sliding window log with atomic operations.

## Distributed Rate Limiting

Single-node rate limiting is simple. Distributed rate limiting (rate limit across a fleet of API servers) is harder.

**Centralized state (Redis)**: All servers talk to a shared Redis cluster. Simple consistency but adds latency (~1ms Redis round-trip per request). Redis Cluster shards keys — shard by user ID for linear scalability.

**Local + sync**: Each server maintains a local counter. Periodically sync with the central store. Allows some over-limit requests between syncs. Acceptable for approximate limits but not for strict enforcement.

**Consistent hashing for stickiness**: Route user_id requests to the same backend server. Local rate limiting is sufficient. Fails during server rebalancing.

**For most production APIs**: Centralized Redis with Lua scripts for atomicity. The ~1ms overhead is acceptable for API calls measured in milliseconds.

## Rate Limit Headers

Communicate rate limit status to clients:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 47
X-RateLimit-Reset: 1679500000
Retry-After: 30  (when 429 is returned)
```

RFC 6585 defines the `429 Too Many Requests` status code. Return it with `Retry-After` header so clients know when to retry.

## Rate Limit Granularity

Design rate limits at multiple levels:
- **Per user/API key**: The standard limit (100 requests/minute per user)
- **Per IP**: Defense against credential stuffing and DDoS
- **Per endpoint**: Expensive endpoints (search, LLM) have lower limits than cheap endpoints (profile read)
- **Global**: Circuit-breaker-style global limits protect downstream services

## Interview Trade-offs to Discuss

- **Algorithm**: Token bucket for user-facing APIs (bursting is UX-friendly). Sliding window for strict enforcement. Leaky bucket for smooth outbound flows.
- **Storage**: Redis for distributed. In-memory for single-server simplicity.
- **Consistency**: Strict limits require centralized state. Approximate limits allow local computation with eventual consistency.
- **Bypass prevention**: Rate limit by API key AND by IP. Rate limit at the edge (Cloudflare, API Gateway) before the request reaches your service.

Rate limiting is deceptively rich. The algorithm choice, the distributed coordination strategy, and the client communication design all matter. Demonstrating that you understand the trade-offs across all three is what separates strong candidates.

## Related Articles

- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Distributed Cache](/blog/system-design-distributed-cache)
- [System Design: Payment Gateway](/blog/system-design-payment-gateway)
- [API Design Best Practices Guide](/blog/api-design-best-practices-guide)
- [System Design Interview Framework](/blog/interview-system-design-framework)
