---
title: "Docker and Containers: Engineering Deep Dive for Technical Interviews"
date: 2026-03-19
tags: [docker, containers, system-design, devops, interviews]
excerpt: "Containers dominate modern infrastructure interviews. Here's what interviewers actually ask—from Linux primitives to multi-stage builds to production system design."
---

## Why Containers Appear Constantly in Engineering Interviews

Containers show up at every level—from L4 backend roles to principal SRE positions. The range of questions reflects the range of knowledge expected: "What is a container?" for junior candidates, up to "Design a multi-tenant container orchestration layer" for staff engineers. This post covers the full spectrum with the depth interviewers expect.

---

## Linux Primitives: The Foundation Questions

Interviewers at companies like Google, Meta, and Stripe frequently open with this: **"What actually is a container? How does it differ from a VM?"**

The answer they want touches Linux kernel features directly.

**Namespaces** provide process isolation. Docker uses six namespace types:

- `pid` — process ID isolation; container processes see their own PID 1
- `net` — isolated network stack (interfaces, routing tables, iptables rules)
- `mnt` — filesystem mount points; containers get their own root filesystem
- `uts` — hostname and domain name isolation
- `ipc` — inter-process communication isolation (shared memory, semaphores)
- `user` — UID/GID mapping; container root can map to unprivileged host UID

**cgroups (control groups)** enforce resource limits. When you set `--memory=512m` or `--cpus=1.5`, the kernel's cgroup subsystem enforces those limits. The container runtime writes to `/sys/fs/cgroup/` to configure limits before exec-ing the container process.

The follow-up: **"What's the difference between cgroups v1 and v2?"** In v1, each resource controller (cpu, memory, blkio) has its own hierarchy. In v2, there's a unified hierarchy with a single tree. Systemd and modern container runtimes default to v2, which simplifies accounting and eliminates inconsistencies in multi-controller scenarios.

**Union filesystems** underlie Docker's layer model. OverlayFS (the default on modern Linux) presents a merged view of a lower read-only layer stack and an upper writable layer. When a container reads a file, it traverses layers bottom-up. When it writes, copy-on-write (CoW) triggers: the file is copied from the lower layer to the upper layer, then modified. This is why deleting a large file in a `RUN` command doesn't shrink the image—the deletion exists as a "whiteout" file in a new layer, while the original file remains in lower layers.

---

## Dockerfile Interview Scenarios

**"Review this Dockerfile and tell me what's wrong with it."**

```dockerfile
FROM ubuntu:latest
RUN apt-get update
RUN apt-get install -y python3 pip
COPY . /app
RUN pip install -r /app/requirements.txt
RUN apt-get clean
CMD ["python3", "/app/app.py"]
```

Problems to call out:

1. `ubuntu:latest` is non-deterministic—pin to `ubuntu:22.04` or use a purpose-built base like `python:3.12-slim`
2. Separate `apt-get update` and `apt-get install` layers can produce stale caches; combine them in a single `RUN`
3. `apt-get clean` in a separate layer doesn't shrink the image—apt cache was committed in the install layer. Must clean in the same `RUN` command
4. `COPY . /app` before dependency installation means any source change invalidates the pip install cache; copy `requirements.txt` first, then run install, then copy source
5. No `--no-install-recommends` flag on apt-get; installs unnecessary packages

**Multi-stage builds** eliminate build tooling from production images:

```dockerfile
FROM golang:1.22 AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /app/server ./cmd/server

FROM gcr.io/distroless/static-debian12
COPY --from=builder /app/server /server
ENTRYPOINT ["/server"]
```

The final image contains only the static binary and distroless base (~5MB total vs. ~900MB with the Go toolchain). Interviewers ask you to walk through why this matters for security (reduced attack surface—no shell, no package manager) and performance (smaller pull times, faster cold starts in serverless/lambda scenarios).

---

## Container Security Questions

**"A container runs as root by default. What are the implications?"**

Container root maps to host UID 0 unless user namespaces remap it. If a process escapes the container (via a kernel exploit or misconfigured mount), it has root on the host. Defense layers:

