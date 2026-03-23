---
title: "API Design Interview Deep Dive: REST, GraphQL, and gRPC Compared"
description: "Master API design for interviews — REST maturity model, REST vs GraphQL vs gRPC trade-offs, API versioning strategies, pagination patterns, authentication, and rate limiting design decisions."
date: "2026-03-20"
category: "System Design"
---

# API Design Interview Deep Dive: REST, GraphQL, and gRPC Compared

API design appears in system design interviews, backend engineering interviews, and platform/API team interviews. Strong candidates go beyond "use REST" to articulate when each protocol is appropriate, how to design APIs that evolve cleanly, and what the operational trade-offs are.

## REST: The Richardson Maturity Model

Leonard Richardson's maturity model describes four levels of REST API design:

**Level 0 — HTTP Tunneling:** One endpoint, all operations through POST. XML-RPC, SOAP. Not REST.

**Level 1 — Resources:** Multiple endpoints, each representing a resource. `/users`, `/orders`. Still uses only POST/GET.

**Level 2 — HTTP Verbs:** Uses HTTP methods semantically (GET for read, POST for create, PUT/PATCH for update, DELETE for delete) and HTTP status codes (200 OK, 201 Created, 404 Not Found, 422 Unprocessable Entity). This is what most "REST APIs" are in practice.

**Level 3 — Hypermedia (HATEOAS):** Responses include links to related actions. `{"user": {...}, "links": {"orders": "/users/123/orders"}}`. Almost no one fully implements this.

When an interviewer asks if you know REST well, Level 2 is the baseline. Mentioning the maturity model and HATEOAS demonstrates deeper understanding.

## REST Design Principles

**Resource naming:**
- Nouns, not verbs: `/users`, not `/getUsers`
- Plural: `/users/123`, not `/user/123`
- Hierarchy for relationships: `/users/123/orders`
- Actions via HTTP methods, not URL paths

**Status code semantics:**
| Code | Meaning | When |
|------|---------|------|
| 200 OK | Success | GET, PUT, PATCH |
| 201 Created | Resource created | POST |
| 204 No Content | Success, no body | DELETE |
| 400 Bad Request | Client error, invalid input | Validation failures |
| 401 Unauthorized | Not authenticated | Missing/invalid auth |
| 403 Forbidden | Authenticated but not authorized | Wrong permissions |
| 404 Not Found | Resource doesn't exist | Bad ID |
| 409 Conflict | State conflict | Duplicate, version mismatch |
| 422 Unprocessable | Business logic validation | Domain errors |
| 429 Too Many Requests | Rate limited | Throttling |
| 500 Internal Server Error | Unexpected server error | Bugs, infrastructure |

**Pagination:** Offset-limit vs cursor-based.
- `?page=3&limit=20` — simple, breaks on inserts, slow on deep pages
- `?cursor=abc123&limit=20` — stable, constant-time, only supports sequential access

## GraphQL: When and Why

GraphQL solves specific problems REST has:

**Under-fetching:** REST requires multiple round trips to assemble data from multiple resources. GraphQL fetches exactly the shape you need in one request.

**Over-fetching:** REST endpoints return fixed shapes regardless of what the client needs. GraphQL returns only requested fields.

**Schema as documentation:** GraphQL's type system is introspectable. Clients can discover what's available without separate docs.

**When GraphQL makes sense:**
- Complex client-driven data requirements (dashboards, mobile apps with varied screens)
- Multiple clients (web, mobile, 3rd party) with different data needs
- Rapid product iteration where clients need field flexibility
- Already built out the data graph

**GraphQL trade-offs:**
- **N+1 problem:** GraphQL resolvers can trigger N+1 queries unless you implement DataLoader batching. This is mandatory at production scale.
- **Caching complexity:** REST has HTTP cache semantics at the URL level. GraphQL POSTs require application-level caching.
- **Query depth/complexity attacks:** A malicious client can craft a deeply nested query that exhausts server resources. Requires depth limiting and query complexity analysis.
- **Operational complexity:** Schema evolution with backward compatibility, deprecations, field-level analytics.

## gRPC: High-Performance Service-to-Service

gRPC uses Protocol Buffers over HTTP/2. It's the choice for internal service-to-service communication where performance matters.

**Advantages:**
- **Performance:** Binary serialization (smaller payloads vs JSON), HTTP/2 multiplexing, connection reuse
- **Type safety:** Proto definitions generate client stubs in multiple languages
- **Streaming:** First-class support for server streaming, client streaming, and bidirectional streaming
- **Strong contracts:** Proto definitions are a formal contract between services

**When gRPC makes sense:**
- Internal microservice communication (not client-facing)
- High-throughput, low-latency requirements
- Polyglot service communication (Go service calling Python service)
- Streaming use cases (log shipping, real-time data pipelines)

**gRPC trade-offs:**
- Not human-readable (debugging requires tooling like grpcurl or Postman with gRPC support)
- Less ecosystem support than REST for public APIs (no curl-based testing, browsers can't call gRPC directly)
- Proto schema evolution requires careful attention to backward compatibility (don't renumber fields)

## API Versioning Strategies

This is a classic interview question because there's genuine disagreement:

**URL versioning** (`/api/v2/users`): Explicit, easy to route, simple for clients to understand. Most common.

**Header versioning** (`Accept: application/vnd.api+json;version=2`): Cleaner URLs, HTTP-correct. Harder to test in browser.

**Query param versioning** (`/api/users?version=2`): Flexible, but often criticized as polluting the URL.

**No versioning (GraphQL style):** Add fields but never remove them. Mark deprecated fields with `@deprecated`. Clients can migrate at their own pace.

**Interview perspective:** URL versioning is the pragmatic answer for most REST APIs. The key insight to share: versioning is most important for breaking changes. Additive changes (new fields, new endpoints) don't require versioning.

## Common Interview Questions

**Q: How would you design a public API that handles 10K clients upgrading at different speeds?**
Run v1 and v2 in parallel for a deprecation period (typically 6-18 months). Log usage by API key and version to track migration. Sunset announcements with email/changelog. Remove v1 only after usage drops below threshold or deprecation window expires.

**Q: When would you choose GraphQL over REST for an internal API?**
When multiple teams have diverse data consumption patterns, when you want to avoid the coordination overhead of adding REST endpoints for every new client need, or when the data access pattern is genuinely graph-like. Not for simple CRUD APIs where REST is more transparent.

**Q: How do you prevent a GraphQL query from bringing down your server?**
Depth limiting (reject queries beyond depth 10), query complexity analysis (assign cost to each field/resolver, reject above threshold), per-client rate limiting on query complexity, field-level authorization. Also: DataLoader for N+1 prevention, query whitelisting for public APIs.
