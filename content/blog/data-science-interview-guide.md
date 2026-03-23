# Data Science Interview Guide 2024: Statistics, ML, and the Full Spectrum

Data science interviews test a broader range of skills than almost any other technical role. In a single loop you might face SQL window function problems, probability puzzles, A/B testing design questions, machine learning concept explanations, and open-ended business case studies. Unlike software engineering interviews, where the LC-style coding problem is the central axis, data science interviews vary enormously by company and level—a DS role at a consumer tech company will weight experiment design heavily, while a DS role at a financial services firm will probe statistics and causal inference deeply.

This guide covers the full spectrum so you can prepare efficiently. We will cover statistics fundamentals, probability reasoning, SQL, ML depth, experiment design, business sense questions, and how the role differs from Machine Learning Engineering (MLE).

## Statistics Fundamentals: The Foundation That Most Candidates Underprepare

Statistics is the area where data science candidates most frequently struggle, particularly candidates who came up through ML-heavy programs that emphasized gradient descent over hypothesis testing. Interviewers at companies with mature data cultures—Meta, Airbnb, Lyft, LinkedIn—probe statistics deeply.

**Hypothesis testing and p-values:**

A hypothesis test starts with the null hypothesis (H₀)—the assumption that there is no effect, no difference, nothing interesting. The p-value is the probability of observing a result at least as extreme as yours, assuming the null hypothesis is true. A p-value of 0.03 means: if there were truly no effect, you would see a result this extreme or more extreme only 3% of the time by chance.

The critical misconception to avoid in interviews: the p-value is not the probability that the null hypothesis is true, and it is not the probability that your result occurred by chance. It is a conditional probability—P(data | H₀)—not P(H₀ | data). Interviewers at rigorous companies will probe exactly this distinction.

Statistical significance at p < 0.05 means you have chosen a 5% Type I error rate. You should be able to articulate what that means: if you run 100 A/B tests where the treatment has no real effect, you expect to incorrectly declare significance in 5 of them.

**Type I and Type II errors:**

A Type I error (false positive) is rejecting a true null hypothesis—concluding there is an effect when there is not. The probability of a Type I error is α, your significance threshold.

A Type II error (false negative) is failing to reject a false null hypothesis—missing a real effect. The probability of a Type II error is β. Statistical power is 1 − β: the probability that your test will detect a real effect when one exists.

The practical implications for interview questions: if someone asks "we ran an A/B test and got p = 0.07, should we ship the feature?", the right answer is not simply "no, it's not significant." You should ask about power: was the test adequately powered to detect the effect size you care about? A p-value of 0.07 in an underpowered test is much less informative than a p-value of 0.07 in a well-powered test.

**Confidence intervals:**

A 95% confidence interval means: if you repeated this experiment many times and computed a CI each time, 95% of those intervals would contain the true population parameter. It does not mean there is a 95% probability that the true value lies within this specific interval—once computed, the interval either contains the true value or it does not.

Confidence intervals are often more useful than p-values in practice, because they convey the magnitude and precision of an estimate, not just a binary significance flag. Being able to explain this distinction demonstrates statistical maturity.

**Statistical power and sample size:**

Power is determined by four factors: effect size (larger effects are easier to detect), sample size (more data increases power), significance threshold α (a stricter threshold reduces power), and variance (noisier metrics require larger samples). You should be able to reason through how each of these affects the required sample size for an experiment.

A common interview question: "How would you determine how long to run an A/B test?" The answer involves specifying the minimum detectable effect (MDE)—the smallest effect size that would be practically meaningful—and then using a power analysis to determine the required sample size. You run the experiment until you have collected enough samples, not until you see a result you like. "Peeking" at results and stopping early when significance is reached is a form of p-hacking that inflates Type I error rates.

## Probability and Bayesian Reasoning

Probability questions test whether you can reason carefully under uncertainty. They appear in two forms: classic probability puzzles and Bayesian reasoning problems.

**Bayesian reasoning:**

Bayes' theorem: P(A|B) = P(B|A) × P(A) / P(B)

The canonical interview application is the base rate problem. "A disease affects 1% of the population. A test for the disease is 99% sensitive (correctly identifies 99% of true cases) and 99% specific (correctly identifies 99% of true negatives). If a patient tests positive, what is the probability they actually have the disease?"

