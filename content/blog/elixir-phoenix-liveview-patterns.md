---
title: "Elixir Phoenix LiveView: Production Patterns"
description: "How to build real-time web applications with Phoenix LiveView—the programming model, stateful processes, PubSub for multi-node broadcasts, and why the actor model makes concurrency simple."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Elixir Phoenix LiveView: Production Patterns

Phoenix LiveView enables rich, real-time web experiences without writing JavaScript for state management. Server-rendered HTML is pushed to the client over a persistent WebSocket connection, updating only the changed parts. For applications where real-time is a first-class requirement—dashboards, collaboration tools, live data feeds—LiveView is a remarkably elegant solution.

## The Actor Model Foundation

Elixir is built on the Erlang virtual machine (BEAM), which implements the actor model. Each process is lightweight (~2KB), isolated, and communicates via message passing. A Phoenix LiveView is a process:

```elixir
defmodule MyAppWeb.CounterLive do
  use Phoenix.LiveView

  # State is initialized here
  def mount(_params, _session, socket) do
    {:ok, assign(socket, count: 0)}
  end

  # Template renders from socket assigns
  def render(assigns) do
    ~H"""
    <div>
      <p>Count: <%= @count %></p>
      <button phx-click="increment">+</button>
    </div>
    """
  end

  # Event handlers update state
  def handle_event("increment", _params, socket) do
    {:noreply, update(socket, :count, &(&1 + 1))}
  end
end
```

Each connected user gets their own LiveView process. Millions of concurrent connections become millions of lightweight BEAM processes.

## LiveView vs JavaScript SPA

What makes LiveView distinctive:

- State lives on the server (in the LiveView process)
- Client sends DOM events, server sends diffs
- No client-side state management (no Redux, Zustand, etc.)
- Forms work without JavaScript (progressive enhancement)

The tradeoff: requires a persistent WebSocket connection. Not suitable for offline-first apps. Well-suited for dashboards, admin interfaces, collaboration tools.

## PubSub for Multi-Node Real-Time

For broadcasting to multiple users, use Phoenix.PubSub:

```elixir
# Publisher (e.g., a background job or other LiveView)
Phoenix.PubSub.broadcast(MyApp.PubSub, "room:lobby", {:new_message, message})

# Subscriber (in your LiveView)
defmodule MyAppWeb.ChatLive do
  use Phoenix.LiveView

  def mount(%{"room" => room_id}, _session, socket) do
    Phoenix.PubSub.subscribe(MyApp.PubSub, "room:#{room_id}")
    {:ok, assign(socket, messages: load_messages(room_id))}
  end

  def handle_info({:new_message, message}, socket) do
    # Automatically pushed to client
    {:noreply, update(socket, :messages, &[message | &1])}
  end
end
```

PubSub distributes across nodes in a cluster automatically.

## LiveComponents for Reusability

```elixir
defmodule MyAppWeb.UserCardComponent do
  use Phoenix.LiveComponent

  def render(assigns) do
    ~H"""
    <div id={"user-#{@user.id}"}>
      <h3><%= @user.name %></h3>
      <button phx-click="follow" phx-target={@myself}>Follow</button>
    </div>
    """
  end

  def handle_event("follow", _params, socket) do
    # Handle event within component
    {:noreply, socket}
  end
end
```

```heex
<!-- Using the component -->
<.live_component module={MyAppWeb.UserCardComponent} id={@user.id} user={@user} />
```

## Database Interaction Patterns

Use Ecto (Elixir's database library) with changeset-based validation:

```elixir
defmodule MyAppWeb.UserFormLive do
  use Phoenix.LiveView
  alias MyApp.Accounts

  def mount(_params, _session, socket) do
    changeset = Accounts.change_user(%User{})
    {:ok, assign(socket, changeset: changeset)}
  end

  def handle_event("validate", %{"user" => params}, socket) do
    changeset = Accounts.change_user(%User{}, params) |> Map.put(:action, :validate)
    {:noreply, assign(socket, changeset: changeset)}
  end

  def handle_event("save", %{"user" => params}, socket) do
    case Accounts.create_user(params) do
      {:ok, user} ->
        {:noreply, push_navigate(socket, to: "/users/#{user.id}")}
      {:error, changeset} ->
        {:noreply, assign(socket, changeset: changeset)}
    end
  end
end
```

Validation runs on the server with each input change, displayed via LiveView diffs.

## Presence for User State

Phoenix Presence tracks who is online across a cluster:

```elixir
# Track user presence in a room
Phoenix.Presence.track(self(), "room:lobby", user.id, %{
    username: user.username,
    joined_at: DateTime.utc_now()
})

# Subscribe to presence changes
def handle_info(%Phoenix.Socket.Broadcast{event: "presence_diff"}, socket) do
    users = Phoenix.Presence.list("room:lobby")
    {:noreply, assign(socket, online_users: users)}
end
```

## Performance at Scale

Elixir/BEAM performance characteristics:

- **2M+ concurrent connections** on a single server (WhatsApp ran on BEAM with 2M connections per server)
- **Fault tolerance**: Supervisors restart crashed processes automatically
- **Hot code upgrades**: Deploy without downtime (unique to BEAM)
- **Soft real-time**: Garbage collected per-process, not globally—no GC pauses affecting all users

## Interview Tips

Elixir/Phoenix questions test understanding of alternative paradigms:

1. **Actor model** — how processes communicate, why isolation matters
2. **LiveView vs SPA** — when server-state wins, the tradeoffs
3. **PubSub broadcasting** — how multi-node real-time works
4. **Fault tolerance** — supervisor trees, process restart strategies
5. **When to choose Elixir** — real-time features, concurrent connections, distributed systems

The interview insight: Elixir's concurrency model (actor model vs shared memory) is a fundamentally different approach to concurrency. Understanding it demonstrates breadth beyond mainstream runtimes.
