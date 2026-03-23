---
title: "Go Concurrency Interview Guide: Goroutines, Channels, and Sync Patterns"
description: "Master Go concurrency for technical interviews — goroutines, channels, select, sync primitives, and common patterns like worker pools, pipelines, and fan-out/fan-in with working code examples."
date: "2026-03-20"
category: "Technical Skills"
---

# Go Concurrency Interview Guide: Goroutines, Channels, and Sync Patterns

Go's concurrency model is one of its defining features — and a major focus area in any Go engineering interview. Companies like Google, Cloudflare, Docker, HashiCorp, and Temporal use Go extensively, and interviewers at these companies expect deep fluency with goroutines, channels, and synchronization primitives.

## The GMP Scheduler Model

Go's runtime uses a three-component scheduler: **G** (goroutines), **M** (OS threads), and **P** (logical processors). Understanding this model helps you reason about performance.

- **G (Goroutine):** Lightweight thread managed by the Go runtime. Starts at 2-8KB stack, grows as needed.
- **M (Machine):** OS thread. The runtime creates M threads to execute goroutines.
- **P (Processor):** Execution context. GOMAXPROCS determines how many Ps exist. Each P has a local run queue of goroutines.

Why does this matter in interviews? When you use `GOMAXPROCS(1)`, only one goroutine runs at a time — useful for understanding sequential behavior. The scheduler is cooperative (with preemption points at function calls and since Go 1.14, at loop iterations), meaning goroutines yield on syscalls and channel operations.

## Channels: The Core Primitive

Channels provide communication and synchronization between goroutines. The key rule: **don't communicate by sharing memory; share memory by communicating**.

**Buffered vs unbuffered:**

```go
unbuffered := make(chan int)      // send blocks until receiver ready
buffered := make(chan int, 10)    // send blocks only when buffer full
```

Unbuffered channels provide synchronization guarantees — the send and receive happen simultaneously. Buffered channels decouple sender and receiver speed.

**Channel direction in function signatures:**

```go
func producer(out chan<- int) { out <- 42 }   // send-only
func consumer(in <-chan int) { v := <-in }    // receive-only
```

This is an interview favorite — it makes data flow explicit and prevents misuse.

**Closing channels:** Only the sender closes. Receivers can detect closure:

```go
for v := range ch { /* ranges until ch is closed */ }
v, ok := <-ch  // ok=false when closed and empty
```

## Select Statement

`select` is Go's multiplexing primitive for channels:

```go
select {
case msg := <-ch1:
    fmt.Println("from ch1:", msg)
case ch2 <- data:
    fmt.Println("sent to ch2")
case <-time.After(5 * time.Second):
    fmt.Println("timeout")
default:
    fmt.Println("no channel ready")
}
```

Key interview points:
- If multiple cases are ready, `select` chooses one **uniformly at random**
- `default` makes select non-blocking
- `time.After` creates a timer channel — commonly used for timeouts

## Essential Sync Patterns

**Worker Pool:**

```go
func workerPool(jobs <-chan Job, results chan<- Result, n int) {
    var wg sync.WaitGroup
    for i := 0; i < n; i++ {
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

**Pipeline:**

```go
func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums { out <- n }
        close(out)
    }()
    return out
}

func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in { out <- n * n }
        close(out)
    }()
    return out
}
```

**Fan-out / Fan-in:**

Fan-out distributes work to multiple goroutines; fan-in merges results:

```go
func fanIn(channels ...<-chan int) <-chan int {
    merged := make(chan int)
    var wg sync.WaitGroup
    for _, ch := range channels {
        wg.Add(1)
        go func(c <-chan int) {
            defer wg.Done()
            for v := range c { merged <- v }
        }(ch)
    }
    go func() { wg.Wait(); close(merged) }()
    return merged
}
```

## sync Package

**Mutex and RWMutex:**

```go
var mu sync.Mutex
mu.Lock()
defer mu.Unlock()
// critical section

var rw sync.RWMutex
rw.RLock()    // multiple concurrent readers
defer rw.RUnlock()
```

**WaitGroup:** Track completion of a set of goroutines. `Add` before starting goroutines; `Done` in defer; `Wait` to block.

**Once:** Execute exactly once — useful for lazy initialization:

```go
var once sync.Once
var instance *Singleton

func getInstance() *Singleton {
    once.Do(func() { instance = &Singleton{} })
    return instance
}
```

**atomic:** For simple counters without mutex overhead:

```go
var count int64
atomic.AddInt64(&count, 1)
n := atomic.LoadInt64(&count)
```

## Common Interview Questions

**Q: What's the difference between a goroutine leak and a deadlock?**
A deadlock happens when all goroutines are blocked — the Go runtime panics. A goroutine leak happens when goroutines are blocked but others continue running — no panic, just memory growth. The most common leak: a goroutine blocked on a channel that no one will ever write to or read from.

**Q: How do you cancel a goroutine?**
Use `context.Context` with cancellation:

```go
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

go func() {
    for {
        select {
        case <-ctx.Done():
            return
        case work := <-jobs:
            process(work)
        }
    }
}()
```

**Q: When would you use a buffered channel vs unbuffered?**
Unbuffered for synchronization — you need confirmation the receiver got the message. Buffered for decoupling — producer can move ahead without waiting. Classic buffered use case: semaphore limiting concurrent goroutines.

**Q: Is this code safe? `go fmt.Println(m["key"])` where m is a map.**
No. Map reads from goroutines require either a mutex or `sync.Map`. Go's race detector (`go test -race`) will catch this.

## What Interviewers Are Scoring

Strong candidates understand *why* patterns work, not just the syntax. When you write a worker pool, explain: "WaitGroup tracks active workers; ranging over the jobs channel means workers stop when jobs is closed; we close results after all workers finish so the consumer's range terminates cleanly." That chain of reasoning — showing you understand goroutine lifecycles, channel semantics, and synchronization — is what separates good Go engineers from copy-paste implementers.
