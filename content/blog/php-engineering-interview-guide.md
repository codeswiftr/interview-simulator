---
title: "PHP Engineering Interview Guide"
description: "Technical interview preparation for PHP roles: modern PHP 8.x features, Laravel and Symfony frameworks, performance at scale, and what companies like Etsy, Slack, and WordPress.com look for in PHP engineers."
date: "2026-03-19"
category: "Technical Skills Guides"
---

PHP has a reputation problem it does not deserve. When engineers hear "PHP role," many picture 2008-era spaghetti code and `register_globals`. The reality in 2026 is a mature, typed, performant language running a significant fraction of the internet's infrastructure. WordPress alone powers roughly 43% of all websites. Etsy runs PHP. Slack was originally built on PHP before its backend rewrite. Facebook created Hack — a statically-typed PHP dialect — rather than abandon the language. If you are interviewing for a PHP engineering role, you are entering a serious production environment, and interviewers will expect you to treat it that way.

## The Language You Actually Need to Know

Modern PHP is not the PHP you learned to avoid. PHP 8.x introduced changes that close the gap with other typed, object-oriented languages.

**Typed properties and union types.** Since PHP 7.4, class properties can be typed. PHP 8.0 added union types (`int|string`) and PHP 8.2 added `true`, `false`, and `null` as standalone types. Interviewers will expect you to write typed code by default, not as an afterthought.

**Named arguments.** Calling `array_slice(array: $items, offset: 0, length: 5)` is clearer than relying on argument position. This matters in codebases with long function signatures.

**Match expressions.** `match` is a stricter, expression-based replacement for `switch`. It uses strict comparison, does not fall through, and must be exhaustive or have a default. If you write a `switch` in an interview, you will likely be asked why you did not use `match`.

**Nullsafe operator.** `$user?->profile?->avatar` short-circuits to `null` instead of throwing an error. Clean, readable, and a direct signal that you know the modern API.

**Fibers.** PHP 8.1 introduced Fibers for cooperative multitasking — the low-level primitive underlying async frameworks like ReactPHP and Amp. You do not need to implement Fibers in an interview, but understanding what they enable (non-blocking I/O without separate threads) is expected at the senior level.

**Readonly properties and enums.** PHP 8.1 also added `readonly` properties (immutable after initialization) and native `enum` types with backed values. These replace a lot of class constant patterns and are now idiomatic.

## Framework Depth: Laravel and Symfony

Most PHP roles involve one of two frameworks. Know both conceptually; be deep on whichever the company uses.

**Laravel** is the dominant choice for product companies. Key areas:

- **Eloquent ORM**: Active Record pattern. Know how it handles relationships (hasMany, belongsToMany, polymorphic), and critically, understand the N+1 problem and how `with()` eager loading solves it. Interviewers test this frequently.
- **Queues and jobs**: Laravel's queue system (backed by Redis, SQS, or database) is central to async processing. Know how to dispatch jobs, handle failures, set retry limits, and use Horizon for queue monitoring in Redis environments.
- **Service container and dependency injection**: Laravel's container resolves type-hinted dependencies automatically. Understanding how to bind interfaces to implementations and write testable code via DI is table stakes for senior roles.
- **Artisan CLI**: Custom commands, scheduled tasks via `schedule:run`, and database seeding. You should be comfortable writing Artisan commands.
- **Blade templates**: Less tested for backend roles but knowing the basics (components, directives, layout inheritance) rounds out your picture.

