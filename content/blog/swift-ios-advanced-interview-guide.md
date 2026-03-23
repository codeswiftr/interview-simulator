---
title: "Advanced Swift and iOS Interview Guide: Concurrency, SwiftUI, and Architecture"
description: "Senior iOS engineer interview preparation — Swift concurrency (async/await, actors), SwiftUI vs UIKit trade-offs, app architecture patterns (MVVM, TCA), memory management, and system design for mobile."
date: "2026-03-20"
category: "Mobile Development"
---

# Advanced Swift and iOS Interview Guide: Concurrency, SwiftUI, and Architecture

Advanced iOS interviews test whether you understand the Swift language and Apple platform deeply enough to architect reliable, performant applications. Senior iOS engineers face questions about concurrency models, memory management, SwiftUI internals, and architectural patterns. This guide covers the depth required for senior and staff mobile engineering roles.

## Swift Concurrency: async/await and Actors

Swift 5.5+ introduced structured concurrency as a first-class language feature. Understanding it deeply separates senior iOS engineers from those who've used it without knowing why.

**async/await**: An async function can be suspended at `await` points, allowing other work to run on the current thread's cooperative thread pool. Unlike completion handlers, errors propagate normally and the call stack is preserved for debugging.

```swift
func fetchUser(id: String) async throws -> User {
    let url = URL(string: "https://api.example.com/users/\(id)")!
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(User.self, from: data)
}

// Concurrent execution
async let user = fetchUser(id: "123")
async let posts = fetchPosts(userId: "123")
let (u, p) = try await (user, posts) // Both execute concurrently
```

**Actors**: Reference types that protect their mutable state from concurrent access. Only one piece of code can access an actor's state at a time — accesses from outside the actor are automatically async.

```swift
actor UserCache {
    private var cache: [String: User] = [:]
    
    func user(for id: String) -> User? {
        cache[id]
    }
    
    func store(_ user: User, for id: String) {
        cache[id] = user
    }
}
```

**MainActor**: A global actor that ensures code runs on the main thread. Use `@MainActor` to mark UI-updating code. Removes the need for `DispatchQueue.main.async` calls.

**Sendable**: A type that can be safely shared across concurrency domains. Value types and actors are automatically Sendable. Non-Sendable types cannot be passed across actor boundaries — enforced by the compiler in strict concurrency mode.

## Memory Management: ARC and Common Pitfalls

iOS uses Automatic Reference Counting (ARC) — the compiler inserts retain/release calls at compile time, not a runtime garbage collector. Understanding ARC is critical for avoiding memory leaks and unexpected retains.

**Strong, weak, unowned**: Strong references (default) increment the reference count. Weak references (optional, auto-nils on deallocation) don't increment. Unowned references (non-optional, crash on access after deallocation) don't increment.

**Retain cycles**: Two objects holding strong references to each other can never be deallocated. The classic case: a closure capturing `self` strongly, stored as a property on `self`.

```swift
class ViewModel {
    var onComplete: (() -> Void)?
    
    func setup() {
        // RETAIN CYCLE: closure captures self strongly
        onComplete = {
            self.process() // Keeps ViewModel alive forever
        }
        
        // FIX: capture list with weak
        onComplete = { [weak self] in
            self?.process()
        }
    }
}
```

**Interview question**: "When do you use weak vs unowned?" Use `weak` when the captured reference might become nil (delegate patterns, closures in VCs that can be dismissed). Use `unowned` when you're certain the captured reference outlives the closure (and accept the crash if wrong). When in doubt, use `weak`.

## SwiftUI vs UIKit

Understanding when to use each and how they interact is a critical senior iOS interview topic.

**SwiftUI strengths**: Declarative UI, automatic dark mode/dynamic type support, built-in animations, previews in Xcode, excellent for new greenfield apps. Constraints: limited customization for complex UI, iOS 14+ requirement for many features, some UIKit components not yet available.

**UIKit strengths**: Full control over rendering, extensive customization, battle-tested for 15+ years, all third-party libraries support it, better performance for complex custom drawing.

**Interoperability**: `UIViewRepresentable` wraps UIKit views in SwiftUI. `UIHostingController` hosts SwiftUI views in UIKit hierarchies. Senior engineers know when to bridge and how.

**@State, @StateObject, @ObservedObject**: `@State` for simple local value types. `@StateObject` creates and owns an ObservableObject — the view creates it and retains ownership. `@ObservedObject` receives an ObservableObject from outside — the view doesn't own it.

The critical distinction: if you put a `@StateObject` in a parent view, it survives parent re-renders. If you use `@ObservedObject` with an instance created in the view body, it gets recreated on every render — a common bug.

## Architecture Patterns

**MVVM in iOS**: Model (data + business logic), ViewModel (transforms model for display, handles user actions), View (UIKit/SwiftUI, observes ViewModel).

```swift
@MainActor
class UserViewModel: ObservableObject {
    @Published var user: User?
    @Published var isLoading = false
    
    func load(userId: String) async {
        isLoading = true
        defer { isLoading = false }
        user = try? await userService.fetchUser(id: userId)
    }
}
```

**The Composable Architecture (TCA)**: Popular for teams that want testability and predictability. Unidirectional data flow: State → View → Actions → Reducer → State. More boilerplate but highly testable.

**Coordinator pattern**: Separates navigation logic from view controllers. A Coordinator object owns a UINavigationController and handles all navigation decisions. Views call `delegate.didTapLogin()` instead of pushing view controllers directly.

## Performance Optimization

**Main thread blocking**: Any non-trivial work on the main thread causes UI jank. Profile with Instruments → Time Profiler. Move image processing, JSON decoding, and network parsing off main thread.

**List performance**: UICollectionView/UITableView with cell reuse is still faster than SwiftUI List for very large datasets. For SwiftUI, use `LazyVStack` and ensure list items have stable IDs.

**Image loading**: Never load images synchronously. Use async image loading (SwiftUI's `AsyncImage`, Kingfisher, SDWebImage for UIKit). Cache decoded images — decoding is expensive.

**Instruments time profiling**: Launch Time profiler in Instruments. Look for excessive time in main thread. Common culprits: synchronous Core Data fetches, synchronous network calls, complex view hierarchies.

For senior iOS roles, the ability to reason about Swift concurrency correctness, memory ownership, and the trade-offs between UIKit and SwiftUI distinguishes candidates who've built production apps at scale.
