---
title: "System Design: E-Commerce Platform — Building Amazon at Scale"
description: "How to design an e-commerce platform in system design interviews — product catalog, inventory management, order processing, checkout flow, recommendation engine, and scaling to 100M daily active users."
date: "2026-03-20"
category: "System Design"
---

# System Design: E-Commerce Platform — Building Amazon at Scale

E-commerce platform design tests a wide range of system design skills: product catalog search, inventory consistency, order processing workflows, payment integration, and recommendation systems. It's a common senior interview question because it exercises service decomposition, data modeling, consistency trade-offs, and scalability all in one problem.

## Requirements

- 100M daily active users; peak 500K concurrent sessions (holiday sale)
- Product catalog: 300M SKUs across millions of sellers
- Orders: 10M orders per day
- Inventory: Must prevent overselling (strong consistency for last unit)
- Search: Full-text product search with filters, facets, personalization
- Checkout: <2s page load; payment authorization <3s
- Recommendations: Real-time personalized product recommendations

## Service Architecture

E-commerce decomposes cleanly into services aligned with business domains:

- **Catalog Service**: Product metadata, images, pricing
- **Inventory Service**: Stock levels, reservations, warehouse allocation
- **Search Service**: Full-text search, faceted filtering, ranking
- **Cart Service**: Shopping cart state
- **Order Service**: Order lifecycle, fulfillment coordination
- **Payment Service**: Payment authorization and capture
- **User Service**: Authentication, profiles, address book
- **Notification Service**: Order confirmations, shipping updates
- **Recommendation Service**: Personalized product ranking

## Product Catalog

The catalog is read-heavy (reads vastly outnumber writes). Store in PostgreSQL (primary) with aggressive caching.

Product pages are cached at multiple layers:
1. CDN (CloudFront/Fastly) caches rendered HTML for anonymous users — cache hit rate >95%
2. Redis caches product data (prices, metadata) — TTL 5 minutes
3. Database serves cache misses

**Search**: Don't use your OLTP database for search. Elasticsearch or OpenSearch handles full-text search, faceted filtering (category, price range, brand), and custom ranking. Product data is denormalized into search documents including aggregated reviews, inventory status, and seller rating.

**Search ranking**: A combination of relevance score (BM25 text matching), engagement signals (click-through rate, conversion rate), inventory availability, and personalization. Offline ML trains a ranking model; online serving applies a linear combination of features.

**Price changes**: Prices change frequently (flash sales, seller updates). Elasticsearch documents are refreshed on a 1-5 minute schedule. For real-time accuracy on the product page, the rendered HTML includes a JavaScript fetch to the Pricing Service on load.

## Inventory Management

Inventory is the hardest consistency problem in e-commerce. Overselling creates customer anger and operational chaos.

**Two-phase reservation**: When a customer adds to cart, the system does a "soft reserve" — it records interest but doesn't guarantee the item. When they proceed to checkout, a "hard reserve" is placed. Hard reserves lock inventory for a time window (e.g., 15 minutes) while the customer completes checkout.

**Inventory data model** (PostgreSQL):
```sql
inventory (sku_id, warehouse_id, quantity_on_hand, quantity_reserved, quantity_available)
-- quantity_available = quantity_on_hand - quantity_reserved
```

Reservation uses a transaction with a row lock:
```sql
BEGIN;
SELECT quantity_available FROM inventory WHERE sku_id = X FOR UPDATE;
-- If >= requested quantity:
UPDATE inventory SET quantity_reserved = quantity_reserved + N WHERE sku_id = X;
COMMIT;
```

**Distributed inventory**: For high-volume SKUs, partitioning inventory across shards reduces contention. Split 1,000 units across 10 shards of 100 units each. Reservations go to random shards. Rebalancing runs periodically.

## Order Processing Workflow

Order processing is a multi-step saga with multiple services and potential failures:

1. **Payment authorization** → Payment Service (Stripe/Adyen)
2. **Inventory commit** → Inventory Service (convert reservation to sale)
3. **Order created** → Order Service (write to database)
4. **Fulfillment triggered** → Warehouse Management System
5. **Confirmation sent** → Notification Service

Use the **Saga pattern** with compensating transactions. If Step 3 fails (database down), Step 2 must be compensated (release the inventory reservation). If Step 4 fails, the order is created but flagged for retry.

**Idempotency**: Every step must be idempotent. Payment authorization includes a unique order ID — if retried, the payment provider returns the existing authorization rather than charging twice.

## Checkout Performance

Checkout is where revenue is made or lost. Every 100ms of latency reduces conversion ~1%.

**Optimize the critical path**: The checkout page needs cart contents, prices, shipping options, and user address. Pre-compute as much as possible:
- Cart service maintains computed totals (updated on each item change)
- Shipping options are calculated lazily on checkout page open via background fetch
- Address is pre-loaded from User Service

**Payment flow**: Redirect to payment provider or use embedded payment form (Stripe Elements). Payment authorization is synchronous — the user waits for a response. p95 target: <1.5s.

## Recommendation Engine

Product recommendations drive 35% of Amazon's revenue. The standard architecture:

**Offline training**: Collaborative filtering (users who bought X also bought Y), content-based filtering (similar products by attributes), and session-based models (what's in your current cart?). Trained daily on behavioral data.

**Online serving**: Recommendations served from Redis (precomputed per user). For new users (cold start), fall back to popularity-based recommendations for the category.

**A/B testing**: Recommendation algorithms run in parallel experiment groups. Conversion rate is the primary metric. A 1% improvement in recommendation click-through on 100M daily users is significant revenue.

## Failure Handling

- **Inventory service down at checkout**: Return "temporarily unavailable" — never allow checkout without inventory confirmation
- **Payment service timeout**: Retry with the same idempotency key; show user a wait state rather than duplicate-charging
- **Search service down**: Fall back to database-backed category browsing; degrade gracefully
- **Database overload during flash sale**: Rate limit add-to-cart; use a virtual queue ("You're #4,521 in line") rather than showing out-of-stock immediately

E-commerce design rewards engineers who can reason about consistency boundaries — knowing when eventual consistency is acceptable (search freshness) versus when strong consistency is required (inventory, payment). That distinction is what interviewers are probing.