Working through this: P(disease) = 0.01, P(positive | disease) = 0.99, P(positive | no disease) = 0.01. P(disease | positive) = (0.99 × 0.01) / (0.99 × 0.01 + 0.01 × 0.99) = 0.0099 / 0.0198 = 0.5. A positive test result only gives you a 50% probability of actually having the disease, because the prior probability is so low. This is the base rate fallacy in action.

This directly applies to fraud detection, anomaly detection, and medical screening—all common DS application domains. Being able to reason through Bayesian updating and explain why base rates matter is a strong signal.

**Common probability puzzles:**

The birthday problem (how many people in a room before the probability of a shared birthday exceeds 50%—answer is 23, which surprises most people) tests combinatorial thinking. The Monty Hall problem tests conditional probability and whether you can update beliefs correctly. You should be able to work through these from first principles, showing your reasoning step by step, rather than just reciting the answer.

## SQL Proficiency: Beyond Basic Queries

SQL in data science interviews is not just "write a SELECT statement." Interviewers test whether you can answer analytical questions efficiently using intermediate and advanced SQL constructs.

**Window functions** are the most commonly tested advanced SQL feature. They allow you to compute aggregates without collapsing rows. The key clause is `OVER (PARTITION BY ... ORDER BY ...)`. Common patterns:

`ROW_NUMBER()` for deduplication and ranking. `LAG()` and `LEAD()` for comparing a value to the previous or next row—essential for computing session durations, conversion funnel drop-offs, and day-over-day changes. `SUM() OVER (PARTITION BY user_id ORDER BY event_time ROWS UNBOUNDED PRECEDING)` for running totals. `NTILE(n)` for bucketing users into percentile groups.

A classic interview problem: "Find the second purchase for each user." This requires `ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY purchase_time)` and then filtering where the row number equals 2. Candidates who reach for a subquery with `LIMIT 2` are demonstrating unfamiliarity with the cleaner window function approach.

**Cohort analysis** is a pattern you should be able to write fluently. Cohort analysis groups users by their acquisition period (typically week or month of first activity) and tracks their retention or revenue over subsequent periods. This requires a self-join or window function to compute each user's cohort date, followed by aggregation by cohort and period offset.

**Funnel analysis** requires computing the count of users who completed each step of a sequence, with the denominator being users who completed the prior step. This often involves conditional aggregation: `SUM(CASE WHEN step >= 2 THEN 1 ELSE 0 END)`.

**Handling duplicates and data quality** is a practical concern interviewers probe: how do you handle duplicate event logs? How do you identify users who appear under multiple IDs? Being able to discuss COUNT(DISTINCT) vs COUNT(*), deduplication strategies using ROW_NUMBER(), and joins that produce unexpected fan-outs demonstrates production SQL experience.

## Python and Pandas for Data Manipulation

Python proficiency in DS interviews focuses on data manipulation with pandas, basic statistical computation, and communicating analysis clearly. You are unlikely to be asked to implement a linked list.

Key pandas operations interviewers expect fluency with: `groupby().agg()` for aggregation, `merge()` for joins (and understanding left vs inner vs outer join semantics), `pivot_table()` for reshaping data, handling missing values with `fillna()` and `dropna()`, string operations with `.str` accessor, and date/time operations with `pd.to_datetime()` and the `.dt` accessor.

A common interview format presents a DataFrame and a question: "Find the top three products by revenue in each country for the last 30 days." You should be able to translate that into: filter on date, group by country and product, sum revenue, rank within group using `groupby().rank()` or `nlargest()`, and return the result. Working through this fluently, narrating your approach, is what interviewers observe.

## Machine Learning Concepts: Depth Over Breadth

ML questions in data science interviews typically do not require you to implement algorithms from scratch. They test conceptual understanding, trade-off reasoning, and the ability to choose the right tool for a problem.

**Bias-variance tradeoff:**

Bias is error from incorrect assumptions in the model—underfitting, when the model is too simple to capture the true pattern. Variance is error from sensitivity to small fluctuations in the training set—overfitting, when the model has memorized training data and does not generalize. These trade off: as you increase model complexity, bias decreases but variance increases.

