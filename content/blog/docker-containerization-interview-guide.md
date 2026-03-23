---
title: "Docker and Containerization Interview Guide"
description: "Technical interview preparation for containerization: Docker internals (namespaces, cgroups), multi-stage builds, image optimization, Docker Compose, container security, and what platform and DevOps roles expect from container expertise."
date: "2026-03-19"
category: "Technical Skills Guides"
---

Most engineers know how to run `docker build` and `docker run`. Platform and DevOps interviews test whether you understand what actually happens underneath. This guide covers the internals that separate a Docker user from a Docker practitioner.

## What a Container Actually Is

A container is not a lightweight VM. It is a process — or a group of processes — with Linux kernel features applied to restrict what that process can see and do.

The two primary mechanisms are **namespaces** and **cgroups**.

**Namespaces** create isolated views of system resources for the container process:

- `pid` — the container gets its own process ID space. PID 1 inside the container is just some regular PID from the host's perspective.
- `net` — the container gets its own network interfaces, routing tables, and ports. The `eth0` you see inside a container is a virtual interface bridged to the host.
- `mnt` — the container sees its own filesystem mount tree. This is what makes the container filesystem appear separate from the host.
- `uts` — allows the container to have its own hostname and domain name.
- `ipc` — isolated inter-process communication (message queues, shared memory).
- `user` — maps container UIDs to host UIDs, enabling rootless containers.

**cgroups** (control groups) impose resource limits — how much CPU, memory, and I/O a container can consume. When you pass `--memory 512m` to `docker run`, that constraint is enforced at the kernel level through cgroups.

The practical point for interviews: containers share the host kernel. If the host runs Linux kernel 6.x, all containers on that host run on the same kernel. This means faster startup (no OS boot) and lower overhead, but also weaker isolation than a VM where each guest has its own kernel.

## Docker Image Internals: Layers and Caching

A Docker image is a stack of read-only layers. Each `RUN`, `COPY`, and `ADD` instruction in a Dockerfile creates a new layer. The container runtime (using `overlay2` by default on modern Linux) stacks these layers and presents a unified filesystem view via a union filesystem.

**Layer caching** is what makes repeated builds fast. Docker compares each instruction against the cached layer. If nothing has changed, it reuses the cache. The cache is invalidated at the first changed layer and everything after it is rebuilt.

This has a direct implication for Dockerfile ordering:

```dockerfile
# Bad: copies source before installing dependencies
COPY . /app
RUN pip install -r requirements.txt

# Good: install dependencies first (rarely changes), copy source last (changes every commit)
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app
```

With the second pattern, `pip install` is cached as long as `requirements.txt` does not change. The source copy only invalidates its own layer and those below it.

## Multi-Stage Builds

Multi-stage builds solve the problem of build tools ending up in production images. The pattern: use one stage for compiling, copy only the output to a minimal final stage.

```dockerfile
# Stage 1: build
FROM golang:1.22 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o server .

# Stage 2: runtime
FROM scratch
COPY --from=builder /app/server /server
ENTRYPOINT ["/server"]
```

The builder stage has the full Go toolchain — over 1 GB. The final image contains only the statically compiled binary. Resulting image: 8–15 MB. This is not a marginal improvement. It reduces attack surface, cuts registry storage, and speeds up pull times in CI and Kubernetes.

The same pattern applies to Node.js (build assets in a full Node image, serve from nginx), Java (compile in JDK, run in JRE), and Rust (build in the Rust image, run from distroless).

## Dockerfile Best Practices

**Use pinned base image versions.** `FROM ubuntu:latest` will silently pull a different image after every upstream release. Use `FROM ubuntu:24.04` or pin by digest: `FROM ubuntu@sha256:abc123...`.

**Use .dockerignore.** Without it, `COPY . .` sends your `node_modules`, `.git`, and local build artifacts to the daemon. This bloats the build context and slows every build.

**Run as non-root.** By default, container processes run as root inside the container. Even with namespace isolation, this is unnecessary risk. Add a user:

```dockerfile
RUN adduser --disabled-password --no-create-home appuser
USER appuser
```

**ENTRYPOINT vs CMD.** `ENTRYPOINT` is the executable that always runs. `CMD` provides default arguments that can be overridden at `docker run` time. Use `ENTRYPOINT ["./server"]` and `CMD ["--port", "8080"]` so operators can override the port without replacing the binary. Avoid shell form (`ENTRYPOINT ./server`) — it wraps the process in a shell, which means signals like SIGTERM go to the shell, not your application.

