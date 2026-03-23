---
title: "DoorDash Engineering Deep Dive: Food Delivery Platform at Last-Mile Scale"
date: "2024-01-22"
category: "Engineering Deep Dive"
tags: ["doordash", "food-delivery", "distributed-systems", "ml", "microservices", "interview-prep"]
excerpt: "A technical breakdown of how DoorDash orchestrates a three-sided marketplace across customers, restaurants, and Dashers — covering the assignment problem, real-time ETA prediction, reliability engineering, and their monolith-to-microservices journey."
---

# DoorDash Engineering Deep Dive: Food Delivery Platform at Last-Mile Scale

DoorDash's engineering challenge is fundamentally harder than a two-sided marketplace. A rideshare platform matches riders to drivers — two parties. DoorDash coordinates three: customers placing orders, restaurants preparing food, and Dashers picking up and delivering. Every order is a multi-stage pipeline with time constraints at each stage, and failures at any stage cascade to the others.

At peak, DoorDash processes millions of orders per day, each requiring real-time coordination, ETA estimation, and contingency handling when things go wrong. The systems behind this are a masterclass in distributed systems under operational pressure.

## The Three-Sided Marketplace: Dispatch Architecture

DoorDash's Dispatch system is their core orchestration engine. When a customer places an order, Dispatch must:

1. Confirm the restaurant can accept the order
2. Find and assign a Dasher who can arrive at the restaurant close to when the food will be ready
3. Continuously reoptimize as reality diverges from the plan

The assignment problem — matching orders to Dashers — is a variant of the vehicle routing problem (VRP), which is NP-hard in its general form. DoorDash uses a combination of heuristics and approximate optimization:

- **Greedy initial assignment**: assign each new order to the best available Dasher given current state
- **Periodic batch reoptimization**: every 30 seconds, run a constrained optimization pass over all unassigned and in-progress orders to find globally better assignments
- **Stacking**: one Dasher can carry multiple orders if pickup locations and delivery windows align — this dramatically improves efficiency but adds combinatorial complexity

The key insight is that the greedy pass handles latency requirements (assignments must happen in seconds), while the batch optimizer improves overall system efficiency without blocking real-time operations.

## Real-Time ETA: A Pipeline of Uncertainty

DoorDash's estimated delivery time is not a single number — it's the sum of three uncertain quantities:

1. **Restaurant preparation time**: How long until the food is ready?
2. **Dasher travel time to restaurant**: How long for the assigned Dasher to reach the pickup?
3. **Delivery travel time**: How long from restaurant to customer's door?

Each of these is a separate ML model, and they compose into a final ETA with propagated uncertainty. Here's a simplified version of how this pipeline works:

```python
from dataclasses import dataclass
from typing import Optional
import math

@dataclass
class ETAComponent:
    mean_minutes: float
    std_minutes: float  # Uncertainty as standard deviation

    def pessimistic(self, percentile: float = 0.85) -> float:
        """Return percentile estimate (assumes log-normal distribution)."""
        # Approximate: mean + z_score * std
        z_scores = {0.50: 0.0, 0.75: 0.674, 0.85: 1.036, 0.95: 1.645}
        z = z_scores.get(percentile, 1.036)
        return self.mean_minutes + z * self.std_minutes


@dataclass
class OrderContext:
    restaurant_id: str
    cuisine_type: str
    order_complexity: int        # Number of items
    hour_of_day: int
    dasher_lat: float
    dasher_lng: float
    restaurant_lat: float
    restaurant_lng: float
    customer_lat: float
    customer_lng: float


def predict_prep_time(ctx: OrderContext) -> ETAComponent:
    """
    Predict restaurant prep time from historical restaurant performance,
    order complexity, and current restaurant load.
    In production: gradient-boosted model with restaurant-specific features.
    """
    base_minutes = 12.0
    complexity_penalty = ctx.order_complexity * 1.5
    # Peak hour adjustment (simplified)
    peak_penalty = 3.0 if 11 <= ctx.hour_of_day <= 13 or 18 <= ctx.hour_of_day <= 20 else 0.0
    mean = base_minutes + complexity_penalty + peak_penalty
    # Higher complexity = more uncertainty
    std = 2.0 + ctx.order_complexity * 0.5
    return ETAComponent(mean_minutes=mean, std_minutes=std)


def predict_dasher_pickup_eta(ctx: OrderContext) -> ETAComponent:
    """
    Estimate how long it takes the Dasher to reach the restaurant.
    In production: routing API + real-time traffic + dasher behavior model.
    """
    R = 6371
    lat1, lng1 = math.radians(ctx.dasher_lat), math.radians(ctx.dasher_lng)
    lat2, lng2 = math.radians(ctx.restaurant_lat), math.radians(ctx.restaurant_lng)
    dlat, dlng = lat2 - lat1, lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlng/2)**2
    distance_km = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    # Urban speed ~25 km/h, with 20% traffic variance
    mean = (distance_km / 25) * 60
    std = mean * 0.20
    return ETAComponent(mean_minutes=mean, std_minutes=std)


def predict_delivery_eta(ctx: OrderContext) -> ETAComponent:
    """Estimate delivery leg from restaurant to customer."""
    R = 6371
    lat1, lng1 = math.radians(ctx.restaurant_lat), math.radians(ctx.restaurant_lng)
    lat2, lng2 = math.radians(ctx.customer_lat), math.radians(ctx.customer_lng)
    dlat, dlng = lat2 - lat1, lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlng/2)**2
    distance_km = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    mean = (distance_km / 22) * 60  # Slightly slower with food
    std = mean * 0.25               # More variance (parking, building entry)
    return ETAComponent(mean_minutes=mean, std_minutes=std)


def compute_total_eta(ctx: OrderContext, pessimism: float = 0.85) -> dict:
    """
    Compose three ETA components into total delivery estimate.
    The displayed ETA is the pessimistic estimate — DoorDash optimizes
    for on-time delivery, not optimistic promises.
    """
    prep = predict_prep_time(ctx)
    pickup = predict_dasher_pickup_eta(ctx)
    delivery = predict_delivery_eta(ctx)

    # Components are partially correlated (same traffic conditions)
    # Simplified: assume independence for variance composition
    total_mean = prep.mean_minutes + pickup.mean_minutes + delivery.mean_minutes
    total_std = math.sqrt(
        prep.std_minutes**2 + pickup.std_minutes**2 + delivery.std_minutes**2
    )
    total_component = ETAComponent(total_mean, total_std)

    return {
        "mean_eta_minutes": round(total_mean, 1),
        "displayed_eta_minutes": round(total_component.pessimistic(pessimism), 1),
        "breakdown": {
            "prep": round(prep.mean_minutes, 1),
            "dasher_to_restaurant": round(pickup.mean_minutes, 1),
            "restaurant_to_customer": round(delivery.mean_minutes, 1),
        }
    }


# Example
ctx = OrderContext(
    restaurant_id="r123", cuisine_type="thai", order_complexity=4,
    hour_of_day=19, dasher_lat=37.775, dasher_lng=-122.418,
    restaurant_lat=37.780, restaurant_lng=-122.415,
    customer_lat=37.770, customer_lng=-122.420
)
eta = compute_total_eta(ctx)
print(f"ETA: {eta['displayed_eta_minutes']} min (mean: {eta['mean_eta_minutes']} min)")
print(f"Breakdown: {eta['breakdown']}")
```

