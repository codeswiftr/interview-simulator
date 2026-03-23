---
title: "Docker and Kubernetes Interview Guide: Containers, Orchestration, and Production"
description: "Complete interview preparation for Docker and Kubernetes questions covering image layers, networking, Kubernetes architecture, scheduling, resource management, and production patterns."
date: "2026-03-20"
category: "Technical Skills"
---

# Docker and Kubernetes Interview Guide: Containers, Orchestration, and Production

Container interviews span a wide range — from understanding how Linux namespaces underpin Docker to designing multi-cluster Kubernetes architectures. This guide covers the material that appears most frequently across senior engineering and DevOps interviews.

## Docker Fundamentals

**Image layers.** Docker images are built from a series of read-only layers stored as filesystem diffs. Each instruction in a Dockerfile creates a new layer. The Union filesystem (OverlayFS) presents these as a single coherent filesystem at runtime. A writable layer is added when a container starts.

Why this matters in interviews: layer caching. Interviewers ask about build performance. The answer is to order Dockerfile instructions from least frequently changed (OS base, system dependencies) to most frequently changed (application code). Changing an early layer invalidates all subsequent cached layers.

**Multi-stage builds.** A build-stage image compiles your application. A runtime-stage image copies only the compiled artifact. This keeps production images small and removes build toolchain from the runtime attack surface.

**Networking.** Docker provides several network modes: bridge (default, isolated network with NAT), host (container shares host network namespace), and overlay (multi-host networking for swarm). For interviews, understand that `bridge` is the default and containers on the same bridge can communicate via IP, while host names require explicit DNS or container linking.

**Volumes.** Named volumes persist beyond container lifecycle and are managed by Docker. Bind mounts map host filesystem paths into the container — useful for development, problematic in production due to host coupling.

**Interview Q&A:**

Q: "Why does running as root in a container matter if the container is isolated?"

A: Container isolation is not complete isolation. A root process inside a container is root on the host if it escapes the namespace through a kernel vulnerability. Running containers as non-root users limits blast radius. `USER` in Dockerfile, `securityContext.runAsNonRoot` in Kubernetes.

## Kubernetes Architecture

**Control plane components:**
- **kube-apiserver:** The only component that talks to etcd. All state reads and writes go through it.
- **etcd:** Distributed key-value store. Holds all cluster state. Back it up.
- **kube-scheduler:** Watches for unscheduled pods and assigns them to nodes based on resource requests, affinity rules, taints and tolerations.
- **kube-controller-manager:** Runs controllers (deployment controller, replicaset controller, etc.) that reconcile desired state to actual state.

**Node components:**
- **kubelet:** Runs on every node. Receives pod specs from the API server and ensures containers are running.
- **kube-proxy:** Manages iptables (or IPVS) rules for Service networking.
- **Container runtime:** containerd or CRI-O — the component that actually runs containers.

## Pod, Deployment, and Service Patterns

**Pod.** Smallest schedulable unit. One or more containers that share a network namespace and storage volumes. Pods are ephemeral — design for them to be killed and replaced.

**Deployment.** Manages a ReplicaSet to maintain desired pod count. Handles rolling updates — by default, it ensures at least 75% of desired pods are available and no more than 125% are running during an update.

**Service.** Stable network endpoint for a set of pods, selected by label. Types:
- `ClusterIP`: Internal only.
- `NodePort`: Exposes on every node's IP at a static port.
- `LoadBalancer`: Provisions a cloud load balancer.

**Ingress.** Manages external HTTP/S access. Routes requests to Services based on host and path rules. Requires an ingress controller (NGINX, Traefik, ALB controller).

## Resource Management

Every production pod should have resource requests and limits.

**Requests** determine scheduling. The scheduler places a pod on a node that has enough unallocated resources to satisfy the request.

**Limits** enforce runtime constraints. A container that exceeds its memory limit is OOMKilled. A container that exceeds its CPU limit is throttled.

A common mistake is setting limits without requests (requests default to limits, which can over-pack nodes) or setting limits far above requests (allows noisy neighbors).

**QoS classes.** Kubernetes assigns pods to QoS classes based on request/limit configuration:
- **Guaranteed:** Requests equal limits for all containers. First in line during resource pressure.
- **Burstable:** Requests below limits. Evictable under pressure.
- **BestEffort:** No requests or limits set. Evicted first.

## Horizontal Pod Autoscaler

HPA scales replica count based on metrics. Default metric is CPU utilization. Custom metrics (from Prometheus via an adapter) enable scaling on queue depth, request rate, or business metrics.

HPA works in a control loop: every 15 seconds by default, it fetches the current metric, computes the desired replica count, and updates the Deployment if the count has changed.

**Interview Q&A:**

Q: "An HPA is configured but pods are not scaling. What do you check?"

A: Verify the metrics server is running and returning data. Check that resource requests are set (HPA can't calculate CPU percentage without a request baseline). Check HPA events with `kubectl describe hpa`. Look for `FailedGetScale` or missing metrics conditions.

## Common Production Scenarios

**Pod stuck in Pending.** Either insufficient resources on any node (check `kubectl describe pod` for the scheduler message), or a node selector/affinity/taint that no node satisfies.

**CrashLoopBackOff.** Container starts and immediately exits. Check logs with `kubectl logs --previous`. Common causes: missing environment variables, misconfigured secrets, application startup error.

**ImagePullBackOff.** Kubelet can't pull the image. Check image name and tag (typo is common), registry credentials (imagePullSecrets), and network connectivity from the node to the registry.

## Scheduling Controls

- **Node selector / Node affinity:** Control which nodes pods can schedule onto.
- **Taints and tolerations:** Nodes repel pods unless the pod has a matching toleration. Used for dedicated node pools (GPU nodes, spot instances).
- **Pod affinity/anti-affinity:** Spread pods across zones for availability, or co-locate pods for latency.

The interview test for scheduling knowledge is usually a scenario: "You have a service that needs to spread across three AZs but your pods are all landing in one. How do you fix it?" Answer: `topologySpreadConstraints` with `topologyKey: topology.kubernetes.io/zone` and `maxSkew: 1`.
