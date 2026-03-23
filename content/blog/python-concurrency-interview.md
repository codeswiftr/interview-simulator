---
title: "Python Concurrency Interview Guide: asyncio, Threading, and Multiprocessing"
description: "Python concurrency for technical interviews — the GIL, asyncio event loop, async/await patterns, threading vs. multiprocessing vs. asyncio decision tree, and common concurrency bugs."
date: "2026-03-20"
category: "Programming Languages"
---

# Python Concurrency Interview Guide: asyncio, Threading, and Multiprocessing

Python concurrency is a frequent interview topic at companies with Python backends, data pipelines, or systems code. The GIL, three concurrency models, and their appropriate use cases are expected knowledge for senior roles. This guide covers what interviewers actually probe.

## The Global Interpreter Lock (GIL)

The GIL is CPython's mutex that protects access to Python objects. Only one thread can execute Python bytecode at a time.

**Implications:**
- CPU-bound work with threads: no parallelism. Threads context-switch but don't run simultaneously on multiple cores.
- I/O-bound work with threads: effective. While a thread waits for I/O, the GIL is released and another thread runs.
- Multiprocessing: bypasses the GIL entirely. Each process has its own Python interpreter and GIL.

**Interview question:** "Can Python threads run in parallel?"

The precise answer: for CPU-bound work, no — the GIL prevents simultaneous execution. For I/O-bound work, effectively yes — threads release the GIL during I/O waits, enabling other threads to run. The threading module is useful for I/O concurrency; multiprocessing is needed for CPU parallelism.

## asyncio: Event Loop and Coroutines

asyncio is Python's cooperative multitasking framework. A single-threaded event loop runs coroutines, switching between them at `await` points.

```python
import asyncio

async def fetch_data(url):
    # Yield control while waiting for I/O
    await asyncio.sleep(1)  # Simulates I/O wait
    return f"data from {url}"

async def main():
    # Run two fetches concurrently
    results = await asyncio.gather(
        fetch_data("https://api1.example.com"),
        fetch_data("https://api2.example.com"),
    )
    print(results)

asyncio.run(main())
```

**`asyncio.gather` vs. `asyncio.create_task`:**

```python
# gather: run and wait for all
results = await asyncio.gather(coro1(), coro2(), coro3())

# create_task: schedule a coroutine, continue doing other work
task = asyncio.create_task(long_running_coro())
# ... do other work ...
result = await task  # Wait for it later
```

**Key concept:** asyncio is single-threaded. "Concurrency" here means interleaving, not parallelism. While one coroutine awaits I/O, another runs. CPU-bound coroutines block the event loop for all other coroutines.

## When to Use Which Concurrency Model

```
Is the work I/O-bound or CPU-bound?

I/O-bound:
├── Many concurrent connections (thousands): asyncio
├── Simpler code preferred: threading (ThreadPoolExecutor)
└── Legacy synchronous libraries: threading

CPU-bound:
├── Pure Python computation: multiprocessing
├── NumPy/pandas (releases GIL): threading may work
└── Embarrassingly parallel: concurrent.futures ProcessPoolExecutor
```

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import asyncio

# I/O-bound work: thread pool
with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(fetch_url, urls))

# CPU-bound work: process pool
with ProcessPoolExecutor() as executor:
    results = list(executor.map(heavy_computation, data_chunks))

# Mixing asyncio with blocking sync code
async def run_in_thread(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)
```

## Common asyncio Patterns

**Producer-consumer with asyncio.Queue:**

```python
async def producer(queue):
    for item in data_source:
        await queue.put(item)
    await queue.put(None)  # Sentinel

async def consumer(queue):
    while True:
        item = await queue.get()
        if item is None:
            break
        await process(item)
        queue.task_done()

async def main():
    queue = asyncio.Queue(maxsize=100)
    await asyncio.gather(producer(queue), consumer(queue))
```

**Timeout handling:**

```python
try:
    result = await asyncio.wait_for(
        fetch_data(url),
        timeout=5.0
    )
except asyncio.TimeoutError:
    print("Request timed out")
```

**Semaphore for concurrency limiting:**

```python
semaphore = asyncio.Semaphore(10)  # Max 10 concurrent tasks

async def fetch_with_limit(url):
    async with semaphore:
        return await fetch_data(url)

# Run 100 URLs but max 10 at a time
tasks = [fetch_with_limit(url) for url in urls]
results = await asyncio.gather(*tasks)
```

## Common Concurrency Bugs

**Shared mutable state (threading):**

```python
# Bug: race condition
counter = 0

def increment():
    global counter
    counter += 1  # Not atomic! Read-modify-write is three operations

# Fix: use threading.Lock
lock = threading.Lock()
def increment_safe():
    global counter
    with lock:
        counter += 1
```

**Forgetting to await:**

```python
# Bug: creates coroutine object but doesn't run it
result = fetch_data(url)  # Returns coroutine, not result

# Fix:
result = await fetch_data(url)
```

**Blocking the event loop:**

```python
# Bug: blocks the event loop for all other coroutines
async def bad():
    import time
    time.sleep(5)  # Blocks! Use asyncio.sleep(5) instead

# For blocking I/O or CPU work in async context:
async def good():
    await asyncio.get_event_loop().run_in_executor(None, blocking_function)
```

**Race condition with shared state in asyncio (less common but possible):**

Despite being single-threaded, asyncio can have race conditions when shared state is modified across `await` points. Between `await` calls, another coroutine can run and modify the same state.

```python
# Can be racy if another coroutine modifies balance between the two awaits
async def transfer(from_account, to_account, amount):
    balance = await get_balance(from_account)  # Await point
    if balance >= amount:
        await update_balance(from_account, -amount)  # Await point
        await update_balance(to_account, amount)
```

Use asyncio locks or database transactions for atomic operations.

## Interview Answers

**"When would you use asyncio vs. threading?"** asyncio for new code with high concurrency (thousands of concurrent connections, microservices, API servers). Threading for integrating with synchronous libraries (database drivers, legacy code), or when simpler code is preferred over maximum performance.

**"How do you run CPU-bound work in an async application?"** Use `run_in_executor` with a ProcessPoolExecutor to off-load CPU work to a separate process, preventing blocking of the event loop.

**"What is a coroutine?"** A function defined with `async def` that can suspend execution at `await` points, yielding control back to the event loop. Different from a thread: coroutines are cooperative (they yield voluntarily); threads are preemptive (they can be interrupted).
