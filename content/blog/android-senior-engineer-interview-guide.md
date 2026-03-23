---
title: "Android Senior Engineer Interview Guide"
description: "Advanced Android interview preparation: Kotlin coroutines and Flow, Jetpack Compose, Android architecture components (ViewModel, Room, Navigation), performance optimization, and what Google, top app companies, and Android-focused teams expect from senior engineers."
date: "2026-03-19"
category: "Technical Skills Guides"
---

Senior Android engineer interviews have converged on a consistent set of expectations: deep Kotlin proficiency, fluency with Jetpack libraries, hands-on experience with Compose, and the architectural judgment to build apps that survive real-world scale and device fragmentation. This guide covers the technical areas that separate senior candidates from mid-level ones.

## Kotlin Depth

Kotlin is not optional at the senior level — interviewers expect you to reason about its features, not just use them.

**Coroutines** are the foundation of all async work in modern Android. Be prepared to explain:

- `suspend` functions and how the compiler transforms them into state machines
- `CoroutineScope` and structured concurrency — why `GlobalScope` is an antipattern
- `Dispatchers.Main`, `Dispatchers.IO`, and `Dispatchers.Default` — when each is appropriate and what happens if you block the main thread
- `launch` vs `async`/`await` — fire-and-forget versus concurrent work with a result
- `SupervisorJob` and how it changes cancellation propagation compared to a regular `Job`

**Flow** is where most senior-level questions get interesting. Know the distinction between cold and hot streams at a mechanical level:

- Cold streams (`flow { }`) start on each collection — suitable for database queries, network calls
- Hot streams (`StateFlow`, `SharedFlow`) exist independently of collectors — suitable for UI state and event buses
- `StateFlow` holds the latest value and replays it to new collectors; `SharedFlow` is configurable (replay cache, buffer, overflow strategy)
- Operators: `map`, `filter`, `flatMapLatest` (cancels prior emission on new upstream value), `combine`, `zip`
- Lifecycle-safe collection with `repeatOnLifecycle` and why `lifecycleScope.launch { collect {} }` alone is not safe

**Sealed classes and when expressions** come up in architecture discussions. Sealed classes model exhaustive state (Loading, Success, Error) and force callers to handle all cases when used in `when` expressions. Know how sealed interfaces differ from sealed classes and when each is appropriate.

## Android Architecture Components

**ViewModel** is the entry point for most architecture conversations. Key points: it survives configuration changes (rotation, theme switch) because it is scoped to the `ViewModelStore`, not the `Activity`. It does not survive process death — that requires `SavedStateHandle`. Expect questions about how ViewModel interacts with `onCleared()` and how you scope coroutines to it via `viewModelScope`.

**Room** is the standard SQLite ORM. Senior candidates should know:

- `@Entity`, `@Dao`, `@Database` and how Room generates implementations at compile time
- Returning `Flow<List<T>>` from DAO queries — Room re-emits on table changes, enabling reactive UI
- Migrations (`Migration` class) and destructive migration trade-offs in production
- `@Transaction` for multi-step operations that must be atomic

**Navigation component** manages fragment and Compose destinations through a graph defined in XML or code. Know safe args (type-safe argument passing), deep links, and how to handle back stack behavior for bottom navigation tabs (saving state per tab using `saveState`/`restoreState`).

**WorkManager** handles deferrable, guaranteed background tasks. It persists work across app restarts and device reboots. Know the difference between `OneTimeWorkRequest` and `PeriodicWorkRequest`, chaining with `then()`, and how constraints (network, charging) are applied.

## Jetpack Compose

Compose requires a different mental model than View-based UI. Interviewers probe whether you understand the runtime, not just the API.

**Recomposition** is triggered when state that a composable reads changes. To reason about performance:

- Only composables that read changed state recompose — Compose skips unaffected subtrees
- Use `remember` to survive recomposition within a composable's lifetime; use `rememberSaveable` to survive activity recreation (persists to `Bundle`)
- `derivedStateOf` creates a new state that only recomputes when its inputs change — useful for derived values like "is the list empty"
- Unstable types (classes without stable equals) force recomposition even when values haven't changed; annotate with `@Stable` or use data classes

