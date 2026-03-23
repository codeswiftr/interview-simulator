---
title: "Cloud-Native Microservices Patterns for Senior Engineers"
description: "Production-grade microservices patterns for senior engineering interviews — service mesh, sidecar proxy, API gateway patterns, service discovery, health checks, and the patterns that separate junior from senior cloud engineers."
date: "2026-03-20"
category: "System Design"
---

# Cloud-Native Microservices Patterns for Senior Engineers

Cloud-native microservices interviews test whether you understand the operational complexity of distributed systems, not just the happy path. Senior candidates are expected to discuss service mesh, observability, failure isolation, and the patterns that prevent cascading failures. This guide covers the production patterns that distinguish senior from mid-level engineers.

## Service Mesh: What It Is and When It Matters

A service mesh is an infrastructure layer that handles service-to-service communication. Instead of implementing retry logic, circuit breaking, mTLS, and observability in each service, a sidecar proxy (Envoy in Istio/Linkerd) handles it transparently.

**Without service mesh:** Each service implements its own retry policies, timeout handling, and metrics. When a team adds a new service, they must implement all of these correctly. Policies are inconsistent across services.

**With service mesh:** A control plane (Istiod in Istio) pushes configuration to sidecar proxies. The service only makes HTTP calls; the sidecar handles retries, circuit breaking, mTLS, and emits traces/metrics automatically.

**Interview question:** "When would you add a service mesh to your architecture?"

The honest answer: service meshes add significant operational complexity. The break-even point is roughly 8-10+ services where the cross-cutting concern management (security, observability, traffic management) would otherwise require duplicated effort across services. For smaller deployments, a well-configured API gateway plus shared libraries is simpler.

## API Gateway Patterns

The API gateway is the entry point for external traffic. Three patterns:

**Simple reverse proxy:** Routes requests to backend services, handles TLS termination and load balancing. Kong, nginx, Traefik. Low complexity; no business logic.

**Backend for Frontend (BFF):** Separate gateways optimized for different client types (mobile API vs. web API vs. partner API). Allows each BFF to aggregate and transform data for its specific client without bloating a single gateway.

**GraphQL gateway:** Aggregates data from multiple services into a unified graph. Clients request exactly the fields they need; the gateway orchestrates calls to underlying REST/gRPC services. Netflix's DGS framework and Apollo Federation implement this pattern.

## Service Discovery

Services need to find each other. Two approaches:

**Client-side discovery:** Service A queries a service registry (Consul, Eureka) to get instances of Service B, then load balances itself. More control, but service must implement discovery logic.

**Server-side discovery:** Service A calls a load balancer (ELB, Kubernetes Service), which queries the registry and routes the request. Service A knows only the load balancer address. Simpler for services, but load balancer is a bottleneck.

In Kubernetes, server-side discovery is the default: Services provide a stable DNS name and ClusterIP; kube-proxy handles routing to pods. etcd is the registry. External services use Ingress controllers or Service type LoadBalancer.

## Health Checks: Liveness vs. Readiness vs. Startup

Kubernetes has three health check types that senior engineers must distinguish:

**Liveness:** Is the container alive? If liveness fails, Kubernetes restarts the container. Use for deadlock detection — a container that's stuck in an infinite loop is alive but useless.

**Readiness:** Is the container ready to serve traffic? If readiness fails, the pod is removed from the Service's endpoint list (no new requests). Use for: startup warmup, dependency unavailability (database is down).

**Startup:** Used for containers that take a long time to start. Disables liveness/readiness until startup probe succeeds, preventing premature restarts.

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

**Common mistake:** Using a deep health check (that verifies database connectivity) for the liveness probe. If the database is temporarily down, all pods restart simultaneously — cascading failure. Deep checks belong in readiness probes.

## Graceful Shutdown

When a pod is terminated, Kubernetes sends SIGTERM, waits `terminationGracePeriodSeconds` (default 30s), then sends SIGKILL. Proper graceful shutdown:

1. Stop accepting new connections (remove from load balancer — Kubernetes does this by removing from Service endpoints, but there's propagation delay)
2. Complete in-flight requests
3. Close database connections and release resources
4. Exit

```python
import signal, asyncio

shutdown_event = asyncio.Event()

def handle_sigterm(*args):
    shutdown_event.set()

signal.signal(signal.SIGTERM, handle_sigterm)

# In your server:
await shutdown_event.wait()
# Then: stop accepting, drain, close
```

The propagation delay between SIGTERM and load balancer deregistration is why a short sleep (2-5 seconds) before stopping request acceptance is a common production pattern.

## Sidecar Pattern

The sidecar runs alongside the main application container in the same pod, sharing network namespace and (optionally) storage. Use cases:

- **Proxy sidecar:** Envoy for service mesh, logging aggregation (Fluentd)
- **Agent sidecar:** Datadog agent, Vault agent for secret injection
- **Adapter sidecar:** Transform legacy protocols into standard ones

The key property: the sidecar and main container share the pod lifecycle. They start and stop together. The main application container doesn't know or care about the sidecar.

## Bulkhead Pattern

Isolate failures to prevent cascading. Name comes from ship compartments — a breach in one doesn't sink the whole ship.

In microservices: separate thread pools (or connection pools) for calls to different downstream services. If Service B becomes slow, its thread pool fills, but Service C's pool is unaffected.

```python
# Separate executors per downstream service
executor_b = ThreadPoolExecutor(max_workers=10)
executor_c = ThreadPoolExecutor(max_workers=10)

# Calls to B and C use their own pools — B being slow doesn't affect C
```

Combined with circuit breakers: when Service B's circuit opens, its thread pool stops blocking. When it half-opens, only a few threads probe.

## Choreography vs. Orchestration (Again, in Microservices Context)

This deserves emphasis: the choice between choreography (event-driven, decentralized) and orchestration (central coordinator) is one of the most asked microservices architecture questions.

**Choreography:** Services publish events; other services subscribe and react. No central controller. More resilient (no single point of failure), harder to debug (distributed transaction state is implicit).

**Orchestration:** A coordinator (workflow engine or service) calls other services in sequence. Explicit flow, easier to monitor. Coordinator is a bottleneck/single point of failure.

Production answer: use choreography for business events (order placed → various services react), orchestration for complex workflows with compensation logic (saga orchestrator for multi-step transactions).