The real DoorDash models are far more sophisticated — they incorporate restaurant-specific historical distributions, Dasher-level behavioral features (some Dashers consistently park faster), and live signal from Dashers' GPS traces to detect when they've been waiting longer than expected.

## Consumer-Facing Reliability: Handling Failures Gracefully

DoorDash's reliability engineering is not just about uptime — it's about what the system does when a restaurant is running 20 minutes late or when a Dasher drops an order mid-delivery.

**Restaurant delay handling**: DoorDash's system continuously monitors the gap between predicted and actual prep time. When a restaurant is running behind, the system can:
- Delay the Dasher assignment (no point sending them to wait)
- Proactively notify the customer with a revised ETA
- In extreme cases, re-route an already-dispatched Dasher to pick up a different order first

**Dasher drop handling**: If a Dasher becomes unavailable after pickup (phone dies, emergency), the system must reassign the order. This is harder than initial assignment — the food is already prepared and cooling. The system prioritizes Dashers near the restaurant, and if none are available, it escalates to a support queue where human operators can intervene.

These flows require event sourcing: every state transition in an order's lifecycle is recorded as an immutable event, so the system can reconstruct current state and make decisions based on full history.

## Monolith to Microservices: The Migration Story

DoorDash, like many fast-growing startups, started with a Python/Django monolith. By 2018, the monolith had become a liability: deployment required testing the entire application, a bug in one domain could take down unrelated features, and team velocity was declining as the codebase grew.

Their migration followed a strangler fig pattern:

1. **Identify bounded contexts**: catalog the monolith's domain concepts (Orders, Payments, Dashers, Restaurants, Dispatch) and define their interfaces
2. **Extract leaf services first**: services with few dependencies migrate cleanly — they chose Payments first because it had a well-defined boundary and high business incentive (PCI compliance)
3. **Build an API gateway**: route traffic to either the monolith or extracted services based on feature flags — this enabled gradual traffic shifting without big-bang cutover
4. **Manage data ownership**: each microservice owns its data store; shared data requires explicit contracts and eventual consistency

Key technical decision: they chose gRPC for internal service communication (typed contracts, efficient binary serialization) and Kafka for event-driven coordination between services. The Order service publishes events (OrderPlaced, OrderPickedUp, OrderDelivered), and downstream services consume them without direct coupling.

The migration took three years and is still ongoing. The engineering blog post they published on this is one of the most honest accounts of microservices migration in the industry — they openly discuss the distributed systems complexity they introduced (distributed transactions, saga pattern for order cancellations) that didn't exist in the monolith.

## Interview Implications

**System design questions to expect at DoorDash:**
- Design a food delivery tracking system
- Design the order assignment system for a three-sided marketplace
- Design a real-time ETA prediction pipeline
- How would you handle a cascading failure when a restaurant is down?

**Key concepts to master:**
- Multi-sided marketplace coordination and the assignment problem
- Event sourcing for complex state machines with many failure modes
- Composing probabilistic estimates (ETA as sum of uncertain components)
- Saga pattern for distributed transactions (order cancellation spanning multiple services)
- Strangler fig migration pattern and traffic shifting with feature flags

**A common interview trap**: candidates design DoorDash as a two-sided marketplace (customer + Dasher), forgetting the restaurant as an active participant with its own latency, state, and failure modes. Always enumerate all actors and their failure modes before proposing a design.

The interview simulator's DoorDash question bank specifically tests whether you can reason about three-party coordination — a materially harder problem than the two-party case that requires different consistency and failure handling strategies.
