---
title: "iOS Senior Engineer Interview Guide"
description: "Advanced iOS interview preparation: Swift concurrency (async/await, actors), SwiftUI vs UIKit depth, memory management with ARC, architecture patterns (MVVM, TCA), and what Apple, top app companies, and iOS-focused startups expect from senior iOS engineers."
date: "2026-03-19"
category: "Technical Skills Guides"
---

Senior iOS interviews are a different class of challenge from mid-level ones. You are expected to reason deeply about language semantics, concurrency correctness, memory safety, and architectural trade-offs — not just write features. This guide covers the technical domains that consistently surface in senior-level loops at Apple, Airbnb, Lyft, Spotify, and high-quality iOS startups.

## Swift Language Depth

Interviewers at senior level will probe your understanding of the type system, not just your ability to write idiomatic Swift.

**Value vs. reference types** is foundational. `struct` and `enum` are value types copied on assignment; `class` is a reference type sharing identity. The practical implication: structs are safer in concurrent code because there is no shared mutable state. Know when a class is genuinely necessary — when you need identity semantics, subclassing, or `deinit` lifecycle hooks.

**Copy-on-write (COW)** is how Swift makes value types efficient. Standard library collections (`Array`, `Dictionary`, `Set`) defer actual copying until a mutation occurs, and only if the buffer is shared. Be ready to explain how to implement COW for a custom type using `isKnownUniquelyReferenced`.

**Property wrappers** encapsulate access patterns. `@Published`, `@AppStorage`, `@FetchRequest` are standard examples. Expect to be asked how to write a custom property wrapper and what `wrappedValue` vs. `projectedValue` is used for.

**Result builders** power SwiftUI's DSL. Understanding `buildBlock`, `buildOptional`, and `buildEither` is not required for daily work but signals genuine language depth in an interview.

**Opaque types** (`some Protocol`) preserve type identity for the compiler while hiding the concrete type from callers. The key distinction from `any Protocol` (existential): `some Protocol` erases the concrete type from the API surface but retains it internally, enabling protocol conformances that require `Self` or associated types. SwiftUI's `body: some View` is the canonical example.

## Swift Concurrency

The structured concurrency model introduced in Swift 5.5 is now a first-class interview topic at any company running iOS 15+.

**async/await** replaces completion handler pyramids with linear, readable call sites. Errors propagate with `throws`, and cancellation propagates automatically through the task tree. Know the difference between `Task` (unstructured, inherits actor context) and `Task.detached` (no actor inheritance, explicit scheduling).

**Actors** enforce data isolation at the language level. An actor serializes access to its mutable state — no locks required. All stored properties of an actor are actor-isolated by default. `@MainActor` is a global actor that pins execution to the main thread, replacing `DispatchQueue.main.async`. Understand actor reentrancy: suspension points (`await`) are opportunities for other tasks to run, which means actor-isolated state can change across an `await` within the same actor.

**Structured concurrency** gives you `async let` for parallel bindings and `TaskGroup` for dynamic concurrency. With `async let`, the child tasks are cancelled automatically if the parent task is cancelled or throws. `TaskGroup` gives you a handle to add tasks dynamically and iterate results as they complete.

**Transition from GCD**: the mental shift is from managing queues (resources) to expressing task relationships (structure). `DispatchQueue.global().async` does not propagate cancellation, actor context, or priority — Task does all three. In practice, GCD still appears in legacy code and third-party SDKs, so you need to bridge it using `withCheckedContinuation` or `withUnsafeContinuation`.

## Memory Management with ARC

ARC (Automatic Reference Counting) is deterministic, but still requires deliberate reference discipline.

**Strong, weak, unowned**: a `strong` reference increments the retain count. A `weak` reference does not retain and becomes `nil` when the object deallocates — always `Optional`. An `unowned` reference does not retain and assumes the referenced object outlives it; accessing an invalid `unowned` reference crashes at runtime. Use `weak` when the referenced object can outlive the referencing one (delegate pattern, closures capturing view controllers). Use `unowned` only when the lifetimes are tightly coupled and you are certain the reference remains valid.

**Retain cycles** are the most common source of memory leaks in iOS code. Two patterns dominate:

- **Delegate pattern**: a parent holds a strong reference to a child; the child holds a strong reference back to the parent via its delegate property. Fix: declare `weak var delegate`.
- **Closures capturing self**: a closure stored as a property on the object it captures creates a cycle. Fix: use `[weak self]` in the capture list, then guard against nil at the call site.

