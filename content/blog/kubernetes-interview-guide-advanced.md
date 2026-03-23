---
title: "Advanced Kubernetes Interview Guide: Architecture, Production Patterns, and Debugging"
description: "Deep-dive Kubernetes interview preparation — control plane internals, scheduling, resource management, network policies, security contexts, and debugging production issues at senior and staff level."
date: "2026-03-20"
category: "DevOps & Infrastructure"
---

# Advanced Kubernetes Interview Guide: Architecture, Production Patterns, and Debugging

Kubernetes interviews for senior engineers go well beyond `kubectl apply` and basic pod specs. Interviewers probe your understanding of the control plane, scheduler behavior, networking internals, and how you'd diagnose a production incident. This guide covers the topics that separate engineers who've run Kubernetes at scale from those who've only used it casually.

## Control Plane Architecture

The Kubernetes control plane consists of four components:

**etcd**: Distributed key-value store holding all cluster state. It's the source of truth. Every object — pods, services, configmaps, secrets — is stored here. etcd uses Raft consensus for distributed consistency. A majority of members must be healthy for writes to succeed, which is why you always run odd numbers (3 or 5) of etcd nodes.

**API Server**: The single entry point for all cluster operations. Validates and processes requests, reads/writes state from etcd, and notifies watchers of state changes. Every `kubectl` command, every controller, every kubelet communicates through the API server. It's stateless — you can run multiple replicas behind a load balancer.

**Controller Manager**: Runs all the built-in controllers as goroutines. The ReplicaSet controller watches for pods being deleted and creates replacements. The Node controller detects node failures. The Endpoints controller updates service endpoint lists. Controllers are reconciliation loops: observe current state, compare to desired state, take action to converge them.

**Scheduler**: Watches for newly created pods with no assigned node. Runs them through filtering (which nodes are eligible?) and scoring (which is best?). Filtering checks: resource requests fit, taints/tolerations match, node affinity rules satisfied, pod anti-affinity not violated. Scoring ranks by resource balance, affinity preferences, and pod topology spread.

## Pod Lifecycle and Restarts

Understanding pod lifecycle is critical for debugging production issues.

A pod goes through: `Pending → Running → Succeeded/Failed`. Within `Running`, containers can be `Running`, `Waiting`, or `Terminated`.

**CrashLoopBackOff** is the most common production issue. The container starts, exits with a non-zero code, and Kubernetes restarts it with exponential backoff (10s, 20s, 40s... up to 5 minutes). Diagnose with: `kubectl logs pod --previous` (logs from the crashed container) and `kubectl describe pod` (check exit code and events).

**OOMKilled** means the container exceeded its memory limit. The kernel OOM killer terminated it. Fix: increase memory limits, find the memory leak, or implement graceful memory management.

**ImagePullBackOff** means the container image can't be pulled. Check image name, tag, and registry credentials (imagePullSecrets).

## Resource Requests and Limits

Resources in Kubernetes have two values:
- **Request**: What the pod is guaranteed. The scheduler uses this to find a fitting node.
- **Limit**: The maximum the pod can use. The kubelet enforces this via cgroups.

CPU is compressible: exceeding CPU limits causes throttling, not termination. Memory is not compressible: exceeding memory limits causes OOMKill.

**Quality of Service (QoS) classes** determine eviction priority:
- **Guaranteed**: requests == limits for all containers. Never evicted except when node runs out of uncompressible resources.
- **Burstable**: requests < limits. Evicted before Guaranteed pods.
- **BestEffort**: no requests or limits set. Evicted first.

For production services, use Guaranteed or Burstable with carefully tuned values. BestEffort is suitable only for non-critical batch work.

## Networking and Services

Every pod gets a unique IP in Kubernetes's flat network model. Pods can communicate directly without NAT. This is implemented by CNI plugins (Calico, Flannel, Cilium).

**Service types**:
- **ClusterIP**: Internal only. A stable virtual IP that load-balances across pod endpoints. Implemented by kube-proxy via iptables or IPVS rules.
- **NodePort**: Exposes the service on each node's IP at a static port (30000-32767). Accessible from outside the cluster.
- **LoadBalancer**: Creates a cloud load balancer (AWS ELB, GCP GLBC). Used for external-facing services.
- **ExternalName**: DNS CNAME to an external service. No proxying.

**Service endpoints and readiness**: A pod is added to a service's endpoint list only when its readiness probe passes. This is critical — deploy without readiness probes and Kubernetes will send traffic to pods still initializing, causing errors.

## Network Policies

By default, all pods can communicate with all other pods. Network Policies restrict traffic at the pod level, acting as a firewall.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes: [Ingress]
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - port: 8080
```

This allows only pods labeled `app: frontend` to reach `app: backend` on port 8080. All other ingress is denied. Network Policies require a CNI plugin that supports them (Calico, Cilium — Flannel does not).

## RBAC and Security Contexts

**RBAC** controls what API operations principals (users, service accounts) can perform. The key objects: `Role`/`ClusterRole` (what operations are allowed), `RoleBinding`/`ClusterRoleBinding` (who gets those permissions).

**Security Contexts** control Linux security settings for pods and containers:
- `runAsNonRoot: true` — prevent root containers
- `readOnlyRootFilesystem: true` — prevent writes to the container filesystem
- `allowPrivilegeEscalation: false` — prevent setuid binaries from escalating privileges
- `capabilities` — drop Linux capabilities not needed (most containers only need `NET_BIND_SERVICE`)

## Debugging Production Issues

When a production service degrades on Kubernetes:

1. `kubectl get pods -n namespace` — identify pod states
2. `kubectl describe pod <pod>` — events, resource usage, exit codes
3. `kubectl logs <pod> --previous` — logs from crashed container
4. `kubectl top pods` — current CPU/memory usage (requires metrics-server)
5. `kubectl exec -it <pod> -- /bin/sh` — shell into running container
6. Check HPA: `kubectl describe hpa` — is the autoscaler failing to scale?
7. Check node pressure: `kubectl describe node <node>` — disk, memory, PID pressure

This systematic approach — pod state, events, logs, metrics — resolves 80% of Kubernetes production issues.
