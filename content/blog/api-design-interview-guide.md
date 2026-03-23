# API Design Interview Guide 2024: REST, GraphQL, gRPC, and the Design Conversation

*API design questions show up in system design rounds but rarely get dedicated preparation. Most candidates wing it. This guide gives you the frameworks to answer precisely.*

---

API design is one of the most underprepared topics in system design interviews. Candidates spend weeks on database sharding and message queues, then get asked "how would you version this API?" and give a vague answer about URL paths. Interviewers notice.

API design is also a topic where opinion and best practice overlap in ways that create opportunities for nuanced discussion — exactly what senior-level interviews reward. The goal is not to recite rules but to demonstrate that you have thought deeply about trade-offs between different design decisions and can defend your choices with concrete reasoning.

This guide covers the full spectrum: REST fundamentals, GraphQL trade-offs, gRPC use cases, versioning strategies, authentication patterns, rate limiting, idempotency, and the interview question frameworks that demonstrate genuine API design fluency.

---

## REST API Design Principles

### Resource Modeling

The foundation of REST is resources — not actions. The URL identifies what you are operating on; the HTTP verb identifies what you are doing to it.

Correct resource modeling:
```
GET    /users/{id}           # Retrieve a user
POST   /users                # Create a user
PUT    /users/{id}           # Replace a user (full update)
PATCH  /users/{id}           # Update a user (partial update)
DELETE /users/{id}           # Delete a user
GET    /users/{id}/orders    # Retrieve orders for a user
POST   /users/{id}/orders    # Create an order for a user
```

The common anti-patterns that signal poor design:
```
POST /getUser                # Action in URL, wrong verb
GET  /deleteUser?id=123      # Mutation in GET (cacheable, dangerous)
POST /user/create            # Action noun in URL
GET  /api/v1/fetchUserData   # Verb in URL
```

**Nested resources**: Nest when the nested resource does not have meaning without the parent. Orders belonging to a user: `/users/{id}/orders`. But if orders can be accessed globally (by an admin), also expose `/orders/{id}` as a top-level resource. The rule: never more than two levels of nesting in the URL.

**Singleton vs. collection resources**: A collection is plural (`/users`), a singleton is singular within context (`/users/{id}/profile` — a user has one profile). This signals to clients whether they receive an array or an object.

### HTTP Verb Semantics

The correct semantics matter for caching, idempotency, and client behavior:

| Verb | Idempotent | Safe | Use for |
|------|-----------|------|---------|
| GET | Yes | Yes | Read. Never mutate state. |
| HEAD | Yes | Yes | Metadata only (same as GET but no body). |
| POST | No | No | Create, or operations that do not fit other verbs. |
| PUT | Yes | No | Full replacement of a resource. |
| PATCH | No | No | Partial update. |
| DELETE | Yes | No | Delete. Repeated calls return 404 after first success. |
| OPTIONS | Yes | Yes | CORS preflight, capability discovery. |

**Idempotency**: An operation is idempotent if calling it N times has the same effect as calling it once. PUT is idempotent because sending the same full representation twice leaves the resource in the same state. PATCH is not because the patch semantics may be relative (e.g., "increment quantity by 1").

**Safe**: A safe method does not modify state. GET, HEAD, and OPTIONS are safe. This allows caches and browsers to make these requests automatically without user confirmation.

### HTTP Status Codes

The single most-abused aspect of REST APIs. Using the right status code communicates intent precisely and enables clients to handle errors programmatically without parsing response bodies.

