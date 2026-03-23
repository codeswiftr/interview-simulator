---
title: "Kotlin Language Interview Guide"
description: "Technical interview preparation for Kotlin developer roles: Kotlin vs. Java, coroutines and structured concurrency, extension functions, sealed classes, Kotlin multiplatform, and what Android teams, backend Kotlin shops, and JetBrains-ecosystem companies expect."
date: "2026-03-19"
category: "Technical Skills Guides"
---

# Kotlin Language Interview Guide

Kotlin has become the primary language for Android development (officially preferred by Google since 2019) and is gaining ground in backend services as a more expressive alternative to Java. Its combination of null safety, concise syntax, functional programming features, and full JVM interoperability makes it a pragmatic language that solves Java's most persistent pain points. Companies hiring Kotlin engineers range from Android-heavy organizations (major app companies, game studios, fintech) to backend teams using Spring Boot with Kotlin (Zalando, JetBrains' own infrastructure).

## What Kotlin Adds Over Java

Understanding the improvements Kotlin makes over Java is the foundation of Kotlin interview preparation:

**Null safety**: Kotlin distinguishes nullable (`String?`) from non-nullable (`String`) types at the compile level. Calling `.length` on a `String?` is a compilation error — you must handle the nullable case explicitly with `?.` (safe call), `!!` (non-null assertion, throws NPE if null), or the Elvis operator `?: defaultValue`. This eliminates a large class of NullPointerExceptions.

**Data classes**: `data class User(val name: String, val age: Int)` generates `equals()`, `hashCode()`, `toString()`, `copy()`, and destructuring component functions automatically. Equivalent to a Java class with 50+ lines of boilerplate.

**Extension functions**: Add methods to existing classes without inheritance. `fun String.isPalindrome(): Boolean = this == this.reversed()` adds `isPalindrome()` to every String. Extension functions are resolved statically (not virtual dispatch), making them a tool for organizing code without modifying existing classes.

**Sealed classes and when expressions**: Sealed classes define a closed hierarchy — all subclasses are defined in the same file. When used with `when` (Kotlin's switch equivalent), the compiler enforces exhaustiveness: `when (shape) { is Circle -> ... is Square -> ... }` generates a compile warning if a subclass is added but the `when` isn't updated.

**Smart casts**: After an `is` check, Kotlin automatically casts: `if (x is String) { x.length }` — no manual cast needed. Reduces boilerplate and eliminates `ClassCastException` risk.

## Kotlin Coroutines

Coroutines are Kotlin's approach to asynchronous programming — arguably its most important feature for modern development:

**Suspend functions**: `suspend fun fetchUser(id: Int): User` can be paused and resumed without blocking a thread. The suspend modifier marks functions that can participate in coroutine suspension.

**Coroutine builders**: `launch { }` starts a coroutine without returning a result (fire and forget). `async { }` starts a coroutine that returns a `Deferred<T>`. `runBlocking { }` blocks the current thread until the coroutine completes (use in tests and main functions, not in production coroutines).

**Structured concurrency**: Coroutines have a scope. A `CoroutineScope` (or more specifically, a `Job`) controls the lifecycle. Child coroutines fail together with their parent; cancellation propagates down the hierarchy. `viewModelScope` in Android automatically cancels coroutines when the ViewModel is cleared — eliminating a class of memory leaks.

**Dispatchers**: `Dispatchers.Main` for UI thread operations, `Dispatchers.IO` for I/O operations (network, file), `Dispatchers.Default` for CPU-intensive computation. Switching dispatchers with `withContext(Dispatchers.IO) { }` is the idiomatic way to move work off the main thread.

**Flow**: Kotlin's reactive streams implementation. A `Flow<T>` emits multiple values asynchronously. Cold flows (only emit when collected), hot flows (`StateFlow` — always has a value, like `LiveData`; `SharedFlow` — broadcasts to multiple collectors). The `flow { emit(...) }` builder, operators (`map`, `filter`, `collect`), and terminal operators are expected knowledge for Android interviews.

## Android-Specific Kotlin Patterns

**ViewModel and coroutines**: `viewModelScope.launch` is the idiomatic way to start coroutines in a ViewModel. StateFlow/SharedFlow replaces LiveData in modern architecture.

**Companion objects**: Kotlin's equivalent of Java's static methods and constants. `companion object { fun create(): MyClass = ... }` accessed as `MyClass.create()`. Constants in companion objects are accessible as `MyClass.CONSTANT`.

**Delegation**: `by lazy { }` for lazy initialization of properties. `by viewModels()` for ViewModel initialization in Android. `by Delegates.observable { }` for property change listeners. The `by` keyword invokes Kotlin's delegation pattern.

## Backend Kotlin with Spring Boot

Kotlin with Spring Boot is a growing combination. Kotlin-specific Spring features: constructor injection works cleanly with data classes, `@ConfigurationProperties` binds to data classes, coroutine support in Spring WebFlux. Common interview topic: Kotlin's `open` keyword (classes are final by default in Kotlin; Spring proxying requires `open` or the all-open compiler plugin).

## Who Hires Kotlin Engineers

**Android-first companies**: Any company with a significant Android app — Square/Cash App, Duolingo, Monzo, Nubank, N26. Android roles universally expect Kotlin; Java-only Android engineers are at a disadvantage.

**JetBrains and Kotlin ecosystem**: JetBrains (Kotlin creator) and companies building Kotlin Multiplatform projects (share code between Android and iOS with Kotlin Multiplatform Mobile — KMM).

**JVM backend migration**: Companies migrating from Java to Kotlin for backend services — Zalando, some Pivotal/VMware Spring shops.

Kotlin interviews heavily emphasize coroutines for Android roles and null safety for all roles. Engineers who can articulate why specific Kotlin features eliminate classes of bugs or reduce boilerplate stand out from candidates who just know the syntax.