**Side effects** are operations that affect state outside the composition:

- `LaunchedEffect(key)` — launches a coroutine scoped to composition; restarts when key changes, cancels on leave
- `SideEffect` — runs after every successful recomposition, synchronously; use for non-Compose state synchronization
- `DisposableEffect(key)` — for cleanup logic (registering/unregistering listeners); `onDispose` block runs on leave or key change

**State hoisting** is the pattern of moving state up to the caller so composables remain stateless and reusable. The pattern: stateless composable receives state and a lambda to request state changes; the caller owns the `MutableState`. This is not optional at the senior level — it is the standard.

## Android-Specific Challenges

The Activity and Fragment lifecycle is legitimately complex. Know the full sequence (`onCreate` through `onDestroy`), when `onSaveInstanceState` is called versus `onStop`, and why `onCreate` vs `onStart` matters for observer registration. Fragments add their own lifecycle layered on top.

**Background execution limits** introduced in Android 8.0 (Oreo) and tightened in subsequent releases mean that implicit broadcast receivers and background services are heavily restricted. Know which scenarios WorkManager, foreground services, and `AlarmManager` each address.

**Battery optimization** (Doze mode, App Standby buckets) affects scheduled work and network access. WorkManager handles Doze automatically; raw `AlarmManager` does not. `setExactAndAllowWhileIdle` is the last resort for time-critical exact alarms.

## Architecture Patterns

**MVI (Model-View-Intent)** has become the dominant pattern for Compose-based apps. The ViewModel exposes a single immutable `UiState` via `StateFlow`, processes `Intent` events from the UI, and produces `SideEffect`s (one-time events like navigation or toasts) via `SharedFlow`. This unidirectional data flow makes state predictable and testable.

**Clean Architecture** organizes code into layers: domain (use cases, entities — pure Kotlin, no Android dependencies), data (repositories, data sources, Room DAOs, Retrofit services), and presentation (ViewModel, UI). Dependency inversion means domain layer does not depend on data or presentation.

**Hilt** (built on Dagger) is the standard DI framework. Know `@HiltAndroidApp`, `@AndroidEntryPoint`, component hierarchy (`SingletonComponent` → `ActivityComponent` → `ViewModelComponent`), and `@Provides` vs `@Binds`.

## Performance

The Android Profiler in Android Studio provides CPU (method traces, call charts), Memory (heap dumps, allocation tracking), and Network (request timing) views. Use CPU profiling to find janked frames; the frame rendering track shows which frames exceeded 16ms.

**Systrace** (via `perfetto`) gives a system-wide view of thread execution, binder calls, and rendering pipeline. Useful for diagnosing startup regressions and jank that the in-app profiler misses.

**Baseline Profiles** precompile critical code paths (startup, key user journeys) into optimized ahead-of-time form, reducing app startup time by up to 30-40%. You define them in a `BaselineProfileGenerator` using the Macrobenchmark library and ship the generated profile file with the release APK.

## Who Hires Senior Android Engineers and What They Expect

**Google** expects deep platform knowledge — understanding the rendering pipeline, how the ART runtime handles object allocation, and binder IPC. Expect system design questions with Android constraints.

**Spotify** focuses on large-scale feature development, modularization (hundreds of modules), and performance at scale (complex audio session management, offline sync).

**Lyft and Square/Cash App** emphasize financial-grade reliability, security (keystore, biometric authentication, certificate pinning), and multi-team coordination in large codebases.

**Fintech companies broadly** add compliance requirements: certificate pinning, root detection, secure storage with Android Keystore, and often custom obfuscation beyond ProGuard/R8 defaults.

Across all of these, the consistent expectation is that you can defend your architectural choices, reason about trade-offs, and have direct experience shipping production Android apps at scale — not just knowledge of the APIs.
