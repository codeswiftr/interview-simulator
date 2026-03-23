---
title: "Go/Golang Engineering Interview Guide"
description: "What companies like Google, Cloudflare, Uber, and Docker ask about Go in technical interviews — goroutines, channels, the runtime, and Go-specific design questions."
date: "2026-03-19"
category: "Backend Engineering"
---

Go engineering interviews have a distinct character. Companies that use Go at scale — Cloudflare, Uber, Docker, HashiCorp, Cockroach Labs — care less about algorithmic puzzles and more about whether you understand the runtime, the memory model, and how to write concurrent code that doesn't deadlock. Here's what they actually ask.

## Go-Specific Language Questions

### Goroutines vs OS Threads

The most common opening question. A goroutine is not a thread. It starts at 2–8KB of stack space (compared to 1–8MB for an OS thread), is multiplexed onto OS threads by the Go scheduler, and can be parked cheaply when blocked on I/O or channel operations.

The Go scheduler is an M:N scheduler — M goroutines run on N OS threads, managed by a work-stealing scheduler (the GMP model: Goroutines, OS threads (M), and logical Processors (P)). When a goroutine blocks on a syscall, the scheduler can park the thread and move other goroutines to a different OS thread.

What interviewers want to hear: goroutines are cooperative (yield at function calls, channel ops, syscalls), cheap to create, and the scheduler handles multiplexing. You should be able to explain why you can spawn 100,000 goroutines but not 100,000 OS threads.

### Channel Patterns and the Select Statement

Channels are Go's primary synchronization primitive. Know the difference between buffered and unbuffered channels and their blocking semantics. An unbuffered send blocks until a receiver is ready. A buffered channel blocks the sender only when the buffer is full.

The `select` statement is how you multiplex channel operations. It picks a ready case at random when multiple cases are ready — this is intentional and interviewers sometimes ask why. It prevents starvation.

```go
// Timeout pattern using select
func fetchWithTimeout(ctx context.Context, ch <-chan Result) (Result, error) {
    select {
    case result := <-ch:
        return result, nil
    case <-ctx.Done():
        return Result{}, ctx.Err()
    }
}
```

Know how to implement a done channel for cancellation, and why `context.Context` replaced manual done channels in modern Go.

### Defer, Panic, and Recover

`defer` runs in LIFO order when a function returns — including on a panic. Arguments to a deferred function are evaluated immediately, not when the defer fires. This trips people up:

```go
x := 10
defer fmt.Println(x) // prints 10, not 20
x = 20
```

`recover` only works when called directly from a deferred function. It captures a panic and lets the program continue. The canonical pattern:

```go
func safeExecute(fn func()) (err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("recovered: %v", r)
        }
    }()
    fn()
    return nil
}
```

### Interfaces and Embedding

Go interfaces are satisfied implicitly — no `implements` keyword. This enables duck typing at compile time and is central to how Go achieves polymorphism. Interviewers often ask you to design a system using interfaces, then ask how you'd test it (answer: interfaces make mocking trivial).

Embedding is composition, not inheritance. Embedding a type promotes its methods. Know the difference between embedding an interface in a struct (for mocking/wrapping) versus embedding a concrete type.

```go
type ReadWriter interface {
    io.Reader
    io.Writer
}

type BufferedWriter struct {
    *bufio.Writer // embedded — promotes Flush, Write, etc.
    mu sync.Mutex
}
```

## Concurrency Interview Questions

### Worker Pool Pattern

This is asked frequently at Uber and infrastructure companies. Implement a worker pool with a fixed number of goroutines processing jobs from a channel.

```go
func workerPool(numWorkers int, jobs <-chan Job, results chan<- Result) {
    var wg sync.WaitGroup
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                results <- process(job)
            }
        }()
    }
    wg.Wait()
    close(results)
}
```

Key points: closing the `jobs` channel signals workers to exit, `sync.WaitGroup` tracks completion, closing `results` after `wg.Wait()` signals the consumer.

### Fan-Out Fan-In Pipeline