| Code | Meaning | Use for |
|------|---------|---------|
| 200 OK | Success | GET, PUT, PATCH, DELETE that returns data |
| 201 Created | Resource created | POST that creates a resource |
| 204 No Content | Success, no body | DELETE, PUT/PATCH with no response body |
| 400 Bad Request | Client sent invalid data | Validation errors, malformed request |
| 401 Unauthorized | Not authenticated | Missing or invalid credentials |
| 403 Forbidden | Authenticated but not authorized | Correct credentials, insufficient permissions |
| 404 Not Found | Resource does not exist | Unknown ID, or resource hidden for security |
| 409 Conflict | State conflict | Duplicate creation, optimistic lock failure |
| 410 Gone | Resource permanently deleted | When you want to communicate intentional removal |
| 422 Unprocessable Entity | Semantic validation failure | Request is well-formed but logically invalid |
| 429 Too Many Requests | Rate limited | Include `Retry-After` header |
| 500 Internal Server Error | Unexpected server failure | Never return for validation errors |

The critical distinction between 401 and 403: 401 means "I do not know who you are, please authenticate." 403 means "I know who you are, and you are not allowed to do this." Conflating them leaks information or degrades client behavior.

### API Versioning Strategies

Versioning is necessary because APIs are contracts, and contracts must evolve. There are three dominant strategies, each with genuine trade-offs.

**URL Path Versioning** (`/api/v1/users`):
- Visible, cacheable, easy to route
- Works with all clients (no header support required)
- Creates parallel URL namespaces that must be maintained
- Forces clients to change URLs on upgrade
- The most common approach in practice; used by Stripe, Twitter, GitHub

**HTTP Header Versioning** (`API-Version: 2` or `Accept: application/vnd.api+json;version=2`):
- Clean URLs
- Harder to test (cannot click a link to test a version)
- Requires client header support
- Harder to cache correctly (Vary header complexity)
- Used by GitHub's Content-Type approach

**Query Parameter Versioning** (`/users?version=2`):
- Flexible, easy to add
- Optional versioning (default to latest if absent)
- Breaks caching without careful Vary header management
- Easier to forget or accidentally omit

**The right answer for interviews**: URL path versioning for public APIs because it is explicit, cacheable, and works everywhere. Header versioning for internal APIs where you control the clients and want clean URLs. Always have a position on this and defend it — the interviewer is looking for reasoning, not the "right" answer.

---

## Pagination Patterns and Performance Implications

Pagination is a topic with real performance consequences that interviewers probe specifically.

### Offset Pagination

```
GET /users?limit=20&offset=40
```

The simplest pattern. Skip the first 40 records, return the next 20.

**The hidden performance problem**: `OFFSET` in SQL does not skip records efficiently — it scans and discards them. `SELECT * FROM users ORDER BY created_at OFFSET 10000000 LIMIT 20` scans and discards 10 million rows before returning 20. On large tables, this is catastrophically slow.

**The consistency problem**: If a record is inserted or deleted between page 1 and page 2 requests, the user sees duplicated or missing records. Offset pagination does not handle concurrent mutations gracefully.

Use offset pagination only for small, relatively static datasets where total count display ("showing 1-20 of 342") is required.

### Cursor Pagination (Keyset Pagination)

```
GET /users?limit=20&after=cursor_opaque_value
```

The cursor encodes the position of the last item seen (typically the ID or a combination of sort fields, base64-encoded for opacity). The next query uses a WHERE clause: `WHERE id > last_id ORDER BY id LIMIT 20`.

**Performance advantage**: This query uses an index. No scanning of discarded rows. Consistent O(log n) performance regardless of page depth.

**Consistency**: Because you are querying based on a stable position in the data, inserts and deletes between requests do not cause duplicates or gaps.

**Trade-off**: You lose the ability to jump to page N, or display "showing 221-240 of 4,521." Bidirectional cursors (next/previous) require additional implementation. Total counts require a separate COUNT query (expensive for large tables).

Used by: Facebook Graph API, GitHub, Slack, Stripe.

### Keyset Pagination with Multi-Column Sort

For complex sort orders (e.g., "sort by score descending, then by ID ascending"), the cursor must encode all sort columns. The WHERE clause becomes:

```sql
WHERE (score < last_score)
   OR (score = last_score AND id > last_id)
```

This is the correct implementation of cursor pagination for non-unique sort keys. The cursor value is `base64({"score": 0.94, "id": 12345})`.

