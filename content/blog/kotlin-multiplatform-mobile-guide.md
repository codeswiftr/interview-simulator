---
title: "Kotlin Multiplatform Mobile: Complete Guide"
description: "How to build cross-platform iOS and Android apps with Kotlin Multiplatform—shared business logic, platform-specific UI, Compose Multiplatform, and production patterns for KMP apps."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Kotlin Multiplatform Mobile: Complete Guide

Kotlin Multiplatform (KMP) has graduated from experimental to production-ready. It takes a different approach than React Native or Flutter: share only the business logic, let each platform use its native UI. This results in truly native UIs with shared code for networking, data persistence, and domain logic.

## The KMP Philosophy

React Native/Flutter: write UI once, run everywhere (but often feel like a cross-platform app).
KMP: write business logic once, build truly native UIs on each platform.

```
Shared (Kotlin):
  - API calls
  - Data models
  - Business logic
  - Database (SQLDelight)
  - State management

iOS-specific (Swift/SwiftUI):
  - UI components
  - Platform integrations (HealthKit, ARKit)

Android-specific (Kotlin/Compose):
  - UI components
  - Platform integrations (Notifications, Maps)
```

## Project Structure

```
shared/
├── commonMain/
│   ├── data/
│   │   ├── repository/
│   │   └── api/           # Ktor HTTP client
│   ├── domain/
│   │   ├── model/
│   │   └── usecase/
│   └── presentation/      # ViewModels (using coroutines)
├── iosMain/               # iOS-specific implementations
└── androidMain/           # Android-specific implementations

androidApp/                # Android UI (Compose)
iosApp/                    # iOS UI (SwiftUI)
```

## Shared Networking with Ktor

```kotlin
// shared/commonMain/data/api/UserApi.kt
class UserApi(private val client: HttpClient) {
    suspend fun getUser(id: String): User {
        return client.get("$BASE_URL/users/$id").body()
    }
}

// Platform-specific client setup
// androidMain
actual fun createHttpClient() = HttpClient(OkHttp) {
    install(ContentNegotiation) { json() }
}

// iosMain
actual fun createHttpClient() = HttpClient(Darwin) {
    install(ContentNegotiation) { json() }
}
```

## SQLDelight for Shared Database

SQLDelight generates type-safe Kotlin from SQL, running on both platforms:

```sql
-- shared/src/commonMain/sqldelight/User.sq
CREATE TABLE User (
    id TEXT NOT NULL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL
);

selectAll:
SELECT * FROM User;

insertUser:
INSERT INTO User(id, name, email) VALUES (?, ?, ?);
```

Generated Kotlin is available in commonMain:
```kotlin
val users: List<User> = userQueries.selectAll().executeAsList()
userQueries.insertUser(id = "1", name = "Alice", email = "alice@example.com")
```

## Shared ViewModels

```kotlin
// shared/commonMain — accessible from both iOS and Android
class UserViewModel(
    private val userRepository: UserRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow<UserUiState>(UserUiState.Loading)
    val uiState = _uiState.asStateFlow()

    fun loadUser(userId: String) {
        viewModelScope.launch {
            _uiState.value = UserUiState.Loading
            userRepository.getUser(userId)
                .onSuccess { user -> _uiState.value = UserUiState.Success(user) }
                .onFailure { error -> _uiState.value = UserUiState.Error(error.message) }
        }
    }
}
```

iOS uses this ViewModel from Swift via the KMP framework.

## Compose Multiplatform

Compose Multiplatform (from JetBrains) extends Jetpack Compose to iOS, Desktop, and Web:

```kotlin
// Shared UI with Compose Multiplatform
@Composable
fun UserScreen(viewModel: UserViewModel) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    when (uiState) {
        is UserUiState.Loading -> CircularProgressIndicator()
        is UserUiState.Success -> UserContent(uiState.user)
        is UserUiState.Error -> ErrorMessage(uiState.message)
    }
}
```

This allows sharing even the UI layer, though with different trade-offs than pure KMP (less native look and feel by default).

## iOS Integration

The shared module compiles to an iOS XCFramework:

```swift
// iosApp/ContentView.swift
import SwiftUI
import shared  // Import KMP framework

struct UserView: View {
    @StateObject private var viewModel = UserViewModel(userRepository: ...)

    var body: some View {
        switch viewModel.uiState {
        case is UserUiStateLoading:
            ProgressView()
        case let success as UserUiStateSuccess:
            Text(success.user.name)
        default:
            Text("Error")
        }
    }
}
```

## When to Use KMP

**KMP works well for**:
- Apps with significant business logic (validation, algorithms, state machines)
- Teams with Android Kotlin expertise who need iOS too
- Apps where native UI feel is critical
- Gradual migration from separate native codebases

**Consider Flutter instead when**:
- Team has no Kotlin experience
- Maximum code sharing (including UI) is the priority
- Rapid prototyping is more important than native feel

## Interview Tips

KMP interview questions in 2026:

1. **KMP vs Flutter vs React Native** — the philosophy difference (share logic vs share UI)
2. **Ktor for networking** — multiplatform HTTP client
3. **SQLDelight** — type-safe shared database layer
4. **Compose Multiplatform** — when to use shared UI vs platform-native
5. **iOS integration** — XCFramework and Swift interop

The core interview insight: KMP's approach (share business logic, not UI) often produces better apps than "write once, run anywhere" because each platform's UI layer remains native.