Pipeline patterns compose stages connected by channels. Fan-out distributes work across multiple goroutines; fan-in merges results.

```go
func fanIn(channels ...<-chan int) <-chan int {
    merged := make(chan int)
    var wg sync.WaitGroup
    forward := func(ch <-chan int) {
        defer wg.Done()
        for v := range ch {
            merged <- v
        }
    }
    wg.Add(len(channels))
    for _, ch := range channels {
        go forward(ch)
    }
    go func() {
        wg.Wait()
        close(merged)
    }()
    return merged
}
```

Be ready to discuss backpressure — what happens when your pipeline processes faster than it consumes, and how buffered channels or semaphores address it.

### Common Concurrency Bugs

Interviewers test for practical awareness. Know these pitfalls:

- **Goroutine leak**: a goroutine blocked forever on a channel no one will write to or read from. Always use `context.Context` for cancellation.
- **Closure capture in goroutines**: the classic loop variable capture bug. Use `go func(v int) { ... }(v)` to capture by value.
- **Data race**: concurrent read/write without synchronization. Use `go test -race` to detect. The fix is a mutex, atomic operation, or channel.

## Go Runtime and Garbage Collector

Companies like Cloudflare and Google ask about the GC because they care about latency. Key points:

- Go uses a **concurrent tri-color mark-and-sweep GC**. Since Go 1.5, it runs concurrently with the program, targeting sub-millisecond stop-the-world pauses.
- The GC is triggered by heap growth (default: when heap doubles). You can tune `GOGC` (default 100) to trade CPU for pause frequency.
- `runtime.ReadMemStats` and `pprof` are the tools for profiling allocation pressure.
- Reducing allocations is the primary lever. Escape analysis determines what lives on the heap vs stack.

## Performance Questions

### Escape Analysis

If the compiler can prove a variable doesn't outlive the function, it's stack-allocated (fast, no GC pressure). Otherwise it escapes to the heap. Use `go build -gcflags='-m'` to see what escapes.

Common escape causes: returning a pointer to a local variable, storing to an interface, closures capturing variables, values too large for the stack.

### Memory Layout and Struct Alignment

Interviewers at systems companies ask about this. Padding between struct fields adds up. Order fields from largest to smallest alignment to minimize struct size:

```go
// 24 bytes due to padding
type Bad struct {
    a bool    // 1 byte + 7 padding
    b float64 // 8 bytes
    c bool    // 1 byte + 7 padding
}

// 16 bytes
type Good struct {
    b float64 // 8 bytes
    a bool    // 1 byte
    c bool    // 1 byte + 6 padding
}
```

### Profiling with pprof

Know the workflow: import `net/http/pprof`, hit `/debug/pprof/`, use `go tool pprof` to analyze. The four profiles to know: CPU, heap (allocations), goroutine (leak detection), and block (contention).

## When to Use Go vs Other Languages

Interviewers at multi-language shops (Uber, Cloudflare) ask this directly. The honest answer:

Go excels at network services, CLIs, and infrastructure tools where you need: high concurrency, predictable latency, fast compile times, and a single binary with no runtime dependency. It's the right call for API servers, proxies, agents, and anything Kubernetes-adjacent.

Go is weaker for: CPU-bound numerical computing (use Rust or C++), rapid prototyping where type verbosity slows iteration (use Python), or domains with rich ecosystem requirements (data science, ML).

The answer they're looking for shows you understand Go's strengths (simplicity, concurrency, operational properties) without overselling it.

## Preparation Checklist

- Implement a goroutine pool and a fan-in merge from scratch
- Be able to explain GMP scheduling in 2 minutes
- Know what `GOMAXPROCS` does and its default value
- Understand nil interface vs nil pointer (a frequent gotcha)
- Read the Go memory model — at minimum, the happens-before rules for channel operations
- Run `go test -race` on any concurrent code you write before an interview

Go interviews reward engineers who've operated Go in production — who've chased goroutine leaks with pprof, tuned GC for latency, and debugged data races. Study the runtime, not just the syntax.
