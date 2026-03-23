---
title: "System Design: Ride-Sharing Platform — Uber/Lyft Architecture Deep Dive"
description: "Design a ride-sharing platform for interviews — location tracking, driver matching, surge pricing, trip lifecycle, and the distributed systems challenges at scale."
date: "2026-03-20"
category: "System Design"
---

# System Design: Ride-Sharing Platform — Uber/Lyft Architecture Deep Dive

The ride-sharing system design question tests your ability to handle real-time location data, build matching algorithms, design state machines for trip lifecycle, and reason about global scale. It's a favorite at Uber, Lyft, DoorDash, and any company with real-time logistics. Here's how to approach it.

## Scoping the Problem

Start by clarifying requirements. Minimum viable design:
- Riders can request a ride from location A to location B
- Available drivers receive the request and can accept
- Matched driver and rider can see each other's location
- Trip completes; payment is processed
- At scale: 10 million daily trips, 1 million active drivers

Exclude for initial design: multiple vehicle types, pool rides, scheduled rides, driver background checks.

## High-Level Architecture

Five core services:

**Location Service:** Ingests driver location updates (GPS pings every 4-5 seconds from driver app), stores current position, enables proximity queries ("find drivers within X km of rider").

**Matching Service:** Given a ride request, queries the Location Service for nearby available drivers, applies matching logic (distance, driver rating, ETA), sends the request to the best candidate(s).

**Trip Service:** Manages the trip state machine (requested → driver_assigned → en_route → arrived → in_progress → completed). Stores trip history.

**Notification Service:** Pushes real-time updates to rider (driver en route, driver arrived) and driver (new request, trip updates) via WebSocket or mobile push.

**Payment Service:** Calculates fare, processes payment at trip completion. Integrates with Stripe or internal payment processor.

## Location Storage: The Core Problem

At 1 million active drivers pinging every 4 seconds, that's 250K writes/second. You need:
1. **Fast writes** for location updates
2. **Fast geospatial reads** for "find nearby drivers"

Standard approach: Redis with geospatial support. `GEOADD drivers {lon} {lat} {driver_id}` for updates. `GEORADIUS drivers {lon} {lat} 5 km` for proximity search. Redis handles hundreds of thousands of operations per second.

Geohashing is a common alternative: encode latitude/longitude into a hash string. Nearby locations share common prefixes. For a given rider location, compute the geohash, then query drivers with matching prefix. Requires checking neighboring geohash cells to avoid boundary effects.

For persistent storage, write location updates to a time-series database (InfluxDB, TimescaleDB) for historical queries and analytics.

## Matching Algorithm

When a ride is requested:
1. Find available drivers within 5km (configurable)
2. Filter by: vehicle type, rating threshold, not currently on a trip
3. Rank by: ETA to pickup, driver rating
4. Offer to top N drivers simultaneously (first accept wins) or sequentially (top candidate gets 15 seconds to respond, then next)

The simultaneous vs. sequential decision is a tradeoff: simultaneous reduces wait time but causes "wasted" offers to drivers who will decline. Sequential is more efficient but slower. Most companies use a hybrid: offer to top candidate first, then expand if no response within threshold.

**Preventing double-booking:** Use a distributed lock (Redis SET NX with TTL) on the driver ID when sending an offer. The first request to acquire the lock "owns" the driver; concurrent matching requests for the same driver will fail and move to the next candidate.

## Trip State Machine

The trip lifecycle is a state machine. Transitions must be:
- **Atomic:** A trip can't be in two states simultaneously
- **Durable:** State persists across service restarts
- **Consistent:** Driver and rider apps agree on the current state

Store the current state in a relational database. Use database transactions for state transitions. Publish state change events to a message queue (Kafka) for other services to react (notification service sends push when driver is assigned, analytics service records trip metrics).

## Real-Time Communication

Riders and drivers need sub-second location updates and state changes. Options:

**WebSockets:** Persistent bidirectional connection. Server pushes updates without client polling. Good for: frequent updates (driver location on rider's map), instant state changes. Requires connection management at scale — use a WebSocket gateway with sticky sessions.

**Server-Sent Events (SSE):** Server pushes updates over HTTP. Simpler than WebSockets but unidirectional. Sufficient for rider updates (they mostly receive, not send).

**Long polling:** Request + wait for response until data available. Less efficient than WebSocket but works everywhere. Good fallback.

For driver location sharing to rider's map: rider's app opens WebSocket connection. When a trip is active, the server subscribes to driver location updates from the Location Service and pushes to the rider's WebSocket channel.

## Surge Pricing

When demand exceeds supply in a geographic area, surge pricing increases fare to incentivize more drivers to enter the area.

Architecture: a background service monitors supply/demand ratio per hexagonal grid cell (H3 is a standard geographic grid library). When ratio exceeds a threshold, compute a surge multiplier (1.5x, 2x, etc.). Store surge multipliers in Redis (low latency reads for every ride request). The Matching Service applies the multiplier to the fare estimate before presenting to the rider.

Fraud consideration: synthetic demand (coordinated fake ride requests to trigger surge) is a known attack vector. Rate limit requests per device and detect suspicious patterns.

## Scaling Considerations

Location Service: partition drivers by geographic region (sharding by geohash prefix). Driver density varies dramatically by city and time of day.

Matching Service: stateless, horizontally scalable. Scale up at peak hours.

Notification Service: at 10M trips/day with multiple notifications per trip, you have ~50M push notifications/day. Use a dedicated push notification service (Firebase, APNs) with batching and delivery receipts.

Database: Trip Service uses PostgreSQL with read replicas for trip history queries. Location Service uses Redis clusters for current locations.

This architecture — geospatial storage, distributed matching with locking, state machine for trips, WebSocket for real-time — covers the core system design patterns. Walk through failure modes: what happens if the Matching Service crashes during matching? (Trip remains in REQUESTED state; timer-based cleanup retries matching.) What if payment fails at trip end? (Trip completes for the rider; payment retry queue handles the charge asynchronously.)

## Related Articles

- [Uber Surge Pricing System Design](/blog/uber-surge-pricing-system-design)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Real-Time Chat](/blog/system-design-real-time-chat)
- [System Design: Notification System](/blog/system-design-notification-system)
- [System Design Interview Framework](/blog/interview-system-design-framework)
