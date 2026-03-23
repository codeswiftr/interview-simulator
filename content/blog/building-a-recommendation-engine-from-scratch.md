---
title: "Building a Recommendation Engine from Scratch"
description: "A practical guide to recommendation system design—collaborative filtering, content-based models, two-tower neural networks, and real-time serving infrastructure used by Netflix, Spotify, and Amazon."
date: "2026-03-21"
category: "System Design"
---

# Building a Recommendation Engine from Scratch

Recommendation systems power a disproportionate share of revenue at tech companies. Netflix attributes 80% of hours watched to recommendations. Amazon claims 35% of revenue from its recommendation engine. Building one from scratch in an interview demonstrates ML system design fluency that separates senior from principal candidates.

## Problem Framing

Before algorithms, nail the problem statement:

- **Objective**: maximize long-term engagement (not just click-through rate)
- **Constraints**: fresh content needs cold-start handling; latency < 100ms for UI
- **Feedback signals**: explicit (ratings, thumbs) and implicit (watch time, skips, shares)

## Recommendation Approaches

### Collaborative Filtering

"Users like you also liked X." Two variants:

**Memory-based**: find similar users or items using cosine similarity on the interaction matrix. Simple, interpretable, but doesn't scale to millions of users.

**Model-based (Matrix Factorization)**: decompose the user-item interaction matrix into latent factor vectors.

```
R ≈ U × Vᵀ

Where:
R[u][i] = predicted rating by user u for item i
U = user latent factors (users × k)
V = item latent factors (items × k)
```

Use ALS (Alternating Least Squares) or SGD to learn U and V. This is what early Netflix Prize solutions used. k=50–200 factors work well in practice.

**Pros**: captures hidden preference patterns, handles sparse data well
**Cons**: cold-start problem for new users/items

### Content-Based Filtering

"You liked action movies, so here's another action movie." Build item feature vectors from metadata (genre, actors, description embeddings) and match against user preference profiles.

```python
# Item embedding from metadata
item_vector = concatenate([
    genre_embedding,
    director_embedding,
    tfidf(description),
    popularity_features
])

# User profile = weighted average of interacted items
user_profile = weighted_mean(
    [item_vector for item in user_history],
    weights=[interaction_strength]
)

# Score = cosine similarity
score = cosine_similarity(user_profile, candidate_item)
```

**Pros**: works for new users (only needs initial interaction), transparent
**Cons**: filter bubble — only recommends more of what you've already seen

### Two-Tower Neural Networks

The modern standard (used by YouTube, TikTok, Twitter). Two separate networks:

- **Query tower**: encodes user context (user features + recent history + session context)
- **Item tower**: encodes item features (content, metadata, engagement stats)

Both towers output a fixed-dimension embedding. Score = dot product of embeddings.

```
User Features → [Query Tower] → user_embedding (128-dim)
Item Features → [Item Tower]  → item_embedding (128-dim)

score = dot(user_embedding, item_embedding)
```

The key insight: item embeddings can be pre-computed offline. At serving time, only the query tower runs in real-time. Nearest-neighbor search over pre-computed item embeddings is fast.

Train with contrastive learning: positive pairs (user interacted) scored higher than negative pairs (sampled non-interactions).

## Retrieval vs. Ranking

Production systems are two-stage:

**Stage 1 — Retrieval (Candidate Generation)**: Narrow billions of items to ~1000 candidates. Must be fast (< 10ms). Use ANN (Approximate Nearest Neighbor) search like FAISS or ScaNN over item embeddings. Retrieval recall @ 1000 should be > 90%.

**Stage 2 — Ranking**: Score the 1000 candidates with a heavier model (gradient-boosted trees or deep neural net). Can use user context, item features, cross-features, and real-time signals. Output: ranked list of ~100 items.

**Optional Stage 3 — Re-ranking**: Business rules, diversity injection, sponsored content integration.

## Feature Engineering

What features matter:

**User features**: demographics, historical preferences, session context (what they just watched), time of day, device type

**Item features**: content metadata, engagement statistics (CTR, completion rate, likes/dislikes), freshness

**Cross features**: `user_genre_affinity × item_genre`, `user_avg_watch_time × item_duration`

**Real-time features**: currently trending, friends just watched (if social), contextual banners

## Cold-Start Problem

New users have no history. Solutions:

1. **Onboarding survey**: ask 3-5 preference questions at signup
2. **Popularity fallback**: show globally popular or trending content
3. **Exploration**: ε-greedy or UCB bandit — show diverse content, observe which gets engagement
4. **Context signals**: infer from device, referrer, time of day

New items (cold items): use content-based retrieval until enough interaction data exists to learn quality factors.

## Infrastructure

```
Offline (daily batch):
  - Train/retrain two-tower model
  - Compute and index all item embeddings → FAISS index
  - Pre-compute user embeddings for known users

Online (real-time):
  - Query tower forward pass (< 5ms)
  - ANN search in FAISS index (< 10ms)
  - Ranking model inference over candidates (< 50ms)
  - Re-ranking and assembly (< 10ms)
  - Total: < 80ms
```

## A/B Testing and Metrics

**Proxy metrics (online)**: CTR, watch completion rate, session length
**North star metrics (long-term)**: weekly active users, retention, subscriber renewal rate

Run interleaving experiments for faster convergence — mix items from two rankers per request, track which gets more engagement. 10x more power than traditional A/B tests.

Watch for **feedback loops**: if the model only serves what it already knows users like, you starve new content and lock users into filter bubbles. Inject exploration (10-20% of slots) and monitor catalog coverage.

## Interview Strategy

1. Clarify implicit vs explicit feedback and objective function
2. Sketch the two-stage pipeline (retrieval + ranking)
3. Describe two-tower architecture and why it enables fast serving
4. Address cold-start explicitly — interviewers always ask
5. Discuss A/B testing and feedback loop risks

This scope covers system design, ML model design, and data engineering — show depth in at least one area while demonstrating breadth across all three.
