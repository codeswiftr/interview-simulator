---
title: "Python Concurrency and AsyncIO: Interview Guide for Senior Engineers"
description: "Deep-dive Python concurrency interview preparation — GIL internals, threading vs multiprocessing, asyncio event loop, async/await patterns, and production concurrency patterns for backend systems."
date: "2026-03-20"
category: "Programming Languages"
---

# Python Concurrency and AsyncIO: Interview Guide for Senior Engineers

Python concurrency questions are notoriously tricky because Python has multiple concurrency models, each suited to different problems, and a fundamental constraint (the GIL) that shapes how they work. Senior Python interviews probe whether you understand these models deeply enough to choose the right one and avoid common pitfalls.

## The GIL: What It Actually Does

The Global Interpreter Lock (GIL) is a mutex that protects CPython's reference counting from race conditions. Only one thread can execute Python bytecode at a time. This prevents parallel CPU execution across threads.

**What the GIL doesn't affect**: I/O operations release the GIL. When a thread calls `socket.recv()` or `file.read()`, it releases the GIL before blocking, allowing other threads to run. This is why threading works well for I/O-bound tasks despite the GIL.

**What the GIL does affect**: CPU-bound tasks can't benefit from multiple threads. Two threads doing heavy computation will run serially, not in parallel.

**Interview answer**: "The GIL prevents true parallel execution for CPU-bound work. For I/O-bound work, threads work fine because the GIL is released during I/O operations. For CPU-bound parallelism, use multiprocessing — each process has its own GIL and its own Python interpreter."

## threading vs multiprocessing vs asyncio

The decision tree:

| Scenario | Tool |
|----------|------|
| I/O-bound, many concurrent connections | asyncio |
| I/O-bound, simpler code OK | threading |
| CPU-bound, parallelism needed | multiprocessing |
| CPU-bound, data processing | ProcessPoolExecutor |

**threading**: `threading.Thread` or `concurrent.futures.ThreadPoolExecutor`. Use for I/O-bound tasks where blocking is acceptable. The overhead per thread (~8MB stack, OS scheduling) limits you to hundreds of concurrent threads.

**multiprocessing**: Spawns separate OS processes. No GIL contention. Data is passed via pickling (serialization) which adds overhead. Use for CPU-bound work that benefits from multiple cores. `multiprocessing.Pool` and `ProcessPoolExecutor` manage the pool for you.

**asyncio**: Single-threaded, event-loop-based concurrency. Handles thousands of concurrent I/O operations with low overhead. Requires your entire call stack to be async-aware — you can't call blocking code from async functions without blocking the event loop.

## AsyncIO Deep Dive

The asyncio event loop is a scheduler that runs coroutines. A coroutine is a function defined with `async def` that can be suspended at `await` points.

```python
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def main():
    # Run 100 requests concurrently
    urls = [f"https://api.example.com/item/{i}" for i in range(100)]
    results = await asyncio.gather(*[fetch_data(url) for url in urls])
    return results
```

**What `await` does**: Suspends the current coroutine and yields control back to the event loop. The event loop can run other coroutines while waiting. When the awaited operation completes, the event loop resumes this coroutine.

**asyncio.gather vs asyncio.TaskGroup**: `gather` runs coroutines concurrently. `TaskGroup` (Python 3.11+) provides structured concurrency — if any task fails, all others are cancelled automatically. Prefer `TaskGroup` for production code.

## Common Asyncio Pitfalls

**Blocking the event loop**: The most critical mistake. Any synchronous blocking call (`time.sleep()`, `requests.get()`, CPU-intensive computation) blocks the entire event loop and all other coroutines.

Fix: Use `asyncio.sleep()` instead of `time.sleep()`. For blocking I/O, use async libraries (aiohttp, asyncpg). For CPU-bound work, use `loop.run_in_executor()` to delegate to a thread pool.

**Not awaiting coroutines**: Calling an `async def` function without `await` returns a coroutine object without executing it. Python 3.11+ generates a warning; earlier versions silently drop it.

**Task cancellation**: Always handle `CancelledError` properly in cleanup code. Use `try/finally` to ensure resources are released even when tasks are cancelled.

```python
async def worker():
    try:
        await do_work()
    except asyncio.CancelledError:
        await cleanup()
        raise  # Always re-raise CancelledError
```

## Synchronization Primitives

AsyncIO provides async versions of standard synchronization primitives:

- `asyncio.Lock()`: Mutual exclusion for coroutines
- `asyncio.Semaphore(n)`: Limit concurrent access (rate limiting, connection pool size)
- `asyncio.Event()`: Signal between coroutines
- `asyncio.Queue()`: Producer-consumer patterns

```python
# Semaphore example: limit to 10 concurrent requests
semaphore = asyncio.Semaphore(10)

async def rate_limited_fetch(url):
    async with semaphore:
        return await fetch(url)
```

## Interview Scenarios

**"How would you process 1 million records in Python?"**

CPU-bound transformation: `ProcessPoolExecutor` with `executor.map()`, splitting work into chunks. I/O-bound fetching: asyncio with controlled concurrency via `Semaphore` to avoid overwhelming the target.

**"A FastAPI endpoint is slow. How do you diagnose it?"**

First check: is the slow operation CPU or I/O? Profile with `cProfile` for CPU. Add timing instrumentation for I/O. Common causes: database queries without proper indexes, synchronous calls in async handlers, N+1 queries. Fix async handlers that call sync libraries by using `run_in_executor` or switching to async equivalents.

**"What happens when you `await asyncio.gather(*tasks)` and one raises an exception?"**

By default, `gather` returns exceptions as results (if `return_exceptions=True`) or raises the first exception and cancels other tasks (if `return_exceptions=False`, the default). With `TaskGroup`, all tasks are cancelled if any fail — the correct behavior for most production code.

Mastering Python's concurrency model — knowing not just the APIs but why they work the way they do — is what distinguishes senior Python engineers from those who've just used `async/await` without understanding its constraints.
