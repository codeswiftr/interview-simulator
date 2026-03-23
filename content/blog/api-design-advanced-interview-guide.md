---
title: "API Design Advanced Interview Guide: REST, GraphQL, gRPC, and Versioning"
description: "Deep-dive API design interview prep — REST constraints, resource naming, idempotency, versioning strategies, pagination, GraphQL vs REST tradeoffs, and gRPC."
date: "2026-03-20"
category: "Backend"
---

# API Design Advanced Interview Guide: REST, GraphQL, gRPC, and Versioning

API design questions separate mid-level from senior backend engineers. They test not just technical knowledge but design judgment — knowing when to apply which pattern, how to reason about breaking changes, and how to balance developer experience with operational constraints. This guide covers the depth expected at senior and staff levels.

## REST Fundamentals Interviewers Actually Test

Most candidates say "REST" but can't explain what makes an API RESTful. The six Roy Fielding constraints come up at senior levels:

1. **Client-server separation** — UI and data storage concerns are decoupled.
2. **Statelessness** — Each request contains all information needed; no server-side session.
3. **Cacheability** — Responses must define whether they're cacheable.
4. **Uniform interface** — Resource identification in requests, manipulation through representations, self-descriptive messages, HATEOAS.
5. **Layered system** — Clients can't tell whether they're connected to the end server or an intermediary.
6. **Code on demand (optional)** — Servers can extend client functionality via executable code.

Interviewers often ask: "Is your API truly RESTful?" The honest answer for most production APIs is "REST-inspired" — HATEOAS and code-on-demand are almost universally omitted. Being able to articulate this distinction signals sophistication.

## Resource Naming and HTTP Verb Semantics

Strong API designers follow consistent conventions:

- **Nouns, not verbs:** `/users/{id}` not `/getUser`
- **Plural collections:** `/orders`, `/products`
- **Nested only when ownership is clear:** `/users/{id}/addresses` works; `/users/{id}/orders/{id}/items/{id}/reviews` is too deep
- **Actions as sub-resources:** `/payments/{id}/refund` (POST) rather than `/refundPayment`

HTTP verb semantics matter for idempotency — a critical concept for distributed systems:

| Method | Idempotent | Safe | Use case |
|--------|-----------|------|----------|
| GET | Yes | Yes | Read |
| PUT | Yes | No | Full replace |
| PATCH | No | No | Partial update |
| DELETE | Yes | No | Remove |
| POST | No | No | Create, non-idempotent actions |

**Common interview question:** "Why is PUT idempotent but POST isn't?" Calling PUT `/users/1` with the same body ten times produces the same state. Calling POST `/users` ten times creates ten users.

## Idempotency Keys for Non-Idempotent Operations

When POST operations have side effects (payments, email sends, order creation), idempotency keys allow safe retries. The client generates a unique key; the server deduplicates on it:

```
POST /payments
Idempotency-Key: uuid-abc123

{ "amount": 9999, "currency": "USD" }
```

The server stores the key with the result. Subsequent requests with the same key return the cached response without re-executing the operation. This is how Stripe handles payment retries. Interviewers at fintech and payments companies almost always ask this.

## Versioning Strategies

API versioning is one of the most debated topics in API design. Three main approaches:

**URL versioning:** `/v1/users`, `/v2/users`
- Pros: Obvious, easy to route, cacheable.
- Cons: Violates REST (URL should identify a resource, not a version). Creates duplication.

**Header versioning:** `Accept: application/vnd.myapi.v2+json`
- Pros: Cleaner URLs, REST-compliant.
- Cons: Less discoverable, harder to test in browsers, requires client sophistication.

**Query parameter versioning:** `/users?version=2`
- Pros: Simple to implement.
- Cons: Easy to ignore, breaks caching semantics.

The right answer depends on context. URL versioning is most common in practice because it's explicit and easy to route at the infrastructure level. For internal APIs or SDK-based clients, header versioning is often cleaner.

**Key principle:** Additive changes are non-breaking (new fields, new endpoints). Removing or renaming fields, changing types, or altering semantics requires a version bump.

## Pagination Patterns

Three pagination strategies come up frequently:

**Offset pagination:** `?offset=40&limit=20`
- Simple but has the "page drift" problem — items inserted during pagination shift subsequent pages.
- Fine for non-real-time data, bad for feeds.

**Cursor pagination:** `?cursor=eyJpZCI6MTAwfQ&limit=20`
- Cursor encodes the position (often a timestamp or ID). Stable under concurrent writes.
- Used by Twitter, Slack, and most modern APIs.
- Downside: Can't jump to arbitrary pages.

**Keyset pagination:** `?after_id=1000&limit=20`
- Similar to cursor but uses a visible key rather than an encoded token.
- Efficient because it leverages indexed columns.

For interview questions about designing a feed or activity stream, cursor or keyset pagination is almost always the right answer.

## GraphQL: When It Wins and When It Doesn't

GraphQL solves specific problems: over-fetching, under-fetching, and complex client-driven data requirements. It excels when:

- Multiple client types (web, mobile, third-party) have different data needs.
- The data model has rich relationships clients need to traverse.
- Developer experience and iteration speed are priorities.

GraphQL struggles when:
- **Caching is critical** — REST's URL-based caching is trivial; GraphQL caching requires persisted queries or CDN workarounds.
- **File uploads** are required — awkward in GraphQL, trivial in REST.
- **Simple CRUD** — the schema overhead isn't justified.
- **Public APIs** — rate limiting and abuse prevention are harder with arbitrary query depth.

N+1 query problems are the most common GraphQL performance pitfall. The solution is DataLoader — batching and caching database calls per request. Expect this to come up in any serious GraphQL interview.

## gRPC for Internal Services

gRPC uses Protocol Buffers over HTTP/2. It's the right choice for internal service-to-service communication where:

- Performance matters (binary encoding vs JSON)
- Strict contracts are valuable (`.proto` files)
- Streaming is required (bidirectional streaming is native)
- Polyglot environments benefit from generated clients

The tradeoff: gRPC is harder to debug (no human-readable format), requires a build step, and is harder to consume from browsers without a gateway (gRPC-Web).

In interviews, the right answer is usually: REST or GraphQL for external/client-facing APIs, gRPC for internal microservices where performance and contract strictness matter.

## Error Design

Good error responses are often overlooked but indicate API design maturity:

```json
{
  "error": {
    "code": "PAYMENT_DECLINED",
    "message": "The card was declined by the issuing bank.",
    "details": { "decline_code": "insufficient_funds" },
    "request_id": "req_abc123"
  }
}
```

Key principles: machine-readable error codes (not just HTTP status codes), human-readable messages, request IDs for debugging, and structured detail for programmatic handling.

## Putting It Together in an Interview

When asked to design an API, work through this sequence:

1. **Clarify the clients and their needs** — who consumes this API and how?
2. **Define resources and their relationships** — draw it out if whiteboarding.
3. **Choose the right paradigm** — REST, GraphQL, or gRPC based on requirements.
4. **Define key endpoints** with verbs, request/response shapes, and status codes.
5. **Address pagination, filtering, and sorting** for collection endpoints.
6. **Discuss versioning strategy** and breaking vs. non-breaking changes.
7. **Cover error design** and idempotency for mutation endpoints.
8. **Mention auth** — JWT, API keys, OAuth2 depending on context.

Interviewers at senior level want to see you reason through tradeoffs, not recite patterns. Ask clarifying questions, explain why you're making each choice, and flag the things you're consciously deprioritizing.
