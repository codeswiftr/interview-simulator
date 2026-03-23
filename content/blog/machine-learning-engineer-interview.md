---
title: "Machine Learning Engineer Interview Guide: ML System Design and Coding"
description: "Complete ML engineer interview preparation — ML system design (recommendation systems, fraud detection), coding interviews for ML roles, ML fundamentals asked in interviews, and how MLE interviews differ from SWE interviews."
date: "2026-03-20"
category: "Career Guides"
---

# Machine Learning Engineer Interview Guide: ML System Design and Coding

ML engineer interviews are hybrid: you need software engineering fundamentals (data structures, system design) plus ML fundamentals (training, inference, model lifecycle) plus ML system design (end-to-end systems). This guide covers all three.

## How MLE Interviews Differ from SWE Interviews

**Coding:** Same DSA content as SWE interviews — LeetCode-style problems. Some companies add Python-specific questions (list comprehensions, generators, numpy operations). A few ask ML-adjacent coding (implement k-means from scratch, implement a decision tree split criterion).

**ML fundamentals:** Questions about model training, evaluation, common algorithms, bias-variance tradeoff, regularization, feature engineering. Depth varies by company — research labs probe deeply, product ML roles care more about practical ML system knowledge.

**ML system design:** Design a recommendation system, a fraud detection system, a search ranking system. This is the differentiator for senior MLE roles. You need to cover the full lifecycle: data pipeline, feature engineering, training infrastructure, serving infrastructure, evaluation, monitoring.

## ML Fundamentals: What Gets Asked

**Bias-variance tradeoff:** High bias = underfitting (model too simple, can't capture patterns). High variance = overfitting (model memorizes training data, doesn't generalize). Regularization (L1/L2) reduces variance. Cross-validation diagnoses overfitting.

**Regularization:** L1 (Lasso) adds sum of absolute weights to loss — produces sparse models, sets some weights to exactly zero, effectively doing feature selection. L2 (Ridge) adds sum of squared weights — doesn't zero weights, distributes coefficient shrinkage. L1 when you suspect few features matter; L2 when all features may contribute.

**Gradient descent variants:** Batch GD uses all data per step (stable but slow). SGD uses one sample (noisy but fast). Mini-batch GD (standard in deep learning) uses a batch — balance of stability and speed. Adam combines momentum and adaptive learning rates — the de facto default optimizer.

**Evaluation metrics:** Know when to use which:
- Classification: Accuracy (good when classes balanced), Precision/Recall/F1 (imbalanced classes), AUC-ROC (ranking quality), PR-AUC (better for imbalanced classes than ROC)
- Regression: MAE (robust to outliers), MSE/RMSE (penalizes large errors), MAPE (relative error)
- Ranking: NDCG (normalized discounted cumulative gain), MAP (mean average precision)

**Class imbalance:** 99/1 split makes a model that always predicts 0 achieve 99% accuracy. Fixes: oversampling minority class (SMOTE), undersampling majority, class weights in loss function, changing threshold on probabilities, using precision/recall instead of accuracy as the success metric.

## ML System Design: Recommendation System

"Design YouTube's recommendation system" appears frequently. Framework:

**Problem definition:**
- Objective: maximize engagement (watch time), not clicks (leads to clickbait)
- Implicit feedback: watch completion rate, likes, shares
- Cold start: new users have no history, new videos have no interactions

**Data pipeline:**
- User events: watches, likes, shares, skips → streaming ingestion (Kafka) → feature store
- Video features: transcript, tags, category, upload time
- User features: demographics, watch history, subscription list

**Two-stage architecture (standard for scale):**

Stage 1 — Candidate generation: From millions of videos → hundreds of candidates. Techniques: collaborative filtering (matrix factorization, neural CF), content-based filtering (video embedding similarity), popularity-based (trending). This runs offline/near-real-time on precomputed embeddings.

Stage 2 — Ranking: From hundreds of candidates → top 50 to show. Uses heavier features: user-video interaction features, contextual features (time of day, device), predicted satisfaction signals. Uses a deep neural network trained on engagement labels. Runs per-request but on a small candidate set (fast enough for <100ms).

**Training infrastructure:**
- Daily batch retraining for collaborative filtering model
- Near-real-time updates for trending signals
- Shadow mode testing: new model runs alongside old, logs predictions without serving

**Serving:**
- User and video embeddings in ANN (approximate nearest neighbor) index (FAISS)
- Ranking model served via TensorFlow Serving or Triton
- Feature store (Redis for low-latency user features, precomputed offline features)

**Evaluation:**
- Offline: NDCG on held-out test set, AUC for click prediction
- Online: A/B test with primary metric (watch time/session), guardrail metrics (complaint rate, subscription cancellations)

## ML System Design: Fraud Detection

"Design a fraud detection system for a payment processor" tests real-time inference and the class imbalance problem.

Key challenges: extreme class imbalance (~0.1% fraud), adversarial users (adapt to your model), low latency (must score a transaction in <100ms), interpretability (need to explain why a transaction was flagged).

**Feature engineering:**
- Transaction features: amount, merchant category, time of day, card-present vs card-not-present
- Velocity features: # transactions in last 1min/10min/1hr, # unique merchants in last 24hrs
- Historical features: user's average transaction amount, typical locations, typical merchants
- Behavioral features: time since last transaction, deviation from typical patterns

**Model:**
- Gradient Boosted Trees (XGBoost, LightGBM): excellent for tabular fraud data, interpretable feature importances, fast inference, handles imbalanced data with class weights
- Threshold tuning: optimize for recall (catch more fraud) vs precision (fewer false positives) based on business requirements

**Real-time vs batch:**
- Real-time: velocity features computed in Redis (sliding window counters), model inference <50ms
- Batch: historical features computed daily, stored in feature store

**Feedback loop:**
- Disputed transactions → labeled fraud/not-fraud → feed back to training
- Chargeback data arrives weeks later — delayed labels require careful handling

## Python-Specific Coding Patterns

For MLE coding rounds, know numpy well:

```python
# Vectorized operations (fast, avoid Python loops)
a = np.array([1, 2, 3, 4])
b = a ** 2  # [1, 4, 9, 16] — vectorized

# Broadcasting
matrix = np.ones((3, 4))
row = np.array([1, 2, 3, 4])
result = matrix + row  # row broadcast across all 3 rows

# Efficient matrix multiplication
A = np.random.randn(100, 50)
B = np.random.randn(50, 30)
C = A @ B  # prefer over np.dot for clarity
```

Know pandas: groupby with aggregation, merge/join, handling missing values (fillna, dropna), apply for custom transformations.

## Model Monitoring in Production

Models degrade over time due to: data drift (input distribution shifts), concept drift (relationship between features and labels shifts), data quality issues (upstream pipeline changes).

Monitoring: track input feature distributions (KL divergence or statistical tests vs training distribution), model output distributions, and business metrics (click-through rate, revenue impact).

Alert on: sudden distribution shift, gradual drift over weeks, degradation in A/B test metrics. Response: investigate the drift, potentially retrain with recent data, investigate if adversarial behavior (in fraud) is causing the shift.

