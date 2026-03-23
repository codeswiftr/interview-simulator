---
title: "Python Backend Advanced Interview: Django, FastAPI, and Production Systems"
description: "Master senior Python backend interviews with deep coverage of Django ORM vs SQLAlchemy, async vs sync frameworks, advanced Python internals (descriptors, metaclasses, generators), performance patterns, and real Q&A."
date: "2026-03-20"
category: "Technical Skills"
---

# Python Backend Advanced Interview: Django, FastAPI, and Production Systems

Python backend interviews at senior levels test more than framework familiarity. They probe your understanding of how Python's object model works, how to identify and fix performance bottlenecks, and how to make defensible framework choices. This guide covers the topics that appear most frequently in senior Python backend interviews at companies from mid-stage startups to FAANG.

## Framework Comparison: Django vs. FastAPI in Production

The framework choice question comes up in almost every senior Python interview. Have a structured answer.

**Django's strengths:** batteries-included (ORM, admin, auth, migrations, forms), strong conventions that reduce decision fatigue in large teams, mature ecosystem with well-understood deployment patterns. Django's ORM is excellent for most relational database patterns and handles migrations cleanly. The Django admin is genuinely useful for internal tooling. Where Django struggles: async support is bolted on (though Django 4.1+ has async ORM support, it is not idiomatic), and the framework's conventions can feel constraining for API-only services with unusual data access patterns.

**FastAPI's strengths:** built on top of Starlette and Pydantic, fully async-first, automatic OpenAPI documentation generation from type hints, fast request handling due to async I/O. FastAPI is excellent for: API gateways, services that make many outbound HTTP calls concurrently, ML model serving, and teams that want strong type enforcement at the API boundary. Where FastAPI struggles: no built-in ORM or migration system (you integrate SQLAlchemy and Alembic separately), no admin, and less opinionated structure requires teams to establish their own conventions.

**The interview answer:** "I choose Django for full-featured web applications with complex data models and team scaling requirements. I choose FastAPI for API services where async I/O matters, where I'm building on top of existing infrastructure, or where the team has strong async Python experience."

**Django ORM vs. SQLAlchemy:** Django's ORM is tightly coupled to its migration system and model definition. SQLAlchemy's Core and ORM layers are more powerful and flexible but require more explicit configuration. SQLAlchemy's session model (`Session`, `scoped_session`) maps more directly to database transaction semantics. For complex query patterns, SQLAlchemy's `select()` statement composition is often cleaner than Django's queryset chaining.

## Advanced Python Internals

### Descriptors

A descriptor is any object that implements `__get__`, `__set__`, or `__delete__`. This is the mechanism behind Python properties, class methods, and static methods. Django's ORM model fields are descriptors: when you access `instance.name`, the descriptor's `__get__` method returns the value from the instance's `__dict__` (or issues a database query for deferred fields).

Interview value: understanding descriptors lets you build domain-specific validation patterns without metaclass complexity, and explains why attribute access on ORM instances can have side effects.

### Metaclasses

A metaclass is the class of a class. `type` is the default metaclass. When Python processes a `class` statement, it calls the metaclass to construct the class object. Django's `Model` base class uses a metaclass (`ModelBase`) to inspect the class body, collect field definitions, build the `_meta` object, and register the model with the app registry.

In interviews, metaclasses come up as: "how does Django know what fields your model has?" The metaclass intercepts class creation and collects all `Field` instances from the class namespace. You rarely need to write metaclasses directly—class decorators or `__init_subclass__` handle most modern use cases more cleanly.

### `__slots__` and Memory Optimization

By default, Python instances store attributes in a `__dict__`. For classes that create many instances, this per-instance dictionary has significant memory overhead. Defining `__slots__` replaces the instance dictionary with a fixed-size C struct, reducing per-instance memory by 30-50% for small objects.

When does this matter in backend systems? In data processing pipelines where you instantiate millions of small objects (event records, data points), the memory savings can meaningfully affect whether a service fits in a container's memory budget.

### Generators as Coroutines

Python generators (`yield`) predate async/await and underpin the `asyncio` event loop implementation. A generator function pauses at each `yield` and can receive values via `send()`. Coroutines (`async def`) are syntactic sugar built on this mechanism. Understanding this explains why you cannot `await` inside a regular generator (unless it's an `async def` generator), and why mixing sync and async code requires explicit bridging.

## Performance Patterns in Production Python

**Caching:** Use `functools.lru_cache` for pure in-process caching of expensive computations. For distributed caching, Redis with the `redis-py` asyncio client is standard. The critical pattern: cache invalidation on write (write-through cache) rather than relying on TTL expiration for correctness-sensitive data.

**Database connection pooling:** SQLAlchemy's `create_engine` includes a built-in connection pool. For async applications using `asyncpg` or `aiosqlite`, set pool size to slightly above your expected concurrency—too large wastes database connections, too small creates queuing under load. A common misconfiguration: setting pool size based on CPU count when the service is I/O-bound; async services can handle far more concurrent connections than threads.

**Async I/O patterns:** `asyncio.gather()` runs coroutines concurrently within a single event loop thread. For CPU-bound work, use `loop.run_in_executor()` with a `ProcessPoolExecutor` to avoid blocking the event loop. The common mistake: using `ThreadPoolExecutor` for CPU-bound work inside asyncio, which only parallelizes if the GIL is released (true for C extensions like NumPy, not for pure Python).

## Sample Q&A

**Q: How does Python's GIL affect your backend service design?**
The GIL serializes Python bytecode execution across threads, meaning CPU-bound work does not parallelize with `threading`. For I/O-bound work (database calls, HTTP requests), threads are effective because the GIL is released during I/O system calls. The practical implication: for CPU-bound Python services, use `multiprocessing` or deploy multiple processes behind a load balancer rather than relying on threading.

**Q: How would you diagnose a memory leak in a long-running FastAPI service?**
Start with `tracemalloc` to capture memory snapshots at intervals and compare to find growing allocations. Use `objgraph` to identify object types accumulating in memory. Common culprits: circular references preventing garbage collection (Python's cyclic GC handles most of these, but C extension objects may not participate), caches without size limits, and accumulated background task state.

---
