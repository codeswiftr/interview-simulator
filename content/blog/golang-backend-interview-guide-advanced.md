---
title: "Go Backend Advanced Interview: HTTP Servers, Middleware, and Production Patterns"
description: "A deep dive into advanced Go interview topics including net/http internals, middleware chains, context propagation, error handling patterns, graceful shutdown, database pooling with pgx, and testing HTTP handlers."
date: "2026-03-20"
category: "Technical Skills"
---

# Go Backend Advanced Interview: HTTP Servers, Middleware, and Production Patterns

Go backend interviews at companies that run Go in production go well beyond syntax and basic concurrency. Interviewers want to see that you understand how the standard library works, how to structure middleware chains correctly, and how to build HTTP servers that behave correctly under load and during deployments. This guide covers the technical depth that separates senior Go engineers from mid-level candidates.

## net/http Deep Dive: What Actually Happens

The `net/http` package's `ServeMux` and `Server` types are the foundation of Go HTTP servers, and understanding their internals is important for both interviews and production work.

`http.ListenAndServe` creates a TCP listener, accepts connections, and spawns a goroutine per connection that reads HTTP requests and dispatches them to the registered handler. This per-connection goroutine model means Go HTTP servers scale well under concurrent connections without thread pool management—the goroutine scheduler handles multiplexing.

`http.Handler` is an interface with a single method: `ServeHTTP(ResponseWriter, *Request)`. Every piece of the HTTP stack implements this interface, which enables composition. The simplicity of this interface is what makes Go's middleware pattern so clean.

`http.ServeMux` does path-based routing with longest-prefix matching. For production applications, most teams use third-party routers (chi, gorilla/mux, httprouter) that support path parameters and method-based routing. In interviews, know why: `ServeMux` doesn't distinguish HTTP methods, has no path parameter extraction, and the longest-prefix matching can behave unexpectedly with trailing slashes.

## Middleware Chains: The Pattern and the Pitfalls

Go middleware is a function that takes an `http.Handler` and returns an `http.Handler`. The canonical implementation:

```go
func LoggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        next.ServeHTTP(w, r)
        log.Printf("%s %s %v", r.Method, r.URL.Path, time.Since(start))
    })
}
```

Chaining multiple middleware follows a right-to-left wrapping pattern: `LoggingMiddleware(AuthMiddleware(handler))` means requests flow through `LoggingMiddleware` first, then `AuthMiddleware`, then `handler`. When building chains of more than 2-3 middleware, use a helper or a library like alice to maintain readability.

**The pitfall: writing to the response after the handler returns.** `http.ResponseWriter` can only write headers once. If your middleware attempts to set headers after calling `next.ServeHTTP`, those headers will be silently ignored (if the response has already been written) or may panic. To capture the status code in logging middleware, wrap `ResponseWriter` in a struct that intercepts the `WriteHeader` call:

```go
type responseRecorder struct {
    http.ResponseWriter
    statusCode int
}

func (r *responseRecorder) WriteHeader(code int) {
    r.statusCode = code
    r.ResponseWriter.WriteHeader(code)
}
```

This pattern comes up in interviews as a test of whether you understand `ResponseWriter`'s write-once semantics.

## Context Propagation: The Right Pattern

`context.Context` carries request-scoped values, deadlines, and cancellation signals across API boundaries. The Go convention: `ctx` is always the first parameter, and you should always check `ctx.Err()` before expensive operations.

In HTTP handlers, `r.Context()` provides the request context. When the client disconnects, this context is cancelled. Respecting context cancellation in your handler prevents resource leaks:

```go
func handler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    result, err := db.QueryContext(ctx, "SELECT ...")
    if err != nil {
        if ctx.Err() != nil {
            // Client disconnected; don't bother writing a response
            return
        }
        http.Error(w, "database error", http.StatusInternalServerError)
        return
    }
    // ...
}
```

For passing values through context, use unexported key types to prevent collisions:

```go
type contextKey string
const requestIDKey contextKey = "requestID"

func WithRequestID(ctx context.Context, id string) context.Context {
    return context.WithValue(ctx, requestIDKey, id)
}

func RequestIDFromContext(ctx context.Context) (string, bool) {
    id, ok := ctx.Value(requestIDKey).(string)
    return id, ok
}
```

Interview question: "Why use an unexported type for context keys?" Answer: to prevent other packages from accidentally using the same key, which would cause silent collisions when two packages store different values under the same key.

## Error Handling: errors.Is, errors.As, and Wrapping

