---
title: "Go Microservices: Production Patterns for 2026"
description: "Battle-tested patterns for Go microservices in production—service structure, gRPC vs REST, graceful shutdown, circuit breakers, observability, and the idioms that make Go services reliable at scale."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Go Microservices: Production Patterns for 2026

Go has become the default language for microservices at companies like Google, Uber, Cloudflare, and Dropbox. Its combination of fast compilation, low memory footprint, excellent concurrency primitives, and readable code make it ideal for network services. This guide covers the production patterns that distinguish Go microservices that work well at scale from those that don't.

## Project Structure

A scalable Go service structure:

```
myservice/
├── cmd/
│   └── server/
│       └── main.go          # Entry point
├── internal/
│   ├── handler/             # HTTP/gRPC handlers
│   ├── service/             # Business logic
│   ├── repository/          # Database access
│   └── middleware/          # Auth, logging, etc.
├── pkg/                     # Shared, importable packages
├── api/
│   └── proto/               # Protobuf definitions
├── configs/                 # Configuration files
└── go.mod
```

The `internal/` directory is not importable by other modules — use it for service-specific code. `pkg/` is for code you want to share across services.

## Service Initialization with Dependency Injection

Use constructor injection, not global state:

```go
type Server struct {
    userService  *service.UserService
    authService  *service.AuthService
    logger       *zap.Logger
    db           *sql.DB
}

func NewServer(cfg Config) (*Server, error) {
    db, err := sql.Open("postgres", cfg.DatabaseURL)
    if err != nil {
        return nil, fmt.Errorf("opening db: %w", err)
    }

    logger, _ := zap.NewProduction()
    userRepo := repository.NewUserRepository(db)
    userService := service.NewUserService(userRepo, logger)

    return &Server{
        userService: userService,
        logger:      logger,
        db:          db,
    }, nil
}
```

## Graceful Shutdown

Always implement graceful shutdown. In-flight requests must complete:

```go
func main() {
    srv := &http.Server{Addr: ":8080", Handler: router}

    // Start server in goroutine
    go func() {
        if err := srv.ListenAndServe(); err != http.ErrServerClosed {
            log.Fatalf("server error: %v", err)
        }
    }()

    // Wait for shutdown signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, os.Interrupt, syscall.SIGTERM)
    <-quit

    // Give in-flight requests 30 seconds to complete
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := srv.Shutdown(ctx); err != nil {
        log.Printf("server shutdown error: %v", err)
    }

    // Close database connections
    db.Close()
    log.Println("server stopped")
}
```

## Context Propagation

Always pass context as the first parameter. It carries deadlines, cancellation, and request-scoped values:

```go
func (s *UserService) GetUser(ctx context.Context, userID int64) (*User, error) {
    // Context cancellation will abort the DB query
    row := s.db.QueryRowContext(ctx,
        "SELECT id, name, email FROM users WHERE id = $1", userID)
    // ...
}
```

Set timeouts at the entry point (HTTP handler or gRPC handler), not deep in the stack:

```go
func (h *Handler) GetUser(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
    defer cancel()

    user, err := h.userService.GetUser(ctx, userID)
    // ...
}
```

## Error Handling Patterns

Wrap errors with context using `fmt.Errorf` with `%w`:

```go
func (r *UserRepository) GetByEmail(ctx context.Context, email string) (*User, error) {
    var user User
    err := r.db.QueryRowContext(ctx,
        "SELECT id, name, email FROM users WHERE email = $1", email,
    ).Scan(&user.ID, &user.Name, &user.Email)

    if errors.Is(err, sql.ErrNoRows) {
        return nil, ErrUserNotFound  // sentinel error
    }
    if err != nil {
        return nil, fmt.Errorf("querying user by email: %w", err)  // wrapped with context
    }
    return &user, nil
}
```

## Circuit Breaker Pattern

Prevent cascading failures when a dependency goes down:

```go
import "github.com/sony/gobreaker"

var cb *gobreaker.CircuitBreaker

func init() {
    cb = gobreaker.NewCircuitBreaker(gobreaker.Settings{
        Name:        "payment-service",
        MaxRequests: 1,               // requests allowed in half-open state
        Interval:    10 * time.Second, // reset failure count window
        Timeout:     30 * time.Second, // open state duration before retry
        ReadyToTrip: func(counts gobreaker.Counts) bool {
            return counts.ConsecutiveFailures > 5
        },
    })
}

func callPaymentService(req PaymentRequest) (*PaymentResponse, error) {
    result, err := cb.Execute(func() (interface{}, error) {
        return paymentClient.Process(req)
    })
    if err != nil {
        return nil, fmt.Errorf("payment service: %w", err)
    }
    return result.(*PaymentResponse), nil
}
```

## Structured Logging with Zap

Use structured logging, not fmt.Println:

```go
logger.Info("user created",
    zap.String("user_id", userID),
    zap.String("email", email),
    zap.Duration("duration", time.Since(start)),
)

logger.Error("database query failed",
    zap.Error(err),
    zap.String("query", "SELECT users"),
    zap.Int64("user_id", userID),
)
```

Structured logs are queryable in Datadog/Elasticsearch. `fmt.Println` logs are not.

## gRPC vs REST: When to Use Each

Use **gRPC** for:
- Service-to-service communication
- When streaming is needed (server-side, client-side, bidirectional)
- When you want strong typing and code generation
- High-throughput, low-latency internal APIs

Use **REST** for:
- Public APIs (consumers may not support gRPC)
- Web clients (browser support for gRPC is limited without gRPC-Web)
- When human readability of the protocol matters

Many services expose both: gRPC for internal services, REST (often via grpc-gateway) for external consumers.

## Observability: The Triad

Every production Go service needs:

```go
// 1. Metrics (Prometheus)
requestDuration := prometheus.NewHistogramVec(
    prometheus.HistogramOpts{
        Name:    "http_request_duration_seconds",
        Buckets: prometheus.DefBuckets,
    },
    []string{"method", "path", "status"},
)

// 2. Tracing (OpenTelemetry)
tracer := otel.Tracer("my-service")
ctx, span := tracer.Start(ctx, "GetUser")
defer span.End()

// 3. Logging (Zap with trace correlation)
logger.Info("request", zap.String("trace_id", span.SpanContext().TraceID().String()))
```

## Interview Tips for Go Microservices

Key patterns to demonstrate:
1. Graceful shutdown — interviewers ask about it frequently
2. Context propagation for timeouts and cancellation
3. Error wrapping with `%w` for stack traces
4. Circuit breaker for dependency resilience
5. Structured logging with correlation IDs

The most impressive Go knowledge to show: you understand the concurrency model (goroutines + channels) and can design systems that use it correctly, not just write sequential code with goroutines sprinkled in.
