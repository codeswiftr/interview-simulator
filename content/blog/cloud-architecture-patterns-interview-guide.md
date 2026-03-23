---
title: "Cloud Architecture Patterns Interview Guide: Multi-Region, Resilience, and Cost"
description: "Cloud architecture interview prep — multi-region design, disaster recovery strategies, cloud-native patterns, cost optimization approaches, and common cloud architecture interview questions."
date: "2026-03-20"
category: "Cloud"
---

# Cloud Architecture Patterns Interview Guide: Multi-Region, Resilience, and Cost

Cloud architecture questions appear in senior and staff engineer interviews, often framed as: "How would you make this system resilient to a regional outage?" or "What would you change about this architecture to reduce cost by 50%?" This guide covers the patterns and reasoning that strong answers require.

## Multi-Region Architecture

Multi-region design is the standard approach for systems requiring high availability and low global latency. The core decision: active-active vs. active-passive.

**Active-active:** All regions serve production traffic simultaneously. Read and write traffic is routed to the nearest region. Requires data synchronization across regions — the hardest part. Any write must eventually be visible in all regions. This introduces consistency challenges: conflicts when two regions write the same data concurrently.

**Active-passive (hot standby):** One region serves all traffic, the other is ready to take over. Simpler consistency model (one writer), but the passive region is wasted capacity during normal operation, and failover has operational complexity.

Most production systems for high availability use active-active for reads with primary-region writes, which gets geographic read latency benefits without multi-master write complexity.

**Interview question: "How do you handle a database in a multi-region setup?"** Common approaches: read replicas in each region (reads are local, writes go to primary), a globally distributed database (CockroachDB, Google Spanner, DynamoDB Global Tables), or a CQRS approach where read models are eventually consistent replicas.

## Disaster Recovery Fundamentals

Two metrics define DR: **RPO (Recovery Point Objective)** — the maximum acceptable data loss in time ("we can afford to lose up to 1 hour of data") — and **RTO (Recovery Time Objective)** — the maximum acceptable downtime ("we must recover within 4 hours").

DR strategies in order of cost/recovery speed:
- **Backup and restore:** Cheapest. RPO/RTO in hours. Suitable for non-critical systems.
- **Pilot light:** Minimal version of critical infrastructure always running. Scale up on failure. RPO minutes, RTO hours.
- **Warm standby:** Scaled-down version of full environment always running. RPO minutes, RTO minutes.
- **Hot standby / multi-site active-active:** Full production environment in multiple sites. RPO near-zero, RTO seconds to minutes. Most expensive.

The interview question is usually: "Given this RPO/RTO requirement, what DR strategy would you recommend and why?" The answer requires mapping the business requirements to the cost/recovery tradeoff, not just describing the options.

## Cloud-Native Patterns

**Serverless for event-driven workloads:** Lambda/Cloud Functions excel at event-triggered processing (S3 uploads, API callbacks, scheduled jobs) where bursty traffic makes provisioning difficult. The gotchas: cold start latency for synchronous APIs, execution time limits, debugging complexity.

**Container orchestration:** Kubernetes for stateless services that need autoscaling, rolling deployments, and complex networking. Managed Kubernetes (EKS, GKE, AKS) reduces operational overhead but not complexity. Know when Kubernetes is overkill — for small teams with few services, ECS Fargate or Cloud Run is simpler.

**Event-driven fan-out:** SNS/SQS combination for fan-out patterns: one event topic fans out to multiple SQS queues, each consumed independently. Decouples producers from consumers and handles variable consumer processing speeds.

**CDN edge computing:** CloudFront Functions and Lambda@Edge for request manipulation at the edge. Use cases: auth at the edge, A/B testing routing, geographic content customization. Reduces origin load and latency.

## Cost Optimization

Cost questions are common at senior level: "How would you reduce the AWS bill by 40%?"

**Compute:** Reserved instances or Savings Plans for predictable baseline load (30-60% cheaper than on-demand). Spot instances for fault-tolerant batch workloads (70-90% cheaper). Right-sizing: most production clusters are over-provisioned. Analyze actual CPU/memory utilization.

**Storage:** S3 lifecycle policies: transition infrequently accessed objects to S3-IA, S3 Glacier. Delete unreferenced snapshots. Eliminate data transfer costs by keeping compute in the same region as storage.

**Database:** Read replicas on RDS can reduce the primary instance size if most load is reads. DynamoDB: understand provisioned vs. on-demand — on-demand is more expensive at steady high throughput, provisioned is more expensive for unpredictable bursts.

**Observability:** Logging and metrics can be expensive at scale. Implement log sampling (log 10% of debug messages, 100% of errors), set metric retention policies, use summarized metrics instead of raw event streams where possible.

## Designing for Observability

Interviewers probe observability in architecture discussions. The three pillars: metrics (aggregate statistics over time), logs (individual event records), traces (end-to-end request journeys across services).

For cloud architecture questions, demonstrate that you design observability in from the start: structured logging (JSON, not plain text), request ID propagation for distributed tracing, SLO-aligned alerting (alert on symptom metrics like error rate and latency, not cause metrics like CPU). The goal is mean time to detection (MTTD) and mean time to resolution (MTTR) — observable systems have both.
