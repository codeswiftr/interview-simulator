---
title: "System Design: Recommendation Engine"
description: "Design a recommendation system for a streaming or e-commerce platform — collaborative filtering, content-based filtering, two-tower models, feature stores, A/B testing, and the architecture behind Netflix/Spotify recommendations."
date: "2026-03-20"
category: "System Design"
---

# System Design: Recommendation Engine

Recommendation systems appear in senior engineer interviews at companies with personalization requirements — streaming platforms, e-commerce, social media, and marketplaces. This question tests your ability to bridge ML system design with traditional distributed systems. You don't need to implement ML algorithms, but you need to explain the overall architecture and the engineering decisions that make recommendations fast, fresh, and testable.

## Clarifying Requirements

Always clarify before designing:
- **Scale:** How many users? Items? DAU? (Netflix: 250M users, 10K+ titles)
- **Latency:** Real-time recommendations (<100ms) or batch pre-computed?
- **Freshness:** How quickly should new user behavior influence recommendations?
- **Cold start:** How do you handle new users or new items with no history?
- **Diversity:** Should recommendations be diverse (avoid repetition) or purely score-maximizing?

A reasonable baseline: 50M users, 5M items, <100ms recommendation latency, recommendations updated within 30 minutes of new interactions, handle cold start.

## High-Level Architecture

Recommendation systems typically have three phases:

1. **Candidate generation:** From millions of items, select thousands of candidates relevant to this user. Speed matters — must be very fast.
2. **Ranking:** Score the candidates using a more complex model. Runs on fewer items (thousands, not millions).
3. **Filtering and serving:** Apply business rules (no out-of-stock, no recently shown), diversity constraints, and serve the final list.

This two-tower funnel is the standard pattern at Netflix, Spotify, Amazon, and similar companies.

## Candidate Generation

**Collaborative filtering:** "Users similar to you liked these items." Offline computation using matrix factorization (ALS, SVD) produces user embeddings and item embeddings. At serving time, compute nearest neighbors in embedding space using approximate nearest neighbor (ANN) search.

**Content-based filtering:** "Because you watched this thriller, here are similar thrillers." Item embeddings based on features (genre, actors, director) rather than user behavior. Works for new items (solves cold start for items).

**Pre-computed candidates:** For most users, compute top-1000 candidates offline every 30 minutes. Store in a key-value store (Redis/DynamoDB) keyed by user ID. At request time, look up candidates instantly — no ML inference in the hot path.

**Real-time candidates:** For very fresh behavior (user just watched 3 thrillers in a row), generate real-time candidates using session-based models. Merged with pre-computed candidates at ranking time.

## Embedding Store and ANN Index

User and item embeddings (typically 64-256 dimensional float vectors) are stored in:
- **Vector store:** Pinecone, Weaviate, or a self-hosted FAISS index
- **Approximate nearest neighbor:** HNSW (Hierarchical Navigable Small World) or IVF-PQ for fast nearest-neighbor lookup in high dimensions

At scale, exact nearest-neighbor search across millions of items is O(n × d) per query — too slow. ANN trades recall for speed, retrieving approximate top-K neighbors in O(log n). Acceptable for recommendations (99% recall is fine; you don't need perfect results).

## Ranking Model

The ranking model takes the ~1000 candidates and produces a ranked score per item. Features:
- User features: age, location, subscription tier, device type, historical preferences
- Item features: genre, release date, popularity, production quality
- Interaction features: cross between user and item (has user watched this genre before? How long ago?)
- Context features: time of day, day of week, session length

The model is typically a neural network trained on click/watch/purchase signal. At serving time, the feature vector for each (user, item) pair is assembled from a feature store and scored by the model.

**Feature store:** Serves pre-computed user and item features at low latency. Offline (batch) features are pre-computed and stored in Redis/DynamoDB. Real-time features (what the user did in this session) are computed on-the-fly from an event stream. Feast and Tecton are common feature store solutions.

## Cold Start Problem

**New users:** Fall back to popularity-based recommendations (what's trending in their region, top-rated in a category). As the user generates behavior, gradually blend personalized recommendations in. After 5-10 interactions, personalization kicks in.

**New items:** Use content-based features to generate item embeddings. Surface new items to a test cohort to gather interaction data, then incorporate into collaborative filtering.

## Serving Architecture

```
Request → Load Balancer → Recommendation Service
                                ↓
                    [Retrieve pre-computed candidates from Redis]
                    [Fetch real-time session features]
                    [Ranking model inference (GPU or CPU)]
                    [Apply diversity + business rules]
                    [Return top-N with scores]
```

Latency budget: candidate retrieval from Redis ~5ms, feature assembly ~10ms, ranking inference ~30ms, filtering ~5ms. Total p95 <100ms.

**Caching:** The final ranked list can be cached per user for 5-10 minutes. This trades freshness for latency, acceptable for most recommendation surfaces.

## A/B Testing

Recommendation systems require continuous experimentation. Design:
- Random bucket users into control and treatment groups (user ID hash mod N)
- Expose different models or ranking weights to different buckets
- Collect click-through rate, conversion, and watch-time metrics per bucket
- Statistical significance testing before shipping winners

Infrastructure: experiment configuration store (feature flags service), metric collection pipeline (event stream → aggregation → dashboard), and experiment analysis service.

## Feedback Loop and Training

The ML models are retrained periodically (daily or weekly) on logged interaction data. The training pipeline:

1. Raw events (clicks, watches, skips) → Kafka → Spark/Flink processing → training dataset
2. Feature engineering in batch → feature store update
3. Model training on GPU cluster → model evaluation
4. Shadow mode deployment → A/B test → full rollout

Watch for: position bias (users click top results regardless of quality), popularity bias (popular items dominate training data). Address with inverse propensity scoring and exploration (occasionally surface non-obvious items).

## Monitoring

Key metrics: recommendation coverage (% of items ever recommended), click-through rate, conversion rate, diversity score (intra-list similarity), and latency percentiles. Alert on CTR drops (model degradation) and latency spikes (ANN index or feature store issues).

## Related Articles

- [Netflix Personalization System Design](/blog/netflix-personalization-system-design)
- [System Design: Social Media Feed](/blog/system-design-social-media-feed)
- [System Design: Search Engine](/blog/system-design-search-engine)
- [The Complete System Design Interview Guide](/blog/system-design-interview-guide)
- [System Design: Distributed Cache](/blog/system-design-distributed-cache)
