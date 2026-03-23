---
title: "Python Engineering Interview Guide"
description: "Python-specific interview questions covering the GIL, memory model, asyncio, generators, decorators, and what companies like Instagram, Dropbox, and Stripe ask about Python."
date: "2026-03-19"
category: "Backend Engineering"
---

## What Python Interviews Actually Test

Python interviews at companies like Instagram, Dropbox, and Stripe go well beyond syntax. They test whether you understand the runtime, can reason about performance characteristics, and know when Python's design choices become constraints at scale. This guide covers the questions that trip up even experienced engineers.

---

## The GIL: Threading, Multiprocessing, and When It Matters

The Global Interpreter Lock (GIL) is Python's single most important runtime constraint for interview purposes. The GIL ensures that only one thread executes Python bytecode at a time, even on multi-core machines.

**What interviewers want to hear:**

- The GIL protects CPython's internal data structures (reference counts, object allocator) from concurrent access. It is not a design flaw — it is a deliberate trade-off.
- I/O-bound work (`requests`, database calls, file reads) releases the GIL. Threading works well here.
- CPU-bound work (numerical computation, parsing, encryption) does not benefit from threading in CPython. Use `multiprocessing` or `concurrent.futures.ProcessPoolExecutor` instead.
- `asyncio` is single-threaded and sidesteps the GIL entirely by using cooperative multitasking.

```python
# GIL-limited: no speedup from threading on CPU-bound work
import threading

def count(n):
    while n > 0:
        n -= 1

# Two threads, same core — roughly same wall time as single-threaded
t1 = threading.Thread(target=count, args=(10**7,))
t2 = threading.Thread(target=count, args=(10**7,))
t1.start(); t2.start()
t1.join(); t2.join()
```

**Follow-up question:** "How does Instagram use Python at scale given the GIL?" Answer: they rely heavily on async I/O, process-level parallelism (gunicorn workers), and offload CPU work to C extensions (NumPy, Pillow) that release the GIL.

---

## Memory Management and Garbage Collection

Python manages memory through two mechanisms: reference counting and a cyclic garbage collector.

**Reference counting** is the primary mechanism. Every object has a `ob_refcnt` field. When it hits zero, the object is immediately deallocated. This gives predictable cleanup but has two problems: it adds overhead to every object operation, and it cannot collect reference cycles.

**The cyclic GC** handles cycles. It runs periodically, scanning generation 0 (recently allocated), 1, and 2 (long-lived). You can tune this with `gc.set_threshold()` or disable it for latency-sensitive applications.

```python
import gc
import sys

a = []
b = [a]
a.append(b)       # cycle: a → b → a
del a, b
# Reference counts are both 1 (each holds a ref to the other)
# Neither reaches zero — cyclic GC must collect these

gc.collect()      # force collection; returns number of unreachable objects collected
```

**What interviewers probe:** Can you explain why `__del__` is unreliable? (Cycles containing `__del__` were uncollectable before Python 3.4.) How do you profile memory leaks? (Use `tracemalloc`, `objgraph`, or `memory_profiler`.)

---

## Generators and itertools

Generators are lazy sequences. They produce values on demand rather than materializing the entire collection in memory. This is the correct answer for any question about processing large datasets in Python.

```python
def chunked(iterable, size):
    """Yield successive chunks without loading the full list."""
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk

# Compose with itertools for pipeline processing
import itertools

def process_log_file(path):
    with open(path) as f:
        lines = (line.strip() for line in f)              # generator
        errors = (l for l in lines if "ERROR" in l)       # generator
        grouped = chunked(errors, 100)                     # generator
        for batch in grouped:
            insert_to_db(batch)                            # only now are lines read
```

`itertools` functions interviewers commonly ask about: `chain`, `islice`, `groupby`, `product`, `combinations`, `takewhile`, `dropwhile`. Know `itertools.chain.from_iterable` as the efficient way to flatten nested iterables.

---

## Decorators and Metaclasses

Decorators are functions that take a function and return a function (or class). The canonical pattern uses `functools.wraps` to preserve the wrapped function's metadata.

```python
import functools
import time

def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

@timed
def slow_query():
    time.sleep(0.1)
```

**Metaclasses** control class creation. `type` is the default metaclass — every class is an instance of `type`. Custom metaclasses are used for ORM field registration (Django models), API route discovery, and schema validation frameworks.

```python
class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Config(metaclass=SingletonMeta):
    pass

assert Config() is Config()   # True
```

Interview tip: if asked "when would you use a metaclass?", give a concrete example from a framework. Saying "almost never — a class decorator usually suffices" demonstrates good judgment.

