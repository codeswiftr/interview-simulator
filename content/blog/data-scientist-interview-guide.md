---
title: "Data Scientist Interview Guide: Statistics, ML Algorithms, and Case Studies"
description: "Prepare for data scientist interviews — probability and statistics fundamentals, ML algorithm questions, SQL, case study frameworks, and what separates strong DS candidates."
date: "2026-03-20"
category: "Career Guides"
---

# Data Scientist Interview Guide: Statistics, ML Algorithms, and Case Studies

Data scientist interviews vary significantly by company and role. A DS role at a startup might be 80% SQL and experimentation; at a FAANG company it might involve ML algorithms, probability, and coding. This guide covers the full spectrum, organized by what companies at different sizes test most.

## Statistics and Probability: The Foundation

**A/B testing and hypothesis testing:** This is the most consistently tested topic. Know: null hypothesis, p-value, significance level (α = 0.05 convention), power, Type I and Type II errors. Be able to explain: "What does a p-value of 0.03 mean?" (Under the null hypothesis, there's a 3% chance of observing data this extreme or more extreme — not: 'there's a 97% chance the effect is real.')

**Sample size calculation:** Given expected effect size, baseline conversion rate, desired power (80%), and significance level (5%), how large a sample do you need? The formula isn't usually required, but understanding the relationship matters: smaller effects need larger samples; higher power needs larger samples.

**Confidence intervals:** The difference between a 95% CI and a p-value. "The 95% CI for lift is [1.5%, 8.2%]" — 95% of such intervals constructed this way contain the true value. Common question: "The 95% CI barely excludes 0. Should we ship?" Answer: technically significant, but the lower bound (1.5%) may not be practically significant — depends on the business context.

**Distributions:** Binomial (coin flips, click/no-click), Normal (CLT, Z-test), Poisson (event counts in fixed interval), Exponential (time between events). Know when to apply each.

## Machine Learning Algorithms

**Bias-variance tradeoff:** The fundamental ML concept. Bias: error from wrong assumptions (underfitting). Variance: error from sensitivity to training data fluctuations (overfitting). High-complexity models have low bias, high variance. Low-complexity models have high bias, low variance. Regularization reduces variance at the cost of slight bias increase.

**Decision trees, random forests, gradient boosting:** Decision trees are interpretable but prone to overfitting. Random forests aggregate many trees (bagging) to reduce variance. Gradient boosting (XGBoost, LightGBM) builds trees sequentially to reduce bias — typically the best-performing tabular ML algorithm.

**Logistic regression:** Despite the name, this is a classification algorithm. Outputs probability via sigmoid. Linear decision boundary. Interpretable coefficients (log-odds ratios). Fast, stable, a strong baseline.

**Neural networks:** Know the basics — forward pass, backpropagation, activation functions (ReLU standard, sigmoid for final layer in binary classification, softmax for multiclass). When to use: large datasets, complex patterns (images, text, sequential data). Not always better than gradient boosting for tabular data.

**Cross-validation:** K-fold CV estimates out-of-sample performance. Time series: use time-based splits (train on earlier, test on later) — random splits leak future information.

**Feature importance and selection:** SHAP values for interpretable feature contributions. Permutation importance. L1 regularization (LASSO) for automatic feature selection.

## SQL for Data Science

Data science roles require strong SQL. Key patterns:

**Retention analysis, cohort analysis:** Joining a user's first activity date to their subsequent activity dates. (See the SQL Advanced guide for code examples.)

**Funnel analysis:** Sequence of steps where users drop off. Use conditional aggregation:
```sql
SELECT 
    COUNT(DISTINCT CASE WHEN event = 'page_view' THEN user_id END) AS page_views,
    COUNT(DISTINCT CASE WHEN event = 'add_to_cart' THEN user_id END) AS adds_to_cart,
    COUNT(DISTINCT CASE WHEN event = 'purchase' THEN user_id END) AS purchases
FROM events;
```

**Anomaly detection in SQL:** Identify records more than N standard deviations from the mean:
```sql
SELECT *
FROM metrics
WHERE value > (SELECT AVG(value) + 3 * STDDEV(value) FROM metrics);
```

## Product Sense and Case Studies

At product analytics and data science roles, expect product/business questions:

**"How would you measure the success of feature X?"** Framework: define the north star metric (what is this feature ultimately trying to improve?), identify leading indicators (faster-moving metrics that predict the north star), and guardrail metrics (things that shouldn't get worse).

**"Why did metric Y drop last week?"** Structured decomposition: break the metric into components (is it a conversion rate drop or volume drop?), then further decompose (which segment, which platform, which cohort?). Use SQL to investigate. Then form hypotheses about causes.

**"How would you design an A/B test for..."** Cover: control and treatment group assignment (user-level vs. request-level — prefer user-level for most features), sample size, primary metric, duration, and analysis plan (will you use t-test, chi-squared, or another test?).

## What Separates Strong Data Science Candidates

Strong candidates demonstrate: statistical rigor (using concepts correctly, not just loosely), SQL fluency (can write complex analytical queries quickly), product intuition (connects analysis to business decisions), and communication clarity (explains statistical results to non-statisticians without dumbing down).

Weak candidates make these mistakes: conflating correlation with causation, not checking statistical assumptions, treating p < 0.05 as automatic significance without considering effect size and business context, and over-engineering with complex ML when regression or a simple rule would suffice.

The best data scientists I've interviewed are deeply pragmatic: they pick the simplest analysis that answers the question, they're appropriately skeptical of their results, and they can articulate the business implication of every finding.
