---
title: "Swift Concurrency: Advanced Patterns"
description: "Advanced Swift concurrency patterns for iOS and macOS development—actors, async sequences, task groups, structured concurrency, and avoiding common pitfalls with Swift's concurrency model."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Swift Concurrency: Advanced Patterns

Swift's structured concurrency (introduced in Swift 5.5) has matured into a powerful and safe concurrency model. Understanding actors, async sequences, task groups, and the MainActor is essential for senior iOS engineers in 2026. These patterns appear regularly in iOS engineering interviews.

## Structured Concurrency Fundamentals

Swift's concurrency is structured: async tasks have a defined lifecycle tied to their parent scope.

```swift
func fetchUserData() async throws -> UserData {
    // Both tasks run concurrently
    async let profile = fetchProfile()
    async let settings = fetchSettings()

    // Await both — this line blocks until both complete
    let (userProfile, userSettings) = try await (profile, settings)
    return UserData(profile: userProfile, settings: userSettings)
}
```

`async let` creates concurrent child tasks that are automatically cancelled if the parent scope throws or returns.

## Actors for Shared Mutable State

Actors prevent data races by ensuring only one task accesses an actor's state at a time:

```swift
actor UserCache {
    private var cache: [String: User] = [:]

    func user(for id: String) -> User? {
        return cache[id]
    }

    func store(_ user: User) {
        cache[user.id] = user
    }

    func clear() {
        cache.removeAll()
    }
}

// Usage
let cache = UserCache()

// Actor methods are async by default from outside the actor
let user = await cache.user(for: "123")
await cache.store(fetchedUser)
```

**Why actors over locks**: Actors are checked at compile time. The compiler prevents you from accessing actor-protected state without `await`. With locks, you can accidentally access state without locking, and the compiler won't warn you.

## MainActor for UI Updates

All UI updates must happen on the main thread. MainActor is a global actor that enforces this:

```swift
@MainActor
class ProfileViewModel: ObservableObject {
    @Published var user: User?
    @Published var isLoading = false

    func loadUser(id: String) async {
        isLoading = true
        do {
            // This runs on a background thread (off MainActor)
            let user = try await userService.fetchUser(id: id)
            // Back on MainActor (UI update)
            self.user = user
        } catch {
            print("Error: \(error)")
        }
        isLoading = false
    }
}
```

Marking the whole class `@MainActor` means all methods run on the main thread by default. Use `Task.detached` or `nonisolated` for background work within a MainActor type.

## Task Groups for Dynamic Concurrency

When you don't know the number of concurrent tasks at compile time:

```swift
func fetchAllUsers(ids: [String]) async throws -> [User] {
    try await withThrowingTaskGroup(of: User.self) { group in
        for id in ids {
            group.addTask {
                try await userService.fetchUser(id: id)
            }
        }

        var users: [User] = []
        for try await user in group {
            users.append(user)
        }
        return users
    }
}
```

Task groups automatically manage child task lifecycle and propagate errors correctly.

## AsyncSequence

Async sequences are like sequences but values arrive asynchronously—perfect for streams:

```swift
func streamUpdates() -> AsyncStream<Update> {
    AsyncStream { continuation in
        let subscription = updateService.subscribe { update in
            continuation.yield(update)
        }

        continuation.onTermination = { _ in
            subscription.cancel()
        }
    }
}

// Consumption
for await update in streamUpdates() {
    await handleUpdate(update)
}
```

AsyncSequence is the standard pattern for handling WebSocket messages, database change notifications, and sensor data.

## Task Cancellation

Tasks can be cancelled. Well-written code respects cancellation:

```swift
func processLargeDataset(items: [Item]) async throws -> [ProcessedItem] {
    var results: [ProcessedItem] = []

    for item in items {
        // Check for cancellation between iterations
        try Task.checkCancellation()

        let processed = try await process(item)
        results.append(processed)
    }
    return results
}

// Cancelling a task
let task = Task {
    try await processLargeDataset(items: largeArray)
}

// Cancel from elsewhere
task.cancel()
```

## Continuations for Callback API Bridging

Bridge callback-based APIs to async/await:

```swift
func fetchDataWithCallback() async throws -> Data {
    try await withCheckedThrowingContinuation { continuation in
        legacyAPIClient.fetch { result, error in
            if let error = error {
                continuation.resume(throwing: error)
            } else if let result = result {
                continuation.resume(returning: result)
            } else {
                continuation.resume(throwing: APIError.emptyResponse)
            }
        }
    }
}
```

Use `withCheckedThrowingContinuation` for failable operations, `withCheckedContinuation` for non-throwing.

## Interview Tips

Swift concurrency is a core topic for senior iOS engineering interviews:

1. **Actor isolation** — explain how actors prevent data races at compile time
2. **MainActor** — why UI updates must be on main thread and how @MainActor enforces this
3. **structured vs unstructured concurrency** — child task cancellation propagation
4. **AsyncSequence** — replace callbacks and delegates with async for-in loops
5. **Task cancellation** — cooperative cancellation with `Task.checkCancellation()`

The most impressive thing to demonstrate: understanding that Swift's concurrency is compile-time checked. The compiler rejects code that could cause data races, unlike other concurrency models that fail at runtime.
