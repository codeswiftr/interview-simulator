---
title: "iOS Swift Advanced Interview Guide: Concurrency, Memory Management, and Architecture"
description: "Advanced iOS engineering interview preparation covering Swift Concurrency, ARC, memory management, MVVM vs TCA, UIKit vs SwiftUI tradeoffs, and senior-level Q&A."
date: "2026-03-20"
category: "Technical Skills"
---

# iOS Swift Advanced Interview Guide: Concurrency, Memory Management, and Architecture

iOS engineering interviews at senior and staff levels test how deeply you understand the Swift runtime and Apple's frameworks — not whether you can look up a UITableView delegate method. Companies like Apple, Spotify, and Lyft expect candidates to reason about memory graphs, concurrency hazards, and architectural tradeoffs with precision.

## Swift Concurrency: async/await, Actors, and Structured Concurrency

Swift Concurrency (introduced in Swift 5.5) replaced the callback pyramid with a cooperative threading model. The key concept is that async functions are not threads — they are tasks that may suspend and resume on different threads without blocking.

**Structured concurrency** means tasks have a parent-child hierarchy. When a parent task is cancelled, all children are automatically cancelled. TaskGroup enforces this by requiring all child tasks to complete before the group returns. This eliminates the classic bug pattern of escaping callbacks that outlive their logical scope.

**Actors** protect mutable state from data races by serializing access. Any method or property on an actor requires await from outside the actor's context. The runtime ensures that only one task accesses the actor at a time. The critical interview point: actors do not guarantee ordering — concurrent callers will be serialized, but the order is unspecified.

**@MainActor** is a global actor that guarantees code runs on the main thread. Annotating a ViewModel class with @MainActor means all its properties and methods are main-thread-safe without explicit DispatchQueue.main calls. This is the preferred modern pattern over the old `DispatchQueue.main.async` scattered throughout ViewModels.

**Sendable** is a marker protocol that tells the compiler a type is safe to pass across concurrency boundaries. Structs with value semantics are Sendable automatically. For classes, you must explicitly conform and guarantee thread safety yourself. The compiler enforces Sendable requirements at async boundaries, turning runtime race conditions into compile-time errors.

## ARC and Memory Management

Automatic Reference Counting deallocates objects when their reference count reaches zero. The interview domain covers two questions: how retain cycles form, and when to use weak vs. unowned.

A retain cycle occurs when two objects hold strong references to each other. The classic iOS example: a view controller holds a closure (strongly captured in a property), and the closure captures self strongly. The solution is a capture list: `[weak self]`.

**weak** references are optional and become nil when the referenced object is deallocated. Use weak when the referenced object's lifetime is independent and shorter-lived than the referencing object.

**unowned** references are non-optional and crash if accessed after the referenced object is deallocated. Use unowned when you are certain the referenced object will outlive the reference — for example, a closure inside an object that captures its own parent when the parent owns the closure.

Senior interview question: "Is using [weak self] always safe?" No. If self is nil when the closure executes and you do `guard let self = self else { return }`, you silently skip important logic. Consider whether the callback should execute at all when self is gone, or whether the architecture should prevent that situation.

Memory debugging tools: Xcode's Memory Graph Debugger identifies retain cycles visually. The Memory Report in Instruments shows heap allocations over time. The `leaks` command-line tool integrates with CI pipelines.

## iOS App Architecture: MVVM and TCA

**MVVM** is the dominant pattern for UIKit and SwiftUI. The ViewModel holds business logic and state, exposes published properties or output streams, and never imports UIKit. The View subscribes to ViewModel outputs. Benefits: testable ViewModels without UI infrastructure; clear data flow.

The common MVVM failure mode is a "massive ViewModel" — all logic pushed into ViewModels that grow as large as the original ViewControllers. The solution is coordinator patterns for navigation and service/repository layers for data access.

**The Composable Architecture (TCA)** from Point-Free takes a different approach: unidirectional data flow with explicit State, Action, Environment, and Reducer types. Every state change is a pure function of the previous state and an action. Benefits: exhaustive testability (every state transition is testable without mocks), powerful debugging (time-travel debug tools), composable feature modules.

TCA's costs: significant boilerplate for small features, a learning curve for the Reducer/Effect system, and ergonomic friction when mixing with UIKit. It's well-suited for teams with strong functional programming backgrounds and applications with complex state dependencies.

Interview framing: don't recommend TCA without acknowledging tradeoffs. The best answer explains what problems each architecture solves and what size/complexity of application justifies each approach.

## UIKit vs SwiftUI Tradeoffs

SwiftUI is declarative, composable, and backed by Apple's future investment. UIKit is imperative, mature, and battle-tested across every iOS version since 2.0.

SwiftUI limitations that matter for senior roles: the declarative model makes fine-grained animation control harder; some UIKit components lack direct SwiftUI equivalents (though UIViewRepresentable bridges them); and debugging SwiftUI's opaque view tree is harder than UIKit's explicit view hierarchy.

UIKit limitations: verbose boilerplate for simple layouts; Auto Layout constraint conflicts are runtime errors rather than compile-time; data binding requires manual implementation or Combine integration.

The practical interview answer for a greenfield project (iOS 16+): start with SwiftUI, use UIViewRepresentable for UIKit-only components, and keep the ViewModels architecture-agnostic so the view layer can evolve.

## Key Senior Interview Questions

**Q: What is actor reentrancy and why is it important?**
An actor can be reentered at suspension points. If an actor method suspends (awaits an async operation), another call to the actor can execute before the first resumes. State that was valid before the suspension may be stale after. Always re-check invariants after any await inside an actor.

**Q: Explain the difference between a strong delegate and a weak delegate.**
Delegates are almost always declared weak to avoid retain cycles between a view/controller and its delegate (often its owner). Strong delegates are appropriate when the delegate should outlive the delegating object — rare but valid in some coordinator patterns.

**Q: How would you design an offline-first iOS app?**
Local SQLite (Core Data or GRDB) as the source of truth; background sync with conflict resolution strategy; optimistic UI updates with rollback on sync failure; network reachability monitoring for sync triggers.

The Swift language evolution proposals (swift-evolution on GitHub) are the best preparation source for understanding *why* Swift concurrency was designed the way it was.

---