**Interview signal**: Knowing that cursor pagination requires encoding all sort fields (not just the primary key) demonstrates real-world database and API design experience.

---

## GraphQL vs. REST: A Precise Trade-off Analysis

GraphQL is not a replacement for REST. It solves specific problems and creates others. Knowing when to choose which is what interviewers want to hear.

### The Problems GraphQL Solves

**Overfetching**: REST endpoints return fixed shapes. A mobile client requesting `/users/{id}` to show an avatar and name receives the full user object (email, address, preferences, billing info). Wasted bandwidth and parsing.

**Underfetching / Request Waterfalling**: To render a user's profile page, the client may need: the user, their recent posts, and the author info on those posts. REST requires three sequential requests. GraphQL can fetch all of this in a single query.

**Schema as contract**: GraphQL's type system and introspection enable automatic documentation, strong typing, and tooling (code generation, IDE integration) that REST requires manual OpenAPI specs to approximate.

### The N+1 Problem and DataLoader

GraphQL's recursive resolution creates a classic N+1 query problem. A query for 10 users, each with their posts, triggers: 1 query for users, then 10 separate queries for each user's posts — 11 queries total.

The standard solution is DataLoader, a batching and caching utility. Instead of resolving each user's posts immediately, DataLoader collects all the user IDs requested in a single tick and issues a single batched query: `SELECT * FROM posts WHERE user_id IN (1, 2, 3, ..., 10)`.

DataLoader implementation pattern:
1. Resolver calls `dataLoader.load(userId)` instead of querying directly
2. DataLoader queues all `.load()` calls in the current execution context
3. In the next tick, it calls the batch function with all queued IDs
4. Batch function returns a sorted array of results
5. Each promise resolves with its individual result

**Interview signal**: Mentioning DataLoader specifically when asked about GraphQL performance demonstrates that you have implemented GraphQL in production, not just read about it.

### GraphQL Subscriptions

For real-time data, GraphQL Subscriptions use WebSocket connections. The client sends a subscription operation; the server pushes updates whenever the subscribed event occurs.

```graphql
subscription {
  messageAdded(channelId: "channel-123") {
    id
    text
    author { name }
  }
}
```

The implementation typically uses a publish-subscribe pattern internally: the mutation resolver publishes to a topic, the subscription resolver subscribes to that topic and streams results to connected clients.

### When to Choose GraphQL vs. REST

| Choose REST when | Choose GraphQL when |
|-----------------|---------------------|
| Simple CRUD resources | Multiple clients with different data needs |
| Caching is critical (REST caches naturally via HTTP) | Rapid frontend iteration with flexible queries |
| External public API (simpler for third parties) | Complex nested data with relationship traversal |
| Team is unfamiliar with GraphQL | Mobile clients where bandwidth is constrained |
| File uploads are a primary use case | Real-time subscriptions needed |

**The hybrid approach**: Use REST for simple, cacheable, public-facing endpoints. Use GraphQL for internal BFF (Backend for Frontend) layers where multiple client types have different data requirements.

---

## gRPC and Protocol Buffers

### When gRPC Outperforms REST

gRPC uses HTTP/2 as the transport and Protocol Buffers as the serialization format. This combination provides:

**Performance**: Protocol Buffers serialize to binary, not JSON. Typically 3-10x smaller payloads and 5-10x faster serialization. HTTP/2 enables multiplexing (multiple requests over one connection), header compression, and server push.

**Streaming**: gRPC supports four communication patterns:
- Unary (standard request/response)
- Server streaming (one request, stream of responses)
- Client streaming (stream of requests, one response)
- Bidirectional streaming (both sides stream simultaneously)

**Generated clients**: Protocol Buffer definitions generate type-safe clients in every major language. No manual HTTP client code, no JSON parsing, no inconsistency between client and server types.

**Strong typing**: The `.proto` file is the contract. The compiler rejects type mismatches at build time.

### When to Choose gRPC Over REST

Internal microservice communication is the primary use case. When services are written in multiple languages, gRPC's generated clients eliminate the impedance mismatch between languages. When throughput and latency are critical (payment processing, real-time analytics), the binary protocol matters.

