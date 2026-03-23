---
title: "Swift Language Deep Dive Interview Guide"
description: "Advanced Swift interview preparation: protocols and protocol-oriented programming, value semantics, generics with associated types, Swift concurrency (async/await, actors), property wrappers, and what Apple, top iOS teams, and Swift server-side companies expect from senior Swift engineers."
date: "2026-03-19"
category: "Technical Skills Guides"
---

Senior Swift interviews are not about syntax recall. They are about demonstrating that you understand the language's design philosophy — why it works the way it does, the trade-offs baked in, and how to apply them correctly under real production constraints. This guide covers the six areas that consistently separate passing candidates from those who get filtered out.

## Protocol-Oriented Programming

Swift's own standard library is built on protocols, not classes. `Collection`, `Equatable`, `Hashable`, `Comparable` — these are all protocols. That choice was intentional and reflects Swift's core design principle: prefer composition over inheritance.

**Key concepts to demonstrate:**

- Protocols as the primary abstraction tool, not base classes. A `Drawable` protocol with a `draw()` requirement is more flexible than an abstract `Shape` base class.
- Protocol extensions give protocols default implementations. You can add behavior to a protocol without requiring conforming types to implement it, and without a shared base class.
- Protocol composition (`TypeA & TypeB`) lets you express precise constraints without deep inheritance hierarchies.
- The difference from OOP inheritance: protocols do not carry state, do not have initializers by default, and multiple conformances are additive rather than overriding.

A common interview question: *why does Swift use `Equatable` as a protocol rather than a method on a base class?* The answer touches on value types — structs cannot inherit from classes, so the only way to express shared behavior across structs and classes uniformly is through protocols.

## Value Semantics

This is one of the areas where Swift diverges most sharply from Objective-C, and interviewers at Apple and senior iOS shops push on it hard.

**Struct vs. class:**

- Structs are value types — copied on assignment. Classes are reference types — shared on assignment.
- The default for custom types in Swift should be struct unless you have a specific reason to use a class.
- Reasons to use a class: identity matters (two references to the same object should be detectable), you need inheritance from a non-protocol base, or you are interoperating with Objective-C APIs.

**Copy-on-write (COW):** Swift's standard library types (`Array`, `Dictionary`, `String`) use COW internally. The storage is shared until one of the copies is mutated, at which point a unique copy is made. When implementing custom value types that wrap heap storage, you replicate this pattern using `isKnownUniquelyReferenced`.

**The `mutating` keyword:** Methods on a struct that modify `self` must be marked `mutating`. This is a compile-time enforcement of value semantics — the compiler prevents mutation of a `let`-bound struct entirely.

## Generics and Associated Types

Generics are where Swift's type system becomes expressive enough to replace many runtime patterns with compile-time guarantees.

**Generic functions and types:** `func max<T: Comparable>(_ a: T, _ b: T) -> T` is the canonical example. The `where` clause adds constraints: `where T: Equatable, T: Hashable`.

**Protocols with Associated Types (PATs):** When a protocol declares `associatedtype Element`, it becomes a generic constraint rather than a concrete type. `Collection` is the best real-world example — it has an associated `Element` type and an `Index` type. You cannot use a PAT directly as a variable type without qualification.

**Opaque types (`some Protocol`):** Introduced in Swift 5.1. A function returning `some Collection` tells the compiler there is exactly one concrete type being returned, known at compile time, but not exposed to the caller. This enables return-type optimization and is how SwiftUI's `body` property works.

**Existential types (`any Protocol`):** Swift 5.7 introduced `any` as an explicit marker for existential types. `any Collection` boxes the concrete type at runtime. It is more flexible (the concrete type can vary) but slower and unable to use associated types directly without constraints. Knowing when to use `some` vs. `any` vs. a generic parameter is a litmus test for senior candidates.

## Swift Concurrency

The async/await model replaced completion handlers and most GCD patterns for new code from Swift 5.5 onward.

**Core model:**

- `async` functions suspend without blocking a thread. `await` marks the suspension point.
- Actors provide data isolation. An `actor` type serializes access to its mutable state, preventing data races at compile time rather than at runtime. `MainActor` is the most common example — annotating a class or method with `@MainActor` guarantees it runs on the main thread.
- `async let` allows parallel child tasks with structured concurrency. `TaskGroup` handles dynamic numbers of parallel tasks.

**The GCD transition:** GCD is not wrong, but it requires discipline to avoid data races. Swift concurrency makes races a compiler error for actor-isolated state. The practical interview question is: *when would you still use GCD or `DispatchQueue` in new code?* Reasonable answers include: interoperating with existing C APIs, work items with specific QoS priorities outside Swift's cooperative thread pool, or legacy code paths not yet migrated.

## Property Wrappers and Result Builders

These are compiler directives, not runtime magic.

**Property wrappers:** A type annotated with `@propertyWrapper` must expose a `wrappedValue`. The compiler rewrites property access to go through `wrappedValue`. Common examples: `@Published` (Combine), `@State` and `@Binding` (SwiftUI), `@AppStorage` (UserDefaults-backed). Writing a custom property wrapper — for example, one that clamps a numeric value to a range — is a standard interview exercise.

**Result builders:** The `@resultBuilder` attribute transforms a sequence of expressions in a closure into a single value. SwiftUI's `@ViewBuilder` is the most visible example. This is how SwiftUI's DSL syntax works — the compiler transforms stacked view expressions into a single `TupleView`.

Both features follow the same principle: push complexity into the type system and the compiler rather than into runtime behavior.

## Memory Management

ARC is automatic, but not invisible. Knowing where it can fail is required knowledge.

**Strong, weak, unowned:**

- `strong` (default): increments retain count.
- `weak`: does not retain; becomes `nil` if the referenced object is deallocated. Must be `Optional`.
- `unowned`: does not retain; assumes the referenced object will outlive the reference. Crashes if accessed after deallocation.

**Retain cycles:** The classic case is a closure capturing `self` strongly, where `self` holds a reference to the closure. The fix is a capture list: `[weak self]` or `[unowned self]`. The choice between them: use `weak` when the referenced object might be nil at execution time; use `unowned` when you can guarantee it will not be.

Interviewers test this with delegate patterns (delegates should almost always be `weak`), timer callbacks, and notification observers.

## Who Tests Swift Depth and Why

**Apple (highest bar):** Apple's iOS and macOS interviews assume you have read the Swift Evolution proposals and can discuss language decisions. The Swift language team is internal, and Apple engineers are expected to understand the rationale behind `some` vs. `any`, why actors were designed the way they were, and how the optimizer behaves with value types. Vague answers about "best practices" do not pass here.

**Senior iOS shops:** At companies with mature iOS teams — fintech, health tech, large-scale consumer apps — you will be asked to debug retain cycle scenarios, explain why a particular design uses generics vs. existentials, and demonstrate working knowledge of structured concurrency. These teams have production bugs caused by incorrect concurrency assumptions and interview specifically to filter for them.

**Server-side Swift (Vapor, Hummingbird):** Swift on the server has gained real adoption, particularly at companies already invested in the Apple ecosystem. Server-side interviews emphasize async/await and actors more heavily than UIKit-specific patterns, and they test Swift's concurrency model against alternatives like Go's goroutines or Rust's async model. If you are applying to a backend Swift role, know how `TaskGroup` handles cancellation and how actor reentrancy works under load.

The common thread across all three: Swift mastery is demonstrated by understanding trade-offs, not by reciting syntax.
