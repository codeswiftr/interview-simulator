---
title: "Brex Engineering Deep Dive: Corporate Cards and Spend Management at Scale"
date: "2024-01-22"
author: "Interview Simulator Team"
tags: ["brex", "fintech", "elixir", "real-time-systems", "data-engineering", "engineering"]
description: "How Brex processes card authorizations in under 150ms, migrated from Ruby to Elixir for concurrency, and built a modern spend analytics platform — and what it means for your Brex engineering interview."
---

# Brex Engineering Deep Dive: Corporate Cards and Spend Management at Scale

Brex launched in 2017 with a proposition that seemed almost impossible: corporate credit cards for startups with no personal guarantee. Traditional corporate card underwriting relies on a founder's personal credit score. Brex instead underwrites the business in real time based on cash balance — specifically, the balance in the company's connected bank account. That single product decision created a set of technical requirements that shaped their entire engineering organization.

## The Real-Time Underwriting Model

Traditional credit underwriting is a batch process. An analyst reviews financials, assigns a credit limit, and the limit is static until the next review cycle. Brex's model is continuous. When a card authorization comes in, Brex needs to answer two questions simultaneously:

1. Does the company currently have enough cash to cover this charge?
2. Is this transaction consistent with the company's spending patterns?

Both questions must be answered before the card network times out — Visa and Mastercard give issuers roughly 150 milliseconds to respond to an authorization request. Miss that window and the transaction is declined by default.

This is a hard real-time constraint in the computer science sense. The 150ms budget includes network round trips to Brex's infrastructure, database reads, fraud scoring, and the response back to the network. In practice, Brex targets sub-100ms for the authorization decision itself to leave headroom for network variance.

## The Ruby to Elixir Migration