The practical implications: a linear regression on a non-linear problem has high bias. A depth-1000 decision tree on a small dataset has high variance. Regularization, cross-validation, and ensemble methods are tools for navigating this tradeoff.

**Regularization: L1 vs L2:**

L1 regularization (Lasso) adds the sum of absolute values of weights to the loss function. It tends to produce sparse solutions—driving irrelevant feature weights exactly to zero. This makes L1 useful for feature selection.

L2 regularization (Ridge) adds the sum of squared weights. It shrinks all weights toward zero but rarely to exactly zero. L2 is more stable numerically and generally preferred when all features are expected to contribute.

Elastic Net combines both, allowing you to tune the balance between sparsity (L1) and stability (L2).

**Tree-based models and gradient boosting:**

Random forests build many deep trees on bootstrapped samples of the data and average their predictions. The key intuition is that averaging many high-variance, low-bias models reduces variance without increasing bias—this is the bias-variance tradeoff in action.

Gradient boosting (XGBoost, LightGBM, CatBoost) builds trees sequentially, where each tree corrects the residual errors of the ensemble so far. Gradient boosting tends to outperform random forests on tabular data and is the default choice for structured data competitions. The trade-offs: slower to train, more hyperparameters to tune, and more prone to overfitting on small datasets.

**Evaluation metrics:**

Accuracy is misleading on imbalanced datasets—a model that predicts "not fraud" for every transaction is 99.9% accurate if fraud is 0.1% of transactions. For classification, use precision (of positive predictions, how many were correct), recall (of true positives, how many did we catch), F1 score (harmonic mean of precision and recall), and AUC-ROC (area under the receiver operating characteristic curve, which plots true positive rate vs false positive rate at all classification thresholds). AUC is particularly useful for ranking-style problems and is threshold-independent.

For regression, understand MSE (penalizes large errors heavily due to squaring), MAE (more robust to outliers), and RMSE (same units as the target, easier to interpret than MSE).

**Neural network basics:**

You do not need to implement backpropagation from scratch, but you should understand forward pass (matrix multiplications plus non-linearity), gradient descent (compute gradients of loss with respect to weights, update weights opposite to gradient), and common non-linearities (ReLU: max(0, x), sigmoid: 1/(1+e^−x) for binary output, softmax for multi-class). Overfitting prevention: dropout (randomly zero out neurons during training), batch normalization, early stopping.

## Experiment Design: Where DS Interviews Get Serious

Experiment design questions separate data scientists who can analyze data from those who can generate trustworthy insights from data. This is where DS interviews at companies like Airbnb, Uber, and Meta become demanding.

**A/B testing design:**

When asked "how would you set up an A/B test for feature X?", your answer should cover: the hypothesis (what effect do you expect and why), the metric hierarchy (primary metric, guardrail metrics), the randomization unit (user-level, session-level, or item-level), the duration (based on power analysis for the MDE), the assignment mechanism (how do you ensure users in treatment always see the treatment, not a mix?), and the analysis plan (two-sided t-test if the metric is approximately normal, Mann-Whitney for non-normal distributions, proportion test for binary metrics).

**Network effects and interference:**

If you are testing a feature where users interact with each other—a feed ranking algorithm, a messaging feature, a marketplace—a standard A/B test may be invalid because treatment and control groups are not independent. A user in control who interacts with a user in treatment is "contaminated." Solutions include cluster-based randomization (assign all users in a social cluster to the same condition), switchback tests (alternate treatment and control by time period), or network-level modeling to estimate spillover effects. This topic is the signal that you understand when standard experimental assumptions break down.

**Causal inference for observational data:**

When you cannot run an experiment—for ethical reasons, feasibility reasons, or because you want to understand the effect of something that already happened—you need causal inference methods. Key tools:

Regression discontinuity: if there is a threshold that determines treatment (users who signed up before date X got feature Y), you can compare users just above and just below the threshold, where treatment assignment is essentially random near the cutoff.

Difference-in-differences: compare the change in outcome for a treated group before and after treatment to the change for a comparable control group. Controls for time-invariant confounders.

Propensity score matching: estimate the probability that each unit received treatment based on observed covariates, then match treated and control units with similar propensity scores to make groups comparable.

**Simpson's paradox:**

