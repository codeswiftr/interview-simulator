---
title: "FastAPI Advanced Interview Guide: Async Python, Dependency Injection, and Production APIs"
description: "Master FastAPI interviews with deep coverage of asyncio, dependency injection, Pydantic v2, middleware, and production deployment patterns."
date: "2026-03-20"
category: "Technical Skills"
---

# FastAPI Advanced Interview Guide: Async Python, Dependency Injection, and Production APIs

FastAPI has become the de facto standard for Python API development, and senior engineering roles at companies building data-intensive or high-throughput services increasingly expect deep familiarity with it. Interviewers probe beyond basic route definitions — they want to know how you reason about async concurrency, structure dependency graphs, and ship APIs that survive production.

## The Async Model: Event Loop and Concurrency

FastAPI runs on top of Starlette, which in turn runs on ASGI (Asynchronous Server Gateway Interface). The runtime is a single-threaded event loop powered by `asyncio`. Understanding what this means in practice is essential.

When you define a route with `async def`, your handler runs on the event loop. I/O-bound operations (database queries, HTTP calls) should `await` coroutines so the loop can schedule other work while waiting. CPU-bound operations block the loop — for those, you must offload to a thread pool via `asyncio.run_in_executor` or use `def` (sync) routes, which FastAPI automatically dispatches to a thread pool.

```python
@app.get("/data")
async def get_data(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))  # yields control during I/O
    return result.scalars().all()
```

A common interview gotcha: calling a sync blocking function (like `time.sleep` or a synchronous ORM call) inside an `async def` route. This stalls the event loop and eliminates all concurrency benefits.

## Dependency Injection System

FastAPI's DI system is one of its most powerful and underappreciated features. Dependencies are declared as function parameters with `Depends()`. The framework builds a dependency graph and resolves it per request.

```python
async def get_current_user(token: str = Header(...), db: AsyncSession = Depends(get_db)):
    user = await db.get(User, decode_token(token))
    if not user:
        raise HTTPException(status_code=401)
    return user

@app.get("/me")
async def me(user: User = Depends(get_current_user)):
    return user
```

Dependencies can be classes (useful for stateful initialization), can have their own dependencies (enabling deep graphs), and can use `yield` to implement teardown logic — making them ideal for database session management.

For interviews, be ready to explain how `yield`-based dependencies enable resource cleanup and how you'd structure a multi-layer dependency graph for auth, tenant resolution, and feature flags.

## Pydantic v2 Integration

FastAPI uses Pydantic for request/response validation. Pydantic v2 is significantly faster (written in Rust via `pydantic-core`) and introduces `model_config`, `field_validator` with `mode='before'/'after'`, and `model_serializer`.

```python
from pydantic import BaseModel, field_validator, model_config

class OrderRequest(BaseModel):
    model_config = model_config(str_strip_whitespace=True)
    
    quantity: int
    price: float
    
    @field_validator('quantity')
    @classmethod
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('quantity must be positive')
        return v
```

Interviewers may ask about the difference between `response_model` and return type annotations, how to exclude fields from responses, or how to handle discriminated unions for polymorphic payloads.

## Middleware Patterns

Middleware in FastAPI (inherited from Starlette) wraps every request. Common uses: logging, request ID injection, CORS, rate limiting.

```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

For complex middleware, prefer Starlette's `BaseHTTPMiddleware` class. Be aware that middleware exceptions don't trigger FastAPI exception handlers — a nuance that trips up many engineers.

## Background Tasks

FastAPI's `BackgroundTask` runs after the response is sent, within the same process. Use it for fire-and-forget work like sending emails or writing audit logs.

```python
@app.post("/register")
async def register(user: UserCreate, background_tasks: BackgroundTasks):
    new_user = await create_user(user)
    background_tasks.add_task(send_welcome_email, new_user.email)
    return new_user
```

For heavier workloads, interviewers expect you to recommend Celery or ARQ (asyncio-native) instead.

## Testing with httpx and pytest-asyncio

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_order():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/orders", json={"quantity": 5, "price": 10.0})
    assert response.status_code == 201
```

Use `pytest-asyncio` with `asyncio_mode = "auto"` in `pyproject.toml` to avoid decorating every test. Override dependencies using `app.dependency_overrides` to inject test doubles.

## Production Deployment

Run FastAPI with `uvicorn` behind `gunicorn` using `UvicornWorker`:

```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Worker count: `(2 * CPU cores) + 1` is a common starting point for I/O-heavy workloads. For containerized deployments, a single uvicorn worker per container is often preferred — let the orchestrator (Kubernetes, ECS) handle scaling.

## Sample Interview Q&A

**Q: When would you use `def` instead of `async def` for a route?**
A: When the route calls blocking synchronous code (legacy SDKs, sync ORMs). FastAPI dispatches sync routes to a thread pool, avoiding event loop starvation.

**Q: How do you handle database transactions spanning multiple dependencies?**
A: Share a session via a `yield` dependency and commit/rollback in the dependency's teardown — not in the route handler. This keeps transaction management centralized.

**Q: What's the difference between `status_code` in `@app.post()` and raising `HTTPException`?**
A: The decorator sets the success status code; `HTTPException` is for error responses. You can also use custom exception handlers via `app.exception_handler()` for application-level errors.

FastAPI interviews reward engineers who understand the async runtime deeply and can reason about dependency design. The framework's magic disappears quickly when production traffic arrives — knowing the underlying machinery is what separates senior candidates.
