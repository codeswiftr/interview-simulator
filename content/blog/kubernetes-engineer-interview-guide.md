---
title: "Kubernetes Engineer Interview Guide"
description: "Technical interview preparation for Kubernetes and container orchestration roles: pod lifecycle, scheduling, operators, networking (CNI, services, ingress), and what platform teams and cloud-native companies look for in K8s engineers."
date: "2026-03-19"
category: "Technical Skills Guides"
---

# Kubernetes Engineer Interview Guide

Kubernetes has become the default platform for running containerized workloads at scale, and the interview bar for engineers who work with it professionally has risen accordingly. Platform engineers, SREs, and infrastructure engineers at most companies now need Kubernetes depth — not just the ability to run `kubectl apply`, but genuine understanding of how it works and how to troubleshoot it.

## The Kubernetes Architecture You Must Know

Kubernetes is a distributed system. The control plane manages cluster state; nodes run workloads.

**Control plane components**:
- `kube-apiserver`: the entry point for all cluster operations; validates and stores objects in etcd; the only component that talks to etcd directly
- `etcd`: distributed key-value store holding all cluster state; the source of truth
- `kube-scheduler`: watches for unscheduled pods and assigns them to nodes based on resource requirements, affinity rules, and taints/tolerations
- `kube-controller-manager`: runs controllers (ReplicaSet controller, Node controller, Endpoint controller, etc.) that reconcile desired state with actual state

**Node components**:
- `kubelet`: agent on each node; watches for pods assigned to its node, manages container lifecycle via CRI (Container Runtime Interface)
- `kube-proxy`: maintains network rules for service routing (iptables or IPVS)
- Container runtime (containerd or CRI-O): runs containers

Interview question: "A pod is scheduled but not starting. How do you diagnose it?" Walk through: `kubectl describe pod` (events section), `kubectl logs`, check node resource pressure, check image pull status, inspect init containers, review security context.

## Pod Lifecycle and Resource Management

**Resource requests and limits**: Requests are used for scheduling (the scheduler places pods on nodes with sufficient capacity). Limits are enforced at runtime (CPU throttling, OOM kill for memory). Setting requests without limits is risky — a pod can consume all node CPU. Setting requests equal to limits (Guaranteed QoS) prevents throttling.

**QoS classes**: Guaranteed (requests == limits), Burstable (requests < limits), BestEffort (no requests or limits). Under memory pressure, BestEffort pods are evicted first.

**Pod disruption budgets (PDBs)**: Minimum available replicas during voluntary disruptions (node drain, rolling update). Prevents Kubernetes from evicting too many pods at once. Often forgotten when designing highly available services.

**Probes**: Liveness (restart container if fails — use carefully; aggressive liveness probes cause cascading restarts under load), Readiness (remove from service endpoints if fails — use to stop traffic during startup/overload), Startup (delays liveness/readiness checks during slow startup).

## Scheduling: Affinity, Taints, and Tolerations

**Node affinity**: Soft (preferred) or hard (required) rules for which nodes a pod can run on. Based on node labels. Example: require pods to run on nodes labeled `zone=us-west-2a`.

**Pod affinity/anti-affinity**: Spread pods across topology (anti-affinity) or co-locate related pods (affinity). Anti-affinity is the more common use case — ensure replicas land on different nodes or availability zones.

**Taints and tolerations**: Taints mark nodes as restricted; tolerations allow pods to run on tainted nodes. Use case: reserve GPU nodes for GPU workloads, or prevent non-system workloads from running on master nodes.

**TopologySpreadConstraints**: The modern way to spread pods across zones. More flexible than pod anti-affinity for multi-zone deployments.

## Kubernetes Networking

Networking is where most Kubernetes complexity lives:

**Pod networking (CNI)**: Every pod gets its own IP. The CNI plugin (Calico, Cilium, Flannel, AWS VPC CNI) implements pod-to-pod routing. Cilium (eBPF-based) is increasingly preferred for performance and network policy flexibility.

**Services**: Abstract a set of pods behind a stable IP. ClusterIP (internal only), NodePort (expose on each node's IP), LoadBalancer (provision a cloud load balancer). Services use label selectors to route to pods — pods matching the selector join the service's endpoint list.

**kube-proxy and iptables**: The default service implementation uses iptables rules to DNAT packets to random pod endpoints. Under high connection rates, iptables rule chains become a bottleneck — IPVS mode scales better.

**Ingress and IngressController**: L7 HTTP routing. The Ingress resource defines rules; the IngressController (nginx-ingress, Traefik, AWS ALB controller) implements them. Gateway API is the newer, more expressive replacement.

**Network policies**: Firewall rules for pod-to-pod traffic. By default, Kubernetes allows all pod-to-pod communication. Network policies (implemented by CNI) restrict traffic. Zero-trust: deny all, then explicitly allow needed paths.

## Operators and Custom Resources

Operators encode operational knowledge as code. A custom controller watches a Custom Resource Definition (CRD) and reconciles it — similar to how kube-controller-manager reconciles Deployments.

Interview question: "When would you write a Kubernetes Operator?" Good answers: when you have a stateful application with complex lifecycle management (database with leader election, backup/restore), or when you need to manage a complex multi-resource application as a single logical unit. Operators are engineering investments — don't write one when a Helm chart or simple controller would suffice.

## Troubleshooting Scenarios

Expect scenario-based questions:
- "Pods are evicted frequently on one node" → Node resource pressure (memory/disk), PDBs are misconfigured, noisy neighbor pods
- "Service routes traffic to wrong pods" → Label selector mismatch, endpoints not populated, pod not passing readiness probe
- "Rolling update is stalled" → PDB preventing eviction, not enough capacity for new pods, new pods failing readiness probe

The diagnostic toolkit: `kubectl describe`, `kubectl logs --previous`, `kubectl exec` for in-container debugging, `kubectl debug` (ephemeral containers), Metrics Server for resource usage, events sorted by time.

Kubernetes depth is best demonstrated through production experience — the specificity of your troubleshooting stories matters more than knowing every API field.
