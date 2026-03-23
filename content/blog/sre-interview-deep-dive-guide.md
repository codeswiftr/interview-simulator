---
title: "SRE Interview Deep Dive: Reliability, Incident Management, and SLOs"
description: "Comprehensive SRE interview preparation — SLOs/SLAs/error budgets, incident management, postmortem culture, on-call best practices, and production reliability system design."
date: "2026-03-20"
category: "Site Reliability"
---

# SRE Interview Deep Dive: Reliability, Incident Management, and SLOs

SRE interviews are distinct from standard software engineering interviews in a key way: they test your judgment about reliability tradeoffs, not just your ability to build things. Interviewers want to see how you reason about failure, how you prioritize reliability work, and whether you can bridge the gap between software engineering practices and operational excellence. This guide covers the topics that appear consistently across SRE interviews.

## SLOs, SLAs, and Error Budgets

This is the conceptual foundation of modern SRE practice, and interviewers will probe it from multiple angles.

An SLI (Service Level Indicator) is a specific, measurable metric — request latency at the 99th percentile, error rate, availability. An SLO (Service Level Objective) is your target for that metric — "99.9% of requests complete in under 200ms." An SLA (Service Level Agreement) is the contractual commitment to customers, usually more lenient than your internal SLO with financial penalties for breach.

The error budget is the gap between your SLO and 100%. For a 99.9% availability SLO, you have 0.1% of time — about 43 minutes per month — to spend on failures. The key insight: the error budget creates a shared language between engineering and product. When the budget is healthy, you can take risks and ship fast. When it's depleted, you slow down and focus on reliability. Be ready to discuss how error budgets change prioritization conversations.

Common interview question: "Your service has burned through its error budget with two weeks left in the month. What do you do?" The expected answer involves freezing non-critical releases, convening a reliability review, and investigating the root cause of the burns.

## Toil Reduction

Toil is manual, repetitive, automatable work that scales with service growth and provides no enduring value. SRE interviews often include a "describe a toil reduction project you led" question — have a specific example ready.

The Google SRE recommendation is to keep toil below 50% of an SRE team's time. More than that, and the team becomes a pure operations team rather than an engineering team. Be able to articulate how you identify toil (track it, measure it), prioritize what to automate first (highest frequency, highest impact), and measure the outcome.

Know common sources of toil: manual deployments, on-call ticket triage that could be auto-resolved, capacity scaling that requires human intervention, and repetitive runbook steps that could be scripted.

## Incident Management and On-Call

Incident command is a structured approach to managing production outages. Interviewers expect you to walk through a realistic incident scenario — how you'd detect, declare, mitigate, resolve, and follow up.

The incident commander role is critical: one person coordinates, makes decisions, and owns communication. Separate the IC role from the person doing technical investigation. Know the communication cadence: regular status updates to stakeholders, clear internal coordination, and post-incident communication.

On-call health is a real SRE concern. Discuss alert fatigue — the dangers of too many low-signal alerts desensitizing responders to real incidents. Know the principles of good alerting: alert on symptoms (user-facing impact), not causes (CPU at 80%). Every alert should be actionable and have a clear runbook.

## Postmortem Culture

Blameless postmortems are a cornerstone of SRE. Interviewers will often ask you to walk through how you'd write one or how you'd facilitate a postmortem process.

A good postmortem includes: a timeline of events, the contributing factors (not "causes" — complex systems have multiple contributing factors), the impact, what went well, what went poorly, and concrete action items with owners and deadlines. The "five whys" technique can help identify systemic issues rather than stopping at the surface-level trigger.

Be ready to discuss what makes a postmortem culture successful: psychological safety (people don't fear blame), follow-through on action items (otherwise it's just documentation), and systemic focus (fixing the process, not punishing individuals).

## Observability: Metrics, Logs, and Traces

The three pillars of observability come up in nearly every SRE interview. Know not just what they are but when to use each.

Metrics are aggregated numeric data — great for dashboards, alerting, and trend analysis. Logs are timestamped records of discrete events — essential for debugging but expensive at high volume. Distributed traces track a request across multiple services — critical for understanding latency in microservice architectures.

Be familiar with the USE method for resource analysis (Utilization, Saturation, Errors) and the RED method for services (Rate, Errors, Duration). Know how you'd instrument a service to expose the right signals and how you'd design dashboards that give operators situational awareness quickly.

## Reliability System Design

SRE system design questions often ask you to design a monitoring system, an on-call rotation management tool, or a capacity planning system. Apply the same structured approach as software system design but emphasize failure modes and resilience.

For a monitoring system: discuss data collection (pull vs. push), time-series storage, alert evaluation, notification routing, and escalation policies. Address the meta-monitoring problem — how do you know your monitoring system is working?

Common reliability patterns to know: circuit breakers, bulkheads, retry with exponential backoff and jitter, graceful degradation, and load shedding. Be able to explain when each pattern is appropriate and what its failure modes are.

## SRE vs. DevOps

Interviewers sometimes ask directly: "What's the difference between SRE and DevOps?" The framing that lands well: DevOps is a philosophy and cultural movement. SRE is Google's opinionated implementation of DevOps principles with specific practices, tooling, and team structure. SRE is one way to do DevOps; DevOps is not synonymous with SRE.

The class SRE principles — eliminating toil, using error budgets, treating ops as a software problem — are what distinguish the discipline. Be able to articulate these principles and connect them to concrete practices you've implemented or would implement.

Practice walking through real production incidents you've handled — what happened, how you detected it, how you resolved it, and what changed afterward. These concrete examples are the most compelling evidence that you can actually do the job.
