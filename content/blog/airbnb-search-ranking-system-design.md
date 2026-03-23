---
title: "Airbnb Search Ranking System Design"
description: "How to design Airbnb's search and ranking system—query processing, listing retrieval, personalized ranking, and the ML infrastructure behind 7M+ listings at global scale."
date: "2026-03-21"
category: "System Design"
---

# Airbnb Search Ranking System Design

Airbnb's search ranking is the product's core value engine. With 7 million active listings, 1 billion search queries per year, and highly personalized results, it's a rich system design problem that spans search infrastructure, machine learning, and real-time personalization.

## Requirements

**Functional:**
- Search listings by location, dates, guests, price range
- Rank results by relevance + quality + personalization
- Filter by amenities, property type, super host status
- Map view with clustering
- Real-time availability checking

**Non-functional:**
- P99 search latency < 300ms
- 7M listings globally, 1M new searches/day
- Result quality measured by booking conversion rate
- Support 20+ filter dimensions

## Architecture Overview

```
User Query → Query Service → [Retrieval] → [Ranking] → Results
                                 ↓               ↓
                          Elasticsearch    ML Ranking
                          + Availability   Service
                          Filter
```

Two-stage pipeline: broad retrieval (thousands of candidates), precise ranking (ML model scores each).

## Query Processing

Parse the user's query into structured fields:

```python
{
  "location": {"lat": 48.8566, "lng": 2.3522, "radius_km": 30},
  "check_in": "2026-04-10",
  "check_out": "2026-04-15",
  "guests": 2,
  "filters": {
    "price_max": 200,
    "amenities": ["wifi", "kitchen"],
    "property_type": ["entire_place"]
  }
}
```

Location is geocoded (city/neighborhood → coordinates) using a geocoding service with LRU cache. "Paris" → (48.8566, 2.3522) with standard radius.

## Retrieval

Use Elasticsearch with geographic sharding (one index per region: US, EU, APAC, etc.).

Each listing document contains:
- Location (geo_point — enables fast radius queries)
- Listing attributes (amenities, capacity, type)
- Quality signals (rating, review count, superhost)
- Availability bitmap (per-date bitmap, queryable for date ranges)

```json
GET /listings-eu/_search
{
  "query": {
    "bool": {
      "filter": [
        {"geo_distance": {"distance": "30km", "location": {"lat": 48.8566, "lng": 2.3522}}},
        {"range": {"price": {"lte": 200}}},
        {"term": {"amenities": "wifi"}}
      ]
    }
  },
  "size": 2000
}
```

The availability check is the expensive part. A bitset approach: 365-bit vector per listing, bit `i` = available on day `i` from a reference date. Bitwise AND of check-in to check-out range returns available listings in microseconds.

This retrieval returns ~2000 listings in < 100ms.

## Ranking Model

Score the 2000 candidates with a learning-to-rank model. Features:

**Listing quality features:**
- Average rating, review count
- Superhost status, response rate
- Listing photos quality score (computer vision)
- Price per night (raw + percentile within market)

**Relevance features:**
- Distance from search center
- Match score on amenities requested
- Property type preference match
- Capacity fit (guests / max capacity)

**Personalization features:**
- User's historical booking preferences (property type, price range)
- User's search session context (pages viewed, wishlisted)
- User's location preferences (beach vs city)

**Contextual features:**
- Day of week / seasonality
- Lead time (booking now vs 3 months out)
- Similar users' click + book patterns

Train a GBM (LightGBM) or neural ranker on historical search → click → book labels. Optimize for booking conversion (not just clicks — bookings are what matter).

## Personalization

New users (cold start): use global popularity ranking with basic preference matching.

Returning users: build a preference vector from booking history + wishlist + search patterns. Update in near-real-time (after each interaction, update user feature store in Redis).

**Session-level personalization**: within a single search session, boost listings similar to those the user clicked (immediately after click) and demote property types they've been ignoring.

## Price Intelligence

Airbnb has a "Smart Pricing" feature that advises hosts on optimal prices. This feeds back into search:
- Listings using smart pricing have better availability predictability
- Market price percentile is a ranking feature (extreme outliers ranked down)
- Price consistency (not varying wildly) is a trust signal

## Availability Calendar

Availability is complex: hosts can block dates, minimum stay requirements apply, instant book vs request-to-book distinction matters.

The availability check happens in two places:
1. **Fast path**: bitset check during retrieval (eliminates unavailable listings quickly)
2. **Precise path**: after ranking, top 50 results are re-checked against real-time booking state in Redis (the bitset can be slightly stale)

This two-step availability check prevents "ghost listings" (showing up in search but unavailable when booked) without paying the cost of real-time DB lookup for all 2000 candidates.

## Map View

When user switches to map view, render clustered pins. Use H3 hexagonal cells for geographic clustering:
- High zoom (street level): individual pins
- Low zoom (city level): clusters with count badges

Clusters are pre-computed and cached. Map viewport changes send bounding box to the backend, which fetches listings in that viewport from the cached cell grid.

## A/B Testing

Every ranking change is A/B tested. Primary metric: booking conversion rate. Secondary: guest satisfaction (post-trip rating), revenue per search.

Run holdout groups (10% of traffic sees old ranker) for 2+ weeks to capture booking cycle latency — users often search 30-60 days before their trip.

## Interview Tips

The two-stage retrieval + ranking pattern is the heart of this answer. Depth areas:
1. Availability checking — the bitset trick is impressive and practical
2. Personalization — explain cold start and session-level signals
3. A/B testing with booking cycle lag — shows real product thinking
4. Map clustering — often asked as a follow-up

## Related Articles

- [Airbnb Interview Guide](/blog/airbnb-interview-guide)
- [System Design: Search Engine](/blog/system-design-search-engine)
- [System Design: Recommendation Engine](/blog/system-design-recommendation-engine)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Distributed Cache](/blog/system-design-distributed-cache)
