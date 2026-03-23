---
title: "Kubernetes Production Guide: Cluster Management, Security, and Reliability Patterns"
description: "Advanced Kubernetes for engineering interviews — cluster architecture, networking, RBAC, pod security, autoscaling, and operating Kubernetes reliably in production."
date: "2026-03-20"
category: "DevOps & SRE"
---

# Kubernetes Production Guide: Cluster Management, Security, and Reliability Patterns

Basic Kubernetes knowledge (deployments, services, pods) is table stakes. Senior DevOps and platform engineering interviews go deeper: cluster architecture, networking internals, security hardening, and the operational patterns that keep production clusters reliable. Here's what advanced Kubernetes interviews test.

## Cluster Architecture

A Kubernetes cluster has control plane nodes and worker nodes. The control plane runs: API Server (the gateway for all operations, validates and stores state), etcd (distributed key-value store for all cluster state — highly available etcd is critical), Controller Manager (runs controllers that reconcile actual state to desired state), and Scheduler (assigns pods to nodes based on resource requests, affinity, taints, and tolerations).

Worker nodes run: Kubelet (talks to the API server, manages pods on the node), kube-proxy (implements Service networking using iptables or IPVS), and the container runtime (containerd or CRI-O — Docker shim was removed in Kubernetes 1.24).

**High availability control plane:** In production, run 3 or 5 control plane nodes (odd number for etcd quorum). API server is stateless and load-balanced. etcd requires quorum — with 3 nodes, can tolerate 1 failure; with 5 nodes, can tolerate 2 failures.

## Networking Deep Dive

**Pod networking:** Every pod gets a unique IP. All pods can communicate with all other pods without NAT. This is the Kubernetes network model requirement — CNI plugins (Calico, Cilium, Flannel, Weave) implement it.

**Service networking:** A Service gets a stable ClusterIP (virtual IP). kube-proxy writes iptables rules that DNAT packets destined for the ClusterIP to one of the endpoint pods. With IPVS mode, uses Linux IPVS for more efficient load balancing at scale.

**DNS:** CoreDNS runs as a cluster add-on. Service DNS: `service-name.namespace.svc.cluster.local`. Pod DNS: `pod-ip-with-dashes.namespace.pod.cluster.local`. Applications should use service DNS names, not IPs.

**NetworkPolicy:** Acts as a layer 3/4 firewall. By default, all pod-to-pod communication is allowed. NetworkPolicy rules select pods by labels and restrict ingress/egress. Requires a CNI plugin that supports NetworkPolicy (Calico, Cilium — Flannel doesn't support it).

Best practice: default-deny all traffic in a namespace, then explicitly allow required communications:
```yaml
kind: NetworkPolicy
spec:
  podSelector: {}  # Apply to all pods in namespace
  policyTypes: [Ingress, Egress]
  # No ingress/egress rules = deny all
```

## Security Hardening

**RBAC:** Role-based access control for all Kubernetes API operations. Create per-application ServiceAccounts with minimal permissions. Avoid the `cluster-admin` ClusterRole for applications — it grants full cluster access.

**Pod Security Standards:** Replaced the deprecated PodSecurityPolicy. Three levels: Privileged (no restrictions), Baseline (prevents obvious privilege escalations), Restricted (heavily restricted, follows security best practices). Apply at the namespace level:
```yaml
metadata:
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
```

**Secrets management:** Kubernetes Secrets are base64 encoded, not encrypted. Enable encryption at rest for etcd. Better: use external secrets managers (HashiCorp Vault, AWS Secrets Manager) with the External Secrets Operator syncing secrets into Kubernetes Secrets — avoids storing sensitive data in etcd unencrypted.

**Image security:** Always specify digest-pinned image references (`image: nginx@sha256:abc123`) in production — tags are mutable. Scan images with Trivy or Snyk in CI. Enforce image policies with OPA Gatekeeper or Kyverno (reject deployments with `latest` tag or unscanned images).

## Autoscaling

Three types of autoscaling:

**HPA (Horizontal Pod Autoscaler):** Scales pod count based on metrics (CPU, memory, or custom metrics from Prometheus via metrics-server or KEDA). Reacts to current load. Suitable for stateless services.

**VPA (Vertical Pod Autoscaler):** Adjusts pod resource requests/limits based on historical usage. Requires pod restarts (in `Auto` mode). Use in `Recommend` mode to get suggestions without automatic changes.

**Cluster Autoscaler:** Scales the number of nodes based on pod scheduling failures (scale up) and node utilization (scale down). Works with cloud provider node groups. Configure min/max node count per node group.

**KEDA (Kubernetes-based Event Driven Autoscaling):** Scales deployments to zero based on event sources (Kafka consumer lag, SQS queue depth, cron schedules). Enables scale-to-zero for cost efficiency.

## Reliability Patterns

**Pod Disruption Budgets (PDB):** Limit the number of pods that can be disrupted during voluntary disruptions (node drains, rolling updates). Ensures a minimum number of pods remain available.

```yaml
spec:
  minAvailable: 2  # At least 2 pods must be running
  selector:
    matchLabels:
      app: my-service
```

**Resource quotas:** Limit total resource consumption per namespace. Prevents one team from consuming all cluster resources. Enforce with `ResourceQuota` objects.

**Readiness probes:** Remove pods from service endpoints when they're not ready. Prevents traffic from hitting pods during startup or when temporarily overloaded.

**Topology spread constraints:** Spread pods across failure domains (zones, nodes) to improve availability:
```yaml
topologySpreadConstraints:
- maxSkew: 1
  topologyKey: topology.kubernetes.io/zone
  whenUnsatisfiable: DoNotSchedule
  labelSelector:
    matchLabels:
      app: my-service
```

## Observability

**Prometheus + Grafana:** Standard monitoring stack. kube-state-metrics exposes Kubernetes object metrics. Node exporter exposes node metrics. Application pods expose /metrics endpoints scraped by Prometheus.

**Key alerts:** Pod crash loop (restartCount > N), persistent volume nearly full, API server latency, etcd latency, node not ready, deployment rollout stuck.

**Logging:** Ship container logs (stdout/stderr) to centralized logging with Fluentd/Fluent Bit DaemonSet → Elasticsearch/Loki.

Kubernetes interviews at platform engineering and SRE roles go deep on these topics. Pair this with hands-on experience — run a production-like cluster with these patterns applied. Understanding comes from operating, not just reading.
