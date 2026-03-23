---
title: "Machine Learning in Production: Engineering Interviews for ML Infrastructure Roles"
description: "A deep dive into ML production engineering interview topics — feature stores, model serving architectures, drift detection, A/B testing for models, and the MLOps patterns that distinguish research ML from production ML."
date: "2026-03-20"
category: "System Design"
---

Machine learning interviews at companies running production ML systems are distinct from both pure algorithm interviews and traditional system design interviews. They live at the intersection: you need to understand ML concepts deeply enough to reason about operational failure modes, and you need software engineering depth to design the systems that keep models working reliably at scale.

This guide covers the production ML engineering topics that appear most frequently in senior and staff-level interviews at companies with mature ML platforms.

## The Feature Store: Why It Exists

A feature store is a centralized system for storing, computing, and serving machine learning features. Before feature stores existed, teams typically computed features in one of two ways: in batch pipelines that populated training datasets, or in online services at inference time. This bifurcation caused the most notorious category of ML production bugs: **training-serving skew**.

Training-serving skew occurs when the feature computation logic used during training differs from the logic used at inference time. A model trains on correctly computed features and learns accurate patterns, but at serving time the features are subtly different — a different time zone handling in a timestamp calculation, a different default for missing values, a different aggregation window. The model's predictions are wrong, often in ways that are hard to detect because the errors are consistent rather than catastrophically obvious.

A feature store solves this by maintaining a single implementation of feature computation logic used in both training and serving paths. Interview questions around feature stores probe:

- **Point-in-time correctness:** When you generate training data, you must be careful not to use feature values that weren't available at the time of the training label. If you're predicting whether a user will churn in the next week, and your feature "number of support tickets in last 30 days" is computed using data available today, you've introduced label leakage.

- **Dual storage:** Feature stores typically maintain both offline storage (data warehouse / data lake, for training) and online storage (low-latency key-value store, for inference). Keeping them synchronized is a core engineering challenge.

- **Feature freshness:** A feature computed on a batch schedule is stale by the time it's served. For real-time applications, streaming feature computation is required. The tradeoff between computation cost and feature freshness is a common design question.

## Model Serving Architecture

Model serving is the infrastructure that takes a trained model artifact and serves predictions over HTTP or gRPC at production scale.

**Batch vs. online serving:** Batch serving generates predictions for a large set of inputs in advance (e.g., overnight risk scores for all accounts) and stores them for lookup. Online serving generates predictions at request time. Online serving requires low latency (typically P99 < 100ms); batch serving can tolerate hours of latency but must handle large volumes.

**Model server options:** Frameworks like TensorFlow Serving, TorchServe, and Triton Inference Server handle the mechanics of loading model artifacts, batching requests for GPU efficiency, versioning models, and exposing prediction endpoints. A common interview question: "Why would you use Triton over a simple Flask wrapper around your model?" The answers: GPU batching, dynamic model loading, hardware optimization (CUDA graphs, TensorRT), and operational features like metrics and health checks.

**Hardware and batching:** GPUs are highly parallelizable but have high per-request overhead. Batching multiple inference requests together amortizes the overhead over many inputs. The optimal batch size is a function of model size, GPU memory, latency requirements, and request rate. Adaptive batching — accumulating requests up to a time threshold or size threshold and processing them together — is a standard pattern in production model servers.

**Shadow mode deployment:** A new model version receives a copy of production traffic but its predictions are not served to users. This allows evaluation of the new model's behavior under real traffic before making it live. Essential for catching edge cases not represented in offline evaluation sets.

## Drift Detection: Keeping Models Honest Over Time

Models trained on historical data degrade over time as the real-world distribution changes. This is called **drift**. There are two kinds:

**Data drift (covariate shift):** The distribution of input features changes. A fraud detection model trained in 2023 may see a different distribution of transaction amounts, devices, and merchant categories in 2026. The model's learned decision boundary may no longer be appropriate.

**Concept drift:** The relationship between features and labels changes. In a demand forecasting model, the relationship between historical sales and future sales may shift due to a competitor entering the market.

**Detection approaches:**

- **Statistical tests:** Compare the distribution of production features to the training distribution using tests like Population Stability Index (PSI), Kolmogorov-Smirnov test, or Chi-squared test for categorical features. High PSI (typically > 0.2) signals significant distribution shift.

- **Model performance monitoring:** Track ground-truth labels as they arrive and compare actual outcomes to predictions. Requires a system that joins prediction logs with delayed outcome labels.

- **Proxy metrics:** When ground truth is delayed (e.g., whether a loan defaults takes months to observe), use proxy metrics that correlate with model quality: prediction score distribution, rate of high-confidence predictions, feature value distributions.

## A/B Testing for ML Models

A/B testing ML models is more complex than A/B testing UI changes because:

**Interference effects:** In systems where model predictions affect user behavior (recommendation systems, pricing, ranking), users who see control and treatment simultaneously can create spillover effects that invalidate the experiment.

**Metric selection:** Online metrics (click rate, conversion) are noisy and may not capture model quality. Offline metrics (AUC, NDCG) don't always correlate with business outcomes. Choosing the right evaluation metric is a design decision with significant consequences.

**Causal validity:** Did the model change cause the metric change, or did something else happen during the experiment window? Proper holdout groups, experiment infrastructure, and statistical power calculations are required.

**Interleaving:** For ranking models (search, recommendations), interleaving both models' results in a single ranked list and measuring preference is more statistically efficient than separate A/B groups because variance is reduced. Spotify and Netflix use interleaving for recommendation model evaluation.

## MLOps Patterns

**Model registry:** A versioned catalog of trained model artifacts, with metadata (training data lineage, hyperparameters, evaluation metrics). Teams should be able to reproduce any previously deployed model and understand what changed between versions.

**Training pipelines:** Reproducible, automated pipelines for retraining models on new data. Key properties: deterministic (same inputs → same outputs), parameterized (training data window, hyperparameters configurable), and observable (logs, metrics, artifacts at each stage).

**Canary rollouts:** Deploy a new model version to a small fraction of traffic (1–5%), monitor metrics, and gradually increase the rollout percentage if metrics are healthy. Roll back automatically if error rate or latency exceed thresholds.

**Rollback capability:** Every production model deployment must have a fast rollback path. Rollback should take seconds, not require a new training run. This means keeping the previous model artifact live on standby.

## Common Interview Questions

"How would you detect that a deployed model's performance has degraded?" — Frame around the drift detection approaches above, distinguish between data drift and concept drift, and discuss what monitoring signals to build.

"Design a feature store for a real-time fraud detection system." — This is a demanding system design question that tests understanding of dual storage, point-in-time correctness, streaming computation, and the latency requirements of fraud detection (typically sub-100ms).

"How do you safely deploy a new model version to production?" — Shadow mode, canary rollout, interleaving, metric gates, and automated rollback are all relevant here.

The best ML production engineering candidates can reason about failure modes — not just how systems work when everything goes right, but what fails silently, what causes gradual degradation, and what monitoring catches problems before users are affected.
