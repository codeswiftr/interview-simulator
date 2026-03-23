---
title: "Rust Engineering Interview Guide"
description: "Everything you need for Rust in technical interviews: ownership, borrowing, async/await, systems programming trade-offs, and when to choose Rust over Go or C++."
date: "2026-03-19"
category: "Technical Skills"
---

# Rust Engineering Interview Guide

Rust has moved from a niche systems language to a mainstream choice at companies like Discord, Cloudflare, AWS, Dropbox, and Mozilla. Senior roles at these companies now test Rust knowledge directly, and system design interviews increasingly include Rust-vs-Go-vs-C++ trade-off discussions. This guide covers what interviewers actually test when Rust comes up.

## Why Companies Interview on Rust

The adoption curve matters for understanding what interviewers expect. Companies that have rewritten performance-critical services in Rust (Discord's read states service, Cloudflare's Pingora proxy, AWS's Firecracker VMM) now have staff who interview candidates on Rust proficiency. The questions are almost never about syntax — they're about whether you understand why Rust makes certain guarantees and what those guarantees cost.

Rust appears in interviews in three contexts:

- **Systems programming roles**: Memory-safe replacements for C/C++ — embedded, OS, compiler, and runtime work
- **Performance-critical services**: Network proxies, databases, game engines, anything where GC pauses are unacceptable
- **Rewrite-from-X discussions**: "We're considering rewriting our Go service in Rust — what would we gain and lose?"

## The Ownership System: What Interviewers Test

The ownership system is the first thing interviewers probe because it's what makes Rust Rust. Every interview on Rust will involve at least one question about ownership, borrowing, or lifetimes.

### Ownership and Move Semantics

In Rust, each value has exactly one owner. When you assign a value to another variable or pass it to a function, ownership moves — the original binding becomes invalid. This eliminates use-after-free and double-free bugs at compile time.

```rust
fn process(data: Vec<i32>) -> usize {
    data.len()
}

let v = vec![1, 2, 3];
let len = process(v);  // v is moved into process
// println!("{:?}", v);  // Compile error: v was moved
```

The common interview question: "Why doesn't Rust have a garbage collector, and how does it still prevent memory leaks?" The answer is that the compiler tracks ownership statically — memory is freed when the owner goes out of scope (via `Drop`), no runtime tracking needed.

### Borrowing and the Borrow Checker

Borrowing lets you use a value without taking ownership. The borrow checker enforces two rules at compile time:

1. You can have any number of immutable references (`&T`), OR exactly one mutable reference (`&mut T`)
2. References must not outlive the value they reference (lifetimes)

```rust
fn calculate_average(numbers: &[f64]) -> f64 {
    let sum: f64 = numbers.iter().sum();
    sum / numbers.len() as f64
}

let scores = vec![85.0, 92.5, 78.0, 95.5];
let avg = calculate_average(&scores);  // Borrow, not move
println!("Scores: {:?}, Average: {}", scores, avg);  // scores still valid
```

Interviewers often ask candidates to explain a borrow checker error they've encountered, or present code that won't compile and ask why. Strong candidates explain not just the rule being violated but why the rule prevents a real class of bugs.

### Lifetimes

Lifetimes become explicit when structs hold references or functions return references derived from parameters:

```rust
struct Cache<'a> {
    data: &'a str,  // Cache cannot outlive the str it references
}

fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

The lifetime annotation `'a` tells the compiler that the returned reference lives at least as long as both inputs. Without it, the compiler can't verify the returned reference is valid. Interviewers at companies with significant Rust codebases (Cloudflare, Discord) will expect you to read and write lifetime annotations without struggling.

## Concurrency: Fearless Parallelism

Rust's concurrency model is one of its strongest selling points. The ownership system prevents data races at compile time — if you can compile concurrent Rust code, it doesn't have data races. Interviewers ask about this specifically.

### Send and Sync

These marker traits control what can be safely shared across threads:
- `Send`: A type can be moved to another thread
- `Sync`: A type can be shared (via reference) between threads

Most types are `Send + Sync` automatically. The exceptions reveal important patterns: `Rc<T>` is not `Send` (use `Arc<T>` for multi-threaded reference counting), `Cell<T>` and `RefCell<T>` are not `Sync` (interior mutability via runtime borrow checking, not safe to share).

```rust
use std::sync::{Arc, Mutex};
use std::thread;

let counter = Arc::new(Mutex::new(0));
let mut handles = vec![];

for _ in 0..10 {
    let counter = Arc::clone(&counter);
    handles.push(thread::spawn(move || {
        let mut num = counter.lock().unwrap();
        *num += 1;
    }));
}
```

## Async/Await in Rust

Rust's async model is zero-cost: futures don't allocate by default, and there's no implicit runtime. The tradeoff is that you must choose and integrate an async runtime (usually Tokio).

Interview questions often involve:
- Why is `async fn` in a trait difficult? (Object-safe traits can't have async methods without additional machinery like `async-trait`)
- What's the difference between `tokio::spawn` (spawns a task that can run on any thread) and `tokio::task::spawn_local` (keeps the task on the current thread)?
- When should you use async vs threads? (Async excels for I/O-bound concurrency with many tasks; threads are better for CPU-bound work)

## Rust vs Go vs C++: The System Design Question

System design interviews at companies evaluating Rust adoption often ask candidates to compare languages. The expected framework:

**Choose Rust when:**
- Memory safety guarantees are non-negotiable (security-critical systems, kernel space)
- GC pauses are unacceptable (real-time systems, low-latency services)
- You need C-level performance with safer abstractions
- You're writing code that will be embedded or run at the edge (no runtime overhead)

**Choose Go when:**
- You need fast developer onboarding (Go's learning curve is gentler)
- Concurrency model fits your domain (goroutines are simpler than Rust's async)
- GC pauses are acceptable (most web services)
- Compilation speed matters (Go compiles much faster than Rust)

**Choose C++ when:**
- You're extending an existing C++ codebase
- You need the full ecosystem of mature C++ libraries
- Your team already has deep C++ expertise

The honest answer: Rust has a steep learning curve (the borrow checker fights you for weeks before clicking). The benefits are substantial for certain problem domains, but it's not automatically the right choice.

## What to Study

- **The Rust Book** (`doc.rust-lang.org/book`): Still the best resource, especially chapters on ownership, lifetimes, and concurrency
- **Rustlings**: Small exercises that build muscle memory for common patterns
- **Tokio tutorial**: For async Rust specifically
- **`cargo clippy`**: The linter teaches idiomatic Rust patterns better than most documentation
- **Real codebases**: Ripgrep (rg), Servo, and Rust's standard library source are all readable and instructive

Rust interviews reward candidates who have written real Rust — not just studied it. If you haven't shipped Rust code, build a small CLI tool or HTTP service before the interview so you have genuine experience to discuss.
