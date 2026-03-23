---
title: "Kotlin Multiplatform Interview Guide: KMP Architecture and Cross-Platform Patterns"
description: "Kotlin Multiplatform interview prep — shared business logic, expect/actual mechanism, integration with SwiftUI and Jetpack Compose, testing shared code, and when KMP is the right choice."
date: "2026-03-20"
category: "Mobile"
---

# Kotlin Multiplatform Interview Guide: KMP Architecture and Cross-Platform Patterns

Kotlin Multiplatform has crossed from experimental curiosity to production-grade technology in the past two years. Major companies including Netflix, Cash App, and Touchlab's clients have shipped KMP-based apps to millions of users. If you're interviewing for a senior mobile role at a company using KMP — or pitching KMP as a solution — this guide covers the architectural questions, pattern nuances, and comparison points that come up most often.

## KMP Architecture Fundamentals

The core idea of KMP is straightforward: write shared Kotlin code that compiles to the target platform's native format. The shared module compiles to JVM bytecode for Android and to a native binary (via LLVM) for iOS.

**Project structure** in a typical KMP app:

```
shared/
  commonMain/       ← pure Kotlin, platform-agnostic
  androidMain/      ← Android-specific implementations
  iosMain/          ← iOS-specific implementations
androidApp/         ← Android UI (Jetpack Compose or XML)
iosApp/             ← iOS UI (SwiftUI or UIKit)
```

The shared module contains business logic: data models, use cases, repositories, and networking. Platform apps contain only the UI layer and platform-specific integrations (push notifications, biometrics, etc.).

Interviewers often ask: "What belongs in `commonMain` versus platform-specific source sets?" The clean answer: anything without a platform API dependency. Networking, serialization, business rules, and ViewModels (optionally) live in `commonMain`. File I/O, camera, notifications, and UI stay in platform modules.

## The expect/actual Mechanism

This is the most-tested KMP concept. When you need platform-specific behavior in shared code, you declare an `expect` declaration in `commonMain` and provide `actual` implementations in platform source sets.

```kotlin
// commonMain
expect class PlatformLogger() {
    fun log(message: String)
}

// androidMain
actual class PlatformLogger actual constructor() {
    actual fun log(message: String) = android.util.Log.d("App", message)
}

// iosMain
actual class PlatformLogger actual constructor() {
    actual fun log(message: String) = println(message)
}
```

Common expect/actual use cases: date/time handling (before kotlinx-datetime), random number generation, UUID generation, cryptography, and platform-specific storage paths.

A follow-up interview question: "What's the limitation of expect/actual compared to dependency injection?" The key limitation is that expect/actual is compile-time and structural — you can't swap implementations at runtime, and it creates tight coupling to the KMP compilation model. DI (using Koin or manual injection) is more flexible for testing.

## Key Libraries

**Ktor** — The standard for HTTP networking in KMP. Uses coroutines throughout and supports multiple engines per platform (OkHttp on Android, Darwin on iOS). Interview question: "How do you handle authentication token refresh in Ktor?" Expect a discussion of interceptors or a custom HttpClient plugin.

**SQLDelight** — Cross-platform SQL database with type-safe generated APIs. Compiles `.sq` files into Kotlin code. For iOS, it uses SQLite under the hood. Key interview topic: "How does SQLDelight differ from Room?" SQLDelight is multiplatform and generates from `.sq` SQL files; Room is Android-only and annotation-driven.

**kotlinx.coroutines** — Fully multiplatform. The main KMP-specific nuance is the `Dispatchers.Main` dispatcher on iOS requires `kotlinx-coroutines-core` with the native main thread runloop integration.

**kotlinx.serialization** — Preferred over Gson/Moshi in KMP since it's pure Kotlin and works on all platforms.

## Sharing ViewModels

This is a design question with no single right answer — expect to discuss tradeoffs:

**Shared ViewModel approach** — using KMP ViewModels (via `lifecycle-viewmodel-compose` or a custom abstraction) means the same state management logic runs on both platforms. The challenge is that iOS doesn't have native lifecycle management, so you need a wrapper (often a Swift class that holds the KMP ViewModel and manages its scope).

**Shared use cases only** — a more conservative approach where only business logic and data layer are shared. Each platform has its own ViewModel. Simpler, more idiomatic on each platform, at the cost of duplicating some logic.

Most production teams land somewhere between these: shared data layer plus shared domain logic, with platform-native presentation logic.

## Testing Shared Code

Testing in `commonMain` uses `kotlin.test` — a multiplatform-aware test API. Tests can run on JVM (fast) and on native (slower, but catches platform-specific issues).

```kotlin
// In commonTest
class UserRepositoryTest {
    @Test
    fun `fetchUser returns cached data when offline`() {
        // Pure Kotlin test — runs on all targets
    }
}
```

Mocking is trickier in KMP since Mockito is JVM-only. Common solutions: MockK (has KMP support), manual fakes, or interface-based design that makes testing straightforward without mocks.

## KMP vs React Native vs Flutter

This comparison comes up in architecture and system design rounds:

| Dimension | KMP | React Native | Flutter |
|-----------|-----|--------------|---------|
| UI sharing | No (by design) | Yes (JS) | Yes (Dart/Skia) |
| Performance | Native | Near-native | Near-native |
| iOS/Android feel | Native (platform UI) | Mostly native | Custom renderer |
| Language | Kotlin | JavaScript/TypeScript | Dart |
| Best for | Sharing logic, native UI | Web team extending to mobile | Full cross-platform |

The key KMP value proposition: you share the hard parts (business logic, networking, data) while keeping fully native UIs. This makes it compelling for teams with strong platform expertise who don't want to rewrite UI but do want to eliminate duplication in the data layer.

## Common KMP Interview Questions

- "How does the expect/actual mechanism work, and when would you use it versus constructor injection?"
- "What's the difference between `commonMain`, `androidMain`, and `iosMain`? What belongs in each?"
- "How would you share a ViewModel in a KMP app while keeping the iOS side idiomatic Swift?"
- "How do you test code in `commonMain`? What are the constraints compared to JVM-only testing?"
- "A team is choosing between Flutter and KMP for a new app. Walk me through how you'd frame the decision."

For the last question, structure your answer around team composition, existing codebase, UI requirements, and long-term maintenance. There's no universally correct answer — the interviewer is evaluating your reasoning, not your conclusion.
