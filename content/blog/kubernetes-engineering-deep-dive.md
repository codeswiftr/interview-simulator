---
title: "Kubernetes Engineering Deep Dive: What Companies Like Google, Spotify, and Airbnb Actually Ask"
date: 2026-03-19
tags: [kubernetes, system-design, devops, interview-prep, cloud-native]
description: "A technical interview guide covering the Kubernetes problems that engineering teams at Google, Spotify, Airbnb, and Lyft actually care about — from pod scheduling to service mesh to production incident postmortems."
---

## The Kubernetes Interview Landscape

Companies running Kubernetes at scale — Google, Spotify, Airbnb, Lyft, Datadog, Cloudflare — don't ask trivia. They ask whether you've been paged at 2am because a deployment went sideways, whether you understand *why* the scheduler placed a pod on that node, and whether you can reason about failure modes under load. The interview is a proxy for production judgment.

This guide covers the five core areas that consistently appear, what depth of understanding is expected, and how to frame your answers.

---

## Pod Scheduling: The Scheduler Is Not Magic

Most candidates treat pod scheduling as a black box. Interviewers at companies with large clusters treat it as a first-class topic.

**What gets asked:**
- How does the Kubernetes scheduler assign pods to nodes?
- What happens when no node satisfies a pod's constraints?
- Explain node affinity vs. pod affinity vs. taints/tolerations.

