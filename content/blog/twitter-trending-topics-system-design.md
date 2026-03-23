---
title: "Twitter Trending Topics System Design"
description: "How to design Twitter's trending topics feature—real-time tweet counting, sliding window aggregation, anomaly detection, and geographic trending for 500M daily tweets."
date: "2026-03-21"
category: "System Design"
---

# Twitter Trending Topics System Design

Twitter's trending topics surface the most-discussed subjects in near-real-time. With 500M tweets per day, the system must aggregate tweet counts, detect velocity spikes, filter spam, and localize trends—all within seconds of the tweets being posted.

## Requirements

**Functional:**
- Show top-10 trending topics globally and by location
- Update trends every 30 seconds
- Trends reflect velocity (rising topics), not absolute volume (Justin Bieber shouldn't permanently trend)
- Filter spam and coordinated inauthentic behavior

**Non-functional:**
- 500M tweets/day = ~5,800 tweets/second average, 30K/s peak
- Trend freshness: within 30 seconds of a tweet spike
- Localization: trends per country, state/region, city (top 50 cities)

## Defining "Trending"

The naive approach—count hashtag occurrences in the last hour—doesn't work. Topics with huge baseline volume (sports teams, celebrities) would always trend, drowning out genuine breakout moments.

The correct approach: measure **velocity** relative to baseline.

```
trend_score = (recent_count - expected_baseline) / expected_baseline_stddev
```

This is essentially a z-score of recent activity vs historical pattern. A topic is trending when its activity is statistically anomalous, not just high.

**Baseline** is computed from historical patterns for the same time window (same hour, same day of week, over the past 4 weeks). A topic that always spikes on Sunday evenings isn't "trending" — it's expected.

## Data Pipeline

```
Tweet → Kafka (tweet_stream topic)
          ↓
     Stream Processor (Flink)
     ├─ Extract hashtags, mentions, phrases
     ├─ Count per 30-second window
     └─ Compute sliding window aggregates
          ↓
     Trend Score Calculator
     ├─ Fetch baseline from feature store
     ├─ Compute z-score per term
     └─ Filter and rank
          ↓
     Redis (trending cache)
          ↓
     Trend API → Clients
```

## Hashtag and Term Extraction

Not just hashtags. Trending topics include:
- Explicit hashtags (`#SuperBowl`)
- Named entity mentions (`Taylor Swift`)
- Multi-word phrases (`new album`)

NLP pipeline on each tweet:
1. Tokenize
2. Named entity recognition (NER) for person/org/location names
3. N-gram extraction for phrase detection
4. Merge hashtag mentions with entity mentions (`#TaylorSwift` + `Taylor Swift` = same topic)

Entity resolution is expensive. In practice, run NER on a sample (10-20% of tweets) and rely on hashtag extraction for full volume.

## Sliding Window Counting

Use a **count-min sketch** for approximate counting at scale. Exact counts for 500M tweets with millions of potential terms require too much memory. CMS provides approximate counts with bounded error using far less memory.

```
Window: 30-second tumbling windows
Aggregation: count-min sketch per window
Merge: sum last 4 windows for 2-minute rolling count
```

For the final ranking, extract the top-K terms using a min-heap (space efficient):

```python
def top_k_terms(cms, k=1000):
    heap = []
    for term in candidate_terms:  # pre-filtered high-activity terms
        count = cms.query(term)
        if len(heap) < k or count > heap[0][0]:
            heappush(heap, (count, term))
            if len(heap) > k:
                heappop(heap)
    return sorted(heap, reverse=True)
```

## Localization

Store tweet origin metadata (user's declared location, tweet geotag if provided). For each geographic region:
- Maintain separate CMS per region
- Top-K computation per region
- Aggregate smaller regions into larger (city → country)

User location is unreliable (many users set fake locations). Fall back to:
1. User's declared location (account profile)
2. Language of tweet (proxy for country)
3. IP geolocation (if available via API)
4. Network-level signals

## Trend Score Ranking

```python
def compute_trend_score(term, region="global"):
    current_count = get_count(term, window=30min, region=region)
    baseline = get_historical_baseline(term, hour=current_hour, day=current_day)
    baseline_std = get_historical_std(term)

    if baseline_std == 0:  # new term, no history
        # Score purely on absolute velocity
        return current_count / max_new_term_velocity

    z_score = (current_count - baseline) / baseline_std
    return sigmoid(z_score)  # normalize to [0, 1]
```

New terms (no historical baseline) are scored on absolute velocity. This lets genuinely new events trend without historical context.

## Spam and Manipulation Detection

Trending manipulation is a real attack vector (coordinated hashtag campaigns). Detection:

**Account quality filtering**: Filter tweets from accounts with low quality scores (new accounts, no followers, unusual tweet rates). Assign each tweet a quality weight; use weighted counts.

**Coordination detection**: If 10,000 accounts all tweet the same hashtag within 60 seconds of each other, that's likely coordinated. Detect via temporal clustering of similar content.

**Rate limiting per topic**: Cap how much any single account can contribute to a topic's trending count (1 tweet per account per 30-second window for counting purposes).

## Caching and Serving

Trending topics are read millions of times per second. Cache aggressively:

```
Redis key: trending:{region}
Value: JSON array of top-10 topics with metadata
TTL: 30 seconds (regenerated by Flink job)

Client cache: 30 seconds (no need to fetch on every page load)
CDN cache: Not cached (too region-specific for global CDN)
```

The Flink job writes to Redis every 30 seconds. All API servers read from Redis. No direct computation on API request path.

## Interview Tips

Key points for this question:

1. **Velocity over volume** — the z-score approach is the insight that separates good answers from great ones
2. **Count-min sketch** — exact counting is impractical at this scale
3. **Sliding windows** — tumbling 30s windows + rolling merge
4. **Anti-spam** — always asked as a follow-up; weighted counts by account quality
5. **Geographic trending** — per-region CMS, language as location proxy

The most common mistake: designing a system that trends things with huge baseline volume (Super Bowl teams trending all year). Make sure your trending definition rewards velocity, not absolute count.

## Related Articles

- [Twitter/X Software Engineer Interview Guide](/blog/twitter-x-software-engineer-interview-guide)
- [System Design: Social Media Feed](/blog/system-design-social-media-feed)
- [System Design: Notification System](/blog/system-design-notification-system)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Distributed Cache](/blog/system-design-distributed-cache)
