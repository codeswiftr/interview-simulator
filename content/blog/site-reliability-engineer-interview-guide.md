---
title: "Site Reliability Engineer (SRE) Interview Guide: From On-Call to System Design"
description: "Ace SRE interviews — SLOs, SLAs, error budgets, incident management, toil reduction, distributed systems reliability, and Google SRE culture."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

# Site Reliability Engineer (SRE) Interview Guide: From On-Call to System Design

Site reliability engineering sits at the intersection of software engineering and operations. SREs are hired to eliminate the category of problems that used to require a dedicated ops team permanently in firefighting mode. If you are interviewing for an SRE role, you will be evaluated on your ability to think in systems, quantify reliability, write code to automate toil, and lead an organization through incidents without panic. This guide covers the technical and behavioral dimensions of SRE interviews at companies running the Google SRE model and its derivatives.

## SLOs, SLAs, and Error Budgets: The Core Framework

Every SRE interview will probe your understanding of service level objectives, service level agreements, and error budgets. These are not abstract concepts — interviewers want to see that you can define and operationalize them for real services.

**Service Level Indicators (SLIs)** are the raw measurements: request latency at the 99th percentile, availability as a ratio of successful requests, throughput in requests per second, error rate as a percentage of total traffic. The choice of SLI matters enormously. Measuring availability as "server up" is weaker than measuring it as "fraction of user requests that return a 200 within 500ms."

**Service Level Objectives (SLOs)** set the target: 99.9% of requests succeed within 300ms over a 30-day rolling window. Good SLOs are tight enough to matter and loose enough to be achievable. If your SLO is 99.999% and your cloud provider's published availability is 99.95%, your SLO is aspirational fiction.

**Error budgets** are the operationalization of SLOs. If your SLO is 99.9% availability over 30 days, you have 43.2 minutes of allowed downtime per month. The error budget is what you spend on risk: new deployments, infrastructure changes, experiments. When the budget is depleted, you stop taking risk until it recovers. Interviewers at Google, Stripe, Datadog, and similar companies will ask you to walk through a scenario where the error budget is nearly exhausted and a feature team wants to ship a risky change — your answer should include stakeholder communication, risk quantification, and the rollback plan.

## Incident Management: What Interviewers Actually Test

SRE behavioral interviews often center on incident scenarios. The format is usually a past incident you managed or a hypothetical you work through live. Interviewers are not looking for a heroic story of staying up all night — they are looking for structured thinking under pressure.

The key elements of a strong incident response:

- **Detection**: How did you know something was wrong? What alerting fired, and how quickly? Was the alert actionable or noisy?
- **Diagnosis**: How did you narrow from "something is broken" to "this specific component is the cause"? Walk through your use of dashboards, logs, traces, and runbooks.
- **Mitigation vs. resolution**: Mitigation stops the bleeding (roll back the deployment, increase timeouts, shed load). Resolution fixes the root cause. SREs prioritize mitigation first. Interviewers want to see this distinction clearly.
- **Communication**: How did you keep stakeholders informed without becoming the person writing status updates instead of debugging? Who declared the incident, who was incident commander, who handled external communication?
- **Postmortem**: Blameless postmortems are a cultural cornerstone of SRE. Your postmortem should identify contributing causes (not a single root cause), produce action items with owners and deadlines, and be shared broadly. Interviewers will ask about a postmortem you wrote or improved.

Prepare two or three incident stories with this structure before any SRE interview. If you have not managed incidents professionally, use open-source outpost reports (the Cloudflare blog, the AWS status history, Stripe engineering posts) to practice reasoning through them.

## Toil Reduction and Automation

The SRE mandate is to cap operational toil at 50% of engineering time and continuously reduce it. "Toil" has a specific meaning: manual, repetitive, automatable work that scales with service growth rather than diminishing over time. Answering tickets, manually rotating certificates, SSHing into boxes to restart services — these are toil.

SRE coding interviews often involve automation tasks rather than pure algorithm problems. You might be asked to write a script that parses log files and emits structured metrics, build a simple health-check system, or implement a basic rate limiter. The expected language varies by company — Python is common, Go is increasingly expected, and shell scripting fluency is always assumed.

Be prepared to discuss automation projects you have built: what the toil was, how you measured its cost, what you automated, and how you measured the reduction. The quantitative dimension matters. "I automated certificate rotation, saving about four hours per month across the team" is stronger than "I automated certificate rotation."

## Distributed Systems Reliability

SRE system design interviews focus on reliability properties of distributed systems rather than the pure scale-and-throughput focus of a backend system design interview. Key topics:

**Failure modes**: Cascading failures, thundering herd, retry storms, split-brain. You should be able to describe how each happens and how to mitigate it. Circuit breakers, exponential backoff with jitter, and bulkheads are standard mitigations interviewers expect you to know.

**Observability**: The three pillars — metrics, logs, and traces — and when to use each. Metrics for alerting on known failure modes. Logs for debugging specific requests. Traces for understanding latency across service boundaries. Familiarity with Prometheus/Grafana, the ELK stack, and distributed tracing systems (Jaeger, Zipkin, Honeycomb) is expected at most companies.

**Deployment reliability**: Canary deployments, blue-green deployments, feature flags, traffic shifting. SREs own the reliability of the deployment pipeline, not just the running service. Be ready to design a deployment strategy for a service that cannot afford more than 0.1% error rate increase during rollout.

**Capacity planning**: SREs own capacity planning alongside product engineering. Know how to estimate resource requirements from load projections, how to model headroom, and how to communicate capacity risk to leadership before it becomes an incident.

Approaching your SRE interview with the mindset that reliability is a feature — one that must be designed, measured, and continuously improved — will distinguish you from candidates who treat it as a secondary concern. Companies running at scale have learned this the hard way. They hire SREs who already know it.
