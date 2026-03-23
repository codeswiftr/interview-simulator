---
title: "Designing a Real-Time Bidding Platform"
description: "How to design an RTB (real-time bidding) platform for programmatic advertising—auction mechanics, bid request/response flow, win notification, and sub-100ms latency architecture."
date: "2026-03-21"
category: "System Design"
---

# Designing a Real-Time Bidding Platform

Real-time bidding (RTB) powers the majority of digital advertising. When you load a webpage, an auction runs in under 100 milliseconds to determine which ad you see—and what price the advertiser pays. This system design problem is highly constrained: correctness, latency, and scale must all be achieved simultaneously.

## How RTB Works

1. User visits a webpage. Publisher's ad server calls the **Supply-Side Platform (SSP)**.
2. SSP sends a **bid request** to multiple **Demand-Side Platforms (DSPs)**.
3. Each DSP evaluates the user, runs internal auction, responds with a **bid** (price + ad creative).
4. SSP runs a **second-price auction** across all bids. Highest bidder wins, pays second-highest price + $0.01.
5. Winner's ad is rendered on the page. Win notification sent to winner; loss notifications to losers.

All of this must complete in < 100ms (realistically < 50ms for competitive exchanges).

## RTB Platform Requirements

Designing the DSP (the bidder):

**Functional:**
- Evaluate bid requests: match advertiser targeting criteria against user data
- Compute bid price for each matched request
- Respond with bid within 50ms SLA
- Process win/loss notifications, update spend pacing
- Budget management: never overspend advertiser budget

**Non-functional:**
- 10M bid requests/second (global)
- P99 bid response < 50ms (or the SSP ignores your bid)
- Budget enforcement: < 1% overspend tolerance
- Scale: 10K active campaigns

## Architecture Overview

```
Bid Request (10M/s) → Bid Request Receivers (stateless, horizontal)
                          ↓
                    User Data Lookup (< 5ms) ← Redis Cluster
                          ↓
                    Campaign Matching (< 10ms) ← In-memory campaign index
                          ↓
                    Bid Pricing Model (< 5ms) ← ML inference service
                          ↓
                    Budget Check (< 2ms) ← Redis atomic ops
                          ↓
                    Bid Response → SSP
```

Total: < 22ms for core path, leaves margin for network.

## User Data Lookup

The bid request contains a user identifier (cookie ID or device ID). The DSP must enrich this with audience segments:

```
user_id → {segment_ids: [sports_fan, luxury_buyer, 18-34_male, NY_resident]}
```

User profiles stored in Redis Cluster. Single key lookup per request:
```
GET user_profile:{user_id}
→ returns {segments: [...], frequency_caps: {...}, last_seen: timestamp}
```

P99 Redis lookup: 1-2ms at single datacenter. This lookup must happen in the request path.

Profiles are built by a separate data pipeline (Kafka consumers processing behavioral events, ML models computing audience probabilities) and continuously updated in Redis.

## Campaign Matching

Given the user's segments and the bid request's context (URL, ad size, device type), find all eligible campaigns.

**Inverted index** in memory:
```python
# Index: segment → list of campaigns targeting that segment
segment_index = {
    'sports_fan': [campaign_123, campaign_456],
    'luxury_buyer': [campaign_789, campaign_123],
    ...
}

def match_campaigns(user_segments, context):
    candidate_campaigns = set()
    for segment in user_segments:
        candidate_campaigns.update(segment_index.get(segment, []))

    eligible = []
    for campaign in candidate_campaigns:
        if campaign.matches(context) and not over_frequency_cap(campaign, user):
            eligible.append(campaign)
    return eligible
```

The in-memory index fits in RAM because campaign metadata is small (< 1KB per campaign × 10K active campaigns = 10MB). Updated from a Redis-backed campaign store on change events.

## Bid Pricing

Bid price = value of this impression to the advertiser. Two approaches:

**Rule-based**: Fixed CPM (cost per thousand impressions) per campaign, adjusted by targeting tier. Simple, predictable spend.

**ML-based**: Predict P(conversion | user, context, ad). Bid = eCPM = P(conversion) × conversion_value × 1000.

```python
def compute_bid_price(campaign, user_features, context_features):
    # ML model: two-tower embedding, trained on historical conversions
    p_conversion = model.predict(user_features, context_features, campaign.ad_id)
    ecpm = p_conversion * campaign.conversion_value * 1000
    # Apply bid shading (second-price auction strategy)
    return min(ecpm * campaign.bid_modifier, campaign.max_bid_cpm)
```

The ML model runs as a separate inference service (TensorFlow Serving / Triton). Latency budget: < 5ms using an optimized model.

## Budget Management

Budget enforcement is the hardest correctness problem. Overspend > 1% is a contractual violation. Underspend wastes inventory. The challenge: 10M bids/second across distributed servers.

**Global budget counter in Redis**:
```python
def can_bid(campaign_id, bid_price):
    remaining = redis.get(f"budget_remaining:{campaign_id}")
    return remaining >= bid_price

def record_win(campaign_id, win_price):
    redis.decrby(f"budget_remaining:{campaign_id}", win_price)
```

Problem: 10M bids/second → 10M Redis calls/second for budget checks. Redis can handle this (1M ops/sec per node, horizontal scaling), but it's tight.

**Token bucket optimization**: Each bidding server maintains a local token bucket (short-term budget allocation). Global Redis budget distributed in chunks (e.g., $10 at a time) to local servers. Local check is in-memory (< 0.1ms). Risk: slight overspend if all servers have tokens when budget runs out.

Acceptable tradeoff: < 1% overspend with local token buckets, vs < 0.01% overspend with global Redis counter but 2ms overhead per bid.

## Win/Loss Notification Processing

After the auction, SSP sends win/loss notifications asynchronously:
- Win notification includes the clearing price (second-price)
- Loss notification (optional, for analytics)

Process via Kafka consumer:
```
Win notification → Kafka → win_processor
                                ↓
                  Deduct actual win price from budget (was reserved)
                  Update campaign performance metrics
                  Log to analytics (cost, impressions, clicks)
```

Budget was **reserved** at bid time; adjusted to actual win price at win notification. This prevents overspend due to bid price vs clearing price difference.

## Frequency Capping

Limit how many times a user sees the same ad in a time window:

```
frequency:{campaign_id}:{user_id} → [timestamp1, timestamp2, ...]
```

Store in Redis as a sorted set. Before bidding:
```python
count = redis.zcount(f"freq:{campaign_id}:{user_id}", time.now() - 24*3600, time.now())
if count >= campaign.frequency_cap_daily:
    skip_campaign()
```

## Interview Tips

RTB is a specialized domain, but the engineering patterns are universal:

1. **Strict latency budget** — every component gets a time allocation (User lookup: 5ms, Campaign match: 10ms, etc.)
2. **In-memory campaign index** — don't query DB per request; keep campaigns in RAM
3. **Budget enforcement tradeoff** — local token bucket vs global counter, explain the overspend risk explicitly
4. **Second-price auction mechanics** — shows domain knowledge
5. **Async win/loss processing** — separate critical path from analytics

The budget management section is where strong candidates differentiate themselves. Show that you understand distributed counter patterns and the inherent tension between consistency and latency.
