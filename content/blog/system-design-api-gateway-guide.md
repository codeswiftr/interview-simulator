---
title: "System Design: API Gateway Patterns, Rate Limiting, and Service Mesh"
description: "System design deep dive on API gateways — rate limiting algorithms, authentication, routing patterns, service mesh vs API gateway, and how to answer gateway questions in interviews."
date: "2026-03-20"
category: "System Design"
---

# System Design: API Gateway Patterns, Rate Limiting, and Service Mesh

API gateway design is a staple system design interview topic. Whether you're asked to design an API gateway from scratch, explain how rate limiting works, or compare service mesh and API gateway architectures, this guide gives you the technical depth to answer confidently.

## What an API Gateway Does

An API gateway is the entry point for all external client requests. It handles cross-cutting concerns that would otherwise pollute every microservice:

- **Routing:** Map `/api/users` to the Users service, `/api/orders` to Orders
- **Authentication/Authorization:** Validate JWTs or API keys before the request reaches upstream services
- **Rate Limiting:** Prevent abuse and enforce usage tiers
- **SSL Termination:** Handle TLS at the edge so internal services communicate over plain HTTP
- **Request/Response Transformation:** Add headers, transform payloads, translate protocols
- **Circuit Breaking:** Stop routing to unhealthy upstream services
- **Observability:** Centralized logging, tracing, and metrics collection

Well-known implementations: AWS API Gateway, Kong, Nginx, Envoy, Traefik, Caddy.

## Rate Limiting Algorithms

Rate limiting is frequently asked about in depth. Know these four:

### Fixed Window Counter

Divide time into fixed windows (e.g., every minute). Count requests per window per user. Reset at window boundary.

```
Window: [00:00, 00:01) → limit 100 requests
requests["user123"][window] += 1
if requests["user123"][window] > 100: reject
```

**Problem:** A burst at the window boundary can double the effective rate — 100 requests at :59, 100 at :00 next window = 200 requests in 2 seconds.

### Sliding Window Log

Store the timestamp of every request. On each request, remove timestamps older than the window, check the count.

**Pros:** Accurate. **Cons:** Memory-intensive — O(requests) storage per user.

### Sliding Window Counter

Approximate the sliding window using two fixed window counters:

```
rate = prev_window_count * (1 - elapsed_fraction) + current_window_count
```

If the current minute is 70% elapsed, weight the previous minute's count at 30%. Much more memory-efficient than log-based sliding window.

### Token Bucket

Each user has a bucket with capacity C tokens. Tokens refill at rate R per second. Each request consumes one token.

```
tokens = min(capacity, tokens + (now - last_refill) * rate)
if tokens >= 1: tokens -= 1; allow
else: reject
```

**Properties:** Allows bursts up to bucket capacity. Most API providers (AWS, Stripe, Twilio) use token bucket or variants.

### Leaky Bucket

Requests enter a queue (the "bucket") and are processed at a fixed rate. If the queue is full, reject.

**Properties:** Guarantees a constant output rate — useful for smoothing bursty traffic before sending to a backend that can't handle spikes.

## Distributed Rate Limiting

Single-server rate limiting is easy. Distributed is hard:

**Redis with atomic operations:**

```
-- Lua script for token bucket in Redis
local tokens = redis.call('GET', key) or capacity
tokens = math.min(capacity, tokens + refill_amount)
if tokens >= 1 then
    redis.call('SET', key, tokens - 1, 'EX', ttl)
    return 1  -- allow
else
    return 0  -- deny
end
```

Redis Lua scripts execute atomically, avoiding race conditions. The tradeoff: Redis becomes a hot dependency.

**Approximate local rate limiting:** Each gateway node tracks rate locally with a local counter, accepting some over/under-counting. Suitable when perfect enforcement isn't required (marketing APIs) but not for financial rate limiting.

## Authentication Patterns

**JWT validation at the gateway:** The gateway validates the JWT signature using the public key. No round-trip to an auth service for every request. Tradeoff: revocation requires short expiry + refresh tokens or a revocation list.

**API key validation:** Hash the API key and look up in a cache (Redis). First miss hits the database; subsequent requests hit cache. Revocation is instant.

**OAuth 2.0 token introspection:** Gateway calls the authorization server to validate the token. Accurate revocation, but adds latency. Optimize with caching with short TTLs.

## API Gateway vs Service Mesh

This is a common interview question that trips people up:

**API Gateway:** North-south traffic — requests coming from outside into your system. Focus: client-facing concerns (rate limiting, auth, docs, versioning).

**Service Mesh (Istio, Linkerd, Consul Connect):** East-west traffic — communication between your internal microservices. Focus: mTLS between services, service discovery, retries, circuit breaking, traffic splitting.

They're complementary, not competing. You typically have both: an API gateway at the edge, a service mesh for internal communication. The service mesh runs as sidecar proxies (usually Envoy) alongside each service.

**When to use each:**
- API gateway for: rate limiting external clients, API versioning, developer portal/docs, monetization
- Service mesh for: zero-trust security between services, A/B deployments, canary releases, distributed tracing across service boundaries

## Circuit Breaker Pattern

A circuit breaker at the gateway protects upstream services from cascade failures:

- **Closed:** Normal operation. Track error rates.
- **Open:** Too many errors. Immediately reject requests for this upstream, return fallback.
- **Half-Open:** After a timeout, send a probe request. If it succeeds, close the circuit.

Netflix's Hystrix popularized this pattern. Envoy and Kong implement it natively. Key configuration: error threshold percentage, measurement window, open duration before half-open probe.

## Common Interview Questions

**Q: How would you design rate limiting for a public API with three tiers: free (100 req/min), pro (1000 req/min), enterprise (unlimited)?**
Use token bucket per API key, with capacity and refill rate configurable by tier. Store in Redis with the API key as the Redis key. At the gateway, look up the plan before checking rate limits. For "unlimited," skip the rate check entirely or set an extremely high limit.

**Q: Your API gateway is a single point of failure. How do you make it resilient?**
Multiple gateway instances behind a load balancer. Stateless gateway (rate limiting state in Redis, not in-process). Health checks with automatic removal of unhealthy instances. Multi-region with traffic routing at DNS/anycast level.

**Q: How do you handle API versioning in a gateway?**
Three patterns: URL path (`/api/v2/users`), query parameter (`?v=2`), or `Accept` header (`Accept: application/vnd.api+json;version=2`). URL path versioning is most common because it's explicit and easy to route. The gateway routes to different upstream versions based on the path prefix.

## What Interviewers Are Scoring

When you answer API gateway questions, show that you understand trade-offs. Rate limiting in Redis is accurate but adds latency and a dependency — when does that matter? JWT validation is fast but stale tokens stay valid until expiry — when is that a problem? The best system design answers aren't "here's how to build it" — they're "here are the trade-offs, and here's why I'd make this choice given your constraints."
