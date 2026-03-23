---
title: "Kubernetes Engineering Interview Guide: Pod Lifecycle, Operators, CRDs, and Production Reliability"
description: "Comprehensive Kubernetes engineer interview guide covering pod lifecycle management, writing operators and CRDs, production reliability patterns, and what senior K8s roles actually test."
date: "2026-03-20"
category: "System Design"
---

# Kubernetes Engineering Interview Guide

Kubernetes engineering interviews range from "can you write a Deployment manifest" to "design a multi-cluster federation for five regions with sub-50ms failover." This guide targets mid-to-senior K8s roles and assumes you already know `kubectl apply` — the depth here is what separates candidates who have run K8s from candidates who have built on and operated it at scale.

## What the Interview Actually Tests

Senior K8s interviews test four distinct competencies:

1. **Internals understanding**: Can you explain what happens when you `kubectl apply -f deployment.yaml`?
2. **Operational judgment**: Given a production incident, how do you diagnose it systematically?
3. **Extension design**: Can you write a controller or operator that safely manages custom resources?
4. **Architecture**: Can you design multi-cluster, multi-region K8s infrastructure with real tradeoffs?

## Pod Lifecycle: Deep Dive

"What happens when a pod is created?" is the K8s equivalent of "what happens when you type a URL in a browser." Know every step.

**Creation flow:**
1. `kubectl apply` sends the manifest to the API server
2. API server persists the resource to etcd, returns 201
3. The **scheduler** watches for unscheduled pods (pods with no `spec.nodeName`)
4. Scheduler selects a node based on resources, affinity, taints/tolerations
5. Scheduler writes the selected node to the pod's `spec.nodeName` in etcd
6. The **kubelet** on the selected node watches for pods assigned to it
7. Kubelet calls the **container runtime** (containerd/CRI-O) via CRI
8. Container runtime pulls the image, creates the container, starts it
9. Kubelet runs liveness/readiness probes; updates pod status

**Termination flow (the critical part):**
1. `kubectl delete pod` → API server sets `deletionTimestamp` on pod
2. Kubelet sends `SIGTERM` to the main container process
3. **Grace period** countdown begins (`terminationGracePeriodSeconds`, default 30s)
4. If container hasn't exited after grace period, kubelet sends `SIGKILL`
5. Pod status moves to `Terminating` → `Terminated`
6. **kube-proxy** updates iptables rules to stop routing traffic to the pod
7. **Endpoints controller** removes the pod from the Endpoints object

**Common interview failure:** Not knowing that kube-proxy and the kubelet act concurrently — this means there's a brief window where SIGTERM is sent but traffic is still routed to the pod. The mitigation is a `preStop` hook with a sleep:

```yaml
lifecycle:
  preStop:
    exec:
      command: ["sleep", "5"]
```

This gives kube-proxy time to drain traffic before the process terminates.

## Operators and CRDs

This is where many candidates plateau. Know the full operator pattern.

**CRD definition:**
```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: databases.forge.io
spec:
  group: forge.io
  versions:
    - name: v1alpha1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                replicas:
                  type: integer
                engine:
                  type: string
                  enum: [postgres, mysql]
  scope: Namespaced
  names:
    plural: databases
    singular: database
    kind: Database
```

**Controller reconciliation loop (using controller-runtime):**
```go
func (r *DatabaseReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    log := log.FromContext(ctx)

    // Fetch the Database resource
    db := &forgev1alpha1.Database{}
    if err := r.Get(ctx, req.NamespacedName, db); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }

    // Check if a StatefulSet already exists
    sts := &appsv1.StatefulSet{}
    err := r.Get(ctx, req.NamespacedName, sts)
    if errors.IsNotFound(err) {
        // Create the StatefulSet
        newSts := r.buildStatefulSet(db)
        if err := r.Create(ctx, newSts); err != nil {
            return ctrl.Result{}, err
        }
        return ctrl.Result{Requeue: true}, nil
    }

    // Reconcile: ensure desired state matches current state
    if sts.Spec.Replicas != &db.Spec.Replicas {
        sts.Spec.Replicas = &db.Spec.Replicas
        if err := r.Update(ctx, sts); err != nil {
            return ctrl.Result{}, err
        }
    }

    return ctrl.Result{}, nil
}
```

