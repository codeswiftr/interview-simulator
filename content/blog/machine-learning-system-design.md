---
title: "Machine Learning System Design: Feature Stores, Model Serving, and ML Pipelines"
description: "ML system design for engineering interviews — feature stores, online vs. offline inference, model versioning, A/B testing, data pipelines, and designing recommendation systems."
date: "2026-03-20"
category: "System Design"
---

# Machine Learning System Design: Feature Stores, Model Serving, and ML Pipelines

ML system design questions appear in senior engineering interviews at companies with significant ML infrastructure. Unlike pure algorithm questions, these test whether you understand how ML integrates with production systems — data pipelines, serving infrastructure, monitoring, and feedback loops. Here's the framework and the key concepts.

## The ML System Design Framework

For any ML system design question, cover these layers:

1. **Problem framing** — what are you predicting? What's the objective function?
2. **Data pipeline** — how is training data collected, processed, and served?
3. **Feature engineering** — what features, how computed, where stored?
4. **Model training** — offline batch, online learning, or hybrid?
5. **Model serving** — how are predictions served? Latency requirements?
6. **Feedback and evaluation** — how do you know the model is working?

## Feature Stores

A feature store is a centralized system for storing, computing, and serving ML features. It solves the training-serving skew problem: features computed identically during training and serving.

**Two access patterns:**
- **Offline store** (batch): Historical features for model training. Stored in a data warehouse (BigQuery, Redshift, Delta Lake). Time-travel semantics critical — you must reconstruct features as they existed at any past timestamp for accurate training.
- **Online store** (real-time): Latest feature values for serving. Stored in a low-latency key-value store (Redis, DynamoDB). Features are precomputed and written here by streaming jobs.

**Training-serving skew** is the most common ML production bug: the feature computation logic differs between training and serving, causing the model to see different distributions at inference time. Feature stores solve this by centralizing the computation logic.

Systems like Feast, Tecton, and Databricks Feature Store implement this pattern. Interview question: "Why do you need a feature store? Can't you just compute features at request time?" Answer: you can, but you'll duplicate computation logic and risk skew. Feature stores separate feature computation from model training and serving, enabling reuse across models and teams.

## Online vs. Offline Inference

**Offline (batch) inference:** Compute predictions for all users/items periodically (hourly, daily), store in a database, serve from there. Advantages: cheap, can use complex models with high latency. Disadvantages: stale predictions, can't react to real-time context.

Use batch inference for: email recommendation, weekly reports, cases where prediction can be precomputed.

**Online (real-time) inference:** Compute predictions at request time. Advantages: uses latest context, can personalize based on current behavior. Disadvantages: latency requirements constrain model complexity, scaling is harder.

Use online inference for: real-time recommendations (Netflix home page), fraud detection (must decide in milliseconds), search ranking.

**Hybrid:** Batch + online. Compute heavy features offline, combine with lightweight real-time features at serving time. Common pattern: offline-computed user embeddings + real-time context features fed to a lightweight scoring model.

## Model Serving Infrastructure

**Model versioning:** Each trained model gets an immutable version identifier. Serving infrastructure routes traffic to versions. Enable rollback by pointing traffic back to the previous version.

**Shadow deployment:** New model version receives a copy of production traffic but responses are discarded. Lets you compare predictions and latency before routing real traffic.

**A/B testing:** Split traffic between models. Measure business metrics (CTR, conversion, revenue) over a statistically significant sample. Don't just measure model metrics (AUC, accuracy) — measure downstream business impact.

**Canary deployment:** Route 5% of traffic to new model, monitor for errors and degraded metrics, gradually increase to 100%.

**Serving latency:** P99 latency matters more than average. Identify your SLA (50ms, 200ms, 1s) and architect accordingly. If the model is too slow: simplify the model, precompute features, add caching for repeated inputs, or move to batch.

## Data Pipelines and Training Infrastructure

**Training data pipeline:** Raw events → feature computation → training dataset. Must be reproducible: given a timestamp, you should be able to reconstruct the training dataset exactly. Use point-in-time correct joins in your feature store.

**Data validation:** Validate schema (expected columns, types), data quality (nulls, outliers), and distribution shift (new data distribution matches training assumptions). Great Expectations and TFX Data Validation are common tools.

**Feedback loops:** Production predictions should feed back into training data. Log the prediction, the context (features), and eventually the outcome (did the user click? was the transaction fraudulent?). This feedback loop is critical for model improvement.

**Label delays:** The time between prediction and observing the outcome. Fraud labels may arrive days later. This affects training data freshness and requires careful windowing.

## Designing a Recommendation System

The canonical ML system design question. Key components:

**Candidate generation:** Narrow millions of items to hundreds of candidates. Use approximate nearest neighbor search (FAISS, ScaNN) on embeddings. Two-tower model (user embedding + item embedding) is standard.

**Ranking:** Score and rank the candidates. More expensive model with richer features. Optimize for click-through rate (CTR), conversion, or a composite business metric.

**Exploration vs. exploitation:** Pure exploitation (always show highest-scored items) leads to filter bubbles. Epsilon-greedy, UCB, or contextual bandits introduce exploration to discover new relevant content.

**Feature freshness:** Real-time behavior (last 5 clicks) is highly predictive but requires streaming feature computation. Balance freshness with serving latency.

## Model Monitoring

Models decay as the world changes (concept drift) and as input distributions shift (data drift). Monitor:
- **Data drift:** Distribution of input features over time
- **Prediction drift:** Distribution of model outputs
- **Business metrics:** CTR, conversion, revenue — the ground truth
- **Label feedback rate:** Are outcome labels arriving as expected?

Alert when metrics drift beyond thresholds; trigger retraining or rollback. This operational loop — monitor, detect, retrain, evaluate, deploy — is the continuous improvement cycle that keeps ML systems valuable.
