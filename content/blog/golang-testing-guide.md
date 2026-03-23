---
title: "Go Testing Guide: Table-Driven Tests, Mocking, Benchmarks, and Test Patterns for Production Code"
description: "A comprehensive guide to writing effective Go tests — table-driven patterns, interface-based mocking, benchmark testing, test helpers, and the practices that distinguish production-quality test suites."
date: "2026-03-20"
category: "Programming Languages"
---

Go's testing philosophy is opinionated: the standard library provides just enough tooling to write effective tests without imposing a framework. The result is that Go test suites vary widely in quality. This guide covers the patterns used in serious Go codebases — the ones interviewers expect senior candidates to know.

## Table-Driven Tests

Table-driven tests are idiomatic Go. They reduce duplication, make it easy to add cases, and produce clear output when tests fail. The structure:

```go
func TestAdd(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive numbers", 2, 3, 5},
        {"negative numbers", -1, -2, -3},
        {"zero", 0, 5, 5},
        {"mixed signs", -3, 7, 4},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := Add(tt.a, tt.b)
            if got != tt.expected {
                t.Errorf("Add(%d, %d) = %d, want %d", tt.a, tt.b, got, tt.expected)
            }
        })
    }
}
```

`t.Run` creates subtests named `TestAdd/positive_numbers`, `TestAdd/zero`, etc. You can run a specific subtest with `go test -run "TestAdd/zero"`. Subtests also run in parallel with `t.Parallel()` inside the subtest body.

**When to use a struct vs. named fields:** For more than 3 fields in the test case struct, use named fields when initializing cases. For 2–3 fields, positional initialization is fine. Consistency within a file matters more than a fixed rule.

## Subtests and Parallel Execution

```go
for _, tt := range tests {
    tt := tt  // capture loop variable — critical before Go 1.22
    t.Run(tt.name, func(t *testing.T) {
        t.Parallel()
        // test body
    })
}
```

The `tt := tt` shadow is required in Go versions before 1.22 because the loop variable is shared across iterations. The goroutine spawned by `t.Parallel()` captures the variable; without shadowing, all subtests see the last loop value. Go 1.22 changed loop variable semantics to make this unnecessary, but you'll encounter both patterns in production code.

## Interface-Based Mocking

Go's implicit interface satisfaction is the foundation of testable design. Define small interfaces at the point of use:

```go
// emailer.go
type Emailer interface {
    Send(to, subject, body string) error
}

type NotificationService struct {
    emailer Emailer
}

func (s *NotificationService) NotifyUser(userID string) error {
    // ... build message ...
    return s.emailer.Send(email, subject, body)
}
```

In tests, inject a mock:

```go
type mockEmailer struct {
    calls []string
    err   error
}

func (m *mockEmailer) Send(to, subject, body string) error {
    m.calls = append(m.calls, to)
    return m.err
}

func TestNotifyUser(t *testing.T) {
    mock := &mockEmailer{}
    svc := &NotificationService{emailer: mock}
    
    err := svc.NotifyUser("user-123")
    if err != nil {
        t.Fatal(err)
    }
    if len(mock.calls) != 1 {
        t.Errorf("expected 1 email, got %d", len(mock.calls))
    }
}
```

For more complex mocks, `testify/mock` or `gomock` add expectation-based verification. For simple cases, hand-written mocks like above are idiomatic and have no dependencies.

## Test Helpers with t.Helper()

Test helpers reduce repetition in test bodies. Mark them with `t.Helper()` so failures point to the calling test, not the helper:

```go
func assertNoError(t *testing.T, err error) {
    t.Helper()
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
}

func assertEqual(t *testing.T, got, want interface{}) {
    t.Helper()
    if got != want {
        t.Errorf("got %v, want %v", got, want)
    }
}
```

Without `t.Helper()`, when `assertNoError` fails, the error points to line 3 of the helper. With it, the error points to the `assertNoError(t, err)` call in your test — which is where you need to look.

## Benchmarks

Benchmarks live in `*_test.go` files and start with `Benchmark`:

```go
func BenchmarkJSONMarshal(b *testing.B) {
    data := map[string]interface{}{
        "id":   "user-123",
        "name": "Alice",
        "age":  30,
    }
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, err := json.Marshal(data)
        if err != nil {
            b.Fatal(err)
        }
    }
}
```

Run with `go test -bench=. -benchmem`. The `-benchmem` flag adds allocation statistics — crucial for catching memory regressions.

`b.ResetTimer()` excludes setup time from the benchmark. `b.StopTimer()` and `b.StartTimer()` pause and resume the timer around expensive setup that must happen inside the loop.

For comparing implementations: `go test -bench=. -count=5 | benchstat old.txt -` (using the `benchstat` tool) gives statistically sound comparison with p-values.

## Testing HTTP Handlers

`net/http/httptest` provides `httptest.NewRecorder()` for capturing handler responses without a real server:

```go
func TestGetUserHandler(t *testing.T) {
    req := httptest.NewRequest("GET", "/users/123", nil)
    w := httptest.NewRecorder()

    handler := GetUserHandler(mockUserStore)
    handler.ServeHTTP(w, req)

    resp := w.Result()
    if resp.StatusCode != http.StatusOK {
        t.Errorf("got status %d, want %d", resp.StatusCode, http.StatusOK)
    }
    
    var user User
    json.NewDecoder(resp.Body).Decode(&user)
    if user.ID != "123" {
        t.Errorf("got user %s, want 123", user.ID)
    }
}
```

`httptest.NewServer` starts a real HTTP server on a random port for integration tests where you need a real client.

## Testing with Context

Production code takes `context.Context`. Tests should pass meaningful contexts:

```go
func TestWithTimeout(t *testing.T) {
    ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
    defer cancel()
    
    result, err := slowOperation(ctx)
    if !errors.Is(err, context.DeadlineExceeded) {
        t.Errorf("expected deadline exceeded, got %v", err)
    }
}
```

Test that your functions respect context cancellation — don't just test the happy path.

## Test Organization

- One `_test.go` file per source file is a common convention, but not enforced
- Use `package foo` (white-box) when you need to test unexported functions
- Use `package foo_test` (black-box) when testing the public API — preferred for library code
- `TestMain` for setup/teardown at the package level (starting a test database, for example)

## Running Tests

```bash
go test ./...                         # all packages
go test -v ./...                      # verbose
go test -run TestFoo ./...            # specific test
go test -race ./...                   # race detector (always use in CI)
go test -cover -coverprofile=c.out    # coverage
go tool cover -html=c.out             # visualize coverage
```

The race detector (`-race`) is non-negotiable in CI for any concurrent code. It adds overhead but catches data races that are otherwise nearly impossible to reproduce.
