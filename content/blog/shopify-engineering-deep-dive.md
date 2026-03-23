# Shopify Engineering Deep Dive: E-Commerce Infrastructure for 10% of US E-Commerce

Shopify powers over 10% of US e-commerce by GMV — a number that becomes concrete when you realize that on Black Friday 2023, the platform processed over $4.1 billion in sales in a single day. Understanding how Shopify's engineering organization built the infrastructure to support that scale reveals patterns relevant to every distributed systems interview you'll face.

## Black Friday/Cyber Monday: The Annual Stress Test

Every year, Shopify engineers treat BFCM as a production load test with real money on the line. The challenge isn't just raw throughput — it's handling 10x to 40x normal traffic with unpredictable spikes, across hundreds of thousands of merchant storefronts simultaneously.

Shopify's preparation strategy centers on what they call "production load testing." Rather than relying solely on synthetic benchmarks, they run controlled flash sales and promotions in the weeks before BFCM, intentionally pushing segments of the platform to failure to observe real degradation patterns. This is a critical interview insight: at scale, you discover failure modes you couldn't predict in staging.

Their architecture evolved toward what they call "pods" — isolated, independently-scalable units of the platform. During BFCM, traffic is deliberately uneven across pods, which lets them scale individual pods under load without impacting others. This is the same principle behind AWS Availability Zones and horizontal pod autoscaling in Kubernetes, and it's a pattern you should be ready to discuss in depth.

A less-discussed element of their BFCM story is database strategy. Shopify historically ran on MySQL with Vitess for horizontal sharding. During peak periods, read replicas absorb the query load that would otherwise saturate primary instances. Knowing which reads can tolerate replication lag — product catalog, prices — versus which cannot — inventory counts, cart state — is a judgment call that shapes the entire read/write architecture.

## Flash Sales: Atomic Inventory Reservation Under Concurrency

Flash sales are the adversarial case for e-commerce infrastructure. A product drops with 1,000 units; 50,000 users try to buy simultaneously. Without careful design, you oversell, undersell (by being too conservative), or — worst — create a thundering herd that takes down your checkout service.

Shopify's approach to inventory reservation leans on Redis for the hot path, with a database as the source of truth. The core insight is that inventory reservation is fundamentally a decrement-with-floor operation: subtract one if and only if the current value is greater than zero. This is a classic atomic operation that relational databases handle with row-level locking, but at flash-sale concurrency levels, lock contention becomes the bottleneck.

Redis Lua scripts solve this by executing arbitrary logic atomically on the Redis server — no round trips, no race conditions between read and decrement:

```lua
-- atomic_reserve.lua
-- KEYS[1]: inventory key, e.g., "inventory:product:42"
-- ARGV[1]: quantity to reserve
-- Returns: remaining inventory after reservation, or -1 if insufficient

local current = tonumber(redis.call('GET', KEYS[1]))

if current == nil then
    return redis.error_reply("inventory key not found")
end

local requested = tonumber(ARGV[1])

if current < requested then
    return -1  -- reservation failed: insufficient stock
end

local remaining = current - requested
redis.call('SET', KEYS[1], remaining)

-- Also write to a reservation log for reconciliation
redis.call('RPUSH', 'reservation_log', KEYS[1] .. ':' .. requested .. ':' .. redis.call('TIME')[1])

return remaining
```

This script runs atomically because Redis is single-threaded for command execution. Even with 50,000 concurrent requests, each `EVALSHA` call queues behind the last. The practical throughput of this pattern is roughly 100,000 operations per second on a single Redis instance — sufficient for most flash sales.

The important interview follow-up: Redis is not your source of truth. You need a reconciliation loop that periodically syncs the Redis counter back to your database, and you need a strategy for Redis failure (circuit breaker to fall back to database-level locking? serve a sold-out page proactively?).

## GraphQL API Architecture: Storefront vs. Admin

Shopify runs two major public GraphQL APIs with very different design constraints. The Storefront API is consumer-facing — it's called from storefronts, mobile apps, and third-party clients. It's read-heavy, publicly accessible, and must be cacheable. The Admin API is merchant-facing — it's called from backend integrations, has write access to orders and inventory, and runs behind OAuth.

The schema design reflects these constraints. Storefront queries are designed around connection-based pagination (the Relay spec) so that clients receive stable cursor-based pages rather than offset-based ones, which break under concurrent inserts. Admin mutations use input objects extensively rather than flat argument lists, which makes schema evolution safer — adding a field to an input object is backward-compatible; adding a top-level argument is not.

From a multi-tenant SaaS perspective, Shopify's most interesting GraphQL challenge is per-tenant rate limiting. Each merchant's API key has a leaky bucket rate limit, enforced at the API gateway layer before requests reach the application. GraphQL complicates this because a single request can represent vastly different amounts of work depending on query depth and field selection. Shopify introduced a "cost" system where each field has an estimated compute cost, and requests are throttled against a cost budget rather than a raw request count.

## Kubernetes Migration and What It Taught Them

Shopify migrated from bare metal to Kubernetes over several years, and their public post-mortems are instructive. The primary motivation was reducing the time from "we need more capacity" to "capacity is live" — on bare metal, that cycle was measured in weeks; on Kubernetes, it's minutes.

The harder challenge was stateful services. MySQL and Redis don't behave like stateless web servers; pod restarts have real consequences for durability and replication topology. Shopify's approach was to run stateful data stores outside Kubernetes on dedicated hardware, using Kubernetes only for stateless application pods. This is a common pattern called the "pets vs. cattle" split, and it's worth knowing the tradeoffs in depth for infrastructure interviews.

## Interview Implications

When Shopify appears in a system design interview, the examiner is often probing your intuition about three things. First, multi-tenancy: how do you isolate one merchant's traffic spike from another's? The answer involves sharding, rate limiting, and bulkhead patterns. Second, consistency under concurrency: how do you prevent overselling without serializing all checkout traffic? The answer is optimistic locking, atomic operations, and reservation expiry. Third, API design for external developers: how do you version and evolve a public API without breaking existing integrations? The answer is GraphQL schema evolution rules, versioned REST endpoints, and deprecation policies with long sunset windows.

The BFCM story is ultimately a story about building systems that fail gracefully under load rather than systems that never fail — and knowing the difference is what separates senior engineers from the rest.
