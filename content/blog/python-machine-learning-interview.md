---
title: "Python Machine Learning Interview Guide: scikit-learn, PyTorch, and ML System Design"
description: "Senior ML engineer interview preparation — scikit-learn pipelines, PyTorch model training, ML system design patterns, feature engineering, model evaluation, and production deployment considerations."
date: "2026-03-20"
category: "Machine Learning"
---

# Python Machine Learning Interview Guide: scikit-learn, PyTorch, and ML System Design

Machine learning engineering interviews blend classical algorithms, Python ML libraries, statistical understanding, and system design. This guide covers the technical depth required for senior ML engineer roles — not just theory, but the practical engineering knowledge that separates ML engineers from data scientists.

## Core ML Concepts for Interviews

**Bias-variance tradeoff**: High bias = underfitting (model too simple, high training error). High variance = overfitting (model memorizes training data, poor generalization). Regularization (L1/L2) reduces variance by penalizing complexity. Ensemble methods (bagging, boosting) reduce variance and bias respectively.

**Cross-validation**: K-fold CV estimates generalization performance. Split data into K folds; train on K-1, validate on 1; rotate. Stratified K-fold preserves class proportions. Don't use cross-validation naively with time-series data — use time-based splits (train on past, validate on future).

**Evaluation metrics**:
- **Classification**: Accuracy (misleading for imbalanced classes), precision/recall trade-off (F1 balances both), AUC-ROC (discrimination ability across thresholds), AUC-PR (better for imbalanced classes).
- **Regression**: MAE (mean absolute error — robust to outliers), RMSE (penalizes large errors more), R² (proportion of variance explained).

**Feature engineering**: Normalization (StandardScaler, MinMaxScaler) for gradient-based models. Categorical encoding: one-hot for low-cardinality, target encoding for high-cardinality (use carefully to avoid target leakage). Interaction features for tree models. Log transforms for skewed distributions.

## scikit-learn Patterns

**Pipeline**: Combines preprocessing and model into a single object. Prevents data leakage by ensuring transformers are fit only on training data.

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('classifier', LogisticRegression(max_iter=1000))
])

param_grid = {'classifier__C': [0.01, 0.1, 1, 10]}
search = GridSearchCV(pipeline, param_grid, cv=5, scoring='f1')
search.fit(X_train, y_train)
```

**ColumnTransformer**: Apply different preprocessing to different feature types:
```python
from sklearn.compose import ColumnTransformer

preprocessor = ColumnTransformer([
    ('num', StandardScaler(), numeric_features),
    ('cat', OneHotEncoder(), categorical_features)
])
```

**Interview question**: "Why does data leakage occur when you scale before splitting?" If you StandardScale the full dataset before splitting, the test data's distribution influences the scaler fit — the model has indirect information about test data. Always fit transformers on training data only, then transform both train and test with the same fitted transformer. `Pipeline` handles this automatically.

## PyTorch: Training Loop and Key Concepts

**Custom dataset**:
```python
class MyDataset(torch.utils.data.Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.LongTensor(y)
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]
```

**Standard training loop**:
```python
model.train()
for epoch in range(num_epochs):
    for batch_X, batch_y in dataloader:
        optimizer.zero_grad()          # Clear gradients
        outputs = model(batch_X)       # Forward pass
        loss = criterion(outputs, batch_y)  # Compute loss
        loss.backward()                # Backprop
        optimizer.step()               # Update weights
```

**Common pitfall**: Forgetting `optimizer.zero_grad()`. Gradients accumulate by default — if you don't zero them, you're summing gradients across batches instead of computing per-batch gradients.

**Model evaluation**: `model.eval()` disables dropout and batch norm updates. `torch.no_grad()` disables gradient computation (saves memory and computation during inference).

**GPU training**: `.to(device)` moves tensors and models to GPU. Use `device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')`.

## ML System Design

This is the most common senior ML interview component. Key questions: recommendation systems, fraud detection, search ranking, ad click prediction.

**Feature store**: A centralized system for storing and serving features. Online store (Redis) for low-latency serving; offline store (data warehouse) for training. Ensures training-serving consistency — training and inference use the same feature definitions.

**Model serving**: Real-time serving via FastAPI + Triton Inference Server or TorchServe. For latency-critical paths: model quantization (INT8/FP16), model distillation, ONNX runtime.

**A/B testing ML models**: Never deploy directly to all users. Shadow mode (new model runs in parallel, no serving impact, compare offline). Canary deployment (5% traffic). A/B test for business metrics, not just ML metrics.

**Data freshness**: How often does the model retrain? Daily? Weekly? Real-time? Online learning? Depends on concept drift rate and cost of retraining. Feature pipelines must match — if you retrain on new data, ensure the training pipeline's features match the serving pipeline's features.

**Class imbalance**: For 1:99 positive:negative datasets, the model can achieve 99% accuracy by always predicting negative. Solutions: class weights in loss function (`weight` parameter in PyTorch CrossEntropyLoss), oversampling positive class (SMOTE), undersampling majority class, change evaluation metric to AUC-PR.

## Common ML Interview Scenarios

**"Design a recommendation system for an e-commerce platform"**:
- Collaborative filtering: users similar to you liked X (user-item matrix factorization)
- Content-based: items similar to what you've bought (item embeddings)
- Two-stage: candidate generation (fast, high-recall ANN search) + ranking (precise, ML model on 100 candidates)
- Cold start: use demographic signals, trending items, or content-based for new users/items

**"How would you detect fraud in real-time?"**:
- Features: transaction amount, velocity (N transactions in last hour), device fingerprint, location deviation, merchant category
- Model: gradient boosting (fast inference, interpretable) or deep learning for sequential patterns
- Latency requirement: <100ms → model must be preloaded, feature lookup from Redis
- Threshold tuning: optimize for false positive rate (blocking legitimate transactions hurts UX)

ML engineering is ultimately about reliable, reproducible, production-ready systems. The theory matters, but the engineering rigor is what separates ML engineers who ship from those who only analyze.
