---
title: "API Design Best Practices: Interview Guide for Backend Engineers"
description: "Complete guide to API design interviews — RESTful principles, versioning strategies, authentication patterns, error handling, pagination, and GraphQL vs REST tradeoffs for backend engineering roles."
date: "2026-03-20"
category: "Technical Skills Guides"
---

# API Design Best Practices: Interview Guide for Backend Engineers

API design is one of the most practical skills tested in backend engineering interviews. At companies that build developer-facing products (Stripe, Twilio, Plaid) or large-scale internal systems, API design decisions have enormous consequences — a poor API design is painful to use, hard to version, and generates disproportionate support burden. This guide covers what strong API design looks like and how to discuss it in interviews.

## RESTful Design Principles

REST is the dominant API style for web services. Interviewers test whether you understand REST deeply, not just that you know HTTP verbs.

**Resource-oriented URLs:**
URLs should identify resources (nouns), not actions (verbs). The HTTP method conveys the action.
- ✅ `GET /orders/{id}` — Get an order
- ❌ `GET /getOrder?id=123` — Verbing in URL
- ✅ `POST /orders` — Create an order
- ✅ `PATCH /orders/{id}` — Partial update
- ✅ `DELETE /orders/{id}` — Delete an order

**Nested resources:** When a resource belongs to another: `GET /users/{userId}/orders` — Get all orders for a user. But avoid deep nesting beyond 2-3 levels; it creates awkward URLs and often signals a modeling problem.

**Idempotency — a critical interview topic:**
- GET, PUT, DELETE: idempotent (same result each call)
- POST: not idempotent (creates new resource each call)
- PATCH: may or may not be idempotent depending on implementation

For payments and financial APIs: clients must be able to safely retry failed requests. This requires either idempotency keys (client generates a unique key per logical operation; server deduplicates on it) or idempotent PUT semantics. Stripe's idempotency key header is the industry model.

**Proper HTTP status codes:**
- 200 OK — Success
- 201 Created — Resource created (POST)
- 204 No Content — Success with no body (DELETE)
- 400 Bad Request — Client error (invalid input)
- 401 Unauthorized — Not authenticated
- 403 Forbidden — Authenticated but not authorized
- 404 Not Found — Resource doesn't exist
- 409 Conflict — Conflict with current state (duplicate, version conflict)
- 422 Unprocessable Entity — Syntactically valid but semantically invalid
- 429 Too Many Requests — Rate limited
- 500 Internal Server Error — Server error

A common mistake: returning 200 with `{"success": false}` for errors. Use appropriate error codes.

## API Versioning Strategies

API versioning is a classic senior interview topic — what are the options and tradeoffs?

**URL versioning** (`/v1/orders`): Clear, cacheable, easy to route. Downside: violates REST (version isn't a resource property). Used by Stripe, Twilio, most commercial APIs. **Most interview-correct answer** for most contexts.

**Header versioning** (`Accept: application/vnd.api+json;version=2`): Keeps URLs clean. Harder to test (can't just open in browser), harder to cache. Used by GitHub (Accept: `application/vnd.github.v3+json`).

**Query parameter versioning** (`?api_version=2021-11-15`): Stripe uses this internally as the stripe-version header. Visible in logs. Simple to implement.

**Date-based versioning:** Stripe's actual versioning — clients lock to a specific API date (e.g., `2023-10-16`). Stripe maintains backward compatibility for all versions indefinitely. More complex to maintain but excellent developer experience.

**Semantic versioning + deprecation policy:** Major version (breaking) vs minor (additive). Communicate deprecation timelines clearly — minimum 6-12 months notice for breaking changes at external APIs.

## Error Response Design

Consistent error responses make APIs dramatically easier to work with. Stripe's error format is the industry gold standard:

```json
{
  "error": {
    "type": "invalid_request_error",
    "code": "insufficient_funds",
    "message": "Your card has insufficient funds.",
    "param": "amount",
    "doc_url": "https://docs.stripe.com/error-codes#insufficient-funds"
  }
}
```

Key components: machine-readable error `code`, human-readable `message`, the invalid `param` if applicable, and a link to documentation.

**What to avoid:** Returning HTML error pages from APIs (happens when a framework's default error handler is used), vague error messages ("Something went wrong"), inconsistent error format across endpoints.

## Pagination Patterns

Pagination is tested in almost every API design interview:

**Offset pagination** (`?page=3&limit=20`): Simple to implement and understand. Problem: if items are inserted between page loads, the user misses items or sees duplicates. Poor performance for large offsets (the database must skip N rows).

**Cursor-based pagination** (`?after=eyJpZCI6MTAwfQ`): Uses an opaque cursor (often a base64-encoded record ID or timestamp) as the position marker. Solves the insertion problem and performs well at large offsets. Cannot seek to arbitrary pages — can only go forward/backward. Used by Twitter, Instagram, most GraphQL APIs.

**Keyset pagination:** Similar to cursor but exposes the sort key directly (`?after_id=1000`). Simpler but reveals implementation details.

Best practice: always include a `has_more` boolean and the next cursor in the response. Include total count separately if needed (expensive query for large datasets).

## GraphQL vs REST Tradeoffs

Senior backend engineers are expected to have an informed view on GraphQL:

**When GraphQL wins:**
- Complex, nested data with many optional fields (avoids over-fetching)
- Multiple frontend clients with different data needs (mobile needs less data than web)
- Rapid product iteration where data requirements change frequently
- Built-in schema documentation and type safety

**When REST wins:**
- Public APIs (easier to document, cache, version)
- File uploads (awkward in GraphQL)
- Simple CRUD services with well-defined resources
- Team unfamiliar with GraphQL (operational complexity is real)
- Performance-critical hot paths (REST endpoint can be optimized more easily than general GraphQL resolver)

**N+1 problem in GraphQL:** Naive resolver implementations make N database queries to fetch N items. DataLoader pattern batches and caches database calls within a single request.

Strong API design interview performance requires not just knowing the patterns but discussing their tradeoffs — why you'd choose cursor pagination over offset, when GraphQL's complexity is justified, and how error handling design affects developer experience. Companies like Stripe treat their API as a product; they look for engineers who think the same way.

## Related Articles

- [System Design: Rate Limiter (Advanced)](/blog/system-design-rate-limiter-advanced)
- [System Design: Payment Gateway](/blog/system-design-payment-gateway)
- [Stripe Interview Guide](/blog/stripe-interview-guide)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design Interview Framework](/blog/interview-system-design-framework)