**When not to use gRPC**: Browser clients cannot call gRPC directly (HTTP/2 is not fully accessible from browsers; gRPC-Web is a workaround with limitations). Public APIs benefit from REST's universality — any HTTP client can call it without code generation. Debugging gRPC is harder than debugging REST (binary payloads are not human-readable in transit).

### Breaking Changes in Protocol Buffers

Protocol Buffers are backward-compatible by field number, not field name. Adding a new optional field with a new field number is always safe — old clients ignore unknown fields. Removing a required field is a breaking change. Changing a field's type is a breaking change. Reusing a field number for a different type is a catastrophic breaking change.

Best practice: never delete field numbers, just mark them as reserved. Never reuse field numbers.

---

## API Versioning and Breaking Changes

### What Constitutes a Breaking Change

A breaking change is any modification that requires existing clients to change their code to continue functioning correctly. Specific examples:

**Always breaking**:
- Removing or renaming a required field in a response
- Changing the type of a field (string to integer)
- Removing an endpoint
- Changing authentication requirements
- Changing the meaning of an existing field
- Removing values from an enum

**Never breaking**:
- Adding optional request fields (clients that do not send them still work)
- Adding new response fields (clients that ignore unknown fields still work)
- Adding new endpoints
- Adding new enum values (though this can break exhaustive switch statements — a practical concern)

**Conditionally breaking**:
- Making a previously optional field required (breaks clients that omit it)
- Adding required request fields (breaks clients that do not send them)
- Changing validation rules to be stricter

### Deprecation Strategy

A sound deprecation lifecycle:
1. Announce the deprecation with a sunset date (minimum 6 months for public APIs, 3 months for internal)
2. Add `Deprecation` and `Sunset` headers to deprecated endpoint responses
3. Add deprecation notices to documentation and changelogs
4. Notify API consumers directly if possible
5. At sunset, return 410 Gone (not 404) so clients know the removal was intentional

The `Deprecation` header (RFC 8594) carries a timestamp when the deprecation was announced. The `Sunset` header carries the date after which the endpoint will cease to function.

---

## Authentication in APIs

Different authentication schemes suit different contexts. The interview expects you to know which to apply when.

### API Keys

Simple shared secrets, typically passed in a header (`Authorization: ApiKey abc123` or `X-API-Key: abc123`).

**Best for**: Server-to-server communication, developer API integrations, simple read-only access.

**Limitations**: No expiration by default. If leaked, the key must be rotated (and all consumers updated). No fine-grained permissions without additional infrastructure. Cannot embed user identity.

**Implementation considerations**: Store only a hashed version of the key in your database (same as passwords). Display the key only once at creation. Enable key rotation without breaking existing clients by allowing overlapping validity periods.

### JWT (JSON Web Tokens)

Self-contained tokens that encode claims (user ID, roles, expiration) and are signed by the server. Clients include the token in subsequent requests; the server verifies the signature without a database lookup.

**Structure**: Header (algorithm) + Payload (claims) + Signature (HMAC or RSA). Base64url-encoded, dot-separated.

**Best for**: Stateless authentication where you want to avoid session store lookups. Microservices where multiple services need to verify user identity without calling a central auth service.

**Limitations**: Cannot be invalidated before expiration without a revocation list (which adds statefulness and undermines the stateless benefit). If the JWT secret is compromised, all tokens are compromised. Payload is base64-encoded, not encrypted — do not store sensitive data in it.

**Access + refresh token pattern**: Short-lived access tokens (15 minutes) are used for API calls. Long-lived refresh tokens (7-30 days) are stored securely (httpOnly cookie) and used only to obtain new access tokens. Revocation affects refresh tokens only, limiting the revocation list size.

### OAuth 2.0

A delegation framework, not an authentication protocol. OAuth 2.0 answers: "can Application A act on behalf of User B?" — not "who is User B?"

**Core grant types**:

