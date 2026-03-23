---
title: "System Design: Ride-Sharing Platform (Uber/Lyft Architecture)"
description: "How to design a ride-sharing platform in system design interviews — location matching, real-time driver tracking, surge pricing, dispatch algorithm, and payment processing."
date: "2026-03-20"
category: "System Design"
---

# System Design: Ride-Sharing Platform (Uber/Lyft Architecture)

Designing a ride-sharing platform is a senior-level system design question that tests your grasp of real-time systems, geospatial data structures, state machines, and distributed coordination. Uber and Lyft operate at a scale that makes every component interesting — here's how to walk through it confidently.

## Requirements and Scale Estimation

Start by clarifying scope. A typical prompt covers: rider requests a ride, nearby drivers are matched, driver accepts, trip completes, payment is charged. At global Uber scale: 5 million trips per day, ~58 trips per second. Assume 5 million active drivers worldwide at peak.

The unique technical challenges are: real-time location tracking for millions of drivers, low-latency geospatial matching, and consistent trip state across distributed services.

## Geospatial Matching: The Core Technical Challenge

This is where most interviewers spend the most time. You need to efficiently find drivers within N kilometers of a rider's location. Three approaches are commonly discussed:

**QuadTree**: Recursively divides a 2D space into four quadrants. Efficient for sparse distributions. Searching for drivers near a point means traversing the tree to the relevant leaf node(s). Works well when driver density varies widely by region. The challenge: the tree must be updated in near-real-time as drivers move.

**Google S2 Library**: Decomposes the Earth's surface into a hierarchy of cells using a space-filling Hilbert curve. Each cell has a 64-bit ID. Finding nearby drivers becomes a range query on cell IDs, which maps naturally to sorted indexes. Used by Google Maps and reportedly by early Uber.

**Uber H3**: Uber's open-source hexagonal hierarchical geospatial indexing system. Hexagons tile uniformly (unlike squares), making distance calculations more consistent across directions. H3 is the modern preferred answer — mention it to signal current industry knowledge.

For the interview, QuadTree is safe and well-understood. Mentioning H3 as a production-grade improvement shows depth.

## Real-Time Location Updates

Drivers send location updates every 4 seconds (Uber's reported interval). At 5 million active drivers, that's 1.25 million updates/second. This must be handled asynchronously.

Architecture: Drivers maintain a persistent **WebSocket connection** to a location service. Location updates are published to a **Kafka topic** partitioned by city or geographic region. A location consumer updates a **Redis geo-index** (`GEOADD` / `GEORADIUS` commands), which serves the matching service with sub-millisecond lookup.

Redis's native geo commands make it a natural fit here: `GEOADD drivers:cityId lon lat driverId` and `GEORADIUS drivers:cityId lon lat 5 km COUNT 10 ASC` returns the 10 nearest available drivers in one command.

## Driver-Rider Matching Algorithm

When a rider requests a ride, the matching service:
1. Queries Redis for available drivers within a radius (start at 2km, expand if none found)
2. Filters by driver type (UberX, UberXL, etc.)
3. Ranks candidates by ETA (not just distance — a driver 1.5km away but stuck in traffic may rank below one 2km away on a clear road)
4. Dispatches a request to the top candidate
5. If no acceptance within 10 seconds, moves to the next candidate

ETA calculation requires a routing engine (Google Maps Directions API or internal OSRM instance). Caching common route ETAs reduces API calls significantly.

## Trip State Machine

Trips progress through well-defined states: `REQUESTED → DRIVER_ASSIGNED → DRIVER_EN_ROUTE → DRIVER_ARRIVED → IN_PROGRESS → COMPLETED` (with `CANCELLED` possible at several transitions). Store this state in a relational database (PostgreSQL). State transitions must be atomic — use database transactions to prevent race conditions where two drivers accept the same ride simultaneously. Optimistic locking or a `SELECT FOR UPDATE` on the trip row handles this cleanly.

## Surge Pricing System

Surge pricing adjusts fares when demand exceeds supply in a given area. The system monitors request rate vs. available drivers per H3 hex cell every 60 seconds. When the ratio exceeds a threshold (e.g., 1.5 requests per available driver), surge multiplier increases. The calculation runs as a batch job, writing multipliers to a low-latency store (Redis) that the pricing service reads at trip-request time.

Surge decisions are coarse-grained (city-block or hex level) — precise real-time calculation per meter is unnecessary and computationally wasteful.

## Payment Processing

Payment is asynchronous relative to the trip. When a trip completes:
1. Fare is calculated (distance × rate × surge multiplier)
2. A payment event is published to Kafka
3. A payment consumer calls the payment processor (Stripe, Braintree)
4. Receipt is emailed/pushed to rider
5. Driver earnings are updated

Never process payment synchronously during the trip-end flow — payment failures shouldn't block the rider from exiting the app. Idempotency keys on payment API calls prevent double-charging on retries.

## Notification System

Riders and drivers receive push notifications at each state transition. A notification service subscribes to trip state change events from Kafka and fans out to APNS (iOS) and FCM (Android). At scale, a dedicated notification microservice with its own queue prevents notification backpressure from affecting core trip operations.

## Scaling: Regional vs. Global

Ride-sharing is inherently regional — a driver in Chicago is irrelevant to a rider in São Paulo. Partition your services by city or region. Each region has its own:
- Location service cluster
- Matching service instance
- PostgreSQL primary for trip data

A global control plane handles cross-region operations: account management, payment aggregation, analytics. This architecture minimizes cross-region latency and allows regional failover.

## Common Follow-Up Questions

**"How do you handle the case where a driver's app crashes during a trip?"** — Trip state is persisted in the database. The driver app reconnects and re-fetches current trip state. The rider app polls the trip status endpoint. No data is lost.

**"How do you prevent a driver from accepting two rides simultaneously?"** — Database-level constraint: a trip assignment sets `driver_id` and `status=ASSIGNED` atomically. Any subsequent assignment for the same driver fails the uniqueness check.

**"What's your database choice and why?"** — PostgreSQL for trips (ACID guarantees for state transitions), Redis for real-time driver locations (speed), Cassandra or BigQuery for historical trip analytics (scale).

A strong candidate covers geospatial matching, the state machine, and at least two of the supporting subsystems in 45 minutes. Uber's engineering blog is excellent supplementary reading for candidates who want to go deeper.
