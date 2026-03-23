---
title: "DoorDash Delivery Optimization Architecture"
description: "How DoorDash optimizes delivery logistics—order assignment, route optimization, ETA prediction, batch delivery, and the real-time systems handling 2B+ orders annually."
date: "2026-03-21"
category: "System Design"
---

# DoorDash Delivery Optimization Architecture

DoorDash processes 2 billion orders per year. Each delivery involves three parties—customer, restaurant, Dasher—whose schedules must be coordinated precisely. The optimization problem (assign orders to Dashers efficiently) is NP-hard, but must be solved in seconds. This system design question tests graph optimization, real-time data processing, and multi-sided marketplace mechanics.

## The Core Problem

When an order is placed:
1. Restaurant needs time to prepare (10-30 minutes)
2. A Dasher must be assigned and dispatched
3. Dasher picks up when food is ready (not before — cold food is bad)
4. Dasher delivers to customer within promised window

The assignment problem: which Dasher gets which order? With 1M+ orders per hour and 1M+ active Dashers, this is a large-scale matching problem with real-time constraints.

## System Architecture

```
Customer places order → Order Service
                             ↓
                      Restaurant notified
                             ↓
                    Dispatch Service (core)
                    ├─ Dasher Pool Manager
                    ├─ Assignment Engine
                    └─ Route Optimizer
                             ↓
                    Dasher receives assignment
                             ↓
                    Order Tracking Service → Customer
```

## Order Lifecycle

```
CREATED → CONFIRMED (restaurant accepted)
        → PREPARING
        → READY_FOR_PICKUP
        → PICKED_UP (Dasher en route)
        → DELIVERED
```

State transitions trigger real-time notifications to all three parties. The Dispatch Service listens to state changes via Kafka and triggers reassignment if needed (e.g., a Dasher cancels).

## Dasher Assignment: The Matching Problem

Simple greedy: assign nearest available Dasher. Works but suboptimal — doesn't account for upcoming orders, Dasher batching opportunities, or restaurant prep time.

**Optimized assignment**:
- Consider Dashers within a radius of the restaurant
- Score each candidate Dasher by estimated pickup ETA × delivery ETA × batching opportunity
- Account for prep time: don't assign a Dasher who'd arrive 15 minutes before food is ready

```python
def score_dasher_for_order(dasher, order):
    # ETA from Dasher to restaurant
    pickup_eta = route_service.eta(dasher.location, order.restaurant.location)

    # Will the Dasher arrive after food is ready?
    ready_time = order.placed_at + estimate_prep_time(order)
    dasher_arrival = time.now() + pickup_eta
    wait_time = max(0, ready_time - dasher_arrival)

    # Total delivery time
    delivery_eta = pickup_eta + wait_time + route_service.eta(order.restaurant.location, order.customer.location)

    return -delivery_eta  # maximize: minimize delivery time
```

## Batch Delivery (Multiple Orders)

A Dasher can carry 2-3 orders simultaneously if restaurants are nearby and deliveries are in the same direction. Batching improves economics but risks longer delivery times for each individual order.

**Batch scoring**:
- Route increase: how much longer is the batched route vs single delivery?
- Time increase per order: tolerable if < 10 extra minutes
- Restaurant proximity: both restaurants within 0.5km of each other

```
Order A: Restaurant R1, Customer at C1
Order B: Restaurant R2, Customer at C2

Single route: R1 → C1 (15min)
Batched route: R1 → R2 → C1 → C2 (22min)
  → Order A: +7min (acceptable)
  → Order B: +0min (delivered last)
```

The batch decision is made when Order B is created if Order A's Dasher is nearby and on the way.

## ETA Prediction

"Your food arrives in 25 minutes." This ETA must be accurate — DoorDash found that accurate ETAs reduce support contacts by 30%.

Components of ETA:
1. **Prep time**: ML model trained on restaurant's historical prep times (varies by order size, time of day, current queue)
2. **Pickup wait**: time for Dasher to arrive at restaurant
3. **Drive time**: Google Maps / DoorDash's own historical route data

```python
def predict_delivery_eta(order, dasher):
    prep_time = prep_time_model.predict(
        restaurant_id=order.restaurant_id,
        order_size=order.item_count,
        hour=current_hour,
        current_queue_depth=restaurant_orders_in_flight()
    )
    drive_time = route_service.predicted_eta(
        dasher.location, order.restaurant.location,
        time=now()
    )
    delivery_drive = route_service.predicted_eta(
        order.restaurant.location, order.customer.location,
        time=now() + prep_time
    )
    return prep_time + max(0, prep_time - drive_time) + delivery_drive
```

ETA is recalculated every 30 seconds and pushed to the customer's app.

## Dynamic Dasher Positioning (Supply Shaping)

DoorDash influences where Dashers are located before orders arrive. Using historical demand patterns:

1. Predict order demand by zone for next 30 minutes (time-series ML model)
2. Identify zones where supply (Dashers) won't meet predicted demand
3. Show Dashers heatmaps of high-demand zones (earn more by positioning there)
4. Offer bonuses for Dashers positioning in undersupplied zones

This is a proactive supply-demand balancing act. Similar to Uber's surge pricing but applied to positioning, not pricing.

## Restaurant Coordination

DoorDash faces the "cold food" problem: Dasher arrives before food is ready, waits at restaurant (wastes time, blocks other orders). Or: Dasher arrives late, food sits cold.

Solution: **dynamic dispatch timing**. Don't dispatch the Dasher immediately when order is placed. Dispatch based on predicted food-ready time:

```
dispatch_time = order.placed_at + prep_time_estimate - dasher_travel_time
```

The restaurant sends a "food ready" signal from their tablet. This triggers immediate dispatch if Dasher wasn't already en route.

## Fraud Detection

Common fraud patterns:
- **Dasher never delivered**: Dasher claims delivery, customer claims non-receipt
- **Order stealing**: Dasher picks up wrong order
- **GPS spoofing**: Dasher fakes delivery location

Countermeasures:
- GPS trail audit: verify Dasher was actually at delivery address
- Delivery photo: required for delivery confirmation (restaurant + door)
- ML anomaly detection: Dasher claiming delivery without ever being near the address

## Interview Tips

DoorDash delivery optimization is a rich multi-dimensional problem:

1. **Three-sided marketplace**: customer, restaurant, Dasher each have their own state machines
2. **Batching tradeoffs**: efficiency vs individual delivery time
3. **Prep time prediction**: the hidden variable that determines dispatch timing
4. **Dynamic positioning**: supply shaping before demand arrives
5. **ETA accuracy**: decompose into prep + pickup + drive components

The dynamic dispatch timing (don't dispatch immediately — wait until food is nearly ready) is the key insight that separates good answers from generic "ride sharing but for food" answers.
