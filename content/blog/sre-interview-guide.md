---
title: "SRE Interview Guide: Incident Response, SLOs, Error Budgets, and Reliability Engineering"
description: "Prepare for Site Reliability Engineering interviews with deep coverage of SLOs, error budgets, incident management, toil reduction, and the on-call culture that defines the role."
date: "2026-03-20"
category: "Specialized Roles"
---

Site Reliability Engineering interviews test a distinct blend of software engineering depth and operations pragmatism. The questions probe your judgment — how you balance reliability against velocity, how you handle incidents under pressure, and whether you understand that SRE is fundamentally about applying software engineering to operations problems. This guide covers the core concepts and the thinking SRE interviewers reward.

## SLOs, SLAs, and SLIs — Getting the Definitions Right

Confusing these terms in an interview is an immediate red flag. Get them precise:

- **SLI (Service Level Indicator):** A specific, measurable metric. "The fraction of requests completing in under 200ms." SLIs are the raw measurements.
- **SLO (Service Level Objective):** A target for an SLI over a time window. "99.9% of requests complete in under 200ms over a 30-day rolling window." SLOs are internal targets.
- **SLA (Service Level Agreement):** A contractual commitment to customers, usually looser than internal SLOs, with defined consequences for breach (credits, refunds). SLAs are external contracts.

The relationship: SLIs measure the thing; SLOs set the target; SLAs are what you promise customers and what you get held to contractually.

**Choosing good SLIs:** They should reflect user experience, not just system health. CPU utilization is not a good SLI — it doesn't tell you whether users are happy. Request success rate and latency percentiles (p50, p95, p99) are good SLIs because they correlate directly with user experience.

## Error Budgets

The error budget is the flip side of an SLO. If your SLO is 99.9% availability, your monthly error budget is 0.1% × 30 days × 24 hours × 60 minutes = 43.2 minutes of allowable downtime.

**Why error budgets matter:** They create a shared language between SREs and product teams. When the error budget is healthy, you can deploy aggressively. When it's nearly exhausted, you slow down and focus on reliability. This replaces subjective arguments ("we should ship faster" vs. "we should be more reliable") with an objective metric.

**Error budget policies** define what happens at different consumption levels:
- 0–50% consumed: proceed normally
- 50–75% consumed: increase observability, perform pre-mortem on upcoming releases
- 75–100% consumed: freeze non-emergency deployments, focus on reliability work
- >100% consumed: exec review, moratorium on features until budget recovers

In an interview, explaining error budget policy in this structured way signals you've thought about reliability as a system, not just a technical problem.

## Incident Response

SRE interviews almost always include a "tell me about an incident you handled" question. The structure interviewers want:

1. **Detection:** How did you find out? Alert, customer report, anomaly detection? Good answer: automated alerting with clear runbook links.
2. **Initial response:** How did you assess impact and severity? What made you declare an incident?
3. **Mitigation:** What did you do first — and did you prioritize mitigation (stop the bleeding) over root cause (understand why)?
4. **Communication:** How did you keep stakeholders informed? Incident channels, status pages, escalation.
5. **Resolution:** How did you confirm the incident was resolved, not just suppressed?
6. **Post-mortem:** What did you learn, what changed as a result?

The key nuance: experienced SREs separate mitigation from investigation. The first goal is restoring service. "Roll back the deployment and understand why later" is usually the right call. Interviewers value candidates who understand this prioritization.

**Blameless post-mortems:** The blameless culture originated at Google and is now standard. The goal is systemic improvement, not individual accountability. Post-mortems should produce action items with owners and due dates. An interview candidate who mentions "we updated the runbook and added a alert for this condition" demonstrates the full loop.

## Toil Reduction

Google's SRE book defines **toil** as work that is manual, repetitive, automatable, tactical, and grows in proportion to service size. SREs should spend less than 50% of their time on toil; the rest should go to engineering work that reduces future toil.

In interviews, you'll often get questions like "describe a manual process you automated." Strong answers:
- Quantify the time savings: "This took 2 hours per week; now it takes 2 minutes"
- Describe what broke and how you made the automation resilient
- Explain how you handed it off and made it maintainable

Interviewers are assessing whether you see toil as a problem to solve, not just work to do.

## Monitoring and Observability

The three pillars of observability:
- **Metrics:** Aggregated numerical measurements over time. Good for dashboards and alerting.
- **Logs:** Timestamped records of discrete events. Good for debugging specific requests.
- **Traces:** End-to-end request flows across services. Essential for diagnosing latency in distributed systems.

**The four golden signals** (from the Google SRE book):
1. **Latency:** How long requests take (distinguish successful vs. error latency)
2. **Traffic:** How much demand is hitting the system
3. **Errors:** Rate of failed requests
4. **Saturation:** How "full" the system is (approaching capacity)

Alert on golden signals, not on causes. Alert on "error rate > 5% for 5 minutes," not on "CPU > 80%." High CPU is a possible cause; high error rate is the user-impacting symptom.

## Capacity Planning

SRE interviewers at larger companies ask about capacity planning. The framework:
1. Define growth metrics (requests per second, active users, data volume)
2. Model growth rate (linear, exponential, seasonal)
3. Identify bottlenecks (CPU, memory, I/O, database connections)
4. Plan headroom: provision for peak load × safety factor, not average load
5. Trigger capacity reviews when utilization exceeds 70%

The "never less than N+2" principle: always have two extra units of capacity beyond what's needed. N handles load; N+1 handles one failure; N+2 handles a failure during a maintenance window.

## On-Call and Operational Health

On-call quality questions probe judgment and sustainability:

- **How do you decide if an alert is worth waking someone up at 3am?** (Every alert should be actionable and correspond to a user-impacting condition. Non-actionable alerts are noise and erode on-call health.)
- **What do you do with an alert that fires frequently but rarely indicates a real problem?** (Either fix the underlying condition or adjust the alert threshold — but don't train yourself to ignore it.)
- **How do you protect on-call engineers from burnout?** (Limit interrupt-driven work, rotate frequently, use incident review to eliminate repeat pages, compensate appropriately.)

## Preparing for SRE Interview Scenarios

Practice thinking out loud about system design from a reliability lens. For any system, be ready to discuss:
- What are the failure modes?
- What would your SLIs and SLOs be?
- How would you know the system is degraded before users tell you?
- How would you handle a 10x traffic spike?
- What would your runbook say for the top 3 incident types?

SRE interviews reward candidates who treat reliability as engineering discipline, not operational heroics.
