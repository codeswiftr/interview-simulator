---
title: "WebAssembly in Production: An Engineer's Interview Guide"
description: "A practical guide to WebAssembly for senior engineers: WASM in production systems, Rust-to-WASM compilation, the component model, WASI, edge WASM with Fermyon and Fastly, and interview questions."
date: "2026-03-20"
category: "Technical Skills Guides"
---

# WebAssembly in Production: An Engineer's Interview Guide

WebAssembly has crossed the line from browser curiosity to serious production infrastructure. Compute at the edge, portable plugin systems, sandboxed untrusted code execution — WASM is now relevant beyond front-end performance optimization. If you're interviewing at companies working on edge compute, platform engineering, or polyglot runtime environments, expect WASM questions. This guide covers the production realities, not just the hello-world basics.

## WASM in Production Systems: Where It Actually Gets Used

The most impactful production use cases for WASM today fall into three categories:

**Edge compute**: Companies like Fastly (Compute@Edge) and Cloudflare (Workers) allow you to deploy WASM modules that run at network edge nodes globally. The pitch is latency: code running 20ms from the user instead of 80ms from a central data center. WASM's deterministic startup time (microseconds, not milliseconds like a container) is what makes this feasible — you can cold-start a WASM module per HTTP request without noticeable overhead.

**Plugin and extension systems**: Envoy proxy uses WASM for filter extensions. Zellij (a terminal multiplexer) uses WASM for plugins. The advantage over native plugins: WASM modules run in a sandbox — a buggy or malicious plugin can't corrupt the host process's memory or make arbitrary syscalls. This is replacing the old pattern of dynamically loaded `.so` files, which provided no isolation.

**Portable compute**: tools like Spin (from Fermyon) let you write HTTP handlers in Rust, Go, or Python, compile to WASM, and run them on any WASM runtime without targeting a specific OS or CPU architecture. The promise is similar to containers but with a smaller footprint and no Linux kernel requirement.

In interviews, the question "when would you use WASM over a container?" has a sharp answer: when you need sub-millisecond cold starts, when you need strong sandboxing without Linux namespaces, or when you need to run untrusted third-party code inside your process boundary.

## Rust-to-WASM Compilation Pipeline

Rust is the dominant language for production WASM for two reasons: it has no garbage collector (which causes unpredictable pause times), and its zero-cost abstractions produce compact, fast WASM modules.

The compilation target for browser WASM is `wasm32-unknown-unknown`. For WASI-based runtimes (Wasmtime, WasmEdge, etc.), it's `wasm32-wasip1` (formerly `wasm32-wasi`). Add the target with `rustup target add wasm32-wasip1`, then build with `cargo build --target wasm32-wasip1 --release`.

Key tooling:
- **`wasm-bindgen`**: generates JavaScript glue code for browser-facing WASM, handling type conversions between JS and Rust
- **`wasm-pack`**: packages Rust-compiled WASM for npm distribution
- **`wasm-opt`** (from Binaryen): post-processes WASM binaries to reduce size and improve performance — typically reduces binary size by 20–40%
- **`cargo component`**: the emerging tool for building WASM Component Model components

Binary size is a real concern. A debug build of even a simple Rust WASM module can be several MB. Release builds with `opt-level = "z"` and LTO enabled typically come in under 200KB for realistic modules. Use `wasm-opt -Oz` as a post-build step.

## The Component Model and WASI

The **WASM Component Model** (standardized as part of WASI 0.2) is the most important recent development in the WASM ecosystem. Before the component model, WASM modules could only exchange integers and floats across module boundaries — composing WASM components required complex glue code. The component model introduces **WIT (WASM Interface Types)**, a language for declaring interfaces that can be implemented and consumed by WASM modules regardless of their source language.

This means a component written in Rust can call an interface implemented in Go or Python, with the runtime handling the ABI translation. This is the foundation of true polyglot plugin systems.

**WASI (WebAssembly System Interface)** defines the standard syscall layer for non-browser WASM. WASI 0.1 (Preview 1) provided basic POSIX-like capabilities: filesystem access, environment variables, clocks, and random numbers. WASI 0.2 (Preview 2, released in early 2024) is built on the component model and adds: HTTP requests/responses (via `wasi:http`), sockets, key-value stores, and messaging — all as capability-based interfaces. This is what enables Spin and similar frameworks to offer full HTTP server functionality without OS-level networking code in the module.

The capability model is significant for security: a WASM module only has access to the capabilities explicitly granted by the host. A module with no filesystem capability literally cannot access files, regardless of what the code attempts. This is a stronger guarantee than container-based isolation.

## Edge WASM: Fermyon Spin and Fastly Compute

**Fermyon Spin** is an open-source framework for building edge applications on WASM. A Spin application is a set of WASM components with a `spin.toml` manifest that maps HTTP routes to component handlers. Spin handles the WASM runtime (Wasmtime), the HTTP server, and optional infrastructure (key-value store, SQLite, Redis). You deploy to Fermyon Cloud or self-host with `spin up`.

The development workflow: write a handler function, compile to WASM component, define the route in `spin.toml`, test locally with `spin up`. The same binary deploys to development and production — no containers, no Dockerfiles.

**Fastly Compute** is a CDN-integrated edge compute platform that runs WASM at Fastly's 70+ PoPs. The Rust SDK provides APIs for HTTP request/response manipulation, KV store access, and backend calls. Use cases include: auth token validation at the edge, A/B testing without origin round trips, geographic request routing, and request transformation/enrichment.

The key difference from Cloudflare Workers (which uses V8 isolates for JavaScript/WASM): Fastly Compute uses a purpose-built WASM runtime with stricter sandboxing and lower overhead, at the cost of less flexible language support.

## Interview Questions for WASM-Focused Roles

Roles at companies building on WASM (edge compute platforms, plugin infrastructure, portable runtimes) will probe both breadth and depth. Expect:

**Conceptual**: "What guarantees does WASM provide about memory safety? What doesn't it guarantee?" (Answer: linear memory model prevents out-of-bounds into other modules' memory; doesn't prevent logic bugs, infinite loops, or excessive memory allocation.)

**Architecture**: "You need to let customers run custom code in your SaaS platform. When would you choose WASM over containers? What are the tradeoffs?" (WASM: microsecond cold start, in-process isolation, smaller attack surface, no OS image needed. Containers: broader language support, existing tooling, ability to run long-lived processes.)

**Practical**: "How do you pass a complex data structure (like a JSON object) between a Rust WASM module and a JavaScript host?" (Answer: serialize to a byte buffer, pass the pointer and length across the WASM boundary, deserialize in the host. Or use `wasm-bindgen` which handles this automatically for JS targets. With the component model and WIT, structured types can be passed directly.)

**Debugging**: "Your WASM module is running correctly in local Wasmtime but failing on the edge runtime. How do you debug it?" (Check WASI capability grants, check for non-determinism (clocks, random), check for stack size limits, use `wasm-opt --debuginfo` to preserve source maps, compare runtime versions.)

Demonstrating that you understand both the exciting possibilities (edge compute, polyglot composition) and the real limitations (no threads without shared memory extension, limited ecosystem compared to native, debugging complexity) signals the kind of grounded engineering judgment that hiring teams want.
