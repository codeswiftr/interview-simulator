---
title: "Elixir and Phoenix Interview Guide: OTP, Concurrency, and Fault-Tolerant Systems"
description: "A technical guide to Elixir and Phoenix interviews — covering the OTP framework, BEAM concurrency model, GenServer patterns, LiveView architecture, and how to discuss fault tolerance in the context of distributed systems interviews."
date: "2026-03-20"
category: "Programming Languages"
---

Elixir has a devoted following among engineers who value fault tolerance, concurrency, and operational simplicity. Companies that have adopted it — Discord, Bleacher Report, PagerDuty, Heroku — tend to hire engineers who understand not just the language syntax but the OTP philosophy that makes Elixir systems uniquely reliable. Interviews at these companies dig into the BEAM runtime, supervision strategies, and why Elixir makes certain distributed systems problems easier than conventional languages.

## The BEAM and the Actor Model

Everything in Elixir runs on the BEAM virtual machine, originally designed for Erlang's telecom use cases: high concurrency, soft real-time, fault isolation. Understanding the BEAM is non-negotiable for Elixir interviews.

**Processes are lightweight:** BEAM processes are not OS threads. You can spawn millions of them with minimal memory overhead (2KB initial heap). Each process has isolated memory — no shared mutable state — and communicates only through message passing.

**Preemptive scheduling:** the BEAM scheduler is preemptive, using "reductions" (a unit of work) to time-slice CPU fairly across processes. This means a runaway computation in one process doesn't starve others — a fundamental difference from single-threaded event loops like Node.js.

**Garbage collection per process:** each process has its own heap and GC. Full-application stop-the-world GC doesn't happen. This is why Elixir systems can maintain consistent low latencies even under load.

**Immutability:** all data in Elixir is immutable. This isn't a convention — it's enforced by the runtime. Structural sharing makes immutability efficient: functions that "modify" data return new versions sharing most of the original's structure.

## OTP: The Framework That Makes Elixir Real

OTP (Open Telecom Platform) is the set of libraries and design patterns that turn Elixir processes into reliable, observable systems. Interviewers expect OTP fluency.

**GenServer:** the foundation of OTP servers. A GenServer is a process with a well-defined message protocol — synchronous `call` (request/reply) and asynchronous `cast` (fire-and-forget) — and lifecycle callbacks.

```elixir
defmodule RateLimiter do
  use GenServer
  
  def start_link(opts), do: GenServer.start_link(__MODULE__, opts, name: __MODULE__)
  
  def check_rate(key), do: GenServer.call(__MODULE__, {:check, key})
  
  @impl true
  def init(_opts), do: {:ok, %{}}
  
  @impl true
  def handle_call({:check, key}, _from, state) do
    {allowed?, new_state} = do_rate_check(key, state)
    {:reply, allowed?, new_state}
  end
  
  defp do_rate_check(key, state) do
    # sliding window implementation
    now = System.monotonic_time(:second)
    window_start = now - 60
    requests = Map.get(state, key, [])
    recent = Enum.filter(requests, &(&1 > window_start))
    if length(recent) < 100 do
      {true, Map.put(state, key, [now | recent])}
    else
      {false, Map.put(state, key, recent)}
    end
  end
end
```

**Supervisor:** supervisors watch child processes and restart them according to a configured strategy when they crash. The `one_for_one` strategy (restart only the crashed child) is the default. `one_for_all` restarts all children when any fails — useful when children are interdependent. `rest_for_one` restarts the failed child and all children started after it.

**Supervision trees:** the real power is composing supervisors hierarchically. The top-level supervisor watches mid-level supervisors, which watch workers. A crash bubbles up only if a child exceeds its restart budget within a time window — at that point, the parent restarts. This "let it crash" philosophy means you don't defensively handle every error; you design recovery strategies at the appropriate supervision level.

**ETS (Erlang Term Storage):** in-process key/value storage that's accessible across processes without copying. Used for shared read-heavy state like caches, rate limit counters, and connection pools. `ets:lookup` is O(1) and doesn't block the calling process. Know when to use ETS vs. a GenServer to hold state.

## Phoenix Framework Deep Dive

Phoenix is the dominant Elixir web framework, and Phoenix-specific interviews focus on its real-time capabilities.

**Channels:** Phoenix Channels implement a pub/sub system over WebSockets (with fallback transports). Each channel connection is a lightweight process. The architecture handles millions of concurrent connections efficiently because of the BEAM's process model — no thread-per-connection overhead.

**LiveView:** Phoenix LiveView enables server-rendered real-time UIs without JavaScript for state management. Each LiveView is a stateful process that maintains socket state, handles user events, and sends diffs to the client. The interview-relevant insight: LiveView makes real-time applications architecturally simpler by colocating state and render logic, but it introduces tradeoffs around horizontal scaling (sticky sessions or distributed state).

**Presence:** Phoenix Presence tracks which users are connected to which channels, using a CRDT-based design (CRDTs enable conflict-free distributed state merging) to avoid needing a central coordinator. It's a good example of Elixir applying distributed systems theory in a practical library.

**Ecto:** Elixir's database query and migration tool. Know the `Ecto.Changeset` pattern — validations live in changesets, not in models, separating data transformation from persistence. `Repo.transaction/1` wraps multiple operations in a database transaction.

## Distributed Elixir

**Node clustering:** Elixir nodes can form clusters using `Node.connect/1` and communicate as if local. Distributed Erlang gives you transparent message passing across nodes, which enables building distributed systems with the same programming model as single-node systems.

**Consistent hashing:** for distributing work across a cluster, libraries like `libring` implement consistent hash rings. Know when consistent hashing is appropriate (data partitioning, distributed caching) vs. simpler approaches.

**Trade-offs vs. other languages:** the interview question "why Elixir over Go or Java for this problem?" should have a precise answer. Elixir wins for: connection-heavy workloads (chat, notifications, real-time collaboration), systems where fault isolation is critical, and applications that benefit from hot code reloading without downtime. Go wins for raw compute, tight memory budgets, or teams with Go expertise. Know the strengths honestly.

## Common Interview Questions

- Explain the "let it crash" philosophy and when it's appropriate to rescue errors vs. let them propagate
- Design a distributed rate limiter using GenServers and ETS
- What happens to messages in a GenServer's mailbox when the process crashes and restarts?
- How does Phoenix LiveView handle reconnects? What happens to in-flight state?
- Implement a simple Supervisor from scratch without using `use Supervisor`

## Preparation Approach

- Build a small OTP application: a GenServer pool, a task scheduler with retries, or a real-time dashboard with Phoenix LiveView
- Read "Programming Elixir" (Dave Thomas) and "Designing Elixir Systems with OTP" (Bruce Tate)
- Study the Erlang OTP documentation on Supervisor behaviors — the original is still the best reference
- Practice explaining BEAM concurrency to someone who's only worked with threads — this tests true understanding

Elixir interviews reward engineers who've internalized the OTP mindset, not just memorized the API. The best preparation is building something real and reasoning through the failure modes you encounter.
