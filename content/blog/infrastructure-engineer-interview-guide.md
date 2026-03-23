---
title: "Infrastructure Engineer Interview Guide: Cloud, IaC & Systems Design"
description: "Ace infrastructure engineering interviews — AWS/GCP/Azure architecture, Terraform, Kubernetes, networking, observability, and cloud cost optimization."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

# Infrastructure Engineer Interview Guide: Cloud, IaC & Systems Design

Infrastructure engineers build and operate the platforms that development teams rely on — cloud environments, container orchestration, CI/CD pipelines, networking, and observability stacks. Interviews for these roles blend systems design, hands-on cloud knowledge, and operational experience. This guide prepares you for what modern infrastructure interviews actually test.

## Cloud Architecture and Systems Design

Systems design questions are the centerpiece of infrastructure interviews. Unlike software engineering system design, infrastructure interviews emphasize operational concerns: fault tolerance, blast radius, cost efficiency, and operational complexity.

**Multi-region and availability zone design**: Know how to design for 99.99% availability. Active-active vs. active-passive multi-region, data replication strategies (synchronous vs. asynchronous), and the tradeoffs in RTO/RPO. Interviewers at companies like Netflix or Stripe want to see you reason about failure domains and cascade failure prevention.

**Compute architecture**: EC2/GCE instance selection (CPU vs. memory optimized, spot/preemptible instances for cost optimization), container orchestration on EKS/GKE/AKS, serverless (Lambda/Cloud Functions) for event-driven workloads. Know when each model is appropriate.

**Networking fundamentals**: VPC design, subnet CIDR planning (leaving room for growth), route tables, security groups vs. network ACLs, NAT gateway patterns, VPN vs. Direct Connect/Dedicated Interconnect. Transit Gateway for multi-VPC architectures. These appear as design questions and coding challenges.

**Storage tiers**: Object storage (S3/GCS) for durable data, EFS/GFS for shared file systems, EBS for block storage, ElastiCache/Memorystore for caching, and the performance and cost tradeoffs of each.

## Infrastructure as Code: Terraform Deep Dive

IaC proficiency is non-negotiable for modern infrastructure roles. Terraform dominates, with CDK and Pulumi growing:

**State management**: Remote state in S3/GCS with DynamoDB/Firestore locking, state encryption, state isolation by environment and team. Interviewers ask about what happens when state gets corrupted and how you prevent/recover from it.

**Module design**: Composable, reusable Terraform modules with clear input/output contracts. Understanding when to use data sources vs. resources, `count` vs. `for_each` for dynamic resources, and the `depends_on` escape hatch and why it signals design problems.

**Workspace strategies**: Terraform workspaces vs. separate state files vs. separate accounts per environment. Know the tradeoffs — workspaces share a single backend config, which limits blast radius separation.

**Drift detection and remediation**: How do you handle manual changes to infrastructure (drift)? Terraform plan shows drift, but who acts on it? Understanding `terraform import`, `terraform state mv`, and when to abandon and re-create resources.

Interview question: "Walk me through how you'd structure Terraform for a startup that needs to support 5 engineering teams, 3 environments (dev/staging/prod), and separate AWS accounts for security isolation." Strong answers demonstrate module hierarchy, account vending machines, and clear change management processes.

## Kubernetes Operations

Kubernetes expertise is required at most cloud-native companies:

**Cluster architecture**: Control plane components (API server, etcd, controller manager, scheduler), worker node components (kubelet, kube-proxy, container runtime). Understanding what happens during `kubectl apply` end-to-end — API server validation, admission controllers, etcd write, controller reconciliation, scheduler decision, kubelet execution.

**Resource management**: Requests vs. limits, QoS classes (Guaranteed/Burstable/BestEffort), VPA vs. HPA vs. KEDA for scaling. Knowing how requests affect scheduling decisions and how limits affect OOM kill behavior is essential.

**Networking**: CNI plugins (Calico, Cilium, Flannel), service types (ClusterIP/NodePort/LoadBalancer), Ingress controllers (nginx, Traefik, AWS ALB), Network Policies for pod-level firewalling. Cilium's eBPF-based approach is worth knowing as it becomes standard.

**Storage**: PersistentVolumes and PersistentVolumeClaims, StorageClasses, dynamic provisioning, StatefulSet pod identity and stable storage. CSI drivers for cloud-native storage.

**Troubleshooting patterns**: Systematic debugging from `kubectl describe pod` → `kubectl logs` → node resource pressure → network policy blocking → image pull failures. Interviewers present broken cluster scenarios and evaluate your mental model.

## Observability: The Operational Lens

Infrastructure engineers own observability platforms:

**The three pillars**: Metrics (Prometheus/CloudWatch/Datadog), logs (ELK/OpenSearch/CloudWatch Logs/Loki), traces (Jaeger/Zipkin/AWS X-Ray). Know OpenTelemetry as the unifying standard for instrumentation.

**SLO design**: Defining meaningful SLIs (latency, error rate, availability), setting realistic SLOs (don't set 99.99% unless you can achieve it), and error budgets. How error budgets gate feature releases vs. reliability work.

**Alerting philosophy**: Alert on symptoms, not causes. Avoid alert fatigue through tuning and aggregation. PagerDuty/OpsGenie routing, escalation policies, and runbook automation.

## Practical Preparation

- Get AWS Solutions Architect Associate or Professional certified — it forces breadth
- Deploy a complete production-like environment with Terraform: VPC, EKS cluster, RDS, ALB, Route53, ACM
- Set up a full observability stack: Prometheus, Grafana, Loki, and OpenTelemetry instrumentation
- Practice incident response: use GameDay exercises to simulate failures and practice runbook execution
- Study AWS Well-Architected Framework pillars — interviewers ask about them directly

Infrastructure roles reward engineers who think in failure modes, cost efficiency, and operational leverage. The best candidates combine deep technical knowledge with the operational mindset of someone who has been paged at 3am.