---

## asyncio and Async/Await Patterns

`asyncio` uses a single-threaded event loop. Coroutines yield control at `await` points, allowing other coroutines to run. The key insight: `async def` does not make code concurrent by itself — you need `asyncio.gather` or `asyncio.create_task` to run coroutines concurrently.

```python
import asyncio
import httpx

async def fetch(client, url):
    response = await client.get(url)
    return response.status_code

async def fetch_all(urls):
    async with httpx.AsyncClient() as client:
        tasks = [fetch(client, url) for url in urls]
        results = await asyncio.gather(*tasks)   # concurrent, not sequential
    return results
```

**Common interview question:** "What's the difference between `asyncio.gather` and `asyncio.wait`?" — `gather` returns results in order and propagates exceptions by default. `wait` gives you more control (first-completed, first-exception policies) and returns sets of futures.

**asyncio pitfall:** Blocking calls (`time.sleep`, synchronous file I/O, `requests`) block the entire event loop. Use `await asyncio.sleep`, `aiofiles`, and `httpx`/`aiohttp` instead. For unavoidable blocking code, use `loop.run_in_executor`.

---

## Common Python Gotchas

These appear verbatim in interviews. Know them cold.

**Mutable default arguments:**

```python
# Wrong — the list is shared across all calls
def append_item(item, lst=[]):
    lst.append(item)
    return lst

append_item(1)   # [1]
append_item(2)   # [1, 2] — NOT [2]

# Correct
def append_item(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

**Late binding closures:**

```python
# Wrong — all lambdas capture the same `i` variable
fns = [lambda: i for i in range(5)]
fns[0]()   # 4, not 0

# Correct — bind the value at definition time
fns = [lambda i=i: i for i in range(5)]
fns[0]()   # 0
```

**`is` vs `==`:**
- `==` calls `__eq__` — checks value equality.
- `is` checks object identity (same memory address).
- CPython caches small integers (-5 to 256) and interned strings, so `is` can appear to work for values — this is an implementation detail, not a guarantee.

```python
a = 256; b = 256
a is b   # True (cached)

a = 257; b = 257
a is b   # False (not guaranteed)
```

---

## Performance Profiling

For interview questions about production performance issues, name specific tools:

- **`cProfile`** — deterministic profiling, low overhead, built-in. Use `python -m cProfile -s cumulative script.py`.
- **`py-spy`** — sampling profiler, attaches to a running process without code changes. Essential for production debugging. `py-spy top --pid PID`.
- **`line_profiler`** — line-by-line timing for a specific function (requires `@profile` decorator and `kernprof`).
- **`tracemalloc`** — memory allocation tracing, built into Python 3.4+.

---

## Framework Trade-offs at Scale

| | Flask | Django | FastAPI |
|---|---|---|---|
| Best for | Microservices, simple APIs | Full-stack web apps, admin-heavy | High-throughput async APIs |
| Async support | Limited (via extensions) | Django 4.x partial async | Native, built on Starlette |
| ORM | None built-in (use SQLAlchemy) | Django ORM (excellent) | None built-in (use SQLAlchemy/Tortoise) |
| Instagram, Disqus | — | Yes (Django) | — |
| Stripe, Twilio | Flask-style microservices | — | Increasingly FastAPI |

FastAPI's automatic request validation via Pydantic and auto-generated OpenAPI docs make it the default choice for new greenfield APIs. Django remains dominant for applications with complex admin requirements or tight ORM integration.

---

## CPython Internals: What Interviewers Want

You do not need deep CPython knowledge for most roles, but these points signal seniority:

- Python compiles to bytecode (`.pyc` files). The `dis` module disassembles bytecode — useful for understanding what's happening at the VM level.
- `LOAD_FAST` accesses local variables by index (fast); `LOAD_GLOBAL` requires a dict lookup (slower). This is why tight loops benefit from binding globals to locals.
- Python 3.11 introduced specializing adaptive interpreter — frequently executed bytecodes are replaced with faster specialized variants at runtime, yielding 25–60% speedup on many workloads.

```python
import dis
dis.dis(lambda x: x * 2 + 1)
# RESUME, LOAD_FAST, LOAD_CONST, BINARY_OP, LOAD_CONST, BINARY_OP, RETURN_VALUE
```

---

Mastering these topics — the GIL's actual scope, memory lifecycle, generator composition, async concurrency model, and the common gotchas — covers the material that distinguishes a fluent Python engineer from one who knows the syntax. The questions above are consistently reported from interview loops at Python-heavy backend shops.