When Brex launched, they built on Ruby on Rails — a pragmatic choice for moving fast. Ruby is synchronous and single-threaded at the request level. Under load, the threading model (relying on Ruby's GIL or multi-process forking) becomes a bottleneck for high-concurrency workloads.

Card authorization is exactly that workload. Every in-flight card transaction is a concurrent process: receive the authorization request, load account state, evaluate the limit, respond, and then reconcile the posted transaction when it clears. With thousands of cards in active use, the number of concurrent authorization checks can spike dramatically during business hours.

Brex migrated the authorization pipeline to **Elixir**, which runs on the BEAM virtual machine — the same runtime as Erlang, purpose-built for massive concurrency. The actor model maps cleanly onto the authorization problem:

- Each card account has a lightweight Elixir process (an OTP GenServer) maintaining in-memory state
- Authorization requests are messages sent to that process
- The process handles requests sequentially per account, which provides natural serialization without database-level locking
- BEAM schedules millions of these processes across available CPU cores with microsecond-level preemption

The result is that Brex can process tens of thousands of concurrent authorization checks with predictable sub-millisecond per-process latency, because no process blocks waiting for another.

## Real-Time Credit Limit Enforcement

Here is a simplified model of how Brex enforces credit limits during authorization. The key design decision is separating the **available credit calculation** from the **authorization decision** — and making both fast enough to fit within the card network's timeout.

```elixir
defmodule Brex.Authorization.LimitEnforcer do
  use GenServer
  require Logger

  @authorization_timeout_ms 100

  # Each account has one running instance of this GenServer.
  # State is kept in memory and refreshed from the database on startup
  # or after a configurable TTL.
  defmodule AccountState do
    defstruct [
      :account_id,
      :credit_limit,        # Hard limit set during underwriting
      :cash_balance,        # Last known bank balance (refreshed async)
      :pending_charges,     # Sum of authorized but not yet posted charges
      :posted_today,        # Sum of cleared charges in current billing period
      :last_refreshed_at
    ]
  end

  def authorize(account_id, amount_cents, merchant_mcc) do
    # Send a synchronous message to the account's GenServer.
    # Times out before the card network deadline.
    GenServer.call(
      via_registry(account_id),
      {:authorize, amount_cents, merchant_mcc},
      @authorization_timeout_ms
    )
  end

  def handle_call({:authorize, amount_cents, merchant_mcc}, _from, state) do
    case evaluate_authorization(state, amount_cents, merchant_mcc) do
      {:approved, reason} ->
        new_state = %{state |
          pending_charges: state.pending_charges + amount_cents
        }
        Logger.info("Auth approved",
          account: state.account_id,
          amount: amount_cents,
          reason: reason
        )
        {:reply, {:approved, authorization_code()}, new_state}

      {:declined, reason} ->
        Logger.info("Auth declined",
          account: state.account_id,
          amount: amount_cents,
          reason: reason
        )
        {:reply, {:declined, reason}, state}
    end
  end

  defp evaluate_authorization(state, amount_cents, merchant_mcc) do
    available = available_credit(state)

    cond do
      stale_balance?(state) ->
        # If our cash balance data is too old, decline conservatively
        # rather than risk approving a transaction the account can't cover.
        {:declined, :balance_data_stale}

      amount_cents > available ->
        {:declined, :insufficient_credit}

      blocked_merchant_category?(merchant_mcc, state.account_id) ->
        {:declined, :merchant_category_blocked}

      true ->
        {:approved, :within_limit}
    end
  end

  defp available_credit(%AccountState{} = state) do
    # Brex's dynamic limit: the lesser of the assigned credit limit
    # or a percentage of the current cash balance, minus pending charges
    # and amounts already posted this period.
    dynamic_limit = min(
      state.credit_limit,
      floor(state.cash_balance * 0.8)  # 80% of cash as a conservative buffer
    )

    max(0, dynamic_limit - state.pending_charges - state.posted_today)
  end

  defp stale_balance?(%AccountState{last_refreshed_at: refreshed}) do
    DateTime.diff(DateTime.utc_now(), refreshed, :second) > 300
  end

  defp via_registry(account_id) do
    {:via, Registry, {Brex.AccountRegistry, account_id}}
  end

  defp authorization_code do
    :crypto.strong_rand_bytes(6) |> Base.encode16()
  end
end
```

A few things worth noting in this design:

**Optimistic in-memory state.** The GenServer holds credit state in memory and updates it synchronously when authorizations are approved. Posted transactions (cleared charges) arrive asynchronously from the card network and are handled via a separate message. This means the in-memory state can be slightly ahead of the database — a deliberate tradeoff for latency.

**Stale balance protection.** If the bank balance data is older than 5 minutes, the system declines rather than potentially approving a transaction the company can't cover. This conservative fallback trades some approval rate for financial safety.

**No database write on the authorization hot path.** The authorization decision itself does not write to the database. The write happens asynchronously after the response is sent to the card network. This is safe because the state is held in a single process per account (no concurrent mutations), and the BEAM process is durable within the lifetime of the node.

## The Data Platform: Snowflake and dbt

Brex's spend management product — the dashboards, budget tracking, and analytics that finance teams use — runs on a completely different data stack from the real-time authorization pipeline. This is a deliberate architectural separation: OLTP (authorizations, account state) is separate from OLAP (analytics, reporting).

The analytics platform is built on Snowflake as the data warehouse, with dbt (data build tool) managing transformation logic. The raw event stream from the authorization pipeline flows into Snowflake via a Kafka-based CDC (change data capture) pipeline. dbt models then transform raw events into business-layer tables: spend by category, spend by department, budget utilization, merchant analysis.

This architecture gives Brex a clean boundary between:

- **Freshness requirements**: authorization data must be real-time; analytics can tolerate 15-30 minute lag
- **Compute patterns**: authorization is random-access, point lookups; analytics is full-table scans and aggregations
- **Scaling properties**: authorizations scale with card transaction volume; analytics scale with the number of finance teams using the dashboards

The dbt layer is particularly powerful for Brex because spend categorization and budget enforcement rules change frequently as new customer types onboard. Finance teams can define custom category mappings; enterprise customers have custom GL code integrations. dbt's modular transformation model lets the data team publish new category rules without touching the transactional system.

## What This Means for Your Brex Interview

Brex interviews tend to focus on real-time systems, financial data modeling, and the engineering tradeoffs behind their product decisions.

**Likely interview topics:**

- **Real-time systems**: Design a system to enforce spending limits at card authorization speed. Candidates who reach for a relational database on the hot path often hit follow-up questions about why that might not meet latency requirements. The answer involves in-memory state, actor models, and async persistence.
- **Fintech domain knowledge**: How does card authorization work? What is the difference between authorization, clearing, and settlement? Brex interviews reward candidates who understand the underlying card network mechanics.
- **Data pipelines**: Design a spend analytics platform for enterprise customers with custom categorization rules. This is a classic OLTP/OLAP separation question with real Brex context.
- **Concurrency**: The actor model, process isolation, message passing vs. shared memory — Elixir/BEAM shows up in Brex engineering blog posts and interviews as a concrete case study for why concurrency model choice matters.
- **Failure modes**: What happens when the bank balance refresh fails? When the BEAM node crashes mid-authorization? Brex interviews probe fault tolerance and recovery design.

The strongest Brex candidates understand that the real-time underwriting model is not just a product feature — it is an engineering constraint that cascades through every layer of the system, from the authorization hot path to the data model to the analytics architecture.

---

*Practice Brex-style real-time systems and fintech architecture questions with Interview Simulator's engineering interview track. Our AI interviewer simulates the depth of technical discussion you'll face at fintech companies like Brex, and gives you structured feedback on your system design reasoning.*
