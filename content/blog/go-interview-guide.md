---
title: "Go (Golang) Technical Interview Guide: Concurrency, Interfaces, and Performance"
description: "Prepare for Go-specific technical interviews. Covers goroutines and channels, interfaces, error handling, memory management, and what senior Go engineers need to know."
date: "2025-10-29"
category: "Technical Skills Guides"
---

# Go Technical Interview Guide

Go has become the language of choice for high-performance backend systems, infrastructure tooling, and cloud-native applications. Companies like Google, Cloudflare, Stripe, HashiCorp, and Docker hire Go engineers specifically. This guide covers what Go interviews test at all levels.

## Go for Coding Problems

Go's standard library and type system make it excellent for coding interviews. Key patterns:

### Core Data Structures

```go
// Map (hash table)
freq := make(map[string]int)
freq["hello"]++

// Slice (dynamic array)
stack := []int{}
stack = append(stack, 1)
top := stack[len(stack)-1]
stack = stack[:len(stack)-1]  // pop

// Queue (deque with slices)
queue := []int{1, 2, 3}
queue = append(queue, 4)  // enqueue
val, queue := queue[0], queue[1:]  // dequeue
```

### Sorting

```go
import "sort"

// Sort ints
nums := []int{3, 1, 4, 1, 5}
sort.Ints(nums)

// Custom sort
sort.Slice(intervals, func(i, j int) bool {
    return intervals[i][0] < intervals[j][0]
})
```

## Go Concurrency: The Core Differentiator

Go's concurrency model is its most distinctive feature. Interviews for senior Go roles heavily test goroutines, channels, and synchronization.

### Goroutines

Goroutines are lightweight threads managed by the Go runtime. Thousands to millions can run concurrently.

```go
go func() {
    // Runs concurrently
    processItem(item)
}()
```

**Common interview question**: "What's the difference between a goroutine and a thread?"
- Goroutines: 2KB initial stack (grows as needed), ~1 microsecond to create, multiplexed onto OS threads by the Go scheduler
- OS threads: 1-8MB fixed stack, microseconds to milliseconds to create, directly scheduled by OS

### Channels

Channels are the primary communication mechanism between goroutines ("don't communicate by sharing memory, share memory by communicating").

```go
// Unbuffered: sender blocks until receiver is ready
ch := make(chan int)

// Buffered: sender blocks only when buffer is full
ch := make(chan int, 10)

// Directional channels
func producer(ch chan<- int) { ch <- 42 }  // Send only
func consumer(ch <-chan int) { val := <-ch }  // Receive only

// Select: wait on multiple channels
select {
case msg := <-ch1:
    fmt.Println("from ch1:", msg)
case msg := <-ch2:
    fmt.Println("from ch2:", msg)
case <-time.After(1 * time.Second):
    fmt.Println("timeout")
}
```

### Sync Primitives

```go
import "sync"

// WaitGroup: wait for multiple goroutines
var wg sync.WaitGroup
for _, url := range urls {
    wg.Add(1)
    go func(u string) {
        defer wg.Done()
        fetch(u)
    }(url)
}
wg.Wait()

// Mutex: protect shared state
var mu sync.RWMutex
mu.Lock()
sharedMap[key] = value
mu.Unlock()

// Once: execute exactly once
var once sync.Once
once.Do(func() { initialize() })
```

### Common Concurrency Patterns

**Worker pool:**
```go
func workerPool(jobs <-chan Job, results chan<- Result, numWorkers int) {
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

## Interfaces and Composition

Go doesn't have inheritance — it uses interfaces and composition.

```go
// Interface is satisfied implicitly
type Writer interface {
    Write(p []byte) (n int, err error)
}

// io.Writer, net.Conn, os.File all satisfy Writer
// without explicitly declaring so

// Embedding for composition
type TimedWriter struct {
    io.Writer
    start time.Time
}
```

**Interview question**: "How is Go's interface system different from Java's?"
- Go interfaces are implicit (structural typing vs. nominal typing)
- Any type with the right methods satisfies an interface automatically
- This enables retroactive interface satisfaction (add a method to an external type to satisfy your interface)

## Error Handling

```go
// Multiple return values for errors (no exceptions)
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, fmt.Errorf("division by zero")
    }
    return a / b, nil
}

result, err := divide(10, 0)
if err != nil {
    log.Printf("error: %v", err)
    return
}

// Wrapping errors (Go 1.13+)
return fmt.Errorf("processing failed: %w", err)

// Unwrapping
if errors.Is(err, ErrNotFound) { ... }
var nfe *NotFoundError
if errors.As(err, &nfe) { ... }
```

## Memory Management and Performance

**Escape analysis**: Go's compiler decides whether to allocate on the heap or stack. Variables that "escape" (are referenced after the function returns) go to heap.

**Garbage collector**: Go's concurrent, tri-color mark-and-sweep GC. Target: < 1ms pause times. Tunable via `GOGC` env var (default: 100 = GC when heap doubles).

**Profiling**:
```go
import _ "net/http/pprof"

// CPU profile
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30
// Memory profile
go tool pprof http://localhost:6060/debug/pprof/heap
```

## What Go Interviewers Test

At **junior level**: Basic Go syntax, slices vs. arrays, maps, basic goroutines.

At **mid-level**: Channel patterns, error handling idioms, interfaces, testing with `testing` package.

At **senior level**: Concurrency correctness (race conditions, deadlocks), performance optimization, profiling, scheduler understanding, advanced interface patterns.

**Common interview problems in Go**: Implement a concurrent safe map, build a worker pool, implement a rate limiter using channels, design a context-aware HTTP client with timeouts and retries.
