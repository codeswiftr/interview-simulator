---
title: "API Gateway Engineer Interview Guide: Rate Limiting, Auth & Traffic Management"
description: "Master API gateway engineering interviews — reverse proxy architecture, rate limiting algorithms, JWT validation, request routing, circuit breakers, and observability at scale."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

# API Gateway Engineer Interview Guide: Rate Limiting, Auth & Traffic Management

API gateways are the front doors of modern microservices architectures — handling authentication, rate limiting, request routing, protocol translation, and observability for thousands of services. Engineering roles on API gateway teams at companies like Cloudflare, Kong, AWS API Gateway, or internal platform teams require deep knowledge of distributed systems, networking, and security. This guide covers what these interviews test.

## Reverse Proxy and Request Routing

API gateways are sophisticated reverse proxies. Interviewers probe your understanding of how they work:

**Request lifecycle**: Client request arrives → TLS termination → header inspection/modification → authentication/authorization → rate limit check → routing decision → upstream request → response transformation → client response. Know each phase and where failures can occur.

**Load balancing algorithms**: Round robin, least connections, random, weighted round robin, consistent hashing (for sticky sessions or cache affinity). Consistent hashing is particularly important — understand how virtual nodes improve distribution and minimize remapping when upstream instances change.

**Health checks**: Active (gateway pings upstream periodically), passive (gateway marks upstream unhealthy after consecutive failures), and hybrid. Know the tradeoff between health check overhead and detection latency.

**Protocol translation**: REST → gRPC transcoding (gRPC-gateway pattern), HTTP/1.1 → HTTP/2 multiplexing, WebSocket proxying. API gateways often need to handle protocol mismatch between client expectations and upstream service capabilities.

**Traffic shaping**: Canary deployments (route 5% of traffic to v2), A/B testing at the gateway layer, traffic mirroring (shadow requests to a new service without affecting production), and staged rollouts. These are system design topics that differentiate candidates.

## Rate Limiting: Algorithms and Implementation

Rate limiting is the most technically dense topic in API gateway interviews:

**Token bucket algorithm**: Tokens accumulate at a fixed rate up to a maximum bucket size. Requests consume tokens. Allows bursting up to bucket capacity while enforcing average rate. The standard algorithm for most rate limiting use cases. Implementation: store `(tokens, last_refill_timestamp)` per client key, calculate tokens added since last access.

**Sliding window**: Maintains a count of requests in the last N seconds using a sliding window, not a fixed window. More accurate than fixed window (avoids the "2x rate" attack at window boundaries). Implementation: Redis sorted sets with timestamps as scores, `ZREMRANGEBYSCORE` + `ZCARD` per request.

**Leaky bucket**: Requests enter a queue (the bucket); they exit at a constant rate. Enforces strict output rate but adds latency for requests that must wait. Better for smoothing bursty traffic than token bucket.

**Distributed rate limiting**: Single-node rate limiting is easy; distributed is hard. Options: Redis (centralized counter, serialized via INCR + EXPIRE), Redis Lua scripts for atomic multi-step operations, or gossip-based distributed counting (approximate but low-latency). The tradeoff is between accuracy and latency/availability.

Interview question: "Implement a rate limiter that allows 100 requests per minute per user using Redis." Strong candidates write the sliding window implementation, handle Redis failures gracefully (fail open vs. fail closed), and discuss the consistency tradeoffs in a multi-region deployment.

## Authentication and Authorization at the Gateway

**JWT validation**: Parsing and validating JWT tokens is gateway responsibility in modern architectures. Know: Base64url decoding of header/payload/signature, signature verification (HS256 HMAC vs. RS256 asymmetric), `exp` and `nbf` claim validation, and key rotation (JWKS endpoint polling, key ID matching).

**OAuth2 and OIDC**: Gateway as resource server validating opaque tokens via token introspection endpoint, or as OIDC relying party validating ID tokens. Understanding the authorization code flow, client credentials flow, and token introspection vs. JWT self-validation tradeoff (network call vs. local validation with staleness risk).

**API key management**: Hashed storage (never store raw API keys), key rotation without service disruption (dual-key validity periods), and key scoping (per-service permissions attached to key).

**mTLS**: Mutual TLS for service-to-service authentication at the gateway. Certificate rotation, root CA management, and SPIFFE/SPIRE for automated certificate lifecycle management.

## Observability and Resilience Patterns

**Circuit breakers**: Prevent cascading failures by temporarily stopping requests to a failing upstream. States: Closed (normal) → Open (blocking after failure threshold) → Half-Open (probing for recovery). Know Hystrix/Resilience4j as reference implementations and the key parameters (failure threshold, timeout, sleep window).

**Retry policies**: Retry transient failures with exponential backoff + jitter. Critical: only retry idempotent operations (GET, PUT with idempotency key), never blind-retry POST charges. Gateway-level retries vs. client-level retries — understand the interaction and amplification risk.

**Observability**: Request/response logging with sampling (full logging at 100% is cost-prohibitive at scale), distributed tracing (inject trace context headers, export to Jaeger/Zipkin/DataDog APM), and metrics (request rate, error rate, latency by route, by upstream). The golden signals (latency, traffic, errors, saturation) applied to gateway metrics.

**Request transformation**: Header manipulation (add X-Request-ID, strip internal headers before forwarding to external clients), response caching (Cache-Control headers, conditional GET support), and request/response body transformation (deprecated but still present in legacy architectures).

## Preparation Checklist

- Build a simple reverse proxy in Go or Rust — understand how HTTP connection pooling works
- Implement each rate limiting algorithm from scratch: token bucket, sliding window, fixed window
- Set up Kong or Caddy locally and configure routing, plugins, and authentication
- Read Kong, Envoy, and AWS API Gateway documentation — understand their design philosophies
- Study Envoy's architecture deeply if targeting service mesh roles (Istio, Linkerd use Envoy as data plane)

API gateway engineering roles sit at the intersection of network engineering, security, and distributed systems. Candidates who combine hands-on implementation experience with deep understanding of the algorithms and failure modes consistently stand out.
