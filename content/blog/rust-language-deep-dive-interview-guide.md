---
title: "Rust Language Deep Dive Interview Guide"
description: "Advanced Rust interview preparation: ownership and borrowing in depth, lifetimes, async/await with Tokio, unsafe Rust, and what systems companies like Cloudflare, Discord, Amazon, and blockchain companies expect from senior Rust engineers."
date: "2026-03-19"
category: "Technical Skills Guides"
---

Senior Rust interviews are unlike any other language interview. The questions are not trivia — they probe whether you have genuinely internalized the ownership model, or whether you are fighting it. This guide covers the concepts that separate candidates who have used Rust from candidates who understand it.

## Ownership: Move Semantics, Copy, and the Borrow Checker

Rust's ownership model is the language's central feature. Every value has exactly one owner. When ownership is transferred (moved), the original binding becomes invalid. This is not a runtime check — it is enforced at compile time by the borrow checker.

**Move vs. Copy:** Types that implement the `Copy` trait (integers, booleans, `f64`, tuples of Copy types) are duplicated on assignment. Types that do not implement `Copy` — `String`, `Vec<T>`, `Box<T>`, most structs — are moved. After a move, the original variable cannot be used.

**Why this exists:** Memory safety without a garbage collector. In C and C++, use-after-free, double-free, and dangling pointers are among the most exploited vulnerability classes. The borrow checker eliminates them by construction. There is no runtime overhead; all checks are compile-time.

**Common patterns that fight the borrow checker:**

- Trying to mutate a collection while iterating over it. Solution: collect indices first, then mutate.
- Holding a mutable borrow and then passing the value to a function that also wants a reference. Solution: restructure scope so borrows do not overlap.
- Self-referential structs where a field holds a reference to another field. Solution: use `Pin`, `Rc<RefCell<T>>`, or redesign the data structure.
- Shared mutable state across threads. Rust forces you to use `Arc<Mutex<T>>` or channels — the compiler will not let you share `&mut T` across thread boundaries.

## Lifetimes

Lifetimes express how long references are valid. They are not runtime values — they are annotations the compiler uses to verify that references do not outlive the data they point to.

**Lifetime elision:** In many common cases, the compiler infers lifetimes without you writing them. The three elision rules cover: each input reference gets its own lifetime; if there is exactly one input reference, the output lifetime matches it; if one of the inputs is `&self` or `&mut self`, the output lifetime matches `self`.

**Named lifetimes:** You need to write them when the compiler cannot infer the relationship. The canonical example is a function that takes two string slices and returns the longer one — the compiler needs to know the returned reference lives as long as the shorter of the two inputs.

```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

**`'static`:** The special lifetime that lasts for the entire program. String literals are `'static`. Thread-spawned closures often require `'static` bounds because the thread may outlive the current scope.

Interviewers at systems companies will ask you to read a function signature with lifetimes and explain what the relationship means. Practice reading them aloud.

## Traits as the Abstraction Mechanism

Traits are Rust's equivalent of interfaces, but more powerful. They define behavior; types implement them.

**`impl Trait` vs. `dyn Trait`:** `impl Trait` in a function argument position is syntactic sugar for a generic — monomorphized at compile time, zero overhead, but the concrete type must be known. `dyn Trait` is a trait object — a fat pointer (data pointer + vtable pointer), dispatched at runtime. Use `dyn Trait` when you need heterogeneous collections or when monomorphization would be inappropriate.

**Orphan rules:** You can implement a trait for a type only if either the trait or the type is defined in your crate. This prevents conflicting implementations across crates.

**Standard traits to know cold:**

- `Clone` / `Copy` — duplication semantics
- `Display` / `Debug` — formatting for end users vs. developers
- `Iterator` — the most powerful trait in the standard library; implementing `next()` gives you `map`, `filter`, `fold`, `collect`, and dozens of other adapters for free
- `From` / `Into` — infallible type conversions; implementing `From<A> for B` gives you `Into<B> for A` automatically
- `Error` — required to use `?` with custom error types; requires `Display` and `Debug`