The scheduler runs in two phases: **filtering** (eliminate nodes that don't satisfy hard constraints) and **scoring** (rank remaining nodes by soft preferences). A pod that can't be scheduled enters `Pending` state and the scheduler keeps retrying — important to understand for capacity planning.

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: topology.kubernetes.io/zone
              operator: In
              values: [us-east-1a, us-east-1b]
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
              - key: app
                operator: In
                values: [frontend]
          topologyKey: kubernetes.io/hostname
```

The `podAntiAffinity` above spreads frontend pods across different nodes — a common pattern for high availability. Know the difference between `required` (hard) and `preferred` (soft) scheduling rules and when each is appropriate.

**Taints and tolerations** are the inverse: they let nodes *repel* pods unless the pod explicitly tolerates the taint. Common production use: dedicated GPU nodes, spot/preemptible nodes, nodes under maintenance.

---

## Resource Limits and the OOMKiller

Misconfigured resource requests and limits are responsible for a significant share of production incidents. This topic comes up in both technical and behavioral rounds.

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "1000m"
```

**Requests** affect scheduling — the scheduler uses them to determine node fit. **Limits** affect runtime behavior — exceeding CPU limits causes throttling; exceeding memory limits causes the container to be OOM-killed.

A common trap: setting CPU limits too low causes throttling even when the node has spare CPU, because Kubernetes uses CFS (Completely Fair Scheduler) quotas. The result is unpredictable latency spikes. Several companies (including Airbnb) have written about removing CPU limits entirely in some services and relying on requests + VPA instead.

Be ready to explain the three QoS classes:
- **Guaranteed**: requests == limits for all containers
- **Burstable**: requests < limits
- **BestEffort**: no requests or limits set

Under node pressure, the kubelet evicts BestEffort pods first, then Burstable (lowest priority first), then Guaranteed last.

---

## Horizontal Pod Autoscaler and Scaling Dynamics

HPA is a standard interview topic at Spotify, Lyft, and similar companies with variable traffic patterns.

HPA polls the metrics API at a configurable interval (default 15s) and adjusts replicas based on observed vs. target metric values. The default metric is CPU utilization, but production HPA configs typically use custom or external metrics (RPS, queue depth, p99 latency).

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: payment-service
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payment-service
  minReplicas: 3
  maxReplicas: 50
  metrics:
    - type: Pods
      pods:
        metric:
          name: requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

The `behavior` section is where most candidates fall short. `stabilizationWindowSeconds` prevents flapping — HPA won't scale down until the metric has been below the threshold for 5 minutes continuously. The scale-down policy here limits scale-down to 10% of pods per minute. Know why aggressive scale-down can be dangerous (cold start latency, in-flight requests) and how to tune these parameters.

**Interview trap:** "If HPA is configured but the pods aren't scaling, what do you check?" Walk through: Is the metrics server running? Are resource requests set (required for CPU-based HPA)? Is the current replica count at `maxReplicas`? Are there PodDisruptionBudgets blocking eviction?

---

## Rolling Deployments and Zero-Downtime Updates

This is a universal topic. The question isn't "what is a rolling update" — it's "how do you ensure zero downtime during a rolling update at Spotify's scale."

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 0
    maxSurge: 25%
```

`maxUnavailable: 0` ensures no capacity is lost during the rollout. `maxSurge: 25%` allows up to 25% extra pods during the transition. For a 100-replica deployment, this means 25 new pods come up before any old pods are terminated.

The other side of zero-downtime is **graceful shutdown**. When a pod receives SIGTERM, it has `terminationGracePeriodSeconds` (default 30s) to finish in-flight requests. The application must handle SIGTERM correctly — drain connections, finish current requests, exit cleanly. Failing to do this means request errors during every deployment.

Also critical: **readiness probes**. A pod isn't added to Service endpoints until its readiness probe passes. Liveness probes kill and restart unhealthy containers. Misconfigured probes (too aggressive liveness probes, missing readiness probes) are a common source of production incidents.

---

## Service Mesh: Why and When

At companies like Lyft (Envoy was created there) and Airbnb, service mesh knowledge is expected. The core question: what problems does a service mesh actually solve?

The honest answer: mutual TLS (mTLS) between services, traffic shaping (canary deployments, circuit breaking, retries), and observability (distributed tracing, metrics) without modifying application code. Envoy sidecar proxies intercept all inbound/outbound traffic.

Interview questions tend to be practical:
- "How would you do a canary deploy to 5% of traffic?" (VirtualService weight splitting in Istio, or weighted TargetGroupBindings in Envoy)
- "A service is returning 500s intermittently — how does the mesh help you debug it?" (Check Envoy access logs, look at retry budget exhaustion, check circuit breaker state)
- "What's the overhead of a service mesh?" (Latency: 1-10ms per hop for sidecar proxy. Memory: ~50MB per Envoy sidecar. These matter at thousands of pods.)

---

## System Design Questions Involving Kubernetes

At senior levels, expect: "Design a globally distributed batch processing system" or "How would you architect Spotify's podcast processing pipeline on Kubernetes?"

Key concepts to weave in:
- **Namespaces + RBAC** for multi-tenant isolation
- **Jobs and CronJobs** for batch workloads, including handling pod failures and retry limits
- **PodDisruptionBudgets** to ensure maintenance doesn't take down too many replicas simultaneously
- **Cluster Autoscaler** to provision new nodes when pods are unschedulable, and how it interacts with HPA
- **StatefulSets vs. Deployments** — StatefulSets for ordered, stable pod identities (databases, Kafka, ZooKeeper); Deployments for stateless services

---

## Behavioral Questions: Production Incidents

Expect at least one behavioral question about a Kubernetes production incident. Prepare a STAR-format story covering:

- A service degradation caused by resource misconfigurations (OOM kills, CPU throttling)
- A failed deployment that required rollback (`kubectl rollout undo deployment/name`)
- A node failure and how pod rescheduling behaved
- A networking issue — DNS resolution failures, service endpoint churn during rollouts

The answer should demonstrate that you understand *why* things failed at the infrastructure level, not just that you ran some commands and it got better.

---

## What to Study

**Official documentation:**
- [kubernetes.io/docs](https://kubernetes.io/docs/) — especially the Concepts section on Workloads, Scheduling, and Configuration

**Hands-on practice:**
- [KillerCoda Kubernetes scenarios](https://killercoda.com/kubernetes) — free browser-based K8s environments with real clusters
- [killer.sh](https://killer.sh) — CKA/CKAD exam simulator, harder than the real exam

**Certifications worth getting:**
- **CKA (Certified Kubernetes Administrator)** — most relevant for SRE/platform roles
- **CKAD (Certified Kubernetes Application Developer)** — more relevant for backend engineers deploying to K8s

**Papers and engineering blogs:**
- Borg, Omega, and Kubernetes (Google paper — free on ACM)
- Airbnb engineering blog: "Kubernetes at Airbnb"
- Lyft engineering blog: "Envoy: C++ L7 proxy and communication bus"
- Spotify engineering: "Handling 1M+ RPM with Kubernetes"

**The fastest path to interview-readiness:** Spin up a KillerCoda environment, deploy a multi-container application with HPA and proper resource requests/limits, intentionally break it (kill pods, exhaust memory, trigger OOM), and fix it. One hour of hands-on debugging teaches more than a week of reading.
