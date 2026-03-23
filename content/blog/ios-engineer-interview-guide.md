# iOS Engineer Interview Guide 2024: What's Actually Tested

iOS engineering interviews are distinct from general SWE interviews. They test Swift and Objective-C depth, UIKit and SwiftUI patterns, memory management, the iOS runtime, and app architecture — plus standard algorithms. Companies like Apple, Airbnb, Lyft, Spotify, and Robinhood run rigorous iOS-specific loops. Here's everything you need to know.

## What iOS Interviews Test Beyond Standard SWE

- **Swift internals**: Value vs. reference types, ARC, protocol-oriented programming, generics
- **UIKit/SwiftUI**: View lifecycle, AutoLayout, layout engine, state management in SwiftUI
- **iOS runtime and memory**: ARC, retain cycles, weak/unowned references, memory profiling
- **Concurrency**: GCD, OperationQueue, Swift Concurrency (async/await, actors)
- **Architecture**: MVC vs. MVVM vs. VIPER, Coordinator pattern, dependency injection
- **App lifecycle**: Application states, background execution, push notifications, app extensions

## Interview Format

1. Recruiter screen (30 min)
2. Technical phone screen (60 min) — Swift/Objective-C coding + iOS fundamentals
3. Virtual onsite (4-5 rounds):
   - 1-2 coding rounds (Swift DSA)
   - 1 iOS system design / architecture round
   - 1 iOS-specific technical deep dive (memory, threading, lifecycle)
   - 1 behavioral round
4. Hiring decision

Apple and Robinhood weight technical depth heavily. Airbnb and Lyft weight architecture and product thinking.

## Coding in Swift

Swift fluency is expected. Know the language idioms, not just the syntax.

**Value types vs. reference types:**
```swift
// Struct (value type) — copied on assignment
struct Point {
    var x: Double
    var y: Double
}

var a = Point(x: 1.0, y: 2.0)
var b = a  // b is a COPY of a
b.x = 99   // Does not affect a.x

// Class (reference type) — shared reference
class Node {
    var value: Int
    var next: Node?

    init(_ value: Int) { self.value = value }
}

let n1 = Node(1)
let n2 = n1  // n2 POINTS TO the same Node
n2.value = 99  // n1.value is now 99
```

**Protocol-oriented programming (POP):**
Swift favors protocols + extensions over inheritance. A common interview pattern:
```swift
protocol Describable {
    var description: String { get }
}

extension Describable {
    func printDescription() {
        print(description)
    }
}

// Any type can conform and get printDescription() for free
struct User: Describable {
    var name: String
    var description: String { "User: \(name)" }
}
```

**Generics with constraints:**
```swift
func findMax<T: Comparable>(_ array: [T]) -> T? {
    guard !array.isEmpty else { return nil }
    return array.reduce(array[0]) { $0 > $1 ? $0 : $1 }
}
```

**Optionals and safe unwrapping:**
```swift
// Guard-let for early exit (preferred over if-let for complex conditions)
func processUser(_ user: User?) {
    guard let user = user else {
        print("No user")
        return
    }
    // user is non-optional here
    print(user.name)
}

// Nil coalescing
let name = user?.name ?? "Anonymous"

// Optional chaining
let streetName = user?.address?.street?.name  // Returns nil if any link is nil
```

## Memory Management: ARC and Retain Cycles

Every iOS interview will probe ARC (Automatic Reference Counting) and retain cycle detection.

**Retain cycle example:**
```swift
class Parent {
    var child: Child?
    deinit { print("Parent deallocated") }
}

class Child {
    var parent: Parent?  // STRONG reference — causes retain cycle!
    deinit { print("Child deallocated") }
}

var p: Parent? = Parent()
var c: Child? = Child()
p?.child = c
c?.parent = p  // Cycle: Parent → Child → Parent, neither can be deallocated

// Fix: use weak reference
class Child {
    weak var parent: Parent?  // weak = zeroed automatically when Parent is deallocated
}
```

**`weak` vs. `unowned`:**
- `weak`: Optional reference, becomes nil when target is deallocated. Use when the reference may become nil.
- `unowned`: Non-optional reference, crashes if accessed after deallocation. Use when you're certain the reference outlives the object.

**Common retain cycle: closures capturing `self`:**
```swift
class ViewController: UIViewController {
    var timer: Timer?

    func startTimer() {
        // WRONG: strong reference cycle — self → timer → closure → self
        timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
            self.updateUI()  // Strong capture of self
        }
    }

    func startTimerFixed() {
        // CORRECT: weak capture list
        timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            self?.updateUI()  // If self is nil, nothing happens
        }
    }
}
```

Use **Instruments → Leaks** and **LeakSanitizer** in production to detect these.

## iOS Concurrency

Threading is a core iOS interview topic.

**Grand Central Dispatch (GCD):**
```swift
// Background work, then update UI on main thread
DispatchQueue.global(qos: .background).async {
    let data = fetchLargeDataset()  // Runs on background thread
    DispatchQueue.main.async {
        self.tableView.reloadData()  // UI updates must run on main thread
    }
}
```