Simpson's paradox is when a trend that appears in several groups disappears or reverses when the groups are combined. The canonical example: a drug appears effective in both men and women separately, but appears ineffective in the overall population, because more men (who have worse outcomes on average) received the drug.

The implication: always check your aggregations. Segment your analysis by relevant stratifying variables. In DS interviews, being able to identify that a given aggregate statistic might be misleading due to confounding or Simpson's paradox signals statistical sophistication.

## Business Sense Questions

Business sense questions test whether you can connect quantitative work to product and business outcomes. These are common at later interview rounds and for senior roles.

**"How would you measure the success of feature X?"**

The template: define the goal (what is this feature trying to achieve?), identify primary metrics (directly measuring the goal), identify guardrail metrics (things that should not deteriorate—engagement, retention, revenue), consider leading vs lagging indicators (clicks are leading; retention is lagging), and acknowledge measurement challenges (attribution, selection bias, novelty effects).

**"How would you detect fraud in our marketplace?"**

This is an unsupervised and supervised ML question combined. Start with rule-based signals (impossible transaction velocity, geographic impossibility), then discuss supervised models (if you have labeled fraud data), then anomaly detection for zero-day patterns (isolation forests, autoencoders). Critically: discuss the precision-recall tradeoff in fraud—false positives (blocking legitimate users) are costly to the business and to user trust, so you need a thresholding strategy that balances these. Also discuss the feedback loop: when your model flags fraud, you generate labeled data, which improves your model.

**"Daily active users dropped 15% yesterday. How do you investigate?"**

This is a structured debugging question. Your approach should be systematic: first verify the metric (is it a logging/instrumentation bug?), then segment by platform/geography/acquisition channel to isolate the source, look for external events (did a major app store update ship?), check for product changes deployed yesterday, examine the full funnel (where in the funnel is the drop?), and cross-reference with other metrics (are errors up? Is latency up?).

## DS vs. MLE: Understanding Where You Fit

The line between data science and machine learning engineering has blurred, but the roles remain meaningfully distinct.

A data scientist's core work is generating insight from data: designing experiments, building analytical models to understand user behavior, creating dashboards and metrics, and advising product decisions with quantitative analysis. The output is often a recommendation, a report, or a strategic insight.

A machine learning engineer's core work is building systems that make predictions in production: training and evaluating models, building feature pipelines, deploying models to serve real-time or batch predictions, and monitoring model performance over time. The output is a working software system.

In practice, most data scientists write some production code and most MLEs do some analytical work, but the center of gravity differs. DS interviews weight statistics, experiment design, and business thinking more heavily. MLE interviews weight systems design, ML infrastructure, and software engineering more heavily.

When you are preparing, pay attention to the job description's language: "SQL," "A/B testing," "experiment design," and "stakeholder communication" signal a DS-leaning role. "Feature stores," "model serving," "MLflow," and "Kubernetes" signal an MLE-leaning role. Calibrate your preparation accordingly.

## How to Structure Your Case Study Answers

DS interview case studies often have no single right answer. Interviewers are evaluating your reasoning process, not just your conclusion. A strong structure for any case study:

1. Clarify the problem: ask about the business goal, the available data, and any constraints
2. State your assumptions explicitly—this demonstrates awareness of uncertainty
3. Break the problem into components and work through each systematically
4. Quantify when possible: "the impact is roughly X users" is better than "significant impact"
5. Acknowledge limitations and alternative interpretations
6. Summarize your recommendation and its rationale

The habit of narrating your thinking—"I'm going to start by checking whether this metric drop is specific to one platform or universal, because that would narrow the investigation significantly"—signals the collaborative problem-solving style that DS roles require.

## What Separates Strong DS Candidates

The data scientists who perform best in interviews demonstrate a consistent pattern: they know when standard methods break down. They can run a t-test, but they also know that the t-test assumes normality and independence, and they know what to do when those assumptions fail. They can build a gradient boosted model, but they also know that AUC can be misleading when class imbalance is severe. They can design an A/B test, but they also know that network effects can invalidate a standard randomized experiment.

That meta-awareness—knowing the limits of your tools and being honest about uncertainty—is the signal that interviewers at rigorous data-driven organizations look for. It is also the skill that makes data scientists genuinely valuable in production: not someone who produces numbers confidently, but someone who produces trustworthy numbers and communicates clearly when the data does not support confidence.
