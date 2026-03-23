---
title: "DevOps Engineer Interview Guide: CI/CD, Infrastructure, and SRE Crossover"
description: "Complete DevOps interview preparation — CI/CD pipeline design, container orchestration, infrastructure as code, monitoring and observability, incident response, and common DevOps system design questions."
date: "2026-03-20"
category: "Career Guides"
---

# DevOps Engineer Interview Guide: CI/CD, Infrastructure, and SRE Crossover

DevOps and SRE interviews blend software engineering skills with infrastructure knowledge. You need to demonstrate both — that you can write code and automate systems, and that you understand the production characteristics of those systems. Here's what the top companies test and how to prepare.

## What DevOps Interviews Assess

Unlike pure software engineering interviews, DevOps/SRE interviews test:

1. **Automation mindset**: Can you automate this manual process? What would break? How would you test it?
2. **System reliability**: How would you design this for 99.9% vs 99.99% availability? What are the failure modes?
3. **Debugging under pressure**: Given this alert and these metrics, what's wrong? How do you diagnose it?
4. **Tradeoff reasoning**: Faster deploys vs safer deploys. Complexity vs control. These tradeoffs define DevOps work.

## CI/CD Pipeline Design

Be able to design a CI/CD pipeline from scratch. Key components:

**Source control triggers**: Pushes to feature branches run fast unit tests. PRs merge only if tests pass and code review is approved. Merges to main trigger full pipeline.

**Build stage**: Compile, lint, run unit tests. Docker image build. Should complete in < 5 minutes or developers stop waiting for it.

**Test stages**: Integration tests (slower, need infrastructure). Contract tests (API compatibility). Security scanning (SAST — static analysis, dependency vulnerability scanning). Performance benchmarks if you have them.

**Artifact management**: Docker images tagged with commit SHA pushed to registry. Immutable artifacts — don't rebuild in deployment, redeploy the same artifact.

**Deployment stages**: Dev → Staging → Production, each with approval gates. Staging should mirror production infrastructure.

**Interview question**: "How would you design a CI/CD pipeline that deploys 50 services, where each service has its own release cadence?"

Answer: Monorepo with path-based triggers (only build/deploy the service whose files changed), each service has its own versioned artifact, central deployment service handles rollout sequencing and dependencies between services.

## Infrastructure as Code

Know at least one IaC tool deeply:

**Terraform**: Declarative, provider-based. Plan/apply workflow. State file tracks actual infrastructure. Key concepts: modules for reuse, remote state for team collaboration, workspaces for environments. Common pitfall: state drift when someone makes manual changes outside Terraform.

**Ansible**: Procedural, agentless, YAML playbooks. Better for configuration management than infrastructure provisioning. Idempotency is key — running a playbook twice should have the same result as running it once.

Be able to explain immutable infrastructure: instead of patching running servers, replace them with new servers built from updated images. Prevents configuration drift, makes rollbacks trivial.

## Container Orchestration

Kubernetes interviews are a world of their own. Core concepts you must know:

**Pod**: Smallest deployable unit. One or more containers that share network and storage.

**Deployment**: Manages replica sets. Handles rolling updates, rollbacks. The main object you create for stateless services.

**Service**: Stable network endpoint that routes to pods. Types: ClusterIP (internal), NodePort (external with port mapping), LoadBalancer (cloud-native load balancer).

**Ingress**: HTTP routing rules. Single entry point that routes to multiple services by host/path.

**ConfigMap / Secret**: Configuration data separate from the container image. Secrets are base64-encoded (not encrypted — don't mistake this for security).

**HorizontalPodAutoscaler**: Scales deployment replicas based on CPU/memory or custom metrics.

Common interview scenario: "Your service is getting OOMKilled. What do you do?" Answer: Check resource limits (`kubectl describe pod`), look at memory usage trends, increase memory limits, investigate for memory leaks if usage grows unboundedly.

## Observability: Logs, Metrics, Traces

The three pillars of observability:

**Metrics**: Numerical measurements over time. Use for alerting and dashboards. Prometheus + Grafana is the standard stack. Key metric types: counter (only goes up), gauge (can go up/down), histogram (distribution, used for latency percentiles).

**Logs**: Timestamped events. Structured logging (JSON) is essential at scale — enables filtering and aggregation. ELK stack (Elasticsearch, Logstash, Kibana) or Loki + Grafana.

**Distributed traces**: Follows a request across multiple services. Jaeger, Zipkin, or Datadog APM. Essential for debugging latency in microservices.

**Interview question**: "How would you debug a service that's slow for some users but fast for others?"

Answer: Check if there's a pattern — specific geographic region (CDN issue), specific user tier (database query path), specific endpoints (one query is slow). Use distributed traces to pinpoint where latency is added. Check P99 vs P50 latency (P99 outliers suggest specific slow requests, not overload). Look for correlation with recent deploys.

## Incident Response

SRE interviews often include incident scenarios. The OODA loop (Observe, Orient, Decide, Act) applies:

1. **Detect**: Alert fires. What service is affected? What metrics are anomalous?
2. **Scope**: How many users affected? Is it degraded or down? Is it spreading?
3. **Communicate**: Alert the on-call team, post in incident channel
4. **Mitigate**: Rollback if recent deploy caused it. Traffic shift if one region is affected.
5. **Resolve**: Fix root cause
6. **Postmortem**: Document timeline, root cause, action items

Key skill: mitigation first, root cause second. Your goal is to restore service — you can analyze why it broke after users can access it again.

## Linux and Networking Fundamentals

Expect practical Linux questions:

- CPU troubleshooting: `top`, `htop`, `vmstat`, `iostat`. Know how to identify CPU steal (virtualization overhead), iowait (disk bottleneck).
- Networking: `netstat`, `ss`, `tcpdump`. Know TCP states (ESTABLISHED, TIME_WAIT, CLOSE_WAIT). Know how to identify port exhaustion.
- Process management: `ps`, `strace`, `lsof`. How to trace system calls for a running process.
- File system: `df -h` for disk usage, `du -sh *` for directory sizes, `lsof +D /path` to find files in use.

"How do you investigate high CPU on a production server?" → `top` to identify the process, `strace -p PID` to see what system calls it's making, check if it's in user space (computation) or kernel space (I/O), look for recent changes that correlate.

## Common DevOps System Design Questions

- Design a deployment system for 1000 microservices
- Design a centralized logging system for 10,000 servers
- Design a monitoring/alerting system
- How would you migrate a monolith to microservices with zero downtime?
- Design a database backup and restore system with < 1 hour RPO

For each, demonstrate: understanding of the problem scope, failure mode analysis, tradeoff discussion, and familiarity with real tools and patterns.

