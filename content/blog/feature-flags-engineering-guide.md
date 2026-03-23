---
title: "Feature Flags and Experimentation Engineering Guide"
description: "How feature flags work in production engineering: flag types, targeting rules, gradual rollouts, A/B testing infrastructure, kill switches, technical debt from stale flags, and what experimentation platform engineers and senior software engineers are expected to know."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

Feature flags — also called feature toggles or feature gates — are one of the most widely used mechanisms in modern continuous delivery. They decouple code deployment from feature release, letting teams ship code to production without exposing it to users until the team is ready. For senior engineers and experimentation platform roles, interviewers expect deep familiarity with flag architecture, statistical validity, and lifecycle management.

## Flag Types and Targeting Rules

The simplest flag is a **boolean toggle**: a feature is either on or off for all users. Most real systems need more granularity, which is where multivariate flags come in — instead of on/off, a flag evaluates to one of several string or numeric values (for example, `control`, `variant_a`, `variant_b`).

**Targeting rules** determine who sees which variant. Common strategies:

- **User ID targeting**: specific users or internal employees see a flag enabled. Useful for dogfooding.
- **Cohort-based targeting**: users belonging to a pre-defined segment (e.g., premium subscribers, users in a specific geographic region) get a variant.
- **Percentage rollout**: a hash of the user ID (or session ID for logged-out users) maps that user deterministically into a percentage bucket. A 10% rollout always shows the same variant to the same user across sessions.

Deterministic bucketing is critical: if the bucket assignment changes on every page load, you corrupt your experiment by showing users multiple variants, which violates the stable unit treatment value assumption (SUTVA) and invalidates any statistical analysis.

## Use Cases

**Dark launches** let you deploy code that runs silently in production — logging output or running shadow computations — without exposing UI changes. This validates correctness and performance at scale before any user sees it.

**Kill switches** are flags that default to on and exist purely to disable a feature instantly without a deployment. When a service misbehaves in production, flipping a kill switch to off can stop the bleeding in seconds. This is a core reliability pattern at companies running continuous deployment.

**A/B experiments** expose control and treatment groups to different experiences and collect metric data to determine which performs better. Unlike dark launches, experiments are explicitly designed to answer a causal question.

**Canary deployments** progressively expose a new service version to a small slice of traffic — typically 1%, then 5%, then 25% — before full rollout. Feature flags are one mechanism for implementing this; another is traffic splitting at the load balancer level.

## Technical Implementation

**Server-side evaluation** is the most common pattern: the application backend fetches the flag ruleset (either on startup or via a streaming connection), evaluates the flag locally using the user context, and returns a consistent result. This keeps evaluation latency low (sub-millisecond) because there is no per-request network call to a flag service.

**Client-side evaluation** pushes the flag payload to the browser or mobile app. This works well for UI-only flags but exposes the full ruleset to the client, which can be a security concern.

**SDK patterns**: most flag platforms provide a client SDK that maintains an in-memory cache of flag configurations. The SDK connects to a streaming endpoint (SSE or WebSocket) to receive real-time flag updates without polling. Flag evaluation is a pure function: `evaluate(flagKey, userContext, defaultValue) → variant`. The default value is returned if the SDK fails to connect, ensuring safe degradation.

**Caching and consistency**: to avoid thundering-herd problems on startup, SDKs bootstrap from a local cache file and then reconcile with the remote state. At high traffic volumes, some teams push flag configurations to a CDN edge so that evaluation happens at the edge layer before the request even reaches origin.

## Gradual Rollout Mechanics

A percentage-based rollout uses a consistent hash (often MurmurHash or FNV) of `user_id + flag_key` modulo 100 to assign users to buckets. Using the flag key in the hash prevents all flags from splitting users along the same population boundary.

**Ring deployments** formalize progressive delivery into explicit stages: internal users → beta users → 1% of production → 10% → 50% → 100%. Each ring has automated health gates — error rate, p99 latency, business metric thresholds — that must pass before the rollout advances. If a gate fails, the rollout halts or auto-rolls back.

## A/B Testing Statistics

Running an experiment requires pre-calculating the required **sample size** before starting. The key inputs are the minimum detectable effect (MDE — the smallest improvement worth detecting), baseline conversion rate, desired statistical power (typically 80%), and significance level (alpha, typically 0.05).

**Statistical significance** is assessed using a two-sample test (z-test or chi-squared for proportions; t-test for continuous metrics). A **p-value** below alpha indicates that the observed difference is unlikely under the null hypothesis that both variants perform identically. Note that p-values do not measure effect size — a large sample can produce a significant p-value for a trivially small effect.

Common experimentation mistakes: peeking at results before the sample size is reached (inflates false positive rate), running the test too long after significance is reached (regression to the mean), and failing to check for **sample ratio mismatch** — a difference between the actual user split and the intended split, which signals a bucketing bug.

## Technical Debt: Stale Flags

Every flag that stays in the codebase after its purpose is fulfilled is technical debt. Stale flags make code harder to read, introduce conditional branches that can interact unexpectedly, and make onboarding harder. At scale, a codebase can accumulate hundreds of dead flags.

**Flag lifecycle management** involves tracking each flag's creation date, owner, and expected removal date in the flag platform. Automated tooling can scan the codebase for flag references and alert owners when a flag is past its TTL. Some teams gate CI pipelines on flag age — a build fails if code references a flag that has been 100% rolled out for more than 30 days.

Cleanup automation typically involves: removing the flag from the platform, running a codebase search for all SDK call sites, replacing the call with the winning variant's hardcoded value, and deleting the dead branch.

## Tools and Platforms

The mature commercial platforms are **LaunchDarkly**, **Split.io**, and **Optimizely**. Open-source alternatives include **Unleash** and **Flagsmith**. Major tech companies typically build internal systems: Google uses a configuration distribution system tied to Borg, Meta built Gatekeeper, and Airbnb has Trebuchet. The core architecture is similar across all of them: a flag configuration store, a server-side SDK with streaming updates, and an analytics pipeline that joins flag assignments to metric events.

## Interview Scenarios

**Design a feature flag system**: expect to cover flag storage (database or config file), SDK design (streaming vs. polling, caching, default values), targeting rule evaluation, the operator UI, and how you would handle high availability. A common follow-up: how do you ensure consistent bucketing for logged-out users?

**Debug a flag causing production issues**: walk through checking whether the flag is enabled for the right population (verify targeting rules and percentages), checking for sample ratio mismatch, confirming the SDK is receiving the latest configuration (check streaming connection health), and verifying that the application is reading the evaluated value — not a hardcoded override left in by a developer. Also check for mutual exclusion issues: two experiments targeting the same user population can interact and corrupt both experiments' results.

Feature flags look simple on the surface but touch deployment safety, statistics, codebase hygiene, and distributed systems. Interviewers use them to probe how deeply a candidate thinks about production engineering trade-offs.
