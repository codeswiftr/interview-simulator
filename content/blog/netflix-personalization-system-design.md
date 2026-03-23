---
title: "Netflix Personalization System Design"
description: "A deep dive into Netflix's personalization architecture—homepage ranking, artwork personalization, recommendation algorithms, and the A/B testing infrastructure serving 270M subscribers."
date: "2026-03-21"
category: "System Design"
---

# Netflix Personalization System Design

Netflix's homepage is different for every subscriber. The rows you see, the order of titles within rows, even the artwork shown for each title—all personalized. This is a massive ML system serving 270 million subscribers across 190 countries. Understanding it prepares you for any personalization or recommendations system design interview.

## Scale and Context

- 270M subscribers
- 15,000+ titles in the catalog
- 80% of watched content comes from recommendations
- 1,300+ A/B tests running at any given time
- Homepage generates 600M events per hour

## Homepage Architecture

The Netflix homepage has two levels of personalization:

**Row selection and ordering**: Which rows appear (Trending, Continue Watching, Because You Watched X, Top Picks for You) and in what order.

**Row content and title ranking**: Within each row, which titles appear and in what order.

```
User Request → Homepage Service
                    ↓
              Ranking Service (row scores per user)
                    ↓
              Multiple Row Services (in parallel)
              ├─ Continue Watching Service
              ├─ Trending Service
              ├─ Personalized Recommendation Service
              └─ Row-specific services...
                    ↓
              Artwork Personalization Service
                    ↓
              Assembled Homepage Response
```

All downstream services are called in parallel, with a 200ms SLA. Missing a row degrades gracefully — the homepage renders with available rows.

## Recommendation Models

Netflix uses multiple models, each optimized for different scenarios:

**Collaborative Filtering (ALS/SVD++)**: Core personalization. Decomposes interaction matrix into user and item latent factors. Powers "Top Picks for You" and personalized ranking within genre rows.

**Because You Watched**: Item-to-item similarity. "You watched Stranger Things, so here's Dark." Uses embedding similarity on item-to-item co-watch patterns.

**Trending Now**: Combines global trending with personal affinity. Global trend score × user genre affinity score.

**Continue Watching**: Trivially personalized — your own watch history. Non-trivial part: ordering within the row (what to nudge you to finish first based on likelihood to re-engage).

## Feature Store

Personalization at this scale requires a unified feature store:

**User features (updated continuously)**:
- Watch history embeddings
- Ratings and thumbs up/down
- Genre affinity scores
- Time-of-day preferences (comedies on weeknights, documentaries on weekends)
- Device preferences
- Household composition signals

**Item features (updated daily)**:
- Genre, cast, director embeddings
- Engagement stats (completion rate, rewatch rate)
- Quality signals (human editorial ratings)
- Recency and trending scores

Netflix's offline feature store is backed by Apache Spark, online store by Cassandra + Redis. The two-tier approach: Cassandra for persistence, Redis for low-latency serving.

## Artwork Personalization

A unique Netflix innovation: the same title shows different artwork to different users. A user who watches lots of dramas sees the dramatic poster for "The Witcher"; a user who watches action sees an action-focused variant.

This is a multi-armed bandit problem per (user, title) pair. Each title has 10-30 artwork variants. The system learns which variant maximizes click probability for each user segment.

```
artwork_score = P(click | user_features, artwork_features)

Train on: impression events (which artwork was shown), click events
Model: logistic regression / contextual bandit
```

At 270M users × 15K titles, storing per-user artwork selection isn't feasible. Instead, cluster users into ~10K segments; serve artwork per segment.

## Two-Stage Personalization

Stage 1 — Candidate Generation (run offline/batch):
- Generate top-500 recommendations per user daily
- Store in Cassandra under user_id key
- Use multiple models, merge ranked lists

Stage 2 — Real-time Ranking (run online):
- Retrieve 500 candidates from Cassandra (~1ms)
- Re-rank with fresh contextual features (time of day, current session context)
- Score with a lightweight ranking model
- Return top-N per row

The offline step does heavy lifting; real-time step applies freshness without rebuilding from scratch.

## A/B Testing Infrastructure

Netflix's A/B testing is unusually sophisticated:

- **Cell-level allocation**: Each user is assigned a random cell ID (1-1000). New experiments allocate cells without overlap.
- **Long-running holdouts**: 5% of users are always in holdback (seeing previous experience) to measure long-term engagement effects.
- **Interleaving**: For ranking experiments, interleave items from two rankers in a single response, track which gets more engagement.

Primary metric: viewing hours. Secondary: member retention. Never optimize for pure clicks—maximizing clicks on clickbait titles would destroy long-term satisfaction.

## Cold Start

New subscribers:
1. Onboarding: select 3+ genres/titles they're interested in
2. Kickstart popular-in-your-genre recommendations immediately
3. After 5-10 views: transition to collaborative filtering
4. Full personalization: after 20-30 interactions

New titles (cold items):
- Use content features (genre, cast, plot summary embeddings) for content-based retrieval
- Editorial curated placement for launch ("New on Netflix" row)
- Collaborative filtering features available after 1-2 weeks of viewing data

## Infrastructure Numbers

To prepare for capacity questions:

- User feature retrieval: 270M users × 500B feature vectors = ~50TB feature store
- Artwork serving: 270M × request → Redis cache hit rate > 95%
- Candidate generation job: runs on 10,000+ Spark cores nightly
- Online ranking: 270M daily active sessions × 3 homepage loads = 810M ranking requests/day = ~9,400/second

## Interview Tips

Netflix personalization covers:
1. Multi-model ensemble (show breadth of algorithms)
2. Two-stage retrieval + ranking (show scalability thinking)
3. Artwork personalization with bandits (unique to Netflix, impressive depth)
4. A/B testing with long-term holdouts (shows product maturity)
5. Cold start (always asked)

Position yourself as understanding why multiple models exist (different signals, different latency budgets) rather than picking one "best" algorithm.

## Related Articles

- [Netflix Interview Guide](/blog/netflix-interview-guide)
- [System Design: Recommendation Engine](/blog/system-design-recommendation-engine)
- [System Design: Video Streaming](/blog/system-design-video-streaming)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Distributed Cache](/blog/system-design-distributed-cache)
