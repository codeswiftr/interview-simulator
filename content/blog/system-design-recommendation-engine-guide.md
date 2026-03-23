---
title: "System Design: Recommendation Engine (Netflix/Spotify Architecture)"
description: "How to design a recommendation system in system design interviews — collaborative filtering, content-based filtering, candidate generation, scoring pipeline, and serving infrastructure."
date: "2026-03-20"
category: "System Design"
---

# System Design: Recommendation Engine (Netflix/Spotify Architecture)

Recommendation systems power some of the most impactful products in tech — Netflix reports that 80% of content watched is discovered through recommendations. Designing one in a system design interview tests your understanding of ML infrastructure, data pipelines, and low-latency serving. You don't need to be an ML engineer to answer this well, but you do need a clear mental model of the architecture.

## Clarifying the Problem

Before designing, ask: What are we recommending? (movies, songs, products) How many users and items? What signals do we have? (explicit ratings, implicit behavior like watch time, clicks) What are the latency requirements for serving recommendations?

For a Netflix-like system: 300 million users, 15,000 titles, and a requirement to serve personalized recommendations in under 100ms. This shapes every component of the design.

## The Two-Stage Pipeline: Retrieval and Ranking

Modern recommendation systems universally use a two-stage approach. This is the single most important conceptual framework to communicate clearly.

**Stage 1 — Candidate Retrieval**: Quickly narrow 15,000 items down to ~500 candidates relevant to this user. Speed is paramount; precision can be approximate. This stage uses lightweight models and approximate nearest neighbor (ANN) search.

**Stage 2 — Ranking and Scoring**: Take the ~500 candidates and rank them precisely using a more expensive model that incorporates rich features. This stage can afford higher latency because it operates on a small set.

This separation is why Netflix can serve personalized results in milliseconds despite having a complex ranking model — the expensive computation runs on a tiny candidate set.

## Retrieval Approaches

**Collaborative filtering** finds users similar to you (user-based CF) or items similar to what you've liked (item-based CF). The intuition: if Alice and Bob have watched 80% of the same movies and Bob loved *Interstellar*, recommend *Interstellar* to Alice. Computationally expensive at scale but highly effective.

**Matrix factorization** (the conceptual foundation behind most production CF) decomposes the user-item interaction matrix into user embeddings and item embeddings. Each user and item becomes a dense vector in a shared latent space. Recommendations become nearest-neighbor searches in that embedding space. Algorithms like ALS (Alternating Least Squares) and SVD are classic implementations; neural two-tower models are the modern production approach.

**Content-based filtering** uses item attributes (genre, director, actors, audio features for music) and matches them to a user's demonstrated preferences. Less prone to the cold start problem for new items — if you add a new thriller, it can be recommended to thriller fans immediately without any user interaction data.

**Two-tower neural models** are the current industry standard for retrieval. One tower encodes the user (from their history, demographics, context); the other encodes items. Both towers produce embeddings that are trained to place items the user will like close together in the embedding space. During inference, you fix all item embeddings and search for the K nearest neighbors to the user's embedding using ANN.

## Approximate Nearest Neighbor (ANN) Search

The item embedding space might contain millions of vectors. Exhaustive search (comparing the user embedding to every item embedding) is too slow. ANN libraries like **FAISS** (Facebook AI Similarity Search) and **ScaNN** (Google's Scalable Nearest Neighbors) use index structures (HNSW, IVF) to return approximate nearest neighbors in milliseconds with high recall.

In the interview, describe the flow: "We pre-compute embeddings for all items offline, index them in FAISS, and at serving time we compute the user embedding and run an ANN query to retrieve 500 candidates in ~10ms."

## Scoring and Ranking Pipeline

The ranking stage uses a more complex model (typically a deep neural network) that incorporates:
- User features: history, preferences, demographics, context (time of day, device)
- Item features: genre, popularity, recency, quality signals
- Cross-features: has the user watched similar items? How long ago?

The output is a relevance score for each candidate. Items are sorted by score, with optional business logic applied on top (e.g., diversity injection so you don't show 10 thrillers in a row, sponsored content placement, content license constraints by region).

## The Feature Store

Both retrieval and ranking models need features at serving time. A **feature store** provides low-latency access to precomputed features. Architecture: features are computed by batch jobs (daily or hourly) and stored in an offline store (S3, BigQuery). At serving time, features are fetched from an online store (Redis, DynamoDB) with sub-millisecond latency. The feature store ensures training and serving use the same feature computation logic — a critical correctness requirement.

## Batch vs. Real-Time Recommendations

**Batch recommendations** are precomputed offline. Every night, run the full recommendation pipeline for all users and store results in a key-value store. At request time, simply look up the user's precomputed list. Extremely fast to serve, but recommendations don't reflect very recent behavior (watched a movie 2 hours ago? Still showing it in your list).

**Real-time recommendations** incorporate the user's session context (what they've browsed in the last 5 minutes). The session signals feed into the user encoder in real-time, producing a fresh user embedding for each request. Higher latency and infrastructure cost, but dramatically better quality.

Most production systems use a hybrid: batch recommendations as a base, with real-time re-ranking based on session context. Describe this hybrid approach in your interview — it demonstrates practical thinking.

## Cold Start Problem

New users and new items have no interaction data. Standard approaches:

**New users**: Show popularity-based recommendations initially. After 3-5 interactions, transition to personalized recommendations. Some systems use an onboarding survey to gather explicit preferences.

**New items**: Content-based features allow immediate recommendation to relevant users. If Netflix adds a new sci-fi thriller, it can be recommended to sci-fi thriller fans the day it launches, before any watch data exists.

## A/B Testing Recommendations

Recommendation quality must be measured empirically. Run A/B tests by splitting users into control (current model) and treatment (new model) groups. Key metrics: click-through rate (CTR), completion rate (did they finish the content?), downstream engagement (did they return the next day?).

Be cautious about optimizing solely for CTR — "clickbait" thumbnails maximize CTR but hurt long-term retention. Netflix famously measures "did this recommendation lead to a satisfying viewing experience?" not just "did they click?"

## Common Interview Questions

**"How do you handle the cold start problem for new items?"** — Content-based features bridge the gap until interaction data accumulates. New items can also be shown to a small user segment for data collection.

**"What's your database choice for storing user interaction data?"** — Append-only event log (Kafka → S3/BigQuery for training data), Redis for real-time session features, DynamoDB for serving precomputed recommendations.

**"How do you prevent filter bubbles?"** — Diversity-aware ranking: explicitly penalize too-similar consecutive recommendations. Explore-exploit balancing (recommend some lower-confidence items to gather signal).

A strong recommendation system answer covers the two-stage pipeline, at least two retrieval approaches, the feature store, and cold start handling. The interviewer is testing whether you understand the separation between retrieval and ranking — that's the architectural insight that makes modern recommendation systems practical at scale.
