---
title: "GraphQL Engineering Interview Guide"
description: "API design trade-offs, schema design, performance problems, and when GraphQL is the wrong choice — everything you need for GraphQL in technical interviews."
date: "2026-03-19"
category: "Backend Engineering"
---

# GraphQL Engineering Interview Guide

GraphQL appears in technical interviews at companies like GitHub, Shopify, Twitter, Airbnb, and Meta — where it originated. The questions span a wide range: API design trade-offs, schema design, performance problems, and when GraphQL is the wrong choice. This guide covers what those interviews actually test.

## Why Companies Interview on GraphQL

GraphQL adoption has grown enough that senior frontend and full-stack roles at many companies now expect familiarity with it. The interview questions are rarely about syntax — they are about trade-offs. Interviewers want to know whether you understand *why* GraphQL solves certain problems and *when* REST or gRPC is the better choice.

The most common interview contexts:

- **System design**: "Design the API layer for a social feed" — often has a GraphQL vs REST comparison embedded in it
- **Frontend performance**: "Why is our GraphQL app making too many round trips?" — n+1 problems, caching, persisted queries
- **Schema design**: "How would you model a permissions system in GraphQL?" — interfaces, unions, type design
- **Backend architecture**: "How do you handle authorization in GraphQL resolvers?" — field-level auth, DataLoader, resolver complexity

## Core Concepts That Appear in Interviews

### The N+1 Problem

This is the most common GraphQL performance question. If you ask for a list of posts and each post's author:

```graphql
query {
  posts {
    title
    author {
      name
    }
  }
}
```

A naive implementation fires one query for posts, then one query per post for the author — 1 + N queries for N posts. The solution is DataLoader: batch all author lookups into a single query, then cache within the request.

```javascript
const authorLoader = new DataLoader(async (authorIds) => {
  const authors = await db.query(
    'SELECT * FROM users WHERE id = ANY($1)', [authorIds]
  );
  // Must return results in same order as keys
  return authorIds.map(id => authors.find(a => a.id === id));
});
```

Interviewers will ask you to identify this pattern, explain why it happens, and describe the fix. DataLoader is the expected answer. Strong candidates also explain that DataLoader batches *within a single tick* of the event loop, so multiple resolvers requesting the same resource naturally batch without explicit coordination.

### Schema Design Trade-offs

Interviews often present a domain and ask how you'd model it. Common patterns to know:

**Interfaces and unions**: When multiple types share fields (interface), vs when they are truly different shapes that can appear in the same position (union).

```graphql
# Interface: shared fields, different implementations
interface Node {
  id: ID!
}

type User implements Node {
  id: ID!
  email: String!
}

# Union: completely different types in same position
union SearchResult = User | Post | Comment
```

**Connections pattern** (Relay spec): Pagination in GraphQL is almost always implemented with the Cursor Connection spec. Interviewers at companies using Relay (Meta, GitHub) will expect you to know this pattern:

```graphql
type PostConnection {
  edges: [PostEdge!]!
  pageInfo: PageInfo!
}

type PostEdge {
  node: Post!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  endCursor: String
}
```

Why cursors over offset pagination? Cursors are stable when the underlying data changes — an offset-based page 2 shifts if a new item is inserted before page 1.

### Authorization in GraphQL

REST makes authorization easy: middleware on a route. GraphQL makes it harder because every field can theoretically return different data for different users.

Three approaches, and you should be able to discuss the trade-offs:

1. **Resolver-level authorization**: Each resolver checks permissions. Simple but repetitive; easy to miss a field.
2. **Directive-based authorization**: Custom directives (`@requiresAuth`, `@hasRole("ADMIN")`) applied to schema fields. Visible in the schema, but adds complexity.
3. **Schema stitching / field masking**: Remove fields from the schema entirely for unauthorized users. Cleanest but requires schema manipulation.

The right answer for interviews: "I'd use a middleware approach where a permission check function is called in every resolver, combined with a library like graphql-shield for rule composition, so authorization logic is centralized and testable."

## Performance Questions

### Query Complexity and Depth Limits

GraphQL allows clients to write arbitrarily complex queries. Without limits, a malicious or careless client can write a deeply nested query that causes exponential resolver calls:

```graphql
# This could cause hundreds of DB calls
query {
  user {
    friends {
      friends {
        friends {
          name
        }
      }
    }
  }
}
```

Production GraphQL APIs need query complexity analysis (assign a cost to each field, reject queries above a threshold) and depth limiting. Libraries like `graphql-depth-limit` and `graphql-cost-analysis` handle this. Interviewers at companies running public GraphQL APIs (GitHub's API, Shopify's Storefront API) will ask how you'd prevent abuse.

### Persisted Queries

Instead of sending the full query string with every request, clients register queries in advance and send only a hash. This reduces payload size, enables CDN caching of GET requests, and prevents clients from running arbitrary queries.

GitHub's public GraphQL API uses persisted queries. If you're interviewing there, know this pattern.

### Caching Challenges

GraphQL is harder to cache than REST because all requests go to the same endpoint (`POST /graphql`). Strategies:

- **HTTP caching**: Use persisted queries with GET requests — then CDN caching works normally
- **Response caching**: Cache at the field level with cache hints (Apollo Cache Control)
- **Client-side**: Apollo Client and Relay both normalize responses and cache by `id` + `__typename`

## GraphQL vs REST: The Interview Question

Many system design interviews contain an implicit GraphQL vs REST decision. The expected framework:

**Use GraphQL when:**
- Multiple clients (web, mobile) need different data shapes from the same API
- Reducing round trips is critical (mobile apps on slow connections)
- Rapid iteration on frontend without backend changes

**Use REST when:**
- Simple CRUD with well-defined resources
- HTTP caching is important
- Team is unfamiliar with GraphQL tooling overhead
- File uploads are common (GraphQL multipart spec is awkward)

**Use gRPC when:**
- Service-to-service communication (not client-facing)
- High-throughput, low-latency internal APIs
- Strongly-typed contract is more important than flexibility

Interviewers are looking for nuance. "GraphQL is always better" is a wrong answer. "It depends on client diversity and caching requirements" is the right starting point.

## What to Study

- **GraphQL specification**: Understanding the spec (especially execution model and type system) separates strong candidates from those who only know the API surface
- **Apollo Server / Yoga**: Most production Node.js GraphQL servers; know how to add middleware, plugins, error handling
- **DataLoader**: Understand the batching mechanism, not just the API
- **Relay**: Even if you don't use it, understanding why Relay conventions exist (the Cursor Connection spec, Global Node IDs) reveals depth of knowledge
- **GitHub GraphQL Explorer**: Hands-on exploration of a production GraphQL API at scale — invaluable for understanding real-world schema design decisions
