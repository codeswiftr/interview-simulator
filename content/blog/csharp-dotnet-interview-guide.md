---
title: "C# and .NET Interview Guide"
description: "Technical interview preparation for C# and .NET developer roles: the .NET runtime and CLR, async/await and Task-based concurrency, LINQ, dependency injection, ASP.NET Core, Entity Framework, and what enterprise, gaming, and Microsoft-stack companies expect from senior .NET engineers."
date: "2026-03-19"
category: "Technical Skills Guides"
---

C# and .NET occupy a unique position in the software industry. Once synonymous with Windows-only enterprise development, the platform has undergone a dramatic transformation over the past decade. The open-source, cross-platform .NET 6/7/8 unified runtime now powers everything from cloud-native microservices and real-time web APIs to mobile apps via .NET MAUI and 3D game logic in Unity. If you are preparing for a .NET engineering role, expect interviewers to probe your understanding of both the language's modern features and the broader runtime ecosystem.

## The .NET Ecosystem and CLR

The Common Language Runtime (CLR) is the managed execution environment that underlies all .NET code. It handles memory management through a generational garbage collector, just-in-time compilation of intermediate language (IL) to native machine code, and cross-language interoperability. Interviewers at enterprise shops will often ask you to explain the difference between value types (allocated on the stack or inline within containing objects) and reference types (heap-allocated, accessed via reference). Understanding boxing—the wrapping of a value type in a heap-allocated object—matters for performance-sensitive paths because it generates garbage.

The .NET 6+ unified platform collapsed the historical split between .NET Framework (Windows-only, legacy), .NET Core (cross-platform, modern), and Xamarin (mobile). Today a single SDK targets Linux, macOS, and Windows, with a predictable annual release cadence and long-term support versions. NuGet remains the package manager; knowing how to reason about dependency version conflicts, Central Package Management, and the difference between package references and assembly references signals maturity to senior-level interviewers.

## Core Language: Records, Structs, and Nullable Reference Types

C# 9 introduced records, a concise syntax for immutable, value-based data objects that implement structural equality by default. Records are particularly common in domain modeling and event-sourced systems. Know when to prefer a record over a struct: records are reference types (unless declared as `record struct`), so they avoid the copy-on-every-assignment cost of structs while still expressing immutability intent.

Nullable reference types, enabled via `<Nullable>enable</Nullable>` in the project file, bring compile-time null analysis to reference types. The compiler tracks nullability flow and warns when you dereference a potentially null value. Senior interviewers often ask about the null-forgiving operator (`!`), the null-coalescing assignment (`??=`), and how nullable annotations interact with existing codebases during incremental migration.

## Async/Await and Task-Based Concurrency

Async/await is one of C#'s most powerful features and one of the most common interview topics. Every `async` method compiles to a state machine; the `await` keyword yields control back to the caller until the awaited `Task<T>` or `ValueTask<T>` completes. `ValueTask<T>` was introduced to reduce allocations in hot paths where the result is frequently available synchronously—use it when profiling indicates the overhead of heap-allocated `Task` objects is significant.

Two subtleties trip up many candidates. First, `ConfigureAwait(false)` tells the runtime not to resume on the original synchronization context, which is critical in library code to avoid deadlocks in environments that have a single-threaded context (classic ASP.NET, WPF, WinForms). Second, calling `.Result` or `.Wait()` on a `Task` from a synchronous method while inside a single-threaded synchronization context is a classic deadlock pattern: the waiting thread blocks while holding the context, and the async continuation can never resume. Always await properly or use `Task.Run` to offload to the thread pool when bridging sync and async boundaries.

## LINQ and Deferred Execution

Language Integrated Query (LINQ) transforms how C# developers interact with collections, XML, and databases. The crucial distinction for database-facing code is between `IEnumerable<T>` and `IQueryable<T>`. `IEnumerable<T>` executes queries in-process using delegates; once you call `.AsEnumerable()` or materialize with `.ToList()`, all further filtering happens in memory. `IQueryable<T>` represents a query that has not yet been executed; its expression tree can be inspected and translated to SQL by providers such as Entity Framework Core.

