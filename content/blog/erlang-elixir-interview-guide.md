---
title: "Erlang and Elixir Interview Guide"
description: "Technical interview preparation for Erlang and Elixir developer roles: the BEAM VM, actor model concurrency, OTP behaviors (GenServer, Supervisor), fault tolerance by design, Phoenix framework, and what telecom companies, real-time platforms, and functional programming shops expect."
date: "2026-03-19"
category: "Technical Skills Guides"
---

# Erlang and Elixir Interview Guide

Erlang and Elixir share the BEAM VM — a runtime designed from the ground up for distributed, fault-tolerant, concurrent systems. Erlang was created by Ericsson in the 1980s for telecommunications switching software, and its requirements shaped a language and runtime unlike anything else in mainstream use: lightweight processes in the millions, message-passing concurrency with no shared state, "let it crash" fault tolerance philosophy, and hot code reloading in production. Elixir, created by José Valim in 2012, brings a modern Rubyesque syntax and powerful metaprogramming to the same BEAM runtime, democratizing access to Erlang's strengths.

## The BEAM VM: What Makes It Different

The BEAM is not the JVM — its design priorities are different:

**Lightweight processes**: BEAM processes are not OS threads or even goroutines. They're extremely lightweight green threads — initial stack of ~2KB, isolated heap (no shared memory), garbage collected independently. Running millions of concurrent processes is normal; WhatsApp runs millions of sessions per server.

**No shared state**: BEAM processes communicate exclusively by passing messages (copying values). There's no shared memory, no mutexes, no data races. This makes concurrent programs correct by construction — the concurrency primitives eliminate a whole class of bugs.

**Preemptive scheduling**: Unlike Erlang's predecessor approaches and unlike Node.js (cooperative), the BEAM preemptively schedules processes based on reduction count. A long-running process doesn't starve other processes; the scheduler interrupts it.

**Per-process garbage collection**: Each BEAM process has its own heap and GC. GC pauses are per-process and fast (small, isolated heaps). The runtime never has a "stop-the-world" GC pause affecting all processes simultaneously — critical for latency-sensitive applications.

**Hot code reloading**: BEAM supports replacing running code without stopping the system. Erlang was designed for systems that can never go down (telephone switches). In production, a code upgrade deploys new module versions while existing processes continue with old versions and new processes get new versions.

## OTP: The Erlang Standard Library for Reliable Systems

OTP (Open Telecom Platform) is a set of libraries and design principles that are essential for Erlang/Elixir production systems:

**GenServer**: The most-used OTP behavior. A generic server process with a standard callback interface (`init/1`, `handle_call/3`, `handle_cast/2`, `handle_info/2`). `call` is synchronous (client blocks waiting for response); `cast` is asynchronous (fire and forget). GenServer abstracts away process spawn/receive patterns and handles edge cases (process linking, timeouts).

**Supervisor**: A process whose sole job is monitoring child processes and restarting them when they crash. Restart strategies: `one_for_one` (restart only the crashed child), `one_for_all` (restart all children if one crashes), `rest_for_one` (restart crashed child and all children started after it). The supervision tree is the core of Erlang's fault tolerance — crashes are expected and handled by the supervisor.

**Application**: OTP applications define the top-level supervision tree and manage dependencies between components. The `mix.exs` in Elixir projects defines the OTP application.

**GenStateMachine / :gen_statem**: For implementing explicit state machines — useful for protocol implementations, session management, and any system with clearly defined state transitions.

## Elixir-Specific Features

**Pattern matching**: Elixir's pattern matching is more powerful than most languages. Function clauses with pattern matching (`def handle({:ok, result} = msg) do ... end`), `case`, `cond`, `with` for railway-oriented programming (chaining operations that may fail).

**The pipe operator `|>`**: `data |> transform |> validate |> persist` — threads the result of each expression as the first argument to the next. The signature Elixir idiom.

**Macros and metaprogramming**: Elixir is a Lisp-style homoiconic language — code is data. Macros transform AST at compile time. Phoenix controllers, Ecto schemas, and ExUnit tests are all implemented as macros. Senior Elixir engineers understand how to write macros and when to use them (when functions aren't enough because you need compile-time transformation or custom syntax).

**Ecto**: Elixir's database library. Changesets for validating and transforming data (similar to form validation — explicit, composable, no magic). `Repo.all(from u in User, where: u.age > 18)` — SQL-like queries in Elixir with compile-time checks.

**Phoenix Framework**: The dominant Elixir web framework. Phoenix LiveView is its most distinctive feature — server-rendered real-time updates over WebSockets, without writing JavaScript for most interactive UI. Phoenix Channels for real-time communication (chat, notifications).

## Who Hires Erlang/Elixir Engineers

**Telecom and messaging**: WhatsApp (Erlang for backend infrastructure — 2 billion users), Discord (Elixir for real-time messaging infrastructure), Ericsson (Erlang home base).

**Real-time platforms**: PagerDuty, Bleacher Report (NFL, ESPN notifications), Heroku's routing layer, Brex.

**Functional programming shops**: Elixir/Erlang consultancies (DockYard, Paraxial.io), companies that value functional programming disciplines.

The BEAM engineering market is small but specialized. Engineers who deeply understand OTP patterns — supervision trees, GenServer, the let-it-crash philosophy — and can apply them to building fault-tolerant distributed systems are rare and valued in their specific market segment.