- **Authorization Code**: User authenticates with the auth server, receives an authorization code, which the application exchanges for access and refresh tokens. The user's credentials never touch the application. Use this for web apps and mobile apps where you need delegated access.

- **Client Credentials**: Application authenticates directly with the auth server using its own credentials. No user involved. Use this for machine-to-machine (server-to-server) access.

- **PKCE (Proof Key for Code Exchange)**: Extension of Authorization Code for public clients (mobile apps, SPAs) that cannot securely store a client secret. Prevents authorization code interception attacks.

**OpenID Connect (OIDC)**: A thin identity layer on top of OAuth 2.0 that adds user authentication. Provides an ID token (a JWT with user claims). This is how "Sign in with Google" works.

**Interview signal**: Knowing that OAuth 2.0 is authorization, not authentication, and knowing when to add OIDC for identity, distinguishes candidates who have implemented auth from those who have read about it.

---

## Rate Limiting Design

### Per-User vs. Per-Endpoint Rate Limiting

**Per-user limits** prevent any single user from monopolizing resources. Common in SaaS APIs: free tier gets 100 requests/minute, paid tier gets 1,000 requests/minute. Implemented using the API key or user ID as the rate limit key.

**Per-endpoint limits** protect specific expensive operations regardless of user. A `/reports/generate` endpoint that triggers heavy computation might be limited to 5 requests/minute even for premium users.

**IP-based limits** protect against unauthenticated abuse. Less precise (shared NAT means thousands of users behind one IP) but useful as a first line of defense.

In practice, use all three layers: IP limits for unauthenticated requests, user limits for authenticated requests, endpoint limits for expensive operations.

### Token Bucket vs. Sliding Window

**Token bucket**: Each user has a bucket that holds N tokens. The bucket refills at a rate of R tokens per second, up to the maximum N. Each request consumes one token. If the bucket is empty, the request is rejected.

Advantages: allows bursting (a user can consume tokens accumulated over time in a short burst). Smooth refill regardless of when requests arrive.

Implementation with Redis: store the token count and last refill time. On each request, calculate how many tokens have accrued since the last refill, add them (capped at max), and attempt to consume one. Use a Lua script for atomicity.

**Sliding window counter**: Track requests in a rolling time window. Keep a sorted set of request timestamps (or a counter per small time bucket). On each request, count requests in the last N seconds. If count >= limit, reject.

Advantages: more precise than fixed windows (no boundary effects where a user can double their rate limit by making requests at the end of one window and the beginning of the next).

Redis implementation with sorted sets: `ZADD rate_limit:{user_id} {timestamp} {unique_id}`, then `ZCOUNT rate_limit:{user_id} {window_start} +inf`. Prune old entries with `ZREMRANGEBYSCORE`.

**Fixed window**: Count requests in the current fixed window (e.g., the current minute). Simplest to implement, subject to boundary doubling.

**Interview answer**: For external APIs, sliding window counter is most precise and fair. For high-throughput internal systems, token bucket's burst allowance better matches natural traffic patterns.

### Rate Limit Headers

Communicating rate limit state to clients enables them to self-throttle:

```
X-RateLimit-Limit: 1000          # Total allowed in window
X-RateLimit-Remaining: 743       # Remaining in current window
X-RateLimit-Reset: 1672531200    # Unix timestamp when window resets
Retry-After: 30                  # Seconds to wait (on 429 response)
```

The emerging standard is the `RateLimit` header family (RFC 6585 and IETF draft):
```
RateLimit-Limit: 1000
RateLimit-Remaining: 743
RateLimit-Reset: 30
```

---

## Idempotency in API Design

### What Idempotency Means and Why It Matters

An operation is idempotent if executing it multiple times produces the same result as executing it once. In API design, idempotency matters for retry safety: if a network failure occurs after the server processes a request but before the client receives the response, the client does not know whether the request succeeded. Safe retry requires idempotency.

GET, PUT, and DELETE are naturally idempotent by the HTTP spec. POST is not — submitting a form twice creates two records.

