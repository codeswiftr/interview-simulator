---
title: "Python Advanced Interview Guide: Internals, Async, and Senior-Level Patterns"
description: "Advanced Python interview preparation — CPython internals, GIL mechanics, asyncio and event loops, metaclasses, descriptors, memory model, type system, and Python-specific system design questions."
date: "2026-03-20"
category: "Programming Languages"
---

# Python Advanced Interview Guide: Internals, Async, and Senior-Level Patterns

Junior Python interviews test syntax. Senior Python interviews test whether you understand what Python is doing underneath. This guide covers the topics that separate engineers who've read the language spec from those who've just used Python as a scripting tool.

## The GIL (Global Interpreter Lock)

The GIL is CPython's global mutex that prevents multiple native threads from executing Python bytecode simultaneously. One thread holds the GIL; others wait.

Why it exists: CPython's reference counting for memory management is not thread-safe. The GIL is the pragmatic fix that makes object lifecycle management safe without fine-grained locking.

Consequences: CPU-bound multithreaded Python programs don't benefit from multiple cores — threads contend for the GIL. I/O-bound programs work fine because threads release the GIL while waiting for I/O.

The fix for CPU-bound parallelism: `multiprocessing` (separate processes, each with their own GIL and Python interpreter), or use C extensions (NumPy, etc.) that release the GIL during computation.

Python 3.13 introduced an experimental "free-threaded" mode (PEP 703) that can run without the GIL. Still not production default as of 3.13 but the direction Python is heading.

## Generators and Coroutines

Generators are functions that `yield` values. The function's state is preserved between yields. `next()` resumes execution until the next yield.

The key insight: generators don't compute all values upfront. They're lazy. `range(1_000_000_000)` doesn't allocate a billion integers — it yields one at a time.

Generator expressions: `(x*2 for x in range(100))` is a generator; `[x*2 for x in range(100)]` is a list. Use generators when you don't need random access and want memory efficiency.

Coroutines: built on generators. `async def` creates a coroutine function. Calling it returns a coroutine object. `await` suspends execution until the awaited coroutine completes (similar to yield but for async operations).

The `send()` method lets you pass values into a generator — this is the foundation of coroutines. Understanding this mechanical detail helps you reason about what `await` actually does.

## asyncio and the Event Loop

asyncio is single-threaded concurrency. The event loop runs one coroutine at a time, but switches between them at `await` points. While one coroutine awaits I/O (network call, disk read), the event loop runs another coroutine.

This is cooperative multitasking: coroutines must yield control explicitly at `await`. A CPU-bound coroutine that never awaits blocks the entire event loop.

Key asyncio concepts:
- `asyncio.gather()`: run multiple coroutines concurrently, wait for all
- `asyncio.create_task()`: schedule a coroutine to run concurrently without waiting
- `asyncio.wait_for()`: add timeout to a coroutine
- `asyncio.Queue()`: async-safe queue for producer-consumer patterns

Common mistake: calling blocking code (requests.get, time.sleep) inside async functions. This blocks the event loop. Use `asyncio.sleep()` instead of `time.sleep()`, and `aiohttp` instead of `requests`.

For CPU-bound work with asyncio: `loop.run_in_executor(None, cpu_bound_function)` runs the function in a thread pool executor, keeping the event loop free.

## Descriptors

Descriptors are objects that define how attribute access works on a class. If a class attribute has a `__get__`, `__set__`, or `__delete__` method, it's a descriptor.

This is how `@property` works internally. `property` is a descriptor class that stores getter and setter functions.

```python
class property:
    def __get__(self, obj, objtype=None):
        if obj is None: return self
        return self.fget(obj)
    def __set__(self, obj, value):
        self.fset(obj, value)
```

When you access `instance.attr`, Python's attribute lookup checks the class's `__dict__` for descriptors first. If found and it's a data descriptor (has `__set__`), the descriptor takes precedence over the instance's `__dict__`.

Understanding descriptors explains: how `@property`, `@staticmethod`, `@classmethod` work, how ORMs like SQLAlchemy define column attributes, and how `__slots__` works.

## Metaclasses

A metaclass is a class whose instances are classes. `type` is the default metaclass — it's the class that creates all classes.

```python
class Meta(type):
    def __new__(mcs, name, bases, namespace):
        # Called when creating a new class that uses Meta as its metaclass
        return super().__new__(mcs, name, bases, namespace)

class MyClass(metaclass=Meta):
    pass
```

When are metaclasses useful? Creating class registries (automatically register subclasses), enforcing class invariants (every subclass must implement method X), modifying class attributes at creation time (ORMs, API framework models).

The rule: if you think you need a metaclass, you probably need `__init_subclass__` or a class decorator instead. Metaclasses are powerful but complex — most use cases are better served by simpler tools.

## Memory Model and Reference Counting

CPython uses reference counting. Each object has a `ob_refcnt` field. When it hits zero, the object is deallocated. The `sys.getrefcount()` function returns an object's reference count (adding 1 for the function call argument itself).

Reference cycles: A → B → A creates a cycle where reference counts never hit zero. CPython's cyclic garbage collector (`gc` module) detects and breaks cycles. Run with `gc.collect()` or automatically in the background.

`id()` returns the memory address of an object. Important caveat: a deleted object's address can be immediately reused, so two objects at the same `id()` may not be the same object (just using the same memory at different times).

## Type System (Python 3.9+)

Modern Python uses type hints extensively. Key concepts for senior engineers:

`TypeVar`: Generic type parameters. `T = TypeVar('T')`. Used in generic functions and classes.

`Protocol`: Structural subtyping (duck typing made explicit). A class satisfies a Protocol if it has the right methods — no inheritance required. Better than `ABC` for type checking without coupling.

`TypeAlias`: Explicit type alias for complex types. Clearer than bare assignment.

`ParamSpec` and `Concatenate`: For typing decorators that preserve argument types.

The `typing` module (3.5+), `from __future__ import annotations` (lazy evaluation of annotations), and `dataclasses` are all deeply connected to Python's type system evolution.

## Python-Specific Interview Questions

"Explain Python's memory management" → reference counting + cyclic GC, mention when you'd force a collection.

"What's the difference between `__str__` and `__repr__`?" → `__repr__` for unambiguous machine-readable representation (should ideally `eval()` to recreate the object), `__str__` for human-readable. `str(x)` calls `__str__`; `repr(x)` calls `__repr__`; in collections (lists, dicts), elements are shown via `__repr__`.

"What happens when you use `is` vs `==`?" → `is` compares identity (same object in memory, same `id()`), `==` compares equality (calls `__eq__`). Small integers (-5 to 256) and interned strings are cached — `a = 1; b = 1; a is b` may be `True` due to interning, but this is an implementation detail, not a language guarantee.

