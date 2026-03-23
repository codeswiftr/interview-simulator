---
title: "GraphQL Federation Architecture Guide"
description: "GraphQL Federation for microservices—Apollo Federation 2, subgraph design, entity references, schema composition, query planning, and the architectural patterns for building a federated supergraph at scale."
date: "2026-03-21"
category: "Language Deep Dives"
---

# GraphQL Federation Architecture Guide

GraphQL Federation solves a fundamental problem: how do you provide a single unified GraphQL API when your backend is composed of dozens of microservices? Apollo Federation 2 is the dominant solution, used by organizations like Netflix, Expedia, and Wayfair to compose hundreds of services into a single supergraph.

## Core Concepts

**Supergraph**: The unified schema composed from all subgraphs, served by the router.

**Subgraph**: An individual service that owns a subset of the schema and implements a partial graph.

**Entity**: A type that can be extended across subgraphs, identified by a `@key` directive.

**Router**: Apollo Router (Rust, high-performance) or Apollo Gateway (Node.js). Receives client queries, generates a query plan, and federates execution across subgraphs.

## Subgraph Design

Each service defines its own schema and owns its entities:

```graphql
# Users subgraph — owns the User entity
type User @key(fields: "id") {
  id: ID!
  username: String!
  email: String!
  createdAt: String!
}

type Query {
  user(id: ID!): User
  users(limit: Int = 20, offset: Int = 0): [User!]!
  me: User
}

type Mutation {
  createUser(input: CreateUserInput!): CreateUserResult!
  updateUser(id: ID!, input: UpdateUserInput!): User!
}
```

```graphql
# Orders subgraph — references User entity, owns Order
extend type User @key(fields: "id") {
  id: ID! @external
  orders(status: OrderStatus): [Order!]!  # Extends User with orders field
}

type Order @key(fields: "id") {
  id: ID!
  userId: ID!
  user: User!  # References the User entity
  status: OrderStatus!
  total: Float!
  items: [OrderItem!]!
  createdAt: String!
}

enum OrderStatus {
  PENDING
  PROCESSING
  SHIPPED
  DELIVERED
  CANCELLED
}

type Query {
  order(id: ID!): Order
  orders(userId: ID, status: OrderStatus): [Order!]!
}
```

## Implementing Reference Resolvers

Subgraphs must implement `__resolveReference` for each entity they own, enabling the router to fetch entity data from subgraphs by key:

```typescript
// Users subgraph resolver
const resolvers = {
  User: {
    // Called when another subgraph requests a User by id
    __resolveReference: async (ref: { id: string }, context: Context) => {
      return context.usersLoader.load(ref.id);
    },
  },
  Query: {
    user: (_, { id }, ctx) => ctx.db.users.findById(id),
    users: (_, { limit, offset }, ctx) => ctx.db.users.findAll({ limit, offset }),
    me: (_, __, ctx) => ctx.currentUser,
  },
};

// Orders subgraph resolver
const resolvers = {
  User: {
    // Extends User with orders — user.id comes from the Users subgraph
    orders: (user: { id: string }, { status }, ctx) =>
      ctx.db.orders.findByUserId(user.id, status),
  },
  Order: {
    __resolveReference: (ref, ctx) => ctx.db.orders.findById(ref.id),
    user: (order) => ({ __typename: 'User', id: order.userId }),
  },
};
```

## DataLoader for N+1 Prevention

Federation queries can cause N+1 problems when resolving entity references. DataLoader batches these:

```typescript
import DataLoader from 'dataloader';

export function createUserLoader(db: Database) {
  return new DataLoader<string, User>(async (userIds) => {
    const users = await db.users.findByIds(userIds as string[]);
    const userMap = new Map(users.map(u => [u.id, u]));
    // DataLoader requires results in the same order as keys
    return userIds.map(id => userMap.get(id) ?? new Error(`User ${id} not found`));
  });
}

// In context factory
export function createContext(req: Request): Context {
  return {
    db,
    currentUser: req.user,
    usersLoader: createUserLoader(db),  // Fresh loader per request (scoped cache)
    ordersLoader: createOrderLoader(db),
  };
}
```

## Apollo Router Configuration

```yaml
# router.yaml
supergraph:
  path: ./supergraph.graphql

cors:
  origins:
    - https://app.example.com

authentication:
  router:
    jwt:
      jwks:
        - url: https://auth.example.com/.well-known/jwks.json

authorization:
  require_authentication: false  # Subgraphs handle auth

traffic_shaping:
  router:
    global_rate_limit:
      capacity: 1000
      interval: 1s
  all:
    timeout: 30s

telemetry:
  tracing:
    propagation:
      trace_context: true
    exporters:
      otlp:
        endpoint: http://jaeger:4317
```

## Schema Composition and CI

Use `rover` CLI to compose and validate schemas:

```bash
# Introspect subgraph schemas
rover subgraph introspect http://users-service:4001/graphql > users.graphql
rover subgraph introspect http://orders-service:4002/graphql > orders.graphql

# Compose locally for validation
rover supergraph compose --config supergraph.yaml > supergraph.graphql

# Publish to Apollo Studio (managed federation)
rover subgraph publish my-graph@production \
  --name users \
  --schema users.graphql \
  --routing-url http://users-service/graphql
```

```yaml
# supergraph.yaml
federation_version: =2.6.0
subgraphs:
  users:
    routing_url: http://users-service:4001/graphql
    schema:
      file: ./users.graphql
  orders:
    routing_url: http://orders-service:4002/graphql
    schema:
      file: ./orders.graphql
```

## Query Planning

The router generates an execution plan for each query—understanding this helps design efficient schemas:

```graphql
# Client query
query GetUserWithOrders($userId: ID!) {
  user(id: $userId) {
    username
    email
    orders {
      id
      total
      status
    }
  }
}
```

The router's query plan for this:
1. Fetch `user(id)` from Users subgraph (username, email)
2. Fetch `orders` from Orders subgraph using `User @key(id)` reference

Schemas that require many entity reference fetches generate more complex query plans with more network round trips. Design entities to minimize cross-subgraph data dependencies on hot paths.

## Interview Tips

GraphQL Federation interview questions:

1. **Entity references** — how `@key`, `__resolveReference`, and `@external` enable cross-subgraph types
2. **Query planning** — how the router fetches from multiple subgraphs; why deep entity chains cause performance problems
3. **Schema ownership** — who owns what type, why extending types across too many services creates coupling
4. **DataLoader** — why it's essential in federation; N+1 amplification is worse than in monolith GraphQL
5. **Managed vs unmanaged federation** — Apollo Studio schema registry vs local composition; schema change validation

The key federation insight: federation solves the integration problem but doesn't eliminate the distributed systems complexity. You still need to handle partial failures, query timeouts, and the operational overhead of running multiple services. For smaller teams, a well-designed monolithic GraphQL schema with datasource separation often delivers better developer experience without the operational cost.