- `USER` directive in Dockerfile to drop privileges before the entrypoint
- `--read-only` filesystem with explicit tmpfs mounts for writeable paths
- `--cap-drop=ALL --cap-add=NET_BIND_SERVICE` to restrict Linux capabilities
- `seccomp` profiles to filter syscalls (Docker's default profile blocks ~44 syscalls)
- `AppArmor` or `SELinux` profiles for MAC enforcement

**"What is a privileged container and when is it dangerous?"**

`--privileged` disables all security isolation: all capabilities are granted, seccomp/AppArmor profiles are dropped, and devices are exposed. Privileged containers are equivalent to root on the host. Legitimate use cases are narrow: running Docker-in-Docker in CI, or device driver testing. Never in production application workloads.

**Image scanning** is a common process question: interviewers want to hear about Trivy, Grype, or Snyk integrated into CI pipelines, with policy gates that block promotion of images with critical CVEs.

---

## System Design: Containers in Architecture Interviews

**"Design a container-based deployment platform for 500 microservices."**

Key dimensions to address:

**Image registry strategy**: A regional registry (ECR, GCR, or self-hosted Harbor) with geo-replication reduces pull latency and eliminates cross-region data transfer costs. Images are tagged by git SHA, not `latest`. Immutable tags prevent overwrite.

**Runtime and scheduling**: Kubernetes is the expected answer for orchestration at scale, but interviewers want you to explain why—declarative desired state, bin-packing via the scheduler, self-healing via controllers, and native support for rolling deployments and canaries.

**Resource isolation between tenants**: At the Kubernetes layer, namespaces plus LimitRanges and ResourceQuotas enforce per-team resource boundaries. NetworkPolicies restrict lateral movement. For stronger isolation (multi-tenant SaaS), consider gVisor or Kata Containers, which add a guest kernel or hypervisor between the container and the host kernel.

**Cold start optimization**: Large images slow pod startup. Strategies: image pre-pulling via DaemonSets, snapshot-based image loading (Stargz/eStargz lazy pulling), and keeping base images minimal.

**"How would you implement zero-downtime deployments with containers?"**

The answer combines orchestrator-level rolling updates with application readiness. Kubernetes rolling deployments replace pods incrementally, but only mark a pod ready when its readiness probe returns healthy. The probe should check actual application readiness (database connection established, cache warmed) not just process liveness. `preStop` hooks + `terminationGracePeriodSeconds` ensure in-flight requests drain before SIGTERM completes.

---

## Networking Deep Dive

Interviewers at infrastructure companies push into container networking internals.

**"How does container-to-container networking work in Docker bridge mode?"**

Docker creates a `docker0` bridge interface. Each container gets a `veth` pair—one end in the container's network namespace, one end attached to the bridge. The bridge routes traffic between containers using ARP. External traffic reaches containers via NAT rules written by Docker into iptables.

In Kubernetes, each node runs a CNI plugin (Calico, Cilium, Flannel) that handles pod-to-pod routing across nodes. Cilium uses eBPF to bypass iptables entirely for higher throughput and lower latency—a detail that signals strong infrastructure depth.

---

## Quick-Fire Concepts for Final Rounds

- **Difference between `ENTRYPOINT` and `CMD`**: ENTRYPOINT is the fixed executable; CMD provides default arguments. When both are present, CMD arguments are passed to ENTRYPOINT. Using `exec` form (JSON array) avoids shell wrapper processes and ensures signals are delivered directly to the application.
- **Layer caching invalidation**: Any change to a layer invalidates all subsequent layers. Order Dockerfile instructions from least-changed to most-changed.
- **`docker build --cache-from`**: Pulls a remote image to use as a cache source in CI, where local layer cache is absent.
- **OCI specification**: The Open Container Initiative defines the image format and runtime spec. containerd and crun are OCI-compliant runtimes; Docker itself is a higher-level tool that delegates to containerd.
- **Ephemeral containers**: Kubernetes 1.23+ supports injecting a debug container into a running pod without restarting it—useful for live debugging distroless images that lack a shell.

---

## Preparation Checklist

Before a systems or DevOps-heavy interview: be able to explain namespaces and cgroups from first principles, walk through a Dockerfile review identifying layer optimization issues, describe multi-stage build strategy and tradeoffs, articulate container security posture (capabilities, seccomp, user namespaces), and design a container deployment architecture covering registry, orchestration, networking, and zero-downtime rollout. These topics appear in roughly 70% of senior backend and infrastructure interviews at companies running containerized infrastructure.
