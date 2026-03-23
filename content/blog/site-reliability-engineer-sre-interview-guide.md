---
title: "Site Reliability Engineer (SRE) Interview Guide"
description: "Technical interview preparation for SRE roles: on-call practices, SLOs and error budgets, incident management, chaos engineering, and what Google, Netflix, and companies with mature SRE practices look for in reliability engineers."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

# Site Reliability Engineer (SRE) Interview Guide

SRE interviews test a different combination of skills than standard software engineering interviews. You need coding ability, systems knowledge, and operational experience — plus the ability to reason about reliability, failure modes, and the tradeoffs between shipping fast and staying stable. This guide covers what SRE interviews actually test.

## SRE vs. DevOps vs. Platform Engineering

The terminology varies by company, but the differences matter for interview preparation:

**SRE** (Google's model): Software engineers who specialize in reliability. They write code to automate operations, own service level objectives, respond to incidents, and have production veto power. The original SRE mandate: "if a sysadmin task can be automated, automate it; if it can't be automated yet, help the product team fix the system so it can be."

**DevOps**: A culture and practice, not a job title. Companies that call the role "DevOps engineer" often mean platform engineering or infrastructure engineering.

**Platform Engineering**: Builds internal developer platforms (CI/CD, Kubernetes, observability) that product engineers use. Less production ownership than SRE, more developer tooling focus.

For interview purposes: SRE interviews emphasize reliability theory (SLOs, error budgets, incident management), systems knowledge, and coding. Platform engineering interviews emphasize infrastructure tooling and developer experience.

## The Core SRE Concepts You Must Know

**Service Level Indicators (SLIs), Objectives (SLOs), Agreements (SLAs)**:
- SLI: the metric you measure. Request latency, error rate, availability.
- SLO: the target for that metric. "99.9% of requests respond in under 200ms."
- SLA: the business commitment. Usually more lenient than internal SLOs (you want buffer).
- Error budget: the allowed failure budget derived from the SLO. 99.9% availability = 43.8 minutes of downtime per month. If you've burned 40 minutes, you're nearly out of budget — slow down deployments.

Interviewers ask: "How would you define SLOs for a checkout service?" You should distinguish what to measure (latency, error rate, availability), how to aggregate (p50/p95/p99 for latency, not average), and what the right targets are given business context.

**Error budgets in practice**: The error budget governs the tension between velocity and reliability. When the budget is healthy, ship fast. When the budget is nearly exhausted, slow down or freeze deployments until reliability improves. This is the mechanism that makes SRE a partner rather than an obstacle to product engineering.

**Toil**: Repetitive, manual operational work with no long-term value. Google's SRE book defines toil as the enemy — SREs should spend no more than 50% of their time on toil. The rest goes to engineering work that eliminates future toil. Interviewers ask: "Tell me about toil you've identified and how you eliminated it."

## Incident Management

SRE interviews probe your incident response process:

**Incident classification**: severity levels (P0/P1/P2/P3 or SEV1/SEV2/SEV3), what constitutes each level, response times and escalation paths.

**Incident roles**: Incident Commander (coordinates response, owns communication), Operations Lead (executes mitigations), Communications Lead (external/internal stakeholder updates).

**Postmortems**: Blameless postmortems — the goal is to understand the system failure, not to find someone to blame. Every postmortem should produce action items that prevent recurrence. The "5 Whys" technique for root cause analysis.

**MTTR (Mean Time to Resolve)**: More useful than MTTF (Mean Time to Failure) for on-call planning. How do you reduce MTTR? Better monitoring, runbooks, automation of common mitigations, on-call rotation that keeps engineers from burning out.

## Technical Skills Tested

**Coding**: SREs write production code — automation scripts, monitoring systems, chaos engineering tools. Expect Python, Go, or Shell coding. Questions may be algorithmic but are often operational: parse a log file for error rates, write a script that retries with exponential backoff, implement a circuit breaker.

**Linux systems**: Process management, systemd, network stack (TCP/IP, load balancers, DNS), filesystem, kernel parameters relevant to performance (tcp_keepalive, file descriptor limits, vm.swappiness).

**Observability**: Metrics (Prometheus/Grafana, StatsD), logs (ELK stack, structured logging), traces (Jaeger, Zipkin, distributed tracing concepts). "Design an observability strategy for a microservices architecture" — cover metrics for service health, distributed traces for request attribution, and logs for debugging.

**Infrastructure**: Kubernetes (pod lifecycle, resource requests/limits, probes, disruption budgets), Terraform for infrastructure as code, CI/CD pipeline design, load balancer configurations.

**Chaos engineering**: Intentional fault injection to validate resilience. Netflix Chaos Monkey, Gremlin, `tc` (traffic control) for network fault injection. The hypothesis-driven approach: "If we inject 1% packet loss into the payment service, circuit breakers should prevent cascading failures within 5 seconds."

## How to Prepare

Read the Google SRE book (free online at sre.google). Practice incident simulations — "GameDay" exercises where you deliberately break a system and practice response. Build a full observability stack (Prometheus + Grafana + alerting) for a personal project and write SLOs for it. Study load balancer algorithms and failure modes (connection draining, health check configuration, graceful degradation).