Deferred execution means that most LINQ operators do not run until you iterate the sequence. This is efficient—you can compose complex pipelines without creating intermediate collections—but it can also cause subtle bugs when the underlying data source changes between query construction and enumeration, or when you inadvertently enumerate an expensive query multiple times. Interviewers frequently ask candidates to spot the difference between a method that returns `IEnumerable<T>` and one that returns a materialized `List<T>`, and to explain the performance implications of each.

## Dependency Injection in ASP.NET Core

ASP.NET Core ships with a built-in inversion of control container. Services are registered in `Program.cs` (or `Startup.cs` in older projects) using one of three lifetimes. Singleton services are created once for the lifetime of the application and shared across all requests—appropriate for stateless, thread-safe services like `HttpClient` factories or configuration wrappers. Scoped services are created once per HTTP request, making them ideal for database contexts and unit-of-work patterns. Transient services are created fresh every time they are requested; use them for lightweight, stateless operations.

A common interview question asks what happens when you inject a Scoped service into a Singleton—you get a "captive dependency" bug where the Scoped service outlives its intended scope, potentially causing stale state or threading issues. ASP.NET Core's built-in container will throw an `InvalidOperationException` at startup in development mode when it detects this, but it is worth understanding why the pattern is dangerous.

## ASP.NET Core: Minimal APIs and the Middleware Pipeline

Modern ASP.NET Core applications increasingly use the minimal API style introduced in .NET 6, where route handlers are defined as lambda expressions directly on the `WebApplication` builder rather than through controller classes. Minimal APIs reduce boilerplate and are well-suited to microservices, though controller-based MVC still dominates in larger enterprise codebases.

The middleware pipeline is a chain of request-handling components. Each middleware can short-circuit the pipeline (returning a response immediately) or call `next()` to pass control downstream. Order matters: authentication must come before authorization, exception-handling middleware should wrap everything else. Kestrel, the default cross-platform web server, is production-ready and high-performance; it sits behind reverse proxies like nginx or Azure Application Gateway in typical deployments. Health check endpoints, configured with `AddHealthChecks()` and `MapHealthChecks()`, are expected in any service running in Kubernetes or an Azure App Service environment.

## Entity Framework Core: Migrations, Change Tracking, and the N+1 Problem

Entity Framework Core is the standard ORM in the .NET ecosystem. Migrations provide a version-controlled history of schema changes; `dotnet ef migrations add` generates a migration class, and `dotnet ef database update` applies it. Interviewers at companies with large databases will ask about migration strategies for zero-downtime deployments and how to handle large table alterations.

EF Core's change tracker monitors every entity loaded into a `DbContext` and computes the diff when `SaveChanges()` is called. This is powerful but has performance costs: for read-only queries, appending `.AsNoTracking()` eliminates the change-tracking overhead and significantly reduces memory usage.

The three loading strategies each have appropriate use cases. Eager loading with `Include()` issues a JOIN and populates navigation properties in a single query. Lazy loading transparently fires an additional query when you first access a navigation property, which is convenient but dangerous in loops because it produces the N+1 query problem: one query to fetch N parents, then N separate queries to fetch each child collection. Explicit loading gives you fine-grained control by loading navigation properties on demand with `Entry().Collection().LoadAsync()`. Senior candidates are expected to recognize N+1 patterns in code review and know how to restructure queries to use `Include` or raw SQL projections instead.

## Unity and the Broader C# Job Market

Unity is one of the largest employers of C# developers globally. Game scripting in Unity uses a subset of C# with some runtime constraints—no `async/await` on the main thread without careful integration, limited garbage collector tuning options, and the `MonoBehaviour` component lifecycle as the primary architectural pattern. Candidates targeting game development roles should be comfortable with Unity's job system, the Burst compiler, and ECS (Entity Component System) as the modern performance-oriented alternative to the classic object hierarchy.

Beyond games, C# is the dominant language in enterprise line-of-business applications, financial systems, insurance platforms, healthcare software, and any organization that built on the Microsoft stack in the 2000s and 2010s. Microsoft itself, Accenture, Capgemini, Bloomberg, and countless ISVs hiring on Azure are perpetual sources of senior .NET demand. The language's strong type system, mature tooling in Visual Studio and Rider, and the breadth of the .NET library ecosystem make it a compelling choice for teams that prioritize long-term maintainability and developer productivity at scale.