**Key operator design principles:**
- **Idempotent reconciliation**: Running reconcile twice should produce the same result
- **Level-triggered, not edge-triggered**: React to the current state, not the event that triggered the reconcile
- **Owner references**: Set `ownerReferences` on child resources so they're garbage collected when the parent is deleted
- **Status conditions**: Update `.status.conditions` to communicate state to users

## Production Reliability Patterns

**Resource requests and limits:**
```yaml
resources:
  requests:
    cpu: "250m"
    memory: "256Mi"
  limits:
    cpu: "1000m"
    memory: "512Mi"
```

`requests` are used for scheduling. `limits` enforce runtime constraints. A common mistake: setting `limits` without `requests` — the scheduler doesn't know the resource cost. Another: setting CPU limits on latency-sensitive workloads — CPU throttling can cause tail latency spikes even without memory pressure.

**Pod Disruption Budgets (PDB):**
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: web
```

PDBs prevent voluntary disruptions (node drains, rolling updates) from taking too many pods offline simultaneously. Always have one for stateful or critical workloads.

**Horizontal Pod Autoscaler with custom metrics:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  metrics:
    - type: External
      external:
        metric:
          name: queue_depth
          selector:
            matchLabels:
              queue: payment-processor
        target:
          type: AverageValue
          averageValue: "30"
```

Custom metrics (from Prometheus via `kube-state-metrics` + `metrics-server` + custom adapter) let you scale on business metrics, not just CPU.

## Multi-Cluster and Federation

A senior K8s design question: "Design a payment processing system across three regions with K8s."

Key components:
- **Cluster per region**: Isolation boundary, independent control planes
- **Global load balancing**: Anycast DNS or GCP Global Load Balancer for cross-region traffic
- **Configuration management**: Flux CD or ArgoCD with a "fleet" repository pattern — one repo, multiple cluster targets
- **Cross-cluster service discovery**: Submariner or Istio multi-primary for service mesh federation
- **State replication**: Databases replicate independently; K8s is stateless by design

## Common Interview Questions and Model Answers

**Q: What's the difference between a DaemonSet and a Deployment?**
A: DaemonSet ensures one pod per node (or per node matching a selector) — use for node-level agents (logging, monitoring). Deployment manages a specified replica count distributed across available nodes.

**Q: How does K8s handle a node failure?**
A: kube-controller-manager's node lifecycle controller marks node as `NotReady` after 40s. After `pod-eviction-timeout` (default 5 minutes), it evicts pods and reschedules them. StatefulSets are more conservative about this — they wait by default.

**Q: How do you safely roll back a broken deployment?**
A: `kubectl rollout undo deployment/NAME` — reverts to previous ReplicaSet. Always set `revisionHistoryLimit` to keep enough history. For production, use a canary deployment strategy (Argo Rollouts or Flagger) to catch issues before full rollout.

**Q: Explain etcd's role and what happens if it goes down.**
A: etcd is K8s's distributed key-value store — the single source of truth. If etcd is unavailable, the API server can't read or write cluster state. Running pods continue running (kubelet operates independently), but no new scheduling, scaling, or config changes are possible. Always run etcd as a 3 or 5-node cluster for quorum.

## Interview Preparation Checklist

- Deploy a stateful workload (PostgreSQL) with persistent volumes, PDB, and HPA
- Write a simple operator using controller-runtime
- Diagnose a CrashLoopBackOff, OOMKilled, and ImagePullBackOff in a test cluster
- Explain the kube-proxy iptables model vs IPVS mode
- Describe the admission webhook pipeline (mutating vs validating)
- Know your CNI plugins: Flannel vs Calico vs Cilium and when to use each

K8s engineering interviews reward operational experience. Pair your conceptual answers with "and here's a production incident where this mattered" — that's what separates a candidate who read the docs from one who's actually operated the system.
