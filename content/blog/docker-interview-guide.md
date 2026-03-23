---
title: "Docker Interview Guide: Images, Containers, Networking, and Production Docker Patterns"
description: "Prepare for Docker questions in DevOps and backend engineering interviews — from image layering and Dockerfile best practices to container networking, volumes, and production-grade patterns."
date: "2026-03-20"
category: "DevOps & Infrastructure"
---

Docker knowledge is now table stakes for backend, platform, and DevOps engineering roles. Interview questions range from conceptual ("explain image layers") to practical ("how would you reduce this image size?") to operational ("how do you handle secrets in containers?"). This guide covers the full spectrum.

## Images and Layers

Docker images are composed of read-only layers. Each instruction in a Dockerfile creates a new layer. Layers are cached and shared across images, which is why layer order matters for build performance.

**The caching rule:** Docker invalidates the cache for a layer and all subsequent layers when the layer's instruction or its inputs change. This has a critical practical consequence: copy dependency manifests and install dependencies *before* copying application source code.

```dockerfile
# Correct: dependency layer cached separately from source
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
CMD ["node", "server.js"]
```

If you copy all source files first and then run `npm install`, every source file change invalidates the install layer and re-runs the full install. This is the most common Dockerfile inefficiency in interview code reviews.

**Multi-stage builds** reduce final image size by separating build tooling from the runtime image:

```dockerfile
FROM golang:1.22 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o server .

FROM gcr.io/distroless/static
COPY --from=builder /app/server /server
ENTRYPOINT ["/server"]
```

The final image contains only the compiled binary and minimal runtime dependencies — no Go toolchain. This pattern reduces attack surface and image size simultaneously.

## Containers vs. Images

An image is a blueprint; a container is a running instance of that blueprint. Containers add a thin read-write layer on top of the image layers. Stopping a container doesn't delete its writable layer — that's why `docker ps -a` shows stopped containers consuming space. `docker rm` removes the writable layer; `docker rmi` removes the image.

**Key questions interviewers ask:**
- What happens to data in a container when it stops? (It persists in the writable layer until the container is removed)
- How is a container different from a VM? (Containers share the host kernel; VMs have a full OS; containers are processes with namespacing and cgroup limits)
- What is the PID 1 problem in containers? (Zombie processes aren't reaped if PID 1 doesn't handle SIGCHLD; use `tini` or `dumb-init` as an init wrapper)

## Networking

Docker creates several network drivers by default:

- **bridge** (default): containers get a private IP on a software bridge network, can communicate by IP, isolated from the host
- **host**: container shares the host's network stack — no NAT overhead, but no isolation
- **none**: no networking
- **overlay**: multi-host networking for Docker Swarm / Kubernetes setups

For most development setups, Docker Compose creates a bridge network per project. Services discover each other by service name (Docker's embedded DNS resolves `service-name` to the container IP).

**Port mapping:** `-p 8080:80` maps host port 8080 to container port 80. In production, avoid publishing ports directly to 0.0.0.0 unless you intend them to be publicly accessible — use `127.0.0.1:8080:80` to bind to localhost only and let a reverse proxy handle external traffic.

## Volumes and Data Persistence

Three options for persistent data:

| Type | Use case | Notes |
|------|----------|-------|
| Named volume | Database data, application state | Managed by Docker, survives `docker rm` |
| Bind mount | Development (sync source code) | Maps host path to container path |
| tmpfs mount | Sensitive data that shouldn't persist | In-memory only, lost on container stop |

Named volumes are the right choice for production data. Never store production database files in a container's writable layer — you lose them when the container is recreated.

## Secrets and Configuration

**Never bake secrets into images.** Even if you use `RUN rm secret.txt` after using it, the secret exists in the layer history and is recoverable with `docker history`.

Production patterns for secrets:
1. **Environment variables at runtime:** `docker run -e DB_PASSWORD=$DB_PASSWORD` — the secret never enters the image, but is visible in process listings
2. **Docker secrets (Swarm):** mounted as files in `/run/secrets/` — better than env vars
3. **Secret management systems:** Vault, AWS Secrets Manager, or similar — inject at startup, not build time
4. **BuildKit secrets:** `RUN --mount=type=secret,id=token cat /run/secrets/token` — available during build but not stored in layers

## Health Checks

Production containers should define health checks:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
```

Orchestrators (Kubernetes, ECS, Swarm) use health check status to decide whether to route traffic to a container and whether to restart it. A container that starts but has a failing health check will be taken out of rotation.

## Resource Limits

Always set memory and CPU limits in production:

```bash
docker run --memory="512m" --cpus="0.5" my-app
```

Without limits, a runaway container can exhaust host memory and OOM-kill other containers or the host itself. In Kubernetes, this maps to `resources.requests` and `resources.limits` in pod specs.

## Common Interview Questions and Strong Answers

**"How would you reduce a 1.4 GB image to under 200 MB?"**
Use multi-stage builds to separate build and runtime. Switch from a full OS base (ubuntu, debian) to alpine or distroless. Remove development dependencies in the final stage. Clean up package manager caches in the same RUN instruction that installs packages (adding a separate `RUN apt-get clean` creates a new layer that doesn't actually reduce size).

**"How do containers achieve isolation?"**
Linux namespaces (PID, network, mount, UTS, IPC, user) provide resource isolation. cgroups limit CPU, memory, and I/O consumption. This is why Docker requires Linux — on macOS, Docker Desktop runs a Linux VM.

**"What's the difference between CMD and ENTRYPOINT?"**
`ENTRYPOINT` defines the executable; `CMD` provides default arguments. `CMD` is overridden when you pass arguments to `docker run`. Use `ENTRYPOINT ["executable"]` with `CMD ["default-arg"]` for containers designed to behave like commands. Use `CMD` alone for containers where you want the command to be easily overridable.

## Practice Scenarios

Write and explain Dockerfiles for: a Python FastAPI service, a Node.js application, and a Go binary. For each, demonstrate multi-stage builds and explain your layer ordering choices. These exercises surface the depth interviewers are looking for in senior infrastructure roles.
