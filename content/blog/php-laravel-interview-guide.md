---
title: "PHP Laravel Interview Guide: Eloquent ORM, Queue System, and Modern PHP Practices"
description: "A comprehensive PHP Laravel interview guide for senior engineers — covering Eloquent internals, queue architecture, service container, and the modern PHP practices that distinguish expert Laravel developers."
date: "2026-03-20"
category: "Programming Languages"
---

# PHP Laravel Interview Guide: Eloquent ORM, Queue System, and Modern PHP Practices

PHP has a reputation problem that doesn't reflect the current state of the ecosystem. Modern PHP (8.0+) with Laravel is a genuinely capable stack used by serious engineering organizations — Shopify's early codebase, Facebook's HHVM investment, and Laravel's dominance in the SMB and SaaS market demonstrate that PHP expertise is not a consolation prize. For engineers interviewing at Laravel shops, understanding the framework's depth is what separates senior from mid-level candidates.

This guide covers the areas where senior Laravel interviews actually probe depth.

## The Service Container: Laravel's Core Abstraction

The service container is Laravel's IoC container and the foundation on which everything else is built. Most candidates know it as "the thing that auto-resolves dependencies." Senior candidates understand the binding types and their implications.

**Binding types:**

```php
// Basic bind: creates a new instance every time
$app->bind(PaymentGateway::class, StripeGateway::class);

// Singleton: same instance every time
$app->singleton(CacheStore::class, RedisCacheStore::class);

// Instance: bind a specific already-created object
$app->instance('config', $configArray);

// Contextual binding: different implementations per context
$app->when(CheckoutController::class)
    ->needs(PaymentGateway::class)
    ->give(StripeGateway::class);
```

**Interview signal:** Explaining contextual binding demonstrates production-level Laravel knowledge. It solves the problem of needing different implementations of the same interface in different contexts — critical for multi-payment-provider systems.

**Service Providers:**

Service providers are the primary mechanism for registering bindings. The `register()` method runs first (bindings only), then `boot()` runs after all providers are registered (safe to call other services here). The distinction matters — calling a service in `register()` that hasn't been registered yet throws an error.

## Eloquent ORM: Performance and Behavior Depth

Eloquent is powerful but hides significant behavior that interviewers probe:

**The N+1 problem and eager loading:**

Same fundamental issue as JPA's N+1 — accessing a relationship in a loop triggers a query per model instance.

```php
// N+1: loads each user's posts in a separate query
$users = User::all();
foreach ($users as $user) {
    echo $user->posts->count(); // N queries
}

// Eager loading: one additional query
$users = User::with('posts')->get();
```

**Lazy eager loading (for conditional loading):**

```php
$users = User::all();
if ($includePostCounts) {
    $users->load('posts');
}
```

**Interview depth question:** What's the difference between `with()`, `has()`, and `whereHas()`?

- `with('posts')`: eager loads posts (fetches them; result includes post data)
- `has('posts')`: filters to users who have at least one post (existence check, no post data)
- `whereHas('posts', fn($q) => $q->where('published', true))`: filters users based on conditions on related model

Confusing these is a common source of incorrect query behavior.

**Eloquent scopes:**

Local scopes are reusable query constraints:

```php
// Definition
public function scopePublished(Builder $query): Builder {
    return $query->where('published_at', '<=', now());
}

// Usage
Post::published()->latest()->get();
```

Global scopes apply automatically (SoftDeletes is the canonical example). Interviewers ask about disabling global scopes: `User::withoutGlobalScope(SoftDeletingScope::class)`.

**Mass assignment protection:**

`$fillable` whitelist vs. `$guarded` blacklist. The difference in approach: `$fillable` is explicit and safer (fails closed — new fields require explicit addition). `$guarded = []` disables protection entirely — acceptable in some contexts (seeded data) but a code smell in user-facing code.

## Queue System Architecture

Laravel's queue system is used seriously at scale and is a frequent interview topic for backend roles.

**Job lifecycle:**

1. Job class is serialized and pushed to the queue driver (Redis, SQS, database)
2. Queue worker process polls the queue
3. Job is deserialized and `handle()` is called
4. On success: job is deleted from queue
5. On failure: job is released back (with delay) or moved to the failed_jobs table

**Horizon for Redis:**

Laravel Horizon provides a supervisor for Redis queues with auto-scaling, metrics, and failed job management. Interview question: "How does Horizon auto-scale workers?"

It monitors queue throughput and adjusts worker processes per queue. Configuration in `horizon.php` defines queue-to-supervisor mappings with `minProcesses` and `maxProcesses`.

**Job failures and retries:**

```php
class ProcessPayment implements ShouldQueue {
    public $tries = 3;
    public $backoff = [10, 60, 300]; // exponential-ish backoff in seconds
    
    public function failed(Throwable $e): void {
        // notification, cleanup
    }
}
```

**Senior-level question:** How do you prevent the same job from being processed twice (idempotency)?

Common approaches:
- Database lock: check-and-set in the `handle()` method with a unique constraint
- `WithoutOverlapping` middleware (built-in): prevents concurrent execution of jobs with the same unique key
- Idempotency keys stored in Redis/cache with TTL

## Modern PHP Practices

Senior PHP engineers are expected to write modern PHP. Interviewers notice:

**Type declarations (PHP 8.0+):**

```php
// PHP 7.x style
public function processOrder($orderId, $amount) { ... }

// Modern PHP
public function processOrder(int $orderId, Money $amount): OrderResult { ... }
```

Union types (`int|string`), nullables (`?string`), and return type declarations are expected in 2026 codebases.

**Named arguments and attributes:**

```php
// Named arguments (PHP 8.0)
$result = processPayment(amount: 1000, currency: 'USD', retry: true);

// Attributes (PHP 8.0) — replacing docblock annotations
#[Route('/api/users', methods: ['GET'])]
public function listUsers(): Response { ... }
```

**Enums (PHP 8.1):**

```php
enum OrderStatus: string {
    case Pending = 'pending';
    case Processing = 'processing';
    case Completed = 'completed';
}
```

Using string enums instead of class constants with magic strings is a modern PHP best practice. Laravel Eloquent casts support enums directly.

**Fibers (PHP 8.1) and async patterns:**

Fibers enable cooperative multitasking. While PHP isn't traditionally async, tools like ReactPHP and Swoole use Fibers for event loop-based concurrency. For senior roles at companies using these stacks, knowing the difference between thread-based concurrency (traditional PHP-FPM) and event loop concurrency (Swoole) matters.

## Testing Expectations

Senior Laravel engineers are expected to write:
- Feature tests using `RefreshDatabase` trait
- HTTP tests with `$this->getJson()`, `assertStatus()`, `assertJsonStructure()`
- Mocking with Facades: `Queue::fake()`, `Mail::fake()`, `Event::fake()`
- Factory-based test data: model factories with states

The interview question "how would you test a job that sends an email?" has a clean Laravel answer:

```php
Queue::fake();
Mail::fake();
// ... trigger the action
Queue::assertPushed(ProcessOrderJob::class);
// dispatch the job manually and assert mail
Mail::assertSent(OrderConfirmation::class);
```

Laravel's testing tooling is excellent, and interviewers at Laravel-heavy companies expect fluency with it.