## Async/Await with Tokio

Rust's async model is poll-based. An `async fn` returns a `Future`. A future does nothing until it is polled by an executor. `await` suspends the current future and yields control back to the executor until the awaited future is ready.

**Tokio's runtime** is the dominant executor. It runs a thread pool and schedules futures across threads. `tokio::spawn` creates a new task (a lightweight, non-blocking green thread). `tokio::task::spawn_blocking` moves blocking work onto a dedicated thread pool to avoid stalling the async executor.

**Common async pitfalls:**

- **Holding a `Mutex` lock across an `.await` point.** If a future is suspended while holding a lock, other tasks cannot acquire it, causing deadlocks or starvation. Use `tokio::sync::Mutex` for async-aware locking, or restructure to drop the lock before awaiting.
- **Calling blocking code in an async context.** `std::thread::sleep`, synchronous file I/O, and CPU-heavy computation block the executor thread. Wrap them with `spawn_blocking`.
- **Cancellation.** Dropping a future cancels it. If a future performs a multi-step operation, cancellation mid-way can leave state inconsistent. Design for cancellation or use `tokio::select!` carefully.

## Error Handling Patterns

Rust has no exceptions. Errors are values.

**`Result<T, E>` and `Option<T>`** are the primitives. The `?` operator propagates errors up the call stack — it is syntactic sugar for early return on `Err` or `None`, with an implicit `From` conversion on the error type.

**`thiserror` vs. `anyhow`:** `thiserror` is for library crates. It derives `Error` implementations from enums, producing strongly-typed errors that callers can match on. `anyhow` is for application code. It erases error types into a single `anyhow::Error`, making it trivial to propagate any error with context, but callers cannot programmatically distinguish error variants.

A senior candidate knows which to use when and why mixing `anyhow` into a library API is a design mistake.

## When to Use `unsafe`

`unsafe` does not disable the borrow checker — it unlocks four additional capabilities: dereferencing raw pointers, calling unsafe functions, implementing unsafe traits, and accessing mutable statics.

**Legitimate uses:**

- **FFI.** Calling C functions is inherently unsafe because Rust cannot verify C's memory semantics.
- **Performance-critical data structures.** `Vec<T>` itself uses `unsafe` internally to manage heap memory that the borrow checker cannot model.
- **Implementing invariants the compiler cannot verify.** A lock-free ring buffer, SIMD intrinsics, or zero-copy parsing from raw bytes.

**What interviewers look for:** They want to see that you treat `unsafe` as a last resort, that you can articulate exactly which invariant you are upholding manually, and that you know how to minimize the unsafe surface area by wrapping it in a safe abstraction.

## Companies Hiring Senior Rust Engineers and What They Test

- **Cloudflare** — network-level systems, Pingora (their Nginx replacement), Workers runtime. Expect questions on async networking, zero-copy buffer management, and performance profiling.
- **Discord** — moved their read-states service from Go to Rust for latency reasons. Tests on concurrent data structures, `tokio`, and memory layout.
- **Amazon / AWS** — Firecracker (VMM written in Rust), s2n-tls. Tests on unsafe Rust, FFI, and systems-level correctness.
- **Blockchain companies (Solana, Polkadot, Near)** — smart contract runtimes, BPF/Wasm compilation targets. Expect deep ownership questions, `no_std` environments, and deterministic execution constraints.
- **Startups in databases, observability, and security** — ClickHouse contributors, Databend, DataFusion. Tests on iterator chains, custom allocators, and tight performance loops.

Across all of these, the interview pattern is the same: write a function with a non-trivial ownership constraint and fix a set of compiler errors. Candidates who understand why the borrow checker rejects code — not just how to silence it — are the ones who pass.
