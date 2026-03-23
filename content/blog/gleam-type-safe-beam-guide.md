---
title: "Gleam: Type-Safe Programming on the BEAM"
description: "An introduction to Gleam—a statically typed functional language running on the Erlang VM (BEAM), how it differs from Elixir, and why its type system makes concurrent programming safer."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Gleam: Type-Safe Programming on the BEAM

Gleam is a statically typed functional programming language that runs on the Erlang Virtual Machine (BEAM). It combines the battle-tested concurrency and fault tolerance of the BEAM with a modern, expressive type system. Gleam is gaining traction in 2026 as an alternative to Elixir for teams that value static typing.

## Why Gleam on the BEAM?

The BEAM (Erlang's runtime) has extraordinary properties:
- Millions of lightweight concurrent processes
- Fault-tolerant supervision trees
- Hot code upgrades
- Battle-tested in telecoms for 30+ years

Elixir harnesses the BEAM with a Ruby-like syntax but is dynamically typed. Gleam brings static types to the BEAM, catching entire classes of bugs at compile time.

## Gleam Syntax

```gleam
import gleam/io
import gleam/string

pub type User {
  User(id: Int, name: String, email: String)
}

pub fn greet(user: User) -> String {
  string.concat(["Hello, ", user.name, "!"])
}

pub fn main() {
  let user = User(id: 1, name: "Alice", email: "alice@example.com")
  io.println(greet(user))
}
```

Gleam is intentionally simple — there's no implicit state, no null, no exceptions.

## Result Type for Error Handling

Gleam has no exceptions. Errors are values using the `Result` type:

```gleam
import gleam/int
import gleam/result

pub fn parse_age(input: String) -> Result(Int, String) {
  case int.parse(input) {
    Ok(age) if age >= 0 && age <= 150 -> Ok(age)
    Ok(_) -> Error("Age must be between 0 and 150")
    Error(_) -> Error("Invalid number: " <> input)
  }
}

// Using the result
case parse_age("25") {
  Ok(age) -> io.println("Age: " <> int.to_string(age))
  Error(msg) -> io.println("Error: " <> msg)
}
```

The `use` expression (similar to do-notation) makes chaining results ergonomic:

```gleam
import gleam/result

pub fn process_user(user_id: String) -> Result(String, String) {
  use id <- result.try(parse_id(user_id))
  use user <- result.try(fetch_user(id))
  use profile <- result.try(build_profile(user))
  Ok(profile.display_name)
}
```

## Custom Types and Pattern Matching

```gleam
pub type Shape {
  Circle(radius: Float)
  Rectangle(width: Float, height: Float)
  Triangle(base: Float, height: Float)
}

pub fn area(shape: Shape) -> Float {
  case shape {
    Circle(radius: r) -> 3.14159 *. r *. r
    Rectangle(width: w, height: h) -> w *. h
    Triangle(base: b, height: h) -> b *. h /. 2.0
  }
}
```

The compiler ensures all pattern match cases are exhaustive — if you add a new `Shape` variant, every `case` that matches on `Shape` produces a compile error until updated.

## Interop with Erlang and Elixir

Gleam runs on the BEAM alongside Erlang and Elixir:

```gleam
// Call Erlang functions
@external(erlang, "erlang", "node")
pub fn node_name() -> Atom

// Call Elixir modules
@external(erlang, "Elixir.String", "upcase")
pub fn upcase(string: String) -> String
```

Gleam can be incrementally adopted in existing Elixir or Erlang projects.

## Actor Model Support

Gleam supports BEAM's actor model through the `gleam_otp` library:

```gleam
import gleam/otp/actor

pub type Message {
  Increment
  GetCount(reply_with: Subject(Int))
}

pub fn handle_message(message: Message, count: Int) {
  case message {
    Increment -> actor.continue(count + 1)
    GetCount(client) -> {
      process.send(client, count)
      actor.continue(count)
    }
  }
}
```

## Type System Advantages

Gleam's type system catches:
- Pattern match non-exhaustiveness (missing cases)
- Calling functions with wrong argument types
- Accessing record fields that don't exist
- Null pointer equivalent errors (no nil)

What it doesn't have (intentionally simple):
- Type classes/typeclasses
- Implicit conversions
- Inheritance

## When to Consider Gleam

**Gleam makes sense when**:
- You want BEAM fault tolerance with static typing
- Your team has a functional programming background and wants type safety
- You're building a new service and can choose freely

**Elixir makes more sense when**:
- Larger ecosystem is needed (Elixir/Phoenix has much more)
- Team is already familiar with Elixir
- Dynamic nature is an advantage for exploratory development

## Interview Tips

Gleam is a niche but impressive language to know:

1. **Why BEAM** — fault tolerance, concurrency model
2. **Result type** — no exceptions, errors as values
3. **Exhaustive pattern matching** — compile-time completeness checking
4. **Interop** — runs alongside Elixir/Erlang code
5. **Comparison to Elixir** — type safety vs ecosystem breadth

Gleam knowledge signals breadth and genuine interest in programming language design. It's the kind of knowledge that marks an engineer as someone who explores beyond mainstream tools.
