---
title: "C# 12 Modern Patterns Guide"
description: "Modern C# 12 patterns for production code—primary constructors, collection expressions, pattern matching, records, nullable reference types, and the idioms that make modern C# concise and safe."
date: "2026-03-21"
category: "Language Deep Dives"
---

# C# 12 Modern Patterns Guide

C# has evolved dramatically from its Java-influenced origins. C# 12 and .NET 8 (LTS) bring a language that rivals functional languages for expressiveness while maintaining the object-oriented features that enterprise developers rely on. This guide covers the modern patterns that senior C# engineers use in production.

## Primary Constructors (C# 12)

Eliminate boilerplate constructor code:

```csharp
// Before C# 12
public class UserService
{
    private readonly IUserRepository _userRepository;
    private readonly ILogger<UserService> _logger;

    public UserService(IUserRepository userRepository, ILogger<UserService> logger)
    {
        _userRepository = userRepository;
        _logger = logger;
    }
}

// C# 12: Primary constructor
public class UserService(IUserRepository userRepository, ILogger<UserService> logger)
{
    public async Task<User?> GetUserAsync(int id)
    {
        logger.LogInformation("Fetching user {UserId}", id);
        return await userRepository.GetByIdAsync(id);
    }
}
```

Parameters are in scope throughout the class body.

## Records for Immutable Data

Records are immutable by default with value semantics:

```csharp
// Record with init-only properties
public record User(int Id, string Name, string Email);

// Usage
var user = new User(1, "Alice", "alice@example.com");
var updated = user with { Name = "Alice Smith" }; // creates new instance

// Records have built-in equality by value
var user2 = new User(1, "Alice", "alice@example.com");
Console.WriteLine(user == user2); // true — value equality, not reference equality
```

Records are ideal for DTOs, API response models, and domain value objects.

## Pattern Matching

C# pattern matching is expressive and type-safe:

```csharp
public string DescribeShape(object shape) => shape switch
{
    Circle { Radius: > 10 } c => $"Large circle with radius {c.Radius}",
    Circle c => $"Small circle with radius {c.Radius}",
    Rectangle { Width: var w, Height: var h } when w == h => $"Square with side {w}",
    Rectangle r => $"Rectangle {r.Width}x{r.Height}",
    null => "null shape",
    _ => "unknown shape"
};
```

Pattern matching works with switch expressions for functional-style transformations:

```csharp
// Result pattern matching
var message = result switch
{
    { IsSuccess: true, Value: var user } => $"Hello, {user.Name}",
    { IsFailure: true, Error: var error } => $"Error: {error.Message}",
    _ => "Unknown state"
};
```

## Nullable Reference Types

Enable nullable reference types to catch null-reference errors at compile time:

```csharp
// In .csproj:
// <Nullable>enable</Nullable>

public string GetUsername(int? userId)
{
    if (userId is null) return "Anonymous"; // Compiler knows userId could be null here

    var user = _repository.Find(userId.Value); // .Value safe because userId was non-null
    return user?.Name ?? "Unknown"; // Compiler warns if .Name could be null
}
```

The compiler tracks nullability through control flow, eliminating many `NullReferenceException` possibilities.

## Collection Expressions (C# 12)

```csharp
// Unified syntax for creating collections
int[] numbers = [1, 2, 3, 4, 5];
List<string> names = ["Alice", "Bob", "Carol"];
HashSet<int> ids = [1, 2, 3];
Span<byte> bytes = [0x48, 0x65, 0x6c, 0x6c, 0x6f];

// Spread operator
int[] first = [1, 2, 3];
int[] second = [4, 5, 6];
int[] combined = [..first, ..second]; // [1, 2, 3, 4, 5, 6]
```

## Async/Await Production Patterns

```csharp
// ConfigureAwait(false) for library code
public async Task<User> GetUserAsync(int id)
{
    return await _repository.GetByIdAsync(id).ConfigureAwait(false);
}

// IAsyncEnumerable for streaming data
public async IAsyncEnumerable<User> StreamUsersAsync(
    [EnumeratorCancellation] CancellationToken ct = default)
{
    await foreach (var user in _repository.StreamAllAsync().WithCancellation(ct))
    {
        yield return user;
    }
}

// Consuming async streams
await foreach (var user in userService.StreamUsersAsync(cancellationToken))
{
    await ProcessUserAsync(user);
}
```

## Dependency Injection with .NET DI

```csharp
// Program.cs (.NET 8 minimal API)
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<UserService>();
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("Default")));

var app = builder.Build();

app.MapGet("/users/{id}", async (int id, UserService userService) =>
{
    var user = await userService.GetUserAsync(id);
    return user is null ? Results.NotFound() : Results.Ok(user);
});

app.Run();
```

## Source Generators

Source generators run at compile time to generate boilerplate:

```csharp
// AutoMapper-style mapping without reflection overhead
[Mapper]
public partial class UserMapper
{
    public partial UserDto ToDto(User user);
}

// JSON serialization without reflection (AOT-compatible)
[JsonSourceGenerationOptions(WriteIndented = true)]
[JsonSerializable(typeof(User))]
[JsonSerializable(typeof(List<User>))]
internal partial class AppJsonContext : JsonSerializerContext { }
```

Source generators are why .NET can now publish native AOT (ahead-of-time compiled) applications with sub-millisecond startup.

## Interview Tips

Modern C# interview questions in 2026:

1. **Records vs classes** — value equality, immutability, when to use each
2. **Nullable reference types** — how the compiler tracks nullability, why it matters
3. **Primary constructors** — boilerplate reduction, dependency injection pattern
4. **Pattern matching** — switch expressions for functional transformations
5. **async/await** — ConfigureAwait, IAsyncEnumerable, CancellationToken

The most impressive C# knowledge to show: understanding how nullable reference types work with control flow analysis, and the difference between `?` null-forgiving operator (suppressing warnings) vs genuinely null-safe code.
