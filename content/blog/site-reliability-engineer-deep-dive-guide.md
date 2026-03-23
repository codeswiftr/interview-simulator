---
title: "SRE Deep Dive: Error Budgets, Capacity Planning, and Production Systems"
description: "A comprehensive guide to SRE interviews covering the Google SRE model, SLI/SLO/SLA definitions, error budgets, capacity planning, toil reduction, and on-call best practices."
date: "2026-03-20"
category: "Specialty Role Interviews"
---

# SRE Deep Dive: Error Budgets, Capacity Planning, and Production Systems

Site reliability engineering is a distinct discipline with a specific philosophy. Interviewers at Google, Meta, and companies running the Google SRE model will quickly distinguish candidates who have read the SRE book from candidates who have applied it under production pressure. This guide covers the conceptual foundations and the practical interview material.

## SRE vs DevOps vs Platform Engineering

These roles overlap in tooling but differ in charter.

**DevOps** is a cultural and organizational pattern — breaking down walls between development and operations. In practice, the title often describes engineers who own CI/CD pipelines and deployment infrastructure.

**SRE** is Google's answer to operations: apply software engineering discipline to reliability problems. SREs write code to eliminate toil, own error budgets, and gate deployments when reliability is at risk. The key distinguishing feature is that SREs can say no to deployments when the error budget is exhausted.

**Platform engineering** focuses on internal developer experience — building the deployment platform, observability stack, and self-service tooling that product teams use. Platform engineers don't typically own production reliability of product services.

## The Google SRE Model: SLI, SLO, SLA

**Service Level Indicator (SLI):** A quantitative measure of service behavior. Examples: request success rate, p99 latency, queue processing throughput. SLIs must be measurable, not aspirational.

**Service Level Objective (SLO):** A target for an SLI over a time window. "99.9% of requests return a successful response over any 30-day window." The SLO is internal — it's the target you actually run to.

**Service Level Agreement (SLA):** A contractual commitment to customers, usually set below the SLO with financial consequences for breach. If your SLO is 99.9%, your SLA might be 99.5%.

**Interview Q&A:**

Q: "How do you choose an SLO level?"

A: Start from user pain, not from what's technically achievable. Ask: what level of reliability makes users stop noticing reliability? For most services this is 99.9% or above for synchronous APIs. For batch processing, it might be 99.5% with different latency targets. Then verify you can measure it with your current instrumentation.

## Error Budgets

The error budget is the allowable unreliability derived from the SLO. A 99.9% monthly SLO gives you 43.8 minutes of downtime. That budget belongs jointly to engineering and product.

The error budget policy is the critical artifact. It defines:

- What triggers a freeze on non-reliability deployments
- Who has authority to override the freeze
- How the team spends the budget when it's healthy (planned maintenance, experiments, risky migrations)

If you've never written or enforced an error budget policy, be honest about that. But be ready to describe what a good one looks like: clear thresholds (e.g., burn >50% of monthly budget in a week), clear owners, clear consequences.

**Sample question:** "Your team is burning error budget three times faster than expected. Product wants to ship a major feature Friday. What do you do?"

Answer: Calculate the burn rate against the remaining budget. If the feature would risk exhausting the budget before month-end, you exercise the error budget policy and block the release. You present the data — not opinions — to product leadership. If the policy says product can override with sign-off, that's a documented decision with accountability.

## Capacity Planning

Capacity planning is the practice of ensuring you have enough compute, memory, network, and storage to serve expected load with headroom for spikes.

**Demand forecasting.** Use traffic trends (seasonal patterns, growth curves) to project 3-6 months out. Model both average load and peak multipliers. For a retail service, peak might be 10x average during a sale.

**Resource profiling.** Know your service's CPU-to-memory ratio under load. Profile at realistic concurrency levels, not synthetic single-thread benchmarks.

**Headroom policy.** Define how much spare capacity you maintain. 30% headroom is common — it handles organic spikes and gives you time to provision without a crisis.

**Failure scenario planning.** What happens if one availability zone goes down? Can you absorb the traffic with remaining capacity? This drives your redundancy requirements.

## On-Call Practices and Toil Reduction

A well-run on-call rotation is one where engineers are not exhausted and pages are actionable. Interviewers assess whether you've thought carefully about this.

**Toil** is operational work that is manual, repetitive, automatable, and scales with service growth. Restarting a service because it leaks memory is toil. Writing the automation that detects and restarts it is not. SREs track toil as a percentage of work and push for reducing it below 50%.

**Alert hygiene.** Every alert in the rotation should have a runbook. Alerts that fire without a runbook, or that engineers routinely silence without action, are candidates for removal or reclassification.

**Postmortem culture.** Blameless postmortems produce action items, not shame. The postmortem document captures timeline, contributing factors, and follow-up items with owners. A strong SRE candidate can describe a postmortem they facilitated and what changed as a result.

## What SRE Interviews Actually Test

Beyond the concepts, SRE interviews test:

1. **Debugging judgment.** Given a symptom (latency spike, error rate increase), can you walk through a systematic investigation? Use the USE method (Utilization, Saturation, Errors) or RED method (Rate, Errors, Duration).

2. **Production experience.** Have you been paged? Have you broken something and fixed it? Specificity here matters.

3. **Code quality.** SREs write production code. Expect a coding round focused on automation, data processing, or systems reasoning.

4. **Communication.** Can you explain a complex incident to a non-technical stakeholder? SREs are a translation layer between engineering reality and business impact.

Come prepared with two or three production stories: one incident you investigated, one reliability improvement you shipped, and one case where you pushed back on a product request based on reliability data.