**Add HEALTHCHECK.** Orchestrators use it to determine container readiness:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8080/health || exit 1
```

## Image Security

**Scan before pushing.** Tools like Trivy and Snyk integrate into CI pipelines and report CVEs by severity. A common gate: fail the build on any critical CVE.

**Minimal base images reduce attack surface.** In decreasing size and surface area: full distribution → slim variants → alpine → distroless → scratch. Distroless images (from Google) contain only the runtime and its dependencies — no shell, no package manager, no utilities. This makes exploitation harder and image scanning cleaner.

**Never bake secrets into image layers.** Even if you delete a file in a later layer, it is still present in the earlier layer and readable via `docker history` or by inspecting the layer tarball. Pass secrets at runtime via environment variables or mounted files. If you must use build args (`ARG`), be aware they are visible in `docker history` — do not use them for credentials.

**Read-only root filesystem.** Adding `--read-only` to `docker run` (or `readOnlyRootFilesystem: true` in Kubernetes) prevents container processes from writing to the filesystem. Applications that need to write should use explicit volume mounts.

## Docker Networking Modes

- **bridge** (default): Docker creates a virtual bridge (`docker0`) on the host. Containers on the same bridge can communicate. Traffic to the outside goes through NAT.
- **host**: The container shares the host's network namespace directly. No isolation, but no NAT overhead. Useful for performance-sensitive workloads.
- **overlay**: Multi-host networking used by Docker Swarm and Kubernetes. Creates a virtual network that spans multiple hosts using VXLAN encapsulation.
- **macvlan**: Assigns the container its own MAC address. The container appears as a physical device on the network. Used when a container needs to be directly addressable on the LAN without NAT.

## Docker Compose for Development

Compose defines multi-container environments declaratively. The two things interviewers probe most:

**Service dependency ordering.** `depends_on` alone does not wait for a service to be ready — it only waits for the container to start. To wait for readiness, combine it with a healthcheck:

```yaml
depends_on:
  db:
    condition: service_healthy
```

**Volume mounts for hot reload.** Mounting source code into a container at development time means changes on the host reflect immediately inside the container without rebuilding the image. This is standard for development workflows but should never be used in production — it bypasses the reproducibility guarantees the image provides.

## Containers vs VMs

| | Containers | VMs |
|---|---|---|
| Kernel | Shared with host | Own kernel per VM |
| Startup | Milliseconds | Seconds to minutes |
| Isolation | Namespace-based | Hardware-level |
| Overhead | Low | Higher |

For workloads requiring stronger isolation than standard containers — multi-tenant environments, untrusted code execution — look at **gVisor** (user-space kernel interception) and **Kata Containers** (lightweight VMs with container interface). Both provide the container API with VM-level isolation.

## Common Interview Questions

**"How would you debug a container that starts but immediately exits?"**

Start with `docker logs <container>` to see what the process printed before dying. If no useful logs, run the image with a shell override: `docker run -it --entrypoint /bin/sh <image>`. If the image has no shell (distroless), use an ephemeral debug container: `docker debug <container>` or in Kubernetes, `kubectl debug -it <pod> --image=busybox`. Check the process exit code with `docker inspect <container> --format='{{.State.ExitCode}}'`.

**"Design a multi-stage Dockerfile for a Go application."**

Walk through the pattern above: golang builder stage with static binary output, final stage from scratch. Mention build cache optimization (download modules before copying full source). Mention CGO_ENABLED=0 for static linking.

**"What are the security implications of running containers as root?"**

Root inside the container maps to root on the host by default (unless user namespaces are enabled). A container escape vulnerability means full host compromise. Add a non-root user in the Dockerfile. For Kubernetes, set `runAsNonRoot: true` and `allowPrivilegeEscalation: false` in the security context. For anything handling sensitive workloads, also consider `seccomp` profiles to restrict system calls.

## How to Prepare

Theory alone will not hold up in a production-depth interview. Build a real multi-stage Dockerfile for a Go or Rust project and measure image size before and after. Run Trivy against a public image and understand what the CVE output means. Practice debugging a container that exits — stop the entrypoint and step through manually. Understand what happens when you run a distroless container without a shell and there is a runtime error you need to diagnose. The engineers who stand out in these interviews are the ones who have actually gotten stuck on these problems and worked through them.