Go 1.13 introduced error wrapping with `%w` in `fmt.Errorf` and the `errors.Is` / `errors.As` functions. Understanding these is a litmus test for Go experience in interviews.

`errors.Is` checks if an error in the chain matches a target error. Use it for sentinel errors: `errors.Is(err, sql.ErrNoRows)`.

`errors.As` checks if an error in the chain can be assigned to a target type. Use it for typed errors: `errors.As(err, &pgErr)` where `pgErr` is a `*pgconn.PgError`.

The idiomatic pattern for domain errors:

```go
type NotFoundError struct {
    Resource string
    ID       string
}

func (e *NotFoundError) Error() string {
    return fmt.Sprintf("%s %s not found", e.Resource, e.ID)
}

// In a handler:
var notFound *NotFoundError
if errors.As(err, &notFound) {
    http.Error(w, notFound.Error(), http.StatusNotFound)
    return
}
```

**What interviewers look for:** candidates who understand the difference between `errors.Is` and `errors.As`, who wrap errors with context using `fmt.Errorf("loading user: %w", err)`, and who don't use string matching on error messages (fragile) or type assertions without `errors.As` (misses wrapped errors).

## Graceful Shutdown

A production HTTP server must handle in-flight requests cleanly when it receives SIGTERM. The pattern:

```go
server := &http.Server{Addr: ":8080", Handler: mux}

go func() {
    if err := server.ListenAndServe(); !errors.Is(err, http.ErrServerClosed) {
        log.Fatalf("server error: %v", err)
    }
}()

quit := make(chan os.Signal, 1)
signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
<-quit

ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()

if err := server.Shutdown(ctx); err != nil {
    log.Fatalf("server shutdown error: %v", err)
}
```

`server.Shutdown` stops accepting new connections and waits for in-flight requests to complete, up to the timeout. After the timeout, it forcibly closes remaining connections. This is the correct implementation—`server.Close` forcibly closes everything immediately and should only be used as a last resort.

## Database Connection Pooling with pgx

`database/sql` provides connection pooling, but for PostgreSQL at production scale, `pgx` (github.com/jackc/pgx) offers better performance and PostgreSQL-specific features.

Connection pool configuration matters:

```go
config, _ := pgxpool.ParseConfig(os.Getenv("DATABASE_URL"))
config.MaxConns = 25
config.MinConns = 5
config.MaxConnLifetime = time.Hour
config.MaxConnIdleTime = 30 * time.Minute
config.HealthCheckPeriod = time.Minute

pool, _ := pgxpool.NewWithConfig(ctx, config)
```

`MaxConns` should be set based on your database's `max_connections` setting divided by the number of application instances, with headroom for migrations and administrative connections. PostgreSQL's default max_connections is 100—if you have 4 application instances each configured with MaxConns=25, you'll saturate the database under full load.

Interview question: "What happens when your connection pool is exhausted?" With pgx, `pool.Acquire` blocks waiting for an available connection, up to the request context deadline. If the context is cancelled first, the caller gets a context error. This is correct behavior—your request timeout bounds the wait time, preventing indefinite queue buildup.

## Testing HTTP Handlers

`httptest.NewRecorder` and `httptest.NewServer` are the standard library tools for testing handlers. The recorder pattern allows testing a handler in isolation:

```go
func TestGetUser(t *testing.T) {
    req := httptest.NewRequest(http.MethodGet, "/users/123", nil)
    rec := httptest.NewRecorder()

    handler := NewUserHandler(mockUserStore)
    handler.ServeHTTP(rec, req)

    assert.Equal(t, http.StatusOK, rec.Code)
    var user User
    json.NewDecoder(rec.Body).Decode(&user)
    assert.Equal(t, "123", user.ID)
}
```

For integration tests that need a real HTTP server (for testing middleware behavior, content negotiation, or redirects), `httptest.NewServer` starts a real server on a random port:

```go
server := httptest.NewServer(mux)
defer server.Close()

resp, err := http.Get(server.URL + "/health")
```

The test that catches middleware bugs: verify that your auth middleware returns 401 without calling the handler, and that it passes the correct claims via context when authentication succeeds. Test these conditions explicitly—they're easy to get right in isolation and wrong in composition.

Go backend interviews reward engineers who can explain the `why` behind patterns, not just demonstrate they've used them. Understanding that middleware composes because of the `Handler` interface, that context propagation prevents resource leaks, and that graceful shutdown is about respecting in-flight work—these are the answers that distinguish senior engineers.
