---
title: "Android Developer Interview Guide: Kotlin, Jetpack Compose, and Architecture Patterns"
description: "Prepare for Android developer interviews — Kotlin, Jetpack Compose vs Views, MVVM/MVI, Coroutines, Room, and common Android interview questions."
date: "2026-03-20"
category: "Programming Languages"
---

# Android Developer Interview Guide: Kotlin, Jetpack Compose, and Architecture Patterns

Android interviews test Kotlin proficiency, Android framework knowledge, architecture patterns, and modern Jetpack components. Whether you're targeting Google, a consumer app company, or a scale-up with Android-heavy traffic, here's the preparation roadmap.

## Kotlin Essentials

**Null safety:** Kotlin's type system distinguishes nullable (`String?`) from non-null (`String`). Null safety at compile time. Safe call operator (`?.`), Elvis operator (`?:`), not-null assertion (`!!` — avoid in production).

**Coroutines:** Kotlin's concurrency model. `suspend` functions run asynchronously without blocking threads. Launch with `CoroutineScope.launch` (fire-and-forget) or `async`/`await` (for values). 

```kotlin
viewModelScope.launch {
    val result = withContext(Dispatchers.IO) {
        repository.fetchData()  // IO-bound work off main thread
    }
    // Back on main thread
    _uiState.value = result
}
```

**Flow:** Cold observable streams. `StateFlow` for state (always has a value, replays to new collectors). `SharedFlow` for events (configurable replay). Replace LiveData in modern codebases.

**Extension functions, data classes, sealed classes:** Know these deeply — they're ubiquitous in idiomatic Kotlin. Sealed classes for modeling sum types (Result, UiState).

## Jetpack Compose vs. Views

**Traditional Views:** XML layouts, ViewGroups, View recycling. Imperative — you manipulate views directly. Still dominant in existing codebases. Key APIs: RecyclerView with DiffUtil, ViewBinding, ConstraintLayout.

**Jetpack Compose:** Declarative UI, composable functions, recomposition. State drives UI. Modern approach for new projects targeting Android 5.0+.

```kotlin
@Composable
fun UserCard(user: User, onTap: () -> Unit) {
    Card(modifier = Modifier.clickable(onClick = onTap)) {
        Row {
            AsyncImage(model = user.avatarUrl, ...)
            Text(text = user.name)
        }
    }
}
```

**State in Compose:** `remember` for local state surviving recomposition. `rememberSaveable` for state surviving configuration changes. `collectAsStateWithLifecycle` for collecting ViewModel Flows.

## Architecture

**MVVM with ViewModel:** Google's recommended pattern. ViewModel survives configuration changes (screen rotation). Exposes `StateFlow`/`LiveData` for UI to observe. UI layer only handles display logic; ViewModel handles presentation logic; Repository handles data.

**MVI (Model-View-Intent):** Unidirectional data flow. User intents → ViewModel processes → emits new state → UI renders. Popular for complex screens where state transitions need to be explicit and testable.

**Repository pattern:** Abstracts data sources. ViewModel calls repository; repository decides whether to serve from cache, Room database, or network. Decouples data source details from business logic.

## Room Database

Room is Android's SQLite abstraction. Key components: `@Entity` (table), `@Dao` (data access object with suspend queries), `@Database` (database builder).

```kotlin
@Dao
interface UserDao {
    @Query("SELECT * FROM users WHERE id = :userId")
    suspend fun getUser(userId: String): User?
    
    @Query("SELECT * FROM users")
    fun observeAllUsers(): Flow<List<User>>  // Cold flow, updates on table changes
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertUser(user: User)
}
```

## Activity and Fragment Lifecycle

Still tested, even in Compose-heavy codebases. Key states: `onCreate`, `onStart`, `onResume`, `onPause`, `onStop`, `onDestroy`. The classic question: "What's the difference between onStop and onPause?" onPause: activity partially visible or another activity in foreground. onStop: activity completely hidden.

**Configuration changes:** Screen rotation recreates the Activity. ViewModel survives this (it's retained across config changes). `savedInstanceState` for small amounts of state that must survive process death.

**Fragment backstack:** FragmentManager manages the backstack. Know the difference between `add` (keeps existing fragment) vs. `replace` (removes current fragment) transactions.

## Performance and Testing

**Strict mode:** `StrictMode.setVmPolicy` and `StrictMode.setThreadPolicy` detect accidental disk reads on the main thread, leaked SQLite cursors. Enable during development.

**Profiling:** Android Studio's CPU, Memory, and Network profilers. Identify main thread jank (frame drops), memory leaks with the Memory Profiler and LeakCanary.

**Unit testing:** Test ViewModels with `kotlinx-coroutines-test` (`runTest`, `TestCoroutineDispatcher`). Test Room with an in-memory database (`Room.inMemoryDatabaseBuilder`). Test composables with `ComposeTestRule`.

## Common Interview Questions

"How do you handle background work?" — WorkManager for guaranteed background work (sync, cleanup). Coroutines for in-process async. Foreground service for long-running user-visible work (music, navigation).

"How do you share data between fragments?" — Shared ViewModel scoped to the Activity or a Navigation back stack entry. Avoid Fragment-to-Fragment direct calls.

"How do you handle deep links?" — NavDeepLinkBuilder with Jetpack Navigation. Define deep link patterns in the navigation graph.

Prepare one substantial Android project you've shipped — its architecture, the technical decisions you made, what you'd do differently. That concrete example grounds abstract Android knowledge in real experience.
