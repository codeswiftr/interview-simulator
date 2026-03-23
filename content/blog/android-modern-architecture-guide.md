---
title: "Modern Android Architecture in 2025: Compose, Kotlin Flow, and Clean Architecture"
description: "Deep dive into modern Android architecture patterns — Jetpack Compose state management, Kotlin Flow reactive streams, Clean Architecture layers, and architecture interview questions for senior Android engineers."
date: "2026-03-20"
category: "Technical Skills Guides"
---

# Modern Android Architecture in 2025: Compose, Kotlin Flow, and Clean Architecture

Android architecture has stabilized around a set of patterns that Google and the industry have converged on: Jetpack Compose for UI, Kotlin Flow for reactive data, Clean Architecture for layering, and Hilt for dependency injection. Senior Android engineer interviews now assume familiarity with these patterns and test depth of understanding. Here's the practical architecture knowledge that matters in 2025 interviews.

## The Modern Android Architecture Stack

Google's "recommended app architecture" (as of 2024) has three layers:

**UI Layer:** Composables (or Fragments/Views) + ViewModels. The ViewModel holds UI state as `StateFlow<UiState>`, processes user events, and coordinates with the Data Layer. Composables collect from `StateFlow` and render state.

**Domain Layer (optional):** Use cases / interactors that encapsulate business logic. Useful when multiple ViewModels share business rules or when business logic is complex enough to warrant testing independently. Each use case does one thing: `GetUserFeedUseCase`, `SubmitOrderUseCase`.

**Data Layer:** Repositories + data sources (remote API, local Room database, DataStore). Repositories abstract the data source selection (cache first, network fallback). Data sources expose Flows for reactive updates.

This layering enforces unidirectional data flow: ViewModel calls use case, use case calls repository, repository emits Flow data upward through the stack.

## StateFlow and SharedFlow in Practice

**StateFlow for UI state:**
`StateFlow` is always active (hot), has a value (current state), replays the latest emission to new collectors. Perfect for UI state because a new subscriber (e.g., navigating back to a screen) immediately gets the current state without waiting for the next emission.

```kotlin
class SearchViewModel(private val repo: SearchRepository) : ViewModel() {
    private val _query = MutableStateFlow("")
    
    val results: StateFlow<List<Result>> = _query
        .debounce(300)
        .filter { it.length >= 2 }
        .flatMapLatest { query -> repo.search(query) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
}
```

`stateIn` converts a cold Flow to a StateFlow. `WhileSubscribed(5000)` keeps the upstream flow active for 5 seconds after the last subscriber disappears — useful to survive configuration changes without restarting network requests.

**SharedFlow for one-time events:**
Navigation actions, error snackbars, or dialogs should be one-time events, not persistent state. `SharedFlow` with `replay=0` emits to active collectors only — no replay for new subscribers.

```kotlin
private val _events = MutableSharedFlow<UiEvent>()
val events: SharedFlow<UiEvent> = _events.asSharedFlow()
```

Collecting `SharedFlow` requires careful lifecycle management — use `repeatOnLifecycle(STARTED)` to ensure collection only when UI is visible.

## Room Database Patterns

Room is Android's ORM over SQLite. Interview questions probe beyond basic CRUD:

**Flow-backed queries:** Room DAOs support `Flow<List<T>>` return types — the query automatically re-executes when the underlying data changes. This reactive pattern means your UI stays in sync with the database without manual refresh.

**Migration strategies:** When schema changes, provide migration paths via `Migration` objects. For complex changes, `fallbackToDestructiveMigration()` drops and recreates the database (only appropriate when data can be refetched from a server).

**Pagination with Paging 3:** For lists that can't be loaded entirely into memory, the Paging 3 library integrates with Room and network sources. `RemoteMediator` handles the network-to-database pattern (fetch from API, store in Room, display from Room) — a key architecture question for feeds and lists.

## Navigation Component and Deep Links

Jetpack Navigation provides a visual navigation graph, type-safe argument passing, and deep link handling.

**Type-safe navigation (Compose Destinations or Navigation 2.7+):** Pass strongly-typed arguments between destinations rather than serializing to Bundle strings. Prevents runtime crashes from argument mismatch.

**Deep links in architecture:** Deep links into specific app destinations must handle the case where the back stack doesn't exist (user opened the link from a notification without having the app open). Navigation component's `NavDeepLink` handles this by constructing a synthetic back stack.

**Bottom navigation state preservation:** When switching tabs, `saveState = true` and `restoreState = true` parameters on `NavOptions` preserve each tab's back stack and scroll position — a UX expectation that has a non-trivial implementation.

## Testing Architecture in Android

Well-architected Android code is testable. Interviews probe testing strategy at each layer:

**ViewModel testing:**
Use `TestCoroutineDispatcher` (or `UnconfinedTestDispatcher` in newer test libraries) to control coroutine execution. `turbine` library for testing Flow emissions — `test()` collects emissions in an ordered list for assertion.

**Repository testing:**
Test the `suspend fun` interface with `runTest {}`. Mock the remote API (MockWebServer from OkHttp, or Mockk) and verify that the repository correctly handles success, errors, and caching logic.

**Compose UI testing:**
`ComposeTestRule` allows writing UI tests that interact with composables by semantic actions (`performClick()`, `assertIsDisplayed()`). Integration-level tests using real ViewModels with fake repositories validate the complete UI layer behavior.

**The "don't test implementation details" principle:**
Test what the system does (user taps button → item appears in list), not how it does it (ViewModel called repository's fetchItems method). This makes tests more resilient to refactoring.

Modern Android architecture interviews expect you to discuss not just which patterns to use but why — the tradeoffs between event vs state for one-time UI actions, when to add a domain layer vs keep logic in the ViewModel, and how architecture decisions affect testability and code maintainability.
