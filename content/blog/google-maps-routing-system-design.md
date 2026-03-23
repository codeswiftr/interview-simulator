---
title: "Google Maps Routing System Design"
description: "How to design Google Maps routing—road graph representation, Dijkstra vs A* vs CH algorithms, real-time traffic integration, and ETA prediction at global scale."
date: "2026-03-21"
category: "System Design"
---

# Google Maps Routing System Design

Google Maps serves 1 billion users, processes 20 million routing queries per day, and incorporates real-time traffic data from 500 million users' devices. The routing system behind "get directions" is one of the most sophisticated graph algorithms deployed at scale.

## The Problem Space

Routing = shortest path on a weighted directed graph, where:
- Nodes = road intersections
- Edges = road segments
- Weights = travel time (not just distance — accounts for speed limits, traffic, turns)

Global road network: ~60 million nodes, ~150 million edges. Running Dijkstra on this raw graph is too slow (O((V + E) log V) ≈ seconds per query). Production systems use preprocessing to enable millisecond queries.

## Graph Preprocessing: Contraction Hierarchies

**Contraction Hierarchies (CH)** is the standard algorithm for road network routing:

1. **Preprocessing phase** (offline): Rank all nodes by "importance." Less important nodes (residential streets) get contracted first. Contracting a node means adding "shortcut" edges that bypass it.

2. **Query phase** (online): Run bidirectional Dijkstra from source and target simultaneously, only relaxing edges going "upward" in the hierarchy. This limits the search space dramatically.

Result: routing on global road network in < 10ms. Google Maps adds additional optimization layers (A* heuristics, landmarks) on top.

## Hierarchy Design

Road hierarchy mirrors real-world hierarchy:
- Level 4: Highways/motorways (highest importance)
- Level 3: Primary roads
- Level 2: Secondary roads
- Level 1: Tertiary roads
- Level 0: Residential streets (contracted first)

Long-distance routes travel up to highway level, cross the country on highways, come back down at the destination. Short local routes never leave level 0-1.

## Real-Time Traffic Integration

Static routing gives optimal paths assuming empty roads. Real-time traffic adjusts edge weights based on current conditions.

**Data sources:**
- **Crowd-sourced GPS**: 500M active Google Maps/Android users with location sharing. Their speed at each road segment is averaged to compute real-time speed.
- **Historic patterns**: ML model trained on years of data to predict traffic for day/time/weather.
- **Incident reports**: Accidents, road closures (both user-reported and official sources).

**Edge weight formula:**
```
travel_time = segment_length / effective_speed

effective_speed = weighted_blend(
    real_time_speed * 0.6,
    historical_speed * 0.3,
    speed_limit * 0.1
)
```

The blend weights are themselves ML-derived, varying by time of day and data density.

## ETA Prediction

ETA is not just "sum of edge travel times." It must account for:
- Traffic that will exist when you reach each segment (not current traffic)
- Slow segments caused by bottleneck downstream
- Time-dependent edge weights (rush hour builds during the route)

Google uses a **time-expanded graph** where each node at time T is distinct from node at time T+10min. Edges have time-dependent weights. Dijkstra on this graph finds the optimal time-dependent path.

ETA accuracy is measured as MAE (mean absolute error) vs actual completion time. Google's systems achieve < 5% error for routes under 1 hour.

## Tile-Based Graph Storage

The global road graph can't fit in memory of a single server. It's partitioned into geographic tiles (like map tiles):

- Each tile contains nodes and edges for a ~50km × 50km area
- Inter-tile edges reference neighboring tiles
- For long-distance routing, the CH hierarchy allows using only highway-level tiles

At query time, the routing server loads only the tiles relevant to the path. Cache hot tiles (city centers, major highways) in RAM.

## Alternative Routes

"Take the left fork for a 2-minute saving" uses **plateau algorithm** or **penalty method** to find top-k diverse routes:

1. Find optimal route
2. Penalize edges on the optimal route
3. Find next optimal route (different path)
4. Repeat until k diverse routes found

Diversity constraint: routes must differ by at least X% of edges to be considered "alternative" (not just a minor variant).

## Transit and Multi-Modal Routing

Walking + transit routing adds complexity:
- Time-dependent edges: train departure at 10:15, 10:45, 11:15
- Transfer time: walking between platforms
- Fare zones and pass applicability

Uses **time-expanded graph** with transit edges added: a node for "at station X at time T," edges for each scheduled departure.

## Serving Architecture

```
Client → API Gateway
              ↓
      Routing Service Cluster
      (stateless, scales horizontally)
              ↓
      Graph Tile Cache (Redis / CDN)
              ↓
      Graph Tile Storage (GFS/Colossus)

Offline pipeline:
  OSM data + proprietary sources
  → Graph build pipeline (weekly)
  → CH preprocessing (48-hour compute job)
  → Tile generation and distribution
```

The graph is rebuilt weekly (incorporating OSM updates, new roads, corrected data). The CH hierarchy is rebuilt then too—it's not incremental. This is why new roads appear on Maps within 1-2 weeks of opening.

## Real-Time Updates

Traffic updates happen without graph rebuilds:
- Edge weight updates pushed to routing servers every 5 minutes
- Incident overlays (road closures, construction) applied as hard edge removals
- A/B testing routes: compare CH route vs ML-adjusted route, pick better ETA predictor

## Interview Tips

This is a deep algorithms + distributed systems question. Key points:

1. **Why Dijkstra alone is insufficient** — scale it up: 60M nodes, ~10ms budget
2. **Contraction Hierarchies** — the key algorithmic insight
3. **Real-time traffic as edge weight adjustment** — not a separate system
4. **Time-dependent routing for ETA** — not just summing static weights
5. **Tile-based graph storage** — geographic partitioning

Even if you don't know CH perfectly, showing you understand the problem (graph too big for raw Dijkstra, preprocessing enables fast queries, real-time traffic updates edge weights) is a very strong answer.

## Related Articles

- [Google Interview Guide](/blog/google-interview-guide)
- [System Design: Search Engine](/blog/system-design-search-engine)
- [Graph Algorithms Interview Guide](/blog/graph-algorithms-interview-guide)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Distributed Cache](/blog/system-design-distributed-cache)
