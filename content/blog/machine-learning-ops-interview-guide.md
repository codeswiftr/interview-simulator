---
title: "MLOps Interview Guide: Model Deployment, Feature Stores, and ML Infrastructure"
description: "What MLOps engineer interviews test — CI/CD for ML, feature store design, model registry, serving infrastructure, monitoring drift, and how to answer MLOps system design questions."
date: "2026-03-20"
category: "Specialty Role Interviews"
---

# MLOps Interview Guide: Model Deployment, Feature Stores, and ML Infrastructure

MLOps has emerged as a distinct engineering discipline with its own interview patterns. Companies like Uber, Airbnb, Netflix, Lyft, DoorDash, and Databricks have dedicated MLOps teams, and the role bridges machine learning engineering and platform engineering in specific ways. This guide covers what MLOps interviews actually test.

## MLOps Engineer vs MLE vs Data Engineer

Understanding the scope distinction matters:

**Machine Learning Engineer (MLE):** Focuses on model training, feature engineering, and improving model performance. Primarily cares about the ML artifact (the model) and offline metrics.

**MLOps Engineer:** Owns the infrastructure that lets ML engineers do their work at scale — CI/CD pipelines for models, feature stores, model registry, serving infrastructure, monitoring. Closer to platform engineering but specialized for ML workloads.

**Data Engineer:** Owns data pipelines, warehouses, and data quality. MLOps engineers consume their infrastructure but typically don't build it.

MLOps interviews test both the ML system understanding (you need enough to design infrastructure for it) and platform/infrastructure skills (you're building production systems).

## Core Interview Areas

### Feature Store Design

Feature stores solve the "training-serving skew" problem — ensuring that features computed offline for training match features computed online for inference.

**What interviewers test:**
- Online vs offline feature serving (Redis/DynamoDB for online low-latency lookups, Parquet/Delta Lake for offline batch training)
- Point-in-time correctness: features computed for training must reflect what was known at the time of the label, not future data
- Feature versioning and lineage

**Sample question:** "How would you design a feature store for a fraud detection model that needs to serve features in <10ms at 10K QPS?"

Strong answer: Two-tier architecture — offline feature pipeline writes precomputed features to object storage for training; for real-time inference, a streaming processor (Flink/Kafka Streams) materializes features into Redis with TTL. Feature definitions are versioned in a registry. Point-in-time correctness enforced by storing features with timestamps and doing time-travel joins during training data generation.

### ML CI/CD Pipeline

**What interviewers test:**
- Triggering training runs (on schedule, on new data, on code change)
- Automated validation before deployment (performance thresholds, data distribution checks, latency tests)
- Model versioning and rollback
- Shadow mode and canary deployments for models

**Sample question:** "Design a CI/CD pipeline for a ranking model that retrains daily."

Strong answer: Data validation → feature pipeline → training job (with experiment tracking in MLflow) → automated evaluation (offline metrics vs baseline + previous model) → staging deployment → shadow mode comparison vs production model → gradual rollout with A/B test → monitoring dashboards.

### Model Serving Architecture

**Batch serving:** Precompute predictions offline, store results. Low latency at request time, high throughput, but predictions can be stale. Good for recommendation pre-generation.

**Online serving:** Real-time inference at request time. Fresh predictions, more compute cost. Good for fraud detection, search ranking.

**Two-stage serving:** Cheap retrieval model (fast ANN search over embeddings) → expensive re-ranking model (full feature set, higher latency). Balances latency and quality.

**Serving infrastructure considerations:**
- Model artifact loading: containerized serving (TorchServe, TensorFlow Serving, Triton)
- Hardware: GPU vs CPU inference, batching strategies
- Caching: prediction caching for repeated inputs
- Autoscaling: GPU instances are expensive, scale to zero when idle

### Model Monitoring

This is where many ML systems fail in production. Interviewers want to see you think about monitoring proactively.

**Data drift:** Input feature distributions shift over time. User behavior changes, population shifts, data pipeline changes. Detect with statistical tests (KS test, Population Stability Index).

**Concept drift:** The relationship between features and labels changes — the model is fit to old patterns. Detect by monitoring prediction distributions and (where available) delayed labels.

**Model performance degradation:** Track business metrics (CTR, conversion, fraud recall) and ML metrics (AUC, precision@K) over time. Alert when they fall below threshold.

**Alerting strategy:** Don't alert on every fluctuation. Use control charts, Bayesian change-point detection, or simple exponential smoothing to detect sustained shifts vs noise.

## MLOps Tooling You Should Know

**Experiment tracking:** MLflow, W&B (Weights & Biases), Comet ML
**Feature store:** Feast (open source), Tecton (commercial), Hopsworks
**Model registry:** MLflow Model Registry, SageMaker Model Registry
**Pipeline orchestration:** Airflow (general), Kubeflow Pipelines (K8s native), Metaflow (Netflix), Prefect
**Model serving:** TorchServe, TensorFlow Serving, BentoML, Seldon Core, Ray Serve
**Data validation:** Great Expectations, Deequ
**Monitoring:** Evidently AI, WhyLabs, Arize AI

You don't need to have used all of these, but knowing the categories and representative tools signals that you understand the problem space.

## Common Interview Questions

**Q: How do you handle model versioning and rollback?**
Store all models in a versioned model registry with their training metadata, evaluation metrics, and serving configuration. Tag production models explicitly. For rollback, change the production pointer to the previous model version — should take <1 minute. Maintain at least 3 versions in registry before GC.

**Q: Your model's precision dropped from 95% to 80% over 6 months. What do you investigate?**
First check monitoring dashboards: input feature distributions (data drift), label distribution, and business metrics. Check if any recent data pipeline changes correlate with the drop. If data drift is detected, diagnose which features drifted and why (upstream system change, seasonal effect, etc.). Options: retrain on more recent data, update feature computation, add drift detection as a trigger for automatic retraining.

**Q: How do you deploy a model without downtime?**
Blue-green deployment: spin up new model serving containers alongside existing ones, shift traffic gradually (10% → 50% → 100%), rollback if metrics degrade. With Kubernetes, this is a standard rolling update. For online feature serving, preload new feature versions before model switch.
