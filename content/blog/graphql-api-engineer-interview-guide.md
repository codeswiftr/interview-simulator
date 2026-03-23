---
title: "GraphQL API Engineer Interview Guide: Schema Design & Performance"
description: "Master GraphQL interviews — schema design, resolvers, N+1 problem, DataLoader, subscriptions, federation, and Apollo vs Relay."
date: "2026-03-19"
category: "Technical Skills Guides"
---

# GraphQL API Engineer Interview Guide: Schema Design & Performance

GraphQL has become the API layer of choice for companies building complex data-driven products — Shopify, GitHub, Twitter, Netflix, and thousands of startups rely on it. GraphQL engineers need deep understanding of schema design, resolver architecture, performance optimization, and federation. This guide covers what technical interviewers focus on.

## Schema Design Fundamentals

Schema design is the first thing interviewers probe. A poorly designed schema becomes a maintenance nightmare and performance bottleneck. Demonstrate these principles:

**Object types vs. interfaces vs. unions**: Know when to use each. Interfaces define a common field contract (e.g., `Node` with an `id` field), unions represent disjoint types (search results returning `User | Post | Product`). Interviewers will present a domain model and ask you to design a schema — think about query ergonomics, not just data modeling.

**Connection pattern (Relay cursor-based pagination)**: The de facto standard for paginated lists. `edges { node { ... } cursor }` + `pageInfo { hasNextPage endCursor }` beats offset pagination for large datasets because it's stable under concurrent mutations. Know why cursor-based pagination is superior and how to implement it efficiently with database keyset pagination.

**Input types**: Mutations should always take input objects (not individual scalar arguments) for forward compatibility. Understanding nullability semantics in mutations — a `null` explicitly set vs. field absent (`undefined`) — is a nuanced topic that strong candidates address.

**Schema-first vs. code-first**: Schema SDL files (schema-first) vs. programmatic schema construction with type-safe resolvers (code-first with pothos/nexus/strawberry). Understand the tradeoffs in team collaboration and refactoring.

## The N+1 Problem and DataLoader

The N+1 problem is the most common performance interview topic in GraphQL. Without mitigation, fetching a list of 100 posts with their authors triggers 101 database queries (1 for posts, 100 for authors). Interviewers expect you to explain, diagnose, and solve this:

**DataLoader**: Facebook's solution — batch and cache per-request. `DataLoader` collects all keys requested in a single event loop tick and issues a single batched query. The implementation pattern (`new DataLoader(async (keys) => ...)`) and the requirement for result ordering to match key ordering are frequent interview questions.

**SQL JOIN strategies**: Sometimes joining in the resolver is cleaner than DataLoader. Understanding when to batch via DataLoader vs. when to fetch with a JOIN or `IN` clause depends on query patterns and data cardinality.

**Persisted queries and APQ**: For known query patterns, persisted queries reduce bandwidth and allow server-side caching. Apollo's Automatic Persisted Queries use SHA-256 hashing. Know how this interacts with CDN caching.

Interview question: "You're seeing 500ms P95 latencies on a products query that returns 50 items with their reviews and reviewers. Walk me through your debugging approach." Demonstrate using Apollo Studio traces, identifying resolver bottlenecks, implementing DataLoader, and potentially introducing query complexity limits.

## Subscriptions and Real-Time GraphQL

Real-time data adds significant complexity to GraphQL deployments:

**WebSocket transport**: `graphql-ws` (current standard) vs. `subscriptions-transport-ws` (deprecated). Know the protocol handshake and why the newer spec is preferred (connection management, error handling, multiplexing).

**Server-Sent Events (SSE)**: An alternative to WebSockets for push-only scenarios. Simpler infrastructure (HTTP, load-balancer friendly), no full-duplex needed. Newer GraphQL multipart response spec enables SSE-based subscriptions.

**Pub/Sub backends**: Redis Pub/Sub, AWS SNS/SQS, or dedicated message brokers for distributing subscription events across multiple API server instances. Understand fan-out patterns and the thundering herd problem when many clients subscribe to the same event.

**@defer and @stream**: Incremental delivery directives that allow partial responses before the full query resolves. Critical for improving perceived performance on queries with expensive resolvers.

## Federation: Distributed Schema Architecture

Apollo Federation is now standard at companies with multiple teams owning different graph domains. Interview topics:

**Subgraph design**: Entity types with `@key` directives, reference resolvers, cross-subgraph relationships. Understanding the `@external` and `@requires` directives for federated fields.

**Router vs. Gateway**: Apollo Router (Rust) replaced the JavaScript Apollo Gateway for performance. Know the architectural role of the router in query planning and subgraph composition.

**Schema composition rules**: What makes a federated schema valid? Type compatibility, value type sharing, entity ownership. Being able to reason about composition errors signals production experience.

## Practical Interview Preparation

1. Build a complete GraphQL API from scratch: users, posts, comments with pagination, mutations, and DataLoader
2. Instrument a query with Apollo Studio or graphql-playground and analyze the trace
3. Implement a custom scalar (e.g., `DateTime`, `JSON`, `URL`) with proper serialization/parsing
4. Write a query complexity plugin and explain how it prevents abuse
5. Study GitHub's GraphQL API — it's the gold standard for public GraphQL API design

GraphQL engineering roles span API platform teams, e-commerce backends, content management systems, and developer platform companies. Strong candidates combine schema design intuition with performance engineering skills and can reason clearly about the tradeoffs between GraphQL and REST for different access patterns.
