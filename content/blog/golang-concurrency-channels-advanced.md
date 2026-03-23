---
title: "Advanced Go Concurrency: Select, Done Patterns, and Pipelines"
description: "Go beyond basic goroutines — master select statements, done channels, worker pools, pipeline patterns, and context cancellation for production Go code."
date: "2026-03-20"
category: "Programming Languages"
---

Most Go developers know how to launch goroutines and send values over channels. Fewer understand the patterns that make concurrent Go programs robust at scale: cancellation trees, backpressure in pipelines, bounded worker pools, and the subtle differences between buffered and unbuffered channels. These are the patterns that appear in senior Go interviews and production codebases alike.

## The Select Statement: More Than a Switch

`select` is Go's multiplexer for channel operations. It blocks until one of its cases can proceed, then executes that case. When multiple cases are ready simultaneously, Go picks one uniformly at random — not the first one lexically.

```go
func fanIn(c1, c2 <-chan string) <-chan string {
    merged := make(chan string)
    go func() {
        for {
            select {
            case v := <-c1:
                merged <- v
            case v := <-c2:
                merged <- v
            }
        }
    }()
    return merged
}
```

**Non-blocking select with default:** Adding a `default` case makes the select non-blocking. This is the Go idiom for polling:

```go
select {
case msg := <-ch:
    process(msg)
default:
    // Do other work; ch wasn't ready
}
```

Avoid tight-loop polling with default — it burns CPU. Combine with a timer or use `time.After` for backoff.

## The Done Channel Pattern

The fundamental cancellation primitive in pre-context Go. A `done` channel is closed (not sent to) when work should stop. Goroutines select on it alongside their work channels:

```go
func worker(done <-chan struct{}, jobs <-chan Job) {
    for {
        select {
        case job, ok := <-jobs:
            if !ok {
                return // channel closed
            }
            process(job)
        case <-done:
            return // cancelled
        }
    }
}
```

**Why close instead of send?** Closing broadcasts to all receivers simultaneously. A send only unblocks one receiver. This is critical for cancelling multiple goroutines at once.

## Context Cancellation: The Modern Done Pattern

`context.Context` supersedes raw done channels in modern Go. It carries deadlines, cancellation signals, and request-scoped values through your call tree.

```go
func fetchAll(ctx context.Context, urls []string) ([]Result, error) {
    results := make(chan Result, len(urls))
    errCh := make(chan error, 1)

    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel() // Always call cancel to release resources

    for _, url := range urls {
        url := url // capture loop variable
        go func() {
            req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
            if err != nil {
                select {
                case errCh <- err:
                default:
                }
                return
            }
            resp, err := http.DefaultClient.Do(req)
            if err != nil {
                select {
                case errCh <- err:
                default:
                }
                return
            }
            defer resp.Body.Close()
            results <- parseResult(resp)
        }()
    }

    var all []Result
    for range urls {
        select {
        case r := <-results:
            all = append(all, r)
        case err := <-errCh:
            return nil, err
        case <-ctx.Done():
            return nil, ctx.Err()
        }
    }
    return all, nil
}
```

**Critical rule:** Always `defer cancel()` immediately after `WithCancel`, `WithTimeout`, or `WithDeadline`. Forgetting this leaks the context goroutine.

**Context values:** Use context values sparingly, only for request-scoped data (trace IDs, auth tokens). Never use context to pass optional function parameters — that's a misuse pattern.

## Worker Pool Pattern

The bounded worker pool is the most common concurrency pattern in production Go. It limits parallelism to prevent resource exhaustion:

```go
func processWithPool(ctx context.Context, items []Item, concurrency int) []Result {
    jobs := make(chan Item, len(items))
    results := make(chan Result, len(items))

    // Launch fixed number of workers
    var wg sync.WaitGroup
    for i := 0; i < concurrency; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                select {
                case <-ctx.Done():
                    return
                default:
                    results <- process(job)
                }
            }
        }()
    }

    // Feed jobs
    for _, item := range items {
        jobs <- item
    }
    close(jobs) // Signal workers to exit after draining

    // Wait and close results
    go func() {
        wg.Wait()
        close(results)
    }()

    var all []Result
    for r := range results {
        all = append(all, r)
    }
    return all
}
```

**Sizing the pool:** CPU-bound work: `runtime.NumCPU()`. I/O-bound work: much larger, typically 10–100× depending on latency. Benchmark your specific workload.

## Pipeline Pattern

Pipelines chain stages together, each stage reading from the previous output channel:

```go
func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for _, n := range nums {
            out <- n
        }
    }()
    return out
}

func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            out <- n * n
        }
    }()
    return out
}

func filter(in <-chan int, pred func(int) bool) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            if pred(n) {
                out <- n
            }
        }
    }()
    return out
}

// Usage
nums := generate(2, 3, 4, 5, 6)
squares := square(nums)
evens := filter(squares, func(n int) bool { return n%2 == 0 })
```

**Cancellation in pipelines:** Each stage should also select on a done channel or context. Otherwise, a slow consumer blocks producers indefinitely (goroutine leak):

```go
func squareWithCancel(ctx context.Context, in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            select {
            case out <- n * n:
            case <-ctx.Done():
                return
            }
        }
    }()
    return out
}
```

## Backpressure and Buffered Channels

Buffered channels add a queue between producer and consumer. They don't eliminate backpressure — they defer it. A buffered channel of size n allows the producer to run up to n items ahead before blocking.

Use buffered channels when:
- You know the exact number of results (fan-out/fan-in with known count)
- You want to decouple burst behavior from steady-state processing
- Latency spikes on one side shouldn't directly stall the other

Avoid buffered channels to "fix" race conditions — that masks the real problem.

## Common Interview Questions

**Q: What happens if you send to a closed channel?**
A: Panic. Always let the producer close the channel, never the consumer.

**Q: What happens if you read from a nil channel?**
A: Blocks forever. Reading from a closed channel returns the zero value and false.

**Q: How do you implement a semaphore in Go?**
A: Buffered channel: `sem := make(chan struct{}, n)`. Acquire: `sem <- struct{}{}`. Release: `<-sem`.

**Q: Explain sync.WaitGroup vs channels for synchronization.**
A: `WaitGroup` is for "wait until all goroutines finish." Channels are for communication and coordination. Use the right tool — don't use channels just to synchronize completion.

Mastering these patterns puts you firmly in the top tier for Go interviews. The patterns aren't complex, but they require understanding the memory model and knowing which primitives compose cleanly. Practice implementing a bounded worker pool and a context-aware pipeline from scratch — those two cover 80% of real production needs.
