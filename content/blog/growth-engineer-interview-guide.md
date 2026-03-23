---
title: "Growth Engineer Interview Guide: Metrics, Experimentation, and Growth Systems"
description: "Complete guide to growth engineering interviews — A/B testing systems, funnel analytics, viral loops, retention mechanics, growth metrics (DAU/MAU, LTV, CAC), and how to answer growth system design questions."
date: "2026-03-20"
category: "Career Guides"
---

# Growth Engineer Interview Guide: Metrics, Experimentation, and Growth Systems

Growth engineering sits at the intersection of software engineering and product analytics. Growth engineer interviews test both technical implementation skills and data-driven thinking about product behavior. Here's what you need to know.

## What Growth Engineers Do

Growth engineers build systems that accelerate user acquisition, retention, and monetization. They work on: A/B testing infrastructure, onboarding flows, referral programs, notification systems, SEO/content systems, paywall and conversion optimization, and analytics pipelines.

Different from typical product engineers: growth engineers care deeply about metrics, run experiments constantly, and are expected to have opinions about product strategy backed by data.

## Core Growth Metrics

**Acquisition:**
- **CAC (Customer Acquisition Cost):** Total marketing/sales spend / new customers acquired
- **Organic vs paid:** organic (SEO, word-of-mouth, viral) has better LTV; paid scales faster
- **Activation rate:** % of signups who hit the "aha moment" (first meaningful value)

**Engagement:**
- **DAU/MAU ratio (stickiness):** DAU/MAU × 100 = daily engagement rate. 50%+ is excellent (WhatsApp), 10-20% is typical for many apps
- **Session depth:** Number of meaningful actions per session
- **Feature adoption rate:** % of users who discover and use a key feature

**Retention:**
- **D1/D7/D30 retention:** % of new users who return 1, 7, 30 days after first use
- **Cohort analysis:** Track retention curves by acquisition cohort — critical for understanding if improvements are real or just artifacts
- **Churn rate:** Monthly % of subscribers who cancel

**Monetization:**
- **LTV (Lifetime Value):** Average revenue per user × average lifetime. Must exceed CAC for sustainable business
- **ARPU/ARPPU:** Average revenue per user / per paying user
- **Conversion rate:** % of free users who become paid

## A/B Testing System Design

Designing an experimentation platform is a common system design question for growth engineers.

**Core components:**

**Assignment service:** Determines which experiment variant a user sees. Uses consistent hashing on user ID — same user always sees the same variant. Must be extremely fast (<1ms) as it runs on every request.

**Event logging:** Track experiment assignments and user actions. Every impression, click, conversion labeled with experiment ID and variant.

**Metric computation:** Aggregate events per variant. Compute mean, variance, statistical significance tests. Pre-compute daily cohort metrics.

**Statistical analysis engine:** T-tests or Z-tests for conversion rate and mean comparison. Bayesian approaches for faster decision-making. Multiple testing corrections when running many experiments simultaneously.

**Key design decisions:**
- Randomization unit: user ID (for personalization experiments), session ID (for short-term experiments), device ID (pre-login experiments)
- Holdout groups: reserve 1-5% of users as a permanent control group not exposed to any experiments — validates that experiment wins are real
- Mutual exclusivity: ensure users in one experiment aren't contaminated by another (when experiments interact, use layers with orthogonal assignment)

## Viral Loops and Referral Systems

**K-factor:** Average number of new users each existing user refers. K > 1 = viral growth (exponential). K < 1 = growth requires continuous external acquisition.

**Referral program design:**
- Double-sided incentive (both referrer and new user get reward) outperforms single-sided
- Reward should be immediately useful (account credit, feature unlock) not delayed
- Friction must be near-zero: pre-populated share message, one-click send
- Track full referral attribution chain

**Implementation:** Unique referral codes per user. Landing page reads code, stores attribution in cookie/localStorage, links to account on signup. Multi-touch attribution: if user saw referral link AND search ad before signing up, how do you credit?

## Funnel Optimization

Funnels convert users through a sequence of steps. Every step has drop-off. Finding and fixing the highest-impact drop-off point is growth engineering in practice.

**Funnel analysis:** Compute conversion rate at each step. A funnel with 60% → 40% → 30% → 20% final conversion — the first step (60%→40%) has the biggest absolute drop. Fixing it from 67% to 75% would have more impact than optimizing the last step from 67% to 90%.

**Common conversion improvements:** Reduce form fields (every field costs ~5% conversion), add social proof (user count, reviews), progressive disclosure (don't show full complexity upfront), reduce time-to-value (get users to their "aha moment" faster).

## Retention Engineering

**Habit formation:** The hook model — trigger (notification, external prompt) → action (simple behavior) → variable reward (new content, likes, social affirmation) → investment (user adds data, follows, content that makes them more invested). Design products that create habits.

**Re-engagement systems:** Users who haven't returned in N days get a targeted email/push. The message and timing matter enormously. Test: "You have 3 unread notifications" vs "See what you missed" — the specific copy changes conversion significantly.

**Feature discovery:** Users who discover key features have dramatically higher retention. In-app tooltips, email sequences ("Did you know you can..."), and personalized recommendations based on usage patterns drive discovery.

## Growth Interview System Design Questions

"Design an A/B testing framework" — covered above.

"Design a referral program" — unique code generation, attribution tracking, reward fulfillment, fraud prevention (users abusing referrals for credits).

"Design an onboarding flow that maximizes Day 7 retention" — requires you to reason about what "aha moment" is for the product, what minimal steps are required to reach it, how to measure success, and how to test improvements.

"We're seeing a drop in D30 retention — how do you diagnose it?" — cohort analysis (is this specific to recent cohorts or all users?), funnel analysis (where are users dropping off?), feature usage analysis (do retained users use a feature that churned users don't?), qualitative research (survey or interview churned users).

## Technical Skills Expected

Growth engineers are expected to write production code AND run SQL analyses. You'll be asked about both:
- SQL: window functions, cohort queries, event-based retention calculations
- Python/pandas: cohort analysis, statistical testing (scipy.stats), visualization
- Backend: instrumentation, event schemas, API changes to support experiments
- Frontend: experiment assignment in React, tracking events, performance (experimentation adds latency budget)

Know how to structure an experiment event schema: `user_id`, `event_name`, `experiment_id`, `variant_id`, `timestamp`, `properties` (JSON). This schema design affects everything downstream.