### Idempotency Keys

The pattern for making non-idempotent operations (POST) safe to retry is the idempotency key. The client generates a unique key (UUID) and includes it in the request header:

```
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

The server:
1. Checks if it has seen this key before
2. If yes: return the stored response (do not re-execute)
3. If no: process the request, store the response keyed by the idempotency key, return the response

**Storage considerations**: Idempotency keys should expire (24 hours is common for payment operations). Store the full request hash along with the key — if the client retries with the same key but a different request body, return a 422 Unprocessable Entity, not the cached response.

**Stripe's implementation** is the reference model. Every POST request to Stripe's API accepts an `Idempotency-Key`. If you retry a charge creation with the same key, Stripe returns the original charge result. This makes payment retries safe from the client's perspective.

### Designing Idempotent APIs

Beyond idempotency keys, design choices that support idempotency:

**Use PUT for upserts** when the client knows the resource identifier. `PUT /users/{id}` either creates or updates the user. Retrying the same request is safe.

**Include version or ETag in mutations** to implement optimistic concurrency control. If two clients update the same resource, the second update fails with 409 Conflict, forcing the client to re-read and retry with awareness of the current state.

**Make side effects explicit**: If a POST creates a resource and sends a notification email, the idempotency store must prevent the email from being sent twice, not just the database write.

---

## Common API Design Interview Questions

### "How would you design the API for a ride-sharing app?"

**Framework**: Start with resources: riders, drivers, trips, locations. Model the core workflow as state transitions: a trip moves from `requested` → `driver_assigned` → `in_progress` → `completed` or `cancelled`. Use `PATCH /trips/{id}` with a `status` field for transitions, or explicit action endpoints `/trips/{id}/cancel` for clarity.

Real-time location: WebSocket connection from driver publishes location; server fans out to the rider's connection. REST endpoint `/trips/{id}/driver-location` for initial render.

Versioning: URL path (`/api/v1/`) with clear deprecation policy. Authentication: OAuth 2.0 with Authorization Code flow for user authentication; API keys for driver app authentication.

### "How do you handle breaking changes in a public API?"

The strong answer: avoid them by designing for extensibility upfront (optional fields, permissive enum handling, Postel's Law for inputs). When unavoidable, introduce a new version, run both versions in parallel for a minimum deprecation window, provide tooling to help consumers migrate, and use sunset headers to communicate the timeline.

If the change can be done in a backward-compatible way, do that instead: add a new field alongside the old one rather than renaming. Remove fields in a later version.

### "REST vs. GraphQL — which would you choose for a public API?"

REST for a public API. REST is universally understood, works with all HTTP clients without special libraries, caches naturally over HTTP, and is simpler to document and secure. The underfetching/overfetching problems that motivate GraphQL are manageable with well-designed REST resources and sparse fieldsets (`?fields=id,name,email`).

GraphQL for an internal BFF layer where you control client implementations and need maximum flexibility for multiple clients with divergent data needs.

---

## Practicing API Design Fluency

API design questions reward candidates who have made real mistakes in production — who have versioned an API wrong, debugged an N+1 query in a GraphQL schema, or dealt with a client that could not handle a breaking change. If you have not built and evolved a production API, simulated practice with detailed feedback is the fastest way to build the intuition.

**[Interview Simulator at app.codeswiftr.com](https://app.codeswiftr.com)** includes system design scenarios where API design decisions are specifically evaluated — including follow-up questions on versioning strategy, pagination choices, and authentication that mirror what senior and staff engineers probe in real interviews.

Build the vocabulary and the reasoning frameworks here, then walk into your next interview ready to defend every design decision.

**[Start Practicing API Design Questions Free](https://app.codeswiftr.com)**

---

*Related guides: [The Complete System Design Interview Guide](/blog/system-design-interview-guide) | [Backend Engineer Interview Guide](/blog/backend-engineer-interview-guide) | [Distributed Systems Interview Deep Dive](/blog/distributed-systems-interview-deep-dive)*
