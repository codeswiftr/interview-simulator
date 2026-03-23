---
title: "API Platform Engineer Interview Guide"
description: "Technical interview preparation for API platform engineering roles: API gateway design, rate limiting, authentication patterns, versioning strategies, developer portals, and what companies like Kong, Apigee, Stripe, Twilio, and API-first companies expect from platform engineers."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

# API Platform Engineer Interview Guide

API platform engineering is the discipline of building and operating the infrastructure that other engineers use to expose and consume APIs. It sits between backend engineering and platform/infrastructure work — requiring deep understanding of HTTP semantics, distributed systems, security, and developer experience. Companies with API-first business models (Stripe, Twilio, SendGrid, Plaid) have dedicated API platform teams; large tech companies have internal API gateway teams; and companies like Kong, Apigee (Google), and Mulesoft sell API management platforms.

## API Gateway Architecture

The API gateway is the core component of API platform infrastructure. Understanding its responsibilities and design tradeoffs is the foundation of API platform interviews.

**Gateway responsibilities**: Request routing (to upstream microservices), authentication and authorization enforcement, rate limiting and throttling, request/response transformation, SSL termination, load balancing, caching, logging and observability. The gateway is a reverse proxy with domain-specific intelligence layered on top.

**L4 vs. L7 proxies**: L4 proxies (like HAProxy in TCP mode) route at the transport layer — faster but no HTTP awareness. L7 proxies (Nginx, Envoy, Kong) route at the application layer — can inspect headers, paths, bodies, enabling sophisticated routing logic. API gateways are L7 proxies.

**Sidecar proxy pattern**: In service mesh architectures (Istio, Linkerd), each service has a sidecar proxy (Envoy) that handles all inbound/outbound traffic. The control plane pushes routing configuration to the sidecar fleet. API gateway functions can be distributed to the sidecar layer (east-west traffic) while a separate ingress gateway handles north-south traffic.

**Gateway vs. direct service communication**: A gateway adds a network hop and a potential single point of failure. The tradeoffs: gateways enable centralized policy enforcement, reduce coupling between API consumers and service internals, and enable gradual migration of backend services. For very low-latency requirements, some architectures bypass the gateway for internal traffic.

## Rate Limiting Design

Rate limiting is a core API platform interview topic — both design and implementation:

**Algorithms**: Token bucket (requests consume tokens; tokens refill at a fixed rate — allows bursting up to bucket size). Leaky bucket (requests enter a queue; processed at a fixed rate — no bursting). Fixed window (count requests in a fixed time window; reset at window boundary — susceptible to boundary bursting). Sliding window log (track individual request timestamps; count in trailing window — accurate but memory-intensive). Sliding window counter (approximate sliding window using weighted fixed window counts — efficient and accurate enough).

**Distributed rate limiting**: A single API gateway node can do in-memory rate limiting. Multiple gateway nodes require a shared counter store. Redis is the standard: `INCR` + `EXPIRE` for fixed window, sorted sets for sliding window log. The challenge: atomic increment and expiry requires Lua scripts or `INCR`+`EXPIRE` with careful ordering. Redis Cluster for high availability; race conditions when two nodes check before incrementing.

**Rate limit headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`. These are de facto standards (IETF draft standardization ongoing). Returning these headers helps API consumers implement backoff correctly.

**Rate limit key strategies**: By API key (most common), by user ID, by IP address, by endpoint (different limits for expensive operations), by plan tier (Stripe's API gives higher limits to higher-plan customers).

## Authentication Patterns

**API keys**: Simplest. Long random strings, stored hashed (SHA-256) in the database. Benefits: easy to issue and rotate, no expiry by default, easy to audit. Drawbacks: no built-in expiry, long-lived credentials that can be leaked. Use for server-to-server API access.

**JWT (JSON Web Tokens)**: Self-contained tokens with claims. The gateway can validate JWTs without calling the auth service (stateless validation) using the signing key or JWKS endpoint. Expiry built-in (`exp` claim). Drawbacks: revocation is hard (the token is valid until expiry; revocation requires a blocklist, reintroducing statefulness).

**OAuth 2.0**: The standard for delegated authorization. Client credentials flow (server-to-server), authorization code flow (user-delegated access), device code flow. The gateway enforces token validation and scope checking. OpenID Connect adds identity on top of OAuth.

**mTLS (Mutual TLS)**: Both client and server present certificates. Strong authentication, no shared secrets, excellent for service-to-service communication. Complexity: certificate management, rotation, CA infrastructure.

## API Versioning Strategies

Versioning is contentious — every approach has tradeoffs:

**URL path versioning** (`/v1/users`, `/v2/users`): Most common. Clear, cacheable, easy to route at the gateway. Drawback: version is in the URI, which some argue violates REST principles (resource identity should be stable).

**Header versioning** (`Accept: application/vnd.api+json;version=2`): Cleaner URIs, version is a negotiation concern. Harder to use in browsers, harder to debug.

**Query parameter versioning** (`/users?version=2`): Simple, but clutters query strings.

**Evolutionary APIs (no versioning)**: Add-only changes with field deprecation. GraphQL's approach — schema is additive, clients request only what they need. Works when you control clients; harder for public APIs with unknown consumers.

The API platform's role in versioning: routing version-specific requests to version-specific backend deployments, enforcing deprecation policies (returning `Sunset` headers, blocking requests to deprecated versions after the deprecation date).

## Developer Experience

API platform engineers often own the developer portal:

**Documentation**: OpenAPI/Swagger specs as the source of truth. Auto-generated reference docs. Interactive "Try It" consoles (Swagger UI, Redoc, Readme.com). Good documentation is a competitive differentiator — Stripe's documentation is the reference standard.

**SDK generation**: OpenAPI spec → generated SDKs in multiple languages (openapi-generator, Speakeasy). SDK quality matters — generated SDKs often require manual polish.

**Sandbox environments**: Test API keys hitting a mock backend (no real side effects). Essential for developers to explore APIs without consequences. Stripe's test mode is the model implementation.

## Who Hires API Platform Engineers

**API management vendors**: Kong (open-source API gateway + enterprise platform), MuleSoft (Salesforce), Apigee (Google Cloud), AWS API Gateway team.

**API-first companies**: Stripe (internal platform team), Twilio, SendGrid (Twilio), Plaid, Braintree. These companies treat the API as the product — platform quality is existential.

**Large tech internal platform teams**: Meta, Google, Netflix, Uber all have internal API gateway and platform teams managing enormous request volumes.

API platform engineering rewards engineers who think in systems — who understand that the gateway is infrastructure for other engineers and must be correct, observable, and operable above all else.
