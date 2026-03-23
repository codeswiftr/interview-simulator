---
title: "Advanced ML System Design: Feature Stores, Model Serving, and Real-Time Inference"
description: "Senior ML system design interview preparation — feature store architecture, training-serving skew, online vs batch inference, model versioning, A/B testing frameworks, and designing production ML pipelines."
date: "2026-03-20"
category: "Machine Learning"
---

# Advanced ML System Design: Feature Stores, Model Serving, and Real-Time Inference

ML system design is a specialized domain that appears in senior ML engineer, MLOps, and tech lead interviews at ML-heavy companies. The questions test your ability to design end-to-end ML infrastructure — not just models, but the pipelines, feature systems, serving infrastructure, and evaluation frameworks that make ML work reliably in production.

## The Training-Serving Skew Problem

Training-serving skew is the number one cause of ML models performing worse in production than in offline evaluation. It occurs when the features used during training differ from the features available at serving time.

**Common causes**:
- Training uses batch-computed features; serving computes features differently in real-time
- Feature values are computed at different times relative to the prediction window
- Data preprocessing differs between training pipeline and serving pipeline

**The canonical example**: A fraud detection model trained on "time since last transaction" as a feature. In training, this is computed from historical data. In serving, this requires a real-time lookup of the user's last transaction. If the implementation differs (timezone handling, rounding), the feature values diverge.

**Solution: Feature Store**. The feature store is the infrastructure that ensures training and serving use identical feature computation logic.

## Feature Store Architecture

A feature store has two components:

**Offline store**: A data warehouse or data lake (BigQuery, Delta Lake, Hive) that stores historical feature values. Used for training dataset generation. Enables point-in-time correct feature retrieval — "what was the feature value at time T?" — critical for avoiding future data leakage.

**Online store**: A low-latency key-value store (Redis, DynamoDB, Cassandra) that serves features in real-time. Feature values are precomputed and written to the online store by feature pipelines. Lookups at serving time are O(1) Redis GETs rather than expensive computations.

**Feature pipelines**: Stream processing (Kafka + Flink) for real-time feature computation, or batch pipelines (Spark, dbt) for daily/hourly features. The same feature computation logic runs for both training data generation (offline) and online feature updates.

**Interview design**: "Design a feature store for a recommendation system with 10M users."
- Online store: Redis cluster with user embeddings and recent interaction features. Key = user_id, value = feature vector. TTL = 24 hours (refreshed by hourly pipeline).
- Offline store: BigQuery table with user_id, feature_name, value, timestamp. Supports point-in-time queries.
- Feature pipeline: Kafka consumer computing rolling aggregates (last 7 days of clicks, last 30 days of purchases) → writes to both Redis and BigQuery.

## Model Serving Architecture

**Batch inference**: Compute predictions offline for all entities and store results. Low latency at serving time (just a lookup), but predictions may be stale. Use for: recommendations precomputed nightly, risk scores computed daily.

**Real-time inference**: Model runs at request time. Fresh predictions, but adds latency. Use for: search ranking, fraud detection (must be real-time).

**Near-real-time inference**: Predictions computed asynchronously on recent events, available seconds to minutes later. Middle ground.

**Serving infrastructure**:
- **Triton Inference Server**: NVIDIA's production inference server. Supports TensorFlow, PyTorch, ONNX. GPU acceleration, batching, concurrent model execution.
- **TorchServe**: PyTorch's official model server. Easier setup for PyTorch models.
- **FastAPI + ONNX**: Lighter-weight for CPU models. Convert PyTorch/TF model to ONNX for runtime-agnostic serving.

**Model optimization for latency**:
- **Quantization**: Convert FP32 to INT8 or FP16. Reduces model size and speeds up inference with minimal accuracy loss.
- **Pruning**: Remove low-weight connections. Reduces model size.
- **Knowledge distillation**: Train a smaller "student" model to mimic a large "teacher" model. Preserves most accuracy at significantly lower latency.
- **ONNX runtime**: Optimized inference engine with graph optimizations.

## A/B Testing for ML Models

Never deploy a new model to 100% of traffic. Use staged rollout:

1. **Shadow mode**: New model runs in parallel with the current model, but its predictions are not served. Compare offline metrics.
2. **Canary**: Route 1-5% of traffic to the new model. Monitor business metrics (click-through rate, conversion, revenue per session) alongside ML metrics (NDCG, AUC).
3. **Full rollout**: Gradually increase traffic to the new model.

**Metric framework**:
- **Guardrail metrics**: Must not regress. Latency (p99 < 100ms), error rate (< 0.1%), revenue per session.
- **Primary metrics**: The business metric you're optimizing. Click-through rate, conversion rate.
- **Debug metrics**: Model-level metrics to understand behavior. Prediction distribution, feature importance shift.

**Statistical significance**: Use a two-sample t-test or Mann-Whitney U test for continuous metrics. Use chi-squared for conversion rates. Require p < 0.05 and a minimum detectable effect before declaring a winner. Size your experiment to detect the effect you care about.

## Model Versioning and Rollback

Models must be versioned like code:
- Version ID tied to training data snapshot, feature set, hyperparameters, and code commit
- Stored in a model registry (MLflow Model Registry, Weights & Biases, or a custom object storage path)
- Deployment metadata: who deployed, when, what traffic %, current evaluation metrics

**Rollback procedure**: When a deployed model degrades (guardrail metric breaches), automatically or manually rollback to the previous version. The model registry maintains the full history.

**Champion-challenger framework**: The "champion" is the currently serving model. "Challenger" models receive small traffic slices and compete against the champion. This creates continuous experimentation culture without disrupting production.

## ML Platform Design Questions

**"Design the ML platform for a company doing $1B in revenue, 5 ML teams, 50 models in production"**:

1. Unified feature store (Feast or custom) to eliminate training-serving skew
2. Centralized model registry (MLflow) for versioning and deployment tracking
3. Shared serving infrastructure (Triton Inference Server on Kubernetes) with autoscaling
4. Standardized experiment tracking (MLflow or W&B) for all teams
5. Automated retraining pipelines triggered by data drift detection (Evidently) or scheduled
6. A/B testing framework with built-in guardrail monitoring

The key insight for ML system design: models are not standalone artifacts. They're components of a data pipeline that requires the same reliability engineering as any production system — versioning, monitoring, rollback, and graceful degradation.