**Symfony** is more common in enterprise and agency contexts. It is also the foundation Laravel sits on — several Laravel components (HttpFoundation, Console, Routing) are Symfony components. Symfony emphasizes explicit configuration over convention and is more verbose but more predictable at scale. Know Doctrine ORM (Data Mapper pattern, distinct from Eloquent's Active Record), the DI container configuration in YAML/PHP, and Symfony's event dispatcher.

## Performance at Scale

PHP's traditional model is share-nothing: each request spawns a PHP-FPM worker, handles the request, and exits. This is simple and safe but has overhead.

**OPcache** eliminates that overhead by caching compiled bytecode. It must be enabled in production — if it is not, you are recompiling every file on every request. Interviewers at companies running high-traffic PHP will ask about this.

**Redis** handles session storage and application caching. Know how to configure Redis as Laravel's cache and session driver, and understand cache invalidation strategies (TTL, event-driven invalidation, cache tags).

**Connection pooling** is a known limitation of the FPM model. Each worker holds its own database connection, so connection limits scale with worker count rather than request concurrency. This is a common interview topic for senior roles — know the problem, know that PgBouncer or ProxySQL mitigates it.

**RoadRunner** is the modern alternative to PHP-FPM. It keeps the PHP application in memory between requests, eliminating bootstrap overhead. This changes the programming model — you need to think about state isolation between requests — but the performance gains are substantial. Knowing RoadRunner exists and understanding its tradeoffs signals you follow the ecosystem.

## Testing

PHP testing has two primary tools. **PHPUnit** is the standard — you need to know it. **Pest** is a modern alternative with a more expressive API, closely associated with the Laravel ecosystem, and increasingly common in new projects.

For database testing, the standard pattern in Laravel is using database transactions that roll back after each test, keeping your test database clean without truncating tables. Feature tests hit the full HTTP stack; unit tests isolate a single class. Know when to use each. Interviewers will ask about mocking (Mockery or PHPUnit's built-in mocks) and how you test jobs and queued events.

## What Interviewers Actually Test

Beyond language features, senior PHP interviews focus on:

- **OOP design**: interfaces vs. abstract classes, when to use traits, composition over inheritance. PHP supports all of these — use them correctly.
- **SOLID principles**: dependency inversion is the most commonly probed. If your code has `new SomeConcreteClass()` buried in a method, expect follow-up questions.
- **Authentication and authorization**: Laravel Sanctum vs. Passport, gate and policy patterns for authorization, role-based access control.
- **System design in PHP context**: designing a multi-tenant SaaS on Laravel (tenant isolation strategies: separate databases vs. shared database with tenant_id, middleware for tenant context), or a content delivery architecture for a WordPress site under load (page caching with Varnish or Nginx, CDN integration, database read replicas).

## Senior-Level Topics

At the senior level, add these to your preparation:

- **PSR standards**: PSR-4 (autoloading), PSR-7 (HTTP message interfaces), PSR-12 (coding style). If you are reviewing a pull request, you reference PSR-12. If you are designing a library, you implement PSR-7.
- **Composer autoloading**: understand how Composer's classmap and PSR-4 autoloading work. Know the difference between `require` and `require-dev`.
- **Hexagonal architecture**: separating domain logic from infrastructure concerns (framework, database, HTTP) is a growing pattern in PHP. Laravel does not enforce it, but senior engineers often implement it in complex domains.
- **Event sourcing**: storing state as a sequence of events rather than current state. The `spatie/laravel-event-sourcing` package is the common entry point. Know the concept; be honest about your depth.

## How to Prepare

The most effective preparation for a PHP interview is a complete, production-quality project. Build a Laravel application with authentication, background jobs, caching, and a full test suite. Deploy it somewhere. Operate it. The problems you encounter in that process — connection timeouts, queue failures, cache invalidation bugs — are the problems interviewers ask about.

Read Matt Stauffer's *Laravel: Up & Running* — it is the most thorough practical resource on Laravel. For deeper PHP, *PHP 8 Objects, Patterns, and Practice* by Matt Zandstra covers OOP and design patterns in depth.

Contributing to PHP open source projects — Laravel packages, Symfony bundles, or standalone libraries — is the highest-signal preparation. It shows you can write PHP that other engineers review and ship.

PHP roles attract engineers who write clean, testable, production-ready code in a language that has earned its place at scale. Show up prepared to treat the language with the seriousness it deserves.