**Swift Concurrency (async/await — modern approach):**
```swift
func fetchUserProfile() async throws -> UserProfile {
    let (data, _) = try await URLSession.shared.data(from: profileURL)
    return try JSONDecoder().decode(UserProfile.self, from: data)
}

// Calling it
Task {
    do {
        let profile = try await fetchUserProfile()
        await MainActor.run {
            updateUI(with: profile)
        }
    } catch {
        handleError(error)
    }
}
```

**Actors (Swift Concurrency):**
Actors provide mutual exclusion — only one task can access actor state at a time:
```swift
actor ImageCache {
    private var cache: [String: UIImage] = [:]

    func store(image: UIImage, for key: String) {
        cache[key] = image
    }

    func retrieve(for key: String) -> UIImage? {
        return cache[key]
    }
}
```

**MainActor:**
`@MainActor` ensures code runs on the main thread — use for UI-bound properties in ViewModels.

## SwiftUI vs. UIKit

For 2024 interviews, expect both. Senior roles at forward-looking companies require SwiftUI proficiency.

**SwiftUI key concepts:**

*State management:*
- `@State`: Local, view-owned state (simple values, survives re-renders)
- `@StateObject`: Local, owned reference type (ViewModel instances)
- `@ObservedObject`: External observable passed in (don't use for creation)
- `@EnvironmentObject`: Dependency injection via environment (global state)
- `@Binding`: Two-way binding to parent's state

*View lifecycle:*
- `onAppear` / `onDisappear` — lifecycle hooks
- `.task` modifier — cancellable async work tied to view lifetime (preferred over `onAppear` + Task)
- `@MainActor` on ViewModel ensures UI updates on main thread

*Combine integration:*
```swift
class SearchViewModel: ObservableObject {
    @Published var query = ""
    @Published var results: [SearchResult] = []

    private var cancellables = Set<AnyCancellable>()

    init() {
        $query
            .debounce(for: .milliseconds(300), scheduler: RunLoop.main)
            .removeDuplicates()
            .flatMap { query in
                SearchService.search(query: query).catch { _ in Just([]) }
            }
            .assign(to: &$results)
    }
}
```

## iOS System Design

iOS system design rounds focus on app architecture, not server-side systems.

**Common questions:**
- Design the Instagram photo feed
- Design an offline-capable messaging app
- Design a photo/video upload manager
- Design a navigation/routing system (coordinator pattern)
- Design a real-time sports score tracking app

**Framework:**

**1. Architecture pattern choice**
- MVVM: View ↔ ViewModel (data binding, Combine) ↔ Model. Good for most apps.
- MVVM + Coordinator: Coordinators own navigation, ViewModels own data. Decouples navigation from screens.
- VIPER: View, Interactor, Presenter, Entity, Router. Verbose but highly testable; favored at companies with large teams.

**2. Dependency injection**
Pass dependencies through init. Don't use singletons (untestable, hard to mock). Consider a DI container (Swinject) for large apps.

**3. Offline-first**
- Core Data or SwiftData as local cache
- NSFetchedResultsController (UIKit) or @FetchRequest (SwiftUI) for reactive updates
- Background sync via URLSession background transfers + BGTaskScheduler

**4. Image caching**
- NSCache for in-memory (automatically evicts under pressure)
- FileManager for disk cache with LRU eviction
- Third-party: SDWebImage, Kingfisher — interviewers like it when you can explain what they do under the hood

## Behavioral: iOS-Specific

**"Tell me about a memory issue you diagnosed and fixed."**
Walk through: symptom (crash, high memory warning), tool used (Instruments/Leaks), root cause (retain cycle, large image allocations), fix, verification.

**"How do you approach backwards compatibility?"**
Min deployment target, `#available` checks, dynamic feature detection.

**"How do you test iOS code?"**
XCTest for unit tests, XCUITest for UI tests. Mock network layers with URLProtocol subclassing. Test ViewModel in isolation (no UIKit dependency).

**"SwiftUI or UIKit for a new project?"**
SwiftUI for greenfield iOS 16+ apps. UIKit for apps that need iOS 14/15 support, complex custom transitions, or existing UIKit codebases. Hybrid (SwiftUI inside UIKit or vice versa) is always an option.

## Preparation Timeline

**Weeks 1-2: Swift and iOS fundamentals**
- ARC, retain cycles, closure capture lists — quiz yourself until instant
- Implement a thread-safe cache using actor or DispatchQueue
- Swift Concurrency: async/await, actors, task groups

**Weeks 3-4: Architecture and SwiftUI**
- Build an MVVM app with Coordinator navigation
- Learn SwiftUI state management (@State, @StateObject, @EnvironmentObject)
- Design a photo upload manager with offline queue

**Weeks 5-6: DSA + behavioral**
- 25 LeetCode medium problems in Swift
- Prepare 3 STAR stories: performance fix, architecture decision, testing strategy
- Practice iOS system design with a partner (photo feed, offline messaging)

## What Sets iOS Candidates Apart

The iOS engineers who pass at top companies have internalized one thing: **every byte and every cycle matters**. They understand that a scroll freeze happens because they're doing work on the main thread. They know that their image cache can trigger memory warnings if they're not careful. They profile first, optimize second.

This platform-aware instinct — understanding the iOS runtime, not just the Swift language — is what separates engineers who write iOS code from engineers who write great iOS apps.
