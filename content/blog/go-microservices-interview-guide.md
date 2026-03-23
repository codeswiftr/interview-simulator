---
title: "Go Microservices Interview Guide: gRPC, Service Mesh, and Production Patterns"
description: "Senior Go microservices interview preparation — gRPC vs REST trade-offs, service discovery, distributed tracing, circuit breakers, and patterns for building reliable Go services at scale."
date: "2026-03-20"
category: "Backend Engineering"
---

# Go Microservices Interview Guide: gRPC, Service Mesh, and Production Patterns

Go has become the dominant language for building microservices and cloud infrastructure. Go microservices interviews go beyond language features into distributed systems patterns: gRPC, service mesh, observability, and reliability engineering. This guide covers what senior Go engineers face in interviews at cloud-native companies.

## gRPC vs REST: The Core Trade-off

**REST (HTTP/JSON)**: Universal support. Human-readable. Excellent for public APIs and browser-facing services. Schema-less (Swagger/OpenAPI is optional). Flexible but requires discipline to maintain consistent contracts.

**gRPC (HTTP/2 + Protocol Buffers)**: Strongly typed contracts via `.proto` files. Binary serialization (3-10x smaller payloads than JSON). Bidirectional streaming. Code generation for all major languages. Excellent for internal service-to-service communication. Limited browser support (gRPC-Web adds a translation layer).

**Interview answer for "when would you choose gRPC over REST?"**: Choose gRPC for internal service-to-service communication when you have multiple languages, need streaming, or need maximum performance. Stick with REST for external/public APIs, browser-facing services, and when ease of tooling and debugging matters.

```protobuf
syntax = "proto3";

service UserService {
  rpc GetUser (GetUserRequest) returns (User);
  rpc ListUsers (ListUsersRequest) returns (stream User); // server streaming
  rpc UpdateUsers (stream UpdateUserRequest) returns (UpdateSummary); // client streaming
}

message User {
  string id = 1;
  string name = 2;
  string email = 3;
}
```

**Generated Go code** is type-safe and eliminates entire classes of serialization bugs. The `.proto` file is the contract — changes require coordination but are explicit.

## Service Discovery and Communication

In a microservices system, services need to find each other. The two patterns:

**DNS-based discovery**: Kubernetes Services expose a stable DNS name. `user-service.default.svc.cluster.local` resolves to the current pod IPs. Load balancing happens at the DNS level (round-robin) or via Kubernetes Service's kube-proxy (iptables rules). Simple and effective for most cases.

**Client-side discovery**: Services query a service registry (Consul, etcd) directly and handle load balancing themselves. Gives more control (health-aware routing, canary traffic splitting) at the cost of more client-side complexity.

**In Go**: Use standard `http.Client` for REST. Use `google.golang.org/grpc` with a resolver that integrates with your discovery mechanism. The grpc-go library supports DNS resolver by default.

## Resilience Patterns

**Circuit breaker**: After N consecutive failures or a failure rate above a threshold, open the circuit — stop sending requests and fail fast. After a timeout, try a single request (half-open state). If it succeeds, close the circuit. If not, stay open longer.

```go
// Using sony/gobreaker
cb := gobreaker.NewCircuitBreaker(gobreaker.Settings{
    Name:        "UserService",
    MaxRequests: 1,
    Interval:    10 * time.Second,
    Timeout:     60 * time.Second,
    ReadyToTrip: func(counts gobreaker.Counts) bool {
        return counts.ConsecutiveFailures > 5
    },
})

result, err := cb.Execute(func() (interface{}, error) {
    return userClient.GetUser(ctx, req)
})
```

**Retry with exponential backoff**: Transient failures (network blips, temporary overload) often succeed on retry. Exponential backoff with jitter prevents thundering herd: `wait = base * 2^attempt + random_jitter`.

**Timeout propagation**: Every service call should have a timeout. Use context: `ctx, cancel := context.WithTimeout(ctx, 500*time.Millisecond)`. The context propagates down the call chain — if the caller's context cancels, all downstream calls cancel automatically.

**Bulkhead**: Limit resource usage per dependency. Separate goroutine pools for different downstream services. If Service B is slow, its goroutines don't exhaust the pool serving Service A requests.

## Observability: The Three Pillars

**Metrics**: Use Prometheus for instrumenting Go services. `prometheus/client_golang` provides counters, gauges, histograms, and summaries. Standard metrics: request rate, error rate, p50/p95/p99 latency (RED method: Rate, Errors, Duration).

```go
var requestDuration = prometheus.NewHistogramVec(
    prometheus.HistogramOpts{
        Name:    "http_request_duration_seconds",
        Buckets: prometheus.DefBuckets,
    },
    []string{"method", "path", "status"},
)
```

**Distributed tracing**: Use OpenTelemetry (the standard) with Jaeger or Tempo as the backend. Trace propagation: the calling service injects trace context (W3C TraceContext headers) into requests; the receiving service extracts and continues the trace. This links spans across services into a single trace, making request flows visible.

**Structured logging**: Use `log/slog` (Go 1.21+) or `go.uber.org/zap`. Log in JSON format — structured logs are queryable. Include trace ID in every log message to correlate logs with traces.

## Context and Graceful Shutdown

**Context propagation**: Every function that makes I/O calls should accept a `context.Context` as its first parameter. This is Go's convention and the compiler won't enforce it — but neglecting it means you can't cancel downstream calls.

**Graceful shutdown**: When a SIGTERM arrives (Kubernetes sending shutdown signal), you have typically 30 seconds to finish in-flight requests.

```go
server := &http.Server{Addr: ":8080", Handler: mux}

go func() {
    if err := server.ListenAndServe(); err != http.ErrServerClosed {
        log.Fatal(err)
    }
}()

// Wait for interrupt signal
quit := make(chan os.Signal, 1)
signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
<-quit

ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()
if err := server.Shutdown(ctx); err != nil {
    log.Fatal("Server forced shutdown:", err)
}
```

## Service Mesh

A service mesh (Istio, Linkerd) handles cross-cutting concerns at the infrastructure layer rather than application code: mTLS between services, traffic management, circuit breaking, retries, distributed tracing injection.

**Benefits**: Security (mTLS by default, no code changes), observability (automatic span injection), traffic control (canary deployments, A/B testing via traffic weights).

**Costs**: Operational complexity (sidecar proxy management), latency overhead (~1-5ms per hop for the proxy), and debugging difficulty (traffic flows through proxies, which can obscure issues).

**Interview point**: "A service mesh is not free. It's appropriate when you have many services, a dedicated platform team to manage it, and clear security requirements. For 3-5 services owned by one team, the operational overhead isn't worth it."

Go microservices interviews reward engineers who can connect the language patterns (channels, contexts, interfaces) to the distributed systems patterns (circuit breakers, tracing, service discovery) that make services reliable at scale.
