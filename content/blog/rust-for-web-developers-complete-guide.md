---
title: "Rust for Web Developers: A Complete Guide"
description: "How web developers can learn Rust for backend services—ownership, borrowing, async Rust with Tokio, web frameworks like Axum, and how to think about Rust performance for production APIs."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Rust for Web Developers: A Complete Guide

Rust is increasingly used for backend web services, especially where performance, safety, or reliability are paramount. Companies like Cloudflare, Discord, AWS, and 1Password use Rust in production. For web developers familiar with Python, Node.js, or Go, the transition to Rust is steep but the payoff is substantial.

## Why Rust for Web Services

**Memory safety without garbage collection**: Rust's ownership system prevents memory leaks, use-after-free bugs, and data races at compile time. You get the performance of C/C++ with the safety of GC languages.

**Predictable performance**: No GC pauses. Request latencies are consistent. Discord famously moved their member count service from Go to Rust and saw P99 latency drop from 500ms to < 1ms, eliminating GC-related spikes.

**Fearless concurrency**: The borrow checker prevents data races. Async Rust with Tokio is production-grade for high-concurrency services.

## The Ownership Model (What You Must Internalize)

Ownership is Rust's most distinctive feature and the steepest learning curve for web developers:

```rust
fn main() {
    let s1 = String::from("hello");
    let s2 = s1; // s1 is moved — ownership transferred to s2
    // println!("{}", s1); // COMPILE ERROR: s1 was moved
    println!("{}", s2); // OK
}
```

Rules:
1. Each value has exactly one owner
2. When the owner goes out of scope, the value is dropped
3. You can borrow a reference (`&T`) without transferring ownership

```rust
fn print_length(s: &String) { // borrows, doesn't own
    println!("Length: {}", s.len());
} // s goes out of scope, but the String it points to is NOT dropped

fn main() {
    let s = String::from("hello");
    print_length(&s); // borrow
    println!("{}", s); // s still valid
}
```

## Async Rust with Tokio

Modern Rust web services use async/await with the Tokio runtime:

```rust
use tokio;

#[tokio::main]
async fn main() {
    let result = fetch_data().await;
    println!("{}", result);
}

async fn fetch_data() -> String {
    // async operations here
    tokio::time::sleep(std::time::Duration::from_millis(100)).await;
    String::from("data")
}
```

The `async` keyword returns a Future. `.await` polls the Future to completion. Tokio's runtime schedules multiple async tasks on a thread pool efficiently.

## Axum: The Recommended Web Framework

Axum (from the Tokio team) is the leading Rust web framework in 2026:

```rust
use axum::{
    routing::{get, post},
    Router, Json, extract::Path,
    http::StatusCode,
};
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
struct User {
    id: u64,
    name: String,
}

#[derive(Deserialize)]
struct CreateUser {
    name: String,
}

async fn get_user(Path(id): Path<u64>) -> Json<User> {
    Json(User { id, name: format!("User {}", id) })
}

async fn create_user(Json(payload): Json<CreateUser>) -> (StatusCode, Json<User>) {
    let user = User { id: 1, name: payload.name };
    (StatusCode::CREATED, Json(user))
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/users/:id", get(get_user))
        .route("/users", post(create_user));

    axum::Server::bind(&"0.0.0.0:3000".parse().unwrap())
        .serve(app.into_make_service())
        .await
        .unwrap();
}
```

## Error Handling with Result

Rust doesn't have exceptions. Errors are values:

```rust
use std::num::ParseIntError;

fn parse_port(s: &str) -> Result<u16, ParseIntError> {
    s.parse::<u16>()
}

match parse_port("8080") {
    Ok(port) => println!("Port: {}", port),
    Err(e) => println!("Error: {}", e),
}

// Or use ? operator to propagate errors
fn get_port() -> Result<u16, ParseIntError> {
    let port = "8080".parse::<u16>()?;  // returns Err if parsing fails
    Ok(port)
}
```

In web handlers, use `anyhow` or `thiserror` crates for ergonomic error handling.

## Database Access with SQLx

SQLx is the standard for database access in Rust—compile-time checked queries:

```rust
use sqlx::PgPool;

#[derive(sqlx::FromRow)]
struct User {
    id: i64,
    name: String,
    email: String,
}

async fn get_user(pool: &PgPool, id: i64) -> Result<User, sqlx::Error> {
    sqlx::query_as!(User,
        "SELECT id, name, email FROM users WHERE id = $1",
        id
    )
    .fetch_one(pool)
    .await
}
```

The `query_as!` macro verifies the SQL against your actual database schema at compile time. Typos in column names are compile errors, not runtime panics.

## Performance Characteristics

What you get with Rust for web services:
- Startup time: < 10ms (vs seconds for JVM)
- Memory: 20-50MB for a web service (vs 200-500MB for JVM)
- P99 latency: extremely consistent without GC pauses
- Throughput: competitive with Go, often faster than Node.js

The Techempower benchmarks consistently rank Axum and Actix-web in the top 5 frameworks globally.

## Interview Tips

When discussing Rust in interviews:
1. Ownership and borrowing are the key concepts — explain them clearly
2. Async Rust with Tokio for concurrency
3. Why Rust vs Go: when predictable latency matters more than ergonomics
4. Real production use cases: Cloudflare Workers, Discord, AWS Lambda extensions
5. The compile-time safety guarantees are the core value proposition
