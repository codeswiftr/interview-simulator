---
title: "ML Infrastructure Engineer Interview Guide: MLOps, Feature Stores, and ML Systems"
description: "Complete guide to ML infrastructure engineering interviews — MLOps pipelines, feature stores, model serving, experiment tracking, model monitoring, and interview questions for ML platform roles."
date: "2026-03-20"
category: "Technical Skills Guides"
---

# ML Infrastructure Engineer Interview Guide: MLOps, Features Stores, and ML Systems

ML infrastructure engineering (MLOps) is one of the fastest-growing engineering specializations. As companies scale from ML experiments to production ML systems, the need for engineers who can build reliable, reproducible, and scalable ML infrastructure has exploded. Roles at ML-heavy companies (Google, Meta, Netflix, Uber) and AI-native startups increasingly look for this specialization. Here's what these interviews test.

## The ML Lifecycle and Where Infrastructure Fits

ML infrastructure engineers build the systems that support the entire ML lifecycle:

1. **Data ingestion and feature engineering** — Getting data into a usable form
2. **Feature storage** — Making features available for training and serving consistently
3. **Experiment tracking** — Logging parameters, metrics, and artifacts across model iterations
4. **Training pipelines** — Orchestrating reproducible model training
5. **Model registry** — Versioning, staging, and promoting models
6. **Model serving** — Deploying models and making predictions at scale
7. **Model monitoring** — Detecting drift, degradation, and data quality issues in production

Interviewers probe each area. Know which part of the lifecycle each tool addresses.

## Feature Stores: Why They Exist and How They Work

Feature stores are one of the most commonly discussed ML infrastructure topics in interviews.

**The problem they solve:**
Without a feature store, ML teams recalculate the same features multiple times (each team builds their own user activity features), training and serving compute features differently causing training-serving skew, and there's no central catalog of available features.

**Feature store architecture:**
- **Offline store** — Low-cost, high-capacity storage (S3, GCS, Hive) for historical feature values. Used for training data generation. Batch access, minutes to hours latency acceptable.
- **Online store** — Low-latency key-value store (Redis, DynamoDB, Bigtable) for real-time feature retrieval during serving. Sub-millisecond access required.
- **Feature pipeline** — Computes feature values from raw data and writes to both offline and online stores. Batch pipelines (Spark) for historical data; streaming pipelines (Kafka + Flink) for real-time features.

**Point-in-time correctness:** When generating training data, you must join features with their values at the time of the label event — not their current values. This prevents data leakage. Most production feature stores implement point-in-time joins for this reason.

**Popular tools:** Feast (open source), Tecton, Hopsworks, AWS SageMaker Feature Store, Vertex AI Feature Store.

## Experiment Tracking

**MLflow:** The most widely used open-source experiment tracking tool. Logs: parameters (hyperparameters), metrics (loss, accuracy, F1), artifacts (model files, plots). Provides UI for comparing experiments, and MLflow Models for model packaging.

**Weights & Biases (W&B):** Cloud-hosted experiment tracking with richer visualizations, team collaboration features, and sweep (hyperparameter optimization) support. Common at companies that invest heavily in ML research.

**Key concepts for interviews:**
- **Runs, experiments, projects** — Hierarchy of tracking
- **Model registry:** Transition models through staging → production lifecycle; MLflow, W&B, and SageMaker all have model registry components
- **Artifact versioning:** Not just model weights, but feature transformation code, preprocessing pipelines, and training data versions must be captured for reproducibility

## Training Pipeline Orchestration

**Kubeflow Pipelines:** Kubernetes-native ML workflow orchestration. Define pipelines as Python code using the KFP SDK; each step runs as a Kubernetes pod. Good for teams already on Kubernetes.

**Airflow for ML:** General-purpose workflow orchestration often used for ML pipelines, especially when pipelines include non-ML steps (data ingestion, validation). Familiar to data engineers. Less ML-specific than Kubeflow.

**Metaflow:** Netflix's open-source framework for ML workflows. Emphasizes developer productivity — define ML steps as Python functions, Metaflow handles infrastructure (S3 for artifacts, AWS Batch for scaling).

**Interview question:** "How would you design a reproducible model training pipeline?"
Strong answer covers: versioned input data, pinned dependency environments (Docker, conda), tracked hyperparameters, model artifact storage with versioning, idempotent pipeline steps, and automated testing of the pipeline itself.

## Model Serving Architecture

**Batch inference:** Process a batch of examples offline, store predictions. Simple, cheap, no latency requirements. Used for: recommendations generated nightly, risk scores updated hourly.

**Real-time inference:** Serve predictions on-demand via an API. Latency requirements (p99 < 100ms for user-facing). Options: ONNX Runtime, TensorFlow Serving, TorchServe, Triton Inference Server (NVIDIA), Seldon Core.

**Inference optimization:**
- **Quantization** — Reduce model precision (float32 → int8); 4x smaller model, 2-4x faster inference, small accuracy loss
- **Pruning** — Remove low-importance weights
- **Model distillation** — Train a smaller student model to mimic a larger teacher
- **Batching** — Process multiple requests together for throughput (latency tradeoff)

**The shadow deployment pattern:** Run new model alongside current model; route all traffic to current, log predictions from both, compare offline. Zero user impact during validation.

**A/B testing models:** Route X% of traffic to new model, compare business metrics (CTR, conversion) not just ML metrics (accuracy). Business impact is the ultimate validation.

## Model Monitoring

The production ML lifecycle doesn't end at deployment — models degrade over time.

**Types of drift:**
- **Data drift** — Input feature distribution shifts from training distribution (e.g., user behavior changes post-COVID)
- **Label drift** — Target variable distribution shifts
- **Concept drift** — The relationship between inputs and outputs changes (the model's learned patterns no longer hold)

**Detection methods:**
Statistical tests comparing current feature distributions to training baseline: KS test (continuous features), chi-squared (categorical). Population Stability Index (PSI) for comparing distributions.

**Monitoring stack:** Evidently AI, Arize AI, Fiddler AI, WhyLabs — specialized model monitoring platforms. Or custom pipelines computing distribution statistics and logging to Grafana/Prometheus.

**Interview scenario:** "Your recommendation model's click-through rate dropped 20% overnight. Walk me through investigation."
Expected answer: check data pipeline (is feature data still flowing correctly?), check model serving (are predictions being generated? any errors?), check feature drift (did input distributions change?), check label/feedback data (is the CTR measurement pipeline correct?), check business context (any external events that could explain behavior change?).

MLOps interviews reward candidates who understand the full production lifecycle — not just training models but operating them reliably at scale, detecting degradation early, and maintaining reproducibility across the model iteration cycle.
