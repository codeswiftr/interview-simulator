---
title: "Elixir Engineering Interview Guide"
description: "Technical interview preparation for Elixir roles: OTP concurrency, the Actor model with GenServer, Phoenix LiveView, fault tolerance, and what companies hiring Elixir engineers actually test."
date: "2026-03-19"
category: "Technical Skills Guides"
---

# Elixir Engineering Interview Guide

Elixir is a niche language that attracts strong engineers for specific reasons: fault-tolerant distributed systems, real-time features with Phoenix LiveView, and the OTP supervision tree model. Companies that use Elixir tend to use it deliberately — and they interview for depth in the language's distinctive features. If you're interviewing for an Elixir role, generic programming knowledge isn't enough.

## Where Elixir Is Used in Production

Elixir's production footprint: Discord (handles millions of concurrent users), Bleacher Report (live sports updates), Brex (financial infrastructure for some services), PagerDuty, Heroku (routing mesh), WhatsApp (Erlang, which Elixir runs on). The BEAM VM — Elixir's runtime — is the same VM that powers Erlang, which has decades of production use in telecom.

Companies hiring Elixir engineers: Discord, Fly.io, Supabase (Elixir-heavy realtime server), remote-first startups building communication/collaboration tools, and companies with real-time requirements (notifications, chat, live dashboards).

## The BEAM and Concurrency Model

The fundamental concept that differentiates Elixir from most languages: the Actor model with lightweight processes.

BEAM processes are not OS threads. They're managed by the BEAM runtime, extremely cheap to spawn (microseconds, kilobytes of memory), and isolated — a crash in one process doesn't affect others. A production Elixir system might have millions of processes.

**Message passing**: processes communicate by sending messages. No shared memory. This eliminates entire categories of concurrency bugs (race conditions, deadlocks around shared state).

**Supervision trees**: OTP's killer feature. You define a tree of supervisors and workers. When a worker crashes, its supervisor restarts it (with configurable strategies: one_for_one, one_for_all, rest_for_one). The philosophy: "let it crash." Rather than defensive error handling at every function call, you handle errors at the supervision boundary. Build systems that recover from failure, not systems that try to prevent every failure.

Interview question: "Describe the difference between one_for_one and one_for_all supervision strategies." You need to know: one_for_one restarts only the crashed child; one_for_all restarts all children when any crashes (for children that depend on each other).

## GenServer: The Core Pattern

`GenServer` is the generic server behavior that most Elixir server-side code builds on. Know it cold:

```elixir
defmodule MyCache do
  use GenServer

  # Client API
  def start_link(opts), do: GenServer.start_link(__MODULE__, %{}, opts)
  def get(pid, key), do: GenServer.call(pid, {:get, key})
  def put(pid, key, value), do: GenServer.cast(pid, {:put, key, value})

  # Server callbacks
  def init(state), do: {:ok, state}
  def handle_call({:get, key}, _from, state), do: {:reply, Map.get(state, key), state}
  def handle_cast({:put, key, value}, state), do: {:noreply, Map.put(state, key, value)}
end
```

The `call`/`cast` distinction matters: `call` is synchronous (caller blocks waiting for reply), `cast` is fire-and-forget. Interviewers ask about this in the context of back-pressure and system design.

Also know `handle_info/2` — handles arbitrary messages to the process (timers, messages from other processes that aren't call/cast).

## Functional Programming in Elixir

Elixir is functional: immutable data structures, pure functions, no side effects in business logic. Pattern matching is pervasive:

```elixir
def process({:ok, result}), do: handle_success(result)
def process({:error, reason}), do: handle_error(reason)
```

The pipe operator (`|>`) is Elixir's distinctive ergonomic feature — passing the result of one function as the first argument to the next:

```elixir
users
|> Enum.filter(&(&1.active))
|> Enum.map(&(&1.email))
|> Enum.sort()
```

Interview coding questions often involve Enum and Stream. Know the difference: Enum is eager (processes the entire collection), Stream is lazy (computes elements on demand). For large collections, Stream avoids building intermediate lists.

## Phoenix and LiveView

For web-focused Elixir roles, Phoenix LiveView is the key differentiator. LiveView enables real-time, server-rendered web UIs without writing JavaScript — the server pushes diffs to the client over WebSocket.

Know: the LiveView lifecycle (mount → render → handle_event → handle_info), stateful connections (each LiveView process is a GenServer), the tradeoffs (server-side state, WebSocket latency, not right for every use case).

## ETS and Distributed State

ETS (Erlang Term Storage): in-memory key-value store within a node, accessible by multiple processes. Faster than a GenServer for read-heavy caches. For distributed state across nodes, mnesia (the distributed DB built into Erlang/OTP) or external databases.

Interview question: "When would you use ETS vs. a GenServer for caching?" ETS wins on read performance (processes can read concurrently without message passing); GenServer wins when you need complex state management or serialized writes with side effects.

## How to Prepare

The canonical Elixir preparation path: "Programming Elixir" (Dave Thomas), "Designing Elixir Systems with OTP" (Bruce Tate and James Gray), and the official HexDocs for GenServer, Supervisor, and Phoenix.

Build something with OTP supervision trees — a distributed counter, a rate limiter, a simple pubsub. Elixir interview depth is real: the companies that choose it care enough to test whether you understand why, not just how.