**Memory Graph Debugger** in Xcode is the primary tool for diagnosing leaks and unexpected retains. It shows a live object graph with reference edges. Combined with the Leaks instrument, it lets you trace which allocation is holding a reference and preventing deallocation.

## SwiftUI vs. UIKit

Both remain relevant. The senior question is not which one is better, but which one is appropriate and how they interoperate.

**UIKit** is appropriate when you need fine-grained control over layout (custom `UICollectionViewLayout`), complex animations, backward compatibility below iOS 16, or integration with third-party SDKs that hand you `UIView` subclasses directly. UIKit is also more predictable in performance-critical list scenarios with very large datasets.

**SwiftUI** is appropriate for new screens targeting iOS 16+, declarative state-driven UIs, and teams that value rapid iteration. Its diffing model is well-suited to simple to moderately complex data flows.

**Interop**: `UIViewRepresentable` wraps a `UIView` for use inside a SwiftUI hierarchy. `UIViewControllerRepresentable` wraps a `UIViewController`. `UIHostingController` goes the other direction — it hosts a SwiftUI `View` inside a UIKit hierarchy. Coordinators inside `UIViewRepresentable` handle delegate callbacks from UIKit back into SwiftUI state.

**SwiftUI state management**: `@State` is local view state. `@StateObject` owns the lifecycle of an `ObservableObject`. `@ObservedObject` observes an externally owned object. `@EnvironmentObject` injects a shared object through the view hierarchy without explicit passing. The `@Observable` macro (iOS 17+, Swift 5.9) replaces `ObservableObject` with finer-grained dependency tracking — only views reading specific properties re-render when those properties change.

## Architecture Patterns

**MVVM** is the default expectation. The ViewModel owns business logic and exposes state as `@Published` properties (or `@Observable`). The View binds to ViewModel state and forwards user actions. The key discipline: ViewModels must not import UIKit or SwiftUI — they are testable in isolation.

**The Composable Architecture (TCA)** has significant adoption in teams that prioritize testability and explicit state mutation. TCA uses a `State` struct, `Action` enum, `Reducer`, and `Store`. Every state change flows through the reducer — no side effects happen outside it. Effects (network calls, timers) return `Effect` values that the runtime executes. This makes the entire application state machine unit-testable without launching the app.

**Coordinator pattern** addresses SwiftUI's navigation limitations. Rather than embedding navigation logic in views, a Coordinator object owns the navigation stack and decides what to push, present, or dismiss. This separates routing from rendering and makes navigation testable.

## Performance Profiling

Instruments is non-negotiable at the senior level. Know the purpose and workflow for each instrument:

- **Time Profiler**: identifies where CPU time is spent. Look for unexpectedly long work on the main thread.
- **Allocations**: tracks heap allocations over time. Useful for diagnosing memory growth that is not a leak (objects are reachable but should have been released).
- **Leaks**: detects cycles and dangling references at runtime.
- **GPU Driver / Metal System Trace**: diagnoses render pipeline bottlenecks in SwiftUI or Metal workloads.
- **Main Thread Checker**: runtime tool that flags UIKit and AppKit API calls made from background threads. Enable it in the scheme's diagnostics settings.

## Who Hires Senior iOS Engineers and What They Expect

**Apple** expects deep knowledge of frameworks at the abstraction layer below what most developers use — knowing how `RunLoop`, responder chain, and layout passes interact matters there. Expect system design questions about framework architecture.

**Airbnb, Lyft, Spotify, Reddit** operate large codebases with hundreds of engineers. Senior candidates must demonstrate modular architecture knowledge — how to split a monolithic app into independently buildable frameworks, how to manage shared dependencies, and how to reason about build time at scale. TCA and custom coordinator patterns come up frequently.

**Banking and fintech apps** weight security knowledge: certificate pinning, secure enclave usage, keychain access control, and jailbreak detection signals. Architecture compliance with frameworks like PCI-DSS affects technical decisions directly.

**iOS-focused startups** want speed and ownership. You will be asked to own the entire client stack. Demonstrate that you can make architectural trade-offs quickly, ship features without perfect conditions, and instrument production apps to catch issues before users report them.

The differentiator across all of these: senior iOS engineers explain the *why* behind every technical decision, not just the *what*.
